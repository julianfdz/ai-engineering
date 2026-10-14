"""Genera el deck de la Sesión 6 personalizado para Julián Fernández.

Reutiliza la plantilla oficial de LIDR (portada, las 11 diapos de contenido,
ROTI y cierre) y le intercala diapos propias que siguen el guion del directo:
código de cada pieza, salida real de las demos, defensa oral y chuleta.

    python build_deck.py
    # → ../Sesion06-Julian-Fernandez.pdf         (alumnos: sin notas internas)
    # → ../Sesion06-Julian-Fernandez-MENTOR.pdf  (Julián: guion en la franja + chuleta)

Para iterar: cambia el contenido de las funciones ``slide_*`` y vuelve a lanzar.
"""

from __future__ import annotations

import html
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "plantilla-lidr-s06.pdf"
ASSETS = HERE.parent.parent.parent / "assets"
OUTPUT_PUBLIC = HERE.parent / "Sesion06-Julian-Fernandez.pdf"          # la que ven los alumnos
OUTPUT_MENTOR = HERE.parent / "Sesion06-Julian-Fernandez-MENTOR.pdf"   # solo para Julián: notas del guion

SECTIONS = {
    "Bloque 0": "Apertura", "Bloque 1": "Resolución de dudas", "Bloque 2": "Las cinco piezas",
    "Bloque 3": "Cierre", "2.1": "2.1 · Decisión arquitectónica", "2.2": "2.2 · Catálogo de fuentes",
    "2.3": "2.3 · Ingesta y Document canónico", "2.4": "2.4 · Limpieza y validación",
    "2.5": "2.5 · PII y pseudonimización", "Apéndice": "Apéndice",
}

W, H = 720, 405
BADGE = fitz.Rect(7, 7, 72, 35)

PALETTE = {
    "mint": ("#e5f3ec", "#4a9a78", "#0f5a40"),
    "lav": ("#eeedfb", "#6d64c7", "#33298a"),
    "peach": ("#fbeae4", "#c97a62", "#7a2e1a"),
    "beige": ("#f3f0ea", "#a39c8e", "#3a362f"),
    "code": ("#f7f7f5", "#c9c6bf", "#2a2a2a"),
    "note": ("#fff7dc", "#d9b54a", "#5c4a12"),
}

