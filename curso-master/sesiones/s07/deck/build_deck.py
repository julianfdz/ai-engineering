"""Genera el deck de la Sesión 7 (Embeddings y representación vectorial) de Julián Fernández.

Reutiliza la plantilla oficial de LIDR (portada, las 9 diapos de contenido, ROTI y cierre) y le
intercala diapos propias: fundamentos de embeddings, diagramas y los números reales de las
demos sobre el corpus de la sesión. Un solo PDF, el mismo para todos.

    python build_deck.py
    # → ../Sesion07-Julian-Fernandez.pdf

Los diagramas nuevos son SVG en ``curso-master/assets/``; se rasterizan a PNG con Edge
headless (MuPDF no respeta las fuentes ni las puntas de flecha de los SVG).
Para iterar: cambia el contenido de las funciones ``slide_*`` y vuelve a lanzar.
"""

from __future__ import annotations

import html
import subprocess
import tempfile
import time
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "plantilla-lidr-s07.pdf"
ASSETS = HERE.parent.parent.parent / "assets"
OUTPUT = HERE.parent / "Sesion07-Julian-Fernandez.pdf"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
SVGS = {"s07-pipeline-hoy": 330, "s07-anatomia-chunk": 430, "s07-late-chunking": 430}

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

# Tamaños en em: cada caja fija su tamaño base con autoajuste (ver Deck.flush).
CSS = """
* { font-family: sans-serif; }
body { margin: 0; color: #2b2b2b; font-size: 10pt; line-height: 1.32; }
h1 { font-size: 16.5pt; font-weight: normal; text-align: center; margin: 0; color: #222; }
.sub { font-size: 9.5pt; text-align: center; color: #666; margin-top: 3pt; }
.t { font-weight: bold; font-size: 1.12em; margin-bottom: 2pt; }
.s { color: #555; font-size: 0.88em; }
.mono, code, pre { font-family: monospace; font-size: 0.86em; }
pre { margin: 0; white-space: pre-wrap; line-height: 1.25; font-size: 1em; }
ul { margin: 2pt 0 0 0; padding-left: 12pt; }
li { margin-bottom: 2pt; }
table { border-collapse: collapse; width: 100%; }
td, th { border-bottom: 0.5pt solid #ddd; padding: 2.5pt 4pt; text-align: left; vertical-align: top; }
th { color: #555; font-weight: bold; border-bottom: 0.8pt solid #999; }
.k { color: #0f5a40; font-weight: bold; }
.r { color: #a33a1e; font-weight: bold; }
.big { font-size: 1.3em; }
.huge { font-size: 2em; font-weight: bold; }
.center { text-align: center; }
"""

# Las diapos se maquetan en y ∈ [62, 345] y se estiran a [62, 378] para usar toda la altura.
Y0, Y1, Y1_REAL = 62, 345, 378
TEXT_PT = (10, 13.5)   # rango del autoajuste del texto de las cajas
CODE_PT = (7, 10.5)    # y del código (además, sin partir líneas: ver Deck.flush)
TABLE_PT = (8, 11)     # cajas que son una tabla
MONO_EM = 0.6          # ancho de un carácter monoespaciado, en em


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def render_svgs() -> None:
    """Rasteriza los SVG de assets a PNG (solo si el SVG es más nuevo que su PNG)."""
    profile = Path(tempfile.gettempdir()) / "s07-deck-edge-profile"
    for name, height in SVGS.items():
        svg, png = ASSETS / f"{name}.svg", ASSETS / f"{name}.png"
        if png.exists() and png.stat().st_mtime >= svg.stat().st_mtime:
            continue
        before = png.stat().st_mtime if png.exists() else 0
        subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={profile}", "--force-device-scale-factor=2.5",
                        f"--window-size=860,{height}", f"--screenshot={png}", svg.as_uri()],
                       check=True, capture_output=True)
        # msedge.exe devuelve el control antes de que el proceso hijo escriba el PNG
        for _ in range(60):
            if png.exists() and png.stat().st_mtime > before:
                break
            time.sleep(0.5)
        time.sleep(1)
        print(f"{png.name}: rasterizado")


def _stretch(rect: tuple) -> fitz.Rect:
    k = (Y1_REAL - Y0) / (Y1 - Y0)
    x0, y0, x1, y1 = rect
    return fitz.Rect(x0, Y0 + (y0 - Y0) * k, x1, Y0 + (y1 - Y0) * k)


