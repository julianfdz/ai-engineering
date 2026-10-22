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
import re
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
SVGS = ["s07-pipeline-hoy", "s07-anatomia-chunk", "s07-late-chunking", "s07-tamano-chunks"]
ESTRATEGIAS = ["fixed", "recursive", "sentence", "structural", "semantic", "propositional", "contextual",
               "hierarchical"]
SVGS += [f"s07-est-{n}" for n in ESTRATEGIAS]   # generados por diagramas_estrategias.py

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
TEXT_PT = (9, 13.5)    # rango del autoajuste del texto de las cajas
CODE_PT = (7, 10.5)    # y del código (además, sin partir líneas: ver Deck.flush)
TABLE_PT = (8, 11)     # cajas que son una tabla
MONO_EM = 0.6          # ancho de un carácter monoespaciado, en em


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def render_svgs() -> None:
    """Rasteriza los SVG de assets a PNG (solo si el SVG es más nuevo que su PNG)."""
    profile = Path(tempfile.gettempdir()) / "s07-deck-edge-profile"
    for name in SVGS:
        svg, png = ASSETS / f"{name}.svg", ASSETS / f"{name}.png"
        if png.exists() and png.stat().st_mtime >= svg.stat().st_mtime:
            continue
        width, height = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg.read_text(encoding="utf-8")).groups()
        before = png.stat().st_mtime if png.exists() else 0
        subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        f"--user-data-dir={profile}", "--force-device-scale-factor=2.5",
                        f"--window-size={width},{height}", f"--screenshot={png}", svg.as_uri()],
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
# Diapos (máximo 30: las 12 de la plantilla + 18 propias)
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: Chunk + Embed", "Del corpus limpio de la Sesión 6 a los vectores · pgvector llega en la Sesión 8",
              "Apertura")
    d.image(p, (20, 64, 470, 240), "s07-pipeline-hoy.png")
    d.box(p, (482, 68, 700, 238),
          '<div class="t">Al salir de hoy sabréis…</div>'
          "<ul><li>Qué es un chunk, un token y un vector.</li>"
          "<li>Elegir modelo de embeddings con criterio.</li>"
          "<li>Comparar 8 estrategias de chunking con datos.</li>"
          "<li>Defender una elección ante coste y calidad.</li></ul>",
          kind="mint")
    d.box(p, (20, 250, 352, 340),
          '<div class="t">El corpus</div>'
          "17 presupuestos · 60 componentes. Dos con trampa: <b>MONO-001</b>, una descripción de 1391 tokens, y "
          "un MVP con descripciones de una sola línea.",
          kind="beige")
    d.box(p, (364, 250, 700, 340),
          '<div class="t">Cómo trabajamos</div>'
          "Cada estrategia: la idea → el código → la demo. "
          '<span class="s">Teaching Assistant: George Kutsia · dudas en el canal asíncrono.</span>',
          kind="lav")


def slide_sanity(d: Deck) -> None:
    p = d.new("El ejercicio previo: vuestro sanity check",
              "text-embedding-3-small · coseno calculado a mano · tres parejas", "Apertura")
    rows = [
        ("A · cercanas", "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app",
         "Authorization service using JSON Web Tokens for a banking application", "0,596", "&gt; 0,6"),
        ("B · sin relación", "(la misma)", "Database migration from MySQL to PostgreSQL with zero downtime",
         "0,192", "&lt; 0,4"),
        ("C · genéricas", "Backend services", "API development", "0,541", "—"),
    ]
    d.box(p, (24, 68, 696, 190),
          "<table><tr><th>Pareja</th><th>Texto 1</th><th>Texto 2</th><th>Coseno</th><th>Esperado</th></tr>"
          + "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td><b>{v}</b></td><td>{e}</td></tr>"
                    for a, b, c, v, e in rows)
          + "</table>",
          kind="beige", role="table")
    d.box(p, (24, 202, 244, 340),
          '<div class="t">A: 0,596 &lt; 0,6</div>'
          "Mismo concepto, casi sin palabras en común. Los umbrales dependen del modelo y de la redacción.",
          kind="lav")
    d.box(p, (250, 202, 470, 340),
          '<div class="t">B: 0,19</div>'
          "Temas sin relación, bien separados. Entre 0,2 y 0,5 es normal para textos que no se parecen.",
          kind="mint")
    d.box(p, (476, 202, 696, 340),
          '<div class="t">C: 0,54, el aviso</div>'
          "El texto corto y genérico no discrimina. Por eso cada chunk lleva una cabecera de contexto.",
          kind="peach")


