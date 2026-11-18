"""Genera el deck de la Sesión 11 (RAG avanzado: generación y calidad) de Julián Fernández.

Reutiliza el motor del deck de la Sesión 7 y la franja grande «En el código» de la Sesión 5. Cada diapo de
contenido lleva al pie el fichero y la línea que se abre en VS Code (rama session_11_live_local, worktree
ai-engineering-s11). Las cifras son las de la ejecución en local del 17/11/2026.

    python build_deck.py
    # → ../Sesion11-Julian-Fernandez.pdf
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
# El deck de la S5 (motor de la S7 + franja «En el código»), cargado con otro nombre de módulo:
# los tres ficheros se llaman build_deck.py y un import normal se resolvería a sí mismo.
_spec = importlib.util.spec_from_file_location("s05_deck", HERE.parent.parent / "s05" / "deck" / "build_deck.py")
s05 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s05)

base = s05.base
base.OUTPUT = HERE.parent / "Sesion11-Julian-Fernandez.pdf"
H, W = base.H, base.W


class Deck(s05.Deck):
    def footer(self, page: fitz.Page, section: str) -> None:
        band = fitz.Rect(0, H - 17, W, H)
        page.draw_rect(band, color=None, fill=(0.965, 0.96, 0.95))
        page.draw_line(band.tl, band.tr, color=(0.85, 0.83, 0.8), width=0.5)
        txt = (f'<div style="font-size:6.8pt;color:#6b655b">{section}'
               f'<span style="color:#9b958a"> &nbsp;&nbsp;|&nbsp;&nbsp; Julián Fernández · Sesión 11 · '
               f"RAG avanzado: generación y calidad · {len(self.doc)}</span></div>")
        page.insert_htmlbox(fitz.Rect(12, H - 14.5, W - 12, H - 2), txt, css=base.CSS)


def cover(d: Deck) -> None:
    d.doc.insert_pdf(d.tpl, from_page=0, to_page=0)
    page = d.doc[-1]
    page.add_redact_annot(fitz.Rect(48, 158, 470, 242), fill=False)
    page.add_redact_annot(fitz.Rect(48, 124, 330, 147), fill=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for y, line in ((191, "Sesión 11: RAG avanzado,"), (232, "generación y calidad")):
        page.insert_text((51, y), line, fontname="hebo", fontsize=34.5, color=(1, 1, 1))
    page.insert_text((51, 141), "MÓDULO 4: Arquitectura RAG", fontname="hebo", fontsize=15, color=(1, 1, 1))


# ===========================================================================
# Apertura y Bloque 1 · pre-vuelo
# ===========================================================================

def slide_hoy(d: Deck) -> None:
    p = d.new("Hoy: de una estimación citada a una estimación medible",
              "Cada técnica nueva se mide contra el baseline que traéis: medir → mejorar → medir", "Apertura")
    d.codigo(p, "<b>Interfaz:</b> menú <b>Calidad</b> (una pestaña por técnica) y <b>Corpus</b> · "
                "rama <code>session_11_live_local</code> · todo lo de hoy vive en "
                "<code>app/generation/rag/quality/</code>")
    pasos = [("Citada", "S9 · cada cifra con su &lt;source&gt;", "beige"),
             ("Verificable", "Ejercicio · el chunk_id citado existe", "beige"),
             ("Fundamentada", "Hoy · la cifra se deduce de la cita", "mint"),
             ("Medible", "Hoy · RAGAS como puerta y monitor", "lav")]
    for i, (t, s, k) in enumerate(pasos):
        x = 24 + i * 170
        d.box(p, (x, 66, x + 156, 128), f'<div class="t center">{t}</div><div class="center s">{s}</div>', kind=k)
        if i < 3:
            d.arrow(p, x + 157, 97, x + 169, 97)
    bloques = [("1 · Pre-vuelo y errores", "15'"), ("2 · Leer la tabla RAGAS", "15'"),
               ("3 · Detección de alucinaciones", "25'"), ("4 · Augmentation y síntesis", "25'"),
               ("5 · Evaluación en dos modos", "20'"), ("6 · Ampliar e indexar el corpus", "12'")]
    for i, (t, m) in enumerate(bloques):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 142 + row * 64
        d.box(p, (x, y, x + 332, y + 56), f"<b>{t}</b> &nbsp;<span class='s'>{m}</span>", kind="note" if i in (2, 3) else "beige")


def slide_ejercicio(d: Deck) -> None:
    p = d.new("Lo que traéis: citación verificable por línea", "No se reexplica: hoy se profundiza encima", "Bloque 1")
    d.codigo(p, "rag/<b>schemas.py</b> · <code>SourceReference</code> (l. 345) · <code>TaskItem</code> (l. 369) · "
                "rag/<b>validation.py</b> · <code>verify_citations</code> (l. 38) · "
                "scripts/<b>demo_verify_citations_s11.py</b>")
    d.code(p, (24, 66, 360, 196), """class SourceReference(BaseModel):
    chunk_id: str      # el id del <source>
    document_id: str   # el presupuesto histórico
    evidence: str      # el texto citado, literal