CSS = """
* { font-family: sans-serif; }
body { margin: 0; color: #2b2b2b; font-size: 10pt; line-height: 1.32; }
h1 { font-size: 16.5pt; font-weight: normal; text-align: center; margin: 0; color: #222; }
.sub { font-size: 9.5pt; text-align: center; color: #666; margin-top: 3pt; }
.t { font-weight: bold; font-size: 11pt; margin-bottom: 2pt; }
.s { color: #555; font-size: 9pt; }
.mono, code, pre { font-family: monospace; font-size: 8.3pt; }
pre { margin: 0; white-space: pre-wrap; line-height: 1.25; }
ul { margin: 2pt 0 0 0; padding-left: 12pt; }
li { margin-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; }
td, th { border-bottom: 0.5pt solid #ddd; padding: 2.5pt 4pt; text-align: left; vertical-align: top; font-size: 9.5pt; }
th { color: #555; font-weight: bold; border-bottom: 0.8pt solid #999; }
.k { color: #0f5a40; font-weight: bold; }
.r { color: #a33a1e; font-weight: bold; }
.big { font-size: 13pt; }
.center { text-align: center; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


class Deck:
    def __init__(self, mentor: bool) -> None:
        self.mentor = mentor
        self.tpl = fitz.open(TEMPLATE)
        self.doc = fitz.open()
        self.archive = fitz.Archive(str(ASSETS))

    # ---- piezas básicas -------------------------------------------------
    def template(self, pno: int, cue: str | None = None) -> fitz.Page:
        self.doc.insert_pdf(self.tpl, from_page=pno, to_page=pno)
        page = self.doc[-1]
        if cue:
            self.footer(page, cue)
        return page

    def new(self, title: str, sub: str = "", cue: str = "") -> fitz.Page:
        page = self.doc.new_page(width=W, height=H)
        page.show_pdf_page(BADGE, self.tpl, 1, clip=BADGE)
        head = f"<h1>{title}</h1>" + (f'<div class="sub">{sub}</div>' if sub else "")
        page.insert_htmlbox(fitz.Rect(80, 16, W - 80, 62), head, css=CSS)
        if cue:
            self.footer(page, cue)
        return page

    def footer(self, page: fitz.Page, cue: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        if self.mentor:
            left = f"<b>GUION</b> · {cue}"
        else:
            # Versión alumnos: solo la sección, nunca las notas internas del guion.
            left = SECTIONS.get(cue.split(" · ")[0], "")
        txt = (
            f'<div style="font-size:6.8pt;color:#6b655b">{left}'
            f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 6 · Data-driven AI · '
            f'{len(self.doc)}</span></div>'
        )
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=CSS)

    def box(self, page: fitz.Page, rect: tuple, body: str, kind: str = "beige", pad: float = 6) -> None:
        r = fitz.Rect(rect)
        fill, stroke, ink = PALETTE[kind]
        page.draw_rect(r, color=_hex(stroke), fill=_hex(fill), width=0.7, radius=0.06)
        inner = fitz.Rect(r.x0 + pad, r.y0 + pad - 1, r.x1 - pad, r.y1 - pad + 1)
        page.insert_htmlbox(inner, f'<div style="color:{ink}">{body}</div>', css=CSS,
                            archive=self.archive, scale_low=0.55)

    def html(self, page: fitz.Page, rect: tuple, body: str) -> None:
        page.insert_htmlbox(fitz.Rect(rect), body, css=CSS, archive=self.archive, scale_low=0.55)

    def code(self, page: fitz.Page, rect: tuple, src: str, label: str = "") -> None:
        head = f'<div class="s" style="margin-bottom:2pt"><b>{label}</b></div>' if label else ""
        self.box(page, rect, head + f"<pre>{esc(src)}</pre>", kind="code", pad=5)

    def image(self, page: fitz.Page, rect: tuple, name: str) -> None:
        """Inserta un PNG recortando el margen blanco para aprovechar el hueco."""
        from io import BytesIO
        from PIL import Image, ImageChops
        im = Image.open(ASSETS / name).convert("RGB")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bbox = ImageChops.difference(im, bg).point(lambda v: 255 if v > 12 else 0).getbbox()
        if bbox:
            m = 12
            im = im.crop((max(bbox[0] - m, 0), max(bbox[1] - m, 0),
                          min(bbox[2] + m, im.width), min(bbox[3] + m, im.height)))
        buf = BytesIO()
        im.save(buf, format="PNG")
        page.insert_image(fitz.Rect(rect), stream=buf.getvalue(), keep_proportion=True)

    def save(self) -> None:
        out = OUTPUT_MENTOR if self.mentor else OUTPUT_PUBLIC
        self.doc.save(out, garbage=4, deflate=True)
        print(f"{out.name}: {len(self.doc)} diapos")


def _hex(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ===========================================================================
# Diapos
# ===========================================================================

def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    old = fitz.Rect(54, 280, 420, 307)
    page.add_redact_annot(old, fill=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_text((56, 301), "Mentor: Julián Fernández", fontname="helv", fontsize=22, color=(1, 1, 1))


def slide_about(d: Deck) -> None:
    p = d.new("Quién os acompaña hoy", "Sesión 6 · Módulo 3 · Data-driven AI",
              "Bloque 0 · 0:00 · presentación rápida, 1 minuto máximo")
    d.box(p, (60, 80, 400, 300),
          '<div class="t big">Julián Fernández</div>'
          '<div class="s">Informático · fundador de Búho AI</div>'
          "<ul>"
          "<li>Transformo operativas complejas en procesos eficientes con IA y software a medida.</li>"
          "<li>Profesor de IA en LIDR, EBF y UCAM HiTech.</li>"
          "<li>Enfoque <b>transparente y ético</b>: si no sabemos un dato, no lo inventamos "
          "— que es justo la metanorma de hoy.</li>"
          "</ul>"
          '<div class="s" style="margin-top:6pt">linkedin.com/in/julianfernandez-iaenmurcia</div>',
          kind="mint")
    d.box(p, (420, 80, 660, 175),
          '<div class="t">Teaching Assistant</div>'
          "George Kutsia Andguladze<br/>"
          '<span class="s">george@lidr.co · dudas técnicas en el canal asíncrono</span>',
          kind="lav")
    d.box(p, (420, 190, 660, 300),
          '<div class="t">Cómo es la clase</div>'
          "<ul><li>Flipped: los 5 articles y el ejercicio ya están hechos.</li>"
          "<li><b>No se teclea código</b>: se lee el que ya existe y se ejecuta.</li>"
          "<li>Todo en Python en el servicio IA.</li></ul>",
          kind="beige")
    d.html(p, (60, 315, 660, 360),
           '<div class="center s">"Hoy no vectorizamos nada: hoy preparamos el corpus para que '
           "<b>merezca</b> ser vectorizado.\"</div>")


def slide_agenda_public(d: Deck) -> None:
    p = d.new("Lo que vamos a ver hoy",
              "En el orden en que viaja un dato: decidir → elegir fuentes → parsear → limpiar → proteger",
              "Bloque 0")
    items = [
        ("Apertura", "Vuestros números del ejercicio: ¿dónde se rompió el CAG?", "mint"),
        ("Resolución de dudas", "Errores del ejercicio y del stack nuevo", "beige"),
        ("1 · Decisión arquitectónica", "CAG, RAG o híbrido: una decisión defendible", "lav"),
        ("2 · Catálogo de fuentes", "Qué entra al sistema, qué no y por qué", "lav"),
        ("3 · Ingesta", "Un Document canónico para todos los formatos", "lav"),
        ("4 · Limpieza y validación", "pandas + Pandera: reparar, cuarentena o descartar", "lav"),
        ("5 · PII y GDPR", "Pseudonimización con Presidio y mapping table", "lav"),
        ("Cierre", "Un corpus listo para vectorizar · puente a la Sesión 7", "mint"),
    ]
    y = 72
    for title, desc, k in items:
        d.box(p, (70, y, 430, y + 26), f"<b>{title}</b> · {desc}", kind=k, pad=6)
        y += 30
    d.box(p, (450, 72, 660, 186),
          '<div class="t">Al salir de hoy sabréis…</div>'
          "<ul><li>Defender por qué este proyecto necesita RAG.</li>"
          "<li>Auditar y catalogar las fuentes de datos.</li>"
          "<li>Limpiar y validar antes de vectorizar.</li>"
          "<li>Proteger la PII cumpliendo GDPR.</li></ul>",
          kind="mint")
    d.box(p, (450, 198, 660, 312),
          '<div class="t">Cómo trabajamos</div>'
          "Cada pieza: <b>el fundamento</b> → <b>dónde vive en el código</b> → <b>demo</b> → "
          "<b>las decisiones que tenéis que saber defender</b>.<br/>"
          '<span class="s">Todo el código ya está en la rama session_06_live.</span>',
          kind="beige")


def slide_agenda(d: Deck) -> None:
    if not d.mentor:
        slide_agenda_public(d)
        return
    p = d.new("Agenda · 120 minutos", "El orden es el del viaje de un dato: decidir → elegir fuentes → parsear → limpiar → proteger",
              "Bloque 0 · 0:02 · enseñar el mapa y las dos reglas del directo")
    rows = [
        ("0:00 – 0:10", "Bloque 0", "Apertura · vuestros números del CAG roto", "mint"),
        ("0:10 – 0:25", "Bloque 1", "Resolución de errores (15 min innegociables)", "beige"),
        ("0:25 – 0:40", "2.1", "Decisión arquitectónica: CAG, RAG o híbrido", "lav"),
        ("0:40 – 1:00", "2.2", "El catálogo de fuentes como artefacto vivo", "lav"),
        ("1:00 – 1:20", "2.3", "Ingesta y Document canónico", "lav"),
        ("1:20 – 1:35", "2.4", "Limpieza con pandas + validación con Pandera", "lav"),
        ("1:35 – 1:55", "2.5", "Pseudonimización con Presidio + mapping table", "lav"),
        ("1:55 – 2:00", "Bloque 3", "Cierre del módulo y puente a la Sesión 7", "mint"),
    ]
    y = 74
    for t, b, desc, k in rows:
        d.box(p, (70, y, 430, y + 26), f'<span class="mono">{t}</span> &nbsp; <b>{b}</b> · {desc}', kind=k, pad=6)
        y += 30
    d.box(p, (450, 74, 660, 200),
          '<div class="t">Dos reglas innegociables</div>'
          "<ul><li>Embeddings, pgvector activo o chunking → <b>\"Sesión 7.\"</b></li>"
          "<li>Todo el código nuevo es <b>Python en el servicio IA</b>. Rails solo aparece como cliente "
          "HTTP ilustrativo (decirlo cada vez).</li></ul>",
          kind="peach")
    d.box(p, (450, 212, 660, 314),
          '<div class="t">Patrón de cada sub-bloque</div>'
          "<b>Fundamento</b> (pizarra) → <b>dónde vive</b> (IDE, leer) → <b>demo</b> (terminal) → "
          "<b>defensa oral</b> → <b>bridge</b>.<br/>"
          '<span class="s">Lidera con el fundamento, después abre el archivo.</span>',
          kind="beige")


def slide_bloque0(d: Deck) -> None:
    p = d.new("¿Qué restricción del CAG se rompió primero en tu ejercicio?",
              "Quiero un número, no una sensación: tokens, ms, $/turn o drift event",
              "Bloque 0 · 0:03–0:08 · tabular en vivo · al CUARTO input, cortar sin excepción")
    names = [("1 · Context window", "¿Cabía el corpus?"), ("2 · Coste", "$/turno con prefix caching"),
             ("3 · Latencia", "P95 frente al SLO"), ("4 · Lost-in-the-middle", "recall del dato del centro")]
    x = 60
    for n, s in names:
        d.box(p, (x, 74, x + 142, 112), f'<div class="t">{n}</div><span class="s">{s}</span>', kind="mint", pad=5)
        x += 152
    d.box(p, (60, 124, 450, 292),
          '<div class="t">Lo que traéis de casa</div>'
          "<table><tr><th>Alumno</th><th>Restricción rota primero</th><th>Número concreto</th><th>Escenario</th></tr>"
          "<tr><td>1</td><td></td><td></td><td></td></tr><tr><td>2</td><td></td><td></td><td></td></tr>"
          "<tr><td>3</td><td></td><td></td><td></td></tr><tr><td>4</td><td></td><td></td><td></td></tr></table>",
          kind="beige")
    trap_title = "Pregunta trampa" if d.mentor else "¿Alguien detectó lost-in-the-middle?"
    trap_lead = ("Si nadie lo dice: <b>¿alguien detectó lost-in-the-middle?</b><br/><br/>"
                 if d.mentor else "")
    d.box(p, (465, 124, 660, 292),
          f'<div class="t">{trap_title}</div>'
          f"{trap_lead}"
          "Es el fallo más sutil: el modelo <b>siempre responde algo plausible</b>. Solo aparece "
          "si mides el recall del dato que pusiste en el centro.<br/><br/>"
          '<span class="s">Mitigarlo = curar el corpus o un retrieval que ponga lo relevante al final → Sesión 7.</span>',
          kind="note")
    d.html(p, (60, 302, 660, 330),
           '<div class="center"><b>"Estos números no son anécdotas: son la justificación arquitectónica del módulo entero."</b></div>')


def slide_bloque1(d: Deck) -> None:
    p = d.new("Resolución de errores · 15 minutos",
              "Tres cubetas, en este orden: encoding/formato → dependencias rotas → dudas conceptuales",
              "Bloque 1 · 0:10–0:25 · caso que bloquea > 3 min → \"lo retomo en el canal asíncrono\"")
    d.box(p, (40, 70, 355, 312),
          '<div class="t">Formato y encoding</div>'
          "<ul>"
          "<li><b>UTF-8 vs Latin-1</b> → <code>chardet.detect(raw_bytes)</code> y releer.</li>"
          "<li><b>CSV irregular</b> → <code>pd.read_csv(..., sep=\";\", engine=\"python\", on_bad_lines=\"warn\")</code></li>"
          "<li><b>JSON con campos ausentes</b> → <code>payload.get(\"x\")</code> y <code>x: str | None = None</code></li>"
          "<li><b>Fechas en varios formatos</b> → <code>pd.to_datetime(s, errors=\"coerce\", dayfirst=True)</code>"
          '<br/><span class="s">Es el patrón que veremos en 2.4 (<code>cleaning/budget_records.py</code>).</span></li>'
          "</ul>", kind="mint")
    d.box(p, (365, 70, 680, 312),
          '<div class="t">Dependencias del stack</div>'
          "<ul>"
          "<li><b>es_core_news_md</b> → sin él Presidio <b>falla en silencio</b>. Verificar: "
          "<code>nlp(\"Laura Fernández firmó en Madrid.\").ents</code> → PER + LOC.</li>"
          "<li><b>unstructured[all-docs]</b> → ~500 MB la primera vez; para el primer humo, "
          "<code>strategy=\"fast\"</code>.</li>"
          "<li><b>Pandera v2</b> → <code>import pandera.pandas as pa</code> (no <code>import pandera as pa</code>).</li>"
          "<li><b>Pydantic v2</b> → <code>@field_validator</code> + <code>@classmethod</code>; "
          "<code>@model_validator(mode=\"after\")</code>.</li>"
          "</ul>", kind="lav")
    d.html(p, (40, 320, 680, 345),
           '<div class="center s">El preflight de la sesión comprueba los 8 puntos críticos: '
           '<code>python scripts/preflight_s06.py</code></div>')


def slide_21_code(d: Deck) -> None:
    p = d.new("Dónde vive: app/ingestion/architecture.py",
              "La decisión del Article 1, codificada y testeada como un módulo más",
              "2.1 · 0:30 · aha: viable es un all([...]) → AND, no OR · una sola restricción en rojo tumba el CAG")
    d.code(p, (40, 70, 360, 190), """class CAGViability:              # las 4 restricciones
    @property
    def viable(self) -> bool:
        return all([self.context_window_ok,
                    self.cost_ok,
                    self.latency_ok,
                    self.lost_in_the_middle_ok])""", "Las cuatro restricciones")
    d.code(p, (40, 198, 360, 312), """def recommend_architecture(corpus, model):
    fits_in_window = (corpus.estimated_tokens
                      <= model.context_window * 0.7)
    cache_friendly = corpus.refresh_frequency_days >= 7
    traceability_doable = not corpus.traceability_required
    access_doable = not corpus.access_control_required""", "Los cuatro ejes")
    d.box(p, (372, 70, 680, 188),
          '<div class="t">Proyecto 2 · los números que defendemos</div>'
          "<table><tr><td>Volumen</td><td><b>≈ 250 000 tokens</b></td></tr>"
          "<tr><td>Refresco</td><td>7 días (cierre comercial)</td></tr>"
          "<tr><td>Trazabilidad</td><td>obligatoria (contractual)</td></tr>"
          "<tr><td>Acceso</td><td>por usuario</td></tr>"
          "<tr><td>Ventana gpt-4o-mini</td><td><b>128 000 tokens</b></td></tr></table>",
          kind="lav")
    d.code(p, (372, 198, 680, 312), """$ python -m app.ingestion.architecture