class Deck:
    def __init__(self) -> None:
        self.tpl = fitz.open(TEMPLATE)
        self.doc = fitz.open()
        self.archive = fitz.Archive(str(ASSETS))
        self.scratch = fitz.open()
        self.pending: list[tuple] = []   # cajas de la diapo actual, se pintan en flush()

    # ---- autoajuste -----------------------------------------------------
    def _fits(self, rect: fitz.Rect, body: str, pt: float) -> bool:
        page = self.scratch.new_page(width=W, height=H)
        spare, _ = page.insert_htmlbox(rect, f'<div style="font-size:{pt}pt">{body}</div>', css=CSS,
                                       archive=self.archive)
        self.scratch.delete_page(-1)
        return spare >= 0

    def _best_pt(self, rect: fitz.Rect, body: str, lo: float, hi: float) -> float:
        pt = hi
        while pt > lo and not self._fits(rect, body, pt):
            pt -= 0.25
        return pt

    def flush(self) -> None:
        """Pinta las cajas pendientes con un tamaño común por tipo (texto / código) en la diapo."""
        if not self.pending:
            return
        ranges = {"text": TEXT_PT, "code": CODE_PT, "table": TABLE_PT}
        sizes = {role: hi for role, (lo, hi) in ranges.items()}
        for page, r, inner, body, kind, role, longest in self.pending:
            lo, hi = ranges[role]
            if longest:   # que la línea más larga de código quepa sin partirse
                hi = max(lo, min(hi, inner.width / (MONO_EM * longest)))
            sizes[role] = min(sizes[role], self._best_pt(inner, body, lo, hi))
        for page, r, inner, body, kind, role, longest in self.pending:
            fill, stroke, ink = PALETTE[kind]
            page.draw_rect(r, color=_hex(stroke), fill=_hex(fill), width=0.7, radius=0.06)
            page.insert_htmlbox(inner, f'<div style="color:{ink};font-size:{sizes[role]}pt">{body}</div>',
                                css=CSS, archive=self.archive, scale_low=0.55)
        self.pending = []

    # ---- piezas básicas -------------------------------------------------
    def template(self, pno: int) -> fitz.Page:
        """Diapo tal cual de la plantilla, sin pie: su contenido llega hasta el borde inferior."""
        self.flush()
        self.doc.insert_pdf(self.tpl, from_page=pno, to_page=pno)
        return self.doc[-1]

    def new(self, title: str, sub: str = "", section: str = "") -> fitz.Page:
        self.flush()
        page = self.doc.new_page(width=W, height=H)
        page.show_pdf_page(BADGE, self.tpl, 1, clip=BADGE)
        head = f"<h1>{title}</h1>" + (f'<div class="sub">{sub}</div>' if sub else "")
        page.insert_htmlbox(fitz.Rect(80, 16, W - 80, 62), head, css=CSS)
        if section:
            self.footer(page, section)
        return page

    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (
            f'<div style="font-size:6.8pt;color:#6b655b">{section}'
            f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 7 · '
            f'Embeddings y representación vectorial · {len(self.doc)}</span></div>'
        )
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=CSS)

    def box(self, page: fitz.Page, rect: tuple, body: str, kind: str = "beige", pad: float = 6,
            role: str = "text", longest: int = 0) -> None:
        r = _stretch(rect)
        inner = fitz.Rect(r.x0 + pad, r.y0 + pad - 1, r.x1 - pad, r.y1 - pad + 1)
        self.pending.append((page, r, inner, body, kind, role, longest))

    def html(self, page: fitz.Page, rect: tuple, body: str) -> None:
        page.insert_htmlbox(_stretch(rect), f'<div style="font-size:10.5pt">{body}</div>', css=CSS,
                            archive=self.archive, scale_low=0.55)

    def code(self, page: fitz.Page, rect: tuple, src: str, label: str = "") -> None:
        head = (f'<div style="margin-bottom:2pt;color:#555;font-family:sans-serif;font-size:0.95em">'
                f"<b>{label}</b></div>") if label else ""
        longest = max(len(line) for line in src.splitlines())
        self.box(page, rect, head + f"<pre>{esc(src)}</pre>", kind="code", pad=5, role="code",
                 longest=longest)

    def image(self, page: fitz.Page, rect: tuple, name: str) -> None:
        """Inserta un PNG recortando el margen claro para aprovechar el hueco."""
        from io import BytesIO
        from PIL import Image, ImageChops
        im = Image.open(ASSETS / name).convert("RGB")
        bg = Image.new("RGB", im.size, im.getpixel((2, 2)))
        bbox = ImageChops.difference(im, bg).point(lambda v: 255 if v > 12 else 0).getbbox()
        if bbox:
            m = 12
            im = im.crop((max(bbox[0] - m, 0), max(bbox[1] - m, 0),
                          min(bbox[2] + m, im.width), min(bbox[3] + m, im.height)))
        buf = BytesIO()
        im.save(buf, format="PNG")
        page.insert_image(_stretch(rect), stream=buf.getvalue(), keep_proportion=True)

    def save(self) -> None:
        self.flush()
        self.doc.save(OUTPUT, garbage=4, deflate=True)
        print(f"{OUTPUT.name}: {len(self.doc)} diapos")


