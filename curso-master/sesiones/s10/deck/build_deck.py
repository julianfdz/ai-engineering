"""Genera el deck de la Sesión 10 (Técnicas avanzadas de recuperación) de Julián Fernández.

Reutiliza el motor del deck de la Sesión 7 (cajas con autoajuste, pie, imágenes) y la plantilla de
LIDR de esa sesión para la portada (con el título cambiado), el ROTI y el cierre. Intercala las 6
diapositivas oficiales de LIDR de la S10 (``slides-lidr/``) con diapos propias y demos reales.

    python diagramas_s10.py   # si cambian los diagramas
    python build_deck.py
    # → ../Sesion10-Julian-Fernandez.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "s07" / "deck"))
import build_deck as base  # noqa: E402  (motor del deck de la S7)

base.TEMPLATE = HERE.parent.parent / "s07" / "deck" / "plantilla-lidr-s07.pdf"
base.OUTPUT = HERE.parent / "Sesion10-Julian-Fernandez.pdf"
base.SVGS = ["s10-rrf", "s10-rerank", "s10-decaimiento"]
LIDR = HERE / "slides-lidr"
H = base.H
base.Y1_REAL = 358   # deja sitio a la franja «En el código» encima del pie
CODIGO = fitz.Rect(12, 362, base.W - 12, 385)


class Deck(base.Deck):
    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, base.W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 10 · '
               f"Técnicas avanzadas de recuperación · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, base.W - 12, H - 2), txt, css=base.CSS)

    def codigo(self, page: fitz.Page, ref: str) -> None:
        """Franja al pie: dónde se ve en el código lo que cuenta la diapo."""
        page.draw_rect(CODIGO, color=(0.25, 0.27, 0.33), fill=(0.13, 0.15, 0.2), width=0.5, radius=0.25)
        page.insert_htmlbox(CODIGO + (8, 5, -8, -3),
                            f'<div style="font-size:7.6pt;color:#e5e7eb"><b style="color:#a5b4fc">▶ En el código</b> &nbsp; {ref}</div>',
                            css=base.CSS, scale_low=0.6)

    def lidr(self, name: str, ref: str = "") -> None:
        """Diapositiva oficial de LIDR a pantalla completa (1920×1080 = 16:9, encaja exacta)."""
        self.flush()
        page = self.doc.new_page(width=base.W, height=H)
        page.insert_image(page.rect, filename=str(LIDR / name))
        if ref:   # etiqueta en la esquina superior derecha, que en estas diapos está libre
            tag = fitz.Rect(base.W - 262, 8, base.W - 10, 30)
            page.draw_rect(tag, color=(0.39, 0.4, 0.95), fill=(0.08, 0.09, 0.15), width=0.8, radius=0.3)
            page.insert_htmlbox(tag + (7, 5, -7, -2),
                                f'<div style="font-size:7pt;color:#e5e7eb"><b style="color:#a5b4fc">▶ Código</b> &nbsp;{ref}</div>',
                                css=base.CSS, scale_low=0.6)


def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    page.add_redact_annot(fitz.Rect(48, 158, 470, 242), fill=False)
    page.add_redact_annot(fitz.Rect(48, 124, 330, 147), fill=False)   # línea del módulo de la plantilla
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for y, line in ((191, "Sesión 10: Técnicas"), (232, "avanzadas de recuperación")):
        page.insert_text((51, y), line, fontname="hebo", fontsize=34.5, color=(1, 1, 1))
    page.insert_text((51, 141), "MÓDULO 4: Arquitectura RAG", fontname="hebo", fontsize=15, color=(1, 1, 1))


# ===========================================================================
# Diapos propias
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: de un índice a un pipeline", "Decidir dónde buscar, cómo preguntar, qué excluir y cómo desempatar",
              "Apertura")
    arco = [("S8", "pgvector", "beige"), ("S9", "RAG y estimate", "beige"), ("S10 · HOY", "recuperación avanzada", "lav"),
            ("S11", "generación y calidad", "beige")]
    x = 24
    for i, (t, sub, k) in enumerate(arco):
        d.box(p, (x, 68, x + 156, 108), f'<div class="t center">{t}</div><div class="s center">{sub}</div>', kind=k, pad=4)
        x += 170
    items = [
        ("Bloque 1 · 15 min", "Lo que traéis: RRF, idioma del tsvector y reranking"),
        ("Bloque 2 · 90 min", "Multi-índice y routing · expansión y descomposición · filtros, decaimiento y arnés"),
        ("Bloque 3 · 25 min", "Del retrieval al producto: horas por tarea con humano en el lazo"),
    ]
    y = 120
    for t, desc in items:
        d.box(p, (24, y, 440, y + 52), f"<b>{t}</b><br/>{desc}", kind="lav", pad=6)
        y += 60
    d.box(p, (452, 120, 696, 292),
          '<div class="t">Al salir de hoy sabréis…</div>'
          "<ul><li>Elegir y ordenar las etapas de un pipeline de recuperación.</li>"
          "<li>Mandar cada pregunta a su colección.</li>"
          "<li>Medir cada técnica antes de dejarla encendida.</li>"
          "<li>Anclar las horas de un presupuesto en datos históricos.</li></ul>",
          kind="mint")
    d.html(p, (24, 300, 696, 345),
           '<div class="center"><b>Regla de oro:</b> cada etapa entra una lista de chunks y sale una lista de chunks. '
           "Un toggle la enciende o la apaga sin tocar código.</div>")


def slide_prework(d: Deck) -> None:
    p = d.new("Lo que traéis del ejercicio previo", "Los tres cimientos que reutiliza el resto de la sesión", "Bloque 1")
    d.codigo(p, "scripts/eval_retrieval_s10.py · <code>CONFIGS</code> (l. 93) · app/generation/rag/retrieval/fusion.py · reranker.py")
    cards = [
        ("1.1 · Búsqueda híbrida + RRF", "Rama vectorial + rama léxica (<code>tsvector</code>) fusionadas por posición. "
         "Vuelve en la expansión de consultas.", "mint"),
        ("1.2 · Idioma del tsvector", "Columna y consulta con la <b>misma</b> configuración, la del idioma del corpus. "
         "Si no, el índice se ignora en silencio.", "note"),
        ("1.3 · Reranking", "Cross-encoder sobre los 50 mejores. <b>Hoy no se reprograma</b>: se calienta, se compone como "
         "etapa y se mide.", "lav"),
    ]
    x = 24
    for t, body, k in cards:
        d.box(p, (x, 70, x + 216, 250), f'<div class="t">{t}</div>{body}', kind=k, pad=8)
        x += 228
    d.box(p, (24, 262, 696, 340),
          '<div class="t">Y el arnés</div><code>scripts/eval_retrieval_s10.py</code> + golden set: cada configuración es un '
          "dato, no una rama de código. Hoy añadimos filas a vuestra tabla.",
          kind="beige")


def slide_rrf(d: Deck) -> None:
    p = d.new("1.1 · Calibración de RRF", "app/generation/rag/retrieval/fusion.py · RRF_K = 60", "Bloque 1")
    d.codigo(p, "app/generation/rag/retrieval/fusion.py · <code>reciprocal_rank_fusion()</code> (l. 25) · app/config.py · <code>RRF_K</code> (l. 150)")
    d.image(p, (24, 62, 696, 330), "s10-rrf.png")
    d.html(p, (24, 332, 696, 345),
           '<div class="center s">60 es el valor del paper de Cormack et al. y nuestro default: no se optimiza sin evidencia.</div>')


def slide_tsvector(d: Deck) -> None:
    p = d.new("1.2 · El idioma del tsvector", "La configuración sigue al idioma del corpus, no al del enunciado", "Bloque 1")
    d.codigo(p, "app/generation/rag/store/models.py · <code>FTS_REGCONFIG</code> (l. 54), <code>content_tsv</code> (l. 100) · repository.py · <code>search_lexical()</code> (l. 175)")
    d.code(p, (24, 68, 400, 200), """# store/models.py — columna generada
