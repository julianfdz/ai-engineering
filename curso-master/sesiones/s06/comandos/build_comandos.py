"""Genera S06-comandos-y-salidas.pdf: la guía de comandos de la Sesión 6 para los alumnos.

Cada comando de la sesión con para qué sirve, cómo se usa, la salida real y cómo leerla. Las salidas son de
la ejecución en local del 18/11/2026 (rama session_06_live). Las de la carpeta salidas/ se capturaron tal
cual; las demás se pegaron de la misma ejecución.

    python build_comandos.py
"""

import html
import pathlib
import subprocess

AQUI = pathlib.Path(__file__).parent
SAL = AQUI / "salidas"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def leer(nombre: str) -> str:
    return (SAL / nombre).read_text(encoding="utf-8-sig").strip("\n").rstrip()


ITEMS = []  # ("h2", texto) | ("intro", html) | ("paso", dict)


def h2(t):
    ITEMS.append(("h2", t))


def intro(t):
    ITEMS.append(("intro", t))


def paso(titulo, para, cmd, salida=None, leer_=None, diapo="", alt=None, alt_lab="En Windows (PowerShell)"):
    ITEMS.append(("paso", dict(titulo=titulo, para=para, cmd=cmd.strip(), salida=salida, leer=leer_,
                               diapo=diapo, alt=alt, alt_lab=alt_lab)))


# ── 0 · Preparar el entorno ─────────────────────────────────────────────────
h2("0 · Preparar el entorno")
intro("Todos los comandos se lanzan desde la <b>raíz del repositorio</b> (donde está <code>docker-compose.yml</code>), "
      "en la rama <code>session_06_live</code>. El código Python se ejecuta <b>dentro</b> del contenedor "
      "<code>estimator</code> con <code>docker compose exec</code>, así que no hace falta instalar nada en el "
      "ordenador. Si levantaste el stack con un nombre de proyecto propio (<code>docker compose -p mi-nombre up</code>), "
      "añade ese <code>-p mi-nombre</code> a cada <code>docker compose</code>. Ninguno de estos comandos llama a un "
      "modelo de IA: se pueden repetir sin coste.")
paso("Levantar los servicios",
     "Arranca los cinco contenedores: el servicio de IA (<code>estimator</code>), su Postgres, Redis, y la web de "
     "Rails con el suyo. La primera vez construye las imágenes y tarda.",
     "docker compose up -d --build\ndocker compose ps",
     leer("01_ps.txt"),
     "Espera a que los cinco digan <b>healthy</b> (los nombres de los contenedores pueden variar en tu equipo). Si alguno se queda en <i>starting</i> o se reinicia, mira "
     "<code>docker compose logs estimator</code>.")
paso("Aplicar la migración de la sesión",
     "Crea las dos tablas nuevas de la S6: <code>ingestion_jobs</code> (el estado de cada ingesta) y "
     "<code>pseudonym_mappings</code> (la tabla de mapeo de la PII).",
     "docker compose exec estimator alembic upgrade head\ndocker compose exec estimator alembic current",
     leer("03_alembic.txt"),
     "<code>0001_session6_initial (head)</code> quiere decir que la base de datos está en la última versión.")

# ── 1 · Pre-flight ──────────────────────────────────────────────────────────
h2("1 · Pre-flight: comprobar que todo está listo")
paso("scripts/preflight_s06.py",
     "Un script de comprobación previa: ocho chequeos que cazan los fallos de montaje típicos antes de ponerse "
     "a trabajar. Cada chequeo es una función; si falla, imprime el motivo. Sale con código 1 si alguno falla, "
     "así que también sirve en un CI.",
     "docker compose exec estimator python scripts/preflight_s06.py",
     leer("04_preflight.txt"),
     "<ul><li><b>Required packages</b>: pandas, pandera, presidio, spaCy, faker, unstructured… con versión mínima.</li>"
     "<li><b>spaCy es_core_news_md</b>: <b>el más importante</b>. Comprueba que el modelo en español reconoce "
     "«Laura Fernández» como persona. Si falla, la pseudonimización no detectará nombres y nadie se enterará.</li>"
     "<li><b>Corpus seed</b>: los 6 JSON, 3 TXT y 1 XLSX de <code>estimator/data/seed/</code>.</li>"
     "<li><b>Catalog validates</b>: el catálogo YAML cumple su contrato (1 fuente incluida).</li>"
     "<li><b>/health</b> y <b>Postgres + migration</b>: el servicio responde y las tablas existen.</li></ul>"
     "Si justo has editado código, el servicio se recarga y <code>/health</code> puede fallar unos segundos: "
     "vuelve a lanzarlo.",
     diapo="5")