def _hex(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ===========================================================================
# Diapos
# ===========================================================================

def slide_about(d: Deck) -> None:
    p = d.new("Quién os acompaña hoy", "Sesión 7 · Módulo 3 · Data-driven AI", "Apertura")
    d.box(p, (60, 80, 400, 300),
          '<div class="t big">Julián Fernández</div>'
          '<div class="s">Informático · fundador de Búho AI</div>'
          "<ul>"
          "<li>Transformo operativas complejas en procesos eficientes con IA y software a medida.</li>"
          "<li>Profesor de IA en LIDR, EBF y UCAM HiTech.</li>"
          "<li>Enfoque <b>transparente y ético</b>: medir antes de opinar, y si un dato no se sabe, "
          "no se inventa.</li>"
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
          "<ul><li>Flipped: los artículos y el ejercicio previo ya están hechos.</li>"
          "<li><b>No se teclea código</b>: se lee el que ya existe y se ejecuta.</li>"
          "<li>Hoy, mucha terminal: ocho estrategias de chunking medidas en directo.</li></ul>",
          kind="beige")
    d.html(p, (60, 315, 660, 360),
           '<div class="center s">"Cambiar el chunking mueve la calidad de un RAG tanto como cambiar de modelo. '
           "<b>Hoy lo medimos sobre nuestros propios datos.</b>\"</div>")


def slide_agenda(d: Deck) -> None:
    p = d.new("Lo que vamos a ver hoy",
              "Del texto al vector: qué es un embedding y, sobre todo, cómo partir los documentos",
              "Apertura")
    items = [
        ("Apertura", "Dónde estamos en el pipeline RAG y con qué corpus trabajamos", "mint"),
        ("Dudas del ejercicio", "Vuestros números del sanity check y cinco errores reales", "beige"),
        ("Embeddings", "Qué son, cómo se miden, qué modelo elegir y Matryoshka", "lav"),
        ("Chunking I · mecánicas", "Fixed-size, recursive, sentence-window y structural", "lav"),
        ("Chunking II · semánticas", "Semantic, propositional y Contextual Retrieval", "lav"),
        ("Chunking III · avanzadas", "Hierarchical (parent-child) y late chunking", "lav"),
        ("Cierre", "El cuadro de mando para elegir · puente a la Sesión 8", "mint"),
    ]
    y = 74
    for title, desc, k in items:
        d.box(p, (70, y, 440, y + 28), f"<b>{title}</b> · {desc}", kind=k, pad=6)
        y += 33
    d.box(p, (455, 74, 665, 196),
          '<div class="t">Al salir de hoy sabréis…</div>'
          "<ul><li>Explicar qué mide un coseno y qué no.</li>"
          "<li>Elegir modelo de embeddings con criterios.</li>"
          "<li>Comparar 8 estrategias de chunking con datos.</li>"
          "<li>Defender una elección ante coste y calidad.</li></ul>",
          kind="mint")
    d.box(p, (455, 206, 665, 304),
          '<div class="t">Cómo trabajamos</div>'
          "Cada estrategia: <b>la idea</b> → <b>dónde vive en el código</b> → <b>demo</b> → "
          "<b>la pregunta que tenéis que saber responder</b>.",
          kind="beige")


def slide_pipeline(d: Deck) -> None:
    p = d.new("Hoy: Chunk + Embed",
              "La mitad central del pipeline offline de indexación", "Apertura")
    d.image(p, (30, 64, 470, 300), "s07-pipeline-hoy.png")
    d.box(p, (485, 70, 690, 182),
          '<div class="t">pgvector, en la Sesión 8</div>'
          "Hoy los vectores viven <b>en memoria</b> y se devuelven por HTTP. Así liberamos el tiempo para "
          "el chunking, que es donde de verdad se mueve la calidad de un RAG.",
          kind="lav")
    d.box(p, (485, 192, 690, 304),
          '<div class="t">El shape manda</div>'
          "El corpus de hoy está organizado por <b>componentes</b>, no por las fases de la S6. "
          "La forma de tus datos condiciona la estrategia de chunking que eliges.",
          kind="note")
    d.html(p, (30, 312, 690, 345),
           '<div class="center s">Código nuevo de hoy: <code>app/generation/rag/</code> · '
           "<code>chunking/</code> · <code>embedding/</code> · <code>analysis/</code></div>")


def slide_corpus(d: Deck) -> None:
    p = d.new("El corpus de la sesión", "data/budgets_sample.json · 17 presupuestos · 60 componentes",
              "Apertura")
    d.code(p, (30, 70, 360, 312), """{
  "budget_id": "BUD-2024-001",
  "client_metadata": {"name": "FintechCorp",
                      "sector": "finance",
                      "country": "ES"},
  "project_summary": "Mobile banking API with
       OAuth 2.0 authentication and PSD2 compliance",
  "main_technology": "ruby_on_rails",
  "year": 2024,
  "components": [
    {"component_id": "AUTH-001",
     "name": "OAuth 2.0 authentication backend",
     "description": "Implementation of OAuth 2.0
        flows ... JWT-based session management ...",
     "tech_stack": ["ruby_on_rails", "postgresql",
                    "redis"],
     "complexity": "high",
     "estimated_hours": 120},
    ...  PSD2-002 · TXN-003 · NOTIF-004
  ]
}""", "Un presupuesto")
    d.box(p, (372, 70, 690, 150),
          '<div class="t">components[ ] es la unidad de trabajo</div>'
          "Todo lo que hacemos hoy gira sobre ese array: cada componente es una pieza de software "
          "con descripción, stack, complejidad y horas estimadas.",
          kind="mint")
    d.box(p, (372, 160, 690, 248),
          '<div class="t">Dos presupuestos con trampa, a propósito</div>'
          "<ul><li><b>BUD-2024-016</b>: un componente con una descripción gigante "
          "(<code>MONO-001</code>, 1391 tokens).</li>"
          "<li><b>BUD-2024-017</b>: descripciones de una sola línea.</li></ul>",
          kind="peach")
    d.box(p, (372, 258, 690, 312),
          '<div class="t">Para pensar</div>'
          "Si el schema de los datos no coincide con lo prometido, alguien escribe el adaptador. "
          "<b>¿Quién lo presupuesta?</b>",
          kind="note")


def slide_sanity(d: Deck) -> None:
    p = d.new("El ejercicio previo: vuestro sanity check",
              "text-embedding-3-small · coseno calculado a mano · tres parejas", "Dudas del ejercicio")
    rows = [
        ("A · cercanas", "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app",
         "Authorization service using JSON Web Tokens for a banking application", "0,596", "&gt; 0,6"),
        ("B · sin relación", "(la misma)", "Database migration from MySQL to PostgreSQL with zero downtime",
         "0,192", "&lt; 0,4"),
        ("C · genéricas", "Backend services", "API development", "0,541", "—"),
    ]
    body = ("<table><tr><th>Pareja</th><th>Texto 1</th><th>Texto 2</th><th>Coseno</th><th>Esperado</th></tr>"
            + "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td><b>{s}</b></td><td>{e}</td></tr>"
                      for a, b, c, s, e in rows)
            + "</table>")
    d.box(p, (30, 70, 690, 192), body, kind="beige", role="table")
    d.box(p, (30, 202, 250, 312),
          '<div class="t">A: 0,596 &lt; 0,6</div>'
          "Mismo concepto con <b>cero palabras en común</b>. El modelo casi lo salva. "
          "Los umbrales dependen del modelo y de la redacción: no son constantes universales.",
          kind="lav")
    d.box(p, (260, 202, 470, 312),
          '<div class="t">B: 0,19</div>'
          "Lo esperado: temas sin relación quedan claramente separados.<br/>"
          '<span class="s">Ojo: 0,2–0,5 entre textos sin relación es normal en estos modelos.</span>',
          kind="mint")
    d.box(p, (480, 202, 690, 312),
          '<div class="t">C: 0,54, el aviso</div>'
          "Dos frases cortas y vagas puntúan casi como A. <b>El texto corto y genérico no discrimina.</b> "
          "Por eso cada chunk lleva una cabecera con proyecto, sector y tecnología.",
          kind="peach")


