"""Genera el deck de la Sesión 6 (Data-driven AI: análisis y normalización) de Julián Fernández.

Edición 2026-10 (19/11/2026). Reutiliza el motor de la S7 y la franja grande «En el código» de la S5,
como el deck de la S11. Cada diapo de contenido lleva al pie el fichero y la línea que se abre en VS Code
(rama session_06_live_local, worktree ai-engineering-s06). Las salidas son las de la ejecución en local
del 18/11/2026. El deck de la edición 2609 está en ../anterior-2609/.

    python build_deck.py
    # → ../Sesion06-Julian-Fernandez.pdf
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("s05_deck", HERE.parent.parent / "s05" / "deck" / "build_deck.py")
s05 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s05)

base = s05.base
base.OUTPUT = HERE.parent / "Sesion06-Julian-Fernandez.pdf"
H, W = base.H, base.W


class Deck(s05.Deck):
    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 6 · '
               f"Data-driven AI: análisis y normalización · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=base.CSS)


def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    page.add_redact_annot(fitz.Rect(48, 158, 470, 242), fill=False)
    page.add_redact_annot(fitz.Rect(48, 124, 330, 147), fill=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for y, line in ((191, "Sesión 6: Data-driven AI,"), (232, "análisis y normalización")):
        page.insert_text((51, y), line, fontname="hebo", fontsize=34.5, color=(1, 1, 1))
    page.insert_text((51, 141), "MÓDULO 3: Data-driven AI", fontname="hebo", fontsize=15, color=(1, 1, 1))


# ===========================================================================
# Apertura · Bloque 0 · Bloque 1
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: preparar el corpus antes de vectorizar",
              "Hoy no vectorizamos nada: preparamos los datos para que merezcan serlo", "Apertura")
    d.codigo(p, "Todo lo de hoy vive en <code>estimator/app/ingestion/</code> · rama <code>session_06_live</code> · "
                "los datos de ejemplo en <code>estimator/data/seed/</code> · <b>Interfaz:</b> Swagger "
                "(<code>localhost:8000/docs</code>)")
    pasos = [("Decidir", "CAG, RAG o híbrido", "beige"), ("Catalogar", "qué fuentes entran", "beige"),
             ("Ingerir", "un Document común", "mint"), ("Limpiar", "reparar y validar", "mint"),
             ("Proteger", "PII y GDPR", "lav")]
    for i, (t, s, k) in enumerate(pasos):
        x = 24 + i * 136
        d.box(p, (x, 66, x + 124, 124), f'<div class="t center">{t}</div><div class="center s">{s}</div>', kind=k)
        if i < 4:
            d.arrow(p, x + 125, 95, x + 135, 95)
    bloques = [("0 · Vuestros números del ejercicio", "10'"), ("1 · Errores y pre-flight", "15'"),
               ("2.1 · Decisión arquitectónica", "15'"), ("2.2 · Catálogo de fuentes", "20'"),
               ("2.3 · Ingesta y Document canónico", "20'"), ("2.4 · Limpieza y validación", "15'"),
               ("2.5 · PII y GDPR", "20'"), ("3 · Cierre y puente a la Sesión 7", "5'")]
    for i, (t, m) in enumerate(bloques):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 136 + row * 50
        d.box(p, (x, y, x + 332, y + 42), f"<b>{t}</b> &nbsp;<span class='s'>{m}</span>",
              kind="note" if i in (3, 5, 6) else "beige", pad=5)


def slide_bloque0(d: Deck) -> None:
    p = d.new("¿Qué restricción del CAG se rompió primero?",
              "Un número, no una sensación: tokens, ms, € por turno o un dato olvidado", "Bloque 0")
    d.codigo(p, "Vuestro ejercicio: <code>evals/stress/REPORT.md</code> y <code>results.csv</code> · el evento "
                "<code>turn_observed</code> · las métricas <code>LatencyBudgetMetric</code>, "
                "<code>CostBudgetMetric</code> y <code>MemoryDriftMetric</code>")
    names = [("1 · Ventana de contexto", "¿cabía el corpus?"), ("2 · Coste", "€ por turno"),
             ("3 · Latencia", "P95 frente al SLA"), ("4 · Lost in the middle", "recall del dato del centro")]
    for i, (n, s) in enumerate(names):
        x = 24 + i * 170
        d.box(p, (x, 66, x + 160, 110), f'<div class="t">{n}</div><span class="s">{s}</span>', kind="mint", pad=5)
    d.box(p, (24, 120, 440, 330),
          '<div class="t">Lo que traéis de casa</div>'
          "<table><tr><th>#</th><th>Restricción rota primero</th><th>Número</th><th>Escenario</th></tr>"
          "<tr><td>1</td><td></td><td></td><td></td></tr><tr><td>2</td><td></td><td></td><td></td></tr>"
          "<tr><td>3</td><td></td><td></td><td></td></tr><tr><td>4</td><td></td><td></td><td></td></tr></table>",
          kind="beige", role="table")
    d.box(p, (452, 120, 696, 330),
          '<div class="t">¿Alguien detectó lost in the middle?</div>'
          "Es el fallo más sutil: el modelo <b>siempre responde algo plausible</b>. Solo aparece si se mide el "
          "recall del dato que se puso en el centro del contexto.<br/><br/>"
          "Estos números no son anécdotas: son la justificación de todo el módulo.",
          kind="note")


def slide_errores(d: Deck) -> None:
    p = d.new("Errores típicos: formato, encoding y dependencias", "Antes de construir, que el stack esté sano",
              "Bloque 1")
    d.codigo(p, "scripts/<b>preflight_s06.py</b> · <code>check_spacy_model</code> (l. 109) · <code>CHECKS</code> "
                "(l. 179) · cleaning/<b>budget_records.py</b> · fechas con <code>dayfirst=True</code> (l. 69)")
    d.box(p, (24, 66, 352, 330),
          '<div class="t">Formato y encoding</div><ul>'
          "<li><b>UTF-8 frente a Latin-1</b>: <code>chardet.detect(raw_bytes)</code> y releer.</li>"
          "<li><b>CSV irregular</b>: <code>pd.read_csv(..., sep=\";\", engine=\"python\", "
          "on_bad_lines=\"warn\")</code>.</li>"
          "<li><b>JSON con campos ausentes</b>: <code>payload.get(\"x\")</code> y <code>x: str | None = None</code>.</li>"
          "<li><b>Fechas en varios formatos</b>: <code>pd.to_datetime(s, errors=\"coerce\", dayfirst=True)</code>. "
          "Lo vemos en 2.4.</li></ul>",
          kind="mint")
    d.box(p, (368, 66, 696, 330),
          '<div class="t">Dependencias del stack</div><ul>'
          "<li><b>es_core_news_md</b>: sin él Presidio <b>falla en silencio</b>. Prueba: "
          "<code>nlp(\"Laura Fernández firmó en Madrid.\").ents</code> → PER + LOC.</li>"
          "<li><b>unstructured[all-docs]</b>: cientos de MB la primera vez; para probar, "
          "<code>strategy=\"fast\"</code>.</li>"
          "<li><b>Pandera</b>: <code>import pandera.pandas as pa</code>.</li>"
          "<li><b>Pydantic v2</b>: <code>@field_validator</code> + <code>@classmethod</code> y "
          "<code>@model_validator(mode=\"after\")</code>.</li></ul>",
          kind="lav")


def slide_preflight(d: Deck) -> None:
    p = d.new("Pre-flight: ocho comprobaciones antes de empezar", "Si las ocho pasan, el entorno está listo",
              "Bloque 1")
    d.codigo(p, "scripts/<b>preflight_s06.py</b> · <code>CHECKS</code> (l. 179) · se lanza con "
                "<code>docker compose exec estimator python scripts/preflight_s06.py</code> · sale con código 1 si "
                "alguna falla")
    d.code(p, (24, 66, 430, 330), """Pre-flight Sesión 06

