"""Genera el deck de la Sesión 2 (Primeros pasos de arquitectura CAG) de Julián Fernández.

Edición 2026-11 (24/11/2026). Reutiliza el motor de la S7 y la franja grande «En el código» de la S5, como los
decks de la S6 y la S11, y añade una segunda franja «En los tests» con el test que comprueba lo que cuenta la
diapo. Ficheros y líneas verificados contra la rama session_02_live_local (worktree ai-engineering-s02). Las
salidas son las de la ejecución en local del 23/11/2026 (../comandos/salidas/).

Diapos originales de LIDR: la portada (solo cambia el título), el ROTI y el «Gracias» salen tal cual de la
plantilla. Si se dispone del PDF oficial de la sesión (las Google Slides del Notion, exportadas como
plantilla-lidr-s02.pdf en esta carpeta), sus páginas se insertan SIN TOCAR en el orden de ORIGINALES y las
nuestras van detrás de la original que amplían.

    python build_deck.py
    # → ../Sesion02-Julian-Fernandez.pdf
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
base.OUTPUT = HERE.parent / "Sesion02-Julian-Fernandez.pdf"
H, W = base.H, base.W
OFICIAL = HERE / "plantilla-lidr-s02.pdf"

# Con las dos franjas, el contenido se estira hasta 312 en vez de 340.
CODIGO_SOLO = fitz.Rect(10, 344, W - 10, 386)
CODIGO_ALTO = fitz.Rect(10, 317, W - 10, 350)
TESTS_RECT = fitz.Rect(10, 353, W - 10, 386)


class Deck(s05.Deck):
    def new(self, title: str, sub: str = "", section: str = "", tests: bool = False) -> fitz.Page:
        """Como base.Deck.new, pero con fondo blanco opaco: sin él la página es transparente y algunos visores
        la pintan con la cuadrícula de transparencia."""
        base.Y1_REAL = 312 if tests else 340
        self.flush()
        page = self.doc.new_page(width=W, height=H)
        page.draw_rect(page.rect, color=None, fill=(1, 1, 1), overlay=False)
        page.show_pdf_page(base.BADGE, self.tpl, 1, clip=base.BADGE)
        head = f"<h1>{title}</h1>" + (f'<div class="sub">{sub}</div>' if sub else "")
        page.insert_htmlbox(fitz.Rect(80, 16, W - 80, 62), head, css=base.CSS)
        if section:
            self.footer(page, section)
        page._con_tests = tests  # type: ignore[attr-defined]
        return page

    def save(self) -> None:
        """Cada página declara su grupo de transparencia, como la plantilla de LIDR. insert_pdf y new_page no lo
        copian, y sin él el visor de Edge (motor de Adobe) mezcla las transparencias baldosa a baldosa y deja una
        cuadrícula de costuras blancas cada 200 px."""
        self.flush()
        for page in self.doc:
            self.doc.xref_set_key(page.xref, "Group", "<</S/Transparency/CS/DeviceRGB>>")
        super().save()

    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 2 · '
               f"Primeros pasos de arquitectura CAG · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=base.CSS)

    def _franja(self, page: fitz.Page, rect: fitz.Rect, label: str, ref: str, color: tuple, fondo: tuple,
                tinta: str, pt: float) -> None:
        page.draw_rect(rect, color=color, fill=fondo, width=1.2, radius=0.18)
        tag = fitz.Rect(rect.x0, rect.y0, rect.x0 + 112, rect.y1)
        page.draw_rect(tag, color=None, fill=color, radius=0.18)
        dy = (rect.height - 14) / 2
        page.insert_htmlbox(tag + (6, dy, -4, -2),
                            f'<div style="font-size:{pt + 0.5}pt;color:#ffffff;font-weight:bold;text-align:center">'
                            f"{label}</div>", css=base.CSS)
        page.insert_htmlbox(fitz.Rect(tag.x1 + 10, rect.y0 + 4, rect.x1 - 10, rect.y1 - 2),
                            f'<div style="font-size:{pt}pt;color:{tinta};line-height:1.28">{ref}</div>',
                            css=base.CSS + " code { color:#c7d2fe; font-size:0.95em; }", scale_low=0.65)

    def codigo(self, page: fitz.Page, ref: str) -> None:
        alto = getattr(page, "_con_tests", False)
        self._franja(page, CODIGO_ALTO if alto else CODIGO_SOLO, "&lt;/&gt; En el código", ref,
                     (0.39, 0.4, 0.95), (0.11, 0.12, 0.18), "#f3f4f6", 10.5 if alto else 11)

    def tests(self, page: fitz.Page, ref: str) -> None:
        """Segunda franja: el test que comprueba lo que cuenta la diapo."""
        self._franja(page, TESTS_RECT, "En los tests", ref, (0.13, 0.55, 0.38), (0.06, 0.16, 0.12),
                     "#ecfdf5", 10.5)


def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    page.add_redact_annot(fitz.Rect(48, 158, 470, 242), fill=False)
    page.add_redact_annot(fitz.Rect(48, 124, 330, 147), fill=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for y, line in ((191, "Sesión 2: Primeros pasos"), (232, "de arquitectura CAG")):
        page.insert_text((51, y), line, fontname="hebo", fontsize=34.5, color=(1, 1, 1))
    page.insert_text((51, 141), "MÓDULO 2: Arquitecturas CAG", fontname="hebo", fontsize=15, color=(1, 1, 1))


# ===========================================================================
# Apertura · Bloque 1
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: de estimaciones genéricas a un CAG que se mide",
              "Mismo modelo, misma pregunta: lo que cambia es el contexto y cómo se llama al modelo", "Apertura")
    d.codigo(p, "Todo vive en <code>estimator/app/</code> · rama <code>session_2_live</code> · un único endpoint "
                "<code>POST /api/v1/estimate</code> · <b>Interfaz:</b> terminal (<code>curl</code>) y Swagger "
                "(<code>localhost:8000/docs</code>)")
    bloques = [("1 · Problemas y puesta en común", "10'", "beige"),
               ("2 · La transcripción real: limpiar el input", "25'", "mint"),
               ("3 · Iterar el contexto: sí/no, formato, cantidad, prompt", "35'", "mint"),
               ("4 · Parámetros del modelo: tier, max_tokens, thinking", "20'", "lav"),
               ("5 · Evaluar la calidad: el score estructural", "15'", "lav"),
               ("6 · Cierre y puente a la Sesión 3", "15'", "beige")]
    for i, (t, m, k) in enumerate(bloques):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 68 + row * 62
        d.box(p, (x, y, x + 332, y + 54), f"<b>{t}</b><br/><span class='s'>{m}</span>", kind=k, pad=6)
    d.box(p, (24, 258, 696, 330),
          '<div class="t">El termómetro de toda la sesión</div>Cada respuesta trae <code>usage</code> (tokens), '
          "<code>latency_ms</code>, <code>finish_reason</code> y <code>validation.score</code>. Con esos cuatro "
          "números se compara cada cambio sin opinar.", kind="note")


def slide_errores(d: Deck) -> None:
    p = d.new("Bloque 1 · Errores típicos y su arreglo exprés", "Si más de tres personas tienen el mismo, se "
              "resuelve una vez en pantalla", "Bloque 1", tests=True)
    d.codigo(p, "app/<b>config.py</b> · <code>validate_api_key_for_provider</code> (l. 30) · <code>get_settings</code> "
                "con <code>@lru_cache</code> (l. 39) · services/<b>llm_service.py</b> · <code>_call_openai</code> (l. 264)")
    d.tests(p, "tests/<b>test_health.py</b> · <code>test_health_returns_200</code> (l. 9): si este pasa, la app "
               "importa y arranca · <code>uv run pytest</code> → <b>21 passed</b>")
    d.box(p, (24, 66, 696, 300),
          "<table><tr><th>Síntoma</th><th>Causa probable</th><th>Arreglo</th></tr>"
          "<tr><td><code>ModuleNotFoundError</code> al arrancar</td><td>Falta un <code>__init__.py</code> o la "
          "estructura no coincide</td><td>Comparar <code>app/</code> con el repositorio de referencia</td></tr>"
          "<tr><td><code>ValidationError</code> de Settings</td><td><code>.env</code> sin cargar o sin la clave del "
          "proveedor activo</td><td><code>OPENAI_API_KEY</code> si <code>LLM_PROVIDER=openai</code></td></tr>"
          "<tr><td>Import circular <code>main.py</code> ↔ <code>config.py</code></td><td><code>Settings()</code> a "
          "nivel de módulo</td><td>Llamar a <code>get_settings()</code> dentro de las funciones</td></tr>"
          "<tr><td>500 con respuesta vacía</td><td>Mala extracción del texto</td><td>OpenAI: "
          "<code>choices[0].message.content</code> · Anthropic: <code>content[0].text</code></td></tr>"
          "<tr><td>Timeouts</td><td>Modelo grande con prompt largo</td><td>Iterar con <code>gpt-4o-mini</code> o "
          "<code>claude-haiku-4-5</code></td></tr></table>",
          kind="beige", role="table")


def slide_setup(d: Deck) -> None:
    p = d.new("Setup: el servicio levantado y el primer sanity check", "Dos terminales: una con los logs, otra "
              "para las peticiones", "Bloque 1", tests=True)
    d.codigo(p, "<b>docker-compose.yml</b> · <code>env_file</code> (l. 23) · bind mount <code>./app</code> + "
                "<code>uvicorn --reload</code> (l. 33) · app/<b>main.py</b> · <code>/health</code> (l. 77)")
    d.tests(p, "<b>21 tests en 0,08 s sin llamar a OpenAI</b>: <code>uv run pytest -v</code> desde "
               "<code>estimator/</code> · tests/<b>conftest.py</b> · <code>client</code> (l. 13)")
    d.code(p, (24, 66, 420, 300), """docker compose up -d --build
