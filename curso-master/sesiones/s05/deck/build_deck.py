"""Genera el deck de la Sesión 5 (Funcionalidades avanzadas) de Julián Fernández.

Reutiliza el motor del deck de la Sesión 7 (cajas con autoajuste, pie, imágenes) y su plantilla de LIDR para
la portada (con el título cambiado), el ROTI y el cierre. Cada diapo de contenido lleva al pie una franja
grande «▶ En el código» con el fichero y la línea que hay que abrir.

    python build_deck.py
    # → ../Sesion05-Julian-Fernandez.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "s07" / "deck"))
import build_deck as base  # noqa: E402  (motor del deck de la S7)

base.TEMPLATE = HERE.parent.parent / "s07" / "deck" / "plantilla-lidr-s07.pdf"
base.OUTPUT = HERE.parent / "Sesion05-Julian-Fernandez.pdf"
base.SVGS = []
H, W = base.H, base.W
base.Y1_REAL = 340   # deja sitio a la franja «En el código», grande, encima del pie
CODIGO = fitz.Rect(10, 344, W - 10, 386)


class Deck(base.Deck):
    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 5 · '
               f"Funcionalidades avanzadas · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=base.CSS)

    def codigo(self, page: fitz.Page, ref: str) -> None:
        """Franja grande al pie: dónde se ve en el código lo que cuenta la diapo."""
        page.draw_rect(CODIGO, color=(0.39, 0.4, 0.95), fill=(0.11, 0.12, 0.18), width=1.2, radius=0.18)
        tag = fitz.Rect(CODIGO.x0, CODIGO.y0, CODIGO.x0 + 112, CODIGO.y1)
        page.draw_rect(tag, color=None, fill=(0.39, 0.4, 0.95), radius=0.18)
        page.insert_htmlbox(tag + (6, 8, -4, -4),
                            '<div style="font-size:11.5pt;color:#ffffff;font-weight:bold;text-align:center">'
                            "&lt;/&gt; En el código</div>", css=base.CSS)
        page.insert_htmlbox(fitz.Rect(tag.x1 + 10, CODIGO.y0 + 5, CODIGO.x1 - 10, CODIGO.y1 - 3),
                            f'<div style="font-size:11pt;color:#f3f4f6;line-height:1.3">{ref}</div>',
                            css=base.CSS + " code { color:#c7d2fe; font-size:0.95em; }", scale_low=0.7)

    def arrow(self, page: fitz.Page, x0: float, y0: float, x1: float, y1: float, label: str = "") -> None:
        a = base._stretch((x0, y0, x0, y0)).tl
        b = base._stretch((x1, y1, x1, y1)).tl
        page.draw_line(a, b, color=(0.35, 0.33, 0.6), width=1.4)
        v = b - a
        n = (v.x ** 2 + v.y ** 2) ** 0.5 or 1
        ux, uy = v.x / n, v.y / n
        p1 = fitz.Point(b.x - 7 * ux + 3.5 * uy, b.y - 7 * uy - 3.5 * ux)
        p2 = fitz.Point(b.x - 7 * ux - 3.5 * uy, b.y - 7 * uy + 3.5 * ux)
        page.draw_polyline([p1, b, p2], color=(0.35, 0.33, 0.6), fill=(0.35, 0.33, 0.6), width=1, closePath=True)
        if label:
            mid = fitz.Point((a.x + b.x) / 2, (a.y + b.y) / 2)
            page.insert_htmlbox(fitz.Rect(mid.x - 60, mid.y - 13, mid.x + 60, mid.y - 1),
                                f'<div style="font-size:7.5pt;color:#33298a;text-align:center"><b>{label}</b></div>',
                                css=base.CSS)


def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    page.add_redact_annot(fitz.Rect(48, 158, 470, 242), fill=False)
    page.add_redact_annot(fitz.Rect(48, 124, 330, 147), fill=False)   # línea del módulo de la plantilla
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for y, line in ((191, "Sesión 5: Funcionalidades"), (232, "avanzadas")):
        page.insert_text((51, y), line, fontname="hebo", fontsize=34.5, color=(1, 1, 1))
    page.insert_text((51, 141), "MÓDULO 2: Arquitecturas CAG", fontname="hebo", fontsize=15, color=(1, 1, 1))


# ===========================================================================
# Apertura y ejercicio
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: de un chat que estima a un sistema que se audita",
              "Todo el código ya está escrito: hoy se abre, se explica y se ejecuta", "Apertura")
    d.box(p, (24, 68, 352, 112), '<div class="t center">Hora 1 · la base conversacional</div>', kind="mint", pad=5)
    d.box(p, (368, 68, 696, 112), '<div class="t center">Hora 2 · Actor-Critic-Boss</div>', kind="lav", pad=5)
    hora1 = [("Ejercicio · 15 min", "Memoria, metadata, endpoints y adjuntos"),
             ("Bloque 1 · compresión", "Resumen + anclas + ventana"),
             ("Bloque 2 · tier dinámico", "La audiencia se deduce del contexto"),
             ("Bloque 3 · golden dataset", "Evaluar como una suite de tests")]
    y = 120
    for t, desc in hora1:
        d.box(p, (24, y, 352, y + 48), f"<b>{t}</b><br/>{desc}", kind="beige", pad=5)
        y += 54
    hora2 = [("Bloque 4 · el patrón", "Tres roles y los dos fallos que evita"),
             ("Bloques 5-6 · Actor y Critic", "Mismo actor, crítica estructurada"),
             ("Bloque 7 · Boss", "Aceptar, iterar o sintetizar"),
             ("Bloque 8 · trade-offs", "Cuándo compensa y cuándo sobra")]
    y = 120
    for t, desc in hora2:
        d.box(p, (368, y, 696, y + 48), f"<b>{t}</b><br/>{desc}", kind="beige", pad=5)
        y += 54


def slide_ejercicio(d: Deck) -> None:
    p = d.new("Lo que traéis del ejercicio previo", "Cuatro piezas sobre las que se monta toda la sesión", "Bloque 0")
    d.codigo(p, "app/sessions/<b>models.py</b> (l. 33-105) · sessions/<b>metadata_extractor.py</b> (l. 32) · "
                "routers/<b>sessions.py</b> (l. 75-210) · attachments/<b>extractor.py</b> (l. 38-129)")
    cards = [
        ("A · Memoria conversacional", "<code>ConversationHistory</code>: ventana de <b>6 pares</b> user/assistant. "
         "El system prompt <b>no</b> se guarda: se regenera cada turno.", "mint"),
        ("B · Extractor de metadata", "Un LLM barato saca <code>ProjectMetadata</code> en cada turno. Fusión: lo escalar "
         "se pisa, las listas se suman. Si falla, se queda la anterior.", "lav"),
        ("C · Endpoints /sessions", "<code>POST /sessions</code> · <code>GET /sessions/{id}</code> · "
         "<code>POST …/estimate</code> en <b>multipart</b> (texto + ficheros).", "beige"),
        ("D · Adjuntos PDF/DOCX", "Extracción local con <code>pypdf</code> y <code>python-docx</code>, truncado y "
         "envuelto entre marcas <code>--- attachment ---</code>.", "note"),
    ]
    for i, (t, body, k) in enumerate(cards):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 68 + row * 136
        d.box(p, (x, y, x + 332, y + 128), f'<div class="t">{t}</div>{body}', kind=k, pad=8)


def slide_orden(d: Deck) -> None:
    p = d.new("El orden de los mensajes no es negociable", "Y los cinco errores que más salieron en las correcciones",
              "Bloque 0")
    d.codigo(p, "app/services/<b>estimation.py</b> · <code>estimate_conversational()</code> (l. 177) · "
                "mensajes en l. 227-229 · tests: <code>tests/test_sessions_window.py</code>")
    d.code(p, (24, 68, 380, 190), """messages = [{"role": "system",
             "content": system_prompt}]