class TaskItem(BaseModel):
    name: str
    engineer_days: float | None
    grounded: bool
    sources: list[SourceReference]""", "La cita por línea")
    d.box(p, (372, 66, 696, 196),
          '<div class="t">Tres estados por línea</div><ul>'
          "<li><b>grounded</b>: cita chunks que sí estaban en el contexto.</li>"
          "<li><b>dangling</b>: cita un id que nunca se recuperó.</li>"
          "<li><b>insufficient</b>: <code>grounded=false</code>, sin horas a ojo.</li></ul>",
          kind="mint")
    d.code(p, (24, 206, 696, 330), """=== Citation verification report ===
lines: 4  grounded: 2  dangling: 1  insufficient: 1
Authentication & SCA   OAuth 2.0 backend        grounded      ['101'] -> -
PSD2 & Open Banking    Open banking connectors  grounded      ['102'] -> -
Ledger                 Transaction ledger       dangling      ['999'] -> ['999']
Reporting              Regulatory reporting     insufficient  [] -> -
ACCEPTANCE: PASS""", "demo_verify_citations_s11.py · sin red ni base de datos")


def slide_preflight(d: Deck) -> None:
    p = d.new("Pre-vuelo: cinco comprobaciones antes de tocar nada", "Si las cinco pasan, el directo está listo",
              "Bloque 1")
    d.codigo(p, "<code>GET /health</code> · <code>budget_chunks</code> en psql · "
                "evals/<b>golden_generation_s11.json</b> · scripts/<b>demo_verify_citations_s11.py</b> · "
                "<code>POST /v1/estimate/stages/verify</code> con <code>use_judge=false</code>")
    d.box(p, (24, 66, 696, 250),
          "<table><tr><th>#</th><th>Qué comprueba</th><th>Resultado en local</th></tr>"
          "<tr><td>1</td><td>Servicio IA vivo</td><td><code>{\"status\":\"healthy\"}</code></td></tr>"
          "<tr><td>2</td><td>Corpus de tareas + el caso en conflicto</td><td><b>1.547</b> chunks "
          "<code>historical_task</code> (1.543 + 4 del fixture)</td></tr>"
          "<tr><td>3</td><td>Golden set con <code>ground_truth</code></td><td><b>5</b> consultas</td></tr>"
          "<tr><td>4</td><td><code>verify_citations</code> en verde</td><td><b>ACCEPTANCE: PASS</b></td></tr>"
          "<tr><td>5</td><td>El gate nuevo responde, sin LLM</td><td><code>degraded: 1</code> · «claims 90d but the "
          "cited evidence supports ~15d»</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 260, 696, 330),
          '<div class="t">Sin coste</div>Las cinco filas no llaman a ningún modelo: el gate con '
          "<code>use_judge=false</code> solo hace aritmética sobre las horas citadas. Lo caro empieza en el Bloque 3.",
          kind="mint")


def slide_triaje(d: Deck) -> None:
    p = d.new("Los errores típicos del ejercicio", "Dos familias: citas colgantes y los clásicos de RAGAS", "Bloque 1")
    d.codigo(p, "scripts/<b>score_ragas_s11.py</b> · <code>_install_vertex_shims</code> (l. 43) · "
                "venv aislado <code>estimator/.ragas-venv</code> (ragas 0.4.4) · rag/<b>validation.py</b> (l. 38)")
    d.box(p, (24, 66, 696, 330),
          "<table><tr><th>Síntoma</th><th>Causa</th><th>Arreglo</th></tr>"
          "<tr><td><code>ImportError …vertexai</code></td><td>ragas 0.4 importa Vertex al cargar</td>"
          "<td>venv aislado + el stub de <code>_install_vertex_shims</code></td></tr>"
          "<tr><td>Todas las métricas <code>NaN</code></td><td>la clave del shell pisa la del <code>.env</code></td>"
          "<td>quitar <code>OPENAI_API_KEY</code> del shell o correr en el contenedor</td></tr>"
          "<tr><td><code>KeyError: 'ground_truth'</code></td><td>nombres de otra versión "
          "(<code>answer</code>/<code>response</code>, <code>contexts</code>/<code>retrieved_contexts</code>)</td>"
          "<td>el shape <code>question / answer / contexts / ground_truth</code></td></tr>"
          "<tr><td><code>context_recall</code> ≈ 0</td><td><code>ground_truth</code> en días, corpus en horas</td>"
          "<td>no es un bug: es el primer hallazgo del baseline</td></tr>"
          "<tr><td>Cita colgante no detectada</td><td>se comparó contra los chunks equivocados</td>"
          "<td><code>{str(c.id) for c in kept}</code>: los que de verdad se ensamblaron</td></tr></table>",
          kind="beige", role="table")


# ===========================================================================
# Bloque 2 · el marcador
# ===========================================================================

def slide_metricas(d: Deck) -> None:
    p = d.new("Cuatro métricas, dos ejes", "Una métrica alta sola no es calidad: se leen juntas", "Bloque 2")
    d.codigo(p, "evals/<b>golden_generation_s11.json</b> (5 consultas con <code>ground_truth</code> en días) · "
                "scripts/<b>score_ragas_s11.py</b> · juez <code>gpt-4o-mini</code> · embeddings "
                "<code>text-embedding-3-small</code>")
    d.box(p, (24, 66, 352, 96), '<div class="t center">Recuperación · ¿traje lo bueno?</div>', kind="lav", pad=4)
    d.box(p, (368, 66, 696, 96), '<div class="t center">Generación · ¿lo usé bien?</div>', kind="mint", pad=4)
    cards = [
        (24, "context_precision", "¿Lo que traje era relevante?", "lav"),
        (190, "context_recall", "¿Traje <b>todo</b> lo relevante? Necesita <code>ground_truth</code>.", "lav"),
        (368, "faithfulness", "¿Cada afirmación se deduce del contexto?", "mint"),
        (534, "answer_relevancy", "¿Responde a lo que se preguntó?", "mint"),
    ]
    for x, t, s, k in cards:
        d.box(p, (x, 104, x + 160, 210), f'<div class="t">{t}</div>{s}', kind=k)
    d.box(p, (24, 220, 696, 330),
          '<div class="t">Cómo se calcula cada una</div><ul>'
          "<li>Un LLM juez trocea la respuesta en afirmaciones y comprueba cada una contra los chunks "
          "(<b>faithfulness</b>) o contra el <code>ground_truth</code> (<b>recall</b>).</li>"
          "<li><b>answer_relevancy</b> genera preguntas desde la respuesta y mide su parecido con la pregunta real.</li>"
          "<li>Solo <b>faithfulness</b> y <b>answer_relevancy</b> funcionan sin <code>ground_truth</code>: "
          "importa en el Bloque 5.</li></ul>",
          kind="beige")


def slide_baseline(d: Deck) -> None:
    p = d.new("Vuestro baseline ya dice dónde mirar", "5 consultas del golden set × 4 métricas", "Bloque 2")
    d.codigo(p, "evals/<b>RAGAS_BASELINE_S11.md</b> (tabla y nota de hallazgos) · evals/<b>ragas_baseline_s11.json</b> "
                "(datos completos, con el <code>citation_report</code> de cada consulta)")
    d.box(p, (24, 66, 372, 250),
          "<table><tr><th></th><th>faithful.</th><th>relev.</th><th>precision</th><th>recall</th></tr>"
          "<tr><td>Q1 banca</td><td>0,42</td><td>0,00</td><td>1,00</td><td>0,00</td></tr>"
          "<tr><td>Q2 e-commerce</td><td>0,43</td><td>0,06</td><td>1,00</td><td>0,00</td></tr>"
          "<tr><td>Q3 telemedicina</td><td>0,56</td><td>0,00</td><td>1,00</td><td>0,57</td></tr>"
          "<tr><td>Q4 IoT</td><td>0,88</td><td>0,00</td><td>1,00</td><td>0,00</td></tr>"
          "<tr><td>Q5 pagos</td><td>0,48</td><td>0,10</td><td>1,00</td><td>0,00</td></tr>"
          "<tr><td><b>media</b></td><td><b>0,55</b></td><td><b>0,03</b></td><td><b>1,00</b></td><td><b>0,11</b></td></tr>"
          "</table>",
          kind="beige", role="table")
    d.box(p, (384, 66, 696, 250),
          '<div class="t">Lectura</div><ul>'
          "<li><b>precision 1,00 y recall 0,11</b>: trae lo relevante, pero el juez no casa días con horas.</li>"
          "<li><b>faithfulness 0,55</b> con 0 citas colgantes: la cita existe, la cifra no siempre se deduce.</li>"
          "<li><b>relevancy 0,03</b>: un brief frente a una tabla. Es la métrica la que está mal planteada.</li></ul>",
          kind="mint")
    d.box(p, (24, 260, 696, 330),
          '<div class="t">La grieta accionable: faithfulness</div>169 líneas, 116 grounded, 53 sin datos y '
          "<b>0 colgantes</b>. La integridad referencial está resuelta; lo que falla es la cifra. "
          "Y una anomalía gratis: en 4 de 5 consultas el modelo copia <b>horas</b> como <b>días</b>.",
          kind="note")


# ===========================================================================
# Bloque 3 · alucinaciones
# ===========================================================================

def slide_cita_miente(d: Deck) -> None:
    p = d.new("Una cita real puede mentir", "Integridad referencial no es lo mismo que entailment", "Bloque 3")
    d.codigo(p, "rag/<b>validation.py</b> · <code>verify_citations</code> (l. 38): ¿el id existe? · "
                "rag/quality/<b>hallucination.py</b> · <code>gate_estimate</code> (l. 217): ¿la cifra se deduce?")
    d.code(p, (24, 66, 400, 200), """<source id="1">