docker compose ps
NAME        STATUS
estimator   Up 11 seconds (healthy)

curl -s localhost:8000/health
{"status":"healthy","version":"0.1.0",
 "environment":"development"}

curl … /api/v1/estimate  (short_transcription)
{"model": "gpt-4o-mini-2024-07-18",
 "score": 0.75, "latency_ms": 12623}""", label="Salida real (23/11)")
    d.box(p, (432, 66, 696, 300),
          '<div class="t">Dos reglas para todo el día</div><ul>'
          "<li>Un cambio en <code>app/</code> se aplica <b>al guardar</b>: bind mount + <code>--reload</code>.</li>"
          "<li>Un cambio en <code>.env</code> <b>no</b>: hay que recrear el contenedor con "
          "<code>docker compose up -d --force-recreate estimator</code>.</li></ul>"
          "Si el sanity check da 200 y <code>score ≥ 0.5</code>, el sistema está listo.", kind="mint")


# ===========================================================================
# Bloque 2 · la transcripción real
# ===========================================================================

def slide_cag(d: Deck) -> None:
    p = d.new("Qué es CAG: el contexto ya está en el prompt", "Cache Augmented Generation: el modelo no busca "
              "nada; lo que necesita saber se le inyecta antes de llamar", "Bloque 2.0")
    d.codigo(p, "context/<b>examples.py</b> · <code>CANONICAL_EXAMPLES</code> (l. 36): los 5 presupuestos de "
                "referencia · services/<b>llm_service.py</b> · <code>build_system_prompt</code> (l. 102)")
    d.box(p, (24, 70, 128, 128), '<div class="t center">usuario</div><div class="center s">transcripción</div>',
          kind="beige")
    d.box(p, (168, 62, 470, 136), '<div class="t center">system prompt + EJEMPLOS + transcripción</div>'
          '<div class="center s">los ejemplos son lo único que aporta el CAG</div>', kind="note")
    d.box(p, (510, 70, 590, 128), '<div class="t center">LLM</div>', kind="lav")
    d.box(p, (614, 70, 696, 128), '<div class="t center">estimación</div>', kind="mint")
    d.arrow(p, 130, 99, 166, 99)
    d.arrow(p, 472, 99, 508, 99)
    d.arrow(p, 592, 99, 612, 99)
    d.box(p, (24, 150, 352, 330),
          '<div class="t">¿Por qué CAG y no RAG?</div><ul>'
          "<li>Pocos ejemplos (5) y un dominio estable.</li>"
          "<li><b>Más simple</b>: sin vector store, sin búsqueda, sin embeddings.</li>"
          "<li><b>Más barato de operar</b>: cero infraestructura extra.</li>"
          "<li><b>Más fácil de depurar</b>: el prompt entero está en los logs.</li></ul>", kind="mint")
    d.box(p, (368, 150, 696, 330),
          '<div class="t">La contrapartida</div>Cada token de contexto se paga <b>en cada llamada</b>. Con la '
          "transcripción larga, el prompt pesa <b>8.493 tokens</b> de entrada con 3 ejemplos y "
          "<b>7.228</b> sin ellos.<br/><br/>Por eso en el Bloque 3 se mide cuánto contexto vale la pena. "
          "RAG llegará cuando el conjunto de referencia sea grande o cambie a menudo (Módulo 4).", kind="lav")


def slide_recorrido(d: Deck) -> None:
    p = d.new("Bloque 2.1 · Una petición, fichero a fichero", "Del curl a la respuesta JSON en nueve pasos",
              "Bloque 2.1", tests=True)
    d.codigo(p, "<b>main.py</b> l. 74 → routers/<b>estimations.py</b> l. 24 → schemas/<b>estimation.py</b> l. 20 → "
                "services/<b>llm_service.py</b> l. 185 · l. 102 · l. 264 → context/<b>examples.py</b> l. 36 → "
                "services/<b>evaluation.py</b> l. 32")
    d.tests(p, "tests/<b>test_estimate_endpoint.py</b> · <code>call_log</code> (l. 35): sustituye "
               "<code>_call_openai</code> por un falso y recorre el mismo camino sin gastar tokens")
    d.box(p, (24, 64, 696, 304),
          "<table><tr><th>#</th><th>Fichero</th><th>Qué hace</th></tr>"
          "<tr><td>1</td><td><code>main.py</code></td><td>Arranca FastAPI, configura structlog y monta el router</td></tr>"
          "<tr><td>2</td><td><code>routers/estimations.py</code></td><td>Entra la petición: request → "
          "<code>GenerationOptions</code></td></tr>"
          "<tr><td>3</td><td><code>schemas/estimation.py</code></td><td>El contrato: si la transcripción tiene &lt; 50 "
          "caracteres, 422 sin tocar código</td></tr>"
          "<tr><td>4</td><td><code>generate_estimation</code></td><td>Orquesta: preprocesado, prompt, proveedor, "
          "<code>latency_ms</code></td></tr>"
          "<tr><td>5</td><td><code>build_system_prompt</code></td><td>Rol + limpieza + tarifas + formato + ejemplos: "
          "<b>el CAG</b></td></tr>"
          "<tr><td>6</td><td><code>context/examples.py</code></td><td>Una fuente, tres formatos de salida</td></tr>"
          "<tr><td>7</td><td><code>_call_openai</code></td><td>La única línea que paga la factura</td></tr>"
          "<tr><td>8</td><td><code>evaluate_estimation_structure</code></td><td>Regex, sin LLM: <code>score</code> e "
          "<code>issues</code></td></tr>"
          "<tr><td>9</td><td>vuelta al router</td><td><code>EstimationResponse(**result, validation=…)</code></td></tr>"
          "</table>", kind="beige", role="table")


def slide_transcripcion(d: Deck) -> None:
    p = d.new("Bloque 2.2 · La transcripción real: Acme Foods", "Unas 5.000 palabras de reunión: kickoff con el "
              "cliente + deep-dive técnico", "Bloque 2.2", tests=True)
    d.codigo(p, "app/fixtures/<b>long_transcription.txt</b> · services/<b>evaluation.py</b> · "
                "<code>_HEADER_ROW_RE</code> (l. 21) exige la cabecera exacta <code>| Task | Hours | Cost</code>")
    d.tests(p, "tests/<b>test_evaluation.py</b> · <code>test_missing_table_is_detected</code> (l. 49): sin la tabla "
               "esperada, <code>has_breakdown_table=False</code> y el issue lo dice")
    d.box(p, (24, 64, 330, 304),
          '<div class="t">Qué buscar en la estimación</div><ul>'
          "<li>Requisitos implícitos: PWA, WCAG, datos solo en la UE.</li>"
          "<li>Divagaciones tomadas como requisitos («algo simple» + «AI dashboards»).</li>"
          "<li>El matiz <b>SAP → BCN-Touch</b>.</li>"
          "<li>Precios coherentes con los ejemplos.</li>"
          "<li>Qué dicen <code>score</code> e <code>issues</code>.</li></ul>", kind="mint")
    d.code(p, (342, 64, 696, 304), """preprocessing = none   (gpt-4o-mini)