Corpus 'Proyecto 2': 250,000 tokens, refresh cada 7 días,
  trazabilidad=True, control_acceso=True
Modelo 'gpt-4o-mini': ventana 128,000 tokens

Viabilidad CAG: NO viable
  Restricciones en rojo: context_window, latency,
                         lost_in_the_middle
Recomendación arquitectónica: RAG""", "Demo · salida real")
    d.html(p, (40, 318, 680, 345),
           '<div class="center"><b>"250 000 contra 128 000: no cabe ni usando el 70 % útil de la ventana. '
           'Game over para el CAG puro."</b></div>')


def slide_21_defensa(d: Deck) -> None:
    p = d.new("La decisión: CAG, RAG o híbrido",
              "Lo que tenéis que poder defender ante un Director de Producto",
              "2.1 · 0:37 · riesgo: preguntas de embeddings/pgvector → \"Sesión 7\" · bridge: primero el catálogo")
    d.image(p, (30, 66, 370, 330), "s06-arbol-cag-rag-hibrido.png")
    d.box(p, (385, 70, 685, 128),
          '<div class="t">Los cuatro ejes son AND</div>'
          "Un solo eje en rojo tumba el CAG. Por eso <code>viable</code> es un <code>all([...])</code>.",
          kind="mint")
    d.box(p, (385, 136, 685, 212),
          '<div class="t">Fine-tuning no está en el árbol</div>'
          "Es una capa <b>ortogonal</b>: enseña <i>cómo responder</i>, no aporta datos nuevos ni resuelve "
          "trazabilidad. <b>Nunca</b> sustituye a un retrieval mal diseñado.",
          kind="lav")
    d.box(p, (385, 220, 685, 296),
          '<div class="t">Tres opciones, no dos</div>'
          "Lo estable (glosario, plantillas, tarifas) por CAG; lo volátil por RAG: la "
          "<b>arquitectura híbrida residual</b>. Hoy vamos a RAG.",
          kind="peach")
    d.html(p, (385, 302, 685, 335),
           '<div class="s"><b>Siguiente →</b> "Decidido RAG, lo primero NO es cargar un parser: es saber '
           "<b>qué</b> vamos a indexar. Eso es el catálogo.\"</div>")


def slide_22_code(d: Deck) -> None:
    p = d.new("El catálogo es código, no documentación",
              "Tres ficheros pequeños en app/ingestion/catalog/ y un YAML versionado en git",
              "2.2 · 0:45 · leer el YAML en voz alta, NO editarlo en vivo (ya está pre-redactado)")
    d.code(p, (30, 70, 240, 200), """@dataclass
