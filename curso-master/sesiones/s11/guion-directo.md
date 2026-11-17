# session-11-live-guide


# Sesión 11 — RAG avanzado: generación y calidad

> **Módulo 3 · Duración 120 min · Modalidad flipped classroom.Estado de entrada:** los alumnos traen del ejercicio pre-sesión **dos cosas ya
implementadas** (no se reconstruyen en el directo): (1) **citación verificable a
nivel de línea** — esquema `SourceReference{chunk_id, document_id, evidence}`,
atribución por línea en el prompt, y `verify_citations` de integridad referencial
con fallback a `insufficient`; (2) **baseline RAGAS** — golden set de 5 consultas
extendido con `ground_truth`, las cuatro métricas calculadas y una tabla baseline.
Traen al directo esa **tabla RAGAS**, su **informe de citaciones** y una nota con
sus números más llamativos.
**Estado de salida:** encima de la citación, una **capa semántica anti-alucinación**
(anclaje numérico determinista → juez estricto → `gate_line` graduado); una capa de
**augmentation + síntesis** (comprimir/extraer/reordenar con carga de extremos +
síntesis de fuentes contradictorias en un rango con razón); y un **pipeline de
evaluación en dos modos** (puerta de regresión offline + monitor de producción sin
referencia) que cierra el bucle *medir → mejorar → medir*.
Y una pieza operativa: **ampliación e indexación del corpus** (añadir información nueva a la
BBDD vectorial, con índice HNSW incremental) — no re-embeder lo existente, que queda fuera.
**Idioma:** la prosa de esta guía está en español; **todo el código, payloads,
nombres de campo, logs y prompts del LLM están en inglés** (convención del repo).
**Nomenclatura:** *servicio IA* = backend Python (`estimator/`); *backend de
negocio* = Rails (`estimator-web/`). Nunca “backend” a secas.


> ## Nota local (PC de Julián) — leer antes del directo
>
> Todo verificado el 17/11/2026 en el worktree `ai-engineering-s11` (rama `session_11_live_local`), proyecto
> `aieng-s11live`. Los cURL de este guion están pensados para macOS; los comandos de PowerShell probados, con
> helpers que mandan el cuerpo en UTF-8, están en [`guion-julian.md`](guion-julian.md). Todo lo que en el guion es
> `uv run python scripts/…` se lanza dentro del contenedor:
> `docker compose -p aieng-s11live exec estimator python scripts/…`; la puntuación de RAGAS, con
> `estimator\.ragas-venv\Scripts\python.exe`.
>
> Diferencias con lo que dice este guion (detalle en [`contexto-sesion-11.md`](contexto-sesion-11.md), sección 6):
>
> - **Caso 40 h/90 h**: con la descripción de abajo sale el rango **15–40 h** (el vecino de 90 h no entra). Con
>   «Multi-channel delivery (push, email, SMS) with a durable queue, per-channel retry and backoff and delivery
>   receipts» y módulo «Notifications» sale **15–90 h** (consenso 39 h, dispersión 0,71). Subir `top_k` lo empeora.
> - **EXPLAIN del Bloque 6**: sale Seq Scan con 1.607 filas. Con `SET enable_seqscan = off;` delante sale el
>   Index Scan del HNSW (1,3 ms).
> - **Búsqueda final del Bloque 6**: lleva `X-API-Key: demo-retrieval-key`, no `$EST` (401). Y el presupuesto de
>   ejemplo no se recupera después; se usa el proyecto KYC (ya relleno en Corpus → Añadir información).
> - **Tolerancia y umbral** (`HALLUCINATION_NUMERIC_TOLERANCE`, `SYNTHESIS_CONTRADICTION_THRESHOLD`) no se cambian en
>   caliente: solo los tres interruptores.
> - **El juez no tiene tolerancia**: con juez, la línea de +33 % también sale degradada; con evidencia «120 h» a
>   secas, hasta la porción honesta.
> - **Web**: el gate, la augmentation y los interruptores se enseñan en el menú **Calidad** (añadido en local); el
>   paso de generación del wizard es solo estructura y no enseña el gate.

---


## Cómo leer este guion

Cada sub-bloque usa los mismos marcadores que las guías de S09/S10:

| Marcador | Qué es | Dónde |
|---|---|---|
| **■ Fundamento · pizarra** | la idea que se explica de viva voz | pizarra / slide |
| **■ Dónde vive** | archivos exactos (`ruta:línea`) a abrir en pantalla | IDE |
| **■ Demo · terminal** | el comando cURL/psql/script que se ejecuta en directo | terminal |
| **■ UI en Rails (wizard)** | dónde lo ve el usuario en el backend de negocio | navegador |
| **■ Defensa oral / FAQ** | lo que preguntarán y la respuesta corta | — |
| **■ Contingencia** | qué hacer si algo falla en el momento | — |
| **■ Bridge** | la frase puente al siguiente bloque | — |
> **Hilo conductor de la sesión.** La **tabla RAGAS** es el marcador de partida. Cada
técnica nueva se mide contra ese baseline y el alumno ve **moverse** fidelidad,
recall y relevancia. La “mejora iterativa” se materializa como un bucle
**medir → mejorar → medir**, no como una lista de temas.
> **Caso de anclaje recurrente.** `examples/transcripts/02_ambiguous.txt` (tienda
gourmet, alcance difuso) en el pre-vuelo; y el **caso contradictorio 40h/90h** (la
misma tarea “Real-time notifications delivery service” con dos presupuestos
históricos incompatibles) como hilo en los Bloques 3–5.
> **Nota de coherencia con los artículos.** Los artículos enseñaron `client.responses.parse`.
El repo hace **todas** las llamadas LLM con `LLMWrapper.complete_structured`
(Instructor + LiteLLM): misma garantía de salida Pydantic v2, reutilizando reintentos,
fallback y tracking de coste. El generador usa `gpt-5` (razonamiento; el repo lo fija
en `"high"`, config.py:113 — los artículos usaban `medium`); el **juez** y la
**augmentation** van en tier barato (`gpt-5-mini`). Menciónalo una vez y sigue.