def slide_embedding(d: Deck) -> None:
    p = d.new("¿Qué es un embedding?",
              "Una función texto → vector de dimensión fija: textos parecidos, vectores cercanos", "Embeddings")
    d.image(p, (24, 64, 400, 318), "s07-espacio-semantico.png")
    d.box(p, (412, 68, 692, 150),
          '<div class="t">La propiedad que importa</div>'
          "\"authentication service\" encuentra \"OAuth 2.0 backend\" o \"JWT authorization module\" "
          "<b>aunque no compartan palabras</b>. Eso es búsqueda semántica.",
          kind="mint")
    d.box(p, (412, 158, 692, 246),
          '<div class="t">Aprendizaje contrastivo</div>'
          "Millones de tripletes <b>ancla / positivo / negativo</b>. Lo que se etiqueta como \"positivo\" "
          "define qué entiende el modelo por similar.",
          kind="lav")
    d.box(p, (412, 254, 692, 318),
          '<div class="t">Las dimensiones emergen</div>'
          "Ninguna dimensión suelta significa nada legible: lo que tiene sentido son "
          "<b>direcciones y distancias relativas</b>.",
          kind="beige")


def slide_metricas(d: Deck) -> None:
    p = d.new("Tres formas de medir la similitud", "Con vectores normalizados, las tres ordenan igual",
              "Embeddings")
    d.image(p, (30, 64, 690, 214), "s07-metricas-similitud.png")
    d.box(p, (30, 222, 690, 290),
          "<table><tr><th>Métrica</th><th>Fórmula</th><th>Rango</th><th>Rasgo</th></tr>"
          "<tr><td><b>Coseno</b></td><td><code>A·B / (‖A‖ ‖B‖)</code></td><td>−1 a 1</td>"
          "<td>mide el ángulo: un documento largo no sale penalizado frente a una consulta corta</td></tr>"
          "<tr><td><b>Producto escalar</b></td><td><code>Σ A[i]·B[i]</code></td><td>sin acotar</td>"
          "<td>el más barato (no calcula normas)</td></tr>"
          "<tr><td><b>Euclídea</b></td><td><code>√Σ (A[i]−B[i])²</code></td><td>0 a ∞</td>"
          "<td>distancia recta entre las puntas</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (30, 298, 690, 342),
          "<b>text-embedding-3-small devuelve vectores de norma 1</b> → producto escalar = coseno, y "
          "<code>euclídea² = 2 − 2·coseno</code>. La métrica se elige por la <i>model card</i>, "
          "no es una decisión de arquitectura.",
          kind="mint")


def slide_limites(d: Deck) -> None:
    p = d.new("Lo que un embedding NO resuelve",
              "Saberlo de antemano evita diseñar el sistema equivocado", "Embeddings")
    cards = [
        ("1 · Números, fechas e identificadores",
         "\"Presupuestos de 2024\" o \"más de 100 horas\" no se resuelven por similitud: se resuelven con "
         "<b>filtros sobre el metadata</b> (Sesión 8).", "peach"),
        ("2 · Palabras raras exactas",
         "Nombres propios, códigos, siglas: ahí <b>BM25</b> gana. Por eso existe la búsqueda híbrida "
         "(Sesión 10).", "lav"),
        ("3 · La concentración de distancias",
         "En alta dimensión, 0,2–0,5 entre textos sin relación es normal. <b>Calibra los umbrales con tu "
         "dataset</b>: \"&gt; 0,7\" no significa nada por sí solo.", "note"),
        ("4 · El modelo pesa más que la métrica",
         "Pasar de coseno a producto escalar no cambia nada. Pasar de un modelo solo-inglés a uno "
         "multilingüe, sí.", "mint"),
    ]
    pos = [(40, 72, 355, 188), (365, 72, 680, 188), (40, 198, 355, 314), (365, 198, 680, 314)]
    for (t, body, k), r in zip(cards, pos):
        d.box(p, r, f'<div class="t">{t}</div>{body}', kind=k, pad=9)


