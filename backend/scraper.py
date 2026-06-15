import os
import time
import random
import requests
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from database import save_jobs_batch

load_dotenv()

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPERAPI_URL = "https://api.scraperapi.com/"

QUERIES = [
    "jefe+construccion+electrica",
    "administrador+contratos+construccion",
    "jefe+terreno+alta+tension",
    "jefe+construccion+subestaciones+electricas",
    "jefe+general+construccion",
    "administrador+obra+electrica",
]


def random_delay():
    time.sleep(random.uniform(2, 4))


def get_headers():
    return {}


def _scraperapi_get(url: str) -> requests.Response:
    return requests.get(
        SCRAPERAPI_URL,
        params={"api_key": SCRAPERAPI_KEY, "url": url},
        timeout=30,
    )


# ─── COMPUTRABAJO ──────────────────────────────────────────────────────────
def scrape_computrabajo() -> list:
    if not SCRAPERAPI_KEY:
        print("[Computrabajo] SCRAPERAPI_KEY no configurada.")
        return []

    jobs = []
    for query in QUERIES:
        try:
            url = f"https://www.computrabajo.cl/ofertas-de-trabajo/?q={query}"
            resp = _scraperapi_get(url)
            if resp.status_code != 200:
                print(f"[Computrabajo] HTTP {resp.status_code} para '{query}'")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            articles = soup.find_all("article")

            for article in articles:
                title_tag = article.find("a", class_="js-o-link")
                company_tag = article.select_one("p.dFlex.vm_fx")
                location_tag = article.find("span", class_="mr10")

                if not title_tag:
                    continue

                href = title_tag.get("href", "")
                link = f"https://www.computrabajo.cl{href}" if href.startswith("/") else href

                jobs.append({
                    "title": title_tag.get_text(strip=True),
                    "company": company_tag.get_text(strip=True) if company_tag else "Sin especificar",
                    "portal": "Computrabajo",
                    "url": link,
                    "description": "",
                    "location": location_tag.get_text(strip=True) if location_tag else "Chile",
                })

            print(f"[Computrabajo] '{query}': {len(articles)} resultados")
            random_delay()

        except Exception as e:
            print(f"[Computrabajo] Error en '{query}': {e}")

    return jobs


# ─── TRABAJANDO.CL ─────────────────────────────────────────────────────────
def scrape_trabajando() -> list:
    if not SCRAPERAPI_KEY:
        return []

    jobs = []
    for query in QUERIES:
        try:
            url = f"https://www.trabajando.cl/empleos?q={query}&l=Chile"
            resp = _scraperapi_get(url)
            if resp.status_code != 200:
                print(f"[Trabajando] HTTP {resp.status_code} para '{query}'")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("div.job-item, article.job, div.aviso")

            for card in cards:
                title_tag = card.find("a")
                if not title_tag:
                    continue
                href = title_tag.get("href", "")
                link = f"https://www.trabajando.cl{href}" if href.startswith("/") else href

                jobs.append({
                    "title": title_tag.get_text(strip=True),
                    "company": "Sin especificar",
                    "portal": "Trabajando.cl",
                    "url": link,
                    "description": "",
                    "location": "Chile",
                })

            print(f"[Trabajando] '{query}': {len(cards)} resultados")
            random_delay()

        except Exception as e:
            print(f"[Trabajando] Error en '{query}': {e}")

    return jobs


# ─── INDEED RSS (backup) ───────────────────────────────────────────────────
def scrape_indeed_rss() -> list:
    jobs = []
    queries = [
        "jefe+construccion",
        "administrador+contratos+construccion",
        "construccion+electrica",
        "subestaciones+electricas",
        "jefe+terreno+electrica",
    ]
    for query in queries:
        try:
            url = f"https://cl.indeed.com/rss?q={query}&l=Chile&radius=200&sort=date"
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                jobs.append({
                    "title": entry.get("title", "").strip(),
                    "company": entry.get("author", "Sin especificar").strip(),
                    "portal": "Indeed",
                    "url": entry.get("link", "").strip(),
                    "description": BeautifulSoup(entry.get("summary", ""), "lxml").get_text(strip=True)[:600],
                    "location": "Chile",
                })
            random_delay()
        except Exception as e:
            print(f"[Indeed] Error en '{query}': {e}")
    return jobs


# ─── ORCHESTRATOR ──────────────────────────────────────────────────────────
def scrape_all_portals() -> list:
    print("[Scraper] Iniciando escaneo...")

    all_jobs = []
    all_jobs.extend(scrape_computrabajo())
    all_jobs.extend(scrape_indeed_rss())

    seen = set()
    unique = []
    for job in all_jobs:
        url = job.get("url", "").strip()
        if url and url not in seen:
            seen.add(url)
            unique.append(job)

    new_jobs = save_jobs_batch(unique)
    print(f"[Scraper] Total: {len(all_jobs)} | Únicos: {len(unique)} | Nuevos: {len(new_jobs)}")
    return new_jobs