---


## Prerrequisitos (montar 10–15 min antes)

```bash
cd /Users/antonioperez/projects/ia/ai-engineering/estimator

# 1. Levantar el stack (aplica migraciones con alembic upgrade head).
docker compose up -d --build

# 2. Corpus base + corpus de tareas (horas por tarea) + el fixture de contradicciones:
uv run python scripts/query_examples.py                                    # budgets (HTTP)
docker compose exec estimator python scripts/build_task_corpus.py --ingest # chunk_type=historical_task
docker compose exec estimator python scripts/build_contradictions_s11.py   # el caso 40h/90h

# 3. (Scoring RAGAS) venv aislado para ragas (evita el import duro de vertexai):
#    ver la nota operativa en evals/RAGAS_BASELINE_S11.md.
```
Variables de entorno relevantes (`.env`) — las de S11 son **conmutables en caliente**
(no requieren recrear el contenedor):

```plain text
RETRIEVAL_API_KEY=demo-retrieval-key       # header X-API-Key del router de recuperación
ESTIMATE_API_KEY=demo-estimate-key         # header X-API-Key del pipeline de estimación
HALLUCINATION_GATE_ENABLED=true            # gate semántico (Bloque 3)
HALLUCINATION_JUDGE_MODEL=gpt-5-mini       # juez estricto (tier barato)
HALLUCINATION_NUMERIC_TOLERANCE=0.5        # ±50% sobre el ancla determinista
AUGMENTATION_ENABLED=true                  # comprimir + reordenar (Bloque 4)
SYNTHESIS_ENABLED=true                     # rango en contradicción (Bloque 4)
SYNTHESIS_CONTRADICTION_THRESHOLD=0.35     # dispersión que dispara el rango
```
Exporta para abreviar los cURL del directo:

```bash
export EST=demo-estimate-key
export B=http://localhost:8000
```
> **Trampa de entorno conocida.** Si tu shell tiene `OPENAI_API_KEY` exportada, **pisa**
la del `.env`. Desactívala (`unset OPENAI_API_KEY`) o corre los scripts dentro del
contenedor (`docker compose exec estimator …`).

---


## Pre-flight checklist (cURL en frío, dentro del Bloque 1)

Si las 5 filas pasan, el directo está listo. Cada línea verifica una pieza.

| # | Qué verifica | Comando | Esperado |
|---|---|---|---|
| 1 | Servicio IA vivo | `curl -s $B/health \/ jq -c` | `{"status":"healthy",...}` |
| 2 | Corpus de tareas + contradicciones ingerido | `docker compose exec estimator-postgres psql -U estimator -d estimator -c "select count(*) from budget_chunks where chunk_type='historical_task';"` | `> 1500` |
| 3 | Golden set carga (5 consultas + ground_truth) | `jq '.queries \/ length' evals/golden_generation_s11.json` | `5` |
| 4 | `verify_citations` en verde (integridad referencial) | `uv run python scripts/demo_verify_citations_s11.py` | `ACCEPTANCE: PASS` |
| 5 | Gate semántico responde (anclaje sin LLM) | ver bloque abajo | `degraded_lines >= 1` |
```bash
# 5 — el gate nuevo de S11, en modo ancla-only (use_judge=false: sin LLM, determinista).
curl -s -X POST $B/v1/estimate/stages/verify -H "X-API-Key:$EST" -H "Content-Type: application/json" \
  -d '{"use_judge": false,
       "kept_chunks": [{"id": 1, "content": "AUTH-001 :: OAuth backend — 120 h", "chunk_type": "budget_component", "distance": 0.2, "estimated_hours": 120}],
       "estimate": {"confidence":"high","reasoning":"r","total_engineer_days":90,
         "modules":[{"name":"Auth","tasks":[{"name":"OAuth login","engineer_days":90,"grounded":true,
           "sources":[{"chunk_id":"1","document_id":"BUD-1","evidence":"120 h"}]}]}]}}' \
  | jq '{total:.total_lines, grounded:.grounded_lines, degraded:.degraded_lines, why:.lines[0].reason}'
# → { "total":1, "grounded":0, "degraded":1, "why":"claims 90d but the cited evidence supports ~15d" }
```
> **Regla innegociable.** **Ampliar** el corpus con información nueva **sí entra** (Bloque 6:
añadir documentos + indexarlos). Lo que **no** entra es **re-embeder el corpus existente** /
versionar embeddings por un cambio de modelo (blue-green) — eso es material de ampliación
asíncrono. Y la citación **ya viene** del ejercicio: aquí se **profundiza** (de integridad
referencial a verificación semántica), no se reexplica.

---


## Bloque 1 — Pre-vuelo + resolución de errores (15 min)


### ■ Fundamento · pizarra

- El directo **arranca desde vuestros números**, no desde cero. Antes de tocar nada:
todos reproducen su **tabla RAGAS** y su `verify_citations` en verde.
- Dos familias de errores del ejercicio: **citaciones colgantes mal gestionadas** (un
`chunk_id` citado que nunca se recuperó) y los **clásicos de RAGAS** (juez/embeddings
mal configurados, forma del dataset, desajuste de nombres por versión de la librería).
`[SLIDE: El marcador manda]`


### ■ Dónde vive · citación + baseline (lo que traen)