# ── 2.1 · Decisión arquitectónica ───────────────────────────────────────────
h2("2.1 · CAG, RAG o híbrido")
paso("python -m app.ingestion.architecture",
     "Convierte la decisión del Article 1 en código que se ejecuta. Describe el corpus del Proyecto 2 y el modelo "
     "(<code>PROYECTO_2</code> y <code>CURRENT_MODEL</code> en <code>app/ingestion/architecture.py</code>), evalúa "
     "las cuatro restricciones del CAG y recomienda una arquitectura.",
     "docker compose exec estimator python -m app.ingestion.architecture",
     leer("05_architecture.txt"),
     "<ul><li><b>NO viable</b>: basta con que una restricción esté en rojo (<code>viable</code> es un "
     "<code>all([...])</code>).</li>"
     "<li><b>context_window</b>: 250.000 tokens no caben en el 70 % útil de 128.000.</li>"
     "<li><b>latency</b> y <b>lost_in_the_middle</b>: por encima de 100.000 tokens el código asume que la latencia "
     "se dispara y el centro del contexto se atiende peor.</li>"
     "<li><b>cost</b> no sale en rojo: hay caché de prefijo y el corpus cambia cada 7 días.</li></ul>",
     diapo="7")
paso("Prueba tú: cambiar el escenario",
     "Las funciones son puras: puedes evaluar tu propio corpus sin tocar el fichero. Abre un intérprete dentro del "
     "contenedor con <code>docker compose exec estimator python</code> y pega:",
     """from app.ingestion.architecture import *
for name, tok, ref, citar, acceso in [
        ("Pequeño y estable", 60_000, 30, False, False),
        ("Pequeño pero hay que citar", 60_000, 30, True, False),
        ("Proyecto 2", 250_000, 7, True, True)]:
    c = CorpusProfile(name, tok, ref, citar, acceso)
    v = assess_cag_viability(c, CURRENT_MODEL)
    print(name, v.viable, v.failing_constraints(), recommend_architecture(c, CURRENT_MODEL))""",
     """Pequeño y estable           60,000 tokens · citar=False · acceso=False → viable=True  rojo=[] → CAG
Pequeño pero hay que citar  60,000 tokens · citar=True  · acceso=False → viable=True  rojo=[] → Hybrid
Proyecto 2                 250,000 tokens · citar=True  · acceso=True  → viable=False rojo=['context_window',
                                                         'latency', 'lost_in_the_middle'] → RAG""",
     "Fíjate en el segundo caso: las cuatro restricciones técnicas pasan, pero <b>hay que citar la fuente</b> y un "
     "CAG no sabe de qué documento sale cada dato. Por eso recomienda <b>Hybrid</b>: lo estable por CAG, lo que "
     "hay que citar por RAG. (Salida resumida; el <code>print</code> real muestra los mismos valores.)",
     diapo="8")

# ── 2.2 · Catálogo ──────────────────────────────────────────────────────────
h2("2.2 · El catálogo de fuentes")
paso("python -m app.ingestion.catalog.inspect",
     "El primer paso del censo: mira el disco y devuelve solo lo que se puede <b>medir</b> sin opinar. Por cada "
     "carpeta: número de ficheros, tamaño, fecha de la última modificación y formatos. Lo subjetivo (owner, "
     "calidad, sensibilidad) lo decide una persona en el YAML.",
     "docker compose exec estimator python -m app.ingestion.catalog.inspect data/seed",
     leer("06_inspect.txt"),
     "La fila <b>seed</b> es el Excel de tarifas suelto en la raíz: <b>latest=2024-01-12</b>. Si su owner dice que "
     "se actualiza cada año, hace casi dos años que no se cumple: es una <b>fuente podrida</b>. "
     "(Las fechas de <code>budgets</code> y <code>transcripts</code> son las de cuando se descargó el repositorio.)",
     diapo="10")
paso("python -m app.ingestion.catalog.loader",
     "Carga <code>data/catalog/catalog.yaml</code> y lo valida contra los modelos Pydantic de "
     "<code>app/ingestion/catalog/models.py</code>. Úsalo antes de hacer commit de un cambio en el catálogo: si el "
     "YAML rompe el contrato, falla aquí y no en mitad de una ingesta.",
     "docker compose exec estimator python -m app.ingestion.catalog.loader data/catalog/catalog.yaml",
     leer("07_loader.txt"),
     "<ul><li>Tres fuentes auditadas y <b>una sola incluida</b>: <code>presupuestos_json</code>. Las transcripciones "
     "están en <i>review</i> y el Excel en <i>exclude</i>.</li>"
     "<li>El <code>RuntimeWarning</code> de la primera línea es inofensivo: sale por ejecutar con <code>-m</code> un "
     "módulo que el paquete ya importó.</li></ul>",
     diapo="11")