class FolderFacts:
    folder: Path
    file_count: int = 0
    total_size_mb: float = 0.0
    latest_modified: datetime | None
    formats_detected: set[str]""", "inspect.py · facts, cero opiniones")
    d.code(p, (250, 70, 470, 200), """class CatalogDecision(str, Enum):
    INCLUDE = "include"
    REVIEW  = "review"   # la 3ª
    EXCLUDE = "exclude"

@model_validator(mode="after")
def _decision_requires_reason(...):
    # no include => motivo obligatorio""", "models.py · contrato Pydantic v2")
    d.code(p, (480, 70, 690, 200), """def load_catalog(path) -> DataCatalog:
    raw = yaml.safe_load(
        Path(path).read_text("utf-8"))
    return DataCatalog.model_validate(raw)

# 3 líneas: todo el peso está
# en el modelo, que se testea""", "loader.py · deliberadamente trivial")
    d.box(p, (30, 210, 400, 312),
          '<div class="t">data/catalog/catalog.yaml</div>'
          "<table><tr><th>Fuente</th><th>Decisión</th><th>Motivo</th></tr>"
          '<tr><td>presupuestos_json</td><td class="k">include</td><td>PII confidencial</td></tr>'
          "<tr><td>transcripciones_txt</td><td><b>review</b></td><td>la de 2023 sin speaker tags rompe el parser</td></tr>"
          '<tr><td>rate_card_xlsx</td><td class="r">exclude</td><td>actuality=1, fichero del 12/01/2024</td></tr></table>',
          kind="beige")
    d.code(p, (410, 210, 690, 312), """$ python -m app.ingestion.catalog.inspect data/seed
budgets      6 files  formats=json
transcripts  3 files  formats=txt
seed         1 files  latest=2024-01-12  formats=xlsx

$ python -m app.ingestion.catalog.loader \\
      data/catalog/catalog.yaml
Sources total: 3 · Sources included: 1
  - presupuestos_json (json)""", "Demo · salida real")
    d.html(p, (30, 318, 690, 345),
           '<div class="center"><b>"Tres fuentes, una sola incluida. Esto es lo que enseñáis a un auditor."</b> '
           '<span class="s">· excluir es disciplina, no desidia · review evita que lo dudoso se cuele en include</span></div>')