AUTH-001 :: OAuth backend — 120 h
</source>

línea: OAuth login · 90 engineer-days
sources: [{chunk_id: "1",
           evidence: "120 h"}]""", "El contexto y la línea generada")
    d.box(p, (412, 66, 696, 200),
          '<div class="t">verify_citations dice: grounded</div>El chunk 1 estaba en el contexto: la cita es '
          "<b>real</b>. Pero 120 h son unos <b>15 días</b> y la línea reclama <b>90</b>. "
          "Es una alucinación con el disfraz de una cita.",
          kind="peach")
    d.box(p, (24, 210, 352, 330),
          '<div class="t">Capa referencial (el ejercicio)</div>¿El <code>chunk_id</code> citado se recuperó? '
          "Comparar ids: barato, determinista y necesario. Pero no mira el número.",
          kind="beige")
    d.box(p, (368, 210, 696, 330),
          '<div class="t">Capa semántica (hoy)</div>¿La <b>cifra</b> se sostiene con la evidencia? '
          "Tres pasos: ancla numérica sin LLM → juez estricto → <code>gate_line</code> combina los dos.",
          kind="mint")


def slide_tres_desenlaces(d: Deck) -> None:
    p = d.new("Tres desenlaces, no dos", "gate_line: una función pura que se puede enseñar entera", "Bloque 3")
    d.codigo(p, "rag/quality/<b>hallucination.py</b> · <code>numeric_anchor</code> (l. 71) · <code>gate_line</code> "
                "(l. 89) · el exceso, l. 112 · <code>HALLUCINATION_NUMERIC_TOLERANCE=0.5</code>")
    d.code(p, (24, 66, 420, 250), """def gate_line(task, module, anchor_days, verdict,
              *, tolerance):
    if not task.grounded:
        return LineGate(status="insufficient")
    if anchor_days and task.engineer_days is not None:
        overage = (task.engineer_days - anchor_days) \\
                  / anchor_days
        numeric_fail = overage > tolerance
    judge_fail = verdict is not None \\
                 and not verdict.entailed
    if numeric_fail or judge_fail:
        return LineGate(status="degraded", reason=...)
    return LineGate(status="grounded")""", "hallucination.py")
    outs = [("grounded", "La cifra cabe en lo que cita.", "mint"),
            ("degraded", "Reclama más de lo que la fuente sostiene, o el juez lo rechaza.", "peach"),
            ("insufficient", "No hay fuente: se abstiene, no inventa.", "note")]
    for i, (t, s, k) in enumerate(outs):
        y = 66 + i * 62
        d.box(p, (432, y, 696, y + 56), f'<div class="t">{t}</div>{s}', kind=k)
    d.box(p, (24, 260, 696, 330),
          '<div class="t">Regla asimétrica</div>El ancla suma las horas de los chunks citados y las pasa a días (÷ 8). '
          "Una línea puede estimar <b>menos</b> que su fuente (es una porción de un componente histórico); "
          "solo el <b>exceso</b> por encima del 50 % es señal de alucinación.",
          kind="lav")


def slide_demo_gate(d: Deck) -> None:
    p = d.new("Demo: el gate con y sin juez", "Cuatro líneas que citan el mismo chunk de 120 h (≈15 días)", "Bloque 3")
    d.codigo(p, "<b>Interfaz:</b> Calidad → Gate de alucinaciones (casilla «Con juez» y tipo de evidencia) · "
                "<code>POST /v1/estimate/stages/verify</code> · routers/<b>estimate_stages.py</b> (l. 230)")
    d.image(p, (24, 64, 400, 330), "s11-ui-gate.png")
    d.box(p, (412, 64, 696, 216),
          "<table><tr><th>Línea</th><th>Ancla</th><th>+ juez</th></tr>"
          "<tr><td>90 d (+500 %)</td><td class='r'>degraded</td><td class='r'>degraded</td></tr>"
          "<tr><td>10 d (−33 %)</td><td class='k'>grounded</td><td class='k'>grounded</td></tr>"
          "<tr><td>20 d (+33 %)</td><td class='k'>grounded</td><td class='r'>degraded</td></tr>"
          "<tr><td>sin fuente</td><td>insufficient</td><td>insufficient</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (412, 224, 696, 330),
          '<div class="t">Dos lecturas</div><ul><li>El ancla tolera +50 %; el juez <b>no tiene tolerancia</b>, y '
          "basta con que uno falle.</li><li>Con evidencia «120 h» a secas, el juez rechaza también la de 10 días: "
          "la cita no dice <b>de qué</b> trabajo es.</li></ul>",
          kind="note")


def slide_juez(d: Deck) -> None:
    p = d.new("El juez y dónde se engancha el gate", "Una sola llamada barata, y un fallo que no tumba nada",
              "Bloque 3")
    d.codigo(p, "rag/quality/<b>hallucination.py</b> · <code>_judge_system_prompt</code> (l. 140) · "
                "<code>judge_estimate</code> (l. 174) · rag/<b>estimator.py</b> · paso 6.5 (l. 316)")
    d.box(p, (24, 66, 352, 196),
          '<div class="t">judge_estimate</div><ul><li><b>Una</b> llamada para todas las líneas grounded, no una por '
          "línea.</li><li><code>gpt-5-mini</code> vía <code>LLMWrapper</code> (Instructor): salida Pydantic.</li>"
          "<li>«Default to false when in doubt»: estricto a propósito.</li></ul>",
          kind="lav")
    d.box(p, (368, 66, 696, 196),
          '<div class="t">Si el juez falla</div>Devuelve un mapa vacío y el gate sigue <b>solo con el ancla</b>. '
          "Un juez caído no puede tumbar la estimación: el determinista es el suelo.",
          kind="mint")
    d.code(p, (24, 206, 696, 330), """# estimator.py · el conductor del RAG