paso("Prueba tú: romper el catálogo a propósito",
     "La regla «si no es include, el motivo es obligatorio» está en el modelo, no en un documento. Para verla "
     "saltar, en <code>docker compose exec estimator python</code>:",
     """import yaml, pathlib
from app.ingestion.catalog.models import DataCatalog
raw = yaml.safe_load(pathlib.Path("data/catalog/catalog.yaml").read_text(encoding="utf-8"))
raw["sources"][2]["decision_reason"] = ""        # el Excel, sin motivo
DataCatalog.model_validate(raw)""",
     """1 validation error for DataCatalog
sources.2
  Value error, decision=exclude requires a non-empty decision_reason [type=value_error, ...]""",
     "Excluir una fuente sin escribir por qué no pasa la validación. Así el catálogo no se degrada en silencio "
     "con el tiempo.")

# ── 2.3 · Ingesta ───────────────────────────────────────────────────────────
h2("2.3 · Ingesta: el endpoint asíncrono")
intro("La ingesta es el pipeline <b>offline</b>: procesar una fuente puede tardar, así que el endpoint no espera. "
      "Responde <b>202</b> con un <code>job_id</code> y el cliente pregunta por el estado. Los comandos van con "
      "<code>curl</code> (macOS, Linux o Git Bash); debajo de cada uno está el equivalente para PowerShell. "
      "También se puede hacer desde el Swagger: <code>http://localhost:8000/docs</code>, sección <i>ingestion</i>, "
      "«Try it out».")
paso("POST /api/v1/ingestion/runs",
     "Lanza la ingesta de una fuente del catálogo. Por dentro: comprueba que la fuente existe y es <i>include</i>, "
     "crea una fila en <code>ingestion_jobs</code> y deja el trabajo en segundo plano (loader → parser → Documents).",
     """curl -s -X POST http://localhost:8000/api/v1/ingestion/runs \\
  -H 'Content-Type: application/json' -d '{"source_name": "presupuestos_json"}'""",
     leer("11_run.txt"),
     "<b>pending</b> no es un error: el trabajo acaba de empezar. Copia el <code>job_id</code> para el siguiente paso.",
     diapo="14",
     alt="""$r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/ingestion/runs `
  -ContentType 'application/json' -Body '{"source_name":"presupuestos_json"}'
$r""")
paso("GET /api/v1/ingestion/jobs/{job_id}",
     "Consulta el estado del job: <i>pending</i>, <i>running</i>, <i>completed</i> o <i>failed</i>.",
     "curl -s http://localhost:8000/api/v1/ingestion/jobs/<job_id>",
     leer("12_job.txt"),
     "<b>completed</b> con <b>documents_count: 6</b>: los seis JSON de presupuestos se convirtieron en seis "
     "Documents. Con este volumen tarda unos milisegundos; con miles de PDF, minutos.",
     alt='Invoke-RestMethod "http://localhost:8000/api/v1/ingestion/jobs/$($r.job_id)" | Format-List')
paso("Las dos ramas de error",
     "El endpoint respeta el catálogo: una fuente excluida no se procesa aunque el fichero esté en disco.",
     """curl -s -X POST http://localhost:8000/api/v1/ingestion/runs \\
  -H 'Content-Type: application/json' -d '{"source_name": "rate_card_xlsx"}'
curl -s -X POST http://localhost:8000/api/v1/ingestion/runs \\
  -H 'Content-Type: application/json' -d '{"source_name": "no_existe"}'""",
     leer("13_excluida.txt") + "\n\n" + leer("14_noexiste.txt"),
     "<ul><li><b>400 source_not_included</b>: la fuente existe pero es <i>exclude</i>. La respuesta trae el motivo "
     "escrito en el YAML.</li><li><b>404 unknown_source</b>: no está en el catálogo.</li></ul>")
