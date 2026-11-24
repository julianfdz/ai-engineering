"""Genera el deck de la Sesión 7 (Embeddings y representación vectorial) para la edición 2026-10 (26/11/2026).

Mismas diapos que en la edición 2609 (las 12 originales de LIDR de plantilla-lidr-s07.pdf, sin tocar, y las 18
nuestras intercaladas detrás de la original que amplían), con lo que se ha añadido desde entonces:

- franja «En el código» en cada diapo propia, con ruta y línea verificadas contra la rama session_07_live_local
  (worktree ai-engineering-s07, ya con las cabeceras «Julián · Sesión 7»);
- franja «En los tests» donde hay un test que lo comprueba (los del Chunking Lab, en Rails);
- una diapo con los tests de la sesión;
- fondo blanco y grupo de transparencia por página (motor de la S2).

El deck de la 2609 sigue saliendo de build_deck.py (que además es el motor común); su PDF está en ../anterior-2609/.

    python build_deck_2610.py
    # → ../Sesion07-Julian-Fernandez.pdf
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("s02_deck", HERE.parent.parent / "s02" / "deck" / "build_deck.py")
s02 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s02)

base = s02.base   # el motor de la S7 (este mismo directorio)
base.TEMPLATE = HERE / "plantilla-lidr-s07.pdf"
base.OUTPUT = HERE.parent / "Sesion07-Julian-Fernandez.pdf"
H, W = base.H, base.W

C = "estimator/app/generation/rag/"
T = "estimator-web/test/"


class Deck(s02.Deck):
    """Deck de la S2 (franjas código/tests, fondo blanco) con el pie de la S7. Las diapos de la S7 llaman a
    d.new() sin saber de tests: d.con_tests() deja preparada la siguiente diapo con las dos franjas."""

    _siguiente_con_tests = False

    def con_tests(self) -> "Deck":
        self._siguiente_con_tests = True
        return self

    def new(self, title: str, sub: str = "", section: str = "", tests: bool | None = None) -> fitz.Page:
        if tests is None:
            tests, self._siguiente_con_tests = self._siguiente_con_tests, False
        return super().new(title, sub, section, tests=tests)

    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 7 · '
               f"Embeddings y representación vectorial · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=base.CSS)


def con_franjas(slide, codigo: str, tests: str | None = None):
    """Envuelve una diapo de la S7: la dibuja y le pone las franjas al pie."""
    def run(d: Deck, *args) -> None:
        if tests:
            d.con_tests()
        slide(d, *args)
        p = d.doc[-1]
        p._con_tests = bool(tests)  # d.doc[-1] es otro objeto Page: hay que volver a marcarlo
        d.codigo(p, codigo)
        if tests:
            d.tests(p, tests)
    return run


TEST_PAGO = (f"{T}models/rag/<b>strategy_test.rb</b> · <code>expensive_selected? flags the paid LLM strategies</code> "
             "(l. 25): el Lab avisa antes de lanzar una estrategia de pago")

def slide_hoy(d: Deck) -> None:
    """La de la 2609 con el TA de esta edición y el puente desde la S6, que dio Julián a este grupo."""
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
          '<span class="s">Teaching Assistant: Sisley Jiménez · dudas en el canal asíncrono.</span>',
          kind="lav")


hoy = con_franjas(slide_hoy,
                  f"Todo vive en <code>{C}</code> (<code>schemas.py</code>, <code>chunking/</code>, <code>embedding/</code>) "
                  "y <code>estimator/app/api/embeddings.py</code> · <b>Interfaz:</b> Chunking Lab "
                  "(<code>localhost:3000/rag/chunking_comparisons</code>) y terminal")
sanity = con_franjas(base.slide_sanity,
                     "estimator/scripts/<b>compare.py</b> · <code>cosine_similarity</code> (l. 43) · "
                     "<code>docker compose exec estimator python scripts/compare.py --text-a … --text-b …</code>")
ctv = con_franjas(base.slide_ctv,
                  f"rag/<b>schemas.py</b> · <code>Chunk</code> (l. 65) y <code>EmbeddedChunk</code> (l. 78) · "
                  "chunking/<b>base.py</b> · <code>count_tokens</code> (l. 30) · embedding/<b>embedder.py</b> · "
                  "<code>OpenAIEmbedder</code> (l. 47)")
metricas = con_franjas(base.slide_metricas,
                       "rag/analysis/<b>similarity.py</b> · <code>cosine_similarity</code> (l. 14) · "
                       "<code>percentile</code> (l. 24), el p50 y el p95 del Chunking Lab")
modelos = con_franjas(base.slide_modelos,
                      "embedding/<b>embedder.py</b> · <code>PRICE_PER_MILLION_TOKENS_USD = 0.02</code> (l. 36) · "
                      "<code>estimated_cost_usd</code> (l. 42) · <b>config.py</b> · "
                      "<code>EMBEDDING_MODEL = \"text-embedding-3-small\"</code> (l. 41)")
dimensiones = con_franjas(base.slide_dimensiones,
                          "scripts/<b>compare_chunkers.py</b> · <code>run_models</code> (l. 166) · "
                          "<code>build_embedder(dimensions)</code> (l. 89) · <code>--models small-1536,small-768</code> · "
                          "embedder.py · <code>dimensions</code> (l. 95)")
anatomia = con_franjas(base.slide_anatomia,
                       "chunking/<b>structural.py</b> · <code>render_component_text</code> (l. 33), la cabecera de "
                       "contexto · <code>component_metadata</code> (l. 72) · <code>JSONStructuralChunker</code> (l. 85)")
lab = con_franjas(base.slide_lab,
                  "<b>Interfaz:</b> Chunking Lab · <code>chunking_comparisons_controller.rb</code> · <code>create</code> "
                  "(l. 31) · rag/analysis/<b>comparison.py</b> · <code>ChunkingComparator</code> (l. 88) · huérfano "
                  "&lt; 20 y obeso &gt; 800 (l. 37-38)",
                  f"{T}controllers/rag/<b>chunking_comparisons_controller_test.rb</b> · <code>create runs the comparison, "
                  "persists it and redirects to show</code> (l. 65)")
S = C + "chunking/strategies/"
ESTRATEGIA = {
    "fixed": ("chunking/strategies/<b>fixed_size.py</b> · <code>CHUNK_SIZE_TOKENS = 512</code> (l. 26) · "
              "<code>chunk</code> (l. 35): ventanas de tokens sin mirar la estructura", None),
    "recursive": ("chunking/strategies/<b>recursive.py</b> · <code>SEPARATORS</code> (l. 30): párrafo → línea → "
                  "frase → palabra · <code>chunk</code> (l. 44)", None),
    "sentence": ("chunking/strategies/<b>sentence_window.py</b> · <code>WINDOW_SIZE = 2</code> (l. 27) · "
                 "<code>chunk</code> (l. 45): se embebe la frase y la ventana va en <code>metadata.window_text</code>",
                 None),
    "structural": ("chunking/<b>structural.py</b> · <code>JSONStructuralChunker</code> (l. 85) · <code>chunk</code> "
                   "(l. 90): un componente = un chunk, con cabecera de contexto", None),
    "semantic": ("chunking/strategies/<b>semantic.py</b> · <code>BREAKPOINT_THRESHOLD_AMOUNT = 95</code> (l. 32) · "
                 "<code>chunk</code> (l. 51): embebe durante la ingesta", TEST_PAGO),
    "propositional": ("chunking/strategies/<b>propositional.py</b> · <code>PropositionalChunker</code> (l. 51), "
                      "<code>gpt-4o-mini</code> con salida estructurada · <code>chunk</code> (l. 58)", TEST_PAGO),
    "contextual": ("chunking/strategies/<b>contextual_retrieval.py</b> · <code>ContextualRetrievalChunker</code> (l. 55), "
                   "<code>claude-sonnet-4-5</code> · necesita <code>ANTHROPIC_API_KEY</code>", TEST_PAGO),
    "hierarchical": ("chunking/strategies/<b>hierarchical.py</b> · <code>HierarchicalChunker</code> (l. 28) · "
                     "<code>chunk</code> (l. 31): padre = presupuesto, hijo = componente", None),
}
late = con_franjas(base.slide_late,
                   "No está en el código: embedding/<b>embedder.py</b> · <code>embed_many</code> (l. 62) pide un "
                   "vector por chunk; late chunking necesita un modelo que devuelva un vector por token")
cuadro = con_franjas(base.slide_cuadro,
                     "<code>{C}COMPARISON_REPORT.md</code> · <code>compare_chunkers.py --output-table --queries all</code> · "
                     "<b>Interfaz:</b> histórico del Chunking Lab (6 ejecuciones guardadas)".format(C=C))


def estrategia(d: Deck, key: str) -> None:
    codigo, tests = ESTRATEGIA[key]
    con_franjas(base.slide_estrategia, codigo, tests)(d, key)


def slide_tests(d: Deck) -> None:
    p = d.new("Los tests del Chunking Lab", "23 tests en 1,5 s · el servicio de embeddings se sustituye por un falso",
              "Cierre")
    d.codigo(p, "<code>docker compose exec estimator-web bin/rails test -v test/models/rag test/controllers/rag "
                "test/services/estimator_ai/embeddings_client_test.rb</code>")
    d.box(p, (24, 64, 696, 290),
          "<table><tr><th>Fichero</th><th>Tests</th><th>Qué comprueba</th></tr>"
          "<tr><td><code>models/rag/strategy_test.rb</code></td><td>4</td><td>Las 8 estrategias del catálogo, las tres "
          "gratuitas por defecto y cuáles son de pago</td></tr>"
          "<tr><td><code>controllers/rag/chunking_comparisons_controller_test.rb</code></td><td>8</td><td>Formulario, "
          "validaciones, un 400 o un 500 del servicio como aviso, guardar y mostrar la ejecución</td></tr>"
          "<tr><td><code>models/rag/comparison_response_test.rb</code></td><td>5</td><td>La respuesta JSON pasa a "
          "objetos tipados; costes agregados; datos del playground</td></tr>"
          "<tr><td><code>models/rag/chunking_comparison_test.rb</code></td><td>2</td><td>Al menos una estrategia y un "
          "top-k razonable; el payload se guarda y se recupera</td></tr>"
          "<tr><td><code>services/estimator_ai/embeddings_client_test.rb</code></td><td>4</td><td>El POST a "
          "<code>/embeddings/compare</code>; los errores 400 y 500; sin presupuestos no toca la red</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 298, 696, 340),
          "<b>Las estrategias de chunking (Python) no tienen tests todavía</b>: se validan con números, con "
          "<code>compare_chunkers.py</code> y el informe <code>COMPARISON_REPORT.md</code>.", kind="note", pad=5)


def build() -> None:
    d = Deck()
    d.template(0)                   # portada (original)
    hoy(d)
    d.template(1)                   # tres arquitecturas (original)
    sanity(d)
    d.template(2)                   # cinco patrones de error (original)
    ctv(d)
    metricas(d)
    modelos(d)
    d.template(3)                   # Matryoshka (original)
    dimensiones(d)
    anatomia(d)
    d.template(4)                   # cuatro familias (original)
    lab(d)
    estrategia(d, "fixed")
    estrategia(d, "recursive")
    d.template(5)                   # fixed vs recursive (original)
    estrategia(d, "sentence")
    estrategia(d, "structural")
    d.template(6)                   # sentence-window vs structural (original)
    estrategia(d, "semantic")
    estrategia(d, "propositional")
    estrategia(d, "contextual")
    d.template(7)                   # Contextual Retrieval (original)
    estrategia(d, "hierarchical")
    d.template(8)                   # hierarchical (original)
    late(d)
    cuadro(d)
    slide_tests(d)
    d.template(9)                   # cierre y S8 (original)
    d.template(10)                  # ROTI
    d.template(11)                  # gracias
    d.save()


if __name__ == "__main__":
    base.render_svgs()
    build()
