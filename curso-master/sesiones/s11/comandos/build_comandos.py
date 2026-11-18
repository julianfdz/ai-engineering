"""Genera comandos-y-salidas-s11.html (y el PDF con Edge sin ventana).

Cada comando de la línea de formación de la S11 con la salida real que dio en local:
- «hoy»: relanzado el 18/11 antes de clase (sin llamadas a OpenAI);
- «ensayo»: salida guardada de los ensayos del 17/11 y el 18/11 (comandos que llaman a OpenAI).

Uso:  python build_comandos.py   (desde esta carpeta)
"""

import html
import pathlib
import subprocess

AQUI = pathlib.Path(__file__).parent
SAL = AQUI / "salidas"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def leer(nombre: str) -> str:
    return (SAL / nombre).read_text(encoding="utf-8-sig").strip("\n").rstrip()


# (diapo, título, comando, salida, origen, qué comentar)
PASOS = []


def paso(diapo, titulo, comando, salida, origen, nota=""):
    PASOS.append((diapo, titulo, comando.strip(), salida, origen, nota))


SECCIONES = []


def seccion(nombre):
    SECCIONES.append((len(PASOS), nombre))


# ── Antes de empezar ────────────────────────────────────────────────────────
seccion("Antes de empezar (10 min antes)")
paso("—", "Ir a la carpeta de la S11",
     r'cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s11"',
     None, "", "Sin salida. Todos los comandos siguientes se lanzan desde aquí.")
paso("—", "Levantar el stack", "docker compose -p aieng-s11live up -d", None, "",
     "Si ya está levantado no recrea nada. Comprueba con el siguiente.")
paso("—", "Los cinco contenedores, sanos", "docker compose -p aieng-s11live ps", leer("01_ps.txt"), "hoy",
     "Los cinco s11-* tienen que salir «healthy». (Salida resumida a nombre y estado.)")
paso("—", "Helpers (pegar una vez)", r'''$B = "http://localhost:8000"; $E = @{ "X-API-Key" = "demo-estimate-key" }; $R = @{ "X-API-Key" = "demo-retrieval-key" }
function api($metodo, $ruta, $cuerpo = $null, $cab = @{}) { $p = @{ Method = $metodo; Uri = "$B$ruta"; Headers = $cab; ContentType = "application/json; charset=utf-8" }; if ($cuerpo) { $p.Body = [Text.Encoding]::UTF8.GetBytes(($cuerpo | ConvertTo-Json -Depth 10)) }; Invoke-RestMethod @p }
function linea($nombre, $dias) { @{ name = $nombre; engineer_days = $dias; grounded = $true; sources = @(@{ chunk_id = "1"; document_id = "BUD-1"; evidence = "AUTH-001 :: OAuth backend — 120 h" }) } }
function gate($lineas, $juez = $false) { api POST "/v1/estimate/stages/verify" @{ use_judge = $juez; kept_chunks = @(@{ id = 1; content = "AUTH-001 :: OAuth backend — 120 h"; chunk_type = "budget_component"; distance = 0.2; estimated_hours = 120 }); estimate = @{ confidence = "high"; reasoning = "demo"; total_engineer_days = 90; modules = @(@{ name = "Auth"; tasks = @($lineas) }) } } $E }
function horas($modulo, $tarea, $desc) { (api POST "/v1/estimate/tasks/hours" @{ modules = @(@{ name = $modulo; tasks = @(@{ name = $tarea; description = $desc }) }) } $E).tasks[0] }
function psql($sql) { docker compose -p aieng-s11live exec estimator-postgres psql -U estimator -d estimator -c $sql }''',
     None, "", "Sin salida. Definen api, linea, gate, horas y psql para el resto de la clase.")

# ── Bloque 1 ────────────────────────────────────────────────────────────────
seccion("Bloque 1 · Pre-vuelo y errores")
paso("3", "Citación verificable, sin red",
     "docker compose -p aieng-s11live exec estimator python scripts/demo_verify_citations_s11.py 2>$null",
     leer("03_demo_verify.txt"), "hoy",
     "Cuatro líneas: dos grounded, el 999 colgante (dangling) y «Regulatory reporting» insufficient. "
     "verify_citations comprueba que el id existe, no que la cifra salga de él.")
paso("4", "Pre-vuelo 1 · el servicio responde", 'api GET "/health"', leer("02_health.txt"), "hoy")
paso("4", "Pre-vuelo 2 · el corpus está",
     'psql "select chunk_type, count(*) from budget_chunks group by 1;"', leer("04_count.txt"), "hoy",
     "1.547 tareas = 1.543 del corpus + las 4 del caso en conflicto. 60 componentes de presupuesto.")