paso("Ver los logs de la ingesta",
     "Cada ingesta deja eventos estructurados (<code>ingestion.started</code>, <code>ingestion.completed</code>) con "
     "el <code>job_id</code>, la fuente y el número de documentos.",
     "docker compose logs --tail 40 estimator",
     leer("16_logs.txt"),
     "Se ve el ciclo completo: el 202 del POST, el inicio y el fin del job con <code>documents_count=6</code>, y las "
     "peticiones que acabaron en 400 y 404.")
paso("Opcional: el mismo contrato desde Rails",
     "La web de Rails tiene un cliente HTTP de ejemplo (<code>estimator-web/app/services/estimator_ai/"
     "ingestion_client.rb</code>). Solo ilustra el contrato: cualquier cliente HTTP sirve.",
     """docker compose exec estimator-web bin/rails runner 'c = EstimatorAi::IngestionClient.new; j = c.trigger_ingestion(source_name: "presupuestos_json"); p j; sleep 2; p c.job_status(j.fetch("job_id"))'""",
     leer("15_rails.txt"),
     "Las mismas dos llamadas, ahora desde Ruby: primero <i>pending</i>, dos segundos después <i>completed</i>.")

# ── 2.4 · Limpieza ──────────────────────────────────────────────────────────
h2("2.4 · Limpieza y validación")
paso("Mirar los datos antes de limpiarlos",
     "Antes de ejecutar nada, conviene ver qué suciedad traen los presupuestos. Los cuatro casos:",
     "cat estimator/data/seed/budgets/BUDGET-2024-0002.json   # en PowerShell: Get-Content",
     """BUDGET-2024-0002:  "currency": "eur",  "signed_at": "12/03/2024"     ← formato distinto al resto
BUDGET-2024-0003:  "client_name": "TBD",  "contact": "N/A",  "contact_email": ""   ← nulos disfrazados
BUDGET-2024-0004:  "total_amount": -50000                              ← fuera de rango
BUDGET-2024-0005:  dos ficheros, -v1 y -v2                             ← duplicado divergente""",
     "Son las cuatro familias de suciedad: formato heterogéneo, nulos disfrazados, fuera de rango y duplicados. "
     "(Extracto de los campos relevantes de cada fichero.)",
     diapo="16")
paso("scripts/demo_cleaning_s06.py",
     "Ejecuta el paso 2.4 completo sobre los seis presupuestos: <code>clean_budget_records</code> (repara lo "
     "reparable), luego <code>validate_with_policy</code> (valida con Pandera y reparte cada fila en válida, "
     "cuarentena o descartada) e imprime el informe.",
     "docker compose exec estimator python scripts/demo_cleaning_s06.py",
     leer("08_cleaning.txt"),
     "<ul><li><b>6 ficheros → 5 filas</b>: el dedup juntó las dos versiones de BUDGET-2024-0005 y se quedó con la de "
     "<code>signed_at</code> más reciente (la v2).</li>"
     "<li><b>Descartada</b> la 0004: importe negativo, falla <code>greater_than_or_equal_to(0)</code>.</li>"
     "<li><b>Cuarentena</b> la 0002: pandas dedujo el formato <code>%Y-%m-%d</code> de las demás filas, "
     "<code>12/03/2024</code> no encaja y queda como fecha vacía (<code>NaT</code>), que falla "
     "<code>not_nullable</code>. Es lo que avisa el <code>UserWarning</code>.</li>"
     "<li>La 0003 («TBD») pasa: el «TBD» se convierte en nulo, pero <code>client_name</code> admite nulos.</li>"
     "<li><code>column_in_schema: 5</code> y <code>dtype('float64')</code> son fallos de <b>columna</b>, no de fila "
     "(ver el siguiente paso): no mandan ninguna fila a cuarentena.</li></ul>",
     diapo="18")
paso("Prueba tú: ver cada fallo de Pandera",
     "Para entender el informe, mira la tabla de fallos que devuelve Pandera con <code>lazy=True</code>. En "
     "<code>docker compose exec estimator python</code>:",
     """import json, pathlib, pandera.pandas as pa
from app.ingestion.cleaning import clean_budget_records
from app.ingestion.cleaning.schemas import BudgetRecord
recs = [json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(pathlib.Path("data/seed/budgets").glob("*.json"))]
df = clean_budget_records(recs)
try:
    BudgetRecord.validate(df, lazy=True)
except pa.errors.SchemaErrors as e:
    print(e.failure_cases[["column", "check", "index", "failure_case"]])""",
     """      column                       check index  failure_case
        None            column_in_schema  None        phases
        None            column_in_schema  None       contact
        None            column_in_schema  None contact_email
        None            column_in_schema  None         notes
        None            column_in_schema  None  content_hash
total_amount greater_than_or_equal_to(0)     3        -50000
   signed_at                not_nullable     1           NaN
total_amount            dtype('float64')  None         int64""",
     "<ul><li><code>lazy=True</code> recoge <b>todos</b> los fallos de una vez; sin él, Pandera pararía en el "
     "primero y la política no podría repartir las filas.</li>"
     "<li>Los de <code>index None</code> son de columna: <code>strict=True</code> señala las columnas que el esquema "
     "no declara, y <code>total_amount</code> llega como entero en vez de float.</li>"
     "<li>Los que tienen índice (3 y 1) son los que la política reparte: la fila 3 (0004) se descarta y la 1 (0002) va "
     "a cuarentena.</li></ul>")