def slide_modelos(d: Deck) -> None:
    p = d.new("Elegir modelo de embeddings",
              "Precios y scores cambian cada pocos meses: verificar antes de decidir", "Embeddings")
    d.box(p, (24, 68, 462, 312),
          "<table><tr><th>Modelo</th><th>Dims</th><th>$ / M tokens</th><th>Notas</th></tr>"
          "<tr><td><b>text-embedding-3-small</b></td><td>1536</td><td>0,02</td><td>el caballo de batalla · Matryoshka</td></tr>"
          "<tr><td>text-embedding-3-large</td><td>3072</td><td>0,13</td><td>mejor calidad, 6,5× más caro</td></tr>"
          "<tr><td>Cohere embed-v3</td><td>—</td><td>0,10</td><td>fuerte en multilingüe</td></tr>"
          "<tr><td>Voyage voyage-3-large</td><td>—</td><td>≈ Cohere</td><td>optimizado para retrieval</td></tr>"
          "<tr><td>BAAI/bge-m3</td><td>1024</td><td>0 (GPU)</td><td>open source, multilingüe</td></tr>"
          "<tr><td>all-MiniLM-L6-v2</td><td>384</td><td>0 (CPU)</td><td>inglés, ideal para prototipos</td></tr>"
          "</table>",
          kind="beige", role="table")
    d.box(p, (472, 68, 696, 248),
          '<div class="t">Cinco criterios</div>'
          "<ul><li><b>Dimensiones</b>: con cientos de millones de vectores, 1536 vs 768 decide si cabe en RAM.</li>"
          "<li><b>Idioma</b>: corpus en inglés, briefs en español → multilingüe.</li>"
          "<li><b>Dominio</b>: no hay modelo de \"presupuestos\": se valida sobre tus datos.</li>"
          "<li><b>Hosting y coste</b>: API vs self-hosted.</li>"
          "<li><b>Licencia y privacidad</b>: banca, sanidad, defensa → self-hosted.</li></ul>",
          kind="lav")
    d.box(p, (472, 256, 696, 312),
          '<div class="t">Nuestra decisión</div>'
          "<code>text-embedding-3-small</code>, 1536 dims: calidad sobrada, coste despreciable.",
          kind="mint")


def slide_dimensiones(d: Deck) -> None:
    p = d.new("¿Por qué no se comparan vectores de distinta dimensión?",
              "Pregunta frecuente: 1536 contra 768 no da un número malo, da un número sin sentido",
              "Embeddings")
    d.box(p, (30, 68, 360, 168),
          '<div class="t">La matemática</div>'
          "El producto escalar <code>A·B = Σ A[i]·B[i]</code> empareja la coordenada <i>i</i> de uno con la "
          "<i>i</i> del otro. Con 1536 frente a 768, <b>las 768 últimas no tienen pareja</b>: la operación "
          "no está definida. Son espacios distintos, como sumar metros con euros.",
          kind="lav")
    d.code(p, (372, 68, 690, 168), """>>> np.dot(v1536, v768)
ValueError: shapes (1536,) and (768,) not aligned

-- pgvector (Sesión 8)
ERROR: different vector dimensions 1536 and 768
ERROR: expected 1536 dimensions, not 768""", "Si tienes suerte: el error salta")
    d.code(p, (30, 178, 360, 296), """# app/generation/rag/analysis/similarity.py
dot = sum(x * y for x, y in zip(a, b))
#                           ^^^ zip se para en la
#                    lista más corta: sin error
norm_a = math.sqrt(sum(x * x for x in a))   # 1536
norm_b = math.sqrt(sum(y * y for y in b))   #  768""", "Si no la tienes: nuestro coseno en Python puro")
    d.box(p, (372, 178, 690, 296),
          '<div class="t">El bug silencioso, medido</div>'
          "Un vector de 1536 contra <b>sus propias</b> 768 primeras dimensiones:<br/>"
          '<span class="huge">0,689</span> &nbsp;en vez de <b>1,0</b><br/>'
          "El mismo texto \"se parece\" un 69 % a sí mismo. Nada falla, y el ranking queda corrompido.",
          kind="peach")
    d.box(p, (30, 306, 690, 345),
          "<b>Cómo se evita:</b> un solo modelo y una sola dimensión por índice, guardados junto al vector · "
          "<code>assert len(a) == len(b)</code> · con Matryoshka, truncar <b>los dos</b> lados y renormalizar · "
          "y ojo: dos modelos distintos con 1536 dims tampoco son comparables.",
          kind="mint")


def slide_anatomia(d: Deck) -> None:
    p = d.new("El chunk de nuestro proyecto",
              "app/generation/rag/chunking/structural.py · la estrategia de referencia", "Embeddings")
    d.image(p, (30, 62, 690, 316), "s07-anatomia-chunk.png")
    d.html(p, (30, 322, 690, 350),
           '<div class="center s">Las otras siete estrategias reutilizan este mismo render de texto: '
           "<b>todas trocean la misma representación del corpus</b>, así la comparación es justa.</div>")


def slide_por_que_chunking(d: Deck) -> None:
    p = d.new("Por qué el chunking domina",
              "Un presupuesto entero en un vector es un promedio difuso; un trozo demasiado pequeño pierde el contexto",
              "Chunking I · mecánicas")
    cards = [
        ("Vectara · NAACL 2025", "25 configuraciones × 48 modelos",
         "Cambiar el chunking mueve la calidad <b>tanto como cambiar de modelo</b>.", "lav"),
        ("Chroma · 2025", "recall por estrategia",
         "LLM semantic <b>0,919</b> · cluster semantic <b>0,913</b> · recursive bien ajustado (400 tokens) "
         "<b>0,88–0,89</b>.", "mint"),
        ("Vecta · febrero 2026", "ranking sobre su benchmark",
         "Recursive 512 tokens, <b>primero con un 69 %</b>. Semantic, <b>cuarto con un 54 %</b>.", "peach"),
    ]
    x = 30
    for t, s, body, k in cards:
        d.box(p, (x, 74, x + 210, 214), f'<div class="t">{t}</div><div class="s">{s}</div><br/>{body}',
              kind=k, pad=9)
        x += 225
    d.box(p, (30, 226, 690, 300),
          '<div class="t center">Más sofisticado no significa mejor</div>'
          '<div class="center">La única respuesta honesta a "¿qué chunking es el mejor?" es '
          "<b>medirlo sobre tus datos</b> antes de comprometer arquitectura. Es lo que hacemos hoy.</div>",
          kind="note")