# 4.   truncar al presupuesto de tokens → augment_chunks()   (Bloque 4)
# 5.   generar la estimación con fuentes
# 6.   verify_citations() + un reintento si hay ids colgantes
# 6.5  gate_estimate(): una línea degradada → confidence = "low"
# 7.   coherencia de "insufficient": un intento de reparación y, si no, error""",
           "El pipeline completo, con los pasos de hoy")


# ===========================================================================
# Bloque 4 · augmentation y síntesis
# ===========================================================================

def slide_augmentation(d: Deck) -> None:
    p = d.new("Mejor material de entrada: augmentation", "Comprimir cada fuente y reordenar contra lost-in-the-middle",
              "Bloque 4")
    d.codigo(p, "rag/quality/<b>augmentation.py</b> · <code>extract_key_points</code> (l. 34) · "
                "<code>reorder_edge_loaded</code> (l. 58) · rag/<b>estimator.py</b> paso 4 (l. 268) · "
                "<b>Interfaz:</b> Calidad → Augmentation")
    d.box(p, (24, 66, 352, 170),
          '<div class="t">1 · Comprimir</div>Se queda con las líneas que llevan una <b>cifra</b> o <code>::</code> '
          "(nombre + horas) y tira el resto. Nunca deja un chunk vacío. Sin LLM.",
          kind="mint")
    d.box(p, (368, 66, 696, 170),
          '<div class="t">2 · Reordenar con carga de extremos</div>El mejor al <b>principio</b>, el segundo mejor '
          "al <b>final</b> y los más flojos en medio, donde el modelo atiende menos.",
          kind="lav")
    d.box(p, (24, 180, 352, 330),
          "<table><tr><th>Banca móvil · 8 fuentes</th><th>sin</th><th>con</th></tr>"
          "<tr><td>Tokens del contexto</td><td>1.061</td><td><b>740</b> (−30 %)</td></tr>"
          "<tr><td>Orden</td><td>2·1·3·4·868…</td><td><b>2</b>·3·868…4·<b>1</b></td></tr>"
          "<tr><td>Ids</td><td colspan='2'>los mismos: la verificación de citas no cambia</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (368, 180, 696, 330),
          '<div class="t">La trampa de la compresión</div>«Component: Transaction ledger service» no lleva cifra '
          "y se pierde: queda solo «Estimated hours: 140». El componente de PSD2 se salva porque «PSD2» lleva un "
          "número. Menos tokens, pero una evidencia que ya no dice <b>de qué</b> trabajo es.",
          kind="peach")