paso("4", "Pre-vuelo 3 · el golden set",
     r"(Get-Content estimator\evals\golden_generation_s11.json -Raw | ConvertFrom-Json).queries.Count",
     leer("05_golden.txt"), "hoy", "Cinco consultas, cada una con su ground_truth en días.")
paso("4", "Pre-vuelo 5 · el gate nuevo, sin LLM",
     '(gate @(linea "OAuth login" 90)).lines | Format-List component, status, reason',
     leer("06_gate1.txt"), "hoy",
     "Cita 120 h (≈15 días) y reclama 90: degradada. La fila 4 es el demo_verify de la diapo 3. "
     "Ninguna de las cinco comprobaciones llama a un modelo.")

# ── Bloque 3 ────────────────────────────────────────────────────────────────
seccion("Bloque 3 · Detección de alucinaciones")
paso("10", "Referencia: las tres líneas solo con el ancla (sin juez)",
     '$r = gate @((linea "OAuth login" 90), (linea "OAuth token refresh" 10), (linea "OAuth session management" 20)); '
     '$r.lines | Format-Table component, status, reason -Wrap',
     leer("07_gate3_sinjuez.txt"), "hoy",
     "Sin el $true final no llama al juez. La de 20 días (+33 %) pasa porque el ancla tolera hasta +50 %.")
paso("10", "El gate con juez (el comando del guion)",
     '$r = gate @((linea "OAuth login" 90), (linea "OAuth token refresh" 10), (linea "OAuth session management" 20)) $true; '
     '$r.lines | Format-Table component, status, reason -Wrap',
     """component                status    reason
---------                ------    ------
OAuth login              degraded  claims 90d but the cited evidence supports ~15d; Cited evidence is
                                   "OAuth backend — 120 h" (120 hours) but the claim is 90 engineer-days
                                   (~720 hours), which far …
OAuth token refresh      grounded
OAuth session management degraded  Cited evidence is "OAuth backend — 120 h" (120 hours) but the claim is
                                   20 engineer-days (~160 hours), which exceeds the recorded 120 h and is
                                   not supported.""",
     "ensayo 17/11 · llama a gpt-5-mini (~7 s)",
     "Con juez, la de 20 días pasa a degraded: el juez no tiene tolerancia y basta con que uno de los dos falle. "
     "Las razones del juez cambian de redacción en cada ejecución; el estado de cada línea sale igual.")
paso("10", "El mismo gate con la evidencia «120 h» (en la web: Calidad → Gate)",
     "(en la web: «Las cuatro a la vez», «Con juez», evidencia «solo la cifra: 120 h»)",
     """OAuth login               degraded      claims 90d but the cited evidence supports ~15d; Cited evidence only
                                        states «120 h» without naming OAuth login …
OAuth token refresh       degraded      Cited evidence does not specify token refresh work; although 120 hours
                                        exceeds the claimed 10 engineer-days (80 hours), the evidence fails to
                                        name the same work
OAuth session management  degraded      Cited evidence only shows «120 h» (15 engineer-days), which both doesn't
                                        explicitly refer to session management and is insufficient …
Regulatory reporting      insufficient""",
     "ensayo 17/11 · llama a gpt-5-mini",
     "0 grounded, 3 degraded, 1 insufficient: el juez degrada también la porción honesta de 10 días porque la "
     "cita no dice de qué trabajo es.")

# ── Bloque 4 ────────────────────────────────────────────────────────────────
seccion("Bloque 4 · Augmentation y síntesis")
paso("13", "Fuentes en conflicto: el rango",
     'horas "Notifications" "Real-time notifications delivery service" "Multi-channel delivery (push, email, SMS) '
     'with a durable queue, per-channel retry and backoff and delivery receipts" | '
     "Format-List estimated_hours, reliability, dispersion, hours_range",
     """estimated_hours : 39
reliability     : 0.191
dispersion      : 0.711
hours_range     : @{low=15; high=90; reason=historical sources disagree (15h vs 90h across 5 analogs);
                  estimate depends on scope not yet pinned down}

vecinos (source_id → horas): 1606 → 90 · 1604 → 40 · 567 → 15 · 691 → 23 · 1345 → 23""",
     "ensayo 17/11 · igual en 3 repeticiones · hace un embedding de la consulta",
     "Consenso 39 h, dispersión 0,71 > 0,35, así que se ofrece rango con razón. Sale 15 y no 40 porque el rango es "
     "el min/max de los vecinos y la síntesis no sabe cuál es el fixture.")
