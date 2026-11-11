# session-10-live-guide


# Sesión 10 — Recuperación avanzada (multi-índice, routing, expansión, decaimiento)

> **Módulo 3 · Duración 120 min · Modalidad flipped classroom.Estado de entrada:** el repo trae ya, del ejercicio pre-sesión, la búsqueda
híbrida (columna `content_tsv` + RRF) y el reranking con cross-encoder
(recall-then-rerank), más el arnés `scripts/eval_retrieval_s10.py` y su golden
set. La rama `session_10` parte de ahí.
**Estado de salida:** corpus particionado en tres colecciones, router en
cascada, expansión/descomposición de consultas, filtros duros, decaimiento
temporal y el pipeline avanzado ensamblado por etapas conmutables, todo medible
con el arnés extendido. **Y, como cierre-aplicación (Bloque 3),** el flujo de
estimación pasa a *separar estructura de horas*: el LLM genera solo módulos→tareas,
un humano los revisa, las horas se **derivan por búsqueda vectorial por tarea**
(consenso + score de fiabilidad, rojo si no hay análogo) y un segundo humano
edita horas/tarifas y confirma — el motor de recuperación del Bloque 2 puesto al
servicio de una decisión de negocio.
**Idioma:** la prosa de esta guía está en español; **todo el código, payloads,
nombres de campo y logs están en inglés** (convención del repo).


> ## Nota local (PC de Julián) — leer antes del directo
>
> Todo verificado el 11/11/2026 en el worktree `ai-engineering-s10`, proyecto `aieng-s10live`.
> Los cURL del guion están pensados para macOS: en PowerShell usa estos bloques.
>
> **Pre-flight (PowerShell):**
>
> ```powershell
> cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s10"
> docker compose -p aieng-s10live ps
> docker compose -p aieng-s10live exec estimator python -m app.generation.rag.retrieval.verify_reranker 2>$null
> ```
>
> **Helper para las demos de recuperación (pegar una vez):**
>
> ```powershell
> $B = "http://localhost:8000"; $H = @{ "X-API-Key" = "demo-retrieval-key" }; $E = @{ "X-API-Key" = "demo-estimate-key" }
> function adv($body) { Invoke-RestMethod -Method Post -Uri "$B/v1/retrieval/advanced-search" -Headers $H -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 5) }
> ```
>
> **Demos (salidas reales de hoy):**
>
> | Demo | PowerShell | Resultado real |
> |---|---|---|
> | Reglas | `adv @{query_text="what did the client say in the meeting about Stripe checkout"; top_k=4} \| Select routing, technique, cardinality \| Format-List` | `rules → [transcript]`, `expand`, cardinalidad 11 |
> | Clasificador | `adv @{query_text="OAuth 2.0 PKCE flow and PSD2 strong customer authentication reference"; top_k=3} \| Select -Expand routing \| Format-List` | `classifier → [technical_doc]` con su `reason` |
> | Explícito | `adv @{query_text="telemedicine appointment scheduling"; collections=@("budget"); top_k=3} \| Select -Expand routing \| Format-List` | `explicit → [budget]` |
> | Descomposición | `adv @{query_text="we need OAuth and a transaction ledger, plus a Stripe checkout, and also personalized recommendations for the product catalog"; collections=@("budget"); top_k=5} \| Select technique, subqueries \| Format-List` | `decompose`, 4 temas |
> | Directa | `adv @{query_text="Stripe checkout"; collections=@("budget"); top_k=3} \| Select technique \| Format-List` | `direct` |
> | Filtro fecha | `adv @{query_text="telemedicine scheduling and video consultations"; collections=@("budget"); min_date="2024-01-01"; top_k=3} \| Select cardinality \| Format-List` | **1603 → 748** (con `sectors=@("healthcare")`: 84) |
> | Horas por tarea | ver bloque 3.3 abajo, con `Invoke-RestMethod ... -Headers $E` | 42 h · fiabilidad 0,505 · 5 vecinos; el teleporter en rojo |
>
> **Lo que difiere del guion de LIDR:**
>
> - **Cardinalidad del filtro por fecha: 1603 → 748, no 60 → 42.** El corpus de tareas del Bloque 3 se guarda en la misma
>   tabla `budget_chunks` (60 componentes + 1543 tareas). El guion lo ingesta en el pre-flight y luego da los números de
>   antes. Contarlo como lo que es: otro ejemplo de "vigila siempre la cardinalidad".
> - **Reranker en frío: 16,6 s**, no ~80 s (ya calentado al montar).
> - **`/stages/generate` con `include_hours=false`**: con el contexto mínimo del guion ("Auth & RBAC ~32h") gpt-5 responde
>   `confidence: insufficient` sin módulos. Con un brief más rico sale bien (confianza alta, horas a `null`) pero tarda
>   **~130 s**. En clase: enseñarlo en el wizard ya ejecutado, o bajar `GENERATION_MODEL` desde Ajustes.
> - El paso `docker cp evals/...` no hace falta: el override ya monta `estimator/evals`.

---


## Cómo leer este guion

Cada sub-bloque usa los mismos marcadores que las guías de S08/S09:

| Marcador | Qué es | Dónde |
|---|---|---|
| **■ Fundamento · pizarra** | la idea que se explica de viva voz | pizarra / slide |
| **■ Dónde vive** | archivos exactos (`ruta:línea`) a abrir en pantalla | IDE |
| **■ Demo · terminal** | el comando cURL/psql que se ejecuta en directo | terminal |
| **■ Contingencia** | qué hacer si algo falla en el momento | — |
| **■ Bridge** | la frase puente al siguiente bloque | — |
> **Regla de oro de la sesión.** Cada etapa del pipeline es *componible y
conmutable*: entra una lista de chunks, sale una lista de chunks, y un toggle
de configuración la activa o desactiva sin tocar código. El pipeline completo
es el camino **máximo**, no el obligatorio — y por eso cada pieza se puede medir
aislada.
> **Nota de coherencia con los artículos.** Los artículos enseñaron las llamadas
LLM con `client.responses.parse`. El repo de referencia las hace con
`LLMWrapper.complete_structured` (Instructor + LiteLLM): **misma garantía de
salida estructurada Pydantic v2**, reutilizando la infraestructura que ya posee
reintentos, fallback y tracking de coste. Es la regla “la arquitectura existente
gana”. Menciónalo una vez y sigue.

---


## Prerrequisitos (montar 10–15 min antes)