def slide_conflicto(d: Deck) -> None:
    p = d.new("Fuentes en conflicto: un rango con razón", "La misma tarea, dos presupuestos históricos incompatibles",
              "Bloque 4")
    d.codigo(p, "rag/quality/<b>synthesis.py</b> · <code>is_contradiction</code> (l. 43) · "
                "<code>_deterministic_range</code> (l. 48) · rag/<b>task_hours.py</b> (l. 172) · "
                "data/<b>task_corpus_contradictions.json</b> · <b>Interfaz:</b> Calidad → Fuentes en conflicto")
    d.box(p, (24, 66, 400, 132),
          '<div class="t">El fixture</div>«Real-time notifications delivery service»: <b>40 h</b> en una tienda '
          "(solo email) y <b>90 h</b> en una fintech regulada (push, email, SMS, colas, recibos).",
          kind="beige")
    d.image(p, (24, 140, 400, 330), "s11-ui-conflict.png")
    d.box(p, (412, 66, 696, 200),
          '<div class="huge" style="color:#a33a1e">⚠ 15–90 h</div><div class="t">fuentes en conflicto</div>'
          "Consenso 39 h · fiabilidad 0,19 · dispersión <b>0,71</b> (umbral 0,35). "
          "«historical sources disagree (15h vs 90h across 5 analogs)».",
          kind="peach")
    d.box(p, (412, 210, 696, 330),
          '<div class="t">Por qué 15 y no 40</div>El rango es el mínimo y el máximo de los vecinos, y la síntesis no '
          "sabe cuáles son el fixture. Promediar 40 y 90 esconde una decisión de <b>alcance</b> que es del humano: "
          "el rango la deja a la vista.",
          kind="mint")