score 0.625 · 20.210 ms
usage 8.493 in / 957 out

| Task | Description | Hours | Cost (EUR) |
|------|-------------|------:|------------|
| Requirements Analysis … | … | 24 | 1,500 |

issues:
 - Missing breakdown table with
   'Task | Hours | Cost' header""", label="Salida real")


def slide_limpieza(d: Deck) -> None:
    p = d.new("Bloques 2.3 y 2.4 · Limpiar el input: una llamada o dos", "Inline cleaning amplía el system "
              "prompt; two_phase extrae requisitos primero y estima después", "Bloques 2.3-2.4", tests=True)
    d.codigo(p, "services/<b>llm_service.py</b> · <code>INLINE_CLEANING_BLOCK</code> (l. 66) · "
                "<code>extract_requirements</code> (l. 142) · la rama <code>if opts.preprocessing == \"two_phase\"</code> "
                "(l. 199)")
    d.tests(p, "tests/<b>test_estimate_endpoint.py</b> · <code>test_two_phase_invokes_llm_twice_and_fills_extracted</code> "
               "(l. 62): dos llamadas y la segunda recibe los requisitos, no la transcripción")
    d.box(p, (24, 64, 696, 196),
          "<table><tr><th>Modo</th><th>Llamadas</th><th>Tokens in / out</th><th>Fase 1 (in / out)</th>"
          "<th>Latencia</th><th>score</th></tr>"
          "<tr><td><code>none</code></td><td>1</td><td>8.493 / 957</td><td>—</td><td>20,2 s</td><td>0.625</td></tr>"
          "<tr><td><code>inline_cleaning</code></td><td>1</td><td>8.558 / 753</td><td>—</td><td>13,0 s</td>"
          "<td>0.75</td></tr>"
          "<tr><td><code>two_phase</code></td><td>2</td><td>1.758 / 624</td><td>7.190 / 395</td><td>21,9 s</td>"
          "<td>0.75</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 206, 352, 304),
          '<div class="t">Lectura</div>Inline cleaning cuesta <b>65 tokens</b> más y ya sube el score. Two-phase '
          "reparte el trabajo: la estimación recibe <b>1.758</b> tokens en vez de 8.493, pero la fase 1 lee la "
          "transcripción entera.", kind="mint")
    d.box(p, (368, 206, 696, 304),
          '<div class="t">No hay respuesta universal</div>Con 5.000 palabras de ruido, two-phase merece la pena. '
          "Con un brief limpio de 200 palabras, no. <b>Más llamadas al LLM no siempre es mejor.</b>", kind="note")


def slide_requisitos(d: Deck) -> None:
    p = d.new("Two-phase: lo que devuelve la fase 1", "El campo extracted_requirements ya es accionable por sí "
              "solo", "Bloque 2.4")
    d.codigo(p, "services/<b>llm_service.py</b> · <code>EXTRACTION_SYSTEM_PROMPT</code> (l. 76) · "
                "<code>EXTRACTION_MAX_TOKENS = 1500</code> · schemas/<b>estimation.py</b> · "
                "<code>extracted_requirements</code> y <code>preprocessing_*_tokens</code>")
    d.code(p, (24, 64, 450, 332), """## Functional Requirements