def slide_doce(d: Deck) -> None:
    p = d.new("Doce estrategias, cuatro familias",
              "Hoy ejecutamos ocho sobre nuestro corpus, todas tras la misma interfaz Chunker", "Chunking I · mecánicas")
    d.image(p, (24, 62, 430, 330), "s07-familias-chunking.png")
    d.code(p, (442, 66, 692, 170), """class Chunker(ABC):
    @abstractmethod
    def chunk(self, budgets) -> list[Chunk]:
        ...
    # coste de ingesta, por estrategia
    last_extra_api_calls: int = 0
    last_extra_cost_usd: float = 0.0""", "chunking/base.py · la interfaz común")
    d.box(p, (442, 178, 692, 330),
          '<div class="t">Siete criterios para elegir</div>'
          "<ul><li>Empieza con <b>recursive</b>, 400–512 tokens, 10–20 % de overlap.</li>"
          "<li>Si hay estructura, <b>úsala</b>: la palanca de mayor ROI.</li>"
          "<li>Chunks sin sentido aislados → Contextual Retrieval.</li>"
          "<li>Semantic y LLM-based, solo con datos que lo justifiquen.</li>"
          "<li>Parent-child, sobre un pipeline plano que ya funcione.</li>"
          "<li>Late, agentic, query-dependent: vigilar, no producir.</li>"
          "<li>Cada tipo de documento pide su estrategia.</li></ul>",
          kind="lav")


def slide_mecanicas(d: Deck) -> None:
    p = d.new("Las cuatro mecánicas, medidas",
              "compare_chunkers.py --strategies fixed-size,recursive,sentence-window,structural --queries all --output-table",
              "Chunking I · mecánicas")
    d.code(p, (30, 70, 380, 176), """strategy         n_chunks  p50_tokens  top1_cosine_avg
---------------  --------  ----------  ---------------
fixed_size       63        79.0        0.4760
recursive        23        187.0       0.3991
sentence_window  78        21.0        0.5366
structural       60        78.0        0.4734""", "Demo · ejecución real (6 consultas)")
    d.box(p, (30, 186, 380, 312),
          '<div class="t">Cómo leerla</div>'
          "<code>top1_cosine_avg</code> = la confianza media del mejor candidato en las 6 consultas.<br/><br/>"
          "Sentence-window saca el número más alto… y para \"OAuth authentication for fintech mobile app\" "
          "cuela <b>\"Email and password login.\"</b> en su top-3. <b>Score alto ≠ chunk relevante.</b>",
          kind="note")
    d.box(p, (392, 70, 690, 176),
          '<div class="t">Los parámetros</div>'
          "<ul><li><b>fixed-size / recursive</b>: 512 tokens, overlap 80.</li>"
          "<li><b>recursive</b>: corta primero por párrafo, luego por línea, frase y palabra.</li>"
          "<li><b>sentence-window</b>: indexa la frase, guarda ±2 frases en <code>metadata.window_text</code>.</li></ul>",
          kind="beige")
    d.box(p, (392, 186, 690, 312),
          '<div class="t">Sin contar coste, ¿cuál preferís?</div>'
          "<ul><li><b>Structural</b>: misma confianza que fixed-size, pero respeta la unidad de negocio.</li>"
          "<li><b>Recursive</b>: el default razonable cuando no hay estructura.</li>"
          "<li><b>Sentence-window</b>: útil en prosa sin estructura, con su ventana para generar.</li></ul>",
          kind="mint")


def slide_semantic(d: Deck) -> None:
    p = d.new("Semantic chunking: el coste real",
              "Embebe frases consecutivas y corta donde cae la similitud", "Chunking II · semánticas")
    d.code(p, (30, 70, 360, 150), """# chunking/strategies/semantic.py
from langchain_experimental.text_splitter import SemanticChunker
BREAKPOINT_THRESHOLD_TYPE = "percentile"
BREAKPOINT_THRESHOLD_AMOUNT = 95   # solo los saltos bruscos""", "Dónde vive")
    d.code(p, (372, 70, 690, 150), """strategy    n_chunks  p50    max   cost_usd  seconds
semantic    34        112.5  1278  0.000094  5.31
structural  60        78.0   1391  0.000000  0.00""", "Demo · --show-stats --show-cost")
    d.box(p, (30, 160, 250, 312),
          '<div class="t">Qué hace</div>'
          "Junta lo que va junto temáticamente: <b>34 chunks</b> frente a 60. El percentil 95 es agresivo: "
          "pocos cortes y chunks grandes.",
          kind="lav")
    d.box(p, (260, 160, 470, 312),
          '<div class="t">Qué cuesta</div>'
          "Una pasada de embeddings por <b>todas las frases</b> del corpus, antes de servir una sola consulta. "
          "Con 17 presupuestos es ridículo; con un millón, esos 5 segundos son horas.",
          kind="peach")
    d.box(p, (480, 160, 690, 312),
          '<div class="t">¿Lo aprobáis en una review?</div>'
          "Depende de si la mejora lo justifica <b>en tu corpus</b>. Sobre presupuestos estructurados, "
          "structural ya separa bien; semantic brilla en prosa larga sin estructura.",
          kind="note")