✅  Python version: 3.11.17
✅  Required packages: 12 packages OK
✅  spaCy es_core_news_md: loaded;
      detected PER entities: ['Laura Fernández']
✅  unstructured parsers: unstructured 0.22.29
✅  Corpus seed present: 6 json + 3 txt + 1 xlsx
✅  Catalog validates: version 1.0.0, 1 included
✅  Estimator /health: 200 OK
✅  Postgres + migration: tables OK:
      ['alembic_version', 'ingestion_jobs',
       'pseudonym_mappings']

✅  All checks passed""", "Salida real")
    d.box(p, (442, 66, 696, 196),
          '<div class="t">Por qué un script y no una lista</div>Cada comprobación es una función: si falla, '
          "imprime el motivo en vez de dejaros descubrirlo a mitad de una demo.",
          kind="mint")
    d.box(p, (442, 206, 696, 330),
          '<div class="t">La más importante</div>La de spaCy: comprueba que el modelo en español reconoce a '
          "«Laura Fernández» como persona. Sin eso, la pseudonimización de 2.5 no detecta nombres y nadie se entera.",
          kind="peach")


# ===========================================================================
# 2.1 · Decisión arquitectónica
# ===========================================================================

def slide_restricciones(d: Deck) -> None:
    p = d.new("Las cuatro restricciones del CAG", "Las cuatro en verde a la vez: es un AND, no un OR", "2.1")
    d.codigo(p, "app/ingestion/<b>architecture.py</b> · <code>CAGViability</code> (l. 48) · <code>viable</code> "
                "(l. 57): un <code>all([...])</code> de las cuatro")
    cards = [("Ventana de contexto", "Binaria: si el corpus no cabe, no se puede inyectar.", "beige"),
             ("Coste por consulta", "Crece lineal con los tokens. 3 céntimos es desplegable; 2 €, no.", "beige"),
             ("Latencia", "100.000 tokens tardan segundos. Depende del producto, no de la arquitectura.", "beige"),
             ("Lost in the middle", "Aunque quepa, lo del centro se atiende peor. La más subestimada.", "peach")]
    for i, (t, s, k) in enumerate(cards):
        x = 24 + i * 170
        d.box(p, (x, 66, x + 160, 196), f'<div class="t">{t}</div>{s}', kind=k)
    d.code(p, (24, 206, 420, 330), """@dataclass
