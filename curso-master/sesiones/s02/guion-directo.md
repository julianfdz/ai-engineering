# Sesión 2 — Guion del directo · Primeros pasos de arquitectura CAG

> **Nota local (Julián).** Guion oficial de LIDR copiado tal cual del Notion de la edición 2026-09. En este
> PC la rama `session_2_live` va en el worktree `ai-engineering-s02` (rama local `session_02_live_local`) y
> se levanta con `docker compose -p aieng-s02live`. En PowerShell 5.1 los `curl` del guion se sustituyen por
> `Invoke-RestMethod` (ver `guion-julian.md`). Diferencias reales con este guion: `contexto-sesion-02.md`.
# session-2-guide


# Sesión 2 — Guion en vivo · Estimator (CAG)

> **Duración total:** ~2h
**Audiencia:** alumnos del Máster en AI Engineering que ya tienen el proyecto `estimator/` levantado tras la Sesión 1.
**Objetivo:** convertir un endpoint que devuelve estimaciones genéricas en una arquitectura CAG funcional con preprocesamiento configurable, evaluación estructural y comparativas en vivo de formato/cantidad de contexto y parámetros del modelo.

---


## Setup rápido (antes de empezar)

> 📂 **Archivos en juego:** `estimator/Dockerfile` · `estimator/docker-compose.yml` · `estimator/.env` (creado a partir de `estimator/.env.example`) · `estimator/app/fixtures/short_transcription.txt` · `estimator/app/fixtures/long_transcription.txt`
> 💡 El proyecto se ejecuta con **Docker Compose**. El `docker-compose.yml` ya monta `./app` como volumen y arranca uvicorn con `--reload`, así que cualquier edición de código que hagamos en vivo se aplica al instante sin reconstruir la imagen.
```bash
# Terminal 1: arrancar el servicio (hot reload incluido vía bind mount + uvicorn --reload)
cd estimator
docker compose up --build

# Terminal 2: variables y sanity check
export BASE=http://localhost:8000
export TRANS=$(jq -Rs . < estimator/app/fixtures/long_transcription.txt)
export SHORT=$(jq -Rs . < estimator/app/fixtures/short_transcription.txt)

curl -s $BASE/health | jq
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$SHORT}" | jq '{model, score: .validation.score, latency_ms}'
```
Si el segundo comando responde 200 con `score >= 0.5`, el sistema está listo para la sesión.

> ⚠️ **Importante para los Bloques 3.4 y 4.1:**
- Los cambios en archivos bajo `app/` se aplican automáticamente (bind mount + `--reload`).
- Los cambios en `.env` **no** se aplican solos: hay que recrear el contenedor con `docker compose up -d --force-recreate estimator`. Mencionarlo cuando llegue el momento.

### Comandos Docker útiles durante la sesión

```bash
# Ver logs en tiempo real (curls + warnings + errores) en otra terminal
docker compose logs -f estimator

# Reiniciar tras cambiar .env
docker compose up -d --force-recreate estimator

# Apagar todo al final
docker compose down
```

---


## Bloque 1 — Resolución de problemas y puesta en común (10’)

> 📂 **Archivos en juego:** `estimator/app/main.py` · `estimator/app/config.py` · `estimator/.env` · `estimator/app/services/llm_service.py` (extracción del campo de respuesta del LLM)

### Apertura

> “¿Quién consiguió que su endpoint devolviera una estimación? ¿Y quién la leyó y pensó ‘esto no se lo puedo enviar a un cliente’?”
La segunda pregunta prepara el terreno: las primeras estimaciones suelen ser genéricas e inútiles, y la sesión existe para arreglarlo.


### Errores comunes y su fix exprés

| Síntoma | Causa probable | Fix |
|---|---|---|
| `ModuleNotFoundError` al arrancar | Falta un `__init__.py` o la estructura no coincide con la del repo | Comparar `tree app/` con la estructura del repo de referencia. |
| `ValidationError` de Pydantic Settings | `.env` no cargado o variable obligatoria vacía | Verificar `python-dotenv` instalado y que el `.env` tiene la API key del provider activo. |
| Import circular `main.py` ↔︎ `config.py` | Acceso a `Settings()` en módulo top-level | `get_settings()` debe usar `@lru_cache` y llamarse dentro de funciones, no a nivel módulo. |
| 500 con respuesta vacía | Mala extracción del contenido del LLM | OpenAI: `response.choices[0].message.content`. Anthropic: `response.content[0].text`. |
| Timeouts | Modelo premium con prompt largo | Usar `gpt-4o-mini` o `claude-haiku-4-5` para iterar. |
> 💡 **Regla del instructor:** si más de 3 alumnos tienen el mismo problema, resolverlo una vez en pantalla compartida. Si es individual, pedir que tomen nota y se queden 5 min después.

### Puesta en común rápida

Preguntas al grupo (no se profundiza):