def slide_propositional(d: Deck) -> None:
    p = d.new("Propositional chunking: precisión a cambio de contexto",
              "Un LLM descompone cada componente en proposiciones atómicas y autocontenidas",
              "Chunking II · semánticas")
    d.code(p, (30, 70, 360, 160), """# chunking/strategies/propositional.py
PROPOSITIONAL_CHUNKER_MODEL = "gpt-4o-mini"
class _Propositions(BaseModel):      # salida tipada
    propositions: list[str]          # vía Instructor
# si una llamada falla → 1 chunk = el componente entero""", "Dónde vive")
    d.box(p, (372, 70, 690, 160),
          '<div class="t">Consulta "real-time inventory synchronization"</div>'
          '<span class="huge">0,823</span> &nbsp; <code>BUD-2024-007::INV-003::prop5</code><br/>'
          '<span class="s">el score más alto de toda la sesión: la proposición clavada</span>',
          kind="mint")
    d.box(p, (30, 170, 360, 312),
          '<div class="t">El precio, sobre el corpus completo</div>'
          "<table><tr><td>Chunks</td><td><b>778</b> (13× structural)</td></tr>"
          "<tr><td>Huérfanos (&lt; 20 tokens)</td><td class=\"r\">765</td></tr>"
          "<tr><td>Coste de ingesta</td><td>0,00755 $</td></tr>"
          "<tr><td>Tiempo de ingesta</td><td><b>173 s</b></td></tr></table>"
          '<span class="s">En la demo se limita a 3 presupuestos: 149 chunks en 28 s.</span>',
          kind="peach")
    d.box(p, (372, 170, 690, 312),
          '<div class="t">¿Para qué corpus sí y para cuál no?</div>'
          "<ul><li><b>Sí</b>: corpus densos en hechos donde manda la precisión factual (legal, médico).</li>"
          "<li><b>No</b>: corpus ya estructurados. La explosión de fragmentos sin contexto no compensa.</li></ul>",
          kind="lav")


def slide_contextual_code(d: Deck) -> None:
    p = d.new("Contextual Retrieval en el código",
              "Un párrafo generado por Claude sitúa cada chunk en su presupuesto", "Chunking II · semánticas")
    d.code(p, (30, 70, 400, 196), """# chunking/strategies/contextual_retrieval.py
CONTEXTUAL_CHUNKER_MODEL = "claude-sonnet-4-5"
MAX_CONTEXT_TOKENS = 200

system=[{"type": "text",
         "text": f"<document>\\n{parent_doc}\\n</document>",
         "cache_control": {"type": "ephemeral"}}]
# el contexto generado → metadata.generated_context""", "Dónde vive")
    d.box(p, (412, 70, 690, 196),
          '<div class="t">Prompt caching</div>'
          "Los chunks se procesan <b>agrupados por presupuesto</b>: el primero paga el documento "
          "(escritura en caché, 3,75 $/M), los demás lo leen de caché (<b>0,30 $/M</b>, unas 10× más barato).",
          kind="mint")
    d.box(p, (30, 206, 400, 312),
          '<div class="t">Nuestro structural ya lleva una cabecera…</div>'
          "<code>[Project: …] [Client sector: … | Year: … | Main tech: …]</code><br/><br/>"
          "Es una versión <b>estática y gratis</b> de la misma idea. La pregunta honesta: ¿cuánto añade la "
          "versión con LLM?",
          kind="lav")
    d.box(p, (412, 206, 690, 312),
          '<div class="t">Sobre nuestro corpus</div>'
          "AUTH-001: <b>0,568 → 0,607</b> (+0,04)<br/>"
          "60 chunks · <b>0,14 $</b> · <b>203 s</b> de ingesta<br/><br/>"
          '<span class="s">No es obvio que compense aquí. Esa discusión coste/valor es la lección.</span>',
          kind="note")


def slide_gdpr(d: Deck) -> None:
    p = d.new("Una consulta transversal: todas convergen",
              "\"GDPR compliance and audit logging\" · top-1 de cada estrategia", "Chunking II · semánticas")
    rows = [
        ("structural", "BUD-2024-009::CONSENT-004", "0,418"),
        ("fixed_size", "BUD-2024-009::CONSENT-004::p0", "0,418"),
        ("sentence_window", "BUD-2024-009::CONSENT-004::s0", "0,617"),
        ("semantic", "BUD-2024-009::sem1", "0,358"),
        ("propositional", "BUD-2024-009::CONSENT-004::prop5", "0,673"),
        ("contextual_retrieval", "BUD-2024-009::CONSENT-004", "0,465"),
        ("hierarchical", "BUD-2024-009::CONSENT-004", "0,418"),
    ]
    d.box(p, (24, 70, 446, 312),
          "<table><tr><th>Estrategia</th><th>Top-1</th><th>Coseno</th></tr>"
          + "".join(f"<tr><td>{a}</td><td><code>{b}</code></td><td><b>{c}</b></td></tr>" for a, b, c in rows)
          + "</table>",
          kind="beige", role="table")
    d.box(p, (456, 70, 696, 170),
          '<div class="t">La señal está</div>'
          "Todas aterrizan en <b>CONSENT-004</b>, el módulo de consentimiento y auditoría de un proyecto de "
          "sanidad. Lo que cambia es la confianza y el tamaño de lo que devuelven.",
          kind="mint")
    d.box(p, (456, 180, 696, 312),
          '<div class="t">¿Cuál gana?</div>'
          "Pregunta trampa: ganan distinto según qué optimices.<br/>"
          "<ul><li><b>Score</b>: propositional.</li><li><b>Contexto</b>: contextual.</li>"
          "<li><b>Coste</b>: structural, 0 $.</li><li><b>Legibilidad</b>: structural.</li></ul>",
          kind="lav")