# ── 2.5 · PII ───────────────────────────────────────────────────────────────
h2("2.5 · PII y pseudonimización")
paso("Mirar la transcripción original",
     "La demo pseudonimiza una transcripción de reunión con nombres, emails, un id de presupuesto y un código de "
     "cliente. Así empieza:",
     "head -c 700 estimator/data/seed/transcripts/transcripcion_2025-02-03_betanorte.txt",
     """[09:15:02] Javier Romero: Buenas. Estamos revisando el presupuesto BUDGET-2024-0002 firmado en marzo,
código de cliente CLI-0078. Quería preguntar por el escalado de la integración con el ERP.
[09:15:40] Diego Marín: Sí, lo tengo aquí. La fase de backend está cerrada. ¿Qué dudas tienes?
[09:16:18] Javier Romero: Nuestra responsable de logística, Pilar Alonso, quiere meter el almacén de
Zaragoza en el alcance. […] y la mando también a j.romero@betanorte.com y al alias de operaciones
que me diste, ops-betanorte@betanorte.com.""",
     "Los nombres y empresas del repositorio son ficticios.",
     alt='Get-Content estimator\\data\\seed\\transcripts\\transcripcion_2025-02-03_betanorte.txt -TotalCount 4')
paso("scripts/demo_pii_s06.py",
     "Construye el analizador de Presidio en español (<code>build_analyzer</code>: <code>es_core_news_md</code> + los "
     "reconocedores de <code>BUDGET-…</code> y <code>CLI-…</code>) y pasa la transcripción por el "
     "<code>ConsistentPseudonymizer</code>. Imprime los primeros 400 caracteres del resultado y los mapeos.",
     "docker compose exec estimator python scripts/demo_pii_s06.py",
     leer("09_pii.txt"),
     "<ul><li>Cada dato se cambia por otro <b>del mismo tipo</b>: un nombre por un nombre, un email por un email, un "
     "<code>BUDGET-…</code> por otro. Así el texto sigue teniendo sentido para el embedding.</li>"
     "<li><b>Consistencia</b>: «Javier Romero» es «Pánfilo del Barros» en las dos líneas en que aparece.</li>"
     "<li>Los tipos sin generador (<code>ORGANIZATION</code>, <code>URL</code>) se tapan con "
     "<code>REDACTED-xxxxxxxx</code>.</li>"
     "<li><b>Falsos positivos</b>: «Quería» y «Sí» se tomaron por personas, y <code>CLI-0078</code> se detectó como "
     "persona en vez de como código de cliente. Es el precio del NER en español; en producción se sube el umbral, "
     "se añade una lista de exclusión o se usa <code>es_core_news_lg</code>.</li>"
     "<li>El <code>BUDGET-…</code> nuevo es aleatorio: cambia en cada ejecución. Los nombres salen siempre iguales "
     "porque Faker usa una semilla fija.</li></ul>",
     diapo="21")
paso("La mapping table en Postgres",
     "Comprueba cuántos mapeos hay guardados por tipo de entidad en la tabla <code>pseudonym_mappings</code>.",
     'docker compose exec estimator-postgres psql -U estimator -d estimator \\\n'
     '  -c "SELECT entity_type, count(*) FROM pseudonym_mappings GROUP BY 1"',
     leer("10_pii_psql.txt"),
     "<b>0 filas</b> es lo esperado: la demo usa <code>InMemoryMappingStore</code>, que guarda en memoria y se pierde "
     "al acabar. En el pipeline real se usa <code>PostgresMappingStore</code> y ahí se guarda el <b>hash</b> "
     "(HMAC-SHA256) de cada valor, nunca el valor original. Esa tabla es la que hace posible el derecho al olvido.",
     diapo="22")