def slide_ctv(d: Deck) -> None:
    p = d.new("Chunk, token y vector", "Las tres palabras que usamos todo el rato", "Embeddings")
    d.image(p, (16, 62, 400, 310), "s07-espacio-semantico.png")
    d.box(p, (410, 66, 704, 146),
          '<div class="t">Chunk</div>'
          "El trozo de documento que se indexa y se recupera como una unidad. Es lo que el RAG le da al LLM.",
          kind="lav")
    d.box(p, (410, 152, 704, 232),
          '<div class="t">Token</div>'
          "La unidad en la que el modelo cuenta el texto: unos ¾ de palabra. Una página llena ≈ 700–1000 tokens.",
          kind="note")
    d.box(p, (410, 238, 704, 318),
          '<div class="t">Vector (embedding)</div>'
          "1536 números por chunk. Textos parecidos → vectores cercanos, aunque no compartan palabras.",
          kind="mint")
    d.html(p, (16, 322, 704, 345),
           '<div class="center"><b>Si un chunk está mal cortado, su vector lo representa mal… y ningún modelo lo '
           "arregla después.</b></div>")


def slide_metricas(d: Deck) -> None:
    p = d.new("Medir la similitud y sus límites", "Con vectores normalizados, las tres métricas ordenan igual",
              "Embeddings")
    d.image(p, (24, 62, 696, 196), "s07-metricas-similitud.png")
    d.box(p, (24, 206, 352, 340),
          '<div class="t">Coseno</div>'
          "Mide el ángulo, no la longitud. <code>text-embedding-3-small</code> devuelve vectores de norma 1, "
          "así que producto escalar = coseno. La métrica la marca el modelo, no es una decisión de arquitectura.",
          kind="mint")
    d.box(p, (368, 206, 696, 340),
          '<div class="t">Lo que un embedding NO resuelve</div>'
          "<ul><li><b>Números y fechas</b> → filtros sobre el metadata (S8).</li>"
          "<li><b>Palabras raras exactas</b> → búsqueda híbrida con BM25 (S10).</li>"
          "<li><b>Umbrales</b> → se calibran con tus datos.</li></ul>",
          kind="peach")


def slide_modelos(d: Deck) -> None:
    p = d.new("Elegir modelo de embeddings", "Precios y scores cambian cada pocos meses: verificar antes de decidir",
              "Embeddings")
    d.box(p, (24, 68, 462, 340),
          "<table><tr><th>Modelo</th><th>Dims</th><th>$ / M tokens</th><th>Notas</th></tr>"
          "<tr><td><b>text-embedding-3-small</b></td><td>1536</td><td>0,02</td><td>el caballo de batalla · Matryoshka</td></tr>"
          "<tr><td>text-embedding-3-large</td><td>3072</td><td>0,13</td><td>mejor calidad, 6,5× más caro</td></tr>"
          "<tr><td>Cohere embed-v3</td><td>—</td><td>0,10</td><td>fuerte en multilingüe</td></tr>"
          "<tr><td>Voyage voyage-3-large</td><td>—</td><td>≈ Cohere</td><td>optimizado para retrieval</td></tr>"
          "<tr><td>BAAI/bge-m3</td><td>1024</td><td>0 (GPU)</td><td>open source, multilingüe</td></tr>"
          "<tr><td>all-MiniLM-L6-v2</td><td>384</td><td>0 (CPU)</td><td>inglés, para prototipos</td></tr>"
          "</table>",
          kind="beige", role="table")
    d.box(p, (472, 68, 700, 252),
          '<div class="t">Cinco criterios</div>'
          "<ul><li><b>Dimensiones</b>: ¿cabe en RAM?</li>"
          "<li><b>Idioma</b>: briefs en español → multilingüe.</li>"
          "<li><b>Dominio</b>: se valida sobre tus datos.</li>"
          "<li><b>Coste</b>: API o self-hosted.</li>"
          "<li><b>Privacidad</b>: banca, sanidad → self-hosted.</li></ul>",
          kind="lav")
    d.box(p, (472, 262, 700, 340),
          '<div class="t">Nuestra decisión</div>'
          "<code>text-embedding-3-small</code>, 1536 dims: calidad sobrada, coste despreciable.",
          kind="mint")