class CAGViability:
    context_window_ok: bool
    cost_ok: bool
    latency_ok: bool
    lost_in_the_middle_ok: bool

    @property
    def viable(self) -> bool:
        return all([...las cuatro...])""", "architecture.py")
    d.box(p, (432, 206, 696, 330),
          '<div class="t">Data-driven AI</div>El valor no está en el modelo, que es el mismo para todos, sino en '
          "<b>vuestros datos</b>. Y casi nunca falla solo una restricción.",
          kind="mint")


def slide_architecture(d: Deck) -> None:
    p = d.new("Dónde vive la decisión: architecture.py", "El Article 1 convertido en un módulo que se ejecuta",
              "2.1")
    d.codigo(p, "app/ingestion/<b>architecture.py</b> · <code>assess_cag_viability</code> (l. 98) · "
                "<code>recommend_architecture</code> (l. 114) · <code>PROYECTO_2</code> (l. 141) · "
                "<code>python -m app.ingestion.architecture</code>")
    d.code(p, (24, 66, 360, 196), """def recommend_architecture(corpus, model):
    fits_in_window = (corpus.estimated_tokens
                      <= model.context_window * 0.7)
    cache_friendly = corpus.refresh_frequency_days >= 7
    traceability_doable = not corpus.traceability_required
    access_doable = not corpus.access_control_required""", "Los cuatro ejes de la decisión")
    d.box(p, (372, 66, 696, 196),
          "<table><tr><th>Proyecto 2</th><th></th></tr>"
          "<tr><td>Volumen</td><td><b>250.000 tokens</b></td></tr>"
          "<tr><td>Refresco</td><td>cada 7 días</td></tr>"
          "<tr><td>Trazabilidad</td><td>obligatoria</td></tr>"
          "<tr><td>Control de acceso</td><td>por usuario</td></tr>"
          "<tr><td>Ventana de gpt-4o-mini</td><td><b>128.000 tokens</b></td></tr></table>",
          kind="lav", role="table")
    d.code(p, (24, 206, 470, 330), """Corpus 'Proyecto 2': 250,000 tokens, refresh cada 7 días,
  trazabilidad=True, control_acceso=True
Modelo 'gpt-4o-mini': ventana 128,000 tokens, prefix_caching=True

Viabilidad CAG: NO viable
  Restricciones en rojo: context_window, latency, lost_in_the_middle
Recomendación arquitectónica: RAG""", "Salida real")
    d.box(p, (482, 206, 696, 330),
          '<div class="t">Lectura</div>250.000 tokens no caben ni en el 70 % útil de 128.000. El coste pasa '
          "(hay caché de prefijo y el corpus cambia cada semana), pero tres en rojo: <b>RAG</b>.",
          kind="mint")


def slide_decision(d: Deck) -> None:
    p = d.new("CAG, RAG o híbrido: una decisión defendible", "Lo que hay que poder explicar a un Director de Producto",
              "2.1")
    d.codigo(p, "app/ingestion/<b>architecture.py</b> · <code>recommend_architecture</code> (l. 114): devuelve "
                "<code>\"CAG\"</code>, <code>\"Hybrid\"</code> o <code>\"RAG\"</code>")
    d.image(p, (24, 64, 372, 330), "s06-arbol-cag-rag-hibrido.png")
    d.box(p, (384, 66, 696, 146),
          '<div class="t">Tres opciones, no dos</div>Si el corpus cabe y es estable pero hay que citar o filtrar por '
          "usuario: <b>híbrido</b>. Lo estable por CAG, lo volátil o sensible por RAG.",
          kind="mint")
    d.box(p, (384, 156, 696, 246),
          '<div class="t">Fine-tuning no está en el árbol</div>Es una capa que se suma encima: enseña <i>cómo</i> '
          "responder, no aporta datos ni trazabilidad. <b>Nunca</b> sustituye a un retrieval mal diseñado.",
          kind="lav")
    d.box(p, (384, 256, 696, 330),
          '<div class="t">Y ahora qué</div>Decidido RAG, lo primero <b>no</b> es cargar un parser: es saber qué '
          "vamos a indexar. Eso es el catálogo.",
          kind="note")


# ===========================================================================
# 2.2 · Catálogo de fuentes
# ===========================================================================

def slide_antipatron(d: Deck) -> None:
    p = d.new("Antipatrón: vectorizar primero, mirar después", "Los errores no salen el día 1: salen el día 60", "2.2")
    d.codigo(p, "estimator/<b>data/seed/</b> · <code>budgets/</code> (6 JSON) · <code>transcripts/</code> (3 TXT) · "
                "<code>rate_card_2024.xlsx</code> suelto en la raíz: las fuentes del Proyecto 2")
    fallos = [("Mezcla silenciosa de versiones", "La propuesta inicial y la firmada conviven; se recupera la "
                                                 "equivocada porque nada las distingue.", "peach"),
              ("Fuentes podridas", "Documentos válidos pero obsoletos (tarifas, políticas) que dan respuestas "
                                   "seguras y falsas.", "peach"),
              ("Huecos invisibles", "Responde bien donde hay datos e inventa algo plausible donde no los hay.",
               "peach")]
    for i, (t, s, k) in enumerate(fallos):
        x = 24 + i * 226
        d.box(p, (x, 66, x + 216, 186), f'<div class="t">{t}</div>{s}', kind=k)
    d.box(p, (24, 196, 352, 330),
          '<div class="t">El caos documental</div>Presupuestos en Drive, transcripciones en Dropbox '
          "(<code>meeting_final_v3_FINAL.txt</code>), un Excel de tarifas que nadie sabe si sigue vigente. "
          "Sin digitalizar y ordenar antes, la IA no tiene de dónde leer.",
          kind="beige")
    d.box(p, (368, 196, 696, 330),
          '<div class="t">Por dónde empezar</div>Por el <b>inventario</b>: qué hay, dónde, de quién, cada cuánto se '
          "actualiza y con qué calidad. Las tres causas tienen la misma raíz: nadie miró lo que había.",
          kind="mint")


def slide_inspeccion(d: Deck) -> None:
    p = d.new("Inspeccionar: hechos antes que opiniones", "El censo mide lo medible; la calidad la decide una persona",
              "2.2")
    d.codigo(p, "app/ingestion/catalog/<b>inspect.py</b> · <code>FolderFacts</code> (l. 31) · "
                "<code>inspect_root</code> (l. 68) · <code>python -m app.ingestion.catalog.inspect data/seed</code>")
    d.code(p, (24, 66, 696, 136), """budgets       6 files  0.00 MB  latest=2026-10-14T13:18:12+00:00  formats=json
