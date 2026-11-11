# Línea de formación · Sesión 10 · Técnicas avanzadas de recuperación

> Diapo a diapo: **qué contar**, **qué código abrir** (y qué parte), **qué lanzar en la terminal** y **cuándo ir a
> la interfaz**. Las rutas de código son relativas a la carpeta `estimator/` del worktree; en VS Code abre la carpeta
> `ai-engineering-s10` y usa Ctrl+P con el nombre del fichero y Ctrl+G con el número de línea.
> Las diapos llevan la misma ruta en su franja «▶ En el código».

---

## Antes de empezar (10 min antes)

**PowerShell, terminal 1 (comandos):**

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s10"
```

```powershell
docker compose -p aieng-s10live ps
```

```powershell
docker compose -p aieng-s10live exec estimator python -m app.generation.rag.retrieval.verify_reranker 2>$null
```

Pega una vez el helper de las demos:

```powershell
$B = "http://localhost:8000"; $H = @{ "X-API-Key" = "demo-retrieval-key" }; $E = @{ "X-API-Key" = "demo-estimate-key" }
function adv($body) { Invoke-RestMethod -Method Post -Uri "$B/v1/retrieval/advanced-search" -Headers $H -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 5) }
```

**Pestañas abiertas en el navegador:**

- Swagger: <http://localhost:8000/docs>
- Búsqueda avanzada: <http://localhost:3000/rag/advanced_searches/new>
- Corpus: <http://localhost:3000/rag/corpus>
- Histórico: <http://localhost:3000/history>
- Wizard de estimación: <http://localhost:3000/rag/estimation_runs/new>

**La interfaz (menú de arriba: Búsqueda · Corpus · Histórico).** Cada demo de terminal tiene su botón en
*Búsqueda*: los ejemplos de la columna derecha rellenan la consulta y los toggles, y al lanzar se ve el routing, la
técnica, las sub-consultas, la cardinalidad por colección y los chunks con su score. Todo lo que se lanza queda en
*Histórico* (búsquedas, estimaciones del wizard y Chunking Lab). *Corpus* enseña lo que hay de verdad en las tres
tablas, filtrable por tipo de chunk y por texto. Ya hay 7 búsquedas guardadas (una por demo) por si algo va lento.
Se puede elegir: terminal para enseñar el JSON crudo, interfaz para que se entienda de un vistazo.

**VS Code:** carpeta `ai-engineering-s10`, con estos ficheros ya abiertos en pestañas:
`retrieval/fusion.py`, `retrieval/router.py`, `retrieval/query_transform.py`, `retrieval/advanced_pipeline.py`,
`retrieval/temporal.py`, `task_hours.py`, `scripts/eval_retrieval_s10.py`.

---

## Apertura · 5 min

### Diapo 1 · Portada · Diapo 2 · Hoy: de un índice a un pipeline

- La S9 acabó con los límites del RAG básico: preguntas ambiguas, temporales y multi-tema. Hoy es la respuesta.
- Regla de oro: cada etapa entra chunks y sale chunks, y se enciende o se apaga sin tocar código.
- 💻 Sin código. 🖥️ Sin interfaz.

---

## Bloque 1 · Lo que traen del ejercicio · 15 min

### Diapo 3 · Lo que traéis del ejercicio previo

- Tres cimientos: híbrido + RRF, idioma del tsvector y reranking. Hoy el reranking **no se reprograma**: se calienta, se compone y se mide.
- 💻 Solo nombrarlo: `scripts/eval_retrieval_s10.py` existe y hoy le añadimos filas.

### Diapo 4 · Calibración de RRF

- RRF suma `1/(60 + posición)` en cada lista: gana quien va bien en las dos, no quien tiene el mejor score.
- 💻 **`app/generation/rag/retrieval/fusion.py`** → función **`reciprocal_rank_fusion()`** (línea 25). Enseña que recibe
  **listas de ids** (posiciones), nunca puntuaciones, y el `k=60`.
- 💻 `app/config.py` → `RRF_K` (línea 150).

### Diapo 5 · El idioma del tsvector

- Columna y consulta con la misma configuración, la del idioma del corpus (inglés). Si no, el índice se ignora en silencio.
- 💻 **`app/generation/rag/store/models.py`** → `FTS_REGCONFIG = "english"` (línea 54) y la columna `content_tsv` (línea 100).
- 💻 **`app/generation/rag/store/repository.py`** → `search_lexical()` (línea 175): el `plainto_tsquery("english", …)`.
- ⌨️ Demo en psql:

```powershell
docker compose -p aieng-s10live exec estimator-postgres psql -U estimator -d estimator -c "SELECT to_tsvector('english','Stripe Connect onboarding') @@ plainto_tsquery('english','stripe onboarding') AS matches;"
```

  Sale `t`.

### Diapo 6 · Reranking

- Bi-encoder para buscar (barato, miles de chunks) y cross-encoder para ordenar (caro, solo los 50 mejores).
- 💻 **`app/generation/rag/retrieval/reranker.py`** → `score()` (línea 77) y `rerank_with_scores()` (línea 97): construye
  los pares (consulta, documento) y devuelve un logit por documento.
- ⌨️ Ya está calentado. Si quieres enseñarlo: el comando de `verify_reranker` de arriba (relevante +2,95, irrelevante −9,01).

---

## Bloque 2 · Casos avanzados · 90 min

### Diapo 7 · (LIDR) El orden del pipeline es el mensaje

- Lo barato y excluyente al principio, lo caro y fino al final, lo blando al cierre.
- 💻 **`app/generation/rag/retrieval/advanced_pipeline.py`** → `StageConfig` (línea 53: los toggles) y
  **`advanced_retrieve()`** (línea 160): recorre la función de arriba abajo, es el pipeline entero en orden.

### Diapo 8 · (LIDR) Routing en cascada · Diapo 9 · Routing en directo

- Explícito → reglas → clasificador LLM → todas. "El mejor router es no tener router".
- 💻 **`app/generation/rag/retrieval/router.py`** → **`route()`** (línea 73): los cuatro niveles y el log `routing_decided`.
- 💻 **`app/generation/rag/retrieval/collections.py`** → `match_rules()` (línea 195) y los `rule_patterns` de cada
  colección (desde la línea 134): son regex de vocabulario.
- ⌨️ Las tres demos:

```powershell
adv @{query_text="what did the client say in the meeting about Stripe checkout"; top_k=4} | Select routing, technique, cardinality | Format-List
```

```powershell
adv @{query_text="OAuth 2.0 PKCE flow and PSD2 strong customer authentication reference"; top_k=3} | Select -Expand routing | Format-List
```

```powershell
adv @{query_text="telemedicine appointment scheduling"; collections=@("budget"); top_k=3} | Select -Expand routing | Format-List
```

  Salen: `rules → transcript`, `classifier → technical_doc` (con su `reason`) y `explicit → budget`.
- 🖥️ **Interfaz:** Búsqueda → ejemplos «Routing · reglas», «Routing · clasificador LLM» y «Routing · explícito». La
  tarjeta *Routing* enseña el nivel, las colecciones y el motivo.

### Diapo 10 · (LIDR) Expansión vs descomposición · Diapo 11 · Descomposición en directo

- ¿Una cosa dicha de muchas maneras (expansión, fusión por consenso) o muchas cosas a la vez (descomposición, fusión por cobertura)?
- 💻 **`app/generation/rag/retrieval/query_transform.py`** → **`choose_technique()`** (línea 82): la heurística de
  longitud y conectores que decide sin LLM; y `transform_query()` (línea 102).
- 💻 **`app/generation/rag/retrieval/fusion.py`** → `round_robin_merge()` (línea 63).
- 💻 **`advanced_pipeline.py`** → `_fuse_collection()` (línea 134): las dos ramas de fusión.
- ⌨️ Demos:

```powershell
adv @{query_text="we need OAuth and a transaction ledger, plus a Stripe checkout, and also personalized recommendations for the product catalog"; collections=@("budget"); top_k=5} | Select technique, subqueries | Format-List
```

```powershell
adv @{query_text="Stripe checkout"; collections=@("budget"); top_k=3} | Select technique | Format-List
```

  Salen `decompose` con 4 temas y `direct`.
- 🖥️ **Interfaz:** Búsqueda → «Descomposición» y «Consulta directa». La tarjeta *Técnica* lista las sub-consultas por
  tema y los resultados salen intercalados (round-robin).

### Diapo 12 · (LIDR) Filtro duro vs ponderación blanda · Diapo 13 · Decaimiento temporal

- Filtro duro: excluye antes de buscar. Ponderación blanda: desempata al final. El orden no es negociable.
- 💻 **`app/generation/rag/retrieval/collections.py`** → `hard_filter_clauses()` (línea 106): el `WHERE` por sector,
  tecnología y fecha.
- 💻 **`app/generation/rag/retrieval/temporal.py`** → `decay_weight()` (línea 33): la fórmula entera son 3 líneas.
- 💻 **`advanced_pipeline.py`** → `_sigmoid()` (línea 128) y el bloque de las líneas 263–279: reranking y después
  decaimiento.

### Diapo 14 · Filtro duro en directo

```powershell
adv @{query_text="telemedicine scheduling and video consultations"; collections=@("budget"); min_date="2024-01-01"; top_k=3} | Select cardinality | Format-List
```

- Sale **1603 → 748**. Cuenta por qué no son 60: las 1543 tareas históricas viven en la misma tabla. Es justo la lección:
  sin mirar la cardinalidad no te enteras.
- 💻 `app/generation/rag/store/repository.py` → `search_filtered()` (línea 107), que devuelve `candidates_evaluated`.
- 🖥️ **Interfaz:** Búsqueda → «Filtro por fecha»: la tarjeta *Cardinalidad tras filtros* marca 748. Después ve a
  **Corpus → Presupuestos → tipo `historical_task`** y enseña las 1543 tareas: ahí se ve por qué no son 60.
  El ejemplo «Rerank + decaimiento» enseña el score final ya ponderado por fecha.

### Diapo 15 · El arnés · Diapo 16 · (LIDR) El arnés no miente · Diapo 17 · Nuestra ejecución

- El arnés pasa las mismas 8 preguntas por cada configuración y mide precision@5 y latencia.
- 💻 **`scripts/eval_retrieval_s10.py`** → la lista **`CONFIGS`** (línea 93): cada fila es un juego de toggles.
  Añadir una medición = añadir una fila.
- 💻 `evals/golden_retrieval.json`: las preguntas con sus respuestas correctas.
- ⌨️ **No lo lances en clase** (tarda varios minutos): enseña la tabla de la diapo 17. Si lo quieres lanzar:

```powershell
docker compose -p aieng-s10live exec estimator python scripts/eval_retrieval_s10.py 2>$null
```

---

## Bloque 3 · Del retrieval al producto · 25 min

### Diapo 18 · (LIDR) Separar estructura de horas

- El LLM descompone bien y pone números mal. Estructura del LLM; horas de búsqueda; humano en las dos fronteras.
- 💻 **`app/generation/rag/task_hours.py`** → **`_consensus()`** (línea 63): la media ponderada por distancia y la fiabilidad.

### Diapo 19 · Horas por tarea en directo

```powershell
$body = '{"modules":[{"name":"Payments & Billing","tasks":[{"name":"Payment gateway integration","description":"Card payments via a PSP with 3-D Secure"},{"name":"Quantum teleporter","description":"nonexistent"}]}]}'
```

```powershell
(Invoke-RestMethod -Method Post -Uri "$B/v1/estimate/tasks/hours" -Headers $E -ContentType "application/json" -Body $body).tasks | Select task, estimated_hours, reliability, has_match | Format-Table
```

- Sale 42 h con fiabilidad 0,505 y el teleporter en rojo.
- 💻 `task_hours.py` → `estimate_one()` (línea 99) y `app/api/routers/estimate_tasks.py` (línea 40).

### Diapo 20 · El wizard de estimación · 🖥️ INTERFAZ

- 🖥️ **<http://localhost:3000/rag/estimation_runs/new>**: pega una transcripción y recorre los pasos
  (reformulación → estructura → revisión → horas → verificación).
- ⚠️ El paso de estructura llama a gpt-5 y **tarda unos 2 minutos**. Lánzalo al empezar el Bloque 3 y sigue hablando, o
  ten uno ya hecho en <http://localhost:3000/rag/estimation_runs>.
- 💻 `app/generation/rag/prompt_builder.py` → `build_system_prompt(include_hours=False)` (línea 14): el prompt que dice
  "no pongas horas".
- 💻 Lado Rails: `estimator-web/app/controllers/rag/estimation_runs_controller.rb` → `generate` (línea 57),
  `estimate_hours` (79) y `verify` (98).

---

## Cierre · 5 min

### Diapo 21 · Cuadro de mando · Diapo 22 · Cierre y S11

- Ninguna técnica es buena siempre: se mide.
- 🖥️ Swagger <http://localhost:8000/docs> → `GET /api/v1/config/retrieval` para enseñar los toggles en vivo.
- Puente a la S11: generación y calidad con lo recuperado.

### Diapo 23 · ROTI · Diapo 24 · Gracias