def slide_rango_detalle(d: Deck) -> None:
    p = d.new("El rango depende de cómo se describe la tarea", "Busca por módulo + nombre + descripción",
              "Bloque 4")
    d.codigo(p, "rag/<b>task_hours.py</b> · <code>estimate_one</code> (l. 111) · <code>_consensus</code> (l. 75) · "
                "estimator-web/…/<b>_step_hours.html.erb</b> (l. 68): la celda ámbar del wizard")
    d.box(p, (24, 66, 696, 210),
          "<table><tr><th>Descripción de la tarea</th><th>Vecinos de 90 h / 40 h</th><th>Resultado</th></tr>"
          "<tr><td>«push, email and SMS with retries»</td><td>— / sí</td><td>rango 15–40 h</td></tr>"
          "<tr><td>«Multi-channel delivery (push, email, SMS) with a durable queue…»</td><td>sí / sí</td>"
          "<td><b>rango 15–90 h</b></td></tr>"
          "<tr><td>sin descripción</td><td>— / sí</td><td>sin rango (dispersión 0,20)</td></tr>"
          "<tr><td>la misma, con top_k 10 o 15</td><td>— / sí</td><td>sin rango: más vecinos parecidos diluyen</td></tr>"
          "</table>",
          kind="beige", role="table")
    d.box(p, (24, 220, 352, 330),
          '<div class="t">Lectura</div>Subir el número de vecinos <b>no</b> ayuda: con un corpus de 1.500 tareas, '
          "los vecinos extra son tareas parecidas de 15-27 h que bajan la dispersión.",
          kind="note")
    d.box(p, (368, 220, 696, 330),
          '<div class="t">En el producto</div>En el wizard, la tarea en conflicto sale en ámbar con '
          "«⚠ 15–90 h · fuentes en conflicto»; el consenso sigue ahí para que el humano lo edite.",
          kind="mint")


# ===========================================================================
# Bloque 5 · evaluación
# ===========================================================================

def slide_dos_modos(d: Deck) -> None:
    p = d.new("Dos modos de evaluación", "En producción no hay ground_truth", "Bloque 5")
    d.codigo(p, "scripts/<b>eval_generation_s11.py</b> · <code>run_gate</code> (l. 243) · "
                "<code>run_monitor</code> (l. 272) · <code>BASELINE</code> (l. 72) · "
                "<code>REGRESSION_TOLERANCE</code> (l. 78)")
    d.box(p, (24, 66, 352, 160),
          '<div class="t">Puerta de regresión (offline)</div><ul>'
          "<li>Golden set <b>con</b> <code>ground_truth</code>: las 4 métricas + citas contra el baseline.</li>"
          "<li>Si una cae más de <b>0,05</b> o hay una cita colgante → <b>BLOCK</b>, <code>exit 1</code>. "
          "Antes de desplegar, en CI.</li></ul>",
          kind="lav")
    d.box(p, (368, 66, 696, 160),
          '<div class="t">Monitor de producción (sin referencia)</div><ul>'
          "<li>Tráfico real: no hay respuesta correcta. Solo <b>faithfulness</b> y <b>answer_relevancy</b>.</li>"
          "<li>Una lectura de salud sobre una muestra, sin puerta. Después de desplegar.</li></ul>",
          kind="mint")
    d.box(p, (24, 170, 696, 330),
          "<table><tr><th>Métrica</th><th>Baseline</th><th>Suelo</th><th>config full · 2 consultas</th>"
          "<th>Puerta</th><th>Monitor</th></tr>"
          "<tr><td>faithfulness</td><td>0,552</td><td>0,502</td><td><b>0,551</b></td><td class='k'>PASS</td>"
          "<td>0,535</td></tr>"
          "<tr><td>answer_relevancy</td><td>0,033</td><td>−0,017</td><td><b>0,039</b></td><td class='k'>PASS</td>"
          "<td>0,039</td></tr>"
          "<tr><td>context_precision</td><td>1,000</td><td>0,950</td><td><b>1,000</b></td><td class='k'>PASS</td>"
          "<td>—</td></tr>"
          "<tr><td>context_recall</td><td>0,114</td><td>0,064</td><td><b>0,312</b></td><td class='k'>PASS</td>"
          "<td>—</td></tr>"
          "<tr><td>citas colgantes</td><td>0</td><td>0</td><td><b>0</b></td><td class='k'>PASS</td><td>0</td></tr>"
          "<tr><td colspan='6'><b>GATE: DEPLOY · exit 0</b> · el gate marcó 28 líneas degradadas · "
          "2 de las 5 consultas del golden set: orientativo, no comparable 1:1 con el baseline</td></tr></table>",
          kind="beige", role="table")


def slide_tablero(d: Deck) -> None:
    p = d.new("Cada técnica es una config, no una rama de código", "medir → cambiar un interruptor → medir",
              "Bloque 5")
    d.codigo(p, "scripts/<b>eval_generation_s11.py</b> · <code>CONFIGS</code> (l. 95) · <code>_apply_config</code> "
                "(l. 103) · <b>Interfaz:</b> Calidad → Interruptores (<code>PUT /api/v1/config/retrieval</code>)")
    d.box(p, (24, 66, 400, 196),
          "<table><tr><th>config</th><th>gate</th><th>augment</th><th>síntesis</th></tr>"
          "<tr><td>baseline</td><td>—</td><td>—</td><td>—</td></tr>"
          "<tr><td>gate</td><td>✓</td><td>—</td><td>—</td></tr>"
          "<tr><td>augment</td><td>✓</td><td>✓</td><td>—</td></tr>"
          "<tr><td>full</td><td>✓</td><td>✓</td><td>✓</td></tr></table>",
          kind="beige", role="table")
    d.code(p, (412, 66, 696, 196), """--gate --config full --limit 2
  ; echo "exit=$?"
exit=0 → DEPLOY
exit=1 → BLOCK

--monitor --config full --limit 2
--compare   (4 configs × 5)""", "Los tres modos del script")
    d.box(p, (24, 206, 352, 330),
          '<div class="t">El cambio en vivo</div>Apagar un interruptor en Calidad → Interruptores (Redis, sin '
          "reiniciar) → volver a pasar la puerta → desplegar o bloquear según el delta.",
          kind="mint")
    d.box(p, (368, 206, 696, 330),
          '<div class="t">Cuidado</div><code>_apply_config</code> cambia los ajustes <b>del proceso</b>. Si hay un '
          "interruptor cambiado en Redis, manda Redis: devolvedlos a «Por defecto» antes de comparar configs.",
          kind="note")