content_tsv = Computed(
    "to_tsvector('english', content)",
    persisted=True)

# store/repository.py — la consulta
plainto_tsquery("english", query_text)""", "Las dos referencias deben coincidir")
    d.code(p, (24, 210, 400, 340), """psql> SELECT to_tsvector('english',
          'Stripe Connect onboarding')
       @@ plainto_tsquery('english',
          'stripe onboarding') AS matches;
 matches
---------
 t""", "Demo · comprobarlo en psql")
    d.box(p, (412, 68, 696, 200),
          '<div class="t">La trampa</div>'
          "El enunciado dice \"corpus en español\", pero el dataset está <b>en inglés</b>. Poner <code>spanish</code> "
          "sobre texto inglés rompe el stemming y el híbrido degrada a solo vectorial <b>sin avisar</b>.",
          kind="peach")
    d.box(p, (412, 210, 696, 340),
          '<div class="t">Qué aporta al estimador</div>'
          "La rama léxica es la que encuentra los identificadores exactos (<code>Stripe</code>, <code>SAP</code>, "
          "<code>BUD-2024-014</code>) que el embedding diluye en \"algo de pagos\".",
          kind="mint")


def slide_rerank(d: Deck) -> None:
    p = d.new("1.3 · Reranking: cross-encoder y latencia en frío", "app/generation/rag/retrieval/reranker.py", "Bloque 1")
    d.codigo(p, "app/generation/rag/retrieval/reranker.py · <code>score()</code> (l. 77), <code>rerank_with_scores()</code> (l. 97) · advanced_pipeline.py etapa 6 (l. 263)")
    d.image(p, (24, 62, 696, 330), "s10-rerank.png")
    d.html(p, (24, 332, 696, 345),
           '<div class="center s">Antes de clase: <code>python -m app.generation.rag.retrieval.verify_reranker</code></div>')


def slide_routing_demo(d: Deck) -> None:
    p = d.new("Routing en directo: los tres primeros niveles", "POST /v1/retrieval/advanced-search", "Bloque 2")
    d.codigo(p, "<b>Interfaz:</b> Búsqueda → «Routing · reglas / clasificador / explícito» · app/generation/rag/retrieval/router.py · <code>route()</code> (l. 73) · collections.py · <code>match_rules()</code> (l. 195) · app/api/routers/retrieval_advanced.py (l. 92)")
    d.code(p, (24, 68, 696, 152), """«what did the client say in the meeting about Stripe checkout»