messages.extend(session.history.to_messages())
messages.append({"role": "user",
                 "content": user_message})""", "services/estimation.py · cada turno")
    d.box(p, (24, 200, 380, 330),
          '<div class="t">Por qué el system va fuera del historial</div>Se re-renderiza cada turno con la metadata '
          "<b>actual</b>. Guardarlo congelado sería un bug: el modelo seguiría con el tier y el contexto del turno 1.",
          kind="mint")
    d.box(p, (392, 68, 696, 330),
          '<div class="t">Errores frecuentes</div><ul>'
          "<li>Olvidar <code>python-multipart</code>: el endpoint revienta al arrancar.</li>"
          "<li>Llamar sin crear sesión antes: <code>404</code> que parece un bug del servidor.</li>"
          "<li>Omitir el <code>system</code>: se pierden tier, metadata y reglas.</li>"
          "<li>Adjuntos de 80k caracteres sin truncar: revientan la ventana.</li>"
          "<li>Extraer metadata antes de comprimir.</li></ul>",
          kind="peach")


def slide_adjuntos(d: Deck) -> None:
    p = d.new("Adjuntos: multimodal directo o extracción local", "El proyecto se queda con el camino B", "Bloque 0")
    d.codigo(p, "app/attachments/<b>extractor.py</b> · <code>_extract_pdf()</code> (l. 45), <code>_extract_docx()</code> "
                "(l. 61), <code>extract_text()</code> (l. 69), <code>enrich_transcript()</code> (l. 113)")
    d.box(p, (24, 68, 352, 210),
          '<div class="t">A · PDF directo al modelo</div>Cómodo, pero <b>acopla al proveedor</b>: el multimodal de '
          "OpenAI y el de Anthropic no son iguales. Cambias de proveedor y reescribes la integración.",
          kind="peach")
    d.box(p, (368, 68, 696, 210),
          '<div class="t">B · Extraer el texto en local</div>El wrapper del LLM sigue <b>agnóstico</b>: solo recibe '
          "texto. El extractor es un servicio aparte que mañana puede ser OCR o RAG sin tocar la estimación.",
          kind="mint")
    d.code(p, (24, 220, 696, 330), """--- attachment: brief-cliente.pdf ---