def slide_23_code(d: Deck) -> None:
    p = d.new("El Document canónico y los parsers",
              "Un contrato plano para todo lo que sale de la ingesta, venga de JSON, TXT o PDF",
              "2.3 · 1:05 · metanorma del módulo: \"si no sabes, no rellenas con basura\"")
    d.code(p, (30, 70, 260, 175), """class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: str
    metadata: DocumentMetadata
    # lo específico de formato
    # va en metadata.extra""", "documents/models.py")
    d.code(p, (270, 70, 480, 175), """@runtime_checkable
class Parser(Protocol):
    supported_formats: ClassVar[set[str]]
    def parse(self, blob, context
              ) -> Iterable[Document]: ...""", "parsers/protocol.py · Protocol, no ABC")
    d.code(p, (490, 70, 690, 175), """registry.register(BudgetJsonParser())
registry.register(TranscriptTxtParser())
# XLSX/DOCX/PDF: repo de referencia
# añadir un formato = una línea""", "parsers/registry.py")
    d.box(p, (30, 185, 355, 312),
          '<div class="t">budget_json.py · markdown, no json.dumps</div>'
          "<code>text = _render_budget_markdown(payload)</code><br/><br/>"
          "El embedder embebe <b>prosa</b>: \"¿quién es el cliente?\" se parece más a "
          "<code>## Cliente - Nombre: Acme</code> que a <code>{\"client_name\":\"Acme\"}</code>.<br/>"
          '<span class="s">Una decisión de retrieval que adelantamos al parser.</span>',
          kind="mint")
    d.box(p, (365, 185, 690, 312),
          '<div class="t">transcript_txt.py · un formato, dos modos</div>'
          "<ul><li><b>Tagged</b> (≥ 3 líneas <code>[hh:mm:ss] Speaker:</code>) → un Document por turno con "
          "<code>speaker</code> y <code>timestamp</code>.</li>"
          "<li><b>Legacy</b> → un Document por bloque, <b>sin speaker: no lo fabrico</b>.</li></ul>"
          '<span class="s">"Mejor admitir que no sé el speaker que inventármelo."</span>',
          kind="lav")
    d.html(p, (30, 318, 690, 345),
           '<div class="center s"><b>extra="forbid"</b>: si un parser cuela un campo no declarado, Pydantic falla · '
           "<b>error fuerte &gt; error silencioso</b> · el loader solo da bytes, el parser no sabe de dónde vienen</div>")


def slide_23_demo(d: Deck) -> None:
    p = d.new("La ingesta es offline: 202 + polling",
              "Indexar tarda minutos; una llamada síncrona tira al cliente. El query de la Sesión 7 sí será síncrono",
              "2.3 · 1:12 · la defensa más importante del sub-bloque · enseñar los structlog en la otra terminal")
    d.image(p, (24, 66, 330, 245), "s06-pipeline-offline-online.png")
    d.code(p, (340, 68, 692, 250), """$ curl -X POST localhost:8000/api/v1/ingestion/runs \\
       -d '{"source_name": "presupuestos_json"}'
{"job_id": "e417f7f9-...", "status": "pending"}       ← 202

$ curl localhost:8000/api/v1/ingestion/jobs/$JID
{"status": "completed", "documents_count": 6,
 "error_message": null}

# ramas de error
transcripciones_txt (review)  → HTTP 400
rate_card_xlsx (exclude)      → HTTP 400 source_not_included
no_existe                     → HTTP 404 unknown_source""", "Demo · salida real")
    d.box(p, (24, 258, 330, 312),
          '<div class="t">Router fino</div>'
          "Valida contra el catálogo, crea el job, dispara el <code>BackgroundTask</code> (con su propia "
          "sesión de BD) y devuelve <b>202</b>.", kind="beige")
    d.box(p, (340, 258, 692, 312),
          '<div class="t">Cliente Rails ilustrativo · ingestion_client.rb</div>'
          "Solo ilustra el contrato: <b>cualquier cliente HTTP funciona</b> (curl, httpx, fetch). "
          "El servicio Python es el autoritativo.", kind="lav")
    d.html(p, (24, 318, 692, 345),
           '<div class="center s">XLSX, DOCX y PDF siguen exactamente este patrón: '
           "los tenéis en el repo de referencia.</div>")