```bash
cd /Users/antonioperez/projects/ia/ai-engineering/estimator

# 1. Levantar el stack (aplica migraciones con `alembic upgrade head`).
docker compose up -d --build

# 2. Ingestar las TRES colecciones:
uv run python scripts/query_examples.py                                   # budgets (HTTP)
docker compose exec estimator python scripts/build_multi_index_corpus.py  # transcripts + docs

# 3. (Bloque 3) Ingestar el corpus de tareas que ancla las HORAS por tarea
#    (default: 60 proyectos / ~1.500 tareas, 8 sectores; --count/--seed lo ajustan):
docker compose exec estimator python scripts/build_task_corpus.py --ingest # chunk_type=historical_task
```
Variables de entorno relevantes (`.env`):

```plain text
RETRIEVAL_API_KEY=demo-retrieval-key      # header X-API-Key del router de recuperación
ESTIMATE_API_KEY=demo-estimate-key
ROUTER_MODEL=gpt-4o-mini                   # clasificador de routing (pequeño y rápido)
QUERY_TRANSFORM_MODEL=gpt-4o-mini          # expansión/descomposición
TEMPORAL_DECAY_HALF_LIFE_DAYS=900          # semivida del decaimiento (~2.5 años)
RETRIEVAL_ROUTING_ENABLED=true
QUERY_TRANSFORM_ENABLED=true
TEMPORAL_DECAY_ENABLED=false               # blando: encender solo con evidencia
TASK_HOURS_TOP_K=5                         # (Bloque 3) vecinos para el consenso de horas
TASK_HOURS_DISTANCE_THRESHOLD=0.45         # umbral del "rojo" (sin dato si se supera)
```
Exporta para abreviar los cURL del directo:

```bash
export K=demo-retrieval-key
export B=http://localhost:8000
```
> **Trampa de entorno conocida.** Si tu shell tiene `OPENAI_API_KEY` exportada,
**pisa** la del `.env`. Para el directo desactívala (`unset OPENAI_API_KEY`) y
deja que el contenedor use la del `.env`, o ejecuta los scripts dentro del
contenedor (`docker compose exec estimator …`).

---


## Pre-flight checklist (cURL en frío)

Ejecuta esta rutina antes de empezar; cada línea verifica una pieza.

| # | Qué verifica | Comando | Esperado |
|---|---|---|---|
| 1 | API viva | `curl -s $B/health` | `{"status":"healthy",...}` |
| 2 | Migración aplicada | `docker compose exec estimator-postgres psql -U estimator -d estimator -c "SELECT version_num FROM alembic_version;"` | `0004_session10_multi_index` |
| 3 | Tres colecciones | `docker compose exec estimator-postgres psql -U estimator -d estimator -c "\dt *chunks*"` | `budget_chunks`, `transcript_chunks`, `technical_doc_chunks` |
| 4 | Corpus ingestado | `docker compose exec estimator-postgres psql -U estimator -d estimator -c "SELECT 'budget',count(*) FROM budget_chunks UNION ALL SELECT 'transcript',count(*) FROM transcript_chunks UNION ALL SELECT 'doc',count(*) FROM technical_doc_chunks;"` | `60 / 11 / 8` |
| 5 | Endpoint S09 intacto | ver bloque abajo | `chunks` no vacío |
| 6 | Endpoint S10 avanzado | ver bloque abajo | `routing` + `technique` presentes |
```bash
# 5 — el endpoint de S09 NO cambia de contrato (compatibilidad hacia atrás).
curl -s -X POST $B/v1/retrieval/search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"payments gateway with Stripe integration","top_k":3,"search_mode":"hybrid"}' \
  | jq '{n:(.chunks|length), low_confidence}'
# → { "n": 3, "low_confidence": false }

# 6 — el endpoint nuevo de S10.
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"what did the client say in the meeting about Stripe checkout","top_k":3}' \
  | jq '{routing:.routing.level, targets:.routing.targets, technique}'
# → { "routing": "rules", "targets": ["transcript"], "technique": "expand" }
```

---


## Bloque 1 — Resolución de errores del pre-trabajo (15 min)

Los tres fallos típicos que los alumnos traen del **ejercicio previo** (búsqueda híbrida con RRF,
columna `content_tsv` y reranking con cross-encoder). No son bugs aislados: son **los tres cimientos
que el resto de la sesión reutiliza**, así que cierra cada fix señalando dónde reaparece.

- **1.1 RRF** → la misma fusión que volverá en expansión/descomposición (2.2).
- **1.2 **`**tsvector**` → la rama léxica del híbrido, presente en todo el pipeline.
- **1.3 reranking** → **es pre-work, no se reprograma hoy**: se *calienta* aquí, se *compone* como
etapa del pipeline avanzado (Bloque 2) y *alimenta* el consenso de horas por tarea (Bloque 3).
> **Recordatorio para el directo (no olvidar).** El cross-encoder (`reranker.py`) y el bloque
*recall-then-rerank* (`pipeline.py`) ya los construyeron los alumnos en el pre-work. En la Sesión
10 el reranking **nunca se re-implementa**: solo se **calienta** (1.3), se **compone** como etapa 6
del pipeline avanzado (2.1–2.3) y se **mide** en el arnés (filas C/D/E). Dilo en voz alta al
empezar el bloque para encuadrarlo; las referencias de código están en 1.3.

### 1.1 — Calibración de RRF (5 min)

**■ Fundamento · pizarra.** RRF fusiona por **posición**, no por puntuación:
`score(d) = Σ 1/(k + rank_i(d))`. La constante `k` (suavizado) decide cuánto pesa
ir primero: `k` grande aplana la curva (un documento debe ir bien en **ambas**
ramas para ganar); `k` pequeño deja que un único #1 domine. 60 es el valor del
paper de Cormack et al. y nuestro default — **no se optimiza salvo evidencia**.

**■ Qué aporta al estimador.** Los briefs de cliente y los presupuestos históricos están llenos de
*identificadores exactos* —`Stripe`, `SAP`, `Kubernetes`, códigos como `BUD-2024-014`— que el
embedding diluye en un vector “parecido a todo lo de pagos”. El híbrido + RRF hace que una query que cita “Stripe Connect” recupere el componente histórico que **realmente** usó Stripe, no uno genérico de pagos. Para nuestro grounding eso es directo: la estimación se ancla en el presupuesto correcto y evitamos engineer-days copiados de un proyecto con otra tecnología.

**■ Dónde vive.**
- `app/generation/rag/retrieval/fusion.py:23` — `reciprocal_rank_fusion(rankings, *, k=60)`.
Acepta **N rankings**, no solo dos: pieza de fusión universal del pipeline.
- `app/config.py` — `RRF_K: int = 60`.

> **Marcador de IDE.** Abre `fusion.py` y enseña que la entrada es
`list[list[int]]` (listas de ids, nunca puntuaciones crudas: no son comparables
entre el motor vectorial y `ts_rank_cd`).
**■ Demo · terminal.** Comparar híbrido vs vectorial sobre un identificador exacto
(“Stripe”) que el embedding diluye:

```bash
curl -s -X POST $B/v1/retrieval/search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"integration with Stripe Connect for vendor payouts","top_k":5,"search_mode":"hybrid"}' \
  | jq '[.chunks[] | {budget_id, distance}]'
```
**■ Contingencia.** Si el “wow” sale plano (corpus pequeño), apóyate en el test
`tests/test_rrf_fusion.py` que demuestra que un documento presente en ambas ramas
supera a los que solo aparecen en una.


### 1.2 — Configuración de idioma del `tsvector` (5 min)

**■ Fundamento · pizarra.** La columna generada `content_tsv` y la
`plainto_tsquery` de la consulta **deben usar la misma configuración de idioma**.
Si no coinciden, el índice GIN se ignora en silencio y el *matching* cambia sin
avisar. **La configuración debe seguir al idioma del corpus, no al del enunciado.**

> **Aha.** El enunciado dice “corpus en español”, pero el dataset que se sirve
(`data/budgets_sample.json`, transcripciones y docs) está **en inglés**. Por eso
el repo usa `english` de forma deliberada y documentada (ver migración 0003 y
`models.FTS_REGCONFIG`). El error del alumno suele ser poner `spanish` sobre
texto inglés (o viceversa): el stemming deja de funcionar.
**■ Qué aporta al estimador.** Es el cimiento silencioso de 1.1: alinear el `regconfig` es lo que
hace que la **rama léxica dispare** sobre esos identificadores exactos. Con un mismatch, el índice
GIN se ignora y el híbrido degrada a “solo vectorial” sin avisar → la evidencia con el token clave
(`Stripe`, `SAP`) se pierde y el LLM acaba estimando sin fuente. Es decir: 1.2 es lo que garantiza
que el grounding de 1.1 exista de verdad.

**■ Dónde vive.**
- `app/generation/rag/store/models.py` — `FTS_REGCONFIG = "english"` y la columna
`content_tsv` (`Computed("to_tsvector('english', content)", persisted=True)`).
- `app/generation/rag/store/repository.py` — `plainto_tsquery("english", query_text)`
en `search_lexical`. **Las dos referencias deben coincidir.**

**■ Demo · terminal.** Diagnóstico en psql:

```bash
docker compose exec estimator-postgres psql -U estimator -d estimator \
  -c "\d+ budget_chunks" | grep content_tsv
# → content_tsv ... GENERATED ALWAYS AS (to_tsvector('english'::regconfig, content)) STORED

docker compose exec estimator-postgres psql -U estimator -d estimator \
  -c "SELECT to_tsvector('english','Stripe Connect onboarding') @@ plainto_tsquery('english','stripe onboarding') AS matches;"
# → matches = t
```
**■ Contingencia.** Si un alumno tiene `spanish`: o re-stampa la columna generada
con `english`, o cambia ambas referencias a la vez. **Nunca una sola.**


### 1.3 — Reranking: cross-encoder y latencia en frío (5 min en vivo + referencia)

> **El reranking es del ejercicio previo, no se programa hoy.** En la sesión solo se *calienta* (este beat), se *compone* como etapa del pipeline avanzado (Bloque 2) y se *mide* en el arnés (2.3). El beat en vivo es corto (calentar el modelo); el resto de esta sección es **material de referencia y comentarios al mentor** sobre el reranking — léelo antes del directo, no lo dictes entero.
**■ Fundamento · pizarra.** El cross-encoder se carga **perezosamente** la primera
vez que se usa: la descarga + carga de pesos es un coste único de ~varias decenas
de segundos. En caliente, una pasada de reranking son ~cientos de ms — asumible
frente a los segundos que tarda la generación.

**■ Qué aporta al estimador.** El reranking es nuestra **palanca de precisión**. El patrón es
*recall-then-rerank*: lanzamos una red ancha y barata (`recall_k=50`) sobre presupuestos/tareas y un cross-encoder reordena por relevancia real, quedándonos el top-N (`rerank_top_n=5`). Eso mejora dos cosas a la vez en el proyecto: (1) el bloque `<source>` que alimenta la generación S09 contiene los presupuestos *más* parecidos, no solo “parecidos”; (2) los **vecinos del consenso de horas por tarea** (S10, Bloque 3) son los análogos correctos → `estimated_hours`/`reliability` más fiables y **menos filas rojas**. Sin rerank, el orden lo fija una distancia coseno que confunde “del mismo tema” con “de la misma forma”.

**■ Dónde vive.**
- `app/generation/rag/retrieval/reranker.py` — `CrossEncoderReranker`:
- `_ensure_loaded()` (`:58`) — singleton con *double-checked locking* (`threading.Lock`); loguea
`reranker_loaded` con `load_ms` la primera vez.
- `score(query, documents) -> list[float]` (`:77`) — construye los pares `(query, doc)` y delega en
`CrossEncoder.predict`; devuelve un **logit por documento** y loguea `reranker_scored`
(`pairs`, `score_ms`).
- `rerank_with_scores(...)` (`:97`) — devuelve `(chunk, logit)` ordenados desc (lo usa el pipeline
avanzado para exponer el logit crudo al sigmoid); `rerank(...)` (`:121`) — solo reordena y trunca.
- `from_settings()` (`:47`) — toma el modelo de `RERANKER_MODEL`.
- `app/generation/rag/retrieval/pipeline.py` (`:203`) — el bloque *recall-then-rerank* de
`retrieve()`: `recall_pool = ordered[:recall_k]` y
`await asyncio.to_thread(reranker.rerank, query_text, recall_pool, top_n=rerank_top_n)` — el
cross-encoder es **CPU-bound**, por eso va a un thread y no bloquea el event loop.
- `app/generation/rag/retrieval/advanced_pipeline.py` (`:263`, *etapa 6*) — `rerank_with_scores` → `_sigmoid(logit)` (`:128`) como **base no negativa**; rama `else` con score posicional `1/(pos+1)` cuando el rerank está apagado.
- `app/dependencies.py:69` — `get_reranker()` (`@lru_cache`; import perezoso de
`sentence_transformers`, por eso construirlo es barato y el *import-time* no paga torch).
- `app/config.py` — `RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"` (`:143`, multilingüe y CPU-friendly), `RERANKER_ENABLED=False` (`:141`, off por defecto),
`RETRIEVAL_RECALL_TOP_K=50` (`:146`), `RERANK_TOP_N=5` (`:147`).
- `app/foundation/llm/runtime_config.py` — `effective_rerank()` (`:192`) / `RERANK_KEY` (`:125`): toggle **en caliente** (Redis) desde la pestaña Ajustes → `PUT /api/v1/config/retrieval`.
- `tests/test_reranker.py` — prueban el orden descendente por logit, el truncado a top-N y el
extractor de texto inyectable con un `_FakeModel` (sin descargar torch).