- Verificación referencial — `app/generation/rag/validation.py:27` (`verify_citations`):
recorre `modules[].tasks[]` y separa líneas *grounded* / *dangling* / *insufficient*.
- Prueba offline (sin red) de los 3 criterios — `scripts/demo_verify_citations_s11.py`
(planta un `chunk_id=999` colgante y una línea sin datos).
- Recogida + scoring RAGAS — `scripts/eval_ragas_s11.py` (recoge muestras del pipeline
real) + `scripts/score_ragas_s11.py`. **El shim de Vertex** vive en
`scripts/score_ragas_s11.py:32` (`_install_vertex_shims`): `ragas 0.4.x` importa en
carga `langchain_community.chat_models.vertexai`, que el `langchain-community` actual ya
no expone → se registra un stub que nunca se instancia con juez OpenAI.
- La tabla y las notas — `evals/RAGAS_BASELINE_S11.md`.

### ■ Demo · terminal

```bash
# Los 3 criterios de la Parte 1 en verde, sin red ni BBDD:
uv run python scripts/demo_verify_citations_s11.py        # → ACCEPTANCE: PASS

# Recoger muestras del pipeline real (venv del proyecto, stack arriba). Dos pasos:
DATABASE_URL='postgresql+psycopg://estimator:estimator@localhost:5433/estimator' \
  uv run python scripts/eval_ragas_s11.py --collect-only samples.json
# … y puntuar en el venv aislado de ragas:
/ruta/ragas-venv/bin/python scripts/score_ragas_s11.py samples.json --out evals/ragas_baseline_s11.json
```

### ■ Contingencia — triaje de los errores típicos

| Síntoma | Causa | Arreglo |
|---|---|---|
| `ImportError: langchain_community…vertexai` | `ragas 0.4.x` importa Vertex en carga | usar el venv aislado + el shim (`score_ragas_s11.py:32`) |
| Todas las métricas `NaN` / juez cae | `OPENAI_API_KEY` del shell pisa la del `.env` | `unset OPENAI_API_KEY` o correr dentro del contenedor |
| `KeyError: 'ground_truth'` / dataset mal formado | mezcla de nombres (`answer` vs `response`, `contexts` vs `retrieved_contexts`) por versión | alinear al shape de `score_ragas_s11.py` (`question/answer/contexts/ground_truth`) |
| `context_recall` = 0 en casi todo | `ground_truth` en engineer-days vs corpus en horas | es un hallazgo del baseline, no un bug — lo atacamos en el Bloque 2 |
| citación colgante no detectada | se comparó contra los chunks equivocados | `verify_citations(estimate, {str(c.id) for c in kept})` — el set son los chunks **realmente** ensamblados |

### ■ Bridge → Bloque 2

Todos con su tabla en pantalla. Ahora **leámosla como diagnóstico**: las cuatro métricas
juntas dicen dónde está la grieta.


---


## Bloque 2 — El marcador: leer la tabla RAGAS (15 min)

`[SLIDE: Cuatro métricas - dos ejes]`


### ■ Fundamento · pizarra

- Cuatro métricas, **dos ejes**. **Recuperación:** `context_precision` (¿lo que traje era
relevante?) y `context_recall` (¿traje todo lo relevante?). **Generación:** `faithfulness`
(¿cada afirmación se deduce del contexto?) y `answer_relevancy` (¿respondo a lo que se
pregunta?).
- Se leen **juntas**: una sola métrica alta no es calidad. Ese es el anticipo de Goodhart
(Bloque 5).

### ■ Dónde vive · la tabla y el porqué

- `evals/RAGAS_BASELINE_S11.md` — la tabla (5 consultas × 4 métricas + promedio) y la
“nota de hallazgos”.
- `evals/golden_generation_s11.json` — cada consulta lleva `transcript` + `ground_truth`
(estimación de referencia en engineer-days ≈ horas/8).
`[SLIDE: Tu baseline ya te dice donde mirar]`

Lectura diagnóstica del baseline real (promedios):

| métrica | valor | lectura |
|---|---|---|
| `context_precision` | **1.00** | la recuperación trae exactamente lo relevante |
| `context_recall` | **0.11** | pero el juez no atribuye el `ground_truth` al contexto: **days vs horas** |
| `faithfulness` | **0.55** | citación correcta, pero el generador reparte horas en 4–8 subtareas → 1:1 imposible |
| `answer_relevancy` | **0.03** | *artefacto de formato*: pregunta = brief declarativo, respuesta = tabla módulos→tareas |

### ■ Demo · terminal

```bash
# Cada alumno mira SU tabla y nombra su PEOR métrica (será su objetivo del bucle).
sed -n '/Tabla de métricas/,/Nota de hallazgos/p' evals/RAGAS_BASELINE_S11.md
```

### ■ Defensa oral / FAQ

- *“¿**`answer_relevancy`** ≈ 0 significa mala respuesta?”* No: la métrica regenera preguntas
desde la respuesta y las compara con la pregunta; con un brief declarativo y una tabla
estructurada está **mal planteada**. Es medición, no calidad — se ataca reformulando
pregunta/respuesta.
- 

### ■ Bridge → Bloque 3

La primera grieta accionable es `faithfulness`: la citación existe pero la **cifra** no
siempre se deduce de ella. Vamos a cerrarla.


---


## Bloque 3 — Cerrar la grieta: detección de alucinaciones (25 min)

`[SLIDE: Una cita real puede mentir]`


### ■ Fundamento · pizarra

