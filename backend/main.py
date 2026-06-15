import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from database import init_db, get_relevant_jobs, get_job_by_id, dismiss_job, mark_notified
from scraper import scrape_all_portals
from claude_filter import filter_jobs_batch
from cv_adapter import adapt_cv_for_job
from cv_generator import generate_cv_docx
from notifier import send_whatsapp_notification

load_dotenv()

scheduler = AsyncIOScheduler()


async def run_scan():
    """Main scheduled task: scrape → filter → notify."""
    print("\n[Scan] ══ Iniciando escaneo ══")
    try:
        # 1. Scrape all portals for new jobs
        new_jobs = scrape_all_portals()
        if not new_jobs:
            print("[Scan] Sin trabajos nuevos en este ciclo.")
            return

        # 2. Filter relevance with Claude Haiku (single batch call)
        relevant = filter_jobs_batch(new_jobs)
        if not relevant:
            print("[Scan] Ningún trabajo nuevo relevante.")
            return

        # 3. Notify Ronald via WhatsApp
        send_whatsapp_notification(relevant)
        mark_notified([j["id"] for j in relevant])

        print(f"[Scan] ══ Ciclo completo: {len(relevant)} oferta(s) relevante(s) ══\n")

    except Exception as e:
        print(f"[Scan] Error inesperado: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(run_scan, "interval", hours=6, id="scan_job", max_instances=1)
    scheduler.start()
    print("[Scheduler] Activo — escaneo cada 6 horas.")
    yield
    scheduler.shutdown()


app = FastAPI(title="Agente Empleo Ronald", version="1.0.0", lifespan=lifespan)

# Allow requests from the Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Narrow this to FRONTEND_URL once deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "agente-empleo-ronald"}


# ── Jobs ────────────────────────────────────────────────────────────────────
@app.get("/jobs")
def get_jobs():
    jobs = get_relevant_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@app.post("/jobs/{job_id}/dismiss")
def dismiss(job_id: int):
    dismiss_job(job_id)
    return {"ok": True}


# ── Manual scan trigger ─────────────────────────────────────────────────────
@app.post("/scan/run")
async def manual_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scan)
    return {"message": "Escaneo iniciado en segundo plano"}


# ── CV adaptation + download ─────────────────────────────────────────────────
@app.post("/adapt-cv/{job_id}")
async def adapt_cv(job_id: int):
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    # 1. Adapt CV text with Claude Sonnet
    adapted_data = adapt_cv_for_job(job)

    # 2. Generate .docx
    docx_bytes = generate_cv_docx(adapted_data)

    # 3. Stream file back to browser
    safe_company = job["company"].replace(" ", "_").replace("/", "-")[:30]
    filename = f"CV_Ronald_Sarabia_{safe_company}.docx"

    return StreamingResponse(
        iter([docx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