paso("14", "La misma tarea descrita como en el guion de LIDR",
     'horas "Notifications" "Real-time notifications delivery service" "push, email and SMS with retries" | '
     "Format-List estimated_hours, dispersion, hours_range",
     """estimated_hours : 24
dispersion      : 0.37
hours_range     : @{low=15; high=40; reason=historical sources disagree (15h vs 40h across 5 analogs); …}

vecinos (source_id → horas): 1604 → 40 · 567 → 15 · 144 → 17 · 1051 → 24 · 691 → 23""",
     "ensayo 17/11 · hace un embedding de la consulta",
     "Con esta descripción el vecino de 90 h no entra en el top 5: solo está el de 40 h y sale 15–40. "
     "El rango depende de cómo se describa la tarea.")

# ── Bloque 5 ────────────────────────────────────────────────────────────────
seccion("Bloque 5 · Evaluación en dos modos")
paso("16", "Recoger las muestras (lanzar al empezar el Bloque 4, en otra PowerShell)",
     "docker compose -p aieng-s11live exec estimator python scripts/eval_generation_s11.py --gate --config full "
     "--limit 2 --collect-only evals/s11_full.json 2>$null",
     """Collecting 2 samples · config=full (+ Synthesis (full S11))...
  - Q1: Mobile banking application with OAuth2 authentication, PSD2 ...
[info] llm_structured_call_completed  latency_ms=8376   model=gpt-5-mini  (reformulación)
[info] rag_retrieve_done  candidates_evaluated=1607 rerank=True results=5 search_mode=hybrid
[info] llm_structured_call_completed  latency_ms=98615  model=gpt-5       (estimación)
[info] llm_structured_call_completed  latency_ms=18553  model=gpt-5-mini  response_model=_Panel (juez)
  - Q2: Headless e-commerce storefront with a product catalog, shopp...
[info] llm_structured_call_completed  latency_ms=10097  model=gpt-5-mini
[info] rag_retrieve_done  candidates_evaluated=1610 rerank=True results=5 search_mode=hybrid
[info] llm_structured_call_completed  latency_ms=135362 model=gpt-5
[info] llm_structured_call_completed  latency_ms=22875  model=gpt-5-mini  response_model=_Panel

Wrote 2 samples to evals/s11_full.json (score with --score-file).""",
     "ensayo 18/11 · 5,5 min · gpt-5 + gpt-5-mini (log resumido)",
     "Cada consulta: reformular (gpt-5-mini) → recuperar (híbrida + reranker) → estimar (gpt-5, 1,5–2,5 min) → "
     "juez del gate. Que aparezca _Panel confirma que el gate está encendido. No toques los interruptores mientras "
     "corre. Plan B: el fichero ya está commiteado, salta directamente a puntuar.")
paso("16", "Cargar la clave para RAGAS (no la imprime)",
     r"$env:OPENAI_API_KEY = ((Get-Content estimator\.env | Select-String '^OPENAI_API_KEY=').Line -split '=', 2)[1]",
     None, "", "Sin salida. RAGAS corre en el host (venv aparte) y necesita la clave en el entorno.")
paso("15", "Modo puerta (offline, con ground_truth)",
     r'estimator\.ragas-venv\Scripts\python.exe estimator\scripts\eval_generation_s11.py --gate --score-file '
     r'estimator\evals\s11_full.json; "exit=$LASTEXITCODE"',
     """=== Offline regression gate (golden set + ground_truth) ===
metric                 baseline      now    floor  verdict
faithfulness              0.552    0.551    0.502  PASS
answer_relevancy          0.033    0.039   -0.017  PASS
context_precision         1.000    1.000    0.950  PASS
context_recall            0.114    0.312    0.064  PASS
dangling_citations            0        0        0  PASS
(degraded lines flagged by the gate: 28)

GATE: DEPLOY
exit=0""",
     "ensayo 18/11 · 83 s · RAGAS llama a OpenAI",
     "floor = baseline − 0,05. Ninguna métrica cae por debajo y no hay citas colgantes, así que DEPLOY y exit 0 "
     "(un CI lo dejaría pasar). Son 2 de las 5 consultas del baseline: orientativo.")