transcripts   3 files  0.00 MB  latest=2026-10-14T13:18:12+00:00  formats=txt
seed          1 files  0.01 MB  latest=2024-01-12T09:00:00+00:00  formats=xlsx""", "Salida real")
    dims = [("Completitud", "¿Qué % cumple el esquema?"), ("Consistencia", "¿EUR, eur, € y euros a la vez?"),
            ("Actualidad", "¿Cuándo fue el último dato?"), ("Fiabilidad", "¿Fuente autoritativa o una copia?")]
    for i, (t, s) in enumerate(dims):
        x = 24 + i * 170
        d.box(p, (x, 146, x + 160, 220), f'<div class="t">{t}</div>{s}', kind="lav", pad=5)
    d.box(p, (24, 230, 352, 330),
          '<div class="t">La fuente podrida</div>El Excel de tarifas se tocó por última vez el <b>12/01/2024</b>. '
          "Si se declara «anual», hace casi dos años que no se cumple.",
          kind="peach")
    d.box(p, (368, 230, 696, 330),
          '<div class="t">No se promedia</div>Cada dimensión va de 1 a 5 y todas son necesarias: completitud 5 y '
          "fiabilidad 1 no es «calidad 3», son datos completos que pueden ser mentira.",
          kind="note")


def slide_catalogo(d: Deck) -> None:
    p = d.new("El catálogo es código, no documentación", "Un YAML versionado que la ingesta lee para decidir", "2.2")
    d.codigo(p, "catalog/<b>models.py</b> · <code>CatalogDecision</code> (l. 33) · "
                "<code>_decision_requires_reason_when_not_include</code> (l. 95) · data/catalog/<b>catalog.yaml</b> "
                "(l. 33, 58, 86) · catalog/<b>loader.py</b> (l. 28)")
    d.code(p, (24, 66, 352, 186), """class CatalogDecision(str, Enum):
    INCLUDE = "include"
    REVIEW  = "review"     # la tercera vía
    EXCLUDE = "exclude"

@model_validator(mode="after")
def _decision_requires_reason_when_not_include(self):
    # si no es include, el motivo es obligatorio""", "models.py · contrato Pydantic")
    d.code(p, (368, 66, 696, 186), """$ python -m app.ingestion.catalog.loader \\
      data/catalog/catalog.yaml
Catalog version: 1.0.0
Sources total:  3
Sources included: 1
  - presupuestos_json (json)""", "Salida real")
    d.box(p, (24, 196, 696, 290),
          "<table><tr><th>Fuente</th><th>Decisión</th><th>Motivo</th></tr>"
          "<tr><td>presupuestos_json</td><td class='k'>include</td><td>fuente principal; tiene PII → "
          "se pseudonimiza</td></tr>"
          "<tr><td>transcripciones_txt</td><td><b>review</b></td><td>un fichero de 2023 sin speaker tags rompe el "
          "parser por defecto</td></tr>"
          "<tr><td>rate_card_xlsx</td><td class='r'>exclude</td><td>actuality=1: tarifas de enero de 2024</td></tr>"
          "</table>",
          kind="beige", role="table")
    d.box(p, (24, 298, 696, 336),
          "Excluir con el motivo escrito es disciplina, no desidia. El <code>git log</code> del YAML dice quién "
          "decidió qué y por qué.",
          kind="mint", pad=5)


# ===========================================================================
# 2.3 · Ingesta
# ===========================================================================

def slide_capas(d: Deck) -> None:
    p = d.new("Tres capas y un contrato: el Document", "Venga de JSON, TXT, XLSX o PDF, sale lo mismo", "2.3")
    d.codigo(p, "documents/<b>models.py</b> · <code>DocumentMetadata</code> (l. 30) · <code>Document</code> (l. 43) · "
                "loaders/<b>filesystem.py</b> · <code>iter_blobs</code> (l. 37) · parsers/<b>protocol.py</b> · "
                "<code>Parser</code> (l. 46)")
    capas = [("Loader", "Cómo llego al fichero: disco, Drive, S3. Entrega bytes y no sabe qué hay dentro."),
             ("Parser", "Qué hay dentro: uno por formato, todos con la misma firma."),
             ("Document", "El contrato común: texto + metadatos. Lo único que verá la Sesión 7.")]
    for i, (t, s) in enumerate(capas):
        x = 24 + i * 226
        d.box(p, (x, 66, x + 204, 150), f'<div class="t">{t}</div>{s}', kind="mint" if i < 2 else "lav")
        if i < 2:
            d.arrow(p, x + 205, 108, x + 225, 108)
    d.code(p, (24, 160, 352, 330), """class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: str
    metadata: DocumentMetadata

class DocumentMetadata(BaseModel):
    source_name: str
    source_version: str   # versión del catálogo
    ingested_at: datetime
    lineage: list[str]
    sensitivity_pii_flags: list[str]
    extra: dict[str, Any]   # lo propio del formato""", "documents/models.py")
    d.box(p, (368, 160, 696, 240),
          '<div class="t">extra="forbid"</div>Si un parser cuela un campo no declarado, Pydantic falla. '
          "Un error fuerte es mejor que uno silencioso.",
          kind="beige")
    d.box(p, (368, 250, 696, 330),
          '<div class="t">Parser es un Protocol</div>Tipado estructural, sin herencia: cualquier clase con '
          "<code>parse(blob, context)</code> vale. Añadir un formato es registrar una clase.",
          kind="note")


