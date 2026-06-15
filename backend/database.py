import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "jobs.db"))


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url_hash TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        company TEXT,
        portal TEXT,
        url TEXT,
        description TEXT,
        location TEXT DEFAULT 'Chile',
        date_found TEXT,
        is_relevant INTEGER DEFAULT 0,
        relevance_reason TEXT DEFAULT '',
        notified INTEGER DEFAULT 0,
        dismissed INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()


def hash_url(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def save_jobs_batch(jobs: list) -> list:
    """Save new jobs to DB. Returns only the ones that were actually new."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = []
    now = datetime.now().isoformat()
    for job in jobs:
        if not job.get("url"):
            continue
        try:
            c.execute(
                """INSERT INTO jobs
                (url_hash, title, company, portal, url, description, location, date_found, is_relevant, relevance_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, '')""",
                (
                    hash_url(job["url"]),
                    job["title"],
                    job.get("company", "Sin especificar"),
                    job.get("portal", ""),
                    job["url"],
                    job.get("description", ""),
                    job.get("location", "Chile"),
                    now,
                ),
            )
            job["id"] = c.lastrowid
            saved.append(job)
        except sqlite3.IntegrityError:
            pass  # Already in DB
    conn.commit()
    conn.close()
    return saved


def update_relevance(job_id: int, is_relevant: bool, reason: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE jobs SET is_relevant=?, relevance_reason=? WHERE id=?",
        (1 if is_relevant else 0, reason, job_id),
    )
    conn.commit()
    conn.close()


def get_relevant_jobs() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM jobs WHERE is_relevant=1 AND dismissed=0 ORDER BY date_found DESC LIMIT 50"
    )
    jobs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jobs


def get_job_by_id(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_notified(job_ids: list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("UPDATE jobs SET notified=1 WHERE id=?", [(jid,) for jid in job_ids])
    conn.commit()
    conn.close()


def dismiss_job(job_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE jobs SET dismissed=1 WHERE id=?", (job_id,))
    conn.commit()
    conn.close()
