import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

RONALD_CV_BASE = """RONALD SARABIA MELGAREJO
rasarabiam@gmail.com | +56 9 9535 9803 | linkedin.com/in/ronald-sarabia-melgarejo-29a04b157

PRESENTACIÓN PROFESIONAL
Profesional con más de 29 años de experiencia en construcción de proyectos de infraestructura eléctrica y sector de la construcción, Constructor Civil, Diplomado en Gestión de la Construcción.

Especialista senior en Construcción de Líneas de Alta Tensión y Subestaciones Eléctricas. Vasta experiencia desarrollada en Bbosch y Consorcio Kipreos-Inprolec sumando 24 años en cargos como Jefe de Oficina Técnica, Jefe de Terreno, Jefe de Construcción, Jefe General de Construcción y Administrador de Contratos. 13 años ejecutando proyectos para compañías Mineras: Codelco S.A., Minera Escondida, Minera Los Pelambres, AngloAmerican Chile S.A., Collahuasi. 11 años en Empresas Transmisoras: Transelec S.A., Chilquinta Energía, CGE Transmisión S.A.

Responsable, metódico, con competencias en planificación, trabajo en equipo, liderazgo, adaptabilidad y comprometido con seguridad, calidad, medio ambiente, producción y mejora continua.

EXPERIENCIA PROFESIONAL

ASA INGENIERIA, CONSTRUCCION Y MANTENIMIENTO SPA | Febrero – Junio 2026
Jefe de Construcción — Proyecto Reemplazo Fibra Óptica zona 3, mandante Transelec S.A.

BBOSCH S.A. — TRANSBOSCH | Junio 2025 – Enero 2026
Administrador de Contratos — División Ingeniería y Construcción de sistemas eléctricos.

CONSORCIO KIPREOS INPROLEC | Enero 2023 – Abril 2025
Jefe General de Construcción — Proyecto STE C20+ Compañía Minera Doña Inés de Collahuasi.
"Construcción, Precomisionamiento y Puesta en Marcha Líneas Aéreas y Subestaciones 220 kV"
Alcances: SE Tarapacá | LAT 220kV Tarapacá–Puerto Collahuasi | SE Puerto Collahuasi (PS1) | SE Geoglifos | LAT 2x220kV Geoglifos–Caliche | SE Caliche (PS2).
Logro principal: Formación de equipos de alto rendimiento. 40% de avance a dic. 2023, término en plazo abril 2025.

BBOSCH S.A. | 2000 – Agosto 2022
10 años Administrador de Contratos | 8 años Jefe Construcción/Terreno | 4 años Jefe Oficina Técnica.

Administrador de Contratos / Jefe de Construcción (2011–2022):
- 2019–2022 | Transelec — Línea 2x500kV Pichirropulli–Nueva Puerto Montt (140 km, USD 100M). Last Planner. Gestión durante estallido social y pandemia.
- 2016–2018 | Codelco División Chuquicamata — Línea 220kV Encuentro–DMH–Tchitack + salas eléctricas (USD 35M). Metodología Obeya Lean.
- 2015 | Codelco — Reconstrucción fast track Línea 110kV Llanta 2 post-aluvión Atacama (USD 4M).
- 2013–2015 | Codelco VP — Línea distribución 110kV acceso vía andinistas y helicóptero (USD 25M).

Jefe de Terreno / Administrador de Contratos (2004–2011):
- 2008 | AngloAmerican — By Pass Línea 66kV interior Mina Los Bronces (EPC).
- 2007 | Electroandina — Línea 1x220kV SE Laberinto–SE Gaby, Antofagasta (EPC llave en mano).
- 2004 | Minera Escondida — Línea 13,8kV Premina + Línea 69kV + SE Principal Escondida Norte.

Jefe de Oficina Técnica (2000–2004):
- HQI Transelec — Transformación 500kV Línea 2x220kV Charrúa–Ancoa.
- Chilquinta Energía — Refuerzo Línea 2x110kV Agua Santa–Miraflores.
- Minera Los Pelambres — Mejoramiento Línea 2x220kV Quillota–Los Piuquenes.

SECTOR EDIFICACIÓN | 1995–2000
Constructoras: Romeral Ltda. | Jorge Rojas Figueroa | Juan Carlos Ruiz S.A. | Nualart y Cía. Ltda. | Inmobiliaria Cerro Maulén Ltda.

FORMACIÓN ACADÉMICA
Constructor Civil — Universidad de la Frontera, 1996
Diplomado en Gestión de la Construcción — Universidad Católica de Chile, 2013
(Administración de Proyectos | Liderazgo | Desarrollo Organizacional | Gestión y Mejoramiento de la Calidad)

CURSOS Y CERTIFICACIONES
Gestión de Contratos en Proyectos de Construcción | El Último Planificador (Last Planner, Lean Construction)
Primavera P3 | MS Project | Autocad R14 | ISO 9001-2000 | Prevención de Riesgos en Minería | Construyendo con Cero Daño

IDIOMAS: Inglés nivel básico

INTERESES: Bikram Yoga | Básquetbol | Ciclismo MTB"""


def adapt_cv_for_job(job: dict) -> dict:
    """Use Claude Sonnet to adapt the presentation paragraph for the specific job."""

    prompt = f"""Eres un experto en optimización de CVs para sistemas ATS en Chile, especializado en construcción e infraestructura eléctrica.

CV BASE:
{RONALD_CV_BASE}

OFERTA DE TRABAJO:
Título: {job['title']}
Empresa: {job['company']}
Portal: {job['portal']}
Descripción: {job.get('description', 'No disponible')[:800]}

INSTRUCCIONES:
1. Adapta SOLO el párrafo de "PRESENTACIÓN PROFESIONAL" integrando keywords de la oferta de forma natural y profesional.
2. NO inventes experiencia, ni modifiques empresas, cargos o fechas.
3. Identifica los 3 proyectos del CV más relevantes para esta oferta.
4. Lista las 5 keywords técnicas más importantes de la oferta que están presentes en la experiencia real del candidato.
5. El tono debe ser ejecutivo y enfocado al sector minero-eléctrico chileno.

Responde ÚNICAMENTE con JSON válido:
{{
  "presentacion_adaptada": "nuevo texto del párrafo de presentación con keywords integradas",
  "proyectos_destacados": ["descripción breve proyecto 1", "descripción breve proyecto 2", "descripción breve proyecto 3"],
  "keywords_integradas": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        data = json.loads(content)
        print(f"[Sonnet] CV adaptado para: {job['title']} @ {job['company']}")
        return {
            "adapted_presentacion": data.get("presentacion_adaptada", ""),
            "proyectos_destacados": data.get("proyectos_destacados", []),
            "keywords": data.get("keywords_integradas", []),
            "job": job,
        }

    except Exception as e:
        print(f"[Sonnet] Error adaptando CV: {e}")
        return {
            "adapted_presentacion": "",
            "proyectos_destacados": [],
            "keywords": [],
            "job": job,
        }