def slide_dimensiones(d: Deck) -> None:
    p = d.new("¿Por qué no se comparan vectores de distinta dimensión?",
              "1536 contra 768 no da un número malo: da un número sin sentido", "Embeddings")
    d.box(p, (30, 68, 360, 168),
          '<div class="t">La matemática</div>'
          "El producto escalar <code>Σ A[i]·B[i]</code> empareja la coordenada <i>i</i> de uno con la del otro. "
          "Con 1536 frente a 768, <b>las 768 últimas no tienen pareja</b>: son espacios distintos.",
          kind="lav")
    d.code(p, (372, 68, 690, 168), """>>> np.dot(v1536, v768)
ValueError: shapes (1536,) and (768,) not aligned

-- pgvector (Sesión 8)
ERROR: different vector dimensions 1536 and 768""", "Si tienes suerte: el error salta")
    d.code(p, (30, 178, 360, 296), """# app/generation/rag/analysis/similarity.py
dot = sum(x * y for x, y in zip(a, b))
#                           ^^^ zip se para en la
#                    lista más corta: sin error""", "Si no la tienes: nuestro coseno en Python puro")
    d.box(p, (372, 178, 690, 296),
          '<div class="t">El bug silencioso, medido</div>'
          "Un vector de 1536 contra <b>sus propias</b> 768 primeras dimensiones:<br/>"
          '<span class="huge">0,689</span> &nbsp;en vez de <b>1,0</b>',
          kind="peach")
    d.box(p, (30, 306, 690, 345),
          "<b>Cómo se evita:</b> un modelo y una dimensión por índice · <code>assert len(a) == len(b)</code> · "
          "dos modelos distintos con 1536 dims tampoco son comparables.",
          kind="mint")


def slide_anatomia(d: Deck) -> None:
    p = d.new("El chunk de nuestro proyecto", "app/generation/rag/chunking/structural.py · la estrategia de referencia",
              "Embeddings")
    d.image(p, (30, 62, 690, 322), "s07-anatomia-chunk.png")
    d.html(p, (30, 326, 690, 345),
           '<div class="center s">El componente es lo que estimas; el chunk es lo que buscas. '
           "Con structural, son lo mismo.</div>")


def slide_lab(d: Deck) -> None:
    p = d.new("Cómo leer el Chunking Lab", "El mismo corpus, cuatro formas de partirlo", "Chunking")
    d.image(p, (14, 62, 500, 316), "s07-tamano-chunks.png")
    d.box(p, (510, 66, 706, 316),
          '<div class="t">Las columnas</div>'
          "<ul><li><b>p50</b>: el chunk típico; la mitad mide menos.</li>"
          "<li><b>p95</b>: el 95 % mide menos. Lejos de p50 = tamaños irregulares.</li>"
          '<li><b>Huérfano</b> (&lt; 20 tokens): <span class="r">malo</span>, sin contexto.</li>'
          '<li><b>Obeso</b> (&gt; 800 tokens): <span class="r">malo</span>, mezcla temas.</li>'
          "<li><b>Coste y segundos</b>: lo que cuesta la ingesta.</li></ul>",
          kind="beige")
    d.html(p, (14, 322, 706, 345),
           '<div class="center"><b>Lo que buscamos: cero huérfanos, cero obesos y un p50 con sentido para el '
           "documento.</b></div>")


# Una diapo por estrategia del código: diagrama con un ejemplo real + tres ideas en lenguaje llano.
ESTRATEGIA = {
    "fixed": ("Fixed-size", "Mecánica",
              "Cuenta 512 tokens y corta, sin mirar frases ni componentes. Repite 80 entre trozos.",
              "Línea base para comparar. Texto sin ninguna estructura.",
              "Parte palabras y frases. Aquí solo actúa en MONO-001."),
    "recursive": ("Recursive", "Mecánica",
                  "Corta por párrafos; si sigue siendo grande, por líneas, frases y, al final, palabras.",
                  "El punto de partida cuando no hay estructura: 400–512 tokens.",
                  "Si el documento cabe entero, lo deja en un chunk y mezcla temas."),
    "sentence": ("Sentence-window", "Mecánica",
                 "Cada frase es un chunk. Se busca por la frase y al LLM se le da con sus vecinas.",
                 "Prosa larga donde una frase concreta responde.",
                 "Frases cortas sin contexto: huérfanos con score alto que no sirven."),
    "structural": ("Structural", "Estructural",
                   "Respeta la forma del documento: un componente del JSON es un chunk, con su cabecera.",
                   "Datos con estructura: JSON, Markdown, HTML. La palanca de mayor retorno.",
                   "No parte lo demasiado grande: MONO-001 entra entero."),
    "semantic": ("Semantic", "Semántica",
                 "Embebe cada frase y corta donde la siguiente se parece menos a la anterior.",
                 "Prosa larga que cambia de tema sin avisar.",
                 "Cuesta embeddings en la ingesta. En texto estructurado, corta donde no debe."),
    "propositional": ("Propositional", "Semántica",
                      "Un LLM reescribe cada componente en frases cortas que se entienden solas.",
                      "Textos densos en hechos (legal, médico) y preguntas muy concretas.",
                      "Un LLM por componente. 13× más chunks, casi todos huérfanos."),
    "contextual": ("Contextual Retrieval", "Contextual",
                   "Un LLM escribe el contexto que le falta a cada chunk y se pega delante.",
                   "Chunks que pierden el sentido leídos solos. Afinar un RAG que ya funciona.",
                   "La más cara: 0,14 $ y 3,4 min aquí. Nuestra cabecera ya es una versión gratis."),
    "hierarchical": ("Hierarchical", "Estructural",
                     "Dos tamaños a la vez: el componente (hijo) para encontrar y el presupuesto (padre) para responder.",
                     "Documentos largos: manuales, contratos.",
                     "Indexa más y los padres pueden ser obesos. Demasiado para FAQs."),
}