→ level: rules   targets: [transcript]   technique: expand   cardinality: {transcript: 11}""",
           "Nivel 1 · reglas (vocabulario de reunión, sin LLM)")
    d.code(p, (24, 160, 696, 244), """«OAuth 2.0 PKCE flow and PSD2 strong customer authentication reference»
→ level: classifier   targets: [technical_doc]
  reason: "...technical topics best addressed by internal technical documentation." """,
           "Nivel 2 · clasificador LLM")
    d.code(p, (24, 252, 696, 336), """«telemedicine appointment scheduling»  +  "collections": ["budget"]
→ level: explicit     targets: [budget]           (el contrato manda, no se clasifica)""",
           "Nivel 0 · explícito")


def slide_decompose_demo(d: Deck) -> None:
    p = d.new("Descomposición en directo", "Una transcripción multi-tema se parte por temas", "Bloque 2")
    d.codigo(p, "<b>Interfaz:</b> Búsqueda → «Descomposición» y «Consulta directa» · app/generation/rag/retrieval/query_transform.py · <code>choose_technique()</code> (l. 82) · fusion.py · <code>round_robin_merge()</code> (l. 63) · advanced_pipeline.py · <code>_fuse_collection()</code> (l. 134)")
    d.code(p, (24, 68, 420, 250), """query: "we need OAuth and a transaction ledger,
  plus a Stripe checkout, and also personalized
  recommendations for the product catalog"

→ technique: decompose     (4 sub-consultas)
  · OAuth
  · transaction ledger
  · Stripe checkout
  · personalized recommendations

  p. ej. «How to integrate Stripe checkout
          into an e-commerce website?»""", "Demo · ejecución real")
    d.code(p, (432, 68, 696, 160), """query: "Stripe checkout"

→ technique: direct
  (sin LLM)""", "Consulta corta, un tema")
    d.box(p, (432, 170, 696, 250),
          '<div class="t">Sin LLM cuando no hace falta</div><code>choose_technique()</code> decide por longitud y '
          "conectores. Si el LLM falla, degrada a consulta directa.",
          kind="mint")
    d.box(p, (24, 262, 696, 340),
          '<div class="t">Qué aporta al estimador</div>'
          "La entrada real es una transcripción que mezcla login, cobros y catálogo. Un solo embedding queda \"cerca de todo, "
          "lejos de nada\". Descomponiendo, <b>cada módulo del desglose tiene su evidencia</b>, no solo el dominante.",
          kind="lav")


def slide_decay(d: Deck) -> None:
    p = d.new("Decaimiento temporal", "app/generation/rag/retrieval/temporal.py", "Bloque 2")
    d.codigo(p, "app/generation/rag/retrieval/temporal.py · <code>decay_weight()</code> (l. 33) · advanced_pipeline.py · <code>_sigmoid()</code> (l. 128) y decaimiento (l. 279)")
    d.image(p, (24, 62, 696, 330), "s10-decaimiento.png")


def slide_filtro_demo(d: Deck) -> None:
    p = d.new("Filtro duro en directo: vigilar la cardinalidad", "min_date excluye antes de buscar", "Bloque 2")
    d.codigo(p, "<b>Interfaz:</b> Búsqueda → «Filtro por fecha» · Corpus → ver las 1543 tareas · app/generation/rag/retrieval/collections.py · <code>hard_filter_clauses()</code> (l. 106) · store/repository.py · <code>search_filtered()</code> (l. 107) · log cardinalidad (advanced_pipeline.py l. 251)")
    d.code(p, (24, 68, 420, 190), """«telemedicine scheduling and video consultations»