- **Integridad referencial ≠ entailment.** `verify_citations` prueba que el `chunk_id`
citado se recuperó; **no** prueba que la cifra se **deduzca** de él. Una línea puede
citar una fuente real e inventarse las horas: *una alucinación con el disfraz de una cita*.
- Capa semántica graduada, en tres pasos: **ancla numérica determinista** (sin LLM) →
**juez estricto** (¿la `evidence` respalda la cifra?) → `**gate_line**` que combina ambos
en `grounded` / `insufficient` / `degraded`.
- Regla **asimétrica y enseñable**: una línea puede estimar **menos** que su fuente (es una
porción de un componente histórico), pero si reclama **mucho más** de lo que la evidencia
soporta → `degraded`.

### ■ Dónde vive · `app/generation/rag/quality/hallucination.py`

> **Arquitectura.** La lógica de calidad de S11 vive en el subpaquete
`app/generation/rag/quality/` (espejo de `rag/retrieval/` de S10), no suelta en la raíz de
`rag/`. Depende sólo de `foundation` + `domain/schemas` + hermanos de `rag`; compone en el
camino de petición **sólo** a través del conductor (`rag/estimator.py`).
- `numeric_anchor` — `quality/hallucination.py:60`: suma las horas históricas de los chunks
citados (metadata `estimated_hours` o parseadas del texto) y las pasa a engineer-days.
Determinista.
- `gate_line` — `quality/hallucination.py:78`: **función pura** (la unidad enseñable). Degrada
si el *overage* supera la tolerancia **o** si el juez rechaza.
`[SLIDE: Tres desenlaces, no dos]`

- `judge_estimate` — `quality/hallucination.py:163`: **un solo** batched LLM call
(`HALLUCINATION_JUDGE_MODEL`, `gpt-5-mini`), reutiliza `LLMWrapper.complete_structured`.
- `gate_estimate` — `quality/hallucination.py:206`: el conductor; con `use_judge=False` corre
solo el ancla (sin coste).
- Esquemas — `app/generation/rag/schemas.py:445` (`LineGate`) y `:464` (`HallucinationReport`).
- Cableado en el pipeline — `app/generation/rag/estimator.py:305` (**paso 6.5**, tras
`verify_citations` y antes de la coherencia): una línea `degraded` **baja** la confianza.
- Endpoint de enseñanza — `app/api/routers/estimate_stages.py:219` (`POST /v1/estimate/stages/verify`).
- Settings + toggle en caliente — `app/config.py:192` y `app/foundation/llm/runtime_config.py:215`
(`effective_hallucination_gate`); conmutable vía `PUT /api/v1/config/retrieval`.
```python
# quality/hallucination.py:78 — el combinador puro (extracto)
def gate_line(task, module_name, anchor_days, verdict, *, tolerance):
    if not task.grounded:
        return LineGate(module=module_name, component=task.name, status="insufficient")
    numeric_fail = False
    if anchor_days and anchor_days > 0 and task.engineer_days is not None:
        overage = (task.engineer_days - anchor_days) / anchor_days
        numeric_fail = overage > tolerance          # sólo el EXCESO es señal
    judge_fail = verdict is not None and not verdict.entailed
    status = "degraded" if (numeric_fail or judge_fail) else "grounded"
    ...
```

### ■ Demo · terminal — un caso de atribución falsa y uno de abstención

```bash
# (a) ATRIBUCIÓN FALSA: la línea cita 120 h (≈15 días) pero reclama 90 días → degraded.
#     use_judge=false = ancla determinista, sin LLM (rápido, gratis, reproducible).
curl -s -X POST $B/v1/estimate/stages/verify -H "X-API-Key:$EST" -H "Content-Type: application/json" \
  -d @- <<'JSON' | jq '{degraded:.degraded_lines, line:.lines[0]|{status, numeric_deviation, reason}}'
{ "use_judge": false,
  "kept_chunks": [{"id":1,"content":"AUTH-001 :: OAuth backend — 120 h","chunk_type":"budget_component","distance":0.2,"estimated_hours":120}],
  "estimate": {"confidence":"high","reasoning":"r","total_engineer_days":90,
    "modules":[{"name":"Auth","tasks":[{"name":"OAuth login","engineer_days":90,"grounded":true,
      "sources":[{"chunk_id":"1","document_id":"BUD-1","evidence":"120 h"}]}]}]}}
JSON
# → degraded:1, status:"degraded", reason:"claims 90d but the cited evidence supports ~15d"

# (b) ABSTENCIÓN: una línea sin datos suficientes (grounded=false) → insufficient, no inventa.
#     (misma llamada con "grounded":false, "engineer_days":null, "sources":[])
```
Re-ejecutar la **puerta** con el gate activo y ver moverse la fidelidad:

```bash
uv run python scripts/eval_generation_s11.py --gate --config gate --limit 2
```

### ■ UI en Rails (wizard) — pantalla de generación

- `estimator-web/app/models/rag/generation_view.rb:15` — el `GenerationView` ahora parsea
`citation_report` **y** `hallucination_report` (antes sólo `fabricated_source_ids`/`coherent`).
- `estimator-web/app/views/rag/estimation_runs/_step_generation.html.erb:55` (verificación de
citaciones por línea) y `:71` (**gate semántico**: badges grounded/degraded/insufficient +
el motivo por línea degradada), reutilizando el semáforo del wizard.
- POROs nuevos: `app/models/rag/citation_report_view.rb`, `hallucination_report_view.rb`.

### ■ Defensa oral / FAQ

- *“¿Por qué el ancla mira sólo el exceso?”* Porque una tarea es una **porción** de su
componente histórico: estimar menos es legítimo; estimar **más** de lo que la fuente
registra no.
- *“¿Un LLM call por línea?”* No: `judge_estimate` hace **uno** batched para todas las líneas
grounded (`quality/hallucination.py:163`).