def slide_madurez(d: Deck) -> None:
    p = d.new("La madurez documental marca el techo de precisión",
              "Lo que hay que saber de antemano, antes de prometerle nada a un cliente",
              "Bloque 2 · 1:18 · idea propia de Julián · contarlo con un ejemplo real de cliente")
    steps = [
        ("~60 %", "Fácil", "Un RAG directo sobre los documentos tal cual llegan. Impresiona en la demo.", "peach"),
        ("60 → 80 %", "Un salto enorme", "Catálogo, Document canónico, limpieza, validación y PII: "
         "exactamente lo que construimos hoy.", "lav"),
        ("≈ 100 %", "Meses de trabajo… o imposible", "Sin errores en una adopción agéntica o RAG: meses de "
         "iteración, o directamente inalcanzable por la propia naturaleza de la IA.", "mint"),
    ]
    y = 74
    for pct, name, desc, k in steps:
        d.box(p, (40, y, 400, y + 70),
              f'<span class="big"><b>{pct}</b></span> &nbsp;<b>{name}</b><br/>{desc}', kind=k, pad=8)
        y += 80
    d.box(p, (415, 74, 685, 228),
          '<div class="t">No se empieza la casa por el tejado</div>'
          "Muchas empresas aún no han digitalizado de verdad: documentos sueltos en Word, carpetas compartidas "
          "sin orden, ERPs de hace 20 años.<br/><br/>"
          "Sin esa base, la IA <b>no tiene de dónde leer</b>. Primero digitalizar y ordenar; después, IA.",
          kind="beige")
    d.box(p, (415, 238, 685, 312),
          '<div class="t">Por qué importa</div>'
          "Si no se sabe desde el principio, llegan las quejas: del cliente, del jefe de proyecto… "
          "y la culpa acaba siendo \"de la IA\".",
          kind="note")


def slide_24_code(d: Deck) -> None:
    p = d.new("Limpiar y validar son dos pasos distintos",
              "Limpieza permisiva (repara lo reparable) · validación estricta (decide qué entra)",
              "2.4 · 1:25 · los checks de Pandera confunden la primera vez → se leen, no se teclean")
    d.code(p, (30, 70, 350, 160), """# cleaning/budget_records.py  — repara, no juzga
df["signed_at"] = pd.to_datetime(df["signed_at"],
                     errors="coerce", dayfirst=True)
df = (df.sort_values(["budget_id", "signed_at"])
        .drop_duplicates(subset=["budget_id"], keep="last"))""",
           "1 · Limpieza")
    d.code(p, (360, 70, 690, 160), """# cleaning/schemas.py  — Pandera v2
import pandera.pandas as pa
"total_amount": Column(float,
     checks=[Check.ge(0), Check.le(10_000_000)]),
"client_name":  Column(str, nullable=True),
strict=True, coerce=False""", "2 · Contrato de contenido")
    d.code(p, (30, 168, 350, 250), """# cleaning/policy.py  — enruta a tres cubetas
QUARANTINE_CHECKS = {"not_nullable", "no_default",
                     "column_in_dataframe"}
DISCARD_CHECKS    = {"in_range", "greater_than_or_equal_to",
                     "isin", "str_matches"}
validated = BudgetRecord.validate(df, lazy=True)""", "3 · Política")
    d.box(p, (360, 168, 690, 250),
          '<div class="t">Reparar · cuarentena · descartar</div>'
          "<table><tr><td class=\"k\">Reparar</td><td>sin pérdida semántica, sin humano</td></tr>"
          "<tr><td><b>Cuarentena</b></td><td>grave pero útil tras revisión: no entra al RAG, se guarda con motivo</td></tr>"
          "<tr><td class=\"r\">Descartar</td><td>contaminación clara: fuera, con log</td></tr></table>",
          kind="beige")
    d.box(p, (30, 258, 690, 312),
          '<div class="t">Para defender</div>'
          "<code>errors=\"coerce\"</code>: no excepciones, la validación decide · dedup por hash distingue duplicado exacto de "
          "divergencia · \"keep last by signed_at\" es <b>política de negocio</b> documentada en código · "
          "<code>lazy=True</code> recoge <b>todos</b> los errores para poder enrutar · <code>strict=True</code> siempre: "
          "lo que se relaja es la política, no el contrato.",
          kind="mint")


def slide_24_demo(d: Deck) -> None:
    p = d.new("Lo que sale de verdad en la demo",
              "Ejecución real del código de la sesión",
              "2.4 · 1:30 · ojo: no coincide con la diapo anterior → convertirlo en el mejor ejemplo de la sesión")
    d.code(p, (30, 70, 360, 300), """$ python scripts/demo_cleaning_s06.py
Ficheros leídos: 6
UserWarning: Parsing dates in %Y-%m-%d format
  when dayfirst=True was specified.
Filas tras limpieza + dedup: 5

Report:
  input_rows: 5
  valid_rows: 3
  quarantined_rows: 1
  discarded_rows: 1

Descartadas:
  BUDGET-2024-0004   -50000

En cuarentena:
  BUDGET-2024-0002   BetaNorte Distribución""", "Demo · salida real")
    d.box(p, (372, 70, 690, 136),
          '<div class="t">6 ficheros → 5 filas</div>'
          "El dedup colapsó las dos versiones de <b>BUDGET-2024-0005</b> y se quedó con la v2 "
          "(firmada después). Política en código, no en un acta.",
          kind="mint")
    d.box(p, (372, 144, 690, 228),
          '<div class="t">¿Por qué va a cuarentena el 0002 y no el "TBD"?</div>'
          "Su fecha es <code>12/03/2024</code>; las demás, <code>2024-05-02</code>. pandas deduce el formato de la "
          "<b>primera</b> fila y la del 0002 no encaja → <code>NaT</code> → falla <code>not_nullable</code>. "
          "El 0003 (\"TBD\") pasa porque <code>client_name</code> admite nulos.",
          kind="note")
    d.box(p, (372, 236, 690, 300),
          '<div class="t">La lección</div>'
          "<code>dayfirst=True</code> no bastó: <b>la limpieza no pudo reparar esa fecha y la validación la cazó</b>. "
          "Por eso son dos pasos distintos.",
          kind="peach")
    d.html(p, (30, 308, 690, 340),
           '<div class="center"><b>Siguiente →</b> "Datos limpios y validados. <b>Pero todavía con PII en claro.</b> '
           'Lo arreglamos ahora, y es lo más delicado del módulo."</div>')