sin filtro                       → budget: 1603
"min_date": "2024-01-01"         → budget:  748
+ "sectors": ["healthcare"]      → budget:   84""", "Demo · ejecución real")
    d.box(p, (432, 68, 696, 190),
          '<div class="t">La trampa del post-filtrado</div>Con HNSW, filtrar después puede vaciar el resultado '
          "<b>en silencio</b>. Por eso se loguea siempre la cardinalidad tras el filtro.",
          kind="peach")
    d.box(p, (24, 202, 696, 340),
          '<div class="t">Lo que nos dice la cardinalidad</div>'
          "Los 1603 no son 60 presupuestos: en la misma tabla viven también las <b>1543 tareas históricas</b> del Bloque 3. "
          "Sin mirar la cardinalidad no lo sabrías. Y si una demo da <code>low_confidence: true</code> con cardinalidad 0, "
          "es el filtro vaciando la colección: se relaja y se mira el log.<br/><br/>"
          "<b>Para el estimador:</b> estimar una clínica con presupuestos de healthcare de 2024, no con un e-commerce de 2019.",
          kind="note")


def slide_arnes(d: Deck) -> None:
    p = d.new("El arnés: medir antes de encender", "Un banco de pruebas que pasa las mismas preguntas por cada configuración",
              "Bloque 2")
    d.codigo(p, "scripts/eval_retrieval_s10.py · <code>CONFIGS</code> (l. 93) · evals/golden_retrieval.json · "
                "<code>docker compose -p aieng-s10live exec estimator python scripts/eval_retrieval_s10.py</code>")
    steps = [("1 · Golden set", "8 preguntas con la respuesta correcta ya marcada: qué presupuestos, transcripciones o "
              "documentos deberían salir.", "note"),
             ("2 · Configuraciones", "Cada fila (A…H) es un juego de toggles: vector, híbrido, rerank, routing… "
              "Son <b>datos</b>, no ramas de código.", "lav"),
             ("3 · Se mide", "<b>Precision@5</b>: de los 5 primeros resultados, cuántos son correctos. "
              "<b>Latencia</b>: cuánto tarda.", "mint")]
    x = 24
    for t, body, k in steps:
        d.box(p, (x, 68, x + 216, 214), f'<div class="t">{t}</div>{body}', kind=k, pad=8)
        x += 228
    d.box(p, (24, 226, 696, 300),
          '<div class="t">Por qué importa</div>Cada técnica tiene un coste (latencia, llamadas al LLM). El arnés dice si '
          "<b>esa</b> técnica mejora <b>tus</b> preguntas antes de dejarla encendida en producción.",
          kind="beige")


def slide_arnes_local(d: Deck) -> None:
    p = d.new("Nuestra ejecución del arnés", "El mismo arnés sobre nuestro corpus (con las 1543 tareas en la tabla de presupuestos)",
              "Bloque 2")
    d.codigo(p, "<code>docker compose -p aieng-s10live exec estimator python scripts/eval_retrieval_s10.py</code> · "
                "la matriz por consulta sale debajo de la tabla")
    rows = [("A", "Vector", "0,48", "229 ms"), ("B", "Hybrid", "0,48", "225 ms"), ("C", "Vector + Rerank", "0,62", "1142 ms"),
            ("D", "Hybrid + Rerank", "0,62", "1131 ms"), ("E", "Hybrid + Rerank + Temporal", "0,48", "1148 ms"),
            ("F", "Multi-index routing", "0,25", "1451 ms"), ("G", "Query transform", "0,62", "3002 ms"),
            ("H", "Full pipeline", "0,25", "1961 ms")]
    d.box(p, (24, 66, 360, 300),
          "<table><tr><th>Config</th><th>Etapas</th><th>P@5</th><th>Latencia</th></tr>"
          + "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td><b>{c}</b></td><td>{e}</td></tr>" for a, b, c, e in rows)
          + "</table>",
          kind="beige", role="table")
    d.box(p, (372, 66, 696, 140),
          '<div class="t">El reranking sí paga aquí</div>Q3 y Q4 pasan de 0,20 a 0,60. Con ruido en el índice, el '
          "cross-encoder separa lo parecido de lo correcto.",
          kind="mint")
    d.box(p, (372, 148, 696, 222),
          '<div class="t">El decaimiento rompe una consulta</div>Q5 cae de 0,80 a 0,00: la buena respuesta era antigua. '
          "Por eso va apagado por defecto.",
          kind="peach")
    d.box(p, (372, 230, 696, 300),
          '<div class="t">El routing, igual que en LIDR</div>Gana en las consultas que cruzan colecciones (Q8: 0 → 0,40) y '
          "hunde las de presupuestos (Q1–Q5 → 0).",
          kind="lav")


def slide_horas_demo(d: Deck) -> None:
    p = d.new("Horas por tarea: análogo o fila roja", "POST /v1/estimate/tasks/hours · consenso de los vecinos", "Bloque 3")
    d.codigo(p, "app/generation/rag/task_hours.py · <code>_consensus()</code> (l. 63), <code>estimate_one()</code> (l. 99) · app/api/routers/estimate_tasks.py (l. 40)")
    d.code(p, (24, 68, 420, 250), """"Payment gateway integration"
  "Card payments via a PSP with 3-D Secure"