> **Nota al mentor — bi-encoder vs cross-encoder.** El retriever (bi-encoder) embebe query y
documento **por separado** y compara vectores: barato, ideal para *recall* sobre miles de chunks. El cross-encoder los lee **juntos** en una sola pasada del transformer: mucho más preciso pero cuesta una inferencia **por par**, así que es imposible correrlo sobre todo el corpus. De ahí *recall-then-rerank*: el bi-encoder baja de miles a `recall_k=50`, y el cross-encoder afina esos 50.
> **Nota al mentor — por qué sigmoid antes del decaimiento.** El logit del cross-encoder puede ser **negativo**. El decaimiento temporal (2.3) es un multiplicador 0..1; si multiplicas un negativo, **inviertes** el orden. `_sigmoid` (advanced_pipeline.py:128) lleva el logit a (0,1) para que el decaimiento solo *atenúe*, nunca dé la vuelta al ranking. Es la razón de que el rerank exponga el logit crudo (`rerank_with_scores`) en lugar de reordenar a secas.
> **Nota al mentor — operativa y coste.** Off por defecto (`RERANKER_ENABLED=False`) porque añade latencia; se enciende **por request** (`"rerank": true`) o **en caliente** desde Ajustes para un A/B en vivo sin reiniciar. Primera consulta ~80s (carga única), luego ~cientos de ms: **siempre calienta con **`**verify_reranker**`** en el pre-flight**. En el arnés, las filas C/D/E ya cuantifican el *trade-off* (~+2.6s sobre el vectorial a cambio de precisión) — enséñalo, no lo escondas.
**■ Demo · terminal.** Calentar el modelo ANTES del bloque caliente:

```bash
docker compose exec estimator python -m app.generation.rag.retrieval.verify_reranker
```
**■ Contingencia.** Si la primera consulta con `rerank:true` tarda ~80s, es la
carga del modelo, no un cuelgue. Mantén el `verify_reranker` corrido en el
pre-flight para que en el directo el reranking ya esté caliente.

**■ Bridge.** “Con la base sana, subimos un piso: dejar de buscar en un único
índice y empezar a *decidir dónde* buscar.”


---


## Bloque 2 — Casos avanzados (90 min)

Antes de empezar, deja claro el orden de ensamblaje (Artículo 6): *lo barato y
excluyente al principio, lo caro y fino al final, lo blando al cierre.*

[image: sesion-10-slide-01-pipeline-orden_1.jpg](attachment:de5fc857-b8b0-4906-9171-504029da9835:sesion-10-slide-01-pipeline-orden_1.jpg)
**■ Dónde vive (el conductor).** `app/generation/rag/retrieval/advanced_pipeline.py`
— `advanced_retrieve(...)`. Cada etapa la gobierna un `StageConfig` (dataclass de
toggles). El endpoint la construye desde settings/runtime; el arnés la construye
como datos.


### Sub-bloque 2.1 — Multi-índice y routing en cascada (30 min)

**■ Fundamento · pizarra.** Un índice único mezcla texturas: el tipo dominante
(presupuestos) inunda el top-k y “¿cuánto costó SAP?” devuelve reuniones en vez de
presupuestos. Solución: **colecciones separadas** + **router en cascada por coste
creciente**:

[image: sesion-10-slide-02-routing-cascada.jpg](attachment:07c39318-cfd7-489a-9ac2-1669d11de2b5:sesion-10-slide-02-routing-cascada.jpg)
1. **Explícito** — el contrato del endpoint nombra las colecciones → no se clasifica.
1. **Reglas** — patrones de vocabulario deterministas.
1. **Clasificador LLM** — salida estructurada: 1–3 destinos (StrEnum cerrado) +
`reason` de una frase. *La duda se modela como varios destinos, no como umbral.*
1. **Fallback** — todas las colecciones en paralelo (degradación elegante).
**■ Qué aporta al estimador.** Nuestra evidencia es de tres naturalezas: presupuestos (cuánto costó), transcripciones (qué pidió el cliente) y docs técnicos (cómo se implementa). Con un índice único, los presupuestos —que son mayoría— inundan el top-k y una pregunta de alcance (“¿qué dijo el cliente sobre el checkout?”) devuelve presupuestos en vez de la reunión. El router manda cada intención a su colección, así que la estimación cita el **tipo de fuente correcto**: números desde budgets, alcance desde transcripts, decisiones técnicas desde docs.

**■ Dónde vive.**
- `app/generation/rag/store/models.py` — tres tablas: `BudgetChunkRow`, `TranscriptChunkRow`, `TechnicalDocChunkRow` (mixin `_ChunkColumns`; cada una con
su esquema de metadatos). `chunks` se renombró a `budget_chunks` (migración 0004).
- `app/generation/rag/retrieval/collections.py` — `Collection` (StrEnum) + el
registro `COLLECTIONS` (modelo, accesor de fecha, patrones de reglas, filtros).
- `app/generation/rag/retrieval/router.py:74` — `route(...)`, la cascada. Cada
decisión se loguea con `level` y `reason`.

> **Marcador de IDE.** En `router.py`, enseña los cuatro niveles y el log
`routing_decided`. En `collections.py`, enseña `match_rules` (nivel 1) y que la
**etiqueta de procedencia** viaja en cada chunk (`RetrievedChunk.collection`).
**■ Demo · terminal.**

```bash
# (a) Nivel 1 — reglas: vocabulario de reunión → transcript, sin LLM.
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"what did the client say in the meeting about Stripe checkout","top_k":4}' \
  | jq '{level:.routing.level, targets:.routing.targets, cardinality}'
# → level "rules", targets ["transcript"]

# (b) Nivel 2 — clasificador: sin vocabulario de routing → LLM decide y razona.
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"OAuth 2.0 PKCE flow and PSD2 strong customer authentication reference","top_k":3}' \
  | jq '{level:.routing.level, targets:.routing.targets, reason:.routing.reason}'
# → level "classifier", targets ["technical_doc"], reason "...internal technical documentation."

# (c) Nivel 0 — explícito: el contrato manda, no se clasifica.
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"telemedicine appointment scheduling","collections":["budget"],"top_k":3}' \
  | jq '{level:.routing.level, targets:.routing.targets}'
# → level "explicit", targets ["budget"]
```
**■ Contingencia.** *El clasificador que duda*: si devuelve demasiados destinos,
recuérdales que la duda se modela como varios destinos (no es un bug) y que el
`max_targets` (3) lo acota. Si el LLM falla, la cascada degrada a **fallback**
(todas) — nunca peor que el índice único. Demuéstralo apagando el routing:
`"routing_enabled": false` fuerza… (en realidad el fallback se ve si reglas y
clasificador no disparan; para forzar fallback usa una query sin vocabulario y con
el clasificador caído).