def slide_25_fallo(d: Deck) -> None:
    p = d.new("Empezar por el fallo: Presidio en inglés",
              "Por qué hay que configurar el español de forma explícita",
              "2.5 · 1:38 · contarlo ANTES de abrir analyzer.py")
    d.box(p, (40, 72, 330, 206),
          '<div class="t">Lo que pasa por defecto</div>'
          "Presidio monta spaCy <b>en inglés</b>. Sobre \"Laura Fernández\" o \"Javier Romero\" devuelve "
          "<b>cero</b> entidades PERSON.<br/><br/>"
          "Y <b>falla en silencio</b>: el pipeline parece funcionar y en producción alguien pregunta "
          "\"¿qué dijo Laura Fernández?\" y el LLM responde con el nombre sin pseudonimizar.",
          kind="peach")
    d.code(p, (345, 72, 690, 206), """@lru_cache                       # spaCy tarda ~300 ms
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
    return engine""", "pii/analyzer.py · la corrección")
    d.box(p, (40, 216, 330, 312),
          '<div class="t">Recognizers del dominio</div>'
          "<code>BUDGET-\\d{4}-\\d{4}</code> y <code>CLI-\\d{4}</code>, score 0.95 (regex muy específico).<br/>"
          "Presidio trae PERSON, EMAIL o LOC de fábrica; nuestros ids, no. Sin recognizer propio se vectorizan en claro.",
          kind="lav")
    d.box(p, (345, 216, 690, 312),
          '<div class="t">Con la configuración en español</div>'
          "<code>[PERSON Laura Fernández, LOC Madrid]</code> ✔<br/><br/>"
          "El preflight lo comprueba con esa misma frase: "
          "<code>detected PER entities: ['Laura Fernández']</code>.",
          kind="mint")


def slide_25_demo(d: Deck) -> None:
    p = d.new("Mismo valor → mismo pseudónimo, siempre",
              "pii/pseudonymizer.py + mapping table en Postgres (pgvector instalado pero dormido)",
              "2.5 · 1:45 · si los falsos positivos molestan: \"cambio a betanorte, está más limpio\"")
    d.code(p, (30, 70, 340, 160), """self._generators = {
    "PERSON": self._faker.name,
    "EMAIL_ADDRESS": self._faker.ascii_company_email, ...}
results.sort(key=lambda r: r.end, reverse=True)  # der→izq
original_hash = self._hash(original_value)  # HMAC-SHA256""",
           "Tres líneas aha")
    d.code(p, (30, 168, 340, 222), """UniqueConstraint("entity_type", "original_hash",
                 name="uq_mappings_entity_hash")
# se guarda el hash, NUNCA el valor en claro""", "persistence/models.py · la mapping table")
    d.box(p, (30, 230, 340, 312),
          '<div class="t">Por qué así</div>'
          "<ul><li>Generador <b>por tipo</b>: un nombre se cambia por un nombre, no por <code>[PERSON]</code>.</li>"
          "<li>Reemplazo de derecha a izquierda: los offsets no se desplazan.</li>"
          "<li>El UNIQUE hace la concurrencia segura sin locks.</li></ul>", kind="beige")
    d.code(p, (350, 70, 690, 222), """$ python scripts/demo_pii_s06.py
[09:15:02] Pánfilo del Barros: Buenas. Estamos revisando
el presupuesto BUDGET-2026-3206 firmado en marzo, código
de cliente Apolinar Montero Verdejo. ...
--- Mappings aplicados (20) ---
  PERSON         → Purificación Rivero Arjona
  EMAIL_ADDRESS  → dalila38@instalaciones.org
  ORGANIZATION   → REDACTED-7c65c1e5
  LOCATION       → Teruel""", "Demo · salida real (transcripción BetaNorte)")
    d.box(p, (350, 230, 690, 312),
          '<div class="t">Falsos positivos (saldrán)</div>'
          "Ejemplo real: el código de cliente se reemplazó por un nombre de persona. No es un bug, es el "
          "trade-off de Presidio en español. En producción: subir el umbral, deny-list o "
          "<code>es_core_news_lg</code>.<br/>"
          '<span class="s">La demo usa un store en memoria: la tabla de Postgres sale vacía.</span>',
          kind="note")


def slide_25_gdpr(d: Deck) -> None:
    p = d.new("Derecho al olvido (GDPR art. 17): por qué la mapping table es arquitectura",
              "Sin ella, borrar a un cliente es imposible: está embebido en miles de chunks",
              "2.5 · 1:50 · defensa oral final del módulo")
    steps = [
        ("1", "Buscar en la mapping store todos los pseudónimos del solicitante (con sus variantes)."),
        ("2", "Localizar en el índice los chunks con esos pseudónimos o sus documentos."),
        ("3", "Eliminar esos chunks del índice vectorial."),
        ("4", "Borrar sus entradas de la mapping store: si reaparece, recibe un pseudónimo nuevo."),
        ("5", "Registrarlo en un audit log: atendido en plazo y forma."),
    ]
    y = 72
    for n, s in steps:
        d.box(p, (40, y, 420, y + 40), f'<b>{n}</b> · {s}', kind="lav", pad=7)
        y += 46
    d.box(p, (435, 72, 690, 176),
          '<div class="t">Pseudonimizar, no anonimizar</div>'
          "<code>[PERSON]</code> genérico tira la similitud un <b>15–25 %</b>. Un nombre verosímil y consistente "
          "preserva la estructura semántica.", kind="mint")
    d.box(p, (435, 184, 690, 296),
          '<div class="t">Lo que NO frena</div>'
          "La filtración <b>por inferencia</b> (estilo, jerga, dialecto → identidad): la señal está en el lenguaje, "
          "no en los identificadores. Queda abierta como teoría.<br/>"
          '<span class="s">El control de acceso de Rails no protege contra ninguno de los tres modos.</span>',
          kind="peach")


