# Sesión 7 — Guion del directo · Embeddings y Representación Vectorial

> **Nota local (Julián).** Guion oficial copiado tal cual. Diferencias con mi PC:
>
> - **El guion usa `uv run …` en el Mac de Antonio.** Aquí todo se lanza dentro de Docker,
>   desde la carpeta `ai-engineering-fork-julian\ai-engineering-s07`: cambiar
>   `uv run python …` por `docker compose -p aieng-s07live exec estimator python …`.
> - **Sin `ANTHROPIC_API_KEY`:** `contextual_retrieval` no funciona en mi local. Para el
>   sub-bloque 5.3, usar los números de `app/generation/rag/COMPARISON_REPORT.md`.
> - **`--strategies all` aborta entero** ("ContextualRetrievalChunker requires
>   ANTHROPIC_API_KEY"). En los sub-bloques 5.4 y 6.3, listar las otras 7:
>   `--strategies structural,fixed-size,recursive,sentence-window,semantic,propositional,hierarchical`.
>   Ojo: con `propositional` sobre los 17 presupuestos tarda ~3 min; para la demo en vivo,
>   `--limit-budgets 3` (149 chunks, 147 huérfanos, 0,0015 $, 28 s — verificado el 21/10).
> - Añadir `2>$null` en PowerShell para ocultar los avisos de `botocore` de LiteLLM.
> - El guion dice "nada de Rails hoy", pero el Bloque 4 se puede enseñar en la web
>   (`http://localhost:3000/rag/chunking_comparisons/new`, el *Chunking Lab*): verificado.
> - Contexto y artículos: [contexto-sesion-07.md](contexto-sesion-07.md). Dudas de alumnos para
>   responder en directo: [dudas-alumnos.md](dudas-alumnos.md).

> **Duración**: 120 min · **Modalidad**: flipped classroom estricto · **Rama**: `session_07`.
>
> **Cómo se enseña hoy**: clase apoyada en **código ya implementado y commiteado**. Bloque a bloque explicamos el *fundamento*, lo aterrizamos sobre el **archivo concreto** que lo encarna y lo probamos con una demo. **No se teclea código en vivo** — las demos *ejecutan* lo que ya existe.
>
> **Estado al entrar**: pre-ejercicio de la S7 entregado (chunker estructural + embedder + `POST /embeddings/ingest` + `compare.py` + `SANITY_CHECK.md`) y los articles del módulo leídos.
>
> **Estado al salir**: el alumno ha visto **ocho estrategias de chunking** ejecutadas sobre su propio corpus, sabe leer las métricas comparativas y se va con **una estrategia elegida** para su proyecto y una lista de qué mediría antes de cambiarla. Persistencia y retrieval real (pgvector) son **Sesión 8**.

---

## Nota de arquitectura — por qué reorganizamos el proyecto (leer al abrir)

### [Diapositiva tres arquitecturas]

> **Decir esto en voz alta al empezar, antes de tocar ningún archivo.**

El estimador ya no es un único patrón: a lo largo del máster apila **tres arquitecturas de IA**
de forma aditiva — **CAG** (las caches que ya construimos), **RAG** (lo de hoy: chunking +
embeddings) y, más adelante, una capa **agéntica**. Sesión a sesión el código fue creciendo en
una **sucesión plana de carpetas** que escondía esa historia: las caches partidas en dos sitios,
el RAG naciendo aislado en `embedding_pipeline/`, lo agéntico mezclado en `services/`.

A partir de esta sesión el código vive en una **arquitectura por capas** donde las tres
arquitecturas son visibles y **componen** sobre una base común:

```
app/
├── foundation/   # plomería sin opinión: llm, prompts, guardrails, persistence
├── domain/       # schemas (el contrato) + estimation_service.py (el "conductor")
├── generation/   # las 3 arquitecturas que COMPONEN
│   ├── cag/      #   caches exacta + semántica (unificadas)
│   ├── rag/      #   chunking + embeddings (LO DE HOY) + store/ + retriever (Sesión 8)
│   ├── agentic/  #   boss + critic
│   └── conversation/
├── ingestion/    # pipeline batch que alimenta RAG
└── api/          # transporte (routers finos)
```

**La regla que lo sostiene**: los hermanos de `generation/` (cag, rag, agentic) **no se importan
entre sí** — se encuentran **solo** en el conductor (`domain/estimation_service.py`). Así, cuando
añadamos retrieval tiene un sitio obvio y no vuelve a degenerar en carpetas acopladas.

**Lo de hoy en este mapa**: todo lo que tocamos en la S7 (la interfaz `Chunker`, las estrategias,
el `embedder`, `POST /embeddings/ingest`) es exactamente el contenido de **`app/generation/rag/`**.
La persistencia (`generation/rag/store/`) y el retriever (`generation/rag/retriever.py`) son slots
reservados para la **Sesión 8**. El contrato completo está en `estimator/ARCHITECTURE.md`.

> Frase para defender ante un stakeholder: *"No reescribimos lógica: movimos las piezas a su capa. La arquitectura ahora se lee de un vistazo y cada cosa nueva sabe dónde va."*

---

## Cómo leer este guion — leyenda de modalidad

Cada sub-bloque sigue **siempre el mismo patrón de cinco partes**:

| Marcador | Qué es | Dónde |
| --- | --- | --- |
| **■ EL FUNDAMENTO** | El concepto y el problema que motiva la pieza. *Por qué* antes del *cómo*. | pizarra |
| **■ DÓNDE VIVE** | El archivo que encarna el fundamento. Responsabilidad + línea "aha" + decisión de diseño. | IDE — **leer, no teclear** |
| **■ DEMO** | Ejecutar el código existente y leer la salida. | terminal |
| **■ DEFENSA ORAL** | Lo que el alumno debe poder defender ante un stakeholder. | oral |
| **■ BRIDGE** | El enlace al siguiente sub-bloque. | oral |

> Regla de oro: **lidera con el fundamento, después abre el archivo.** Todas las estrategias viven en `app/generation/rag/` y todas implementan la misma interfaz `Chunker` (`app/generation/rag/chunking/base.py`), por eso son intercambiables en el comparador.

---

## Pre-flight checklist (5 min antes del directo)

```bash
# 1. Herramientas y rama
which curl docker uv python3
cd /Users/antonioperez/projects/ia/ai-engineering
git branch --show-current          # → session_07_live

# 2. Claves (las dos hacen falta hoy)
cd estimator
uv run python -c "from app.config import get_settings as g; s=g(); print('OpenAI:', bool(s.OPENAI_API_KEY), '| Anthropic:', bool(s.ANTHROPIC_API_KEY))"
# → OpenAI: True | Anthropic: True   (Anthropic es para Contextual Retrieval; OpenAI ≥ $5)

# 3. Dependencias nuevas resueltas
uv sync
uv run python -c "from app.generation.rag.chunking.strategies import *; print('strategies OK')"

# 4. Datos NLTK para sentence-window (descarga perezosa; forzarla en pre-flight)
uv run python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# 5. Stack arriba y endpoints visibles
docker compose up -d --build
curl -s localhost:8000/health | python3 -m json.tool        # → healthy
# Swagger debe mostrar POST /embeddings/ingest y POST /embeddings/compare
open http://localhost:8000/docs

# 6. Corpus instrumentado correcto
uv run python -c "import json; b=json.load(open('data/budgets_sample.json')); print('budgets', len(b), '| components', sum(len(x['components']) for x in b))"
# → budgets 17 | components 60
uv run python -c "import json; print('queries', len(json.load(open('data/test_queries.json'))))"   # → queries 6

# 7. Red de seguridad: regenerar el reporte (o usar el del día anterior)
uv run python scripts/compare_chunkers.py --strategies all --queries all \
  --show-stats --show-cost --output app/generation/rag/COMPARISON_REPORT.md
# Tarda ~6 min (propositional + contextual_retrieval llaman a LLMs). Coste ~$0.15.

# 8. El log de Contextual Retrieval imprime el contexto generado por Claude (legible)
#    Lo verás como eventos structlog 'contextual_chunk_context' durante el run del paso 7.
```

**Pestañas listas**:

- `http://localhost:8000/docs` — Swagger (`/embeddings/ingest`, `/embeddings/compare`).
- Editor con rutas pineadas: `app/generation/rag/chunking/base.py`, `app/generation/rag/chunking/structural.py`, `app/generation/rag/embedding/embedder.py`, `app/generation/rag/chunking/strategies/`, `app/generation/rag/analysis/comparison.py`, `scripts/compare_chunkers.py`, `data/budgets_sample.json`.
- `app/generation/rag/COMPARISON_REPORT.md` abierto como respaldo.

**Regla innegociable del directo**:

1. **No** debatir pgvector activo, índices HNSW ni retrieval real. Respuesta única: *"Sesión 8."*
2. Todo el código es **Python en el servicio IA**. Nada de Rails hoy.

---

## Bloque 1 — Pre-flight + apertura + reconciliación · 5 min · 0:00 – 0:05

### Sub-bloque 1.1 — Reconciliación narrativa (5 min)

#### ■ EL FUNDAMENTO · pizarra

Dibujar el arco real del módulo:

```
S6 (corpus limpio)  →  S7 (chunking + embeddings EN MEMORIA)  →  S8 (pgvector + retrieval)
                                       ↑ estamos aquí
```

Dos cosas que decir **abiertamente**, sin esquivarlas:

1. *"En la S6 dije que pgvector se activa hoy. **Lo he movido a la S8.** No es descuido: es disciplina. Mover la persistencia libera 90 minutos para chunking, que es donde de verdad se mueve la calidad de un RAG. Hoy los vectores viven en memoria y se devuelven por HTTP; la semana que viene les damos casa en pgvector."*
2. *"El corpus de hoy está basado en **componentes**, no en las **fases** que normalizamos en la S6. En un proyecto real escribiríamos un adaptador fases→componentes. Aquí es el ejemplo perfecto de una metanorma: **el shape de tus datos condiciona la estrategia de chunking que eliges.** Si tuviéramos fases, el chunker estructural se diseñaría distinto."*

#### ■ DÓNDE VIVE · `data/budgets_sample.json`

Abrir el fichero y leer un presupuesto: `budget_id`, `client_metadata`, `project_summary`, `main_technology` y la lista de `components` (cada uno con `description`, `tech_stack`, `complexity`, `estimated_hours`). **Ese `components[]` es el shape sobre el que trabaja todo el día.**

> Aha: 17 presupuestos, 60 componentes. Dos de ellos están **instrumentados a propósito** (los veremos en el Bloque 2): `BUD-2024-016` con una descripción gigante y `BUD-2024-017` con descripciones de una línea.

#### ■ DEMO · terminal

Ninguna en este sub-bloque.

#### ■ DEFENSA ORAL

- *"¿Qué pregunta hace un Tech Lead al ver que el schema de los datos no coincide con lo prometido? **¿Quién paga el adaptador?**"* — la deuda de integración es trabajo real que alguien presupuesta.

#### ■ BRIDGE → Bloque 2

*"Antes de chunking, cinco minutos con los problemas que aparecieron en vuestras entregas del pre-ejercicio."*

---

## Bloque 2 — Resolución de problemas del pre-ejercicio · 10 min · 0:05 – 0:15

### Sub-bloque 2.1 — Patrones de error reales (10 min)

#### [Diapositiva patrones de error reales]

#### ■ EL FUNDAMENTO · pizarra

Cinco patrones de error frecuentes, en orden de impacto:

1. **Sin validación Pydantic** → `KeyError` opaco en producción cuando falta un campo.
2. **Gestión naïve de tokens** → un chunk que excede el contexto del modelo de embeddings → 422 de la API.
3. **Sin batching** → un request por chunk, latencia que se dispara.
4. **Sin backoff** → caída ante el primer `RateLimitError`.
5. **Dimensionalidad inconsistente** → mezclar vectores de 1536 y 768 en el mismo índice rompe la similitud.

#### ■ DÓNDE VIVE · IDE

**`app/generation/rag/schemas.py`** — *el contrato.* Patrones (1) y (5):

```python
class EmbeddedChunk(Chunk):
    embedding: list[float] = Field(...)   # un único contrato de vector, no "a veces 1536, a veces 768"
```

> Aha: `sector` es un `Literal` cerrado y `EmbeddedChunk` extiende `Chunk`; un campo mal escrito o un sector inesperado **falla en validación**, no en producción.

**`app/generation/rag/embedding/embedder.py`** — *batching + backoff + tokens.* Patrones (2), (3), (4):

```python
BATCH_SIZE = 100                       # (3) el endpoint acepta listas → 1 llamada por lote
_RETRY_BACKOFF_SECONDS = (1, 2, 4)     # (4) reintento exponencial ante RateLimitError
```

> Aha: `embed_many` trocea en lotes de 100 y `_create` reintenta 1s/2s/4s. El `token_count` lo calcula el chunker con tiktoken (`app/generation/rag/chunking/base.py::count_tokens`), **antes** de tocar la API.

#### ■ DEMO · terminal

Ingesta con el corpus instrumentado: el componente larguísimo (`BUD-2024-016::MONO-001`) tiene **1.391 tokens**.

```bash
uv run python -c "
import json
from app.generation.rag.schemas import Budget
from app.generation.rag.chunking.structural import render_component_text
from app.generation.rag.chunking.base import count_tokens
budgets=[Budget(**b) for b in json.load(open('data/budgets_sample.json'))]
for b in budgets:
    for c in b.components:
        t=count_tokens(render_component_text(b,c))
        if t>800: print('OBESO', f'{b.budget_id}::{c.component_id}', t, 'tokens')
"
# → OBESO BUD-2024-016::MONO-001 1391 tokens
```

#### ■ DEFENSA ORAL

- *"Vuestro chunker **no truncó** esa descripción de 1.391 tokens. ¿Está bien o está mal? Defendedlo."* — **Depende.** Hoy no rompe nada: `text-embedding-3-small` acepta hasta 8.191 tokens. Pero es el **candidato a romper primero** si cambia el modelo o si añadimos compresión. Por eso lo medimos (`token_count`) aunque hoy no lo cortemos.

#### ■ BRIDGE → Bloque 3

*"Cinco patrones, cinco resueltos. Cerramos rápido el tema de modelos y abrimos chunking."*

---

## Bloque 3 — Cierre del modelo de embeddings · 15 min · 0:15 – 0:30

### Sub-bloque 3.1 — Comparativa rápida sobre el corpus (10 min)

#### ■ EL FUNDAMENTO · pizarra

#### [Diapositiva matryoshka]

Tres ejes para elegir modelo de embeddings: **latencia**, **dimensionalidad** (storage + velocidad de búsqueda) y **calidad**. Hoy comparamos `text-embedding-3-small` a **1536 dims** vs el mismo modelo **truncado a 768** vía el parámetro `dimensions` (Matryoshka). *(Un modelo local tipo `all-MiniLM-L6-v2` sería el tercer eje en producción; no lo ejecutamos hoy para no arrastrar `torch`.)*

#### ■ DÓNDE VIVE · IDE

**`app/generation/rag/embedding/embedder.py`** — la palanca Matryoshka:

```python
def __init__(self, client, model=MODEL, dimensions: int | None = None):
    self._dimensions = dimensions      # None = 1536 nativo; 768 = truncado
```

**`scripts/compare_chunkers.py`** — `run_models()` + `MODEL_VARIANTS` (`small-1536`, `small-768`).

> Aha: truncar dimensiones es **un parámetro**, no un modelo nuevo. Matryoshka entrena las primeras dimensiones para que carguen la mayor parte de la señal.

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --models small-1536,small-768
```

```
model       dims  avg_latency_ms  cosine(c0,c1)
----------  ----  --------------  -------------
small-1536  1536  879.8           0.9119
small-768   768   699.9           0.9117
```

> *"Mitad de dimensiones, **misma similitud** hasta el cuarto decimal (0.9117 vs 0.9119), y algo menos de latencia. La mitad de storage en la BBDD vectorial por casi cero pérdida de señal. Esto es la palanca que abriremos en S8 cuando el storage empiece a importar."*

#### ■ DEFENSA ORAL

- *"Un millón de presupuestos en vez de quince: ¿qué modelo y por qué?"* — **Depende** de coste de storage, latencia de búsqueda e idioma del corpus. No hay respuesta única; 768 dims empieza a pagar a escala.

### Sub-bloque 3.2 — Decisión locked y justificación (5 min)

#### ■ EL FUNDAMENTO · pizarra

*"El proyecto usa `text-embedding-3-small` @ 1536d porque: API ya configurada, coste despreciable a este volumen, multilingüe decente, y Matryoshka disponible como palanca futura. No es el mejor modelo posible; es el mejor balance pedagogía/calidad para este contexto."*

#### ■ DÓNDE VIVE / ■ DEMO

Ninguna; cierre rápido.

#### ■ BRIDGE → Bloque 4

*"Modelos cerrados. Ahora atacamos lo que de verdad mueve el dial: cómo partimos el documento."*

---

## Bloque 4 — Chunking I · Estrategias fundamentales · 30 min · 0:30 – 1:00

> Las cuatro estrategias de este bloque **no entienden el contenido**: cortan por reglas mecánicas. Todas implementan `Chunker` (`app/generation/rag/chunking/base.py`) y emiten el mismo evento `chunking_done`.

#### [Diapositiva familias de chunking]

#### [Este bloque lo podemos mostrar usando la interfaz]

### Sub-bloque 4.1 — Fixed-size como baseline degenerado (8 min)

#### ■ EL FUNDAMENTO · pizarra

La estrategia más simple: N tokens con overlap, ignorando cualquier frontera natural. Útil **solo** como suelo contra el que comparar.

#### ■ DÓNDE VIVE · `app/generation/rag/chunking/strategies/fixed_size.py`

```python
CHUNK_SIZE_TOKENS = 512
OVERLAP_TOKENS = 80
window = tokens[start : start + CHUNK_SIZE_TOKENS]
piece = _ENCODING.decode(window)        # corta a mitad de token/palabra
```

> Aha: trocea la **representación serializada del componente** por ventana de tokens. La frontera cae donde toca, no donde tiene sentido.

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies fixed-size --show-stats
```

```
strategy    n_chunks  min  p50   p95    max  orphans  obese
----------  --------  ---  ----  -----  ---  -------  -----
fixed_size  63        57   79.0  108.7  512  0        0
```

> *"`max = 512` exacto: el componente obeso de 1.391 tokens se ha partido en trozos topados a 512. No hay obesos, pero los cortes caen a mitad de frase. Mirad un trozo de `BUD-2024-016::MONO-001::p1` con `--show-top-k`: empieza y acaba en mitad de una palabra."*

#### ■ DEFENSA ORAL

- *"Ese chunk cortado a mitad de palabra, ¿qué embedding produce?"* — **ruido**. Ninguna decisión real de producción se construye sobre fixed-size salvo en corpus homogéneos sin estructura.

#### ■ BRIDGE → 4.2

*"Subimos un escalón: respetar los separadores naturales del lenguaje."*

### Sub-bloque 4.2 — Recursive como default razonable (8 min)

#### ■ EL FUNDAMENTO · pizarra

Jerarquía de separadores `\n\n → \n → ". " → " " → ""`: baja al siguiente solo si el trozo sigue siendo grande. Los benchmarks lo colocan repetidamente entre las mejores opciones a bajo coste.

#### ■ DÓNDE VIVE · `app/generation/rag/chunking/strategies/recursive.py`

```python
RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=512, chunk_overlap=80,
    separators=["\n\n", "\n", ". ", " ", ""])
```

> Aha: `from_tiktoken_encoder` mide en **tokens**, no en caracteres. Parte el presupuesto **entero serializado** (`serialize_budget`), por eso produce muchos menos chunks que el structural.

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies recursive --show-stats
```

```
strategy   n_chunks  min  p50    p95    max  orphans  obese
---------  --------  ---  -----  -----  ---  -------  -----
recursive  23        10   187.0  488.5  494  1        0
```

> *"23 chunks frente a 60 del structural. Distribución sana (p50 = 187, max 494, ningún obeso), porque junta componentes pequeños hasta llenar ~512 tokens. **Un** huérfano: una cola corta que sobró tras un corte."*

#### ■ DEFENSA ORAL

- *"MVP con un día de plazo: ¿con qué estrategia empezáis?"* — **recursive**. Es el default razonable. Solo se complejiza con evidencia medida.

#### [Diapositiva Fixed-size vs Recursive]

#### ■ BRIDGE → 4.3

*"Recursive no entiende el dominio. Ahora dos ideas más finas: ventana de oraciones y la estructural que ya construisteis."*

### Sub-bloque 4.3 — Sentence-window y structural: qué cambia (10 min)

#### ■ EL FUNDAMENTO · pizarra

Dos ideas distintas:

- **Sentence-window**: indexa **oraciones sueltas** (unidad pequeña → recall alto) pero guarda una **ventana de ±2 oraciones** para devolver al generador. La unidad indexada y la devuelta son **distintas a propósito**.
- **Structural** (lo del pre-ejercicio): explota el JSON, **un componente = un chunk**, con cabecera de contexto del padre.

#### [Diapositiva Sentence-window vs structural]

#### ■ DÓNDE VIVE · IDE — abrir los dos lado a lado

**`app/generation/rag/chunking/strategies/sentence_window.py`**:

```python
WINDOW_SIZE = 2
window_text = " ".join(sentences[lo:hi])   # ±2 oraciones → metadata.window_text
text = sentence                            # se embeda la oración pelada
```

**`app/generation/rag/chunking/structural.py`** (structural):

```python
chunk_id = f"{budget.budget_id}::{component.component_id}"
text = render_component_text(budget, component)   # cabecera de contexto + detalle
```

> Aha: en sentence-window el `text` (oración) **no** es lo que devolverías al LLM — eso es `metadata.window_text`. En structural, `text` ya lleva el contexto del padre incrustado.

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies sentence-window,structural \
  --queries "OAuth authentication for fintech mobile app" --show-top-k 3
```

```
=== sentence_window ===
Query: OAuth authentication for fintech mobile app
  1. [0.4530] BUD-2024-001::PSD2-002::s0
  2. [0.4410] BUD-2024-017::MVP-001::s0        ← "Email and password login." (¡del MVP de e-commerce!)
  3. [0.4110] BUD-2024-006::VENDOR-001::s0

=== structural ===
Query: OAuth authentication for fintech mobile app
  1. [0.5684] BUD-2024-001::AUTH-001           ← el componente OAuth correcto
  2. [0.5310] BUD-2024-001::NOTIF-004
  3. [0.5220] BUD-2024-001::PSD2-002
```

> *"Structural clava `AUTH-001` a 0.568. Sentence-window mete en el top-3 una oración **'Email and password login.' del MVP de e-commerce** a 0.441: una oración corta y descontextualizada que parece de auth pero no lo es. Esa es exactamente la debilidad de indexar oraciones peladas."*

#### ■ DEFENSA ORAL

- *"El sentence-window devuelve oraciones con score alto pero sin saber de qué presupuesto vienen. ¿Es problema?"* — **Sí**, en una llamada real al LLM-generador. Por eso la ventana viaja en `metadata.window_text`: es lo que el retriever pasaría al modelo, no la oración pelada.

#### ■ BRIDGE → 4.4

*"Cuatro estrategias mecánicas. Pongámoslas en una tabla antes de subir de nivel."*

### Sub-bloque 4.4 — Comparativa cuantitativa del bloque (4 min)

#### ■ DÓNDE VIVE · `scripts/compare_chunkers.py` (`--output-table`)

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py \
  --strategies fixed-size,recursive,sentence-window,structural \
  --queries all --output-table
```

```
strategy         n_chunks  p50_tokens  top1_cosine_avg
---------------  --------  ----------  ---------------
fixed_size       63        79.0        0.4744
recursive        23        187.0       0.4022
sentence_window  78        21.0        0.5071
structural       60        78.0        0.4744
```

> *"`top1_cosine_avg` = la confianza media del mejor candidato sobre las 6 consultas. Sentence-window saca el número más alto (0.507) **pero** recordad la oración fantasma del MVP: score alto ≠ chunk relevante. Structural y fixed-size empatan en confianza, pero structural respeta la unidad semántica."*

#### ■ DEFENSA ORAL

- *"Sin contar coste, ¿cuál preferís?"* — **structural** por especificidad de dominio; **recursive** como segundo; sentence-window útil cuando los documentos no tienen estructura.

#### ■ BRIDGE → Bloque 5

*"Las fundamentales no entienden el contenido. Ahora subimos a estrategias que sí — y que cuestan dinero."*

---

## Bloque 5 — Chunking II · Semánticas y contextuales · 30 min · 1:00 – 1:30

> Las tres de este bloque **llaman a un LLM/embeddings durante la ingesta**. Cada una expone `last_extra_cost_usd` y emite el coste en `chunking_done`. Si falta la API key, fallan limpio con un mensaje claro.

### Sub-bloque 5.1 — Semantic chunking: el coste real (8 min)

#### ■ EL FUNDAMENTO · pizarra

Embebe oraciones consecutivas y corta donde **cae la similitud** (un "breakpoint semántico"). El precio: una pasada de embeddings sobre todo el corpus **durante la ingesta**, antes de servir una sola query.

#### ■ DÓNDE VIVE · `app/generation/rag/chunking/strategies/semantic.py`

```python
BREAKPOINT_THRESHOLD_TYPE = "percentile"
BREAKPOINT_THRESHOLD_AMOUNT = 95          # solo los saltos de tema más bruscos son frontera
```

> Aha: usa `langchain_experimental.SemanticChunker`. El 95 es agresivo: pocos cortes, chunks grandes. `last_extra_cost_usd` se calcula con los tokens embebidos durante la ingesta.

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies semantic,structural --show-stats --show-cost
```

```
strategy    n_chunks  min  p50    p95    max   orphans  obese  cost_usd  seconds
----------  --------  ---  -----  -----  ----  -------  -----  --------  -------
semantic    34        57   112.5  165.4  1278  0        1      0.000094  5.31
structural  60        78   78.0   96.5   1391  0        1      0.000000  0.00
```

> *"Semantic produce 34 chunks (junta lo que va junto temáticamente) y cuesta **$0.000094 + 5.3 segundos** de ingesta. Structural: **$0 e instantáneo**. A 15 presupuestos la diferencia es ridícula; a un millón, esos 5 segundos son horas y ese coste se multiplica."*

#### ■ DEFENSA ORAL

- *"El coste y la latencia de ingesta se disparan. ¿Lo aprobáis en una review?"* — **Depende** de si la mejora cualitativa lo justifica para tu corpus. Sobre 17 presupuestos estructurados, structural ya separa bien; semantic brilla en prosa larga sin estructura.

#### ■ BRIDGE → 5.2

*"Semantic embebe para cortar. La siguiente le pide a un LLM que reescriba."*

### Sub-bloque 5.2 — Propositional chunking: cuándo sí y cuándo no (7 min)

#### ■ EL FUNDAMENTO · pizarra

Un LLM descompone cada componente en **proposiciones atómicas** autocontenidas. Preciso, caro, pedagógicamente excelente. Una llamada LLM por componente.

#### ■ DÓNDE VIVE · `app/generation/rag/chunking/strategies/propositional.py`

```python
PROPOSITIONAL_CHUNKER_MODEL  # gpt-4o-mini (settings)
class _Propositions(BaseModel): propositions: list[str]   # salida tipada vía instructor
```

> Aha: salida estructurada con instructor → `list[str]` garantizada. Si una llamada falla, **fallback** a un chunk = el componente entero (nunca se pierde contenido en silencio).

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies propositional --show-stats --show-cost --limit-budgets 3
```

Y los números del run completo (los 17 presupuestos), que es lo impactante:

```
strategy       n_chunks  min  p50   p95   max  orphans  obese  cost_usd  seconds
-------------  --------  ---  ----  ----  ---  -------  -----  --------  -------
propositional  778       6    11.0  17.0  26   765      0      0.007550  173.41
```

> *"60 componentes → **778 chunks**. Cada proposición es diminuta (p50 = 11 tokens) y **765 de 778 son huérfanos** (<20 tokens). Coste: $0.0076 y **casi 3 minutos** de ingesta por 60 llamadas a gpt-4o-mini. Y mirad la query de inventario:"*

```bash
uv run python scripts/compare_chunkers.py --strategies propositional \
  --queries "real-time inventory synchronization" --show-top-k 3
# 1. [0.8230] BUD-2024-007::INV-003::prop5   ← proposición clavada
```

> *"0.823, el score más alto de toda la sesión. La granularidad fina da una similitud altísima en el match exacto… a cambio de explotar el número de chunks por 13 y llenar el índice de fragmentos sin contexto."*

#### ■ DEFENSA ORAL

- *"¿Para qué corpus lo aprobáis y para cuál lo rechazáis?"* — Sí para corpus densos en hechos donde la precisión factual manda (legal, médico). No para corpus ya estructurados: la explosión de huérfanos no compensa.

#### ■ BRIDGE → 5.3

*"La estrella del bloque: la técnica de Anthropic que enriquece, no fragmenta."*

### Sub-bloque 5.3 — Contextual Retrieval: la palanca de Anthropic (12 min)

#### [Diapositiva contextual-retrieval]

#### ■ EL FUNDAMENTO · pizarra

Cada chunk se enriquece con un **párrafo generado por un LLM** que lo sitúa dentro del documento padre, prependido al chunk. **Prompt caching** del documento padre para no pagar el documento entero en cada llamada. Anthropic reporta hasta **−67%** en fallos de retrieval combinado con BM25 contextual + reranking.

#### ■ DÓNDE VIVE · `app/generation/rag/chunking/strategies/contextual_retrieval.py`

```python
CONTEXTUAL_CHUNKER_MODEL  # claude-sonnet-4-5 (settings)
system=[{ "type": "text",
          "text": f"<document>\n{parent_doc}\n</document>",
          "cache_control": {"type": "ephemeral"} }]   # ← se cachea el documento padre
```

> Aha: el documento padre va en un bloque `system` con `cache_control`. Procesamos los chunks **agrupados por presupuesto**: el primer chunk paga el documento (cache write), los demás lo leen de cache (cache read, ~10× más barato). El contexto generado se guarda en `metadata.generated_context` y se loguea (`contextual_chunk_context`).

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies contextual-retrieval,structural \
  --queries "OAuth authentication for fintech mobile app" --show-top-k 3 --show-cost
```

```
=== contextual_retrieval ===
  1. [0.6070] BUD-2024-001::AUTH-001     ← contexto generado + el chunk
=== structural ===
  1. [0.5684] BUD-2024-001::AUTH-001     ← el mismo chunk, pelado
```

Stats + coste del run completo:

```
strategy              n_chunks  cost_usd  seconds
--------------------  --------  --------  -------
contextual_retrieval  60        0.140155  202.72
structural            60        0.000000  0.00
```

> *"Mismo `AUTH-001`, pero el contexto generado por Claude lo sube de **0.568 a 0.607**. Leed en voz alta el `metadata.generated_context` de un par de chunks (sale en el log `contextual_chunk_context`). El precio: **$0.14 y 3.4 minutos** por 60 llamadas a Claude, frente a $0 del structural."*

#### ■ DEFENSA ORAL

- *"Nuestro `JSONStructuralChunker` ya prepende una cabecera con Project/Sector/Tech. ¿Eso ya es Contextual Retrieval?"* — **Sí, una versión estática y barata.** La pregunta honesta: ¿la versión completa con LLM aporta valor incremental? Sobre nuestros 17 presupuestos, +0.04 de cosine por $0.14 — **no es obvio que compense**. Esa discusión coste-vs-valor es el punto pedagógico, no el número.

#### ■ BRIDGE → 5.4

*"Tres estrategias caras. Tabla rápida con una consulta transversal y subimos al último bloque."*

### Sub-bloque 5.4 — Comparativa del bloque (3 min)

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies all \
  --queries "GDPR compliance and audit logging" --show-top-k 1
```

```
structural            BUD-2024-009::CONSENT-004        0.418
sentence_window       BUD-2024-009::CONSENT-004::s0    0.617
semantic              BUD-2024-009::sem1               0.358
propositional         BUD-2024-009::CONSENT-004::prop5 0.673
contextual_retrieval  BUD-2024-009::CONSENT-004        0.465
hierarchical          BUD-2024-009::CONSENT-004        0.418
```

> *"Una consulta abstracta que atraviesa sectores. **Todas** convergen en `CONSENT-004` (el módulo de consentimiento y auditoría de healthcare): la señal está, lo que cambia es la confianza y el tamaño de lo que devuelven. Propositional gana en score, contextual aporta contexto, structural es el más legible."*

#### ■ DEFENSA ORAL

- *"¿Cuál gana? ¿Por qué?"* — Tramposa: ganan distinto según qué optimices (score, contexto, coste, legibilidad).

#### ■ BRIDGE → Bloque 6

*"Último bloque: avanzadas, el framework de evaluación y el cierre."*

---

## Bloque 6 — Chunking III · Avanzadas + evaluación + cierre · 30 min · 1:30 – 2:00

### Sub-bloque 6.1 — Hierarchical / parent-child (10 min)

#### [Diapositiva Hierarchical]

#### ■ EL FUNDAMENTO · pizarra

Dos niveles indexados a la vez: **hijos** (componentes, pequeños → recall) y **padres** (presupuesto entero → contexto para generar la respuesta). El retriever de la S8 elegirá qué nivel devolver.

#### ■ DÓNDE VIVE · `app/generation/rag/chunking/strategies/hierarchical.py`

```python
chunks.append(Chunk(chunk_id=parent_id, ..., metadata={"level": "parent"}))
chunks.append(Chunk(..., metadata={"level": "child", "parent_chunk_id": parent_id}))
```

> Aha: conviven padre e hijos en el mismo índice; el hijo apunta a su padre con `metadata.parent_chunk_id`.

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies hierarchical \
  --queries "GDPR compliance and audit logging" --show-top-k 3 --resolve-parents
```

```
hierarchical:  77 chunks (17 padres + 60 hijos), 2 obesos (max 1472), $0
  1. [0.4180] BUD-2024-009::CONSENT-004     (hijo)
  2. [0.3070] BUD-2024-012::parent          ← un padre entero entra en el top-3
```

> *"77 chunks = 17 padres + 60 hijos. En la consulta de GDPR, un **padre entero** (`BUD-2024-012::parent`) sube al top-3: para una query abstracta, a veces el presupuesto completo es mejor respuesta que un componente suelto. `--resolve-parents` muestra el padre del hijo que matchea."*

#### ■ DEFENSA ORAL

- *"¿Cuándo activa esta estrategia y cuándo es overkill?"* — Overkill en FAQs o tickets cortos. Útil en manuales largos y documentos legales. Para presupuestos: borderline, probablemente útil para queries abstractas.

#### ■ BRIDGE → 6.2

*"Una estrategia más, pero esta no la ejecutamos: no tenemos el modelo que necesita."*

### Sub-bloque 6.2 — Late chunking: demo conceptual (5 min)

#### ■ EL FUNDAMENTO · pizarra

El cambio de orden: **embebes el documento entero** con una context window larga y **partes después**, de modo que cada chunk hereda el contexto de todo el documento en su vector. Requiere modelos con **token-level embeddings** que no son el del proyecto.

#### ■ DÓNDE VIVE · IDE

**Ninguna — no hay código ejecutable.** Es deliberado: meter late chunking bien costaría más de lo que aporta una única demo. Mostrar el diagrama del article o el repo de Jina como referencia.

#### ■ DEMO · terminal

Ninguna.

#### ■ DEFENSA ORAL

- *"¿Cuándo paga la pena late chunking?"* — Cuando los documentos son largos, el modelo soporta contextos grandes y el coste extra de re-embeder se ha vuelto despreciable. En nuestro caso, todavía no.

#### ■ BRIDGE → 6.3

*"Hemos visto ocho estrategias. ¿Cómo decidimos con datos? Ese es el framework."*

### Sub-bloque 6.3 — Cierre con el framework de evaluación (10 min)

#### ■ EL FUNDAMENTO · pizarra

La métrica informal de hoy: **estadísticos del corpus** + **cosine del top-3** + **inspección cualitativa** por consulta. Reconocer abiertamente que **no es recall@k formal** — eso es la Sesión 11.

#### ■ DÓNDE VIVE · IDE

**`app/generation/rag/analysis/comparison.py`** — el motor:

```python
class ChunkingComparator:
    def compute_stats(self, budgets) -> dict[str, ChunkingStats]: ...
    def run_queries(self, budgets, queries, top_k=3) -> dict[str, list[QueryResult]]: ...
```

> Aha: `_materialize` trocea cada estrategia **una sola vez** por corpus y memoiza, para que pedir stats + queries no duplique las (caras) llamadas LLM de propositional o contextual. Orphan < 20 tok, obese > 800 tok son constantes etiquetadas.

**`scripts/compare_chunkers.py`** — el driver del mentor (`build_chunkers` desde el registry de `app/dependencies.py`).

#### ■ DEMO · terminal

```bash
uv run python scripts/compare_chunkers.py --strategies all --queries all --show-stats --show-cost
```

```
strategy              n_chunks  min  p50    p95    max   orphans  obese  cost_usd  seconds
--------------------  --------  ---  -----  -----  ----  -------  -----  --------  -------
structural            60        57   78.0   96.5   1391  0        1      0.000000  0.00
fixed_size            63        57   79.0   108.7  512   0        0      0.000000  0.00
recursive             23        10   187.0  488.5  494   1        0      0.000000  0.01
sentence_window       78        3    21.0   82.0   101   34       0      0.000000  0.01
semantic              34        57   112.5  165.4  1278  0        1      0.000094  5.31
propositional         778       6    11.0   17.0   26    765      0      0.007550  173.41
contextual_retrieval  60        103  132.5  160.7  1457  0        1      0.140155  202.72
hierarchical          77        57   81.0   236.8  1472  0        2      0.000000  0.01
```

> *"Toda la sesión en una tabla. Coste: de $0 (mecánicas) a $0.14 (contextual). Granularidad: de 23 chunks (recursive) a 778 (propositional). Degeneración: 765 huérfanos en propositional, 0 en structural. **Este es el cuadro de mando para elegir.**"* (El reporte `app/generation/rag/COMPARISON_REPORT.md` lo tiene capturado por si algo falla en vivo.)

#### ■ DEFENSA ORAL

- *"Si esto fuera vuestro proyecto en producción, ¿con qué estrategia salís hoy? Y más importante: ¿qué necesitaríais medir antes de cambiarla?"* — La respuesta esperada incluye un plan de medición (recall@k formal, coste por query, latencia), no solo un nombre.

#### ■ BRIDGE → 6.4

*"Tenemos vectores y una estrategia elegida. Falta dónde guardarlos y cómo buscarlos rápido."*

### Sub-bloque 6.4 — Bridge a la Sesión 8 (5 min)

#### ■ EL FUNDAMENTO · pizarra

Lo que tenemos ahora — **vectores en memoria** — vs lo que entrega la S8: **pgvector** con índices HNSW/IVFFlat, búsqueda eficiente a escala, filtrado por metadata combinado con similarity, y **persistencia real**. El arco completo:

```
corpus limpio (S6) → vectores (S7) → BBDD vectorial (S8) → retrieval avanzado (S10) → generación (S11)
```

#### ■ DÓNDE VIVE · IDE

Previsualizar el directorio `alembic/versions/` (la migración que activará `CREATE EXTENSION vector` en S8). Hoy: la imagen `pgvector/pgvector:pg16` está montada pero la extensión sigue **dormida**.

#### ■ DEMO

Ninguna; cierre conceptual.

#### ■ BRIDGE

*"La próxima semana, búsqueda semántica de verdad: persistimos estos vectores y los consultamos con filtros. El código de hoy se queda intacto; la S8 añade una capa, no sustituye nada."*

---

## Reconciliaciones narrativas obligatorias (recordatorio para el mentor)

1. **Pgvector se ha movido a la S8.** Decirlo en el sub-bloque 1.1, sin esquivarlo: priorización de profundidad (90 min de chunking) sobre cobertura. La S8 hereda pgvector entero.
2. **El corpus de S6 (fases) ≠ corpus de S7 (componentes).** Presentarlo como anécdota didáctica: el shape de los datos condiciona el chunker. El adaptador fases→componentes queda como **hometask opcional**.

---

# Apéndice — Resumen ejecutivo

> Para repaso rápido antes del directo.

## Artefactos (todos ya commiteados en `session_07`)

| Ruta | Descripción |
| --- | --- |
| `app/generation/rag/chunking/base.py` | `Chunker` (ABC) + `count_tokens` + `emit_chunking_done`. |
| `app/generation/rag/chunking/structural.py` | `JSONStructuralChunker` (extiende `Chunker`) + helpers `render_component_text`, `serialize_budget`, `component_metadata`. |
| `app/generation/rag/embedding/embedder.py` | `OpenAIEmbedder` (batching, backoff, `dimensions` para Matryoshka). |
| `app/generation/rag/chunking/strategies/fixed_size.py` | `FixedSizeChunker` — ventana de tokens (baseline). |
| `app/generation/rag/chunking/strategies/recursive.py` | `RecursiveChunker` — separadores jerárquicos (LangChain). |
| `app/generation/rag/chunking/strategies/sentence_window.py` | `SentenceWindowChunker` — oración + `window_text` (nltk). |
| `app/generation/rag/chunking/strategies/semantic.py` | `SemanticChunker` — breakpoint por percentil 95 (LangChain). |
| `app/generation/rag/chunking/strategies/propositional.py` | `PropositionalChunker` — gpt-4o-mini, proposiciones atómicas. |
| `app/generation/rag/chunking/strategies/contextual_retrieval.py` | `ContextualRetrievalChunker` — Claude + prompt caching. |
| `app/generation/rag/chunking/strategies/hierarchical.py` | `HierarchicalChunker` — padre-hijo, dos niveles. |
| `app/generation/rag/analysis/comparison.py` | `ChunkingComparator`, `ChunkingStats`, `QueryResult`, `CompareRequest/Response`. |
| `app/generation/rag/analysis/similarity.py` | `cosine_similarity` + `percentile` (stdlib). |
| `app/api/embeddings.py` | `POST /embeddings/ingest` (S7 pre) + `POST /embeddings/compare` (S7 live). |
| `app/dependencies.py` | `get_*_chunker()` por estrategia + `CHUNKER_FACTORIES` + `build_chunkers`. |
| `scripts/compare_chunkers.py` | CLI de comparación (`--strategies/--queries/--show-stats/--show-top-k/--show-cost/--output/--models/--limit-budgets/--resolve-parents`). |
| `data/budgets_sample.json` | 17 presupuestos, 60 componentes (incl. `BUD-2024-016` obeso y `BUD-2024-017` huérfanos). |
| `data/test_queries.json` | Las 6 consultas del directo. |
| `app/generation/rag/COMPARISON_REPORT.md` | Reporte de respaldo (regenerable con `--output`). |
| `app/generation/rag/SANITY_CHECK.md` | Del pre-ejercicio. **No se toca.** |

## Settings nuevas (`app/config.py`)

| Setting | Valor por defecto | Propósito |
| --- | --- | --- |
| `PROPOSITIONAL_CHUNKER_MODEL` | `gpt-4o-mini` | Modelo que descompone en proposiciones. |
| `CONTEXTUAL_CHUNKER_MODEL` | `claude-sonnet-4-5` | Modelo de Contextual Retrieval (con prompt caching). |

*(Umbrales como `CHUNK_SIZE_TOKENS=512`, `OVERLAP_TOKENS=80`, `BREAKPOINT_THRESHOLD_AMOUNT=95`, `ORPHAN_MAX_TOKENS=20`, `OBESE_MIN_TOKENS=800` viven como constantes de módulo en cada estrategia / `comparison.py`.)*

## Dependencias nuevas (`pyproject.toml`)

`langchain-text-splitters`, `langchain-experimental`, `langchain-openai`, `nltk` (`anthropic` ya estaba). **No** `sentence-transformers`/torch.

## Decisiones de diseño cerradas (con justificación)

| Decisión | Elegido | Por qué |
| --- | --- | --- |
| Interfaz de estrategias | `Chunker` ABC común | Intercambiables en el comparador; refactor **no-breaking** del structural. |
| Comparación de modelos | OpenAI 1536 vs 768 (Matryoshka) | Sin `torch`; la palanca de dimensiones es un parámetro, no un modelo. |
| Métrica | Stats + cosine top-3 + inspección | Recall@k/NDCG formales son S11; hoy señales observables. |
| Persistencia | **Ninguna** (todo en memoria) | pgvector + retrieval son S8; el código de hoy no se sustituye, se amplía. |
| Coste instrumentado | `extra_cost_usd` en `chunking_done` y en stats | La decisión coste-vs-valor es el núcleo pedagógico del Bloque 5. |
| Chunkers con API sin key | Fallan limpio con mensaje claro | El endpoint mapea a 500; el resto de estrategias siguen funcionando. |

## Números de referencia (run completo, 17 presupuestos · 6 consultas)

| strategy | n_chunks | orphans | obese | cost_usd | seconds |
| --- | --- | --- | --- | --- | --- |
| structural | 60 | 0 | 1 | 0.000000 | 0.00 |
| fixed_size | 63 | 0 | 0 | 0.000000 | 0.00 |
| recursive | 23 | 1 | 0 | 0.000000 | 0.01 |
| sentence_window | 78 | 34 | 0 | 0.000000 | 0.01 |
| semantic | 34 | 0 | 1 | 0.000094 | 5.31 |
| propositional | 778 | 765 | 0 | 0.007550 | 173.41 |
| contextual_retrieval | 60 | 0 | 1 | 0.140155 | 202.72 |
| hierarchical | 77 | 0 | 2 | 0.000000 | 0.01 |

> Modelo embeddings: 1536d vs 768d → cosine 0.9119 vs 0.9117 (misma señal, menos storage).