### Sub-bloque 2.2 — Expansión y descomposición (30 min)

**■ Fundamento · pizarra.** Dos técnicas que **no** son intercambiables. La
pregunta distintiva: *¿una cosa dicha de muchas maneras, o muchas cosas dichas a la
vez?*
- **Expansión (multi-query):** N formulaciones de la **misma** intención → combate
la lotería del vocabulario. Fusión por **consenso (RRF)**.
- **Descomposición:** sub-consultas independientes **por tema** → combate el
embedding promedio de una transcripción multi-tema. Fusión por **cobertura
(round-robin con dedup)**, porque premiar consenso dejaría temas sin representar.

[image: sesion-10-slide-03-expansion-descomposicion.jpg](attachment:bdc7b2d8-0db6-4cf6-8bb3-65fde1a111dc:sesion-10-slide-03-expansion-descomposicion.jpg)
**■ Qué aporta al estimador.** La entrada real del pipeline S09 es una **transcripción de cliente**:
divagante y multi-tema (“necesitamos login, y cobros con Stripe, y recomendaciones de catálogo”). Un solo embedding de todo eso queda “cerca de todo, lejos de nada” y recupera evidencia floja. La **descomposición** busca por tema y garantiza que **cada módulo** del desglose tenga su evidencia, no solo el dominante; la **expansión** salva el desajuste de vocabulario (el cliente dice “carrito”, el corpus “checkout flow”). Resultado: estimaciones ancladas módulo a módulo, no solo en la parte más ruidosa del brief.

**■ Dónde vive.**
- `app/generation/rag/retrieval/query_transform.py` — `choose_technique()`
(heurística por longitud/conectores), `transform_query()` (salida estructurada
`QueryTransformation`, máx 4 sub-consultas en el esquema **y** en las
instrucciones “de correa corta”: conservar términos exactos, no inventar).
- `app/generation/rag/retrieval/fusion.py` — `reciprocal_rank_fusion` (expansión) y
`round_robin_merge` (descomposición).
- `advanced_pipeline.py` — `_fuse_collection(...)` elige la fusión según la técnica.

> **Marcador de IDE.** En `query_transform.py`, enseña que un solo cambio decide la
técnica (`choose_technique`) y que la decisión se loguea (`query_transform_decided`).
En `_fuse_collection`, enseña las dos ramas de fusión.
**■ Demo · terminal.** Una transcripción multi-tema dispara descomposición:

```bash
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"we need OAuth and a transaction ledger, plus a Stripe checkout, and also personalized recommendations for the product catalog","collections":["budget"],"top_k":5}' \
  | jq '{technique, subqueries:[.subqueries[].topic], n:(.chunks|length)}'
# → technique "decompose", subqueries listadas por tema

# Una consulta corta de un solo tema pasa directa (sin LLM):
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"Stripe checkout","collections":["budget"],"top_k":3}' \
  | jq '{technique, subqueries:[.subqueries[].query]}'
# → technique "direct"
```
**■ Contingencia.** Si la expansión/descomposición falla (timeout LLM), el pipeline
**degrada a una consulta directa** — la recuperación nunca depende del
transformador. Demuéstralo apagándolo: `"query_transform_enabled": false`.


### Sub-bloque 2.3 — Filtros duros, decaimiento temporal y comparativa (30 min)

**■ Fundamento · pizarra.** Los metadatos en dos usos:
- **Filtro duro** (excluye **antes** de buscar): empotrado en la consulta `WHERE` +
vector. *Trampa del post-filtrado con HNSW*: puede vaciar el resultado en silencio
→ **siempre logueamos la cardinalidad** tras el filtro.
- **Ponderación blanda** (reordena finalistas, **al cierre**): decaimiento temporal
exponencial `weight = 0.5 ** (age_days / half_life)`, semivida 900 días por
defecto. Se aplica **después** del reranking, nunca antes.

[image: sesion-10-slide-04-filtros-decaimiento.png](attachment:371662a1-26a2-4350-aa81-0c188df16961:sesion-10-slide-04-filtros-decaimiento.png)
**■ Qué aporta al estimador.** Las dos piezas controlan *con qué proyectos comparamos*. El **filtro
duro** mantiene el grounding en proyectos **comparables**: estimar una clínica con presupuestos de
healthcare de 2024, no con un ecommerce de 2019. El **decaimiento temporal** prefiere suavemente lo reciente, para que las tarifas y el esfuerzo reflejen la realidad de hoy **sin descartar** evidencia antigua válida (solo desempata). Para nuestras horas por tarea, esto evita anclar en un análogo barato pero viejo cuando existe uno reciente igual de parecido.

> **Nota al mentor — el orden importa (fusión → reranking → decaimiento).** Es la cadena de
`advanced_pipeline.py`: la **fusión** junta candidatos, el **reranking** (etapa 6, `:263`) fija el
orden por *relevancia* real, y el **decaimiento** (`:279`) solo *atenúa* a los finalistas por edad.
Invertir el orden rompería el grounding: si decayeras antes de rerankear, penalizarías por fecha
documentos que aún no sabes si son relevantes. Y recuerda el sigmoid (1.3): el decaimiento
multiplica sobre la base `_sigmoid(logit)` ∈ (0,1), nunca sobre un logit que podría ser negativo.
**■ Dónde vive.**
- `collections.py` — `HardFilters` y `CollectionSpec.hard_filter_clauses(...)` (cada
colección solo entiende los ejes que le aplican).
- `app/generation/rag/store/repository.py` — `search_filtered(... extra_filters=...)`
devuelve `candidates_evaluated` (la cardinalidad a vigilar).
- `app/generation/rag/retrieval/temporal.py` — `apply_temporal_decay(...)` (función
pura). El score base del cross-encoder se pasa por `sigmoid` para que el
multiplicador 0..1 no invierta el orden (ver `advanced_pipeline._sigmoid`).

> **Marcador de IDE.** En `temporal.py`, enseña la fórmula y el guard de fecha
futura/inexistente (peso 1.0). En `advanced_pipeline.py`, enseña el log
`advanced_collection_cardinality`.
**■ Demo · terminal.**

```bash
# Filtro duro por fecha: solo presupuestos de 2024 → cardinalidad baja de 60 a 42.
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"telemedicine scheduling and video consultations","collections":["budget"],"min_date":"2024-01-01","top_k":3}' \
  | jq '{cardinality, years:[.chunks[].project_year]|unique}'
# → cardinality {"budget":42}, years [2024]

# Decaimiento temporal + reranking: las fuentes recientes rompen empates.
curl -s -X POST $B/v1/retrieval/advanced-search -H "X-API-Key:$K" -H "Content-Type: application/json" \
  -d '{"query_text":"SAP integration with IDoc BAPI for predictive maintenance","rerank":true,"temporal_decay_enabled":true,"top_k":4}' \
  | jq '[.chunks[] | {collection, source_id, score:.relevance_score}]'
```
**■ Reproducir la comparativa cuantitativa (el arnés).**

