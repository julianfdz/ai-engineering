# Línea de formación · Sesión 11 · RAG avanzado: generación y calidad

> Diapo a diapo: **qué contar**, **qué código abrir** (y qué parte), **qué lanzar en la terminal** y **qué enseñar
> en la interfaz**. Las rutas son relativas a `estimator/` salvo las de Rails (`estimator-web/`). En VS Code abre la
> carpeta `ai-engineering-s11`; Ctrl+P con el nombre del fichero y Ctrl+G con el número de línea. Las diapos llevan
> la misma ruta en su franja «En el código», y cada fichero que se abre tiene arriba una cabecera «Julián · Sesión
> 11» con para qué sirve y qué enseñar.
>
> Formato de la clase: **no se teclea código**. Todo está implementado; se abre, se explica y se ejecuta.

---

## Antes de empezar (10 min antes)

**PowerShell (comandos):**

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s11"
```

```powershell
docker compose -p aieng-s11live up -d
```

```powershell
docker compose -p aieng-s11live ps
```

Los cinco contenedores `s11-*` deben salir `healthy`. Si Docker Desktop no arranca con el error «Ingest server …
sock.stale: El sistema no tiene acceso al archivo», el arreglo está en la memoria de Docker: cerrar Docker, renombrar
`%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine`, y volver a abrirlo.

Pega una vez estos helpers (mandan el cuerpo en UTF-8, así que las tildes y la raya «—» no se rompen):

```powershell
$B = "http://localhost:8000"; $E = @{ "X-API-Key" = "demo-estimate-key" }; $R = @{ "X-API-Key" = "demo-retrieval-key" }
function api($metodo, $ruta, $cuerpo = $null, $cab = @{}) { $p = @{ Method = $metodo; Uri = "$B$ruta"; Headers = $cab; ContentType = "application/json; charset=utf-8" }; if ($cuerpo) { $p.Body = [Text.Encoding]::UTF8.GetBytes(($cuerpo | ConvertTo-Json -Depth 10)) }; Invoke-RestMethod @p }
function linea($nombre, $dias) { @{ name = $nombre; engineer_days = $dias; grounded = $true; sources = @(@{ chunk_id = "1"; document_id = "BUD-1"; evidence = "AUTH-001 :: OAuth backend — 120 h" }) } }
function gate($lineas, $juez = $false) { api POST "/v1/estimate/stages/verify" @{ use_judge = $juez; kept_chunks = @(@{ id = 1; content = "AUTH-001 :: OAuth backend — 120 h"; chunk_type = "budget_component"; distance = 0.2; estimated_hours = 120 }); estimate = @{ confidence = "high"; reasoning = "demo"; total_engineer_days = 90; modules = @(@{ name = "Auth"; tasks = @($lineas) }) } } $E }
function horas($modulo, $tarea, $desc) { (api POST "/v1/estimate/tasks/hours" @{ modules = @(@{ name = $modulo; tasks = @(@{ name = $tarea; description = $desc }) }) } $E).tasks[0] }
function psql($sql) { docker compose -p aieng-s11live exec estimator-postgres psql -U estimator -d estimator -c $sql }
```

**Pestañas del navegador:**

- Calidad: <http://localhost:3000/rag/quality> (una pestaña por técnica)
- Corpus: <http://localhost:3000/rag/index_runs>
- Wizard: <http://localhost:3000/rag/estimation_runs/new>
- Swagger: <http://localhost:8000/docs>

Enlaces directos a cada demo de Calidad (abren ya con el resultado):

- Gate, cuatro líneas, solo ancla: <http://localhost:3000/rag/quality/verify?preset=all_four>
- Gate con juez: <http://localhost:3000/rag/quality/verify?preset=all_four&use_judge=1>
- Gate con juez y evidencia «120 h»: <http://localhost:3000/rag/quality/verify?preset=all_four&use_judge=1&evidence=short>
- Conflicto 40/90: <http://localhost:3000/rag/quality/hours?task_module=Notifications&task_name=Real-time%20notifications%20delivery%20service&task_description=Multi-channel%20delivery%20(push%2C%20email%2C%20SMS)%20with%20a%20durable%20queue%2C%20per-channel%20retry%20and%20backoff%20and%20delivery%20receipts>
- Augmentation: <http://localhost:3000/rag/quality/augment>

**VS Code** (carpeta `ai-engineering-s11`), con estos 18 ficheros abiertos en el orden de la clase:
`rag/schemas.py`, `rag/validation.py`, `scripts/demo_verify_citations_s11.py`, `scripts/score_ragas_s11.py`,
`evals/golden_generation_s11.json`, `evals/RAGAS_BASELINE_S11.md`, `rag/quality/hallucination.py`,
`api/routers/estimate_stages.py`, `rag/estimator.py`, `rag/quality/augmentation.py`,
`data/task_corpus_contradictions.json`, `rag/quality/synthesis.py`, `rag/task_hours.py`,
`estimator-web/app/views/rag/estimation_runs/_step_hours.html.erb`, `scripts/eval_generation_s11.py`,
`rag/index_service.py`, `api/routers/corpus_index.py` y `alembic/versions/0005_session11_hnsw_multi_index.py`.
(`rag/` es `app/generation/rag/`.) Todos los de código llevan cabecera; los JSON y el `.md` no admiten comentarios.

**Interruptores en «Por defecto»** antes de empezar: Calidad → Interruptores, los tres en «Por defecto (on)».

---

## Apertura · 5 min

### Diapo 1 · Portada · Diapo 2 · Hoy

- La S9 y la S10 fueron la mitad de recuperación. Hoy, la mitad de generación: que la cifra se sostenga y que se
  pueda medir.
- El arco: citada (S9) → verificable (vuestro ejercicio) → fundamentada → medible (hoy).
- Hilo conductor: vuestra tabla RAGAS es el marcador; todo lo de hoy se mide contra ella.
- 🖥️ Enseña el menú nuevo de la web: **Calidad** y **Corpus**.

---

## Bloque 1 · Pre-vuelo y errores · 15 min

### Diapo 3 · Lo que traéis: citación verificable por línea

- No se reexplica: se repasa en dos minutos para construir encima.
- 💻 **`rag/schemas.py`**: `SourceReference` (l. 345) y `TaskItem` (l. 369): `grounded` + `sources`. El validador
  impone «grounded ⇒ al menos una fuente; no grounded ⇒ sin fuentes y sin horas».
- 💻 **`rag/validation.py`** → `verify_citations` (l. 38): recorre `modules[].tasks[]` y separa grounded, dangling
  e insufficient. Recalca el límite: comprueba que el id **existe**, no que la cifra se **deduzca**.
- ⌨️ La prueba sin red:

```powershell
docker compose -p aieng-s11live exec estimator python scripts/demo_verify_citations_s11.py 2>$null
```

  Sale `ACCEPTANCE: PASS` con el 999 colgante y «Regulatory reporting» insufficient.

### Diapo 4 · Pre-vuelo: cinco comprobaciones

- ⌨️ Las cinco filas, en orden:

```powershell
api GET "/health"
```

```powershell
psql "select chunk_type, count(*) from budget_chunks group by 1;"
```

  Esperado: `historical_task 1547` (1.543 + las 4 del caso en conflicto) y `budget_component 60`.

```powershell
(Get-Content estimator\evals\golden_generation_s11.json -Raw | ConvertFrom-Json).queries.Count
```

  La fila 4 es el `demo_verify_citations` de la diapo anterior. La fila 5, el gate nuevo sin LLM:

```powershell
(gate @(linea "OAuth login" 90)).lines | Format-List component, status, reason
```

  → `degraded` · «claims 90d but the cited evidence supports ~15d».
- Remarca: ninguna de las cinco llama a un modelo.

### Diapo 5 · Los errores típicos del ejercicio

- Repasa la tabla y pregunta quién se encontró cada uno.
- 💻 **`scripts/score_ragas_s11.py`** → `_install_vertex_shims` (l. 43): ragas 0.4 importa Vertex al cargar; un stub
  vacío lo arregla. Por eso se puntúa en un venv aparte (`estimator\.ragas-venv`).
- El `context_recall ≈ 0` no es un bug: es el primer hallazgo, y lleva a la diapo siguiente.

---

## Bloque 2 · El marcador · 15 min

### Diapo 6 · Cuatro métricas, dos ejes

- Recuperación (precision, recall) frente a generación (faithfulness, relevancy).
- Cómo calcula cada una el juez. Deja sembrado que solo faithfulness y relevancy funcionan sin `ground_truth`
  (sale en el Bloque 5).
- 💻 **`evals/golden_generation_s11.json`**: enseña una consulta con su `transcript` y su `ground_truth` en días.

### Diapo 7 · Vuestro baseline ya dice dónde mirar

- 💻 **`evals/RAGAS_BASELINE_S11.md`**: la tabla y la nota de hallazgos.
- Pide a cada alumno su **peor métrica**: será su objetivo del bucle.
- La grieta accionable es faithfulness: 0 colgantes, pero la cifra no siempre sale de la cita. Menciona la
  anomalía de unidades (horas copiadas como días en 4 de 5).
- Defensa: «¿relevancy ≈ 0 es mala respuesta?» No: brief declarativo frente a tabla; la métrica está mal
  planteada para este formato.

---

## Bloque 3 · Detección de alucinaciones · 25 min

### Diapo 8 · Una cita real puede mentir

- El ejemplo: el chunk 1 dice 120 h, la línea lo cita y reclama 90 días. `verify_citations` dice grounded.
- Dos capas: la referencial (ejercicio) y la semántica (hoy).

### Diapo 9 · Tres desenlaces, no dos

- 💻 **`rag/quality/hallucination.py`**:
  - `numeric_anchor` (l. 71): suma las horas de los chunks citados (metadato o «120 h» en el texto) y divide
    entre 8. Sin LLM.
  - `gate_line` (l. 89): léela entera, es pura. El exceso en l. 112: `overage > tolerance`. Solo el exceso
    cuenta.
- La regla asimétrica: una línea puede ser una porción de su fuente; reclamar mucho más no.

### Diapo 10 · Demo: el gate con y sin juez

- 🖥️ **Calidad → Gate**, «Las cuatro a la vez», sin juez → 2 grounded, 1 degraded, 1 insufficient.
- 🖥️ Marca «Con juez» → la de 20 días (+33 %) pasa a degraded. El ancla la tolera; el juez no tiene tolerancia,
  y basta con que uno falle.
- 🖥️ Cambia la evidencia a «solo la cifra: 120 h» → el juez degrada también la de 10 días: la cita no dice de qué
  trabajo es. Lección: la evidencia que copia la línea tiene que nombrar el trabajo.
- ⌨️ Lo mismo por terminal, si se prefiere el JSON:

```powershell
$r = gate @((linea "OAuth login" 90), (linea "OAuth token refresh" 10), (linea "OAuth session management" 20)) $true; $r.lines | Format-Table component, status, reason -Wrap
```

- 💻 **`api/routers/estimate_stages.py`** → `verify` (l. 230): el endpoint de enseñanza.
- El juez tarda unos 7 s.

### Diapo 11 · El juez y dónde se engancha

- 💻 **`hallucination.py`** → `_judge_system_prompt` (l. 140): «Default to false when in doubt». `judge_estimate`
  (l. 174): una llamada para todas las líneas; si falla, mapa vacío y el gate sigue solo con el ancla.
- 💻 **`rag/estimator.py`**, el conductor: paso 4 (l. 268, augmentation), paso 6 (l. 285, citas), **paso 6.5
  (l. 316)**: una línea degradada baja la confianza a `low`. Paso 7 (l. 339), coherencia.
- Defensa: «¿una llamada por línea?» No, una para todas.
- Contingencia: si el gate es demasiado agresivo, la tolerancia es `HALLUCINATION_NUMERIC_TOLERANCE` en el `.env`
  (no se cambia en caliente), o `use_judge=false` para aislar el ancla.

---

## Bloque 4 · Augmentation y síntesis · 25 min

### Diapo 12 · Mejor material de entrada: augmentation

- 💻 **`rag/quality/augmentation.py`**: `extract_key_points` (l. 34), `reorder_edge_loaded` (l. 58),
  `augment_chunks` (l. 73). Todo determinista, sin LLM, y los ids no cambian.
- 🖥️ **Calidad → Augmentation**, preset «banking» → 1.061 → 740 tokens (−30 %) y el orden 2·3·868…4·1: el mejor
  primero y el segundo mejor el último.
- 🖥️ Señala la trampa en la columna derecha: el chunk 3 se queda en «Estimated hours: 140» sin decir qué
  componente es. Une con la diapo 10: una evidencia sin nombre es justo lo que el juez rechaza.

### Diapo 13 · Fuentes en conflicto: un rango con razón

- El fixture: la misma tarea a 40 h (tienda, solo email) y a 90 h (fintech regulada).
- 💻 **`data/task_corpus_contradictions.json`**: enseña los dos proyectos.
- 💻 **`rag/quality/synthesis.py`**: `is_contradiction` (l. 43, dispersión > 0,35) y `_deterministic_range`
  (l. 48, min/max + razón). 💻 **`rag/task_hours.py`** (l. 172): solo si la síntesis está encendida.
- 🖥️ **Calidad → Fuentes en conflicto**, botón «Conflicto 40 h / 90 h» → «⚠ 15–90 h», consenso 39 h, dispersión
  0,71, y en la tabla los vecinos 90, 40, 15, 23, 23.
- ⌨️ Alternativa en terminal:

```powershell
horas "Notifications" "Real-time notifications delivery service" "Multi-channel delivery (push, email, SMS) with a durable queue, per-channel retry and backoff and delivery receipts" | Format-List estimated_hours, reliability, dispersion, hours_range
```

- Por qué 15 y no 40: el rango es el min/max de los vecinos y la síntesis no sabe cuál es el fixture.
- Defensa: «¿Por qué no elegís un número?» Porque 65 h esconde una decisión de alcance que es del humano.

### Diapo 14 · El rango depende de cómo se describe la tarea

- 🖥️ En la misma pestaña, cambia la descripción a «push, email and SMS with retries» → solo entra el de 40 h y sale
  15–40. Cambia el módulo a «Demo» → otros vecinos.
- La contingencia típica («subir los vecinos») no ayuda: más vecinos parecidos de 15-27 h bajan la dispersión.
- 💻 **`estimator-web/…/_step_hours.html.erb`** (l. 39 el badge, l. 68 la celda ámbar). En el wizard de verdad se
  ve en el paso de horas si una tarea se describe así.

---

## Bloque 5 · Evaluación en dos modos · 20 min

### Diapo 15 · Dos modos de evaluación

- 💻 **`scripts/eval_generation_s11.py`**: `BASELINE` (l. 72), `REGRESSION_TOLERANCE` (l. 78), `run_gate` (l. 243:
  exit 1 si una métrica cae más de 0,05 o hay una cita colgante) y `run_monitor` (l. 272: solo las dos métricas sin
  referencia).
- Defensa: «¿Por qué dos modos?» Porque en producción no hay `ground_truth`.

### Diapo 16 · Cada técnica es una config

- 💻 `CONFIGS` (l. 95): baseline / gate / augment / full como datos. `_apply_config` (l. 103): cambia los
  ajustes del proceso; si hay un interruptor cambiado en Redis, manda Redis.
- ⌨️ No lances `--compare` en vivo (4 configs × 5 consultas con gpt-5). La puerta con 2 consultas, en dos pasos
  (recoger en el contenedor, puntuar en el venv de RAGAS):

```powershell
docker compose -p aieng-s11live exec estimator python scripts/eval_generation_s11.py --gate --config full --limit 2 --collect-only evals/s11_full.json 2>$null
```

```powershell
$env:OPENAI_API_KEY = ((Get-Content estimator\.env | Select-String '^OPENAI_API_KEY=').Line -split '=', 2)[1]
```

```powershell
estimator\.ragas-venv\Scripts\python.exe estimator\scripts\eval_generation_s11.py --gate --score-file estimator\evals\s11_full.json; "exit=$LASTEXITCODE"
```

  El monitor, con las mismas muestras:

```powershell
estimator\.ragas-venv\Scripts\python.exe estimator\scripts\eval_generation_s11.py --monitor --score-file estimator\evals\s11_full.json
```

- Resultado del ensayo del 18/11 (está en la diapo 15): faithfulness 0,551 · answer_relevancy 0,039 ·
  context_precision 1,000 · context_recall 0,312 · 0 colgantes → **GATE: DEPLOY**, `exit=0`; el gate marcó 28
  líneas degradadas. Monitor: faithfulness 0,535 · answer_relevancy 0,039.
- Tiempos medidos: recoger 2 consultas **5,5 min** (cada una, una generación con gpt-5 de 1,5–2,5 min + el juez);
  puntuar la puerta 1,5 min y el monitor 1 min. Lanza la recogida al **empezar el Bloque 4** en una segunda
  PowerShell y puntúa en el Bloque 5.
- Plan B si no da tiempo o falla la API: la recogida del ensayo está en `estimator\evals\s11_full.json`
  (commiteada); basta con los dos comandos de puntuar.
- 🖥️ El cambio en vivo: **Calidad → Interruptores**, apaga «Augmentation» → la siguiente estimación ya no comprime.
  Devuélvelo a «Por defecto» al acabar. **No toques los interruptores mientras corre la recogida**: la evaluación
  lee Redis y mezclarías configs.

### Diapo 17 · Goodhart

- Cada métrica tiene su trampa si se optimiza sola. La puerta lee las cuatro juntas y las citas colgantes son
  fallo directo.

---

## Bloque 6 · Ampliar e indexar el corpus · 12 min

### Diapo 18 · Ampliar el corpus

- Información nueva sí; re-embeder lo existente (cambio de modelo, blue-green) queda fuera de hoy.
- 💻 **`rag/index_service.py`** → `expand` (l. 57): un documento cada vez, duplicados saltados (l. 84).
- 💻 **`api/routers/corpus_index.py`**: `create_index_run` (l. 103, 202 + `BackgroundTask`), `get_index_job`
  (l. 134), `get_corpus_stats` (l. 153). Sin `X-API-Key`.

### Diapo 19 · El índice tiene que casar con la consulta

- 💻 **`alembic/versions/0005_session11_hnsw_multi_index.py`** → `upgrade` (l. 57): el índice sobre
  `embedding::halfvec(1536)` con `halfvec_cosine_ops`.
- ⌨️ El EXPLAIN tal cual sale Seq Scan (con 1.600 filas es lo más barato):

```powershell
psql "EXPLAIN ANALYZE SELECT id FROM budget_chunks ORDER BY embedding::halfvec(1536) <=> (SELECT embedding::halfvec(1536) FROM budget_chunks LIMIT 1) LIMIT 5;"
```

  Forzando que no recorra la tabla, usa el índice:

```powershell
psql "SET enable_seqscan = off; EXPLAIN ANALYZE SELECT id FROM budget_chunks ORDER BY embedding::halfvec(1536) <=> (SELECT embedding::halfvec(1536) FROM budget_chunks LIMIT 1) LIMIT 5;"
```

  → `Index Scan using ix_budget_chunks_embedding_hnsw` (~1,3 ms). Y la consulta con `vector` a secas no puede
  usarlo ni forzada:

```powershell
psql "SET enable_seqscan = off; EXPLAIN SELECT id FROM budget_chunks ORDER BY embedding <=> (SELECT embedding FROM budget_chunks LIMIT 1) LIMIT 5;"
```

### Diapo 20 · Demo: el corpus crece y lo nuevo se recupera

- ⌨️ Antes, lo más parecido a un onboarding KYC es una tarea genérica de finanzas (~0,47):

```powershell
(api POST "/v1/retrieval/search" @{ query_text = "Biometric KYC onboarding with liveness detection and document OCR for a neobank"; top_k = 3 } $R).chunks | Format-Table id, budget_id, distance
```

- 🖥️ **Corpus → Añadir información**: el formulario ya trae el proyecto KYC (3 componentes). «Indexar en el corpus
  →» → barra de progreso → 1.607 → 1.610 chunks.
- ⌨️ La misma búsqueda: ahora los tres primeros son `BUD-2025-0100` (~0,17).
- 🖥️ Vuelve a indexar el mismo JSON → el job acaba con 0 procesados (duplicado saltado).
- Para repetir la demo otro día, borrar lo añadido:

```powershell
psql "DELETE FROM documents WHERE source_path LIKE 'corpus-expansion::%';"
```

---

## Cierre · 8 min

### Diapo 21 · Lo que cierras hoy

- Las tres tensiones: determinismo y juicio, abstenerse o responder, métrica y calidad.
- Puente a la S12: el modelo pasa a decidir el flujo; cada paso necesitará su ancla, su gate y su métrica.
- Rama de referencia: `session_11_live`.

### Diapos 22-23 · ROTI y gracias

---

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `429 credit_balance_exhausted` / «Upstream LLM call failed» | la clave de OpenAI no tiene saldo. Sin LLM siguen funcionando el gate sin juez, la citación, los EXPLAIN y las estadísticas |
| El juez no cambia nada | se cayó y el gate siguió solo con el ancla (aviso `hallucination_judge_failed` en los logs) |
| El rango no aparece | revisa módulo y descripción (diapo 14); el fixture tiene que estar (`psql "select count(*) from budget_chunks where chunk_type='historical_task';"` → 1547) |
| El job se queda en `running` | logs del servicio: `docker compose -p aieng-s11live logs --tail 50 estimator` |
| `--gate` bloquea siempre | interruptores cambiados en Redis: Calidad → Interruptores → «Por defecto» |