- ¿Cuántos ejemplos pusieron en el contexto: 2, 3, 5?
- ¿Qué formato usaron: texto plano, JSON, Markdown?
- ¿Quién usó OpenAI y quién Anthropic? ¿Alguien implementó ambos?
- ¿Alguien probó la petición sin los ejemplos de contexto? ¿Qué diferencia notó?
> 💡 La última pregunta es una **trampa pedagógica**: quien lo haya probado ya habrá visto que sin contexto la estimación es genérica. Es la mejor demostración posible de por qué CAG funciona.
> ⚠️ **Si alguien no tiene el proyecto levantado tras 10 min**: que clone la solución de referencia y arranque desde ahí (`docker compose up --build`). No invertir más tiempo aquí.

---


## Bloque 2 — La transcripción real: del input limpio al input del mundo real (25’)


### Objetivo

Tres metas encadenadas:

1. **Reanclar conceptualmente CAG** en una intro corta. Aunque ya lo vieron en el material asíncrono, hay que ponerlo en el centro de la mesa antes de tocar código.
1. **Recorrer el código en vivo** siguiendo una petición real desde el `curl` hasta la respuesta JSON, archivo por archivo.
1. **Ver el efecto del preprocesamiento del input** comparando los tres modos: `none`, `inline_cleaning`, `two_phase`.

### 2.0 Intro corta a CAG (3 min)

> 📂 **Archivos en juego (referencia conceptual, no editamos aún):** `estimator/app/context/examples.py` (los ejemplos canónicos = “el contexto”) · `estimator/app/services/llm_service.py::build_system_prompt` (donde se inyectan).
Lanzar dos preguntas a la clase y dejar que respondan en chat o en alto:

> “Cuando le mandamos al modelo nuestro `system prompt` de la Sesión 1, ¿le dimos información del **dominio** de la empresa? ¿O solo le dijimos su rol?”
La mayoría dirá que **rol más algunos ejemplos**. Conectar:

> 💡 **CAG (Cache Augmented Generation)** es un patrón en el que **inyectas el contexto relevante directamente en el prompt** como texto estático, antes de la llamada. En nuestro proyecto, ese contexto son **ejemplos de estimaciones pasadas** que viven en `app/context/examples.py`. El modelo no “busca” nada — el contexto **ya está** en el prompt cuando lo invocamos.
**¿Por qué CAG y no RAG?** Porque tenemos pocos ejemplos (5) y el dominio es estable. RAG (Retrieval Augmented Generation) tiene sentido cuando el conjunto de referencia es grande, dinámico, o no cabe en una ventana de contexto. CAG es:
- **Más simple** (no hay vector store, no hay búsqueda semántica, no hay embeddings).
- **Más barato** de operar (cero infraestructura adicional).
- **Más fácil de depurar** (el prompt completo está en los logs).

La contrapartida: cada token de contexto que metemos paga **en cada llamada**. Por eso en el Bloque 3 vamos a medir cuánto contexto vale la pena.

Mostrar visualmente el “antes” y el “después” en pizarra o slide:

```plain text
[ usuario ] ──> [ system prompt + EJEMPLOS + transcripción ] ──> [ LLM ] ──> [ estimación ]
                                ↑
                                └── esto es lo único que aporta CAG
```
> 💡 **Cierre de la intro:** “En esta sesión vamos a tocar **el contexto que inyectamos** y los **parámetros con los que llamamos al modelo**, sin tocar el modelo en sí. Esa es la palanca real de un ingeniero de IA — la mayoría de las decisiones de calidad pasan por aquí.”

### 2.1 Recorrido por el código siguiendo una petición (8 min)

> 📂 **Archivos en juego:** `estimator/app/main.py` · `estimator/app/routers/estimations.py` · `estimator/app/schemas/estimation.py` · `estimator/app/services/llm_service.py` · `estimator/app/context/examples.py` · `estimator/app/services/evaluation.py` · `estimator/app/fixtures/long_transcription.txt`
Compartir pantalla con el editor abierto en `estimator/`. Lanzar el primer curl en otra terminal y, mientras se procesa (o sobre la respuesta ya devuelta), ir abriendo cada archivo y explicando qué hace.

**Lanzar la petición:**

```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"preprocessing\":\"none\"}" \
  | jq '{model, finish_reason, latency_ms, estimation, score: .validation.score, issues: .validation.issues, usage}'
```
Mientras se ejecuta, recorrer el código en este orden. Cada paso son 30-60 segundos:

| # | Archivo | Qué se explica |
|---|---|---|
| 1 | `app/main.py` | Punto de entrada FastAPI. `lifespan` configura `structlog`. El router se monta con `app.include_router(estimations.router)`. |
| 2 | `app/routers/estimations.py` | El endpoint `POST /api/v1/estimate`. Recibe un `EstimationRequest`, construye `GenerationOptions`, llama a `generate_estimation`, ejecuta la validación estructural, devuelve `EstimationResponse`. **Aquí entra la petición.** |
| 3 | `app/schemas/estimation.py` | El contrato. Mostrar `EstimationRequest` con todos los campos opcionales (`preprocessing`, `example_format`, `num_examples`, `model`, `max_tokens`, `thinking_budget`). Y `EstimationResponse` con `validation`, `finish_reason`, `latency_ms`, `usage`. **Pydantic valida automáticamente; si falta **`**transcription**`** o es < 50 chars, el cliente recibe 422 sin que toquemos código.** |
| 4 | `app/services/llm_service.py::generate_estimation` | El orquestador. Decide si hace preprocesamiento (`two_phase` → `extract_requirements`), construye el system prompt, despacha al provider (OpenAI/Anthropic), añade `latency_ms` y `finish_reason`. **Es el corazón del servicio.** |
| 5 | `app/services/llm_service.py::build_system_prompt` | Mostrar **literal** cómo se concatena: rol + (cleaning block opcional) + tasas + `ACTIVE_OUTPUT_PROMPT` + bloque de ejemplos. **Esto es CAG materializado**: la lista `examples_block` es lo que hace que el modelo entienda “cómo estimamos en esta empresa”. |
| 6 | `app/context/examples.py` | Abrir `CANONICAL_EXAMPLES`. Mostrar el `dataclass` con `breakdown` estructurado y `estimation_markdown` precomputado. Mostrar los 3 formatters (`_format_markdown`, `_format_json`, `_format_narrative`). **Una sola fuente, tres salidas.** |
| 7 | `app/services/llm_service.py::_call_openai` | La llamada real al SDK. Pasamos `model`, `messages`, `max_tokens`. Extraemos `finish_reason` y `usage` para devolverlos arriba. **Aquí ocurre lo único que paga la factura.** |
| 8 | `app/services/evaluation.py::evaluate_estimation_structure` | El validador estructural. Regex puro, sin LLM. Detecta secciones, suma filas de la tabla, compara con totales declarados, evalúa `finish_reason`, calcula `score` y `issues`. **Este será el termómetro de toda la sesión.** |
| 9 | Vuelta a `app/routers/estimations.py` | Se construye `EstimationResponse(**result, validation=validation)`. **Esto es lo que ve la terminal.** |
Con la respuesta del curl ya en pantalla, señalar:

- `model` → vino de `_call_openai` (paso 7).
- `validation.score` → vino de `evaluate_estimation_structure` (paso 8).
- `usage.input_tokens` alto → vino de los ejemplos inyectados en `build_system_prompt` (paso 5+6).
- `latency_ms` → calculado en `generate_estimation` (paso 4).
> 💡 **Cierre del walkthrough:** “Cuando os pidan en una entrevista ‘cómo construirías un sistema con LLM’, esta es la respuesta: una API delgada que valida input, un servicio que construye el prompt con contexto curado, una llamada al modelo, y una capa de validación del output. **Lo demás son adornos.**”

### 2.2 La transcripción real — análisis del output (4 min)

> 📂 **Archivos en juego:** `estimator/app/fixtures/long_transcription.txt` (el input que estamos analizando) · `estimator/app/services/evaluation.py` (el origen de `validation.score` e `issues` en pantalla).
Con el output del curl anterior aún en pantalla, abrir el campo `estimation` en otro panel y leer juntos el resultado.

Compartir también el archivo `estimator/app/fixtures/long_transcription.txt` (~5.000 palabras): es una llamada de descubrimiento Acme Foods × agencia con dos partes (kickoff con cliente + deep-dive técnico con su senior backend). Tiene divagaciones, contradicciones (lo de SAP que en realidad es BCN-Touch), plazos mencionados de pasada, requisitos enterrados (Stripe deposits configurables, GDPR con incidente previo, MJML per-tenant, RLS en Postgres, exclude constraint, magic links, etc.).

Analizar juntos sobre la `estimation` devuelta:

- ¿Detectó el modelo los requisitos implícitos (PWA, accesibilidad WCAG, residencia EU only)?
- ¿Ignoró las divagaciones o las interpretó como requisitos (“queremos algo simple” + “AI dashboards”)?
- ¿Capturó el matiz **SAP → BCN-Touch** o se quedó con la mención superficial?
- ¿Los precios son coherentes con los ejemplos de referencia?
- ¿`validation.score` qué nos dice? ¿Y los `issues`?
> 💡 En producción el input nunca es limpio. La calidad del sistema se mide con inputs reales, no con inputs de laboratorio.

### 2.3 Estrategia A — Inline cleaning (system prompt extendido) (4 min)

> 📂 **Archivos en juego:**
- `estimator/app/services/llm_service.py` → constante `INLINE_CLEANING_BLOCK` y la rama `inline_cleaning=(opts.preprocessing == "inline_cleaning")` dentro de `build_system_prompt` y `generate_estimation`.
- `estimator/app/schemas/estimation.py` → literal `PreprocessingMode` y campo `preprocessing` del request.
Una sola llamada al LLM. Se añade al system prompt un párrafo que le dice al modelo cómo lidiar con el ruido. **Ya está implementado** en `INLINE_CLEANING_BLOCK` (en `app/services/llm_service.py`).