paso("15", "Modo monitor (producción, sin ground_truth)",
     r"estimator\.ragas-venv\Scripts\python.exe estimator\scripts\eval_generation_s11.py --monitor --score-file "
     r"estimator\evals\s11_full.json",
     """=== Reference-free production monitor (no ground_truth) ===
faithfulness            0.535
answer_relevancy        0.039
dangling_citations          0
degraded_lines             28

(no exit gating — this is a health read on live, unlabelled traffic)""",
     "ensayo 18/11 · 65 s · RAGAS llama a OpenAI",
     "Solo las dos métricas que no necesitan referencia. No bloquea nada: es una lectura de salud del tráfico real.")

# ── Bloque 6 ────────────────────────────────────────────────────────────────
seccion("Bloque 6 · Ampliar e indexar el corpus")
paso("19", "EXPLAIN tal cual: Seq Scan",
     'psql "EXPLAIN ANALYZE SELECT id FROM budget_chunks ORDER BY embedding::halfvec(1536) <=> '
     '(SELECT embedding::halfvec(1536) FROM budget_chunks LIMIT 1) LIMIT 5;"',
     leer("08_explain1.txt"), "hoy",
     "Con 1.607 filas al planificador le sale más barato recorrer la tabla y ordenar (top-N heapsort).")
paso("19", "Forzando: usa el índice HNSW",
     'psql "SET enable_seqscan = off; EXPLAIN ANALYZE SELECT id FROM budget_chunks ORDER BY embedding::halfvec(1536) '
     '<=> (SELECT embedding::halfvec(1536) FROM budget_chunks LIMIT 1) LIMIT 5;"',
     leer("09_explain2.txt"), "hoy",
     "Index Scan using ix_budget_chunks_embedding_hnsw. El índice existe y casa con la consulta porque los dos usan "
     "halfvec(1536). El tiempo total lo infla el JIT de la primera ejecución; el Index Scan en sí tarda ~10 ms.")
paso("19", "Con vector a secas no puede usarlo ni forzado",
     'psql "SET enable_seqscan = off; EXPLAIN SELECT id FROM budget_chunks ORDER BY embedding <=> '
     '(SELECT embedding FROM budget_chunks LIMIT 1) LIMIT 5;"',
     leer("10_explain3.txt"), "hoy",
     "Sigue siendo Seq Scan + Sort (el coste 10000000000 es la penalización de enable_seqscan=off). "
     "La consulta tiene que usar la misma expresión que el índice.")
paso("20", "Búsqueda antes de ampliar",
     '(api POST "/v1/retrieval/search" @{ query_text = "Biometric KYC onboarding with liveness detection and '
     'document OCR for a neobank"; top_k = 3 } $R).chunks | Format-Table id, budget_id, distance',
     """  id budget_id      distance
  -- ---------      --------
1568 TASK-2024-0059    0.465
 855 TASK-2022-0032    0.472
 134 TASK-2024-0003    0.477""",
     "ensayo 17/11 y 18/11 · hace un embedding de la consulta",
     "Lo más parecido son tareas genéricas de una plataforma financiera (~0,47): no hay nada de KYC en el corpus.")
paso("20", "(web) Corpus → Añadir información → «Indexar en el corpus →»", "(en la web)",
     """Estado pending → running → completed   Procesados 1 / 1
Corpus: budget 79 → 80 documentos · 1.607 → 1.610 chunks · Índice HNSW ✓""",
     "ensayo 18/11", "El job responde 202 al momento y la página se actualiza sola. Tres componentes = tres chunks.")
paso("20", "La misma búsqueda después",
     '(api POST "/v1/retrieval/search" @{ query_text = "Biometric KYC onboarding with liveness detection and '
     'document OCR for a neobank"; top_k = 3 } $R).chunks | Format-Table id, budget_id, distance',
     """  id budget_id     distance
  -- ---------     --------
1613 BUD-2025-0100    0.167
1612 BUD-2025-0100    0.188
1614 BUD-2025-0100    0.242""",
     "ensayo 18/11 · hace un embedding de la consulta",
     "Los tres primeros son ya el proyecto nuevo, a ~0,17. Lo indexado se recupera sin reiniciar nada. "
     "Los id pueden ser otros en clase: dependen de la secuencia de la tabla.")
paso("20", "(web) Indexar otra vez el mismo JSON", "(en la web)",
     """Estado completed   Procesados 0 / 1
log del servicio: corpus_expansion_skip_duplicate · documents_indexed=0 documents_skipped=1""",
     "ensayo 18/11", "El duplicado se salta: no se re-embebe ni se paga dos veces.")
