"""Genera el deck de la Sesión 1 (LLMs y setup de entorno de trabajo) de Julián Fernández.

Reutiliza el motor del deck de la Sesión 7 y su plantilla de LIDR (portada, ROTI y cierre). Cada diapo de
contenido lleva al pie la franja «En el código» con la celda del notebook que se ejecuta: las celdas de
`notebook/sesion-01-en-vivo.ipynb` empiezan con un rótulo («# 2.2 · Iteración 4 …») que es lo que se cita.

Las cifras salen de la ejecución completa del notebook del 16/11/2026 (`sesion-01-en-vivo-ejecutado.ipynb`).

    python build_deck.py
    # → ../Sesion01-Julian-Fernandez.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "s07" / "deck"))
import build_deck as base  # noqa: E402  (motor del deck de la S7)

base.TEMPLATE = HERE.parent.parent / "s07" / "deck" / "plantilla-lidr-s07.pdf"
base.OUTPUT = HERE.parent / "Sesion01-Julian-Fernandez.pdf"
base.SVGS = []
H, W = base.H, base.W
base.Y1_REAL = 340   # deja sitio a la franja «En el código», grande, encima del pie
CODIGO = fitz.Rect(10, 344, W - 10, 386)
NB = "<b>sesion-01-en-vivo.ipynb</b>"


class Deck(base.Deck):
    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 1 · '
               f"LLMs y setup de entorno de trabajo · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=base.CSS)

    def codigo(self, page: fitz.Page, ref: str) -> None:
        """Franja grande al pie: qué celda del notebook se ejecuta en esta diapo."""
        page.draw_rect(CODIGO, color=(0.39, 0.4, 0.95), fill=(0.11, 0.12, 0.18), width=1.2, radius=0.18)
        tag = fitz.Rect(CODIGO.x0, CODIGO.y0, CODIGO.x0 + 112, CODIGO.y1)
        page.draw_rect(tag, color=None, fill=(0.39, 0.4, 0.95), radius=0.18)
        page.insert_htmlbox(tag + (6, 8, -4, -4),
                            '<div style="font-size:11.5pt;color:#ffffff;font-weight:bold;text-align:center">'
                            "&lt;/&gt; En el código</div>", css=base.CSS)
        page.insert_htmlbox(fitz.Rect(tag.x1 + 10, CODIGO.y0 + 5, CODIGO.x1 - 10, CODIGO.y1 - 3),
                            f'<div style="font-size:11pt;color:#f3f4f6;line-height:1.3">{ref}</div>',
                            css=base.CSS + " code { color:#c7d2fe; font-size:0.95em; }", scale_low=0.7)


def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    page.add_redact_annot(fitz.Rect(48, 158, 470, 242), fill=False)
    page.add_redact_annot(fitz.Rect(48, 124, 330, 147), fill=False)   # línea del módulo de la plantilla
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for y, line in ((191, "Sesión 1: LLMs y setup"), (232, "de entorno de trabajo")):
        page.insert_text((51, y), line, fontname="hebo", fontsize=34.5, color=(1, 1, 1))
    page.insert_text((51, 141), "MÓDULO 1: Fundamentos de productos con IA", fontname="hebo", fontsize=13,
                     color=(1, 1, 1))


def table(head: list[str], rows: list[tuple]) -> str:
    return ("<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>"
            + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</table>")


# ===========================================================================
# Apertura
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: la llamada más básica, vista como producto", "Un notebook, siete bloques, 120 minutos",
              "Apertura")
    d.codigo(p, f"{NB} · funciona en <b>Google Colab</b> (claves en 🔑 Secrets) y en local "
                "(<code>curso-master/sesiones/s01/notebook</code>, claves en <code>.env</code>)")
    filas = [("1", "Setup y puesta en común", "10'"), ("2", "Del prompt del usuario al prompt del producto", "25'"),
             ("3", "Parámetros y herramientas integradas", "20'"), ("4", "Comparativa de proveedores en vivo", "20'"),
             ("5", "Agregadores: LiteLLM", "12'"), ("6", "Tokens: cómo funcionan y cuánto cuestan", "20'"),
             ("7", "Arquitecturas reales y cierre", "13'")]
    d.box(p, (24, 66, 452, 330), table(["", "Bloque", ""], filas), kind="beige", role="table")
    d.box(p, (464, 66, 696, 190),
          '<div class="t">La idea que atraviesa todo</div>En un producto el usuario <b>no hace prompting</b>. '
          "La calidad, el coste y la consistencia los diseña quien desarrolla.",
          kind="mint")
    d.box(p, (464, 200, 696, 330),
          '<div class="t">De dónde venimos</div>Ejercicio previo: una pregunta a un LLM por API y su respuesta. '
          "Hoy: qué decide cada línea de esa llamada y cuánto cuesta.",
          kind="lav")


def slide_setup(d: Deck) -> None:
    p = d.new("Bloque 1 · Tres celdas antes de empezar", "Bloqueante: nadie pasa al Bloque 2 sin las tres en verde",
              "Bloque 1")
    d.codigo(p, f"{NB} · <code># Config 1 · Dependencias</code> · <code># Config 2 · Claves y clientes</code> "
                "(<code>leer_clave()</code>) · <code># Config 3 · Función de costes</code> (<code>PRICES</code>)")
    pasos = [("Config 1", "Cuatro ✅: openai, anthropic, tiktoken, litellm"),
             ("Config 2", "«Clients configured successfully»"),
             ("Config 3", "«Cost calculation function loaded»")]
    y = 66
    for t, desc in pasos:
        d.box(p, (24, y, 340, y + 58), f"<b>{t}</b><br/>{desc}", kind="mint", pad=6)
        y += 66
    d.box(p, (352, 66, 696, 330),
          '<div class="t">Los errores que van a salir</div><ul>'
          "<li><b>No encuentra los Secrets</b>: icono 🔑, crear <code>OPENAI_API_KEY</code> y "
          "<code>ANTHROPIC_API_KEY</code> y activar el acceso del notebook.</li>"
          "<li><b><code>RateLimitError</code> que habla de crédito</b>: la cuenta no tiene saldo.</li>"
          "<li><b>Claves cruzadas</b>: OpenAI empieza por <code>sk-</code>, Anthropic por <code>sk-ant-</code>.</li>"
          "<li><b>Avisos de gradio/typer</b> en Colab: inofensivos.</li></ul>"
          "Un problema largo se resuelve aparte o al final: este bloque no pasa de 10 minutos.",
          kind="peach")


# ===========================================================================
# Bloque 2
# ===========================================================================

def slide_generica(d: Deck) -> None:
    p = d.new("La respuesta genérica", "Misma pregunta de siempre, sin system prompt", "Bloque 2")
    d.codigo(p, f"{NB} · <code># 2.1 · Sin system prompt</code> · "
                "<code>openai_client.responses.create(model=MODEL, input=…)</code>")
    d.code(p, (24, 66, 420, 200), """respuesta = openai_client.responses.create(
    model="gpt-4o-mini",
    input="We're migrating our payment service
           from a monolith to microservices.
           What should we consider?",
)""", "La llamada mínima · Responses API")
    d.box(p, (432, 66, 696, 200),
          '<div class="t">Lo que sale</div><b>521 palabras</b> en <b>15 apartados</b>: desacoplar, datos, seguridad, '
          "CI/CD, documentación… Todo cierto, nada útil.",
          kind="peach")
    d.box(p, (24, 210, 696, 330),
          '<div class="t">Tres preguntas a la clase</div><ul>'
          "<li>¿Pondríais esto en un producto?</li>"
          "<li>¿Se lo daríais a un cliente que paga por vuestro software?</li>"
          "<li>Si la calidad depende de que el usuario escriba un buen prompt, ¿cuántos usuarios tendrán buenas "
          "respuestas?</li></ul>"
          "<b>La calidad homogénea es responsabilidad de quien desarrolla.</b>",
          kind="note")


def slide_iteraciones(d: Deck) -> None:
    p = d.new("El system prompt como contrato de calidad", "La pregunta no cambia; solo cambia el system prompt",
              "Bloque 2")
    d.codigo(p, f"{NB} · <code># 2.2 · Iteración 1</code> … <code>Iteración 4</code> · <code>preguntar()</code> · "
                "<code>SYSTEM_PROMPT_V1…V3</code> · <code>PRODUCTION_SYSTEM_PROMPT</code>")
    filas = [("Sin prompt", "—", "521"),
             ("1 · Rol", "senior architect, distributed systems", "548"),
             ("2 · + audiencia + formato", "15 años en pagos · devs de 5+ años · prosa, 250 palabras", "241"),
             ("3 · + comportamiento", "trade-offs con consecuencia · supuestos · sin vendors · un riesgo no obvio", "227"),
             ("4 · Contrato de producción", "PCI-DSS, 1.000 M$ · estructura fija · prohibido «Great question!»", "194")]
    d.box(p, (24, 66, 696, 222), table(["Iteración", "Qué añade", "Palabras"], filas), kind="beige", role="table")
    d.box(p, (24, 232, 352, 330),
          '<div class="t">Lo que se ve</div>El rol solo sube el tono técnico (¡y alarga!). El cambio de verdad llega con '
          "<b>audiencia y formato</b>. La 4 abre con la decisión crítica y cierra con el riesgo olvidado.",
          kind="mint")
    d.box(p, (368, 232, 696, 330),
          '<div class="t">Tras cada iteración</div>¿Qué ha cambiado? ¿Por qué? Cada línea del system prompt es una '
          "<b>decisión de producto</b>: el equivalente a las reglas de negocio de una web.",
          kind="lav")


def slide_reviewer(d: Deck) -> None:
    p = d.new("Abstraer al usuario del prompting", "Un revisor de pull requests: naive frente a producción", "Bloque 2")
    d.codigo(p, f"{NB} · <code># 2.3 · review_pull_request_naive()</code> · "
                "<code># 2.3 · review_pull_request()</code> · <code>PR_REVIEW_SYSTEM_PROMPT</code> · <code>DIFF</code>")
    d.code(p, (24, 66, 352, 186), """def charge_customer(customer_id, amount):
  customer = db.query(f"... id = {customer_id}")
  total = amount * 1.21
  result = stripe.Charge.create(amount=total, ...)
  db.execute(f"UPDATE orders SET paid = 1 ...")
  return result""", "DIFF · lo único que aporta el usuario")
    d.box(p, (364, 66, 696, 186),
          '<div class="t">Lo que recibe el modelo</div><b>172 palabras</b> de system prompt + datos formateados '
          "(lenguaje, servicio, diff). El usuario no ve nada de eso.",
          kind="lav")
    d.box(p, (24, 196, 352, 330),
          '<div class="t">«You are a code reviewer»</div>818 tokens de salida. Mezcla la inyección SQL con '
          "docstrings y «magic numbers». <b>Sin veredicto</b>: el autor no sabe si puede mergear.",
          kind="peach")
    d.box(p, (364, 196, 696, 330),
          '<div class="t">Prompt de producción</div>Primera línea: <b>BLOCK</b>. Cinco hallazgos por gravedad: '
          "inyección SQL (critical), redondeo, euros frente a céntimos de Stripe… Menos tokens (485 frente a 818) y mucho más útil.",
          kind="mint")


def slide_consistencia(d: Deck) -> None:
    p = d.new("Consistencia: ¿dos usuarios, dos calidades?", "Cuatro llamadas con la misma pregunta", "Bloque 2")
    d.codigo(p, f"{NB} · <code># 2.4 · temperature 1.0 + prompt vago</code> · "
                "<code># 2.4 · temperature 0.1 + prompt preciso</code> (<code>PRECISE_PROMPT</code>)")
    d.box(p, (24, 66, 352, 230),
          '<div class="t">temperature 1.0 + «Help the user.»</div>Cuatro respuestas, cuatro enfoques: «complejidad», '
          "«seguridad», «dependencias», «comunicación entre servicios». Cada usuario se lleva una cosa distinta.",
          kind="peach")
    d.code(p, (368, 66, 696, 230), """Risk: System integration complexity