El arnés ejecuta **configuraciones nominadas como datos** (no ramas de código),
cada una un `StageConfig`, contra el golden set, y produce la tabla
precisión@5 / latencia. Las filas A–D son las del pre-trabajo; E–H añaden las
técnicas nuevas.

```bash
# Las TRES colecciones deben estar ingestadas. Se corre dentro del contenedor
# (donde está la API key del .env y el reranker ya cargado):
docker cp evals/golden_retrieval.json estimator:/app/evals/golden_retrieval.json
docker compose exec estimator python scripts/eval_retrieval_s10.py
```
[image: sesion-10-slide-05-arnes-lectura-honesta.png](attachment:91cc4b0f-630d-477a-807a-8ecc828a1c55:sesion-10-slide-05-arnes-lectura-honesta.png)
Salida (Markdown): una tabla `Config | Stages | Precision@5 | Latency (ms)` y la
matriz por query. El relato del directo es **extender la tabla del alumno**: A–D ya
las traen; añadimos routing (F), transform (G), decaimiento (E) y el pipeline
completo (H), y se discute la **ganancia de precisión frente a la latencia
añadida** (las filas con LLM de routing/transform incluyen ese coste — es
justamente la parte del presupuesto que la técnica gasta).

> **Marcador de IDE.** Abre `scripts/eval_retrieval_s10.py` y enseña `CONFIGS`: cada
fila es un `NamedConfig` con su `StageConfig`. Añadir una medición = añadir una
fila de datos.
**■ Contingencia.** *El filtro que vacía resultados*: si una demo devuelve
`low_confidence: true` y `cardinality: {...: 0}`, es el filtro duro vaciando en
silencio — el log lo detecta. Súbelo/relájalo en el momento (`min_date` o
`doc_version`).

**■ Bridge a Bloque 3.** “Ya tenemos un motor de recuperación que decide dónde y
cómo buscar. Ahora lo ponemos al servicio de una decisión de negocio concreta:
estimar las horas de cada tarea desde dato histórico, con el humano en el lazo.”


---


## Bloque 3 — Del retrieval al producto: estimación por tarea con human-in-the-loop (25–30 min)

**Cambio de flujo (anúncialo de entrada).** Hasta ahora la estimación RAG (S09)
generaba en un solo disparo módulos→tareas **con las horas inferidas por el LLM**.
A partir de esta sesión el flujo se invierte y mete al humano en el lazo en dos
puntos:

```plain text
generación (SOLO estructura, sin horas)
  → revisión humana #1 (editar módulos/tareas)
  → horas por BÚSQUEDA VECTORIAL por tarea (consenso + fiabilidad; rojo si no hay análogo)
  → revisión humana #2 (editar horas y tarifas €/h) → confirmar y almacenar
```
El `POST /v1/estimate/from-transcript` de S09 **se mantiene intacto** (horas inline)
como contrato público y comparación pedagógica: *el LLM las infiere* vs *las
derivamos de evidencia recuperada*.


### Sub-bloque 3.1 — Por qué separar estructura de horas (5 min)

**■ Fundamento · pizarra.** Un LLM es bueno *descomponiendo* (qué módulos, qué
tareas) y malo *poniendo números* sin anclaje: inventa horas plausibles pero no
trazables. Separamos las dos decisiones. La estructura la propone el modelo; las
horas las **recupera** de proyectos históricos análogos (el mismo problema de
retrieval del Bloque 2, ahora una query por tarea). El humano valida en cada
frontera. Resultado: cada número o lleva *evidencia histórica + score de fiabilidad*
o queda **marcado en rojo** para que una persona lo decida.

[image: sesion-10-slide-06-human-in-the-loop.png](attachment:6a35325b-5a2e-4c92-a92b-981a7d105d99:sesion-10-slide-06-human-in-the-loop.png)

### Sub-bloque 3.2 — Generación estructura-only + Revisión #1 (8 min)

**■ Fundamento · pizarra.** La generación gana un flag `include_hours`. En `False`
el prompt cambia: “propón módulos y tareas, **NO** estimes horas; deja
`engineer_days` y `total_engineer_days` en null”. `TaskItem.engineer_days` pasa a
opcional para que el esquema valide sin números.

**■ Dónde vive.**
- `app/generation/rag/prompt_builder.py::build_system_prompt(include_hours=False)` — el prompt estructura-only.
- `app/generation/rag/estimator.py::generate_estimate(..., include_hours=...)` — propaga el flag.
- `app/api/routers/estimate_stages.py` (`GenerateRequest.include_hours`, default `True`) — el wizard lo invoca con `false`; S09 conserva el comportamiento.
- `app/generation/rag/schemas.py::TaskItem.engineer_days` (ahora `int | None`).

**■ Demo · terminal.** La estructura sale sin horas:

```bash
curl -s -X POST $B/v1/estimate/stages/generate -H "X-API-Key: demo-estimate-key" \
  -H "Content-Type: application/json" \
  -d '{"context_block":"<source id=\"1\">Auth & RBAC ~32h</source>","query":{"function":"B2B portal"},"kept_chunks":[],"include_hours":false}' \
  | jq '{conf:.estimate.confidence, tasks:[.estimate.modules[].tasks[] | {name, engineer_days}]}'
# → engineer_days: null en cada tarea
```
**▶ UI Rails — paso «Estructura» y «Revisión».** En el wizard
(`app/views/rag/estimation_runs/_step_generation.html.erb`) la pantalla 4 ya no
muestra total/horas: solo módulos→tareas y la confianza. El botón lleva a
**Revisión** (`_step_review.html.erb`): rejilla **editable** (reutiliza el editor
Stimulus `estimate_modules_editor_controller.js` en `mode: :structure`) para
añadir/eliminar/renombrar antes de pagar la búsqueda. El controlador
(`Rag::EstimationRunsController#generate`) llama `generate(include_hours: false)` y
siembra la columna `structure`.


### Sub-bloque 3.3 — Horas por tarea vía búsqueda vectorial (12 min) — el pago del Bloque 2

**■ Fundamento · pizarra.** Por cada tarea: componer texto → embeber →
`search_chunks(chunk_types=["historical_task"])` sobre el corpus de tareas →
**consenso ponderado por distancia** de los *k* vecinos:
`horas = Σ wᵢ·hᵢ / Σ wᵢ` con `wᵢ = 1/(ε+dᵢ)`, y
`fiabilidad = similitud_ponderada · (1 − dispersión)` — alta solo si los vecinos
están *cerca* y *de acuerdo*. Si ningún vecino cruza el umbral → **sin horas,
**`**has_match=false**`**, rojo**. Es el retrieval del Bloque 2 reutilizado: el umbral es el
`distance_threshold` de siempre, ahora como *piso de fiabilidad*.

