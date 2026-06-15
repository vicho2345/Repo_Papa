import os
import json
import anthropic
from dotenv import load_dotenv
from database import update_relevance

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

RONALD_PROFILE = """
Constructor Civil Senior, 29 años de experiencia. Especialista en:
- Construcción LAT (Líneas de Alta Tensión): 66kV, 110kV, 220kV, 500kV
- Construcción y montaje de Subestaciones Eléctricas
- Proyectos EPC en sector minero y transmisión eléctrica
- Clientes: Codelco, Transelec, Minera Escondida, AngloAmerican, Los Pelambres, Collahuasi, Chilquinta, CGE
- Metodologías: Last Planner, Lean Construction, Primavera P3, Obeya

Cargos que le interesan:
- Administrador de Contratos
- Jefe General de Construcción / Jefe de Construcción
- Jefe de Terreno (sector eléctrico)
- Project Manager (infraestructura eléctrica/minera)
"""


BATCH_SIZE = 20


def _filter_batch(jobs: list) -> list:
    """Filter a single chunk of jobs. Returns relevant ones."""
    jobs_text = ""
    for i, job in enumerate(jobs):
        jobs_text += f"\nJOB_{i}:\nTítulo: {job['title']}\nEmpresa: {job['company']}\nDescripción: {job.get('description', '')[:200]}\n---"

    prompt = f"""Analiza estas ofertas de trabajo y determina cuáles son relevantes para este candidato:

PERFIL:
{RONALD_PROFILE}

OFERTAS:
{jobs_text}

Responde SOLO con JSON válido, sin texto adicional:
{{
  "results": [
    {{"job_index": 0, "relevant": true, "reason": "razón en máximo 15 palabras"}},
    {{"job_index": 1, "relevant": false, "reason": "razón en máximo 15 palabras"}}
  ]
}}

Relevante si: construcción eléctrica / LAT / subestaciones / infraestructura eléctrica minera / jefatura de construcción / administración de contratos
No relevante si: mantenimiento operativo / diseño sin construcción / técnico eléctrico / ventas / TI"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text.strip()
    if "```" in content:
        content = content.split("```")[1].replace("json", "").strip()

    data = json.loads(content)
    relevant_jobs = []

    for result in data.get("results", []):
        idx = result.get("job_index", -1)
        if idx < 0 or idx >= len(jobs):
            continue
        job = jobs[idx]
        is_relevant = result.get("relevant", False)
        reason = result.get("reason", "")
        update_relevance(job["id"], is_relevant, reason)
        if is_relevant:
            job["relevance_reason"] = reason
            relevant_jobs.append(job)
            print(f"[Haiku] RELEVANTE: {job['title']} @ {job['company']} — {reason}")

    return relevant_jobs


def filter_jobs_batch(jobs: list) -> list:
    """Process jobs in chunks of BATCH_SIZE to avoid token limits."""
    if not jobs:
        return []

    relevant_jobs = []
    for i in range(0, len(jobs), BATCH_SIZE):
        chunk = jobs[i:i + BATCH_SIZE]
        print(f"[Haiku] Filtrando lote {i // BATCH_SIZE + 1} ({len(chunk)} trabajos)...")
        try:
            relevant_jobs.extend(_filter_batch(chunk))
        except Exception as e:
            print(f"[Haiku filter] Error en lote {i // BATCH_SIZE + 1}: {e}")

    return relevant_jobs