def slide_estrategia(d: Deck, key: str) -> None:
    name, family, idea, bien, cuidado = ESTRATEGIA[key]
    n = ESTRATEGIAS.index(key) + 1
    p = d.new(f"{n}/8 · {name}", f"Familia {family.lower()}", "Chunking")
    d.image(p, (12, 62, 540, 340), f"s07-est-{key}.png")
    d.box(p, (548, 66, 708, 158), f'<div class="t">La idea</div>{idea}', kind="lav")
    d.box(p, (548, 164, 708, 252), f'<div class="t">Úsala para</div>{bien}', kind="mint")
    d.box(p, (548, 258, 708, 345), f'<div class="t">Cuidado con</div>{cuidado}', kind="peach")


def slide_late(d: Deck) -> None:
    p = d.new("Late chunking", "La técnica que no ejecutamos hoy: nuestro modelo no da vectores por token",
              "Chunking")
    d.image(p, (40, 62, 680, 322), "s07-late-chunking.png")
    d.html(p, (40, 326, 680, 345),
           '<div class="center s"><b>¿Cuándo compensa?</b> Documentos largos, modelo con contexto grande y '
           "re-embeber barato. En nuestro caso, todavía no.</div>")


def slide_cuadro(d: Deck) -> None:
    p = d.new("El cuadro de mando", "17 presupuestos · huérfano &lt; 20 tokens · obeso &gt; 800 tokens", "Cierre")
    rows = [
        ("structural", "60", "78", "0", "1", "0", "0 s"),
        ("fixed_size", "63", "79", "0", "0", "0", "0 s"),
        ("recursive", "23", "187", "1", "0", "0", "0 s"),
        ("sentence_window", "78", "21", "34", "0", "0", "0 s"),
        ("semantic", "34", "112,5", "0", "1", "0,0001", "5 s"),
        ("propositional", "778", "11", "765", "0", "0,0076", "173 s"),
        ("contextual_retrieval", "60", "132,5", "0", "1", "0,14", "203 s"),
        ("hierarchical", "77", "81", "0", "2", "0", "0 s"),
    ]
    d.box(p, (24, 66, 470, 300),
          "<table><tr><th>Estrategia</th><th>Chunks</th><th>p50</th><th>Huérf.</th><th>Obesos</th>"
          "<th>$</th><th>Ingesta</th></tr>"
          + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
          + "</table>",
          kind="beige", role="table")
    d.box(p, (480, 66, 696, 300),
          '<div class="t">La pregunta del día</div>'
          "Si fuera vuestro proyecto en producción: <b>¿con qué estrategia salís hoy?</b><br/><br/>"
          "Y más importante: <b>¿qué mediríais antes de cambiarla?</b>",
          kind="note")
    d.box(p, (24, 308, 696, 345),
          '<div class="center">El chunking pesa tanto como el modelo (Vectara, 2025) · más sofisticado no es mejor: '
          "recursive 1º, semantic 4º (Vecta, 2026) · <b>mide sobre tus datos</b></div>",
          kind="mint")


# ===========================================================================

def build() -> None:
    d = Deck()
    d.template(0)                   # portada
    slide_hoy(d)
    d.template(1)                   # tres arquitecturas
    slide_sanity(d)
    d.template(2)                   # cinco patrones de error
    slide_ctv(d)
    slide_metricas(d)
    slide_modelos(d)
    d.template(3)                   # Matryoshka
    slide_dimensiones(d)
    slide_anatomia(d)
    d.template(4)                   # cuatro familias
    slide_lab(d)
    slide_estrategia(d, "fixed")
    slide_estrategia(d, "recursive")
    d.template(5)                   # fixed vs recursive
    slide_estrategia(d, "sentence")
    slide_estrategia(d, "structural")
    d.template(6)                   # sentence-window vs structural
    slide_estrategia(d, "semantic")
    slide_estrategia(d, "propositional")
    slide_estrategia(d, "contextual")
    d.template(7)                   # Contextual Retrieval
    slide_estrategia(d, "hierarchical")
    d.template(8)                   # hierarchical
    slide_late(d)
    slide_cuadro(d)
    d.template(9)                   # cierre y S8
    d.template(10)                  # ROTI
    d.template(11)                  # gracias
    d.save()


if __name__ == "__main__":
    render_svgs()
    build()