> **Vínculo con el reranking (1.3/2.3).** La calidad del consenso depende de **qué** vecinos entran.
Con `rerank` activo, los *k* vecinos de cada tarea no son los “más cercanos en coseno” sino los que
el cross-encoder juzga **realmente** más parecidos (recall ancho → cross-encoder → top-N), así que
`estimated_hours` se promedia sobre los análogos correctos y `reliability` sube. En la práctica:
activar reranking aquí (`RERANKER_ENABLED` en Ajustes) **reduce los rojos** y estabiliza el número
— es el caso de negocio más tangible de toda la palanca de precisión del Bloque 1.3. Demuéstralo en
vivo: misma tarea con `rerank` off vs on y compara los `neighbors`.
**■ Dónde vive.**
- `app/generation/rag/task_hours.py` — `compose_task_search_text`, `_consensus` (función pura, testeable), `estimate_one`, `estimate_all` (fan-out `asyncio.gather`).
- `app/generation/rag/schemas.py` — `TaskHoursEstimate` / `TaskNeighbor` / `TaskHoursRequest` / `TaskHoursResult`, y `RetrievedChunk.estimated_hours` (antes se descartaba; ahora `to_chunk`/`search_chunks` lo exponen desde la metadata JSONB).
- `app/api/routers/estimate_tasks.py` — `POST /v1/estimate/tasks/hours` (auth `ESTIMATE_API_KEY`, 30/min).
- Corpus: `scripts/build_task_corpus.py` (`document_type='historical_task_breakdown'`, `chunk_type='historical_task'`, con `estimated_hours` por tarea). Default ampliado a **60 proyectos / ~1.500 tareas sobre 8 sectores** (incluye logística, educación, media y administración pública) → más vecinos por tarea y menos rojos; `--count`/`--seed` lo ajustan.

**■ Demo · terminal.** Una tarea con análogo (fiabilidad alta) y una inventada (rojo):

```bash
curl -s -X POST $B/v1/estimate/tasks/hours -H "X-API-Key: demo-estimate-key" \
  -H "Content-Type: application/json" \
  -d '{"modules":[{"name":"Payments & Billing","tasks":[
        {"name":"Payment gateway integration","description":"Card payments via a PSP with 3-D Secure"},
        {"name":"Quantum teleporter","description":"nonexistent"}]}]}' \
  | jq '.tasks[] | {task, estimated_hours, reliability, has_match}'
# → la 1ª con estimated_hours+reliability; la 2ª has_match:false, estimated_hours:null
```
**■ Contingencia.** *Todas las tareas en rojo* → el umbral está demasiado tieso o
el corpus de tareas no está ingestado. Sube `TASK_HOURS_DISTANCE_THRESHOLD` en
caliente (Ajustes → `PUT /api/v1/config/retrieval`) o corre
`build_task_corpus.py --ingest`. *Horas absurdamente altas/bajas* → mira los
`neighbors`: el consenso es trazable, no una caja negra.

**▶ UI Rails — paso «Horas».** `_step_hours.html.erb` lista las tareas con badge de
fiabilidad (verde/ámbar) y **fila roja** para las `flagged?`; arriba, el recuento
`matched / sin dato`. El controlador (`#estimate_hours`) persiste la `structure`
revisada, llama `estimate_task_hours`, guarda `task_hours` y siembra el borrador de
coste.


### Sub-bloque 3.4 — Revisión #2: horas, tarifas y confirmación (5 min)

**■ Fundamento · pizarra.** Última palabra humana: editar horas (rellenar los
rojos) y la **tarifa €/h** por tarea; el coste (`horas × tarifa`) y el total se
recalculan al vuelo. Al confirmar, se almacena la estimación (`confirmed_at`).

**■ Dónde vive (UI).**
- `app/views/rag/estimation_runs/_step_verification.html.erb` + `_editable_task.html.erb` (`mode: :cost`) — columnas horas/€/h/coste + badge + resaltado rojo.
- `app/javascript/controllers/estimate_modules_editor_controller.js::recompute` — ahora `coste = horas × tarifa`, total en €.
- `Rag::EstimationRunsController#verify` — recomputa el total **en servidor** y persiste `adjusted_breakdown` (`total_hours`, `total_cost_eur`, `confirmed_at`).

**■ Knobs en caliente.** `TASK_HOURS_TOP_K` y `TASK_HOURS_DISTANCE_THRESHOLD` viven
en `RuntimeRetrievalConfig` → pestaña Ajustes (`PUT /api/v1/config/retrieval`), como
el resto de toggles de S10: se calibran a mitad de directo sin reiniciar.

**■ Bridge a S11.** “Este router acotado —clasificación cerrada, sin razonamiento
abierto ni herramientas— y este lazo humano explícito son el precursor del
*handover* agéntico de la próxima sesión.”


---


## Bloque 4 — Cierre (5 min)

Hemos pasado de “buscar en todas partes con un índice” a un pipeline que **decide
dónde buscar (routing), cómo preguntar (expansión/descomposición), qué excluir
(filtros duros) y cómo desempatar (decaimiento)** — cada etapa medible y conmutable —
y, sobre ese motor, un **flujo de estimación con humano en el lazo** que separa
estructura de horas y ancla cada número en dato histórico con su fiabilidad.
La rama `session_10_live` recoge todo el código de referencia.


---


## Apéndice ejecutivo (para el mentor)


### Resumen por bloque

| # | Bloque | Min | Demo clave |
|---|---|---|---|
| 1.1 | Calibración RRF | 5 | híbrido vs vectorial sobre “Stripe” |
| 1.2 | Idioma del tsvector | 5 | `\d+ budget_chunks` + `plainto_tsquery` |
| 1.3 | Reranking (cross-encoder) + latencia en frío | 5 | `verify_reranker`; refs de código + notas al mentor |
| 2.1 | Routing multi-índice | 30 | reglas / clasificador / explícito |
| 2.2 | Expansión y descomposición | 30 | query multi-tema → `decompose` |
| 2.3 | Filtros + decaimiento + arnés | 30 | `min_date` baja cardinalidad; tabla del arnés |
| 3.1 | Por qué separar estructura de horas | 5 | inferir vs recuperar (pizarra) |
| 3.2 | Estructura-only + Revisión #1 | 8 | `/stages/generate include_hours=false`; UI editable |
| 3.3 | Horas por tarea (búsqueda vectorial) | 12 | `/v1/estimate/tasks/hours`: match vs rojo |
| 3.4 | Revisión #2: horas/tarifas + confirmar | 5 | coste €, `confirmed_at` |