def slide_hierarchical_demo(d: Deck) -> None:
    p = d.new("Hierarchical en la terminal",
              "--strategies hierarchical --queries \"GDPR compliance and audit logging\" --show-top-k 3 --resolve-parents",
              "Chunking III · avanzadas")
    d.code(p, (30, 70, 380, 160), """# chunking/strategies/hierarchical.py
Chunk(chunk_id=parent_id, ...,
      metadata={"level": "parent"})
Chunk(...,
      metadata={"level": "child",
                "parent_chunk_id": parent_id})""", "Padre e hijos en el mismo índice")
    d.code(p, (392, 70, 690, 160), """hierarchical: 77 chunks (17 padres + 60 hijos)
  2 obesos (max 1472) · 0 $
1. [0.4180] BUD-2024-009::CONSENT-004  (hijo)
2. [0.3070] BUD-2024-012::parent   ← padre entero
3. [0.3010] BUD-2024-012::EXPORT-003""", "Demo · ejecución real")
    d.box(p, (30, 170, 360, 312),
          '<div class="t">Lo interesante</div>'
          "Para una consulta abstracta, <b>un presupuesto completo</b> entra en el top-3. A veces el padre "
          "entero es mejor respuesta que un componente suelto.<br/>"
          '<span class="s">El retriever de la Sesión 8 decidirá qué nivel devolver.</span>',
          kind="mint")
    d.box(p, (372, 170, 690, 312),
          '<div class="t">¿Cuándo activarlo?</div>'
          "<ul><li><b>Útil</b>: manuales largos, documentos legales.</li>"
          "<li><b>Overkill</b>: FAQs, tickets cortos.</li>"
          "<li><b>Presupuestos</b>: en el límite; probablemente útil para consultas abstractas.</li></ul>",
          kind="lav")


def slide_late(d: Deck) -> None:
    p = d.new("La que no ejecutamos hoy", "Nuestro modelo de embeddings no da vectores por token",
              "Chunking III · avanzadas")
    d.image(p, (40, 62, 680, 322), "s07-late-chunking.png")
    d.html(p, (40, 326, 680, 345),
           '<div class="center s"><b>¿Cuándo compensa?</b> Documentos largos, modelo con contexto grande y '
           "re-embeber barato. En nuestro caso, todavía no.</div>")


def slide_cuadro(d: Deck) -> None:
    p = d.new("El cuadro de mando: toda la sesión en una tabla",
              "compare_chunkers.py · 17 presupuestos · huérfano &lt; 20 tokens · obeso &gt; 800 tokens",
              "Cierre")
    rows = [
        ("structural", "60", "78", "0", "1", "0", "0,00 s"),
        ("fixed_size", "63", "79", "0", "0", "0", "0,00 s"),
        ("recursive", "23", "187", "1", "0", "0", "0,01 s"),
        ("sentence_window", "78", "21", "34", "0", "0", "0,01 s"),
        ("semantic", "34", "112,5", "0", "1", "0,000094", "5,31 s"),
        ("propositional", "778", "11", "765", "0", "0,00755", "173 s"),
        ("contextual_retrieval", "60", "132,5", "0", "1", "0,140", "203 s"),
        ("hierarchical", "77", "81", "0", "2", "0", "0,01 s"),
    ]
    d.box(p, (24, 66, 470, 312),
          "<table><tr><th>Estrategia</th><th>Chunks</th><th>p50</th><th>Huérf.</th><th>Obesos</th>"
          "<th>$</th><th>Ingesta</th></tr>"
          + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
          + "</table>",
          kind="beige", role="table")
    d.box(p, (480, 66, 696, 168),
          '<div class="t">Tres lecturas</div>'
          "<ul><li><b>Coste</b>: de 0 $ a 0,14 $.</li>"
          "<li><b>Granularidad</b>: de 23 a 778 chunks.</li>"
          "<li><b>Degeneración</b>: de 0 a 765 huérfanos.</li></ul>",
          kind="mint")
    d.box(p, (480, 176, 696, 312),
          '<div class="t">La pregunta del día</div>'
          "Si fuera vuestro proyecto en producción: <b>¿con qué estrategia salís hoy?</b><br/><br/>"
          "Y más importante: <b>¿qué mediríais antes de cambiarla?</b>"
          '<br/><span class="s">recall@k formal, coste por consulta, latencia… (Sesión 11)</span>',
          kind="note")
    d.html(p, (30, 318, 690, 345),
           '<div class="center s">La métrica de hoy es informal: estadísticos + coseno del top-3 + inspección. '
           "No es recall@k, y lo decimos abiertamente.</div>")


# ===========================================================================

def build() -> None:
    d = Deck()
    d.template(0)
    slide_about(d)
    slide_agenda(d)
    slide_pipeline(d)
    slide_corpus(d)
    d.template(1)
    slide_sanity(d)
    d.template(2)
    slide_embedding(d)
    slide_metricas(d)
    slide_limites(d)
    slide_modelos(d)
    d.template(3)
    slide_dimensiones(d)
    slide_anatomia(d)
    slide_por_que_chunking(d)
    d.template(4)
    slide_doce(d)
    d.template(5)
    d.template(6)
    slide_mecanicas(d)
    slide_semantic(d)
    slide_propositional(d)
    d.template(7)
    slide_contextual_code(d)
    slide_gdpr(d)
    d.template(8)
    slide_hierarchical_demo(d)
    slide_late(d)
    slide_cuadro(d)
    d.template(9)
    d.template(10)
    d.template(11)
    d.save()


if __name__ == "__main__":
    render_svgs()
    build()