Abrir el archivo y mostrar el bloque en directo:

```python
INLINE_CLEANING_BLOCK = """\
The transcription you receive is from a real meeting and may contain:
- Informal small talk you must ignore
- Implicit requirements you must surface explicitly
- Contradictions where you must trust the most recent statement
- Non-technical jargon you must interpret

Extract ONLY the functional and technical requirements relevant to the estimation."""
```
Lanzar:

```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"preprocessing\":\"inline_cleaning\"}" \
  | jq '{estimation, score: .validation.score, issues: .validation.issues, latency_ms, usage}'
```
**Hands-on (3 min):** los alumnos editan `INLINE_CLEANING_BLOCK` (añadir, p.ej., una línea sobre “extract budget and deadlines explicitly”). El bind mount + `--reload` aplica el cambio sin reconstruir; repiten el curl y comparan.


### 2.4 Estrategia B — Two-phase (extracción + estimación) (5 min)

> 📂 **Archivos en juego:**
- `estimator/app/services/llm_service.py` → función `extract_requirements`, constante `EXTRACTION_SYSTEM_PROMPT`, rama `if opts.preprocessing == "two_phase"` dentro de `generate_estimation`.
- `estimator/app/schemas/estimation.py` → campos `extracted_requirements`, `preprocessing_input_tokens`, `preprocessing_output_tokens` del response.
Dos llamadas al LLM. La primera (barata) limpia la transcripción y produce un bullet-list de requisitos; la segunda hace la estimación a partir de esos requisitos limpios.

Abrir y leer en directo `extract_requirements` en `app/services/llm_service.py` y la lógica del switch en `generate_estimation` (la rama `if opts.preprocessing == "two_phase"`).

```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"preprocessing\":\"two_phase\"}" \
  | jq '{extracted_requirements, estimation, score: .validation.score, latency_ms, tokens: .usage.total_tokens, prep_tokens: (.usage.preprocessing_input_tokens + .usage.preprocessing_output_tokens)}'
```
Mostrar el `extracted_requirements` en pantalla — con los 5.000 palabras de Acme Foods, ese bullet list ya es accionable por sí solo: integración Loyalty/Java, BCN-Touch relay agent, RLS Postgres, Stripe deposits configurables, GDPR DSAR, MJML per-tenant, multi-idioma ES/CA/PT/EN, etc.extracted_


### Comparativa para proyectar

| Modo | Llamadas LLM | Tokens extra | `score` esperado | Latencia | Coste relativo |
|---|---|---|---|---|---|
| `none` | 1 | 0 | bajo si transcripción ruidosa | base | 1× |
| `inline_cleaning` | 1 | ~+50 (prompt) | medio | base + 5% | 1.05× |
| `two_phase` | 2 | varios cientos | alto | ~2× | ~1.5× |
> 💡 **Punto pedagógico clave:** “más llamadas al LLM” no siempre es mejor. A veces un prompt bien diseñado en una sola llamada supera a un pipeline de múltiples llamadas. La estrategia A es más simple y barata; la B produce resultados más limpios pero duplica coste y latencia. **No hay respuesta universal — depende del input.** Con una transcripción ruidosa de 5.000 palabras, two-phase merece la pena. Con un brief limpio de 200 palabras, no.

---


## Bloque 3 — Iteración sobre el contexto de referencia (35’)

> Bloque central de la sesión. Cada alumno debe salir con su system prompt y su contexto mejorados.

### 3.1 — Con contexto vs. sin contexto (5 min)

> 📂 **Archivos en juego:**
- `estimator/app/schemas/estimation.py` → campo `use_examples` del request.
- `estimator/app/services/llm_service.py::build_system_prompt` → la condición `if use_examples and num_examples > 0` que decide si concatenar el bloque de ejemplos.
```bash
# Sin CAG
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"use_examples\": false}" \
  | jq '{estimation, score: .validation.score, issues: .validation.issues, usage}'

# Con CAG
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"use_examples\": true}" \
  | jq '{estimation, score: .validation.score, issues: .validation.issues, usage}'
```
> 💡 **Verbalizar:** “El modelo es el mismo. La pregunta es la misma. Lo único que cambió es el contexto inyectado. **Esto** es CAG.”

### 3.2 — Formato del contexto: tres enfoques (10 min)

> 📂 **Archivos en juego:**
- `estimator/app/schemas/estimation.py` → literal `ExampleFormat` (`"markdown" | "json" | "narrative"`) y campo `example_format` del request.
- `estimator/app/context/examples.py` → `format_examples_for_prompt` y los tres formatters internos `_format_markdown`, `_format_json`, `_format_narrative`.
```bash
for FMT in markdown json narrative; do
  echo "===$FMT ==="
  curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
    -d "{\"transcription\":$TRANS,\"example_format\":\"$FMT\"}" \
    | jq "{format:\"$FMT\", input_tokens: .usage.input_tokens, latency_ms, estimation, score: .validation.score}"
done
```
Pregunta a la clase tras correr los tres:

- ¿Cuál produjo la estimación más útil? (lectura humana del campo `estimation`)
- ¿Cuál replicó mejor la estructura?
- ¿Cuál consumió menos tokens?
**Hands-on:** los alumnos eligen el formato que mejor funcionó y se quedan con él como default editando su `.env` o el cliente que estén usando.


### 3.3 — Cantidad de ejemplos: punto dulce vs. saturación (10 min)

> 📂 **Archivos en juego:**
- `estimator/app/schemas/estimation.py` → campo `num_examples` del request (rango 0..5).
- `estimator/app/context/examples.py` → `select_examples(n)` y la lista `CANONICAL_EXAMPLES` (5 ejemplos calibrados).
```bash
for N in 0 1 3 5; do
  curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
    -d "{\"transcription\":$TRANS,\"num_examples\":$N}" \
    | jq "{n:$N, input_tokens: .usage.input_tokens, output_tokens: .usage.output_tokens, latency_ms, score: .validation.score, estimation}"
done
```
Construir tabla en pantalla con los datos reales:

| `num_examples` | Tokens input | Latencia | `score` |
|---|---|---|---|
| 0 | (apuntar) | (apuntar) | (apuntar) |
| 1 |  |  |  |
| 3 |  |  |  |
| 5 |  |  |  |
> 💡 **Verbalizar:** “Fíjate en que la calidad mejora mucho entre 1 y 3 ejemplos, algo entre 3 y 5, y los tokens siguen subiendo linealmente. Este es el **rendimiento decreciente del contexto** — y es exactamente lo que convierte un sistema CAG viable en uno caro e ineficiente. En este proyecto, 3 buenos ejemplos serán nuestro punto dulce.”
> 📝 El proyecto tiene 5 ejemplos canónicos calibrados (`CANONICAL_EXAMPLES` en `app/context/examples.py`). Si más adelante quieres demostrar saturación clara, hay que añadir más ejemplos; con 5 la curva ya es visible pero no abrupta.

### 3.4 — El system prompt como multiplicador de calidad (5 min)

> 📂 **Archivos en juego:**
- `estimator/app/services/llm_service.py` → constantes `PROMPT_OUTPUT_BASIC` y `PROMPT_OUTPUT_STRUCTURED`, y la línea `ACTIVE_OUTPUT_PROMPT = ...` que actúa de switch.
- El cambio se aplica en vivo gracias al bind mount declarado en `estimator/docker-compose.yml` y al `--reload` del comando uvicorn.
Aquí está la demo más espectacular del bloque. Hay **dos versiones del prompt de output cohabitando** en `llm_service.py` y un switch (`ACTIVE_OUTPUT_PROMPT`) que decide cuál se usa.


### Versión “antes” (genérica)

```python
PROMPT_OUTPUT_BASIC = "Generate an estimation for the project described above."
```

### Versión “después” (estructura explícita)

```python
PROMPT_OUTPUT_STRUCTURED = """\
Generate the estimation with this exact structure:

## Project summary
[2-3 sentences describing the project scope and goals]

## Task breakdown
| Task | Hours | Cost (EUR) |
[one row per task; cost = hours * 62.50 EUR for developer tasks]

## Totals
- Total hours: [number]
- Total cost: [number] EUR
- Recommended team: [composition]
- Estimated duration: [weeks]

## Risks and assumptions
- [3-5 bullet points covering technical risks, scope assumptions, and external dependencies]
"""
```

### Demo en vivo

1. Curl con la versión actual (`PROMPT_OUTPUT_BASIC` activo por defecto):
```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS}" \
  | jq '{estimation, score: .validation.score, issues: .validation.issues}'
```
1. Abrir `app/services/llm_service.py` y cambiar **una sola línea**:
```python
ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_STRUCTURED   # antes: PROMPT_OUTPUT_BASIC
```
1. El bind mount + `-reload` aplica el cambio sin reconstruir la imagen. Repetir el curl. Comparar `score` e `issues`.
> 💡 La diferencia en consistencia y utilidad del output suele ser dramática. Verbalizar: “Ningún token nuevo de contexto. Solo le dijimos al modelo qué forma queremos. Y la `validation.score` se nos va al techo.”

---


## Bloque 4 — Parámetros del modelo y su impacto (20’)


### 4.1 — Tier de modelo: económico vs. premium (10 min)