### ■ Contingencia

- Gate demasiado agresivo → sube `HALLUCINATION_NUMERIC_TOLERANCE` (Ajustes / `PUT /api/v1/config/retrieval`), o `use_judge=false` para aislar la mitad determinista.

### ■ Bridge → Bloque 4

El gate **detecta** la cifra que no se sostiene. La siguiente palanca es **darle mejor
material de entrada** al generador para que haya menos que degradar.


---


## Bloque 4 — Subir la calidad de entrada: augmentation + síntesis (25 min)

`[SLIDE: Mejor material de entrada]`


### ■ Fundamento · pizarra

- **Augmentation** = mejorar el contexto **antes** de generar, en dos pasadas conmutables:
**comprimir** cada fuente a sus puntos clave (menos ruido, más fuentes por presupuesto de
tokens) y **reordenar con carga de extremos** (lo más relevante al **principio y al final**;
lo débil al medio) contra *lost-in-the-middle*.
- **Síntesis en dos etapas** de las horas por tarea: **ancla determinista** (el consenso
ponderado que ya existe) + **juicio**; cuando las fuentes **contradicen** (una dice 40h,
otra 90h), emitir un **rango con razón** en vez de promediar el conflicto en un `~65h`
engañoso.

### ■ Dónde vive · augmentation · `app/generation/rag/quality/augmentation.py`

- `extract_key_points` — `quality/augmentation.py:23`: extractivo, determinista (líneas con
cifra o id; nunca vacía un chunk).
- `reorder_edge_loaded` — `quality/augmentation.py:47`: el mejor primero, el 2º mejor **último**.
- `augment_chunks` — `quality/augmentation.py:62`: compón las dos pasadas (preserva ids → la verificación de citaciones no se ve afectada). `context_assembler.py` conserva sólo el
ensamblado S9 (`build_context_block`/`truncate_to_token_budget`).
- Cableado en el pipeline — `app/generation/rag/estimator.py:262` (**paso 4**, sobre los
chunks ya truncados) y en `POST /v1/estimate/stages/assemble` (`augment=true`).

### ■ Dónde vive · síntesis · `app/generation/rag/quality/synthesis.py`

- `is_contradiction` — `quality/synthesis.py:32`: dispersión (coef. de variación) > umbral.
- `synthesize_range` — `quality/synthesis.py:61`: rango determinista (min/max de los vecinos + razón con el conflicto nombrado); `use_llm=True` frasea la razón con `gpt-5-mini`, con fallback.
- Esquema — `app/generation/rag/schemas.py:640` (`HourRange`); propagado a `TaskHoursEstimate.hours_range`.
- Cableado — `app/generation/rag/task_hours.py:162` (por tarea, cuando `effective_synthesis()`).

### ■ Demo · terminal — el caso 40h/90h

```bash
# El fixture plantó "Real-time notifications delivery service" con 40h (email-only) y 90h
# (multicanal regulado). La misma tarea, dos verdades históricas incompatibles:
curl -s -X POST $B/v1/estimate/tasks/hours -H "X-API-Key:$EST" -H "Content-Type: application/json" \
  -d '{"modules":[{"name":"Notifications","tasks":[{"name":"Real-time notifications delivery service","description":"push, email and SMS with retries"}]}]}' \
  | jq '.tasks[0] | {consensus:.estimated_hours, dispersion, range:.hours_range}'
# → consensus ~65, dispersion alto, range:{low:40, high:90, reason:"historical sources disagree (40h vs 90h)…"}

# Augmentation visible en el stage de ensamblado (comprime + reordena):
curl -s -X POST $B/v1/estimate/stages/assemble -H "X-API-Key:$EST" -H "Content-Type: application/json" \
  -d '{"augment": true, "chunks": [ … ]}' | jq '{augmented, dropped:.dropped_count, tokens:.token_count}'
```
`[SLIDE: Fuentes en conflicto]`

Re-ejecutar la puerta con augmentation / síntesis y observar el **desplazamiento** y el
diagnóstico recuperación/generación:

```bash
uv run python scripts/eval_generation_s11.py --gate --config augment --limit 2
uv run python scripts/eval_generation_s11.py --gate --config full   --limit 2
```

### ■ UI en Rails (wizard) — pantalla de horas

- `estimator-web/app/views/rag/estimation_runs/_step_hours.html.erb:56` — cuando la tarea está en conflicto, la celda muestra `**⚠ 40–90 h · fuentes en conflicto**` con la razón
(en vez de un punto falso), y un badge de resumen (`:27`).
- `app/models/rag/task_item_view.rb:44` (`contradicted?`) + `app/models/rag/hour_range_view.rb`
(`label` → `"40–90 h"`). El consenso sigue disponible para editar.

### ■ Defensa oral / FAQ

- *“¿Por qué no elegís un número?”* Porque promediar 40 y 90 esconde una decisión de
**alcance** que es del humano. El rango + la razón la hace explícita.
- *“¿La compresión rompe las citas verbatim?”* No: `extract_key_points` conserva las líneas
con la cifra (`— 120 h`), que es justo la `evidence` que la línea cita.

### ■ Contingencia

- El rango no aparece → sube el número de vecinos o baja `SYNTHESIS_CONTRADICTION_THRESHOLD`
(Ajustes); confirma que el fixture está ingerido (`build_contradictions_s11.py`).

### ■ Bridge → Bloque 5

Ya tenemos técnicas que **mueven** el marcador. Falta el **proceso**: cómo decidir, con
datos, si un cambio se despliega o se bloquea.


---


## Bloque 5 — Pipeline de evaluación completo e iteración guiada por métricas (20 min)

`[SLIDE: Dos modos de evaluación]`