def slide_goodhart(d: Deck) -> None:
    p = d.new("Goodhart: una métrica optimizada sola deja de medir", "Por eso la puerta lee las cuatro juntas",
              "Bloque 5")
    d.codigo(p, "scripts/<b>eval_generation_s11.py</b> · docstring del módulo («Goodhart's law») · "
                "<code>run_gate</code> (l. 243): falla si <b>cualquiera</b> de las cuatro cae")
    trampas = [("faithfulness", "Premia copiar el contexto literal: una respuesta que no estima nada es "
                                "perfectamente fiel.", "peach"),
               ("answer_relevancy", "Premia repetir la pregunta. Con un brief y una tabla da ~0 aunque la "
                                    "estimación sea buena.", "peach"),
               ("context_precision", "Premia traer poco: un solo chunk perfecto da 1,0.", "peach"),
               ("context_recall", "Premia traerlo todo, y entonces el contexto se llena de ruido.", "peach")]
    for i, (t, s, k) in enumerate(trampas):
        col, row = i % 2, i // 2
        x, y = 24 + col * 340, 66 + row * 92
        d.box(p, (x, y, x + 332, y + 84), f'<div class="t">{t}</div>{s}', kind=k)
    d.box(p, (24, 252, 696, 330),
          '<div class="t">Las métricas guían, no gobiernan</div>Dos de recuperación y dos de generación, leídas '
          "juntas, más las citas colgantes como fallo directo. Ninguna cifra sola puede dar luz verde.",
          kind="mint")


# ===========================================================================
# Bloque 6 · ampliar e indexar el corpus
# ===========================================================================

def slide_ampliar(d: Deck) -> None:
    p = d.new("Ampliar el corpus: añadir e indexar", "Información nueva sí; re-embeder lo que ya existe, hoy no",
              "Bloque 6")
    d.codigo(p, "rag/<b>index_service.py</b> · <code>expand</code> (l. 57) · routers/<b>corpus_index.py</b> · "
                "<code>create_index_run</code> (l. 103) · <code>get_index_job</code> (l. 134) · "
                "<code>get_corpus_stats</code> (l. 153)")
    pasos = [("Trocear", "chunker estructural de la S7"), ("Embeder", "el MISMO modelo del corpus"),
             ("Persistir", "budget_chunks"), ("Indexar", "HNSW, solo al insertar")]
    for i, (t, s) in enumerate(pasos):
        x = 24 + i * 170
        d.box(p, (x, 66, x + 156, 124), f'<div class="t center">{t}</div><div class="center s">{s}</div>',
              kind="mint" if i < 3 else "lav")
        if i < 3:
            d.arrow(p, x + 157, 95, x + 169, 95)
    d.code(p, (24, 134, 400, 330), """POST /embeddings/index/runs
→ 202 {"job_id": "41a8…", "status": "pending"}

GET /embeddings/index/jobs/41a8…
→ {"status": "running", "documents_processed": 0}
→ {"status": "completed", "documents_processed": 1}

GET /embeddings/index/stats
→ budget: 79 → 80 documentos""", "Asíncrono: 202 + job_id y se pregunta")
    d.box(p, (412, 134, 696, 230),
          '<div class="t">Por qué asíncrono</div>Un lote grande tarda. La petición no se bloquea: devuelve un '
          "<code>job_id</code> y la web sondea el estado con una barra de progreso.",
          kind="lav")
    d.box(p, (412, 238, 696, 330),
          '<div class="t">Duplicados</div>El mismo documento otra vez se <b>salta</b>: el job acaba '
          "<code>completed</code> con 0 procesados, sin romper el lote.",
          kind="note")