> 📂 **Archivos en juego:**
- `estimator/app/schemas/estimation.py` → campo `model` del request (override por petición).
- `estimator/app/services/llm_service.py` → `_call_openai(model=...)`, `_call_anthropic(model=...)` y la línea `model = opts.model or settings.LLM_MODEL` en `generate_estimation`.
- `estimator/.env` → `LLM_PROVIDER` y `LLM_MODEL` por defecto (necesita recrear el contenedor para aplicarse).
- `estimator/app/config.py` → `Settings` con `@lru_cache`, motivo por el que `.env` no se relee en caliente.
```bash
# OpenAI: override por body, sin reiniciar
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"model\":\"gpt-4o-mini\"}" \
  | jq '{model, score: .validation.score, latency_ms, usage}'

curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"model\":\"gpt-4o\"}" \
  | jq '{model, score: .validation.score, latency_ms, usage}'
```
Anthropic (cambiar `LLM_PROVIDER=anthropic` en `.env` y **recrear el contenedor**: `docker compose up -d --force-recreate estimator`):

```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"model\":\"claude-haiku-4-5\"}" \
  | jq '{model, score: .validation.score, latency_ms, usage}'

curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"model\":\"claude-sonnet-4-6\"}" \
  | jq '{model, score: .validation.score, latency_ms, usage}'
```
> ⚠️ **Importante:** `get_settings()` usa `@lru_cache` y, con Docker, las variables de `.env` solo se leen al **arrancar el contenedor**. Cambiar `.env` requiere `docker compose up -d --force-recreate estimator` (no basta con `restart` ni con el `--reload` de uvicorn).
> 💡 **Verbalizar:** “Para prototipado e iteración, usad siempre el modelo económico. Es 10-20× más barato y permite hacer 100 pruebas por el precio de 5 con el premium. Cuando la calidad ya sea buena con el económico, probáis con el premium para ver si el salto justifica el coste. En muchos casos, el modelo económico con un buen prompt supera al premium con un prompt mediocre.”

### 4.2 — Parámetros de generación (10 min)

> 📂 **Archivos en juego:**
- `estimator/app/schemas/estimation.py` → campos `max_tokens` y `thinking_budget` del request, campo `finish_reason` del response.
- `estimator/app/services/llm_service.py` → `_call_openai` (extracción de `finish_reason`) y `_call_anthropic` (rama `if thinking_budget is not None:` y mapeo de `stop_reason`).
- `estimator/app/services/evaluation.py::evaluate_estimation_structure` → check `finish_reason_ok` que aparecerá en `validation.issues` si la respuesta se trunca.

### `max_tokens` y truncamiento

```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"max_tokens\": 200}" \
  | jq '{finish_reason, score: .validation.score, issues: .validation.issues}'
```
Con `max_tokens=200` la respuesta se corta a mitad de la tabla. `finish_reason` viene como `"length"` y `validation.issues` lo flagea explícitamente.

> 💡 **Lección:** siempre configurar `max_tokens` explícitamente y comprobar `finish_reason`. Una estimación truncada que se envía al cliente tal cual es vergonzosa.

### Razonamiento extendido (Anthropic)

> Solo aplica si `LLM_PROVIDER=anthropic`. Con OpenAI activo, `thinking_budget` se ignora con un warning en los logs.
```bash
# .env: LLM_PROVIDER=anthropic, LLM_MODEL=claude-sonnet-4-6
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"thinking_budget\": 2000,\"max_tokens\": 6000}" \
  | jq '{finish_reason, latency_ms, score: .validation.score, output_tokens: .usage.output_tokens}'
```
> 💡 El razonamiento extendido **no es gratuito**: consume tokens de “pensamiento” facturados como output. Para una estimación simple no compensa. Para una compleja donde la coherencia interna importa (que las horas sumen, que el equipo cuadre con la carga de trabajo), puede valer la pena.

---


## Bloque 5 — Evaluación de calidad (15’)


### 5.1 El problema

> 📂 **Archivos en juego:**
- `estimator/app/services/evaluation.py::evaluate_estimation_structure` → los 8 checks regex que componen el `score`.
- `estimator/app/schemas/estimation.py::StructureCheck` → la forma del objeto `validation` que la API devuelve.
- `estimator/app/routers/estimations.py` → la línea `validation = evaluate_estimation_structure(...) if request.evaluate else None`.
> “Imaginad que hacéis 100 estimaciones con este sistema. ¿Cómo sabéis cuántas son buenas, aceptables o inutilizables?”
Una estimación generada por un LLM no tiene una respuesta “correcta” contra la que comparar. Es un problema abierto, en tres niveles:

- **Nivel 1 — Estructural (automatizable):** ¿están todas las secciones? ¿los números cuadran? ¿`finish_reason="stop"`?
- **Nivel 2 — Coherencia (semi-auto):** ¿precios en rango de los ejemplos de referencia? ¿duración coherente con horas y equipo?
- **Nivel 3 — Utilidad (humana):** ¿un PM usaría esto como punto de partida? ¿los riesgos son específicos o boilerplate?
El proyecto ya implementa **Nivel 1** en `app/services/evaluation.py::evaluate_estimation_structure`. La response trae el campo `validation` con el score y los issues legibles.

```bash
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \
  -d "{\"transcription\":$TRANS,\"preprocessing\":\"two_phase\"}" \
  | jq '.validation'
```

### 5.2 Hands-on: añadir un check (10 min)