> **Ahorro de tiempo (para el Bloque 6).** No corras `--compare` en vivo (son 4 configs × 5
consultas de RAGAS): muestra la **tabla ya calculada** y comenta el desplazamiento. El
`--gate` con `--limit 2` sí en vivo (rápido) para enseñar el exit code.

### ■ Fundamento · pizarra

- **Dos modos**, no uno. **Puerta de regresión offline**: golden set **con **`**ground_truth**`,
las 4 métricas + citaciones, comparadas contra el baseline → **PASS/FAIL + exit code**
(desplegar o bloquear). **Monitor de producción sin referencia**: el tráfico real no tiene
`ground_truth`, así que sólo las dos métricas que no lo necesitan (`faithfulness` +
`answer_relevancy`) sobre una muestra — una lectura de salud, sin puerta.
- **Goodhart**: cualquier métrica optimizada **sola** deja de medir calidad (fidelidad premia
copiar; relevancia, repetir la pregunta). Por eso la puerta lee las cuatro **juntas**.

### ■ Dónde vive · `scripts/eval_generation_s11.py`

- `StageConfig` / `CONFIGS` — `eval_generation_s11.py:74` y `:84`: las técnicas como **datos**
(`baseline` / `gate` / `augment` / `full`), no ramas de código.
- `run_gate` — `eval_generation_s11.py:229`: puerta offline; `**return 1**`** si regresa** (mismo
patrón PASS/FAIL + exit code que `evals/run.py`). Una citación colgante es *hard fail*.
- `run_monitor` — `eval_generation_s11.py:258`: sólo métricas *reference-free*.
- Reutiliza `collect_sample`/`score_samples` de `eval_ragas_s11.py` y el shim de Vertex de
`score_ragas_s11.py:32`.

### ■ Demo · terminal — el bucle en vivo

```bash
# Tablero: una fila por config (medir → mejorar → medir):
uv run python scripts/eval_generation_s11.py --compare --limit 2

# La puerta como decisión de despliegue (mira el exit code):
uv run python scripts/eval_generation_s11.py --gate --config full --limit 2 ; echo "exit=$?"
#   exit=0 → DEPLOY ; exit=1 → BLOCK (regresión o citación colgante)

# El monitor sin referencia (lo que corre sobre tráfico real, sin ground_truth):
uv run python scripts/eval_generation_s11.py --monitor --config full --limit 2
```
Un **cambio concreto** en vivo: flip de un toggle vía Ajustes / `PUT /api/v1/config/retrieval`
(p. ej. `augmentation_enabled`) → correr `--gate` → **desplegar o bloquear** según el delta.


### ■ UI en Rails (wizard) — histórico

- `estimator-web/app/views/rag/estimation_runs/index.html.erb` — un **embudo de calidad**
ligero (confirmadas / con horas / en curso) sobre las últimas ejecuciones. Sin coste de
LLM: sólo lee el estado persistido. Es el “monitor” en su forma más barata.

### ■ Defensa oral / FAQ

- *“¿Por qué dos modos y no uno?”* Porque en producción **no hay** `ground_truth`. La puerta
offline protege contra regresiones antes de desplegar; el monitor vigila lo desplegado con
las únicas métricas que se pueden calcular sin referencia.

### ■ Contingencia

- `-gate` bloquea siempre → revisa el umbral (`REGRESSION_TOLERANCE`) y que el baseline del
script coincide con `evals/RAGAS_BASELINE_S11.md`.

### ■ Bridge → Bloque 6

Tenemos un proceso para medir la calidad. Pero un corpus **no es estático**: llega información
nueva y hay que **añadirla e indexarla**. Cerremos con esa pieza operativa.


---


## Bloque 6 — Ampliación e indexación del corpus (12 min)

`[SLIDE: Amplar el corpus]`


### ■ Fundamento · pizarra

- El corpus **crece**: en algún momento hay que **añadir información nueva** (un presupuesto/proyecto
histórico, un transcript, un doc) a la BBDD vectorial y **indexar sus vectores**. Es la
*reindexación* como **ampliación**, no como re-embeder lo existente (eso es un cambio de modelo /
blue-green, fuera de alcance hoy).
- Dos ideas: (1) **añadir = trocear → embeder → persistir** (con el **mismo** modelo del corpus, así
los vectores son comparables); (2) **indexar = HNSW**, que es **incremental** — una vez creado el
índice, cada insert nuevo se indexa solo. Y el índice **debe casar el operador** de la búsqueda
(aquí `halfvec_cosine_ops`), o Postgres lo ignora en silencio (mismo tema que en S08/S10).
- Se hace **asíncrono** (job + progreso): un lote puede tardar, así que devolvemos `202` + `job_id` y
se **sondea** el estado, en vez de bloquear la petición.

### ■ Dónde vive

- Índice — `alembic/versions/0005_session11_hnsw_multi_index.py`: HNSW `halfvec_cosine_ops` sobre
`budget_chunks` / `transcript_chunks` / `technical_doc_chunks` (las tablas de S10 iban a *seq scan*).
- Servicio — `app/generation/rag/index_service.py:46` (`CorpusIndexService.expand`): bucle sobre
`RagIngestService.ingest` por documento, **saltando duplicados**, con `on_progress`.
- Endpoints (espejo de `app/api/ingestion.py`) — `app/api/routers/corpus_index.py`:
`create_index_run` (:92, `POST /embeddings/index/runs` → `202` + `BackgroundTask` async),
`get_index_job` (:123, `GET …/jobs/{id}`), `get_corpus_stats` (:142, `GET …/index/stats`).
- Conteos + estado del índice — `app/generation/rag/store/repository.py:43` (`corpus_stats`).