def slide_parsers(d: Deck) -> None:
    p = d.new("Un parser por formato, cada uno con su estrategia", "JSON y TXT en el repo; XLSX, DOCX y PDF siguen el "
              "mismo patrón", "2.3")
    d.codigo(p, "parsers/<b>budget_json.py</b> · <code>_render_budget_markdown</code> (l. 59) · "
                "parsers/<b>transcript_txt.py</b> · <code>_parse_tagged</code> (l. 54) · <code>_parse_legacy</code> "
                "(l. 76) · parsers/<b>registry.py</b> (l. 45)")
    d.box(p, (24, 66, 352, 200),
          '<div class="t">JSON → Markdown, no json.dumps</div>Un JSON no se extrae: se decide cómo representarlo. '
          "El embedding entiende mejor <code>## Cliente · BetaNorte</code> que "
          "<code>{\"client_name\": \"BetaNorte\"}</code>.",
          kind="mint")
    d.box(p, (368, 66, 696, 200),
          '<div class="t">TXT: un formato, dos modos</div><ul>'
          "<li><b>Con etiquetas</b> <code>[hh:mm:ss] Speaker:</code> → un Document por turno, con speaker.</li>"
          "<li><b>Legacy</b> (2023, sin etiquetas) → un Document por bloque, <b>sin speaker</b>: no se inventa.</li>"
          "</ul>",
          kind="lav")
    d.box(p, (24, 210, 696, 330),
          "<table><tr><th>Formato</th><th>Estrategia</th></tr>"
          "<tr><td>XLSX</td><td>tabla limpia → tabla Markdown; celdas combinadas o varias tablas por hoja → fuera o "
          "a mano</td></tr>"
          "<tr><td>DOCX</td><td><code>python-docx</code>: un Document por sección, con el título como metadato</td></tr>"
          "<tr><td>PDF</td><td><code>pypdf</code> por defecto; <code>unstructured</code> <i>hi_res</i> solo si hay "
          "tablas o escaneo, decidido una vez por fuente en el catálogo</td></tr></table>",
          kind="beige", role="table")


def slide_ingesta(d: Deck) -> None:
    p = d.new("La ingesta es offline: 202 y un job", "Indexar tarda; la petición no espera", "2.3")
    d.codigo(p, "routers/<b>ingestion.py</b> · <code>create_ingestion_run</code> (l. 86) · "
                "<code>get_ingestion_job</code> (l. 128) · <b>orchestrator.py</b> · <code>ingest_source</code> "
                "(l. 51) · <b>Interfaz:</b> Swagger, sección <i>ingestion</i>")
    d.image(p, (24, 64, 330, 150), "s06-ui-swagger.png")
    d.code(p, (24, 158, 330, 330), """POST /api/v1/ingestion/runs
{"source_name": "presupuestos_json"}
→ 202  job_id: 95f56fd1-…  status: pending

GET /api/v1/ingestion/jobs/95f56fd1-…
→ status: completed  documents_count: 6

rate_card_xlsx → 400 source_not_included
no_existe      → 404 unknown_source""", "Salida real")
    d.image(p, (342, 64, 696, 214), "s06-pipeline-offline-online.png")
    d.box(p, (342, 222, 696, 270),
          '<div class="t">Offline frente a online</div>Indexar es por lotes, sin usuario esperando. La consulta de '
          "la Sesión 7 será síncrona y rápida.",
          kind="lav", pad=5)
    d.box(p, (342, 278, 696, 330),
          '<div class="t">El catálogo manda</div>La 400 trae el motivo del YAML: «actuality=1 — fichero del '
          "12/01/2024 con tarifas obsoletas».",
          kind="note", pad=5)


def slide_madurez(d: Deck) -> None:
    p = d.new("La madurez documental marca el techo de precisión", "Lo que conviene saber antes de prometer nada",
              "2.3")
    d.codigo(p, "La calidad declarada en data/catalog/<b>catalog.yaml</b> (bloques <code>quality</code>) · lo que "
                "sube del 60 al 80 % es lo de hoy: <code>catalog/</code>, <code>parsers/</code>, "
                "<code>cleaning/</code> y <code>pii/</code>")
    steps = [("~60 %", "Fácil", "Un RAG directo sobre los documentos tal cual. Impresiona en la demo.", "peach"),
             ("60 → 80 %", "Un salto enorme", "Catálogo, Document común, limpieza, validación y PII: lo que vemos "
                                              "hoy.", "lav"),
             ("≈ 100 %", "Meses de trabajo, o imposible", "Sin errores en un RAG o un agente: mucha iteración, o "
                                                          "inalcanzable por la propia naturaleza de la IA.", "mint")]
    for i, (pct, name, desc, k) in enumerate(steps):
        y = 66 + i * 90
        d.box(p, (24, y, 420, y + 82), f'<div class="huge">{pct}</div><b>{name}</b> · {desc}', kind=k)
    d.box(p, (432, 66, 696, 196),
          '<div class="t">La casa no se empieza por el tejado</div>Documentos sueltos en Word, carpetas sin orden, '
          "ERPs de hace veinte años: sin digitalizar y ordenar, la IA no tiene de dónde leer.",
          kind="beige")
    d.box(p, (432, 206, 696, 330),
          '<div class="t">Por qué importa</div>Si no se sabe desde el principio, llegan las quejas del cliente y del '
          "jefe de proyecto, y la culpa acaba siendo «de la IA».",
          kind="note")


# ===========================================================================
# 2.4 · Limpieza y validación
# ===========================================================================