def slide_cierre(d: Deck) -> None:
    p = d.new("Cinco piezas: el corpus ya es defendible",
              "Ante legal, comercial, técnico y regulatorio",
              "Bloque 3 · 1:55–2:00 · cero coding · entregar el repo de referencia al final")
    d.box(p, (40, 68, 690, 230),
          "<table><tr><th>#</th><th>Pieza</th><th>Dónde vive</th><th>Article</th></tr>"
          "<tr><td>1</td><td>Decisión arquitectónica (RAG, híbrido residual)</td><td><code>app/ingestion/architecture.py</code></td><td>1</td></tr>"
          "<tr><td>2</td><td>Catálogo versionado, 3 fuentes auditadas</td><td><code>data/catalog/catalog.yaml</code> + <code>catalog/</code></td><td>2</td></tr>"
          "<tr><td>3</td><td>Ingesta + Document canónico + endpoint asíncrono</td><td><code>loaders/ parsers/ orchestrator.py</code></td><td>3</td></tr>"
          "<tr><td>4</td><td>Limpieza + Pandera + reparar/cuarentena/descartar</td><td><code>app/ingestion/cleaning/</code></td><td>4</td></tr>"
          "<tr><td>5</td><td>Pseudonimización GDPR-grade + mapping table</td><td><code>app/ingestion/pii/</code> + <code>persistence/</code></td><td>5</td></tr></table>",
          kind="beige")
    d.box(p, (40, 240, 360, 312),
          '<div class="t">Eso es data-driven AI</div>'
          "La exclusión del XLSX tiene motivo, la cuarentena tiene motivo, la política de dedup tiene motivo, "
          "el modelo de Presidio en español tiene motivo. Todo versionado en git.",
          kind="mint")
    d.box(p, (370, 240, 690, 312),
          '<div class="t">Sesión 7 →</div>'
          "<b>Chunking, embeddings y espacio vectorial.</b> Partimos los Documents, los embebemos y los metemos en "
          "pgvector, que se activa con <b>una sola migración Alembic</b>.",
          kind="lav")


def slide_chuleta(d: Deck) -> None:
    p = d.new("Chuleta de demos · local de Julián",
              "Desde ai-engineering-fork-julian\\ai-engineering-s06 · todos los comandos llevan -p aieng-s06live",
              "Apéndice · solo para el mentor")
    d.code(p, (30, 66, 360, 330), """# Pre-flight (5 min antes)
docker compose -p aieng-s06live ps
curl localhost:8000/health
docker compose -p aieng-s06live exec estimator \\
    python scripts/preflight_s06.py        # 8/8

# 2.1
docker compose -p aieng-s06live exec estimator \\
    python -m app.ingestion.architecture

# 2.2
docker compose -p aieng-s06live exec estimator \\
    python -m app.ingestion.catalog.inspect data/seed
docker compose -p aieng-s06live exec estimator \\
    python -m app.ingestion.catalog.loader \\
    data/catalog/catalog.yaml""", "Bloques 0–2.2")
    d.code(p, (370, 66, 690, 330), """# 2.3  (curl va tal cual)
curl -X POST localhost:8000/api/v1/ingestion/runs \\
  -H 'Content-Type: application/json' \\
  -d '{"source_name": "presupuestos_json"}'
curl localhost:8000/api/v1/ingestion/jobs/<job_id>
docker compose -p aieng-s06live logs -f estimator

# 2.4
docker compose -p aieng-s06live exec estimator \\
    python scripts/demo_cleaning_s06.py

# 2.5
docker compose -p aieng-s06live exec estimator \\
    python scripts/demo_pii_s06.py
docker compose -p aieng-s06live exec estimator-postgres \\
    psql -U estimator -d estimator

# Swagger: http://localhost:8000/docs  · Rails: :3000""", "Bloques 2.3–2.5")


# ===========================================================================

def build(mentor: bool) -> None:
    d = Deck(mentor)
    cover(d)
    slide_about(d)
    slide_agenda(d)
    slide_bloque0(d)
    d.template(1, "Bloque 0 · 0:08 · [Slide 1] el concepto: tus datos + privacidad + IA = ventaja competitiva")
    d.template(2, "Bloque 0 · 0:09 · [Slide 2] cada problema de la IA genérica tiene su pieza hoy")
    d.template(3, "Bloque 0 · 0:10 · [Slide 3] RAG vs fine-tuning: fine-tuning es capa ortogonal, no alternativa")
    slide_bloque1(d)
    d.template(4, "Bloque 2 · 0:25 · [Slide 4] el viaje del dato: decidir → catálogo → ingesta → limpieza → PII")
    d.template(5, "2.1 · 0:26 · [Slide 5] las cuatro restricciones tienen que estar en verde a la vez")
    slide_21_code(d)
    d.template(6, "2.1 · 0:34 · [Slide 6] el árbol sobre cuatro ejes · un solo eje en rojo fuerza RAG")
    slide_21_defensa(d)
    d.template(7, "2.2 · 0:40 · [Slide 7] los tres modos de fallo están plantados en nuestro corpus de demo")
    slide_22_code(d)
    d.template(8, "2.3 · 1:00 · [Slide 8] loader da bytes · parser entiende el formato · normalizer = cleaning/ + pii/")
    slide_23_code(d)
    d.template(9, "2.3 · 1:10 · [Slide 9] offline vs online: por eso la indexación es 202 + polling")
    slide_23_demo(d)
    slide_madurez(d)
    d.template(10, "2.4 · 1:20 · [Slide 10] las cuatro familias de suciedad, plantadas en data/seed/budgets/")
    slide_24_code(d)
    slide_24_demo(d)
    d.template(11, "2.5 · 1:35 · [Slide 11] ¿cuál es la más peligrosa? → la inferencia")
    slide_25_fallo(d)
    slide_25_demo(d)
    slide_25_gdpr(d)
    slide_cierre(d)
    d.template(12)
    d.template(13)
    if mentor:
        slide_chuleta(d)  # rutas y comandos del PC de Julián: nunca en la versión de alumnos
    d.save()


if __name__ == "__main__":
    build(mentor=False)
    build(mentor=True)