Why: Microservices can lead to challenges
in ensuring seamless communication and
data consistency across multiple services.

        × 4, idénticas""", "temperature 0.1 + formato exacto")
    d.box(p, (24, 240, 696, 330),
          '<div class="t">Los modelos son estocásticos</div>La consistencia no viene del modelo: viene de tus '
          "<b>instrucciones</b> y tus <b>parámetros</b>. Las palancas: <code>temperature</code>, "
          "<code>max_output_tokens</code> y <i>structured outputs</i> (Sesión 4).",
          kind="mint")


# ===========================================================================
# Bloque 3
# ===========================================================================

def slide_parametros(d: Deck) -> None:
    p = d.new("Parámetros esenciales: temperature, max_output_tokens, stop, seed",
              "Ejecuciones reales con gpt-4o-mini", "Bloque 3")
    d.codigo(p, f"{NB} · <code># 3.1 · Misma pregunta, tres temperaturas</code> · <code># 3.2 · Tres techos de "
                "salida</code> · <code># 3.3 · stop</code> · <code># 3.3 · seed</code> (Chat Completions)")
    d.box(p, (24, 66, 360, 196),
          table(["temperature", "3 nombres para el SaaS"],
                [("0.0", "CostCalc Pro · CostWise · CostWise"), ("0.7", "CostCalc SaaS · CostWise · CostCalc"),
                 ("1.5", "CostCrafters · CostOrchard · CostPioneer")]),
          kind="beige", role="table")
    d.box(p, (372, 66, 696, 196),
          table(["max_output_tokens", "status", "salida"],
                [("50", "incomplete", "50"), ("200", "incomplete", "200"), ("800", "completed", "253")]),
          kind="beige", role="table")
    d.box(p, (24, 206, 248, 330),
          '<div class="t">temperature</div>Ni a 0.0 es idéntica. En producción, <b>0.2-0.3</b>. '
          "<code>top_p</code> es la alternativa: <b>uno u otro, nunca los dos</b> (Claude 4.5+ lo rechaza).",
          kind="mint")
    d.box(p, (260, 206, 484, 330),
          '<div class="t">max_output_tokens</div>Es un <b>techo de seguridad</b>, no un control de longitud: corta a '
          "media frase. Obligatorio en Anthropic, opcional en OpenAI y Gemini.",
          kind="lav")
    d.box(p, (496, 206, 696, 330),
          '<div class="t">stop y seed</div><code>stop=["4."]</code> corta la lista en la fase 3. '
          "<code>seed=42</code>: las tres respuestas <b>no</b> salieron iguales. Reproducibilidad <i>best effort</i>.",
          kind="note")


def slide_resumen_parametros(d: Deck) -> None:
    p = d.new("Puntos de partida por tipo de tarea", "No hay valores correctos universales: se ajustan midiendo",
              "Bloque 3")
    d.codigo(p, f"{NB} · markdown <b>3.4 · Resumen de parámetros</b> · los modelos de razonamiento se controlan con "
                "<code>reasoning={\"effort\": …}</code>")
    filas = [("Extracción de datos", "0 – 0.2", "justo para el JSON", "structured outputs"),
             ("Clasificación", "0", "pequeño", "stop o etiquetas cerradas"),
             ("Asistente técnico / soporte", "0.2 – 0.4", "300 – 800", "formato en el system"),
             ("Redacción, resúmenes", "0.5 – 0.7", "según el texto", ""),
             ("Brainstorming, naming", "0.8 – 1.2", "pequeño", "varias muestras")]
    d.box(p, (24, 66, 696, 230), table(["Tarea", "temperature", "max_output_tokens", "Otros"], filas),
          kind="beige", role="table")
    d.box(p, (24, 240, 352, 330),
          '<div class="t">Pregunta a la clase</div>¿Qué temperature para extraer datos de facturas? '
          "¿Y para una herramienta de brainstorming?",
          kind="lav")
    d.box(p, (368, 240, 696, 330),
          '<div class="t">Modelos de razonamiento</div>No aceptan la mayoría de estos parámetros. Ojo: '
          "<code>gpt-5.4</code> <b>sí</b> acepta <code>temperature</code> si no activas el razonamiento (probado hoy).",
          kind="note")


def slide_tools(d: Deck) -> None:
    p = d.new("Herramientas integradas: de oráculo a agente", "Las ejecuta el proveedor, en una sola llamada",
              "Bloque 3")
    d.codigo(p, f"{NB} · <code># 3.6 · web_search (OpenAI)</code> · <code># 3.6 · Las fuentes, en las annotations"
                "</code> · <code># 3.7 · web_search (Anthropic)</code>")
    filas = [("Búsqueda web", "<code>web_search</code>", "<code>web_search_20250305</code>"),
             ("Documentos (RAG)", "<code>file_search</code>", "—"),
             ("Ejecutar código", "<code>code_interpreter</code>", "<code>code_execution</code>"),
             ("Usar un ordenador", "<code>computer_use_preview</code>", "<code>computer_use</code>"),
             ("MCP remoto", "<code>mcp</code>", "conector MCP")]
    d.box(p, (24, 66, 400, 230), table(["", "OpenAI", "Anthropic"], filas), kind="beige", role="table")
    d.box(p, (412, 66, 696, 230),
          '<div class="t">DevDay 2025 con gpt-4o</div>Pasos: <code>web_search_call</code> → <code>message</code>. '
          "Responde con Apps SDK, AgentKit y GPT-5 Pro, y las fuentes llegan en las "
          "<code>annotations</code> de la respuesta.",
          kind="mint")
    d.box(p, (24, 240, 352, 330),
          '<div class="t">Ojo a la factura</div>Esa llamada: <b>17.509 tokens de entrada</b> (lo que lee de la web '
          "se cobra como entrada) y <b>0,048 $</b>: unas 360 veces una llamada normal.",
          kind="peach")
    d.box(p, (368, 240, 696, 330),
          '<div class="t">Anthropic: control y gobernanza</div>Herramienta <b>versionada</b> con fecha, hay que '
          "<b>habilitarla</b> en la Console y se limita con <code>max_uses</code>. Mostrar las fuentes no es opcional.",
          kind="lav")


def slide_otras_tools(d: Deck) -> None:
    p = d.new("Lo que los proveedores venden y nosotros construiremos", "Criterio para decidir: comprar o hacer",
              "Bloque 3")
    d.codigo(p, f"{NB} · markdown <b>3.8 · Otras herramientas</b> (sin ejecutar)")
    cards = [("file_search → Módulo 3", "RAG gestionado: subes documentos y OpenAI los trocea y vectoriza. "
              "Lo construiremos por dentro (sesiones 6-11).", "mint"),
             ("code_interpreter / code_execution", "Python en un sandbox. El modelo deja de sumar «de cabeza»: "
              "cálculos exactos, CSVs.", "lav"),
             ("computer_use", "El modelo maneja un ordenador con capturas, ratón y teclado. La frontera de los "
              "agentes.", "beige"),
             ("MCP remoto → Módulo 5", "Herramientas propias expuestas al modelo con un protocolo común. "
              "Lo usaremos con agentes (sesiones 12-14).", "note")]
    for i, (t, body, k) in enumerate(cards):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 66 + row * 136
        d.box(p, (x, y, x + 332, y + 128), f'<div class="t">{t}</div>{body}', kind=k, pad=8)


# ===========================================================================
# Bloque 4
# ===========================================================================

def slide_proveedores(d: Deck) -> None:
    p = d.new("Misma pregunta, distinto proveedor y distinto tier",
              "PostgreSQL con 50M filas: ¿columnar o réplicas + índices?", "Bloque 4")
    d.codigo(p, f"{NB} · <code># 4.1 · OpenAI</code> · <code># 4.1 · Anthropic</code> · <code># 4.1 · Lado a lado"
                "</code> · <code># 4.2 · Tiers de OpenAI</code> · <code>COMPARISON_SYSTEM_PROMPT</code>")
    filas = [("gpt-4o-mini", "3,2 s", "158 → 181", "0,00013 $", "Postgres; cifras vagas"),
             ("gpt-5.4-mini", "3,8 s", "157 → 305", "0,00149 $", "tabla resumen: 8-12 s → 50-300 ms"),
             ("gpt-5.4", "10,0 s", "157 → 311", "0,00506 $", "particiones, réplicas, umbral 200-500M filas"),
             ("claude-haiku-4-5", "—", "—", "—", "en directo, con la clave de Anthropic")]
    d.box(p, (24, 66, 696, 210), table(["Modelo", "Tiempo", "Tokens", "Coste", "Lo que aporta"], filas),
          kind="beige", role="table")
    d.box(p, (24, 220, 352, 330),
          '<div class="t">Preguntas a la clase</div><ul><li>¿Cuál respeta mejor el formato?</li>'
          "<li>¿Alguna dice «it depends» sin cuantificar?</li>"
          "<li>¿Justifica 38× más coste la diferencia, <b>para esta pregunta</b>?</li></ul>",
          kind="lav")
    d.box(p, (368, 220, 696, 330),
          '<div class="t">Los tokens no se comparan entre proveedores</div>Cada uno tiene su tokenizador: el mismo '
          "texto da más tokens de entrada en Anthropic que en OpenAI. Compara <b>coste</b>, no tokens.",
          kind="note")


def slide_criterios(d: Deck) -> None:
    p = d.new("No existe «el mejor modelo»", "Existe el mejor para tu caso de uso, tu presupuesto y tu volumen",
              "Bloque 4")
    d.codigo(p, f"{NB} · <code># 4.2 · ¿Cuánto más caro es cada tier?</code> · <code>PRICES</code> "
                "(precios oficiales del 16/11/2026) · <code>calcular_coste()</code>")
    filas = [("gpt-4o-mini", "0,15", "0,60", "1×"), ("gpt-5.4-nano", "0,20", "1,25", "1,9×"),
             ("gpt-5.4-mini", "0,75", "4,50", "7×"), ("claude-haiku-4-5", "1,00", "5,00", "8×"),
             ("gpt-5.4", "2,50", "15,00", "23×"), ("claude-sonnet-4-6", "3,00", "15,00", "24×")]
    d.box(p, (24, 66, 352, 330), table(["Modelo", "$ / M entrada", "$ / M salida", "vs 4o-mini"], filas),
          kind="beige", role="table")
    d.box(p, (364, 66, 696, 196),
          '<div class="t">Tres escenarios para la clase</div><ul><li>Chatbot de FAQs sencillas.</li>'
          "<li>Contratos legales de 50 páginas.</li><li>10.000 usuarios: ¿un modelo para todos?</li></ul>",
          kind="lav")
    d.box(p, (364, 206, 696, 330),
          '<div class="t">Routing / cascada</div>Un modelo barato para el 80 % de las peticiones y uno premium solo '
          "cuando la tarea lo pide. Lo construimos en la <b>Sesión 3</b>.",
          kind="mint")


# ===========================================================================
# Bloque 5
# ===========================================================================

def slide_litellm(d: Deck) -> None:
    p = d.new("Agregadores: una interfaz, varios proveedores", "LiteLLM: cambiar de proveedor es cambiar un string",
              "Bloque 5")
    d.codigo(p, f"{NB} · <code># 5.2 · El mismo código para los dos proveedores</code> · "
                "<code># 5.3 · evaluate_technical_decision()</code>")
    d.code(p, (24, 66, 400, 210), """for modelo in ["openai/gpt-4o-mini",
               "anthropic/claude-haiku-4-5-20251001"]:
    resp = litellm.completion(
        model=modelo,          # ← lo único que cambia
        messages=[{"role": "system", "content": ...},
                  {"role": "user", "content": ...}],
    )
    resp.choices[0].message.content
    resp.usage.prompt_tokens""", "Webhooks de Stripe: ¿síncrono o cola?")
    d.box(p, (412, 66, 696, 210),
          table(["", "Directa", "LiteLLM"],
                [("Entrada", "<code>instructions</code> + <code>input</code>", "<code>messages</code>"),
                 ("Texto", "<code>output_text</code>", "<code>choices[0]…</code>"),
                 ("Tokens", "<code>input_tokens</code>", "<code>prompt_tokens</code>")]),
          kind="beige", role="table")
    d.box(p, (24, 220, 352, 330),
          '<div class="t">Por qué un agregador</div>Caídas, cambios de precio y rate limits de un solo proveedor. '
          "Cada SDK es distinto. LiteLLM es open source: sin coste extra ni lock-in.",
          kind="lav")
    d.box(p, (368, 220, 696, 330),
          '<div class="t">El idioma común es Chat Completions</div>Por eso hay que conocer las dos APIs de OpenAI. '
          "En la <b>Sesión 3</b> esto se convierte en la capa de proveedores con <b>fallback automático</b>.",
          kind="mint")


# ===========================================================================
# Bloque 6
# ===========================================================================

def slide_tokens(d: Deck) -> None:
    p = d.new("Los tokens no son palabras", "Tokenizador o200k_base (gpt-4o y familia gpt-5) frente a cl100k (2023)",
              "Bloque 6")
    d.codigo(p, f"{NB} · <code># 6.1 · Mismo contenido, distintos formatos</code> (<code>tiktoken</code>) · "
                "<code># 6.1 · Token a token</code> · <code># 6.1 · Tu turno</code>")
    d.box(p, (24, 66, 400, 236),
          table(["Texto", "Caracteres", "o200k", "cl100k"],
                [("Inglés", "145", "30", "30"), ("Español", "152", "<b>31</b>", "<b>40</b>"),
                 ("Código Python", "81", "20", "20"), ("JSON", "79", "30", "30"),
                 ("PRODUCTION_SYSTEM_PROMPT", "860", "185", "186")]),
          kind="beige", role="table")
    d.code(p, (412, 66, 696, 166), """¿Cu | ánto | ·cuesta | ·migr | ar |