... texto extraído (truncado a MAX_ATTACHMENT_CHARS) ...
--- end attachment ---""", "Las marcas dicen al modelo qué dijo el cliente y qué leyó del PDF · una página rota no tumba el PDF")


# ===========================================================================
# Bloque 1 · Compresión
# ===========================================================================

def slide_estrategias(d: Deck) -> None:
    p = d.new("Estrategias de historial", "Qué hacer cuando la conversación no cabe", "Bloque 1")
    d.codigo(p, "app/sessions/<b>models.py</b> · <code>ConversationHistory</code> (l. 43): <code>messages</code>, "
                "<code>anchors</code>, <code>summary</code> · app/config.py · <code>MAX_CONVERSATION_TURNS = 6</code> (l. 49)")
    rows = [("Ventana deslizante", "los últimos N turnos", "olvida lo que se pactó al principio", "el ejercicio"),
            ("Resumen acumulado", "lo antiguo, condensado", "pierde la letra exacta de lo crítico", "LLM barato"),
            ("Anclas", "turnos críticos, literales", "si se ancla de más, el prompt crece", "8 reglas, sin LLM"),
            ("<b>Híbrida</b>", "<b>resumen + anclas + ventana</b>", "una llamada extra al comprimir", "<b>hoy</b>")]
    d.box(p, (24, 66, 696, 230),
          "<table><tr><th>Estrategia</th><th>Qué conserva</th><th>Qué arriesga</th><th>Coste</th></tr>"
          + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{e}</td></tr>" for a, b, c, e in rows)
          + "</table>", kind="beige", role="table")
    d.box(p, (24, 240, 352, 330),
          '<div class="t">El fallo de la ventana</div>En el turno 7 desaparece el turno 1: «firmamos NDA», '
          "«presupuesto tope 50k». El modelo deja de tratarlo como confidencial.",
          kind="peach")
    d.box(p, (368, 240, 696, 330),
          '<div class="t">La idea de hoy</div>Lo crítico se queda <b>literal</b> (ancla), lo demás se '
          "<b>resume</b>, y lo reciente sigue <b>vivo</b> en la ventana.",
          kind="mint")


def slide_compresion(d: Deck) -> None:
    p = d.new("Compresión híbrida: cómo se compone el prompt", "Turno 8 con max_turns = 6 y un NDA en el turno 1",
              "Bloque 1")
    d.codigo(p, "sessions/<b>models.py</b> · <code>to_messages()</code> (l. 79) · <code>append()</code> (l. 65) · "
                "compression/<b>policy.py</b> · <code>apply()</code> (l. 50), <code>apply_compression()</code> (l. 96)")
    d.code(p, (24, 68, 420, 230), """to_messages() → [
  {user: "[Earlier conversation summary]
          El cliente describió un CRM…"},   ← resumen
  NDA · turno 1 (user + assistant),         ← ancla
  turnos 3 … 8                              ← ventana
]""", "La ventana solo limita el tramo vivo")
    d.box(p, (432, 68, 696, 230),
          '<div class="t">El resumen entra como <code>user</code></div>Ya hay un <code>system</code> y se regenera cada '
          "turno: un segundo <code>system</code> rompería el contrato. El corchete le dice al modelo que es contexto.",
          kind="lav")
    d.box(p, (24, 240, 696, 330),
          '<div class="t">El cambio de contrato: <code>append()</code> ya no recorta</div>'
          "Antes, <code>append</code> recortaba en silencio. Ahora solo añade, y el servicio llama justo después a "
          "<code>apply_compression(...)</code>: quien lee el código ve <b>cuándo</b> se paga la llamada al LLM. "
          "Un solo resumen por pasada, rehecho entero a partir del anterior (nada de resumen de resúmenes).",
          kind="note")


def slide_anclas(d: Deck) -> None:
    p = d.new("Anclas: ocho reglas, cero LLM", "Mejor quedarse corto que anclar de más", "Bloque 1")
    d.codigo(p, "app/sessions/compression/<b>anchors.py</b> · <code>_HEURISTIC_PATTERNS</code> (l. 41), "
                "<code>detect()</code> (l. 94), modo LLM opcional <code>_detect_llm()</code> (l. 116)")
    d.code(p, (24, 68, 452, 330), """nda                  nda | non-disclosure | under embargo
signed_contract      signed the contract | sow | msa
scope_frozen         scope is frozen | locked | final
budget_locked        budget is capped at …
compliance           hipaa | gdpr | sox | pci-dss | iso-27001
deadline_hard        hard deadline | must go live by
contractual          contractually bound | required
explicit_commitment  we agreed to | the client committed to""", "_HEURISTIC_PATTERNS (resumido)")
    d.box(p, (464, 68, 696, 192),
          '<div class="t">Por qué tan pocas</div>Un falso negativo acaba en el resumen. Un falso positivo se queda '
          "<b>literal en el prompt para siempre</b>: eso es lo caro.",
          kind="peach")
    d.box(p, (464, 202, 696, 330),
          '<div class="t">Solo se mira al usuario</div>El assistant entra «por arrastre» si su turno es ancla. '
          "Cada promoción deja en el log la regla que la disparó (<code>anchor_detected</code>). "
          "<code>ANCHOR_DETECTION_MODE=llm</code> para paráfrasis densas.",
          kind="mint")


def slide_demo_compresion(d: Deck) -> None:
    p = d.new("Demo: ocho turnos en la misma sesión", "Turno 1 en inglés con «we signed the NDA»; turnos 2-8, refinamientos",
              "Bloque 1")
    d.codigo(p, "<b>Interfaz:</b> panel lateral (Window, Anchors kept, Summary) · <code>GET /sessions/{id}</code> · "
                "routers/<b>sessions.py</b> · <code>SessionInfoResponse</code> (l. 63)")
    rows = [("1-6", "2 → 12", "0", "0", "la ventana se llena"),
            ("7", "12", "<b>2</b>", "0", "sale el turno 1: es ancla (<code>nda</code>)"),
            ("8", "12", "2", "<b>908</b>", "sale el turno 2: va al resumen")]
    d.box(p, (24, 66, 452, 210),
          "<table><tr><th>Turno</th><th>Mensajes</th><th>Anclas</th><th>Resumen</th><th></th></tr>"
          + "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{e}</td><td>{f}</td></tr>"
                    for a, b, c, e, f in rows)
          + "</table>", kind="beige", role="table")
    d.box(p, (464, 66, 696, 210),
          '<div class="t">Ejecución real</div>gpt-4o, <code>max_turns=6</code>: la ventana nunca pasa de 12 mensajes, '
          "el NDA sobrevive literal y el resto queda en 908 caracteres de resumen.",
          kind="mint")
    d.box(p, (24, 220, 696, 330),
          '<div class="t">Lo que no hace el ancla</div>En el turno 1 el tier es <b>executive</b> (<code>nda_detected</code>); '
          "del 2 en adelante vuelve a <b>default</b>. El resolver de tier mira el texto del turno y la metadata, "
          "<b>no las anclas</b>. Buena pregunta para la clase: ¿debería?",
          kind="note")


# ===========================================================================
# Bloque 2 · Tier dinámico
# ===========================================================================

def slide_tiers(d: Deck) -> None:
    p = d.new("Tiers: la misma estimación para audiencias distintas", "Un solo prompt, un bloque &lt;audience&gt; que cambia",
              "Bloque 2")
    d.codigo(p, "app/prompts/estimation/v3/<b>system.j2</b> · bloque <code>&lt;audience&gt;</code> (l. 23-45) · "
                "app/sessions/<b>tier_resolver.py</b> · <code>class Tier</code> (l. 36)")
    rows = [("executive", "sponsor, dirección", "cifra defendible, riesgos primero, 3-4 fases, sin jerga"),
            ("pm", "jefe de proyecto", "hitos, quién y qué entrega, máx. 4 fases, confianza prudente"),
            ("developer", "tech lead", "stack, integraciones, riesgo técnico por fase, hasta 6-8 fases"),
            ("default", "audiencia mixta", "equilibrio negocio / técnica, sin ajustes")]
    d.box(p, (24, 66, 696, 210),
          "<table><tr><th>Tier</th><th>Para quién</th><th>Cómo cambia la respuesta</th></tr>"
          + "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
          + "</table>", kind="beige", role="table")
    d.box(p, (24, 220, 352, 330),
          '<div class="t">Estático (el artículo)</div>El cliente pasa <code>tier=executive</code>. Funciona si acierta, '
          "pero en una conversación larga la audiencia cambia: empieza el comercial y termina el CTO.",
          kind="peach")
    d.box(p, (368, 220, 696, 330),
          '<div class="t">Dinámico (hoy)</div>Se deduce de pistas: NDA, normativa, densidad técnica, tamaño del '
          "equipo. <b>Jinja en vez de cuatro prompts</b>: un arreglo común se hace una vez.",
          kind="mint")


def slide_resolver(d: Deck) -> None:
    p = d.new("El resolver: reglas en orden, la primera que acierta gana", "Y un override humano que siempre manda",
              "Bloque 2")
    d.codigo(p, "app/sessions/<b>tier_resolver.py</b> · regex (l. 59-69) · <code>_RULES</code> (l. 107) · "
                "<code>resolve_tier()</code> (l. 115) · llamada en services/estimation.py (l. 205)")
    d.code(p, (24, 68, 400, 186), """_RULES = (
  TierRule("nda_detected",       EXECUTIVE),
  TierRule("regulatory_context", EXECUTIVE),
  TierRule("technical_audience", DEVELOPER),
  TierRule("low_budget_pm",      PM),
)  # si ninguna → DEFAULT""", "tier_resolver.py · el orden importa")
    d.code(p, (24, 196, 400, 330), """e-commerce · Stripe · 4 personas
  → tier: default    rule: default

"Heads-up, firmamos NDA…" + lo mismo
  → tier: executive  rule: nda_detected

microservicios + Kubernetes + Kafka
  → tier: developer  (≥ 2 palabras técnicas)""", "Demo · ejecución real")
    d.box(p, (412, 68, 696, 186),
          '<div class="t">Devuelve (tier, regla)</div>La regla viaja al panel: «executive (nda_detected)». Si el tier no '
          "es el esperado, el porqué está al lado.",
          kind="mint")
    d.box(p, (412, 196, 696, 330),
          '<div class="t">Lo que vimos al probarlo</div>«Equipo de 2 personas» no dispara <code>pm</code> en el '
          "<b>primer</b> turno: el tamaño del equipo llega a la metadata <b>después</b> de resolver el tier. "
          "Desde el segundo turno, sí.",
          kind="note")


# ===========================================================================
# Bloque 3 · Golden dataset
# ===========================================================================

def slide_golden(d: Deck) -> None:
    p = d.new("Golden dataset: evaluar como una suite de tests", "16 casos comiteados en el repo, con rangos y no igualdades",
              "Bloque 3")
    d.codigo(p, "estimator/evals/<b>golden_dataset.json</b> (16 casos) · evals/<b>dataset.py</b> · "
                "<code>GoldenCase</code> (l. 24), <code>load_dataset()</code> (l. 52)")
    d.code(p, (24, 68, 420, 330), """{
  "id": "case-001-web-saas-crm",
  "transcript": "We want a B2B CRM called Nimbus
     for the sales team. Contacts, deal pipeline,
     basic reporting. Stack: React + Postgres.
     Team of 3.",
  "project_type": "web_saas",
  "expected_in_summary": ["CRM"],
  "expected_technologies_any_of": ["React", "Postgres"],
  "expected_phase_count_range": [3, 6],
  "expected_cost_range_eur": [15000, 80000],
  "expected_duration_weeks_range": [4, 16]
}""", "Un caso feliz")
    d.box(p, (432, 68, 696, 186),
          '<div class="t">Rangos, no números exactos</div>El modelo varía de forma legítima entre ejecuciones. '
          "El test caza lo que se sale de proporción, no cada euro.",
          kind="mint")
    d.box(p, (432, 196, 696, 330),
          '<div class="t">Tres reglas de oro</div><ul><li>El dataset vive <b>comiteado</b>: se puede hacer diff.</li>'
          "<li>Métricas <b>deterministas</b> siempre que se pueda.</li>"
          "<li>Un juez LLM complementa, nunca es el primer escalón.</li></ul>",
          kind="beige")


def slide_metricas(d: Deck) -> None:
    p = d.new("Tres métricas binarias y lo que dijeron", "Ocho casos contra el modo actor, con gpt-4o", "Bloque 3")
    d.codigo(p, "evals/<b>metrics.py</b> · Schema (l. 32), CostBounds (l. 71), ContentRecall (l. 109) · "
                "<code>docker compose -p aieng-s05live exec estimator python -m evals.run --mode actor --limit 8</code>")
    d.box(p, (24, 66, 300, 230),
          '<div class="t">Las métricas</div><ul>'
          "<li><b>schema_adherence</b>: fases suman el total, prefijo «Out of scope» si la confianza baja de 30, "
          "nº de fases en rango.</li>"
          "<li><b>cost_bounds</b>: coste y semanas en rango.</li>"
          "<li><b>content_recall</b>: aparecen los términos y alguna tecnología.</li></ul>",
          kind="lav")
    rows = [("001 CRM", "PASS", "PASS", "PASS"), ("002 fidelización", "PASS", "PASS", "PASS"),
            ("003 RRHH interna", "PASS", "PASS", "PASS"), ("004 ETL datos", "PASS", "<span class='r'>FAIL</span>", "PASS"),
            ("005 vago", "PASS", "PASS", "PASS"), ("006 inyección", "PASS", "PASS", "PASS"),
            ("007 NDA", "<span class='r'>FAIL</span>", "<span class='r'>FAIL</span>", "PASS"),
            ("008 HIPAA", "PASS", "<span class='r'>FAIL</span>", "PASS")]
    d.box(p, (312, 66, 696, 230),
          "<table><tr><th>Caso</th><th>Schema</th><th>Coste</th><th>Recall</th></tr>"
          + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{e}</td></tr>" for a, b, c, e in rows)
          + "</table>", kind="beige", role="table")
    d.box(p, (24, 240, 696, 330),
          '<div class="t">5/8 pasan todo. La lectura útil está en los fallos</div>'
          "El 007 (NDA, tier executive) sale «Out of scope» con confianza baja: el bloque executive pide honestidad y el "
          "modelo se retrae. Con gpt-4o-mini, el 004 daba <b>502</b>: no conseguía que las fases sumaran el total ni con "
          "6 reintentos. <b>Sin el dataset no lo habríamos visto.</b>",
          kind="note")


# ===========================================================================
# Bloques 4-7 · Actor-Critic-Boss
# ===========================================================================

def slide_acb(d: Deck) -> None:
    p = d.new("Actor-Critic-Boss: tres roles, separación estricta", "Del artículo «Building Effective Agents» (Anthropic)",
              "Bloque 4")
    d.codigo(p, "<code>POST /sessions/{id}/estimate-acb</code> · routers/<b>sessions.py</b> (l. 209) · "
                "services/<b>estimation.py</b> · <code>estimate_with_acb()</code> (l. 283)")
    d.box(p, (24, 80, 200, 170), '<div class="t center">Actor</div><div class="center">produce un candidato<br/>'
          "no decide si vale</div>", kind="mint", pad=6)
    d.box(p, (272, 80, 448, 170), '<div class="t center">Critic</div><div class="center">audita y señala defectos<br/>'
          "no reescribe</div>", kind="lav", pad=6)
    d.box(p, (520, 80, 696, 170), '<div class="t center">Boss</div><div class="center">decide qué hacer<br/>'
          "con la auditoría</div>", kind="note", pad=6)
    d.arrow(p, 200, 125, 270, 125, "borrador")
    d.arrow(p, 448, 125, 518, 125, "feedback")
    d.arrow(p, 600, 172, 600, 196)
    d.arrow(p, 590, 196, 112, 196, "iterar con el feedback (máx. 3 rondas)")
    d.arrow(p, 112, 196, 112, 172)
    d.box(p, (24, 216, 352, 330),
          '<div class="t">Fallo 1 · bucle infinito</div>Actor y crítico solos no tienen condición de parada: el crítico '
          "siempre encuentra algo. El Boss pone el <b>límite</b> y el plan B.",
          kind="peach")
    d.box(p, (368, 216, 696, 330),
          '<div class="t">Fallo 2 · sesgo de confirmación</div>Con crítica en texto libre el actor se justifica en vez de '
          "corregir. Con crítica <b>estructurada</b> sabe qué campo concreto rehacer.",
          kind="peach")


def slide_actor(d: Deck) -> None:
    p = d.new("Actor: la pieza que ya teníamos, con otro contrato", "No hay código nuevo de actor; cambia qué hace con su salida",
              "Bloque 5")
    d.codigo(p, "services/<b>estimation.py</b> · <code>estimate_conversational()</code> (l. 177) · closure "
                "<code>_actor()</code> (l. 326) · prompts/estimation/v3/<b>user.j2</b> · <code>&lt;critic_feedback&gt;</code> (l. 13)")
    steps = [("1", "Guardrail de entrada"), ("2", "Resolver tier"), ("3", "Prompt v3"), ("4", "[system] + historial + user"),
             ("5", "LLM estructurado"), ("6", "Guardrail de salida"), ("7", "append + comprimir"), ("8", "Actualizar metadata")]
    for i, (n, t) in enumerate(steps):
        x = 24 + (i % 4) * 170
        y = 68 + (i // 4) * 52
        d.box(p, (x, y, x + 160, y + 44), f"<b>{n}</b> · {t}", kind="mint" if i in (5, 6, 7) else "beige", pad=5)
    d.box(p, (24, 180, 352, 330),
          '<div class="t">El orden 6 → 7 → 8 importa</div>Si guardas antes del guardrail, una respuesta dudosa entra en la '
          "historia como si nada. Si comprimes antes de la metadata, puedes perder hechos aún sin consolidar.",
          kind="note")
    d.box(p, (368, 180, 696, 330),
          '<div class="t">El mismo actor en los dos modos</div>En <code>/estimate</code> su salida es la respuesta. En '
          "<code>/estimate-acb</code> es un <b>candidato</b>. La única diferencia: el template recibe "
          "<code>critic_feedback</code> y Jinja decide si añade el bloque. <b>Cero ramas en Python.</b>",
          kind="lav")


def slide_critic(d: Deck) -> None:
    p = d.new("Critic: feedback estructurado, nunca texto libre", "Instructor valida el formato; el prompt lleva el criterio",
              "Bloque 6")
    d.codigo(p, "app/schemas/<b>critic.py</b> · categorías (l. 23), <code>CriticFeedback</code> (l. 56) · "
                "services/<b>critic.py</b> · <code>review()</code> (l. 39) · prompts/critic/v1/<b>system.j2</b>")
    d.code(p, (24, 68, 420, 230), """class CriticIssue(BaseModel):
    category: Literal["math_error", "hallucination",
        "scope_mismatch", "phase_imbalance",
        "missing_assumption", "unrealistic_estimate",
        "tier_mismatch"]
    severity: Literal["critical", "major", "minor"]
    field_path: str      # "phases[2].cost_eur"
    description: str
    suggested_fix: str | None""", "schemas/critic.py")
    d.box(p, (432, 68, 696, 230),
          '<div class="t"><code>field_path</code> es la clave</div>Un crítico útil dice <b>dónde</b> está el defecto. '
          "El Boss lo pega tal cual en el siguiente prompt del actor: sabe qué campo tocar.",
          kind="mint")
    d.box(p, (24, 240, 352, 330),
          '<div class="t">Veredicto: accept · needs_iteration · reject</div>Validador: iterar exige al menos un '
          "problema <b>critical</b> o <b>major</b>. Por detalles menores no se gasta otra llamada.",
          kind="lav")
    d.box(p, (368, 240, 696, 330),
          '<div class="t">Fallback elegante</div>Si el crítico revienta, devuelve <code>accept</code> con '
          "<code>confidence_in_review=0</code>: el usuario recibe el borrador del actor y el log delata que fue degradado.",
          kind="note")


def slide_boss(d: Deck) -> None:
    p = d.new("Boss: tres salidas en nueve líneas", "Un autómata sobre el veredicto y el presupuesto de iteraciones",
              "Bloque 7")
    d.codigo(p, "services/<b>boss.py</b> · <code>run()</code> (l. 56), <code>_decide()</code> (l. 112), "
                "<code>_synthesize_fallback()</code> (l. 123) · config.py · <code>BOSS_MAX_ITERATIONS = 3</code> (l. 72)")
    rows = [("accept", "—", "<b>accept</b>", "devuelve el borrador"),
            ("reject", "—", "<b>synthesize</b>", "no tiene arreglo con este actor"),
            ("needs_iteration", "quedan", "<b>iterate</b>", "vuelve al actor con el feedback"),
            ("needs_iteration", "no quedan", "<b>synthesize</b>", "lo intentó y no convergió")]
    d.box(p, (24, 66, 452, 210),
          "<table><tr><th>Crítico dice</th><th>Rondas</th><th>Boss decide</th><th>Qué pasa</th></tr>"
          + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{e}</td></tr>" for a, b, c, e in rows)
          + "</table>", kind="beige", role="table")
    d.box(p, (464, 66, 696, 210),
          '<div class="t">Stateless</div>El Boss recibe <b>funciones</b> (actor y crítico), no objetos: en los tests se '
          "inyectan falsos sin mocks complicados. No recuerda nada entre estimaciones.",
          kind="lav")
    d.box(p, (24, 220, 696, 330),
          '<div class="t">Synthesize no tira el trabajo</div>Devuelve el último borrador del actor con los avisos del '
          "crítico delante («⚠ Open caveats…») y la confianza a la mitad, con suelo de 30 para no caer en «Out of scope». "
          "La honestidad viaja en <code>final_decision</code>. En la sesión solo se guarda la respuesta final: los "
          "borradores son de usar y tirar.",
          kind="mint")


def slide_demo_acb(d: Deck) -> None:
    p = d.new("Demo ACB: las tres rutas en ejecuciones reales", "Crítico con gpt-4o y con gpt-4o-mini", "Bloque 7")
    d.codigo(p, "<b>Interfaz:</b> Demo presets → «ACB · CRM + Stripe» y «ACB · marketplace imposible» · traza "
                "desplegable bajo el resultado · <code>CRITIC_MODEL</code> en <code>estimator/.env</code>")
    d.code(p, (24, 68, 360, 200), """CRM + facturación con Stripe
  iteración 0 · accept (90)
  → accept · 46.000 €

marketplace: pagos, KYC, chat, app…
2 personas en 6 semanas
  ejecución A · reject → synthesize
  ejecución B · needs_iteration → accept""", "Crítico gpt-4o")
    d.code(p, (372, 68, 696, 200), """CRM + facturación con Stripe
  iteración 0 · needs_iteration
  iteración 1 · needs_iteration
  iteración 2 · needs_iteration
  → synthesize (sin rondas) · 57.000 €
  [critical] math_error @ total_cost_eur
  aunque las fases sí sumaban 57.000""", "Crítico gpt-4o-mini")
    d.image(p, (24, 208, 452, 330), "s05-ui-traza-acb.png")
    d.box(p, (464, 208, 696, 330),
          '<div class="t">Dos lecturas</div>La misma entrada no sale igual dos veces. Y un crítico pequeño da '
          "<b>falsos positivos</b> (un <code>math_error</code> que no existe) que queman rondas.",
          kind="note")


def slide_tradeoffs(d: Deck) -> None:
    p = d.new("Trade-offs: ¿compensa el ACB?", "Los mismos ocho casos del golden dataset en los dos modos", "Bloque 8")
    d.codigo(p, "<code>… exec estimator python -m evals.run --mode actor --limit 8</code> · "
                "<code>… --mode acb --limit 8</code> · resultados en <code>estimator/evals/actor.json</code> y <code>acb.json</code>")
    d.box(p, (24, 66, 360, 186),
          "<table><tr><th>Modo</th><th>Casos OK</th><th>Llamadas LLM / turno</th></tr>"
          "<tr><td><b>actor</b></td><td><b>5/8</b></td><td>2 (actor + metadata)</td></tr>"
          "<tr><td><b>acb</b></td><td><b>6/8</b></td><td>3-7 (+ crítico y rondas)</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (372, 66, 696, 186),
          '<div class="t">Dónde ganó</div>El 004 (ETL) se salía del rango de coste con el actor solo y entró con el '
          "ACB. El 007 (NDA) falla en los dos: el crítico no arregla un prompt que empuja a «Out of scope».",
          kind="mint")
    d.box(p, (24, 196, 352, 330),
          '<div class="t">No usarlo</div><ul><li>Estimaciones rápidas de baja confianza.</li>'
          "<li>Conversaciones de 1-2 turnos.</li><li>Cuando el coste por llamada pesa más que la calidad marginal.</li></ul>",
          kind="peach")
    d.box(p, (368, 196, 696, 330),
          '<div class="t">Sí usarlo</div><ul><li>Cliente importante o contrato grande.</li>'
          "<li>Proyectos con NDA o normativa: un error de cifra cuesta caro.</li>"
          "<li>Cualquier agente que escribe y puede contradecirse.</li></ul>",
          kind="mint")


def slide_interfaz(d: Deck) -> None:
    p = d.new("La interfaz: todo esto sin tocar Python", "Cliente Rails en localhost:3000", "Bloque 8")
    d.codigo(p, "estimator-web/app/views/chat_sessions/<b>_form.html.erb</b> (tier y modo) · <b>_metadata_panel</b> · "
                "<b>_estimation_result</b> (traza) · services/estimator_ai/<b>client.rb</b>")
    d.image(p, (24, 64, 696, 196), "s05-ui-formulario.png")
    d.box(p, (24, 206, 696, 336),
          '<div class="t">Qué hay en pantalla</div><ul>'
          "<li><b>Demo presets</b>: un clic rellena cada demo de hoy · <b>Audience tier</b>: auto o forzado (el override) · "
          "<b>Estimation mode</b>: actor o Actor-Critic-Boss.</li>"
          "<li>Panel lateral: tier y regla, ventana, anclas y caracteres de resumen. Bajo el resultado, la traza del ACB.</li>"
          "<li>Cualquier stack lo replica: multipart a la API, dos endpoints y un <code>GET /sessions/{id}</code>. "
          "El cliente nunca habla con OpenAI directamente.</li></ul>",
          kind="lav")


def slide_cierre(d: Deck) -> None:
    p = d.new("Lo que cierras hoy", "", "Cierre")
    d.box(p, (24, 66, 352, 250),
          '<div class="t">Hoy</div><ul>'
          "<li>Memoria que no olvida lo pactado: resumen + anclas + ventana.</li>"
          "<li>La audiencia se deduce del contexto, con override humano.</li>"
          "<li>Un golden dataset que caza regresiones antes que el cliente.</li>"
          "<li>Actor-Critic-Boss: auditar en vez de inventar.</li></ul>",
          kind="mint")
    d.box(p, (368, 66, 696, 250),
          '<div class="t">Para pensar</div><ul>'
          "<li>¿Qué debería ser ancla en vuestro dominio?</li>"
          "<li>¿Cuándo confiar en el resolver y cuándo forzar el tier?</li>"
          "<li>¿Qué octava categoría añadiríais al crítico?</li>"
          "<li>¿Qué cuarto rol añadiríais al patrón?</li></ul>",
          kind="lav")
    d.box(p, (24, 260, 696, 330),
          '<div class="t">Sesión 6 · Data-driven AI</div>Análisis, formateo y normalización de los datos que alimentan '
          "al estimador: el primer paso para que los adjuntos de hoy acaben en un RAG de verdad. "
          "El código de referencia de hoy está en la rama <code>session_05_live</code>.",
          kind="beige")


# ===========================================================================

def build() -> None:
    d = Deck()
    cover(d)
    slide_hoy(d)
    slide_ejercicio(d)
    slide_orden(d)
    slide_adjuntos(d)
    slide_estrategias(d)
    slide_compresion(d)
    slide_anclas(d)
    slide_demo_compresion(d)
    slide_tiers(d)
    slide_resolver(d)
    slide_golden(d)
    slide_metricas(d)
    slide_acb(d)
    slide_actor(d)
    slide_critic(d)
    slide_boss(d)
    slide_demo_acb(d)
    slide_tradeoffs(d)
    slide_interfaz(d)
    slide_cierre(d)
    d.template(10)  # ROTI
    d.template(11)  # gracias
    d.save()


if __name__ == "__main__":
    build()