- Develop a custom reservation system for fifteen
  restaurants.
- Support multi-country operations with multi-language
  capabilities (Spanish, Catalan, Portuguese, English).
- Integrate with existing loyalty program …
- Enable configurable deposit rules and no-show fee
  management per restaurant.

## Non-Functional Requirements
- Ensure system is GDPR-compliant, including data
  export and erasure features.
- Achieve WCAG AA accessibility standards.

## Integrations
- Integrate with existing loyalty backend (Java, Spring
  Boot, REST).
- Connect to BCN-Touch POS system …""", label="07_two_phase · extracted_requirements (extracto)")
    d.box(p, (462, 64, 696, 332),
          '<div class="t">Fíjate en</div><ul>'
          "<li>Sale <b>BCN-Touch</b>, no SAP: la contradicción se resolvió.</li>"
          "<li>Aparecen requisitos enterrados: depósitos configurables, GDPR con exportación y borrado, WCAG AA.</li>"
          "<li>Es Markdown limpio: se puede revisar antes de estimar.</li>"
          "<li>Coste de la fase 1: <b>7.190 + 395</b> tokens.</li></ul>", kind="mint")


# ===========================================================================
# Bloque 3 · iterar el contexto
# ===========================================================================

def slide_con_sin(d: Deck) -> None:
    p = d.new("Bloque 3.1 · Con contexto y sin contexto", "El modelo es el mismo y la pregunta es la misma: "
              "solo cambia el contexto inyectado", "Bloque 3.1", tests=True)
    d.codigo(p, "services/<b>llm_service.py</b> · <code>if use_examples and num_examples &gt; 0</code> (l. 121) · "
                "schemas/<b>estimation.py</b> · campo <code>use_examples</code>")
    d.tests(p, "tests/<b>test_estimate_endpoint.py</b> · <code>test_use_examples_false_omits_examples_block</code> "
               "(l. 123): sin ejemplos, el system prompt no lleva «EXAMPLE 1»")
    d.box(p, (24, 64, 352, 300),
          '<div class="t r">use_examples = false</div><span class="huge">0.375</span><br/>'
          "7.228 tokens de entrada · 1.034 de salida<ul>"
          "<li>Sin título H2</li><li>Sin tabla <code>Task | Hours | Cost</code></li>"
          "<li>Sin totales</li></ul>"
          "Cada tarea en su propio bloque con viñetas: no se parece a nada de la casa.", kind="peach")
    d.box(p, (368, 64, 696, 300),
          '<div class="t k">use_examples = true</div><span class="huge">0.75</span><br/>'
          "8.493 tokens de entrada · 784 de salida<ul>"
          "<li>Título, tabla, totales, equipo y duración</li>"
          "<li>Falla lo que el contexto no arregla: <b>las sumas</b> (400 h declaradas, 308 en filas)</li></ul>"
          "<b>Esto es CAG</b>: 1.265 tokens de ejemplos doblan el score.", kind="mint")


def slide_formato(d: Deck) -> None:
    p = d.new("Bloque 3.2 · El formato del contexto se contagia", "Los mismos tres ejemplos, escritos de tres "
              "maneras", "Bloque 3.2", tests=True)
    d.codigo(p, "context/<b>examples.py</b> · <code>format_examples_for_prompt</code> (l. 392) · "
                "<code>_format_markdown</code> (l. 408) · <code>_format_json</code> (l. 419) · "
                "<code>_format_narrative</code> (l. 437)")
    d.tests(p, "tests/<b>test_examples_format.py</b> · <code>test_format_json_is_valid_json</code> (l. 28) · "
               "tests/<b>test_estimate_endpoint.py</b> · <code>test_example_format_json_returns_200</code> (l. 96)")
    d.box(p, (24, 64, 696, 170),
          "<table><tr><th>example_format</th><th>Tokens in</th><th>Latencia</th><th>score</th><th>Qué devolvió</th></tr>"
          "<tr><td><code>markdown</code></td><td>8.493</td><td>14,1 s</td><td>0.75</td><td>La tabla de la casa</td></tr>"
          "<tr><td><code>json</code></td><td>9.081</td><td>20,4 s</td><td><span class='r'>0.25</span></td>"
          "<td>Un bloque <code>```json</code> con la misma forma que los ejemplos</td></tr>"
          "<tr><td><code>narrative</code></td><td>8.176</td><td>19,4 s</td><td>0.5</td><td>Prosa con títulos, sin "
          "tabla ni totales</td></tr></table>", kind="beige", role="table")
    d.box(p, (24, 180, 352, 304),
          '<div class="t">El modelo imita lo que ve</div>Con ejemplos en JSON, contesta en JSON. El evaluador busca '
          "Markdown, así que el score se hunde aunque la estimación sea razonable.", kind="note")
    d.box(p, (368, 180, 696, 304),
          '<div class="t">Lección</div>El formato del contexto no es estético: <b>es una instrucción implícita</b>. '
          "Si el evaluador y los ejemplos no hablan el mismo formato, se mide mal.", kind="lav")


def slide_cantidad(d: Deck) -> None:
    p = d.new("Bloque 3.3 · Cantidad de ejemplos: el rendimiento decreciente",
              "Los tokens suben en línea recta; la calidad, no", "Bloque 3.3", tests=True)
    d.codigo(p, "context/<b>examples.py</b> · <code>select_examples(n)</code> (l. 387) · schemas/<b>estimation.py</b> "
                "· <code>num_examples</code> con <code>ge=0, le=5</code> (l. 33)")
    d.tests(p, "tests/<b>test_examples_format.py</b> · <code>test_select_examples_caps_at_available</code> (l. 56) · "
               "<code>test_canonical_examples_have_calibrated_totals</code> (l. 64)")
    d.box(p, (24, 64, 440, 304),
          "<table><tr><th>num_examples</th><th>Tokens in</th><th>Tokens out</th><th>Latencia</th><th>score</th></tr>"
          "<tr><td>0</td><td>7.228</td><td>982</td><td>12,7 s</td><td>0.5</td></tr>"
          "<tr><td>1</td><td>7.676</td><td>775</td><td>14,8 s</td><td>0.625</td></tr>"
          "<tr><td>3</td><td>8.493</td><td>898</td><td>18,1 s</td><td>0.625</td></tr>"
          "<tr><td>5</td><td>9.388</td><td>753</td><td>13,6 s</td><td>0.625</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (452, 64, 696, 304),
          '<div class="t">Lectura</div><ul>'
          "<li>Cada ejemplo cuesta unos <b>430 tokens</b> en <b>cada</b> llamada.</li>"
          "<li>El salto está entre 0 y 1; de 1 a 5 el score no se mueve.</li>"
          "<li>Con una sola ejecución por fila, la latencia es ruido: no saques conclusiones de ella.</li></ul>"
          "El punto dulce de este proyecto: <b>pocos ejemplos buenos</b>.", kind="mint")


def slide_prompt(d: Deck) -> None:
    p = d.new("Bloque 3.4 · El system prompt como multiplicador", "Una sola línea cambia la forma de toda la "
              "respuesta, sin un token más de contexto", "Bloque 3.4", tests=True)
    d.codigo(p, "services/<b>llm_service.py</b> · <code>PROMPT_OUTPUT_BASIC</code> (l. 40) · "
                "<code>PROMPT_OUTPUT_STRUCTURED</code> (l. 42) · el interruptor <code>ACTIVE_OUTPUT_PROMPT</code> "
                "(l. 63)")
    d.tests(p, "tests/<b>test_evaluation.py</b> · <code>test_well_formed_estimation_passes_all_checks</code> (l. 13): "
               "la forma que pide el prompt estructurado saca 1.0")
    d.code(p, (24, 64, 360, 196), """# l. 63 — cambiar y guardar:
ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_STRUCTURED