> 📂 **Archivos a editar (los alumnos):**
- `estimator/app/services/evaluation.py` → añadir el booleano `has_risks_section`, sumarlo al array `checks` y al cálculo del `score`, y añadir el `issues.append(...)`.
- `estimator/app/schemas/estimation.py::StructureCheck` → añadir el campo `has_risks_section: bool` para que el response lo exponga.
- (No tocar) `estimator/app/routers/estimations.py` — sigue funcionando sin cambios porque hace `EstimationResponse(**result, validation=validation)`.
Pedir a los alumnos añadir un check de “sección de riesgos presente”. En `app/services/evaluation.py`, dentro de `evaluate_estimation_structure`, añadir tras el bloque de las secciones:

```python
has_risks_section = bool(
    re.search(r"##\s+(Risks?|Risks?\s+and\s+assumptions)", text, re.IGNORECASE)
)
```
Sumarlo al array `checks` y a la lista de `issues`:

```python
checks: list[bool] = [
    has_title,
    has_breakdown_table,
    has_totals_section,
    has_team_section,
    has_duration_section,
    has_risks_section,        # nuevo
    bool(hours_match),
    bool(cost_match),
    finish_reason_ok,
]
# ...
if not has_risks_section:
    issues.append("Missing risks and assumptions section")
```
Y añadir el campo correspondiente en `StructureCheck` (`app/schemas/estimation.py`).

Volver a ejecutar el curl y verificar que el nuevo check aparece. Discusión: con `PROMPT_OUTPUT_BASIC` falla; con `PROMPT_OUTPUT_STRUCTURED` pasa.


### 5.3 Puesta en común

- ¿Cuántos pasaron todos los criterios de Nivel 1?
- ¿Cuál fue el issue más común? (probablemente `cost_match` o sección de riesgos)
- ¿Quién tiene `score < 0.6`? Investigar en directo el `estimation` y el `system prompt` que envió.
> 💡 La evaluación profunda (frameworks tipo RAGAS) llega en el Módulo 4. Pero el **mindset** de evaluar cada output con criterios explícitos empieza hoy. Si no sabes qué es una buena estimación, no sabes si tu sistema funciona.

---


## Bloque 6 — Cierre y puente a la Sesión 03 (15’)

> 📂 **Mapa de archivos tocados o creados durante la sesión** (proyectar como recapitulación final):
| Archivo | Qué hace |
|---|---|
| `estimator/app/schemas/estimation.py` | Contrato del request/response. Campos `preprocessing`, `example_format`, `num_examples`, `use_examples`, `model`, `max_tokens`, `thinking_budget`, `evaluate` + `StructureCheck`. |
| `estimator/app/context/examples.py` | Fuente única `CANONICAL_EXAMPLES` (5 ejemplos calibrados) + 3 formatters (`_format_markdown`, `_format_json`, `_format_narrative`) + `select_examples`. |
| `estimator/app/services/llm_service.py` | `GenerationOptions`, `build_system_prompt`, `extract_requirements`, `generate_estimation`, switch `ACTIVE_OUTPUT_PROMPT`, soporte de `thinking_budget`. |
| `estimator/app/services/evaluation.py` | Validación estructural Nivel 1 (regex puro). Tras el hands-on incluye `has_risks_section`. |
| `estimator/app/routers/estimations.py` | Endpoint que ata el request → `GenerationOptions` → `generate_estimation` → `evaluate_estimation_structure` → response. |
| `estimator/app/fixtures/long_transcription.txt` | Reunión Acme Foods (~5.000 palabras, kickoff + deep-dive). El payload estrella de la sesión. |
| `estimator/app/fixtures/short_transcription.txt` | Brief limpio de control para comparativas. |
| `estimator/.env`, `estimator/.env.example` | `LLM_PROVIDER`, `LLM_MODEL` por defecto. |
| `estimator/docker-compose.yml` | Bind mount `./app:/app/app` + `--reload` que hace posibles las ediciones en vivo. |

### Recapitulación

> “Al llegar hoy teníais un endpoint que devolvía estimaciones genéricas. Ahora tenéis:
- **Preprocesamiento configurable** del input (none / inline_cleaning / two_phase)
- **Contexto CAG iterado** en formato y cantidad
- **Un system prompt** que define exactamente qué estructura tiene la estimación
- **Configuración consciente** de modelo, `max_tokens`, `thinking_budget`
- **Evaluación estructural Nivel 1** que les dice si su sistema funciona
Esto **es** una arquitectura CAG funcional. No un prototipo — una primera versión de producto.”


### Anticipo de la Sesión 3

Demos rápidas de las limitaciones actuales:

- “¿Qué pasa si la API de OpenAI se cae?” → No hay fallback de provider.
- “¿Y si quiero ver la estimación generándose en tiempo real?” → No hay streaming.
- “¿Dónde están las estimaciones de hoy?” → No hay logging persistente.
- “¿Cómo lo ofrezco al usuario sin que use curl?” → No hay UI.
> “Todo esto en la Sesión 03: wrappers de modelos con fallback, streaming, logging y trazabilidad, e interfaz Streamlit. La arquitectura CAG ya funciona — ahora la convertimos en un producto usable.”