·una | ·base | ·de | ·datos |
·Postgre | SQL | ·a | ·Amazon |
·Aurora | ?""", "15 tokens (· = espacio) · los acentos y las palabras raras se parten")
    d.box(p, (412, 176, 696, 330),
          '<div class="t">El español ya no penaliza</div>La guía dice «~30 % más tokens». Con el tokenizador de '
          "2023 (cl100k) el español gasta <b>+33 %</b>; con el actual (o200k), <b>+3 %</b>. Depende del tokenizador: "
          "se mide con el de tu modelo.",
          kind="note")
    d.box(p, (24, 246, 400, 330),
          '<div class="t">Lo que cuesta de verdad</div>El JSON sale caro (llaves, comillas, nombres de campo). '
          "El <code>PRODUCTION_SYSTEM_PROMPT</code> son 185 tokens que se pagan <b>en cada llamada</b>.",
          kind="mint")


def slide_asimetria(d: Deck) -> None:
    p = d.new("Entrada frente a salida: la asimetría de la factura", "Misma pregunta, tres longitudes de respuesta",
              "Bloque 6")
    d.codigo(p, f"{NB} · <code># 6.2 · Misma pregunta, tres longitudes de respuesta</code> · "
                "<code># 6.2 · Proyección a escala</code> (<code>LLAMADAS_MES = 10_000 * 5 * 30</code>)")
    d.box(p, (24, 66, 352, 196),
          table(["Respuesta", "Entrada", "Salida", "% coste en salida"],
                [("~50 palabras", "213", "160", "75 %"), ("~200 palabras", "213", "239", "82 %"),
                 ("~500 palabras", "213", "566", "91 %")]),
          kind="beige", role="table")
    d.box(p, (364, 66, 696, 196),
          table(["1,5 M llamadas/mes", "$/mes", ""],
                [("gpt-4o-mini", "263", "1×"), ("gpt-5.4-nano", "512", "1,9×"), ("gpt-5.4-mini", "1.853", "7×"),
                 ("claude-haiku-4-5", "2.112", "8×"), ("gpt-5.4", "6.176", "23,5×"),
                 ("claude-sonnet-4-6", "6.336", "24×")]),
          kind="beige", role="table")
    d.box(p, (24, 206, 696, 330),
          '<div class="t">La salida cuesta entre 4 y 6 veces más que la entrada</div>'
          "Por eso acortar las respuestas mueve más la factura que recortar el prompt. Y el modelo elegido multiplica "
          "todo: de <b>263 $</b> a <b>6.176 $</b> al mes con el mismo producto. La guía de LIDR decía «15-20×»; con los "
          "precios de hoy son <b>23,5×</b>.",
          kind="mint")


def slide_multiturno(d: Deck) -> None:
    p = d.new("El coste oculto de las conversaciones", "Incidente de latencia en 5 turnos: cada llamada reenvía todo",
              "Bloque 6")
    d.codigo(p, f"{NB} · <code># 6.3 · Incident response en 5 turnos</code> (<code>historial</code> como "
                "<code>input</code>) · <code># 6.3 · El system prompt se paga en cada turno</code>")
    d.box(p, (24, 66, 400, 230),
          table(["Turno", "Entrada", "Salida", "Coste $", "Acumulado $"],
                [("1", "58", "130", "0,000087", "0,000087"), ("2", "211", "164", "0,000130", "0,000217"),
                 ("3", "402", "155", "0,000153", "0,000370"), ("4", "588", "142", "0,000173", "0,000543"),
                 ("5", "<b>754</b>", "192", "0,000228", "<b>0,000772</b>")]),
          kind="beige", role="table")
    d.box(p, (412, 66, 696, 230),
          '<div class="t">Lo que dicen los números</div>El turno 5 envía <b>13×</b> más entrada que el 1. '
          "La guía dice que el turno 5 cuesta más que los cuatro anteriores juntos: en nuestra ejecución, "
          "<b>no</b> (0,00023 frente a 0,00054). Crece rápido, pero no tanto.",
          kind="note")
    d.box(p, (24, 240, 696, 330),
          '<div class="t">Cómo se mitiga (sesiones 2-5)</div>Truncar el historial · resumir los turnos antiguos · '
          "<b>prompt caching</b> (Anthropic cobra los aciertos al 10 %) · <code>previous_response_id</code> de la "
          "Responses API. Con 20 turnos, solo el system prompt son <b>3.700 tokens</b>. Gestionar el contexto es "
          "viabilidad económica.",
          kind="mint")


# ===========================================================================
# Bloque 7
# ===========================================================================

def slide_productos(d: Deck) -> None:
    p = d.new("Arquitecturas reales", "Las cuatro preguntas para cualquier producto con IA", "Bloque 7")
    d.codigo(p, f"{NB} · markdown <b>Bloque 7</b> · <code># Extra · Misma pregunta en las tres interfaces</code> "
                "(Responses · Messages · LiteLLM)")
    filas = [("GitHub Copilot", "prompt con el fichero, imports y comentarios", "pequeño inline, grande en el chat",
              "fichero actual y vecinos"),
             ("Soporte tipo Intercom", "políticas + datos del cliente + tickets", "gama media (tono, idioma)",
              "prompt largo: caching"),
             ("Documentos tipo NotebookLM", "subes un documento y preguntas", "ventana grande",
              "50 páginas = 50.000 tokens → <b>RAG</b>")]
    d.box(p, (24, 66, 696, 230), table(["Producto", "Abstracción", "Modelo", "Tokens"], filas),
          kind="beige", role="table")
    d.box(p, (24, 240, 696, 330),
          '<div class="t">Los mismos principios de hoy</div>El usuario nunca hace prompting, el system prompt define '
          "el comportamiento, el modelo es un equilibrio entre calidad y coste, y los tokens deciden si el producto es "
          "viable.",
          kind="mint")


def slide_cierre(d: Deck) -> None:
    p = d.new("Lo que os lleváis hoy", "Y cómo encaja en el máster", "Cierre")
    d.box(p, (24, 66, 352, 250),
          '<div class="t">Tres frases</div><ol>'
          "<li>La calidad de un producto con IA la diseña quien desarrolla. El system prompt es la herramienta.</li>"
          "<li>No existe el mejor modelo: existe el mejor para tu caso, presupuesto y volumen.</li>"
          "<li>Los tokens son la moneda. Controlarlos es controlar el margen.</li></ol>",
          kind="mint")
    d.box(p, (368, 66, 696, 250),
          table(["Sesiones", "Qué construimos"],
                [("2", "Nace el proyecto: estimador con FastAPI y CAG"),
                 ("3-5", "Wrapper con fallback, caché, streaming, guardrails, memoria"),
                 ("6-11", "RAG: datos, embeddings, pgvector, retrieval"),
                 ("12-14", "Agentes: el modelo decide qué herramienta usar"),
                 ("15-16", "Producción: despliegue, evals, observabilidad")]),
          kind="beige", role="table")
    d.box(p, (24, 260, 696, 330),
          '<div class="t">Para la próxima sesión</div>Material asíncrono de la Sesión 2 en la plataforma. El notebook '
          "de hoy se queda en vuestro Drive como referencia: las celdas de coste y tokens os van a servir todo el curso.",
          kind="lav")


# ===========================================================================

def build() -> None:
    d = Deck()
    cover(d)
    for slide in (slide_hoy, slide_setup, slide_generica, slide_iteraciones, slide_reviewer, slide_consistencia,
                  slide_parametros, slide_resumen_parametros, slide_tools, slide_otras_tools, slide_proveedores,
                  slide_criterios, slide_litellm, slide_tokens, slide_asimetria, slide_multiturno, slide_productos,
                  slide_cierre):
        slide(d)
    d.template(10)  # ROTI
    d.template(11)  # gracias
    d.save()


if __name__ == "__main__":
    build()