def slide_hnsw(d: Deck) -> None:
    p = d.new("El índice tiene que casar con la consulta", "Migración 0005: HNSW sobre la expresión halfvec",
              "Bloque 6")
    d.codigo(p, "alembic/versions/<b>0005_session11_hnsw_multi_index.py</b> · <code>upgrade</code> (l. 57) · "
                "<code>halfvec_cosine_ops</code> · rag/store/<b>repository.py</b> · <code>corpus_stats</code> (l. 43)")
    d.code(p, (24, 66, 696, 130), """CREATE INDEX ix_budget_chunks_embedding_hnsw ON budget_chunks
  USING hnsw ((embedding::halfvec(1536)) halfvec_cosine_ops) WITH (m = 16, ef_construction = 128)""",
           "La misma expresión que usa la búsqueda")
    d.box(p, (24, 140, 696, 250),
          "<table><tr><th>EXPLAIN sobre 1.607 chunks</th><th>Plan</th></tr>"
          "<tr><td>búsqueda <code>::halfvec</code>, normal</td><td><b>Seq Scan</b>: con 1.600 filas al planificador "
          "le sale más barato recorrer la tabla (12 ms)</td></tr>"
          "<tr><td>la misma, con <code>enable_seqscan = off</code></td><td><b>Index Scan using "
          "ix_budget_chunks_embedding_hnsw</b> (1,3 ms)</td></tr>"
          "<tr><td>búsqueda con <code>vector</code> a secas, forzada</td><td>Seq Scan: el índice <b>no le sirve</b>, "
          "el operador no casa</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (24, 260, 352, 330),
          '<div class="t">Incremental</div>Creado una vez, cada chunk nuevo se indexa al insertarse. Solo se '
          "reconstruye si cambia el modelo o la dimensión.",
          kind="mint")
    d.box(p, (368, 260, 696, 330),
          '<div class="t">En silencio</div>Si la opclass no casa con el operador, Postgres no avisa: ignora el '
          "índice. Siempre <code>EXPLAIN</code>.",
          kind="peach")


def slide_demo_corpus(d: Deck) -> None:
    p = d.new("Demo: el corpus crece y lo nuevo se recupera", "Un proyecto que el corpus no tenía: onboarding KYC",
              "Bloque 6")
    d.codigo(p, "<b>Interfaz:</b> Corpus → Añadir información (el ejemplo KYC viene relleno) · "
                "estimator-web/…/<b>index_runs_controller.rb</b> · <code>create</code> (l. 23) · <code>status</code> (l. 63)")
    d.image(p, (24, 64, 380, 330), "s11-ui-corpus.png")
    d.box(p, (392, 64, 696, 196),
          "<table><tr><th></th><th>antes</th><th>después</th></tr>"
          "<tr><td>Chunks <code>budget</code></td><td>1.607</td><td><b>1.610</b></td></tr>"
          "<tr><td>Mejor resultado para «biometric KYC onboarding…»</td><td>tarea genérica de finanzas, 0,465</td>"
          "<td><b>el proyecto nuevo, 0,167</b></td></tr>"
          "<tr><td>Tiempo del job</td><td colspan='2'>0,3 s para 1 documento y 3 chunks</td></tr></table>",
          kind="beige", role="table")
    d.box(p, (392, 204, 696, 330),
          '<div class="t">Qué demuestra</div>Antes no había nada parecido; después, los tres chunks nuevos ocupan '
          "el top 3. Mismo modelo de embeddings, así que los vectores nuevos y los viejos son comparables.",
          kind="mint")


# ===========================================================================
# Cierre
# ===========================================================================

def slide_cierre(d: Deck) -> None:
    p = d.new("Lo que cierras hoy", "Citada, verificable, fundamentada y medible", "Cierre")
    d.box(p, (24, 66, 352, 236),
          '<div class="t">Tres tensiones</div><ul>'
          "<li><b>Determinismo y juicio</b>: el ancla y el rango son el suelo; el juez y la razón, el matiz.</li>"
          "<li><b>Abstenerse o responder</b>: <code>insufficient</code> y el rango son respuestas de primera.</li>"
          "<li><b>Métrica y calidad</b>: las cuatro, juntas.</li></ul>",
          kind="mint")
    d.box(p, (368, 66, 696, 236),
          '<div class="t">Para pensar</div><ul>'
          "<li>¿Qué tolerancia pondríais al ancla en vuestro dominio, y al juez?</li>"
          "<li>¿Qué evidencia tiene que copiar una línea para que un juez pueda validarla?</li>"
          "<li>¿Qué métrica vigilaríais en producción sin <code>ground_truth</code>?</li></ul>",
          kind="lav")
    d.box(p, (24, 246, 696, 330),
          '<div class="t">Sesión 12 · Introducción a agentes</div>El modelo pasa a decidir el flujo. Al multiplicar '
          "los pasos, medir se vuelve más necesario: cada subtarea necesitará su ancla, su gate y su métrica.",
          kind="beige")


# ===========================================================================

def build() -> None:
    d = Deck()
    cover(d)
    slide_hoy(d)
    slide_ejercicio(d)
    slide_preflight(d)
    slide_triaje(d)
    slide_metricas(d)
    slide_baseline(d)
    slide_cita_miente(d)
    slide_tres_desenlaces(d)
    slide_demo_gate(d)
    slide_juez(d)
    slide_augmentation(d)
    slide_conflicto(d)
    slide_rango_detalle(d)
    slide_dos_modos(d)
    slide_tablero(d)
    slide_goodhart(d)
    slide_ampliar(d)
    slide_hnsw(d)
    slide_demo_corpus(d)
    slide_cierre(d)
    d.template(10)  # ROTI
    d.template(11)  # gracias
    d.save()


if __name__ == "__main__":
    build()