### ■ Demo · terminal

```bash
# 0. El índice ya está (migración 0005). Compruébalo — y que la búsqueda lo USA:
docker compose exec estimator-postgres psql -U estimator -d estimator \
  -c "EXPLAIN ANALYZE SELECT id FROM budget_chunks ORDER BY embedding::halfvec(1536) <=> (SELECT embedding::halfvec(1536) FROM budget_chunks LIMIT 1) LIMIT 5;"
# → 'Index Scan using ix_budget_chunks_embedding_hnsw' (NO 'Seq Scan')

# 1. Estado del corpus ANTES:
curl -s $B/embeddings/index/stats | jq '{total:.total_chunks, budget:(.collections[]|select(.collection=="budget"))}'

# 2. Añadir un presupuesto NUEVO (async) → job_id:
JOB=$(curl -s -X POST $B/embeddings/index/runs -H "Content-Type: application/json" \
  -d '{"documents":[{"budget_id":"NEW-2025-9100","client_metadata":{"name":"Nueva Cuenta","sector":"finance","country":"ES"},"project_summary":"new project","main_technology":"Python","year":2025,"total_estimated_hours":200,"components":[{"component_id":"AUTH-001","name":"OAuth2 login","description":"auth","module":"Authentication & Access","tech_stack":["Python"],"estimated_hours":120,"complexity":"medium","dependencies":[]}]}]}' \
  | jq -r .job_id)

# 3. Sondear hasta 'completed':
curl -s $B/embeddings/index/jobs/$JOB | jq '{status, documents_processed}'

# 4. Estado DESPUÉS (creció) + la info nueva ya se RECUPERA:
curl -s $B/embeddings/index/stats | jq '.total_chunks'
curl -s -X POST $B/v1/retrieval/search -H "X-API-Key:$EST" -H "Content-Type: application/json" \
  -d '{"query_text":"OAuth2 login authentication backend","top_k":3}' | jq '.chunks[0].content'
```

### ■ UI en Rails (wizard) — sección “Corpus / Índice”

- `estimator-web/app/controllers/rag/index_runs_controller.rb`: `create` (:23, dispara el job async),
`status` (:63, endpoint JSON que sondea el job y captura el crecimiento).
- Cliente — `app/services/estimator_ai/index_client.rb`: `start_expansion` (:19), `job_status` (:35),
`corpus_stats` (:46).
- Vista + poller — `app/views/rag/index_runs/show.html.erb` + el Stimulus
`index_run_poller_controller.js`: barra de progreso que se auto-refresca y, al terminar, muestra el
corpus **antes/después** (chunks nuevos). Enséñalo pegando el mismo presupuesto nuevo en el
formulario.

### ■ Defensa oral / FAQ

- *“¿Y si añado un documento repetido?”* Se **salta** (guard de `source_path`), no rompe el lote.
- *“¿Hay que reconstruir el índice tras cada insert?”* No: HNSW es **incremental**. Reconstruir sólo
al **crear** el índice (migración) o si cambia el modelo/dimensión (fuera de alcance).

### ■ Contingencia

- La búsqueda no usa el índice → operador/opclass no casa (`vector_cosine_ops` vs `halfvec`): mira el
`EXPLAIN`. El job se queda en `running` → revisa logs del `BackgroundTask` (embeddings sin API key).

### ■ Bridge → Cierre

Estimación **citada, verificable, medible** y un corpus que **crece de forma segura**. Cerremos.


---


## Cierre — reconciliación y puente (8 min)


### ■ Fundamento · pizarra — el arco

- **Citada** (S9: cada cifra con su `<source>`) → **verificable** (S11 pre-work: integridad
referencial por línea) → **fundamentada semánticamente** (S11 directo: el gate separa “la
cita existe” de “la cifra se deduce”) → **medible** (RAGAS + puerta/monitor).
`[SLIDE: El arco de calidad]`


### ■ Reconciliación de tensiones narrativas

- *Determinismo vs. juicio del modelo*: el ancla y el rango son deterministas (baratos,
reproducibles); el juez y la razón añaden matiz — **el determinista es el suelo**, el LLM el
refinamiento.
- *Abstenerse vs. responder*: `insufficient` y el rango son respuestas de **primera clase**;
forzar un número con mala evidencia es el peor fallo.
- *Métrica vs. calidad* (Goodhart): las métricas se leen **juntas** y guían, no gobiernan.

### ■ Entrega

- Rama de referencia `**session-11-reference**` con todo el código del directo (servicio IA +
backend de negocio) y el arnés de evaluación.

### ■ Bridge → módulo siguiente

- El siguiente módulo descompone el problema en **sub-tareas especializadas** (agentes). Al
multiplicar los pasos, **la disciplina de medir se vuelve más necesaria**, no menos: cada
sub-tarea necesita su ancla, su gate y su métrica.

---


## Apéndice ejecutivo (para el mentor)


### Resumen por bloque

| # | Bloque | Min | Demo clave |
|---|---|---|---|
| 1 | Pre-vuelo + errores | 15 | `demo_verify_citations_s11.py` PASS; triaje RAGAS |
| 2 | Leer la tabla RAGAS | 15 | 4 métricas juntas; cada alumno su peor métrica (Fig. 16) |
| 3 | Alucinaciones | 25 | `/stages/verify`: atribución falsa → `degraded`; re-gate (Figs. 10–12) |
| 4 | Augmentation + síntesis | 25 | `/tasks/hours` caso 40h/90h → rango; `--config augment/full` (Figs. 1–6) |
| 5 | Eval en dos modos | 20 | `--compare` (precalc.) / `--gate` (exit code) / `--monitor`; Goodhart (Figs. 16–18) |
| 6 | Ampliación e indexación del corpus | 12 | `POST /embeddings/index/runs` async → `/stats` crece; `EXPLAIN` usa HNSW (Fig. 7) |
| — | Cierre y puente | 8 | rama `session-11-reference` |
Total: 15 + 15 + 25 + 25 + 20 + 12 + 8 = **120 min**.