def slide_suciedad(d: Deck) -> None:
    p = d.new("Cuatro familias de suciedad", "El Document garantiza la forma; nada garantiza todavía el contenido",
              "2.4")
    d.codigo(p, "data/seed/budgets/ · <b>BUDGET-2024-0002.json</b> (moneda «eur», fecha 12/03/2024) · <b>…0003</b> "
                "(«TBD») · <b>…0004</b> (−50000) · <b>…0005-v1 / v2</b> · cleaning/<b>budget_records.py</b> · "
                "<code>NULL_PLACEHOLDERS</code> (l. 44)")
    d.box(p, (24, 66, 696, 246),
          "<table><tr><th>Familia</th><th>En nuestros datos</th><th>Cómo daña al RAG</th></tr>"
          "<tr><td><b>Formato heterogéneo</b></td><td><code>\"eur\"</code> y <code>\"EUR\"</code>; "
          "<code>12/03/2024</code> y <code>2024-06-21</code></td><td>cada variante es un token distinto</td></tr>"
          "<tr><td><b>Duplicados divergentes</b></td><td>BUDGET-2024-0005 en v1 y v2</td>"
          "<td>se recupera la que se indexó primero</td></tr>"
          "<tr><td><b>Nulos disfrazados</b></td><td><code>\"client_name\": \"TBD\"</code>, "
          "<code>\"contact\": \"N/A\"</code></td><td>se vectorizan como si fueran un dato</td></tr>"
          "<tr><td><b>Fuera de rango</b></td><td><code>\"total_amount\": -50000</code></td>"
          "<td>respuestas muy seguras sobre un absurdo</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 256, 696, 330),
          '<div class="t">En un solo sitio</div>La limpieza y la validación viven en un módulo, entre el parser y el '
          "Document, no repartidas en parches por el chunker, el embedder y el retriever. Así se pueden auditar, "
          "testear y parar el pipeline cuando algo falla.",
          kind="mint")


def slide_limpiar_validar(d: Deck) -> None:
    p = d.new("Limpiar y validar son dos pasos distintos", "Limpieza permisiva que repara · validación estricta que "
              "decide", "2.4")
    d.codigo(p, "cleaning/<b>budget_records.py</b> (l. 47; fechas l. 69; dedup l. 79) · cleaning/<b>schemas.py</b> · "
                "<code>BudgetRecord</code> (l. 30) · cleaning/<b>policy.py</b> · <code>QUARANTINE_CHECKS</code> "
                "(l. 40) · <code>DISCARD_CHECKS</code> (l. 45) · <code>lazy=True</code> (l. 73)")
    d.code(p, (24, 66, 352, 160), """# 1 · limpiar: repara, no juzga
df["signed_at"] = pd.to_datetime(df["signed_at"],
                      errors="coerce", dayfirst=True)
df = (df.sort_values(["budget_id", "signed_at"])
        .drop_duplicates("budget_id", keep="last"))""", "budget_records.py")
    d.code(p, (368, 66, 696, 160), """# 2 · validar: el contrato (Pandera)
"total_amount": Column(float,
    checks=[Check.ge(0), Check.le(10_000_000)]),
"currency": Column(str, checks=Check.isin(
    ["EUR", "USD", "GBP"])),
strict=True, coerce=False""", "schemas.py")
    d.code(p, (24, 170, 352, 252), """# 3 · la política: tres cubetas
QUARANTINE_CHECKS = {"not_nullable", ...}
DISCARD_CHECKS = {"greater_than_or_equal_to",
                  "isin", "str_matches", ...}
BudgetRecord.validate(df, lazy=True)""", "policy.py")
    d.box(p, (368, 170, 696, 252),
          "<table><tr><td class='k'>Reparar</td><td>sin pérdida de significado y sin humano</td></tr>"
          "<tr><td><b>Cuarentena</b></td><td>grave pero útil tras revisión: no entra al RAG</td></tr>"
          "<tr><td class='r'>Descartar</td><td>contaminación clara: fuera, con log</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 262, 696, 330),
          '<div class="t">Para defender</div><code>errors="coerce"</code>: lo inválido pasa a nulo y la validación '
          "decide · <code>lazy=True</code> recoge <b>todos</b> los errores, no solo el primero · «la versión más "
          "reciente gana» es una regla de negocio escrita en código · el contrato es estricto siempre; lo que se "
          "relaja es la política.",
          kind="mint")


def slide_demo_limpieza(d: Deck) -> None:
    p = d.new("Demo: lo que sale de verdad", "Seis presupuestos de entrada, tres válidos de salida", "2.4")
    d.codigo(p, "scripts/<b>demo_cleaning_s06.py</b> · <code>main</code> (l. 43) · se lanza con "
                "<code>docker compose exec estimator python scripts/demo_cleaning_s06.py</code>")
    d.code(p, (24, 66, 360, 330), """Ficheros leídos: 6  (/app/data/seed/budgets)
UserWarning: Parsing dates in %Y-%m-%d format
  when dayfirst=True was specified.
Filas tras limpieza + dedup: 5

Report:
  input_rows: 5
  valid_rows: 3
  quarantined_rows: 1
  discarded_rows: 1

Descartadas:
       budget_id  total_amount
BUDGET-2024-0004        -50000

En cuarentena:
       budget_id            client_name
BUDGET-2024-0002 BetaNorte Distribución""", "Salida real")
    d.box(p, (372, 66, 696, 136),
          '<div class="t">6 ficheros → 5 filas</div>El dedup juntó las dos versiones de BUDGET-2024-0005 y se quedó '
          "con la v2, la firmada después.",
          kind="mint")
    d.box(p, (372, 144, 696, 246),
          '<div class="t">¿Por qué cuarentena el 0002 y no el «TBD»?</div>Su fecha es <code>12/03/2024</code> y la '
          "del resto <code>2024-…</code>. pandas deduce el formato de la primera fila, la del 0002 no encaja → "
          "<code>NaT</code> → falla <code>not_nullable</code>. El «TBD» pasa porque <code>client_name</code> admite "
          "nulos.",
          kind="note")
    d.box(p, (372, 254, 696, 330),
          '<div class="t">La lección</div>La limpieza no pudo reparar esa fecha y la validación la cazó. Por eso son '
          "dos pasos: uno repara, el otro decide.",
          kind="peach")