### Tabla de errores previsibles

| Síntoma | Causa | Arreglo |
|---|---|---|
| `up` falla: container name conflict | contenedor de otra rama con nombre fijo | `docker rm -f estimator estimator-redis estimator-postgres` y `up` |
| `up` falla: port 5433 in use | otro Postgres ocupa el puerto host | parar el otro contenedor o liberar el puerto |
| Embeddings 429 `insufficient_quota` | `OPENAI_API_KEY` del shell pisa la del `.env` | `unset OPENAI_API_KEY` o correr dentro del contenedor |
| Primera consulta con `rerank` ~80s | carga en frío del cross-encoder | `verify_reranker` en el pre-flight |
| `low_confidence:true` + cardinalidad 0 | filtro duro vacía la colección | relajar `min_date`/`doc_version`; mirar el log de cardinalidad |
| Léxico no encuentra identificadores | mismatch de regconfig tsvector/tsquery | alinear ambos a `english` |
| (B3) Todas las tareas en rojo | corpus `historical_task` sin ingestar, o umbral muy tieso | `build_task_corpus.py --ingest`; subir `TASK_HOURS_DISTANCE_THRESHOLD` en Ajustes |
| (B3) Generación con horas pese al flag | `include_hours` no llega como `false` | el wizard lo envía; verifícalo en el log `generation` (`include_hours=false`) |

### Artefactos nuevos / modificados

| Artefacto | Rol |
|---|---|
| `alembic/versions/0004_session10_multi_index.py` | rename `chunks`→`budget_chunks` + 2 tablas nuevas |
| `app/generation/rag/store/models.py` | mixin `_ChunkColumns` + 3 modelos (alias `ChunkRow`) |
| `app/generation/rag/retrieval/collections.py` | registro de colecciones (modelo, fecha, reglas, filtros) |
| `app/generation/rag/retrieval/router.py` | routing en cascada |
| `app/generation/rag/retrieval/query_transform.py` | expansión/descomposición |
| `app/generation/rag/retrieval/temporal.py` | decaimiento temporal |
| `app/generation/rag/retrieval/fusion.py` | `round_robin_merge` (añadido) |
| `app/generation/rag/retrieval/advanced_pipeline.py` | conductor del pipeline avanzado |
| `app/api/routers/retrieval_advanced.py` | `POST /v1/retrieval/advanced-search` |
| `data/transcripts_sample.json`, `data/technical_docs_sample.json` | corpus de ejemplo |
| `scripts/build_multi_index_corpus.py` | ingesta de las colecciones nuevas |
| `scripts/eval_retrieval_s10.py` | arnés con configuraciones nominadas |
| `evals/golden_retrieval.json` | golden set extendido (multi-colección) |
| **(B3)** `app/generation/rag/task_hours.py` | horas por tarea: consenso ponderado + fiabilidad |
| **(B3)** `app/api/routers/estimate_tasks.py` | `POST /v1/estimate/tasks/hours` |
| **(B3)** `app/generation/rag/prompt_builder.py` | `build_system_prompt(include_hours=False)` (estructura-only) |
| **(B3)** `app/generation/rag/schemas.py` | `TaskHoursEstimate/Neighbor/Request/Result`, `RetrievedChunk.estimated_hours`, `TaskItem.engineer_days` opcional |
| **(B3 cliente)** `estimator-web` wizard | pasos `review`/`hours` + verificación de coste (migración `task_hours`/`structure`, POROs `TaskHours*View`, editor Stimulus en € ) |

### Settings nuevas (todas conmutables en caliente vía `PUT /api/v1/config/retrieval`)

`RETRIEVAL_ROUTING_ENABLED`, `QUERY_TRANSFORM_ENABLED`, `TEMPORAL_DECAY_ENABLED`,
`ROUTER_MODEL`, `QUERY_TRANSFORM_MODEL`, `TEMPORAL_DECAY_HALF_LIFE_DAYS`,
`QUERY_MAX_SUBQUERIES`, `ROUTER_MAX_TARGETS` (+ las de S10 pre-trabajo:
`RETRIEVAL_SEARCH_MODE`, `RERANKER_ENABLED`, `RRF_K`, `RETRIEVAL_RECALL_TOP_K`,
`RERANK_TOP_N`). **Bloque 3:** `TASK_HOURS_TOP_K`, `TASK_HOURS_DISTANCE_THRESHOLD`
(umbral del rojo) — también conmutables en caliente.

> **Rebalanceo de tiempo (120 min).** Con el Bloque 3 (~30 min) añadido, comprime
la comparativa del arnés (2.3): muestra la tabla ya calculada en vez de
re-ejecutarla en vivo, y lleva el Bloque 3 mayormente como *walkthrough + demo*.
El núcleo del directo siguen siendo los Bloques 1–2; el 3 es el cierre-aplicación.

### Números de referencia (corpus de ejemplo)

- Cardinalidades: budget 60 chunks, transcript 11, technical_doc 8.
- Filtro `min_date:2024` sobre budgets: 60 → 42 candidatos.
- Reranker en frío: ~80s la primera carga; en caliente ~cientos de ms.
Tabla real del arnés (`eval_retrieval_s10.py`, corpus de ejemplo; los absolutos
varían con la API y la máquina):

| Config | Stages | Precision@5 | Latency (ms) |
|---|---|---|---|
| A | Vector | 0.75 | 197 |
| B | Hybrid | 0.75 | 204 |
| C | Vector+Rerank | 0.75 | 2861 |
| D | Hybrid+Rerank | 0.75 | 3273 |
| E | Hybrid+Rerank+Temporal | 0.75 | 2952 |
| F | Multi-index routing | 0.25 | 1593 |
| G | Query transform | 0.75 | 9931 |
| H | Full pipeline | 0.25 | 6585 |
> **Lectura honesta (úsala en el directo, no la escondas).** El golden set mezcla
5 queries budget-only (Q1–Q5) con 3 cross-colección (Q6–Q8). El **routing** (F,
H) **mejora** las cross-colección (Q7 0.60→0.80, Q8 0.00→0.40: encuentra el
transcript/doc que el índice único nunca vería) pero **hunde** las queries de
descripción de proyecto (Q1–Q5 → 0.00): no contienen vocabulario de routing
(“budget”/“cost”), así que el clasificador las manda a transcript/doc y se pierde
los presupuestos. **Moraleja del directo:** una técnica no es universalmente
buena; el routing ayuda cuando la query *señala* su tipo, y por eso el nivel-0
(colección explícita) y un buen golden set por caso de uso importan. El
reranking (C/D/E) cuesta ~2.6s sobre el vectorial; la expansión (G) ~10s por el
LLM — la latencia que pesa frente a la ganancia.