### Tabla de errores previsibles

| Síntoma | Causa | Arreglo |
|---|---|---|
| `ImportError …vertexai` al puntuar | import duro de `ragas 0.4.x` | venv aislado + shim (`score_ragas_s11.py:32`) |
| Métricas `NaN` | `OPENAI_API_KEY` del shell pisa `.env` | `unset OPENAI_API_KEY` o correr en el contenedor |
| `context_recall` ≈ 0 | `ground_truth` en days vs corpus en horas | hallazgo del baseline; se documenta, no es bug |
| Gate no marca nada | corpus/fixture sin ingerir, o tolerancia alta | `build_contradictions_s11.py`; baja `HALLUCINATION_NUMERIC_TOLERANCE` |
| Rango 40/90 no aparece | fixture sin ingerir o umbral alto | `build_contradictions_s11.py`; baja `SYNTHESIS_CONTRADICTION_THRESHOLD` |
| `--gate` bloquea siempre | umbral/baseline desalineados | revisar `BASELINE`/`REGRESSION_TOLERANCE` en `eval_generation_s11.py` |
| (B6) búsqueda no usa el índice | opclass no casa (`vector_cosine_ops` vs `halfvec`) | `EXPLAIN`; el índice de `0005` es `halfvec_cosine_ops` |
| (B6) job `running` sin avanzar | embeddings sin API key en el `BackgroundTask` | logs del contenedor; `OPENAI_API_KEY` en el `.env` |

### Artefactos nuevos / modificados

| Artefacto | Rol |
|---|---|
| `app/generation/rag/quality/` | **nuevo subpaquete** · agrupa la calidad de generación de S11 (espejo de `rag/retrieval/`) |
| `app/generation/rag/quality/hallucination.py` | **nuevo** · ancla + juez + `gate_line`/`gate_estimate` |
| `app/generation/rag/quality/synthesis.py` | **nuevo** · rango en contradicción (dos etapas) |
| `app/generation/rag/quality/augmentation.py` | **nuevo** · `extract_key_points`/`reorder_edge_loaded`/`augment_chunks` (`context_assembler.py` vuelve a su forma S9) |
| `app/generation/rag/estimator.py` | paso 4 (augment) + paso 6.5 (gate) en el conductor |
| `app/generation/rag/task_hours.py` | síntesis por tarea (`hours_range`) |
| `app/api/routers/estimate_stages.py` | `POST /v1/estimate/stages/verify` |
| `app/generation/rag/schemas.py` | `LineGate`/`HallucinationReport`/`HourRange`/`VerifyRequest` |
| `data/task_corpus_contradictions.json` + `scripts/build_contradictions_s11.py` | **nuevo** · el caso 40h/90h |
| `scripts/eval_generation_s11.py` | **nuevo** · puerta offline + monitor sin referencia |
| **(B6)** `alembic/versions/0005_session11_hnsw_multi_index.py` | **nuevo** · índice HNSW `halfvec_cosine_ops` en las 3 colecciones |
| **(B6)** `app/generation/rag/index_service.py` | **nuevo** · `CorpusIndexService.expand` (añadir en lote + progreso) |
| **(B6)** `app/api/routers/corpus_index.py` | **nuevo** · `POST /embeddings/index/runs` (async) + `GET …/jobs/{id}` + `GET …/stats` |
| **(B6)** `app/generation/rag/store/repository.py` · `app/foundation/persistence/repositories/jobs.py` | `corpus_stats` + `set_documents_count` (progreso) |
| **(cliente)** `generation_view.rb`, `task_item_view.rb`, `task_hours_estimate_view.rb`, `hour_range_view.rb`, `citation_report_view.rb`, `hallucination_report_view.rb` | POROs S11 |
| **(cliente)** `_step_generation.html.erb`, `_step_hours.html.erb`, `index.html.erb` | gate/citación por línea; rango de horas; embudo de calidad |
| **(cliente · B6)** `index_client.rb`, `Rag::IndexRun` (+migración `index_runs`), `index_runs_controller.rb`, vistas `index_runs/*`, `index_run_poller_controller.js` | sección “Corpus / Índice”: añadir info → job async → progreso → crecimiento |

### Settings nuevas (todas conmutables en caliente vía `PUT /api/v1/config/retrieval` · Ajustes)

`HALLUCINATION_GATE_ENABLED`, `HALLUCINATION_JUDGE_MODEL`, `HALLUCINATION_NUMERIC_TOLERANCE`,
`AUGMENTATION_ENABLED`, `AUGMENTATION_COMPRESS`, `AUGMENTATION_REORDER`, `AUGMENTATION_MODEL`,
`SYNTHESIS_ENABLED`, `SYNTHESIS_CONTRADICTION_THRESHOLD`. Los modelos `HALLUCINATION_JUDGE_MODEL`
y `AUGMENTATION_MODEL` están en `AVAILABLE_MODELS` (switchables también vía `PUT /api/v1/config/models`).


### Límites de alcance (no negociables)

- **Ampliar** el corpus con información nueva **entra** (Bloque 6). **Re-embeder el corpus existente**
/ versionar embeddings por un cambio de modelo (blue-green) **NO entra** — material de ampliación
asíncrono.
- La **citación no se reexplica desde cero**: viene del ejercicio; en el directo se profundiza
(de integridad referencial a verificación semántica).