# ===========================================================================
# 2.5 · PII y GDPR
# ===========================================================================

def slide_filtraciones(d: Deck) -> None:
    p = d.new("PII: tres formas de filtrar datos a través de un RAG", "El control de acceso no basta: el vector no "
              "sabe qué es sensible", "2.5")
    d.codigo(p, "app/ingestion/<b>pii/</b> · <code>analyzer.py</code> · <code>recognizers.py</code> · "
                "<code>pseudonymizer.py</code> · <code>mapping_store.py</code> · la protección va <b>antes</b> del "
                "embedding")
    modos = [("Directa", "«¿Qué clientes nos contrataron migraciones a cloud?» → los nombres, literales en los "
                         "chunks.", "peach"),
             ("Por agregación", "Preguntas inocentes que juntas reconstruyen el mapa: el proyecto más caro de 2024, "
                                "su sector, su stack.", "peach"),
             ("Por inferencia", "Tras «[PERSON], CEO de [ORG]» quedan sector, fechas e importes: basta para "
                                "identificar a alguien.", "peach")]
    for i, (t, s, k) in enumerate(modos):
        x = 24 + i * 226
        d.box(p, (x, 66, x + 216, 186), f'<div class="t">{t}</div>{s}', kind=k)
    d.box(p, (24, 196, 352, 330),
          '<div class="t">GDPR mínimo</div><ul>'
          "<li><b>Dato personal</b>: lo que identifica a una persona, también por combinación.</li>"
          "<li><b>Pseudonimizar</b> sigue siendo dato personal (hay un mapeo); <b>anonimizar</b> es irreversible.</li>"
          "<li><b>Minimización</b>: el estimador necesita patrones, no nombres reales.</li></ul>",
          kind="lav")
    d.box(p, (368, 196, 696, 330),
          '<div class="t">Pseudonimizar, no tachar</div>Cambiar «Javier Romero» por <code>[PERSON]</code> rompe la '
          "semántica; cambiarlo por otro nombre verosímil, y siempre el mismo, la conserva. Pruebas internas dan "
          "caídas del 15-25 % en retrieval al tachar.",
          kind="mint")


def slide_presidio(d: Deck) -> None:
    p = d.new("Empezar por el fallo: Presidio en inglés", "Por defecto no detecta «Laura Fernández», y no avisa",
              "2.5")
    d.codigo(p, "pii/<b>analyzer.py</b> · <code>build_analyzer</code> (l. 37) · pii/<b>recognizers.py</b> · "
                "<code>BudgetIdRecognizer</code> (l. 28) · <code>ClientCodeRecognizer</code> (l. 46) · "
                "<code>PRESIDIO_SPACY_MODEL</code> en <code>app/config.py</code>")
    d.box(p, (24, 66, 330, 196),
          '<div class="t">Lo que pasa por defecto</div>Presidio monta spaCy <b>en inglés</b>. Sobre nombres '
          "españoles devuelve <b>cero</b> personas, y el pipeline parece funcionar. En producción alguien pregunta "
          "por un cliente y el nombre sale en claro.",
          kind="peach")
    d.code(p, (342, 66, 696, 230), """@lru_cache                     # spaCy tarda en cargar
def build_analyzer() -> AnalyzerEngine:
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "es",
                    "model_name": "es_core_news_md"}]})
    engine = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        supported_languages=["es"])
    engine.registry.add_recognizer(BudgetIdRecognizer())
    engine.registry.add_recognizer(ClientCodeRecognizer())
    return engine""", "analyzer.py · la corrección")
    d.box(p, (24, 206, 330, 330),
          '<div class="t">Reconocedores del dominio</div><code>BUDGET-\\d{4}-\\d{4}</code> y '
          "<code>CLI-\\d{4}</code> con score 0,95. Presidio trae personas, emails o lugares de serie; nuestros "
          "identificadores, no.",
          kind="lav")
    d.box(p, (342, 240, 696, 330),
          '<div class="t">Comprobado en el pre-flight</div><code>detected PER entities: [\'Laura Fernández\']</code>. '
          "Si esa línea sale en rojo, no sigas: la demo de PII no detectaría nombres.",
          kind="mint")


def slide_demo_pii(d: Deck) -> None:
    p = d.new("Demo: mismo valor, mismo pseudónimo", "La transcripción de BetaNorte, antes y después", "2.5")
    d.codigo(p, "pii/<b>pseudonymizer.py</b> · <code>ConsistentPseudonymizer</code> (l. 60) · <code>_generators</code> "
                "(l. 78) · derecha a izquierda (l. 103) · <code>_hash</code> (l. 130) · scripts/<b>demo_pii_s06.py</b> "
                "(l. 52)")
    d.code(p, (24, 66, 352, 160), """[09:15:02] Javier Romero: Buenas. Estamos revisando el
presupuesto BUDGET-2024-0002 firmado en marzo, código de
cliente CLI-0078. Quería preguntar por el escalado…
[09:15:40] Diego Marín: Sí, lo tengo aquí.""", "Antes · data/seed/transcripts/…betanorte.txt")
    d.code(p, (368, 66, 696, 160), """[09:15:02] Pánfilo del Barros: Buenas. Estamos revisando
el presupuesto BUDGET-2023-5601 firmado en marzo, código
de cliente Apolinar Montero Verdejo. Samu de Samper
preguntar por el escalado…
[09:15:40] Álvaro Girona, lo tengo aquí.""", "Después · salida real")
    d.code(p, (24, 170, 352, 258), """--- Mappings aplicados (20) ---
  PERSON         → Purificación Rivero Arjona
  ORGANIZATION   → REDACTED-7c65c1e5
  EMAIL_ADDRESS  → dalila38@instalaciones.org
  URL            → REDACTED-e61a441c
  LOCATION       → Teruel""", "Salida real (extracto)")
    d.box(p, (368, 170, 696, 258),
          '<div class="t">Por qué así</div><ul>'
          "<li>Un generador <b>por tipo</b>: un nombre por un nombre, un email por un email.</li>"
          "<li>Se reemplaza de derecha a izquierda: las posiciones no se desplazan.</li>"
          "<li>Se guarda el <b>hash</b> (HMAC-SHA256), nunca el valor original.</li></ul>",
          kind="mint")
    d.box(p, (24, 266, 696, 330),
          '<div class="t">Falsos positivos (saldrán)</div>«Quería» y «Sí» se tomaron por personas, y el código '
          "<code>CLI-0078</code> acabó sustituido por un nombre: se detectó como persona y no como código de "
          "cliente. Es el precio del NER en "
          "español: en producción, subir el umbral, una lista de exclusión o <code>es_core_news_lg</code>.",
          kind="note")