# en los logs, al instante:
WatchFiles detected changes in
'app/services/llm_service.py'. Reloading...""", label="El cambio en directo")
    d.box(p, (372, 64, 696, 196),
          "<table><tr><th></th><th>BASIC</th><th>STRUCTURED</th></tr>"
          "<tr><td>score</td><td>0.625</td><td><b>0.75</b></td></tr>"
          "<tr><td>Tokens in / out</td><td>8.493 / 795</td><td>8.598 / 568</td></tr>"
          "<tr><td>Sección de riesgos</td><td>no</td><td><b>sí</b></td></tr>"
          "<tr><td>Totales</td><td>falta «Total cost»</td><td>320 h · 20.000 €</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 206, 696, 304),
          '<div class="t">Lo que dice el número</div>El prompt estructurado consigue todas las secciones y una '
          "respuesta un 30 % más corta. No llega al techo por una sola razón: <b>las filas siguen sin sumar el "
          "total</b> (292 h frente a 320). Eso no lo arregla el prompt: lo vemos en la siguiente.", kind="mint")


def slide_sumas(d: Deck) -> None:
    p = d.new("Lo que el prompt no arregla: las sumas", "En las 19 peticiones del 23/11, ninguna tabla sumó su "
              "total", "Bloque 3.4", tests=True)
    d.codigo(p, "services/<b>evaluation.py</b> · <code>hours_match</code> con tolerancia ±1 h (l. 81) · "
                "<code>cost_match</code> con tolerancia ±2 % (l. 87)")
    d.tests(p, "tests/<b>test_evaluation.py</b> · <code>test_mismatched_total_hours_is_flagged</code> (l. 39): un "
               "total falseado da <code>hours_match=False</code> y el issue «Total hours mismatch»")
    d.box(p, (24, 64, 440, 304),
          "<table><tr><th>Ejecución</th><th>Horas declaradas</th><th>Suma de filas</th></tr>"
          "<tr><td>prompt STRUCTURED</td><td>320</td><td>292</td></tr>"
          "<tr><td>two_phase</td><td>348</td><td>336</td></tr>"
          "<tr><td>inline_cleaning</td><td>324</td><td>274</td></tr>"
          "<tr><td>con ejemplos (3)</td><td>400</td><td>308</td></tr>"
          "<tr><td>gpt-4o</td><td>418</td><td>432</td></tr></table>", kind="beige", role="table")
    d.box(p, (452, 64, 696, 304),
          '<div class="t">Por qué pasa</div>El modelo escribe el total como un texto más, no lo calcula. '
          "Ni el modelo grande lo hace bien.<br/><br/>"
          "<b>En la Sesión 4</b> se resuelve en el código: un schema con validadores obliga a que las fases sumen el "
          "total y re-pregunta al modelo si no.", kind="note")


# ===========================================================================
# Bloque 4 · parámetros del modelo
# ===========================================================================

def slide_tier(d: Deck) -> None:
    p = d.new("Bloque 4.1 · Tier de modelo: económico frente a premium", "Se cambia por petición con el campo "
              "model, sin reiniciar", "Bloque 4.1", tests=True)
    d.codigo(p, "services/<b>llm_service.py</b> · <code>model = opts.model or settings.LLM_MODEL</code> (l. 210) · "
                "<b>config.py</b> · <code>@lru_cache</code> (l. 39): el <code>.env</code> se lee una vez")
    d.tests(p, "tests/<b>test_estimate_endpoint.py</b> · <code>test_model_override_is_passed_to_provider</code> "
               "(l. 111): <code>\"model\": \"gpt-4o\"</code> llega tal cual al proveedor")
    d.box(p, (24, 64, 440, 210),
          "<table><tr><th>Modelo</th><th>score</th><th>Latencia</th><th>Tokens in / out</th><th>Coste</th></tr>"
          "<tr><td><code>gpt-4o-mini</code></td><td>0.75</td><td>14,6 s</td><td>8.493 / 733</td><td>0,0017 $</td></tr>"
          "<tr><td><code>gpt-4o</code></td><td>0.75</td><td>8,0 s</td><td>8.493 / 807</td><td>0,0293 $</td></tr>"
          "</table><span class='s'>Coste con la tabla de precios del Anexo B: 0,15 / 0,60 $ y 2,50 / 10 $ por "
          "millón de tokens.</span>", kind="beige", role="table")
    d.box(p, (452, 64, 696, 210),
          '<div class="t">≈ 17 veces más caro</div>Mismo score. Con un buen prompt, el económico aguanta.<br/>'
          "Itera siempre con el económico y prueba el premium al final.", kind="mint")
    d.box(p, (24, 220, 696, 304),
          '<div class="t">Cambiar de proveedor sí pide reiniciar</div><code>LLM_PROVIDER=anthropic</code> vive en '
          "<code>.env</code> y <code>get_settings()</code> está en caché: <code>docker compose up -d --force-recreate "
          "estimator</code>. Ni <code>restart</code> ni el <code>--reload</code> bastan.", kind="lav")


def slide_parametros(d: Deck) -> None:
    p = d.new("Bloque 4.2 · max_tokens, finish_reason y razonamiento", "Una estimación cortada que llega al "
              "cliente es vergonzosa", "Bloque 4.2", tests=True)
    d.codigo(p, "services/<b>llm_service.py</b> · <code>finish_reason</code> (l. 278) · aviso "
                "<code>thinking_budget_ignored_for_provider</code> (l. 226) · <code>_call_anthropic</code> y "
                "<code>thinking</code> (l. 321)")
    d.tests(p, "tests/<b>test_estimate_endpoint.py</b> · <code>test_max_tokens_low_propagates_finish_reason_length</code> "
               "(l. 81) · tests/<b>test_evaluation.py</b> · <code>test_finish_reason_length_fails_check</code> (l. 58)")
    d.code(p, (24, 64, 380, 304), """"max_tokens": 200
{
  "finish_reason": "length",
  "score": 0.25,
  "issues": [
    "Missing totals section …",
    "Missing recommended team section",
    "Missing estimated duration in weeks",
    "Response truncated or unexpected
     finish_reason='length'"
  ]
}""", label="21_max_tokens_200 · salida real")
    d.box(p, (392, 64, 696, 178),
          '<div class="t">Regla</div>Fija siempre <code>max_tokens</code> y comprueba <code>finish_reason</code>. '
          "La tabla se cortó en la primera fila.", kind="mint")
    d.box(p, (392, 188, 696, 304),
          '<div class="t">thinking_budget (solo Anthropic)</div>Con OpenAI se ignora y queda en los logs:<br/>'
          "<code>[warning] thinking_budget_ignored_for_provider provider=openai</code><br/>"
          "Con Anthropic, el razonamiento se factura como salida: compensa en estimaciones complejas, no en las "
          "simples.", kind="lav")


# ===========================================================================
# Bloque 5 · evaluación
# ===========================================================================

def slide_niveles(d: Deck) -> None:
    p = d.new("Bloque 5.1 · ¿Cómo sabemos si 100 estimaciones son buenas?", "No hay respuesta «correcta»: hay "
              "criterios explícitos", "Bloque 5.1", tests=True)
    d.codigo(p, "services/<b>evaluation.py</b> · <code>evaluate_estimation_structure</code> (l. 32) · "
                "<code>checks</code> (l. 94) · <code>score = round(sum(checks) / len(checks), 3)</code> (l. 104)")
    d.tests(p, "tests/<b>test_evaluation.py</b>: 6 tests con presupuestos conocidos · "
               "<code>test_well_formed_estimation_anthropic_end_turn_passes</code> (l. 32): <code>end_turn</code> "
               "también cuenta como fin correcto")
    niveles = [("Nivel 1 · Estructural", "automatizable", "¿Están las secciones? ¿Cuadran los números? "
                "¿<code>finish_reason=stop</code>? <b>Es lo que hay hoy.</b>", "mint"),
               ("Nivel 2 · Coherencia", "semiautomático", "¿Precios en el rango de los ejemplos? ¿Duración "
                "coherente con horas y equipo?", "lav"),
               ("Nivel 3 · Utilidad", "humano", "¿Un PM la usaría de punto de partida? ¿Los riesgos son "
                "concretos o de plantilla?", "peach")]
    for i, (t, s, b, k) in enumerate(niveles):
        x = 24 + i * 226
        d.box(p, (x, 64, x + 216, 196), f'<div class="t">{t}</div><span class="s">{s}</span><br/>{b}', kind=k)
    d.box(p, (24, 206, 696, 304),
          '<div class="t">Las ocho comprobaciones del nivel 1</div>título H2 · tabla <code>Task | Hours | Cost</code> · '
          "totales · equipo · duración · suma de horas (±1 h) · suma de coste (±2 %) · <code>finish_reason</code>. "
          "<b>score = superadas / 8.</b> Pura regex: cero tokens.", kind="beige")


def slide_handson(d: Deck) -> None:
    p = d.new("Bloque 5.2 · Hands-on: comprobar la sección de riesgos", "Un check nuevo en tres sitios, y lo que "
              "rompe al añadirlo", "Bloque 5.2", tests=True)
    d.codigo(p, "services/<b>evaluation.py</b> · <code>has_risks_section</code> en <code>checks</code> (l. 94) y en "
                "<code>issues</code> · schemas/<b>estimation.py</b> · <code>StructureCheck</code> (l. 75) · el router "
                "no se toca")
    d.tests(p, "Tras el cambio fallan <b>2 tests</b>: <code>test_well_formed_estimation_passes_all_checks</code> (l. 13) "
               "y el de <code>end_turn</code> (l. 32) → <code>assert 0.889 == 1.0</code>")
    d.code(p, (24, 64, 384, 304), """has_risks_section = bool(
    re.search(r"##\\s+(Risks?|Risks?\\s+and"
              r"\\s+assumptions)", text,
              re.IGNORECASE)
)
# + en checks, en issues
# + has_risks_section: bool en StructureCheck