→ estimated_hours: 42
  reliability:     0.505    dispersion: 0.278
  has_match:       true     neighbors: 5
    TASK-2024-0003 · 54 h · distance 0.29 ...

"Quantum teleporter"  ("nonexistent")
→ estimated_hours: null
  has_match:       false      ← fila roja""", "Demo · ejecución real")
    d.box(p, (432, 68, 696, 250),
          '<div class="t">El número es trazable</div>'
          "Cada hora viene con sus <code>neighbors</code>: los proyectos históricos de los que sale. Si un número es raro, "
          "se mira de dónde viene. <b>No es una caja negra.</b>",
          kind="mint")
    d.box(p, (24, 262, 696, 340),
          '<div class="t">Ajustes en caliente</div><code>TASK_HOURS_TOP_K</code> (vecinos del consenso) y '
          "<code>TASK_HOURS_DISTANCE_THRESHOLD</code> (el umbral del rojo) se cambian sin reiniciar con "
          "<code>PUT /api/v1/config/retrieval</code> (Swagger: localhost:8000/docs). Con el reranking encendido, menos rojos.",
          kind="beige")


def slide_wizard(d: Deck) -> None:
    p = d.new("El wizard de estimación, paso a paso", "Rails · Rag::EstimationRunsController", "Bloque 3")
    d.codigo(p, "Interfaz: <b>localhost:3000/rag/estimation_runs/new</b> · estimator-web/app/controllers/rag/estimation_runs_controller.rb · prompt_builder.py · <code>build_system_prompt(include_hours=False)</code> (l. 14)")
    steps = [("1", "Transcripción", "el brief del cliente"), ("2", "Reformulación", "brief limpio"),
             ("3", "Estructura", "el LLM propone módulos y tareas, sin horas"), ("4", "Revisión #1", "un humano edita la estructura"),
             ("5", "Horas", "búsqueda vectorial por tarea, rojo si no hay análogo"),
             ("6", "Revisión #2", "horas y tarifas €/h · confirmar")]
    for i, (n, t, sub) in enumerate(steps):
        col, row = i % 3, i // 3
        x, y = 24 + col * 228, 70 + row * 130
        kind = "note" if t.startswith("Revisión") else ("mint" if t == "Horas" else "lav")
        d.box(p, (x, y, x + 216, y + 118), f'<div class="t">{n} · {t}</div>{sub}', kind=kind, pad=8)
    d.html(p, (24, 334, 696, 345),
           '<div class="center s">El <code>POST /v1/estimate/from-transcript</code> de la S9 sigue intacto: el LLM infiere las '
           "horas frente a horas derivadas de evidencia.</div>")


def slide_cuadro(d: Deck) -> None:
    p = d.new("El cuadro de mando: cada técnica, cuándo y a qué precio", "Encenderla solo con evidencia del arnés", "Cierre")
    d.codigo(p, "app/config.py (l. 141–184) · toggles en caliente: <code>GET/PUT /api/v1/config/retrieval</code> (Swagger: localhost:8000/docs)")
    rows = [
        ("Híbrido + RRF", "identificadores exactos", "~0 ms", "casi siempre"),
        ("Reranking", "orden por relevancia real", "+2,6 s", "precisión importa más que latencia"),
        ("Routing", "mandar a la colección correcta", "+1 LLM pequeño", "la consulta señala su tipo"),
        ("Expansión", "vocabulario distinto", "+1 LLM", "consulta corta y ambigua"),
        ("Descomposición", "varios temas en una", "+1 LLM", "transcripciones largas"),
        ("Filtros duros", "comparar solo lo comparable", "baja el coste", "hay metadatos fiables"),
        ("Decaimiento", "preferir lo reciente", "~0 ms", "las tarifas cambian con el tiempo"),
    ]
    d.box(p, (24, 66, 696, 270),
          "<table><tr><th>Técnica</th><th>Qué resuelve</th><th>Coste</th><th>Cuándo</th></tr>"
          + "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{e}</td></tr>" for a, b, c, e in rows)
          + "</table>",
          kind="beige", role="table")
    d.box(p, (24, 280, 696, 345),
          '<div class="center"><b>Una técnica no es universalmente buena.</b> El routing mejora las consultas que cruzan '
          "colecciones y hunde las que no dicen su tipo. Mide cada etapa sobre tu caso de uso.</div>",
          kind="mint")


def slide_cierre(d: Deck) -> None:
    p = d.new("Lo que cierras hoy · lo que abre la S11", "", "Cierre")
    d.box(p, (24, 66, 352, 300),
          '<div class="t">Hoy</div><ul>'
          "<li>Tres colecciones y un router en cascada.</li>"
          "<li>Expansión y descomposición de consultas.</li>"
          "<li>Filtros duros y decaimiento temporal.</li>"
          "<li>Un pipeline de etapas conmutables y medibles.</li>"
          "<li>Horas por tarea ancladas en datos, con humano en el lazo.</li></ul>",
          kind="mint")
    d.box(p, (368, 66, 696, 300),
          '<div class="t">Sesión 11 · RAG avanzado</div><ul>'
          "<li>Generación con el contexto recuperado.</li>"
          "<li>Calidad: cómo medir si la respuesta es buena.</li>"
          "<li>El router acotado de hoy es el precursor del <i>handover</i> agéntico.</li></ul>",
          kind="lav")
    d.html(p, (24, 310, 696, 345),
           '<div class="center">Todo el código de referencia está en la rama <code>session_10_live</code>.</div>')


# ===========================================================================

def build() -> None:
    d = Deck()
    cover(d)
    slide_hoy(d)
    slide_prework(d)
    slide_rrf(d)
    slide_tsvector(d)
    slide_rerank(d)
    d.lidr("sesion-10-slide-01-pipeline-orden.jpg", "app/generation/rag/retrieval/advanced_pipeline.py · <code>advanced_retrieve()</code> l. 160")
    d.lidr("sesion-10-slide-02-routing-cascada.jpg", "app/generation/rag/retrieval/router.py · <code>route()</code> l. 73")
    slide_routing_demo(d)
    d.lidr("sesion-10-slide-03-expansion-descomposicion.jpg", "app/generation/rag/retrieval/query_transform.py · l. 82–142")
    slide_decompose_demo(d)
    d.lidr("sesion-10-slide-04-filtros-decaimiento.jpg", "app/generation/rag/retrieval/collections.py l. 106 · temporal.py l. 33")
    slide_decay(d)
    slide_filtro_demo(d)
    slide_arnes(d)
    d.lidr("sesion-10-slide-05-arnes-lectura-honesta.jpg", "scripts/eval_retrieval_s10.py · <code>CONFIGS</code> l. 93")
    slide_arnes_local(d)
    d.lidr("sesion-10-slide-06-human-in-the-loop.jpg", "app/generation/rag/task_hours.py · <code>_consensus()</code> l. 63")
    slide_horas_demo(d)
    slide_wizard(d)
    slide_cuadro(d)
    slide_cierre(d)
    d.template(10)  # ROTI
    d.template(11)  # gracias
    d.save()


if __name__ == "__main__":
    base.render_svgs()
    build()