def slide_olvido(d: Deck) -> None:
    p = d.new("Derecho al olvido (GDPR art. 17)", "Sin la mapping table, borrar a una persona es imposible",
              "2.5")
    d.codigo(p, "pii/<b>mapping_store.py</b> · <code>PostgresMappingStore</code> (l. 50) · <code>forget</code> "
                "(l. 69) · persistence/<b>models.py</b> · <code>PseudonymMappingRow</code> (l. 40) · "
                "<code>UniqueConstraint</code> (l. 43)")
    steps = ["Buscar en la mapping store todos los pseudónimos de la persona (con sus variantes).",
             "Localizar en el índice los chunks que los contienen.",
             "Borrar esos chunks del índice vectorial.",
             "Borrar sus entradas de la mapping store: si reaparece, recibe un pseudónimo nuevo.",
             "Dejarlo en un registro de auditoría: atendido en plazo y forma."]
    for i, s in enumerate(steps):
        y = 66 + i * 54
        d.box(p, (24, y, 420, y + 46), f"<b>{i + 1}</b> · {s}", kind="lav", pad=6)
    d.code(p, (432, 66, 696, 196), """UniqueConstraint(
    "entity_type", "original_hash",
    name="uq_mappings_entity_hash")

# se guarda el hash, NUNCA el valor""", "persistence/models.py")
    d.box(p, (432, 206, 696, 330),
          '<div class="t">Un almacén aparte</div>La tabla de mapeo vive separada del corpus, con su propio control '
          "de acceso. La demo usa un almacén en memoria: por eso la tabla de Postgres sale vacía.",
          kind="note")


# ===========================================================================
# Cierre
# ===========================================================================

def slide_cierre(d: Deck) -> None:
    p = d.new("Cinco piezas: el corpus ya es defendible", "Ante legal, comercial, técnico y regulatorio", "Cierre")
    d.codigo(p, "Todo en <code>estimator/app/ingestion/</code>: <code>architecture.py</code> · <code>catalog/</code> · "
                "<code>loaders/</code> + <code>parsers/</code> + <code>orchestrator.py</code> · <code>cleaning/</code> · "
                "<code>pii/</code>")
    d.box(p, (24, 66, 696, 236),
          "<table><tr><th>#</th><th>Pieza</th><th>Dónde vive</th></tr>"
          "<tr><td>1</td><td>Decisión arquitectónica: RAG</td><td><code>architecture.py</code></td></tr>"
          "<tr><td>2</td><td>Catálogo versionado, tres fuentes auditadas</td><td><code>data/catalog/catalog.yaml</code> "
          "+ <code>catalog/</code></td></tr>"
          "<tr><td>3</td><td>Ingesta con Document canónico y endpoint asíncrono</td><td><code>loaders/ parsers/ "
          "orchestrator.py</code></td></tr>"
          "<tr><td>4</td><td>Limpieza, Pandera y reparar / cuarentena / descartar</td><td><code>cleaning/</code></td></tr>"
          "<tr><td>5</td><td>Pseudonimización y mapping table</td><td><code>pii/</code> + <code>persistence/</code></td>"
          "</tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 246, 352, 330),
          '<div class="t">Eso es data-driven AI</div>La exclusión del Excel, la cuarentena, la regla del dedup y el '
          "modelo en español tienen su motivo, y está escrito en el repo.",
          kind="mint")
    d.box(p, (368, 246, 696, 330),
          '<div class="t">Sesión 7</div><b>Chunking, embeddings y espacio vectorial.</b> Partimos los Documents, los '
          "embebemos y los guardamos en pgvector.",
          kind="lav")


# ===========================================================================

def build() -> None:
    d = Deck()
    cover(d)
    slide_hoy(d)
    slide_bloque0(d)
    slide_errores(d)
    slide_preflight(d)
    slide_restricciones(d)
    slide_architecture(d)
    slide_decision(d)
    slide_antipatron(d)
    slide_inspeccion(d)
    slide_catalogo(d)
    slide_capas(d)
    slide_parsers(d)
    slide_ingesta(d)
    slide_madurez(d)
    slide_suciedad(d)
    slide_limpiar_validar(d)
    slide_demo_limpieza(d)
    slide_filtraciones(d)
    slide_presidio(d)
    slide_demo_pii(d)
    slide_olvido(d)
    slide_cierre(d)
    d.template(10)  # ROTI
    d.template(11)  # gracias
    d.save()


if __name__ == "__main__":
    build()