Reevaluando las salidas guardadas:
17_prompt_basic       risks=False  0.556
18_prompt_structured  risks=True   0.778""", label="El cambio y su efecto")
    d.box(p, (396, 64, 696, 304),
          '<div class="t">Por qué fallan dos tests</div>Los <b>cinco ejemplos canónicos no tienen sección de '
          "riesgos</b>. Ahora sacan 8/9 = 0.889.<br/><br/>"
          "Y como el modelo imita los ejemplos (3.2), con el prompt básico tampoco la escribe. Para que el check "
          "tenga sentido hay que <b>añadir riesgos a los ejemplos</b> o pedirlos en el prompt, y actualizar los "
          "tests.", kind="note")


def slide_tests(d: Deck) -> None:
    p = d.new("Los tests de la sesión: todo lo de hoy, sin gastar un token",
              "21 tests en 0,08 s: el falso de _call_openai sustituye a la red", "Bloque 5")
    d.codigo(p, "<code>cd estimator</code> · <code>uv run pytest -v</code> · uno solo: "
                "<code>uv run pytest tests/test_evaluation.py::test_missing_table_is_detected -v</code>")
    d.box(p, (24, 64, 696, 332),
          "<table><tr><th>Fichero</th><th>Tests</th><th>Qué comprueba</th><th>Bloque</th></tr>"
          "<tr><td><code>test_health.py</code></td><td>1</td><td>La app arranca y <code>/health</code> da 200</td>"
          "<td>1</td></tr>"
          "<tr><td><code>test_estimate_endpoint.py</code></td><td>6</td><td>two_phase = 2 llamadas · max_tokens=200 → "
          "length · json en el prompt · use_examples=false · override de model</td><td>2.4 · 3.1 · 3.2 · 4.1 · 4.2</td>"
          "</tr>"
          "<tr><td><code>test_examples_format.py</code></td><td>8</td><td>Los tres formatos · "
          "<code>select_examples</code> · las filas de cada ejemplo suman su total</td><td>3.2 · 3.3</td></tr>"
          "<tr><td><code>test_evaluation.py</code></td><td>6</td><td>Un presupuesto bien formado saca 1.0 · totales "
          "falseados · sin tabla · <code>length</code></td><td>5</td></tr></table>",
          kind="beige", role="table")


# ===========================================================================
# Bloque 6 · cierre
# ===========================================================================

def slide_mapa(d: Deck) -> None:
    p = d.new("Recapitulación: una arquitectura CAG funcional", "Una API delgada, contexto curado, una llamada "
              "al modelo y una capa de validación", "Bloque 6")
    d.codigo(p, "<code>schemas/estimation.py</code> · <code>context/examples.py</code> · "
                "<code>services/llm_service.py</code> · <code>services/evaluation.py</code> · "
                "<code>routers/estimations.py</code> · <code>docker-compose.yml</code>")
    d.box(p, (24, 64, 696, 240),
          "<table><tr><th>Lo que había al llegar</th><th>Lo que hay ahora</th></tr>"
          "<tr><td>Un endpoint con estimaciones genéricas</td><td>Preprocesado configurable: none, inline_cleaning, "
          "two_phase</td></tr>"
          "<tr><td>Ejemplos puestos a ojo</td><td>Contexto CAG medido en formato y cantidad</td></tr>"
          "<tr><td>«Genera una estimación»</td><td>Un system prompt que fija la estructura</td></tr>"
          "<tr><td>El modelo por defecto</td><td>Modelo, <code>max_tokens</code> y <code>thinking_budget</code> "
          "elegidos a conciencia</td></tr>"
          "<tr><td>«Parece que está bien»</td><td>Evaluación estructural de nivel 1 con score e issues</td></tr>"
          "</table>", kind="beige", role="table")
    d.box(p, (24, 250, 696, 332),
          '<div class="t">La respuesta de entrevista</div>«¿Cómo construirías un sistema con LLM?» Exactamente esto: '
          "valida la entrada, construye el prompt con contexto curado, llama al modelo y valida la salida. "
          "Lo demás son adornos.", kind="mint")


def slide_s3(d: Deck) -> None:
    p = d.new("Lo que todavía no tenemos: Sesión 3", "Wrappers de modelos: fallback, streaming, logging y "
              "trazabilidad", "Bloque 6")
    d.codigo(p, "Todo pasa hoy por <code>_call_openai</code> / <code>_call_anthropic</code> en "
                "<code>services/llm_service.py</code>: ese es el punto que la Sesión 3 convierte en un wrapper")
    preguntas = [("¿Y si la API de OpenAI se cae?", "No hay fallback de proveedor."),
                 ("¿Y si quiero ver la estimación mientras se genera?", "No hay streaming."),
                 ("¿Dónde están las estimaciones de hoy?", "No hay registro persistente."),
                 ("¿Cómo lo usa alguien sin curl?", "No hay interfaz.")]
    for i, (q, a) in enumerate(preguntas):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 64 + row * 110
        d.box(p, (x, y, x + 332, y + 100), f'<div class="t">{q}</div>{a}', kind="lav" if row else "mint")
    d.box(p, (24, 286, 696, 332), "<b>Nada se descarta</b>: el código de hoy es la base de la Sesión 3.",
          kind="note", pad=5)


# ===========================================================================

# Si existe plantilla-lidr-s02.pdf (las diapos oficiales), sus páginas entran sin tocar. Cada entrada de
# ORIGINALES es (página del PDF oficial, [diapos nuestras que van detrás]). Se rellena al ver el PDF.
ORIGINALES: list[tuple[int, list]] = []

PROPIAS = [slide_hoy, slide_errores, slide_setup, slide_cag, slide_recorrido, slide_transcripcion, slide_limpieza,
           slide_requisitos, slide_con_sin, slide_formato, slide_cantidad, slide_prompt, slide_sumas, slide_tier,
           slide_parametros, slide_niveles, slide_handson, slide_tests, slide_mapa, slide_s3]


def build() -> None:
    d = Deck()
    if OFICIAL.exists() and ORIGINALES:
        oficial = fitz.open(OFICIAL)
        usadas = set()
        for pno, nuestras in ORIGINALES:
            d.flush()
            d.doc.insert_pdf(oficial, from_page=pno, to_page=pno)
            for s in nuestras:
                s(d)
                usadas.add(s)
        for s in PROPIAS:
            if s not in usadas:
                s(d)
    else:
        cover(d)
        for s in PROPIAS:
            s(d)
    d.template(10)  # ROTI
    d.template(11)  # gracias
    d.save()


if __name__ == "__main__":
    build()