### Indicaciones

- Material asíncrono de la Sesión 03 disponible en X (rellenar antes de la sesión).
- Pre-ejercicio: pensar qué interfaz mínima querrían sobre el endpoint actual.
- El código actual es la base. **Nada se descarta.**

---


## Anexo A — Fragmentos de código clave (referencia rápida)


### Shape del request (`app/schemas/estimation.py`)

```python
class EstimationRequest(BaseModel):
    transcription: str  # min 50 chars
    preprocessing: Literal["none", "inline_cleaning", "two_phase"] = "none"
    example_format: Literal["markdown", "json", "narrative"] = "markdown"
    num_examples: int = 3      # 0..5
    use_examples: bool = True
    model: str | None = None
    max_tokens: int = 4000     # 0..16000
    thinking_budget: int | None = None   # Anthropic only
    evaluate: bool = True
```

### Shape de la respuesta

```python
class EstimationResponse(BaseModel):
    estimation: str
    model: str
    provider: str
    usage: TokenUsage  # input/output/total + preprocessing_input/output
    finish_reason: str
    preprocessing: str
    extracted_requirements: str | None
    latency_ms: int
    validation: StructureCheck | None
```

### `GenerationOptions` (`app/services/llm_service.py`)

```python
@dataclass
class GenerationOptions:
    preprocessing: PreprocessingMode = "none"
    example_format: ExampleFormat = "markdown"
    num_examples: int = 3
    use_examples: bool = True
    model: str | None = None
    max_tokens: int = DEFAULT_MAX_TOKENS  # 4000
    thinking_budget: int | None = None
```

### Switch del Bloque 3.4

Una sola línea en `app/services/llm_service.py`:

```python
ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_BASIC          # versión "antes"
# ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_STRUCTURED  # versión "después"
```

### Núcleo de `evaluate_estimation_structure`

```python
checks = [
    has_title, has_breakdown_table, has_totals_section,
    has_team_section, has_duration_section,
    bool(hours_match), bool(cost_match), finish_reason_ok,
]
score = round(sum(checks) / len(checks), 3)
```

---


## Anexo B — Tabla de precios de modelos

> Multiplicar `usage.input_tokens` y `usage.output_tokens` por la fila correspondiente.
| Modelo | $/M input | $/M output |
|---|---|---|
| gpt-4o-mini | 0.15 | 0.60 |
| gpt-4o | 2.50 | 10.00 |
| claude-haiku-4-5 | 1.00 | 5.00 |
| claude-sonnet-4-6 | 3.00 | 15.00 |
Los precios están **fuera del código** a propósito (cambian); se muestran y discuten aquí en pizarra.


---


## Anexo C — Troubleshooting en vivo

| Problema | Diagnóstico | Acción |
|---|---|---|
| `finish_reason="length"` sistemático | `max_tokens` por defecto se queda corto con `num_examples=5` y formato `narrative`, o con la transcripción larga de 5.000 palabras | Subir `max_tokens` en el body a 6000. |
| Cambié `ACTIVE_OUTPUT_PROMPT` y no se aplica | El bind mount de Compose no está activo (lanzaste con `docker run` directo) o la imagen se construyó sin `--reload` en el `command` | Levantar siempre con `docker compose up`; verificar en `docker compose logs -f estimator` que aparece `Reloading...`. |
| Cambié `.env` y sigue el provider/modelo anterior | Compose lee `.env` solo al crear el contenedor; el `--reload` de uvicorn solo cubre cambios de código | `docker compose up -d --force-recreate estimator`. |
| `thinking_budget` no surte efecto | Provider activo es OpenAI | Mirar `docker compose logs -f estimator`; debe aparecer `thinking_budget_ignored_for_provider`. Cambiar `.env` a `LLM_PROVIDER=anthropic` + recrear contenedor. |
| `validation.cost_match=False` siempre | El modelo está sumando mal o redondeando | Comparar `declared_total_cost` y `sum_row_cost` en el body — la tolerancia es ±2%. Subir a un modelo mejor o aumentar `num_examples`. |
| El curl tarda > 30s y no responde | El contenedor está parado o el modelo en cuestión es muy lento (o el LLM provider está caído) | `docker compose ps` para confirmar que está `Up`; `docker compose logs --tail=50 estimator` para ver el error real. |
| `ModuleNotFoundError: app.fixtures` | No aplica — `fixtures/` es un directorio de assets, no un módulo Python | Acceder a la transcripción como archivo (`jq -Rs . < ...`), no como import. |
> 💡 **Regla de oro de la sesión:** si algo falla en vivo y el grupo se desconecta, mejor saltar al siguiente bloque y volver al final. No dedicar más de 3 minutos al mismo bug en directo.
