# Sesión 10 — Técnicas avanzadas de recuperación (contexto)

> Edición 2026-09 · miércoles 11/11/2026, 17:30–19:30 · Mentor: Julián · TA: George Kutsia.
> Primera vez que Julián da esta sesión. Las S8 (bases de datos vectoriales) y S9 (fundamentos de RAG)
> las dio Juan Pablo Mesa: los alumnos llegan con pgvector, retrieval con filtros y el estimate RAG hechos.
> Fuente: Notion de LIDR (exportado a `LIDR\edicion-26-09\s10-tecnicas-avanzadas-de-recuperacion\`).

## 1. De qué va

De "buscar en todas partes con un índice" a un pipeline que **decide dónde buscar** (routing),
**cómo preguntar** (expansión / descomposición), **qué excluir** (filtros duros) y **cómo desempatar**
(decaimiento temporal), con cada etapa **medible y conmutable**. Y, como cierre-aplicación, el flujo de
estimación pasa a **separar estructura de horas**: el LLM propone módulos y tareas, un humano los revisa,
las horas salen de **búsqueda vectorial por tarea** (consenso + fiabilidad, rojo si no hay análogo) y un
segundo humano edita horas y tarifas.

**Regla de oro:** cada etapa entra una lista de chunks y sale una lista de chunks; un toggle la enciende o
la apaga sin tocar código. El pipeline completo es el camino máximo, no el obligatorio.

**El orden del pipeline es el mensaje:** lo barato y excluyente al principio (filtros), lo caro y fino al
final (reranking), lo blando al cierre (decaimiento).

```
reformular → routing → filtros duros → búsqueda (semántica + léxica) → fusión (RRF / RR) → reranking → decaimiento → top-k
```

## 2. Ejercicio previo (rama `session_10`)

Sobre lo de la S9, los alumnos traen:

- **Búsqueda híbrida**: columna generada `content_tsv` (`to_tsvector('english', content)`, migración 0003)
  + `plainto_tsquery('english', …)` + fusión **RRF** (`retrieval/fusion.py`, `k = 60`).
- **Reranking** con cross-encoder (`retrieval/reranker.py`, `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`),
  patrón *recall-then-rerank*: `recall_k = 50` → `rerank_top_n = 5`. Off por defecto; carga en frío ~80 s.
- **Arnés** `scripts/eval_retrieval_s10.py` + golden set `evals/golden_retrieval.json` (precision@5 y latencia).

Errores típicos que traen (Bloque 1): calibración de RRF, **idioma del tsvector** (el corpus está en
inglés aunque el enunciado diga español: `spanish` sobre texto inglés rompe el stemming en silencio) y el
reranking (que hoy no se reprograma: se calienta, se compone y se mide).

## 3. El directo (rama `session_10_live`) · 120 min

| # | Bloque | Min | Demo clave |
|---|---|---|---|
| 1.1 | Calibración de RRF | 5 | híbrido vs vectorial sobre "Stripe Connect" |
| 1.2 | Idioma del tsvector | 5 | `\d+ budget_chunks` + `plainto_tsquery` en psql |
| 1.3 | Reranking: cross-encoder y latencia en frío | 5 | `verify_reranker` (calentar antes de clase) |
| 2.1 | Multi-índice y routing en cascada | 30 | reglas / clasificador LLM / explícito |
| 2.2 | Expansión y descomposición | 30 | transcripción multi-tema → `decompose` |
| 2.3 | Filtros duros + decaimiento + arnés | 30 | `min_date` baja la cardinalidad 60 → 42; tabla del arnés |
| 3.1 | Por qué separar estructura de horas | 5 | pizarra: inferir vs recuperar |
| 3.2 | Estructura sin horas + revisión #1 | 8 | `/stages/generate` con `include_hours=false` |
| 3.3 | Horas por tarea vía búsqueda vectorial | 12 | `/v1/estimate/tasks/hours`: análogo vs rojo |
| 3.4 | Revisión #2: horas, tarifas, confirmar | 5 | wizard de Rails, coste en € |

Si falta tiempo: enseñar la tabla del arnés ya calculada y llevar el Bloque 3 como recorrido + demo.

### 3.1 Multi-índice y routing

- Tres colecciones en tablas separadas: `budget_chunks` (cuánto costó), `transcript_chunks` (qué pidió el
  cliente) y `technical_doc_chunks` (cómo se implementa). Migración `0004_session10_multi_index`.
- Router en cascada por coste creciente (`retrieval/router.py`): **0 explícito** (el llamante nombra la
  colección) → **1 reglas** de vocabulario → **2 clasificador LLM** (1–3 destinos + `reason`; la duda se modela
  como varios destinos) → **3 fallback** (todas, nunca peor que el índice único).

### 3.2 Expansión y descomposición (`retrieval/query_transform.py`)

- **Expansión (multi-query):** una intención dicha de varias formas → fusión por **consenso (RRF)**.
- **Descomposición:** varios temas a la vez (transcripción) → sub-consultas por tema → fusión por
  **cobertura (round-robin)**.
- Si el LLM falla, degrada a consulta directa.

### 3.3 Filtros duros y decaimiento temporal

- **Filtro duro**: excluye antes de buscar (en el `WHERE`). Trampa del post-filtrado con HNSW: puede vaciar
  el resultado en silencio → siempre se loguea la cardinalidad.
- **Decaimiento**: `weight = 0.5 ** (age_days / half_life)`, semivida 900 días; se aplica **después** del
  reranking, sobre `sigmoid(logit)` para no invertir el orden.

### 3.4 Horas por tarea (`app/generation/rag/task_hours.py`)

`horas = Σ wᵢ·hᵢ / Σ wᵢ` con `wᵢ = 1/(ε+dᵢ)`; `fiabilidad = similitud_ponderada · (1 − dispersión)`.
Sin vecino bajo el umbral (`TASK_HOURS_DISTANCE_THRESHOLD`) → sin horas, `has_match=false`, fila roja.
Corpus `historical_task`: 60 proyectos / ~1.500 tareas en 8 sectores (`scripts/build_task_corpus.py`).

## 4. Números de referencia (guion de LIDR)

- Cardinalidades: budget 60, transcript 11, technical_doc 8. Filtro `min_date 2024`: 60 → 42.

| Config | Etapas | Precision@5 | Latencia |
|---|---|---|---|
| A | Vector | 0,75 | 197 ms |
| B | Hybrid | 0,75 | 204 ms |
| C | Vector + Rerank | 0,75 | 2861 ms |
| D | Hybrid + Rerank | 0,75 | 3273 ms |
| E | Hybrid + Rerank + Temporal | 0,75 | 2952 ms |
| F | Multi-index routing | **0,25** | 1593 ms |
| G | Query transform | 0,75 | 9931 ms |
| H | Full pipeline | **0,25** | 6585 ms |

**Lectura honesta:** el routing mejora las consultas que cruzan colecciones (Q7 0,60 → 0,80; Q8 0,00 → 0,40)
pero hunde las de descripción de proyecto (Q1–Q5 → 0,00): no dicen "budget/cost" y el clasificador las manda a
transcript/doc. Una técnica no es universalmente buena; por eso importan el nivel 0 (colección explícita) y un
golden set por caso de uso.

## 5. En local

Worktree `ai-engineering-fork-julian\ai-engineering-s10` (rama `session_10_live_local` desde
`origin/session_10_live`), proyecto `aieng-s10live`, contenedores `s10-*`. Mismos parches que la S7
(commit cherry-pickeado): Dockerfile con torch CPU + `es_core_news_md` + NLTK, override `s10-*`.
`.env` del servicio IA con la clave de OpenAI y `RETRIEVAL_API_KEY=demo-retrieval-key`,
`ESTIMATE_API_KEY=demo-estimate-key`; `estimator-web/.env` con esas dos claves para el wizard.

## 6. Material de LIDR

- Guion completo del directo: [`guion-directo.md`](guion-directo.md) (copia del Notion con notas locales).
- 6 diapositivas oficiales del guion (1920×1080): `deck/slides-lidr/`.
- Las Google Slides de la sesión no se pueden abrir con las cuentas personales de Julián (piden acceso).
- Sesión con mejor ROTI: edición 2026-04, Antonio Pérez (4,50).

## 7. Material para clase

| Pieza | Fichero | Qué es |
|---|---|---|
| Deck de Julián | [`Sesion10-Julian-Fernandez.pdf`](Sesion10-Julian-Fernandez.pdf) | 24 diapos: portada de la S10, 16 propias con demos reales, las 6 oficiales de LIDR, ROTI y gracias |
| Generador | [`deck/build_deck.py`](deck/build_deck.py) | reutiliza el motor del deck de la S7; `python build_deck.py` |
| Diagramas | [`deck/diagramas_s10.py`](deck/diagramas_s10.py) | RRF con ejemplo, recall-then-rerank y curva del decaimiento (`assets/s10-*`) |
| Diapos de LIDR | `deck/slides-lidr/` | las 6 imágenes oficiales incrustadas en el guion de Notion |
| Guion | [`guion-directo.md`](guion-directo.md) | guion de LIDR con una nota local al principio: comandos de PowerShell y diferencias reales |

### Verificado en local el 11/11/2026

- Stack `aieng-s10live` sano (5 contenedores), migración `0004_session10_multi_index`.
- Corpus: 60 componentes + 1543 tareas históricas en `budget_chunks`, 11 transcripciones, 8 docs técnicos.
- Reranker en frío: 16,6 s; relevante +2,95 frente a irrelevante −9,01.
- Routing: reglas → transcript (`expand`); clasificador → technical_doc; explícito → budget.
- Descomposición: 4 sub-consultas por tema; "Stripe checkout" → `direct`.
- Filtro `min_date 2024`: **1603 → 748** (no 60 → 42: las tareas viven en la misma tabla); + healthcare → 84.
- Horas por tarea: "Payment gateway integration" 42 h, fiabilidad 0,505, 5 vecinos; "Quantum teleporter" en rojo.
- `/stages/generate` sin horas: con brief rico, confianza alta y horas `null`, pero ~130 s con gpt-5.
- Web: home, wizard de estimación, Ajustes y Chunking Lab responden 200.
- Arnés (`scripts/eval_retrieval_s10.py`, 8 preguntas): A/B 0,48; con rerank 0,62; con decaimiento 0,48 (la Q5 cae
  de 0,80 a 0); routing 0,25. Tabla en la diapo 17.

### Interfaz añadida en local (rama `session_10_live_local`)

La web de la rama oficial no tenía forma de lanzar la búsqueda avanzada ni de ver lo hecho. Se añadió:

| Menú | Ruta | Qué hace | Ficheros |
|---|---|---|---|
| Búsqueda | `/rag/advanced_searches/new` | formulario con 7 ejemplos (uno por demo) y toggles; guarda cada búsqueda | `Rag::AdvancedSearchesController`, `EstimatorAi::RetrievalClient`, tabla `advanced_searches` |
| Corpus | `/rag/corpus` | chunks de las 3 tablas con metadatos, filtro por tipo y texto, paginado | `Rag::CorpusController`, `EstimatorAi::CorpusClient`, endpoint nuevo `GET /api/v1/corpus[/{collection}]` (`estimator/app/api/routers/corpus.py`) |
| Histórico | `/history` | línea de tiempo de búsquedas, estimaciones del wizard y Chunking Lab | `HistoryController` |

Las 7 demos ya están guardadas (ids 1–7). Zona horaria de Rails: Madrid.

## 8. Pendiente

- [x] Verificar en local las demos del guion.
- [x] Deck de Julián.
- [x] Tabla del arnés en local.
- [x] Interfaz de búsqueda, corpus e histórico.