# ── HTML ────────────────────────────────────────────────────────────────────
CSS = """
@page { size: A4; margin: 14mm 13mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1d2330; font-size: 10pt; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 2mm; color: #2f2a8a; }
.sub { color: #4a5568; margin-bottom: 4mm; font-size: 9.5pt; line-height: 1.45; }
h2 { font-size: 13pt; color: #fff; background: #3f3fb0; padding: 2mm 3mm; margin: 6mm 0 3mm; border-radius: 1.5mm;
     break-after: avoid; }
.intro { font-size: 9.3pt; line-height: 1.45; margin: 0 0 3mm; background: #eef0ff; border-radius: 1.5mm;
         padding: 2.2mm 3mm; }
.paso { border: 0.3mm solid #cfd3ea; border-radius: 1.5mm; margin: 0 0 3.5mm; padding: 2.5mm 3mm;
        break-inside: avoid; }
.cab { display: flex; justify-content: space-between; align-items: baseline; gap: 3mm; }
.tit { font-weight: 700; font-size: 10.8pt; font-family: Consolas, 'Segoe UI', monospace; color: #2f2a8a; }
.diapo { font-size: 8pt; color: #6b7280; white-space: nowrap; }
.para { font-size: 9.3pt; line-height: 1.42; margin: 1.2mm 0 0; }
.lab { font-size: 7.5pt; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; margin: 1.8mm 0 0.6mm; }
pre { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 7.6pt; line-height: 1.32; margin: 0;
      padding: 1.8mm 2.2mm; border-radius: 1mm; white-space: pre-wrap; word-break: break-word; }
pre.cmd { background: #1c1f2e; color: #f3f6fb; }
pre.alt { background: #2b2f45; color: #dfe3f5; }
pre.out { background: #f4f5f9; color: #1d2330; border: 0.25mm solid #e1e3ee; }
.leer { margin-top: 1.6mm; font-size: 9.1pt; line-height: 1.42; background: #f1fbf5; border-left: 1mm solid #2f9e6a;
        padding: 1.5mm 2.5mm; }
.leer b.l { color: #1f7a50; }
.leer ul { margin: 0.5mm 0 0 4mm; padding: 0; }
code { font-family: Consolas, monospace; font-size: 0.92em; background: #eef0f7; padding: 0 0.6mm; border-radius: 0.6mm; }
"""


def render() -> str:
    out = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>S06 · comandos y salidas</title>"
           f"<style>{CSS}</style></head><body>",
           "<h1>Sesión 6 · Los comandos de la sesión y su salida</h1>",
           "<div class='sub'>Data-driven AI: análisis y normalización · Máster en AI Engineering (LIDR). Cada script y "
           "comando que se usa en el directo, en orden: <b>para qué sirve</b>, <b>cómo se lanza</b>, la <b>salida "
           "real</b> (ejecutada en local sobre la rama <code>session_06_live</code>) y <b>cómo leerla</b>. "
           "La referencia «diapo N» indica dónde aparece en las diapositivas.</div>"]
    for kind, val in ITEMS:
        if kind == "h2":
            out.append(f"<h2>{html.escape(val)}</h2>")
        elif kind == "intro":
            out.append(f"<div class='intro'>{val}</div>")
        else:
            v = val
            diapo = f"<span class='diapo'>diapo {v['diapo']}</span>" if v["diapo"] else ""
            out.append(f"<div class='paso'><div class='cab'><div class='tit'>{html.escape(v['titulo'])}</div>"
                       f"{diapo}</div><div class='para'><b>Para qué sirve.</b> {v['para']}</div>")
            out.append(f"<div class='lab'>Comando</div><pre class='cmd'>{html.escape(v['cmd'])}</pre>")
            if v["alt"]:
                out.append(f"<div class='lab'>{html.escape(v['alt_lab'])}</div>"
                           f"<pre class='alt'>{html.escape(v['alt'])}</pre>")
            if v["salida"]:
                out.append(f"<div class='lab'>Salida</div><pre class='out'>{html.escape(v['salida'])}</pre>")
            if v["leer"]:
                out.append(f"<div class='leer'><b class='l'>Cómo leerla.</b> {v['leer']}</div>")
            out.append("</div>")
    out.append("</body></html>")
    return "".join(out)


if __name__ == "__main__":
    h = AQUI / "comandos-y-salidas-s06.html"
    h.write_text(render(), encoding="utf-8")
    pdf = AQUI.parent / "S06-comandos-y-salidas.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", h.as_uri()], check=True, capture_output=True)
    print("ok", pdf, pdf.stat().st_size)