paso("20", "Para repetir la demo otro día: borrar lo añadido",
     'psql "DELETE FROM documents WHERE source_path LIKE \'corpus-expansion::%\';"',
     "DELETE 1", "esperado",
     "Un documento; sus chunks se van en cascada y el corpus vuelve a 1.607. Solo después de clase.")


# ── HTML ────────────────────────────────────────────────────────────────────
CSS = """
@page { size: A4; margin: 14mm 13mm 14mm 13mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1d2330; font-size: 10pt; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 2mm; color: #12305e; }
.sub { color: #4a5568; margin-bottom: 5mm; font-size: 9.5pt; line-height: 1.45; }
h2 { font-size: 13pt; color: #fff; background: #12305e; padding: 2mm 3mm; margin: 6mm 0 3mm; border-radius: 1.5mm;
     break-after: avoid; }
.paso { border: 0.3mm solid #cfd6e3; border-radius: 1.5mm; margin: 0 0 3.5mm; padding: 2.5mm 3mm;
        break-inside: avoid; }
.cab { display: flex; justify-content: space-between; align-items: baseline; gap: 3mm; margin-bottom: 1.5mm; }
.tit { font-weight: 600; font-size: 10.5pt; }
.diapo { background: #e7eefb; color: #12305e; font-weight: 700; border-radius: 1mm; padding: 0.3mm 2mm;
         margin-right: 2mm; font-size: 9pt; }
.origen { font-size: 8pt; color: #6b7280; white-space: nowrap; }
.origen.hoy { color: #0f7a3a; }
.lab { font-size: 7.5pt; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; margin: 1.5mm 0 0.6mm; }
pre { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 7.6pt; line-height: 1.32; margin: 0;
      padding: 1.8mm 2.2mm; border-radius: 1mm; white-space: pre-wrap; word-break: break-word; }
pre.cmd { background: #12305e; color: #f3f6fb; }
pre.out { background: #f4f6f9; color: #1d2330; border: 0.25mm solid #e1e6ee; }
.nota { margin-top: 1.6mm; font-size: 9pt; line-height: 1.4; }
.nota b { color: #12305e; }
"""


def render() -> str:
    partes = [f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>S11 · comandos y salidas</title>"
              f"<style>{CSS}</style></head><body>"]
    partes.append("<h1>Sesión 11 · Comandos y su salida</h1>")
    partes.append(
        "<div class='sub'>Cada comando de la línea de formación, en orden de clase, con la salida real que dio en "
        "local. <b style='color:#0f7a3a'>hoy</b> = relanzado el 18/11 antes de clase (no llama a ningún modelo). "
        "<b>ensayo</b> = salida guardada de los ensayos del 17/11 y el 18/11; esos comandos llaman a OpenAI y no se "
        "han repetido. Carpeta: <code>ai-engineering-s11</code>, proyecto <code>-p aieng-s11live</code>.</div>")
    cortes = dict(SECCIONES)
    for i, (diapo, titulo, cmd, salida, origen, nota) in enumerate(PASOS):
        if i in cortes:
            partes.append(f"<h2>{html.escape(cortes[i])}</h2>")
        cls = "origen hoy" if origen == "hoy" else "origen"
        etiqueta = "hoy, 18/11" if origen == "hoy" else origen
        badge = f"<span class='diapo'>Diapo {diapo}</span>" if diapo != "—" else ""
        partes.append("<div class='paso'><div class='cab'>"
                      f"<div class='tit'>{badge}{html.escape(titulo)}</div>"
                      f"<div class='{cls}'>{html.escape(etiqueta)}</div></div>")
        partes.append(f"<div class='lab'>Comando</div><pre class='cmd'>{html.escape(cmd)}</pre>")
        if salida:
            partes.append(f"<div class='lab'>Salida</div><pre class='out'>{html.escape(salida)}</pre>")
        if nota:
            partes.append(f"<div class='nota'><b>Qué comentar:</b> {html.escape(nota)}</div>")
        partes.append("</div>")
    partes.append("</body></html>")
    return "".join(partes)


if __name__ == "__main__":
    h = AQUI / "comandos-y-salidas-s11.html"
    h.write_text(render(), encoding="utf-8")
    pdf = AQUI.parent / "S11-comandos-y-salidas.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", h.as_uri()], check=True, capture_output=True)
    print("ok", pdf, pdf.stat().st_size)
