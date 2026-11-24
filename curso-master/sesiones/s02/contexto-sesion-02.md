# Sesión 02 — Primeros pasos de arquitectura CAG (contexto)

> Fichero de contexto para preparar la clase: descripción, encaje en el curso, montaje local, diferencias reales
> con el guion de LIDR y material. Guion oficial: [guion-directo.md](guion-directo.md). Guion propio:
> [guion-julian.md](guion-julian.md).

- **Clase:** martes 24/11/2026, 17:30–19:30 · edición **AI Engineering 2026-11** · TA: Santiago Gallardo · Zoom
  del calendario de la edición.
- **Ramas del repo:** `session_2` (punto de partida) y `session_2_live` (estado final del directo). Ojo: sin el
  cero (`session_2`, no `session_02`).
- **Grabación de la edición 2026-05 (mejor ROTI, Antonio Pérez):** https://vimeo.com/1197893325/d5e96ecf9c
- **Diapos oficiales (Google Slides del Notion):**
  https://docs.google.com/presentation/d/1RLQxnUh91h6ddAw36txXm86mhbDfBH9cpILfBfXPuxc — con la cuenta personal
  da «Acceso denegado» (23/11). Con la cuenta de LIDR se pueden exportar a PDF y dejar en
  `deck/plantilla-lidr-s02.pdf` (ver «Material»).

## 1. De qué va

Un endpoint que devuelve estimaciones genéricas se convierte en una arquitectura **CAG** funcional:

1. **Preprocesado configurable del input**: `none`, `inline_cleaning` (un párrafo más en el system prompt) y
   `two_phase` (extraer requisitos y luego estimar).
2. **El contexto CAG medido**: con y sin ejemplos, en tres formatos y con 0–5 ejemplos.
3. **El system prompt como multiplicador**: el interruptor `ACTIVE_OUTPUT_PROMPT` (BASIC → STRUCTURED).
4. **Parámetros del modelo**: tier (económico/premium), `max_tokens` y `finish_reason`, `thinking_budget`.
5. **Evaluación estructural de nivel 1**: ocho comprobaciones con regex → `score` + `issues`; hands-on para
   añadir `has_risks_section`.

Todo pasa por un único endpoint, `POST /api/v1/estimate`, y se compara con cuatro números de la respuesta:
`usage`, `latency_ms`, `finish_reason` y `validation.score`.

## 1 bis. Ejercicio previo («Scaffolding del proyecto FastAPI», plataforma de LIDR, entrega 22/11)

Montar desde cero un servicio FastAPI con `uv` (Python 3.11+): `app/` con `main.py`, `config.py` (Pydantic
Settings desde `.env`), `routers/estimations.py`, `services/llm_service.py`, `schemas` y `context/examples.py`
con **al menos dos** estimaciones de ejemplo. `POST /api/v1/estimate` recibe `{"transcription": …}` y devuelve
`{"estimation", "model", "provider"}`; mensajes `[system]` = instrucciones + ejemplos, `[user]` = transcripción.
Al menos un proveedor. `GET /health`, Swagger en `/docs`, `.env` en `.gitignore`. La calidad no importa todavía:
basta con que el flujo funcione. Se les da el proyecto resuelto por si se atascan.

Diferencias con lo que se usa en clase: el enunciado pide arrancar con `uv run uvicorn` (sin Docker); la clase usa
Docker Compose. Su carpeta se llama `estimador-cag/` y sus ejemplos son de 2 en adelante, con otro formato; la
rama de la clase trae 5 ejemplos canónicos, las fixtures y los mandos nuevos. Un comentario en la plataforma
señala que la redacción del paso 5 confunde («llame al servicio LLM mediante Postman/curl»).

## 2. Encaje en el curso

| # | Sesión | Relación con la S2 |
|---|---|---|
| 00 | Bienvenida | Entorno, Colab y APIs. |
| 01 | LLMs y setup | Primeras llamadas a OpenAI/Anthropic/Gemini, parámetros y tokens. La S2 parte de ahí: el proyecto `estimator/` levantado y un endpoint que estima. **La dio Julián a esta misma edición el 17/11.** |
| **02** | **Primeros pasos de CAG** | **Hoy.** |
| 03 | Wrappers de modelos | Convierte `_call_openai` / `_call_anthropic` en un wrapper: fallback de proveedor, streaming, logging y trazabilidad. Es el «Anticipo» del Bloque 6. |
| 04 | Productos IA avanzados | Plantillas de prompt desde backend, **salida estructurada con validadores** (resuelve el problema de las sumas que hoy se ve en todas las ejecuciones), guardrails y caché semántica. |

## 3. Montaje local (23/11/2026)

- Worktree `ai-engineering-fork-julian\ai-engineering-s02`, rama **`session_02_live_local`** (sale de
  `origin/session_2_live`, subida al fork).
- Un solo servicio, sin bases de datos ni Rails: el compose está en `estimator/`. Se levanta con
  `cd estimator; docker compose -p aieng-s02live up -d --build` → contenedor **`s02-estimator`**, puerto 8000.
  Imagen ligera (FastAPI + SDKs, sin torch): la build tarda segundos.
- Parches de la rama local (commit `e523003`): `docker-compose.override.yml` (`container_name: s02-estimator`
  y `./tests` montado), `uv.lock` resuelto el 23/11 y las cabeceras «Julián · Sesión 2» en los 8 ficheros de
  clase y los 5 de tests.
- `estimator/.env` (no se sube): `OPENAI_API_KEY` copiada de la S6, `LLM_PROVIDER=openai`,
  `LLM_MODEL=gpt-4o-mini`. **No hay `ANTHROPIC_API_KEY`**: las demos de Claude y `thinking_budget` no se pueden
  ejecutar.
- Tests en el host: `cd estimator; uv sync; uv run pytest -v` → **21 passed en 0,08 s** (ninguno llama a
  OpenAI: `_call_openai` se sustituye por un falso).
- Docker Desktop no arrancaba (23/11) por el `.sock.stale` de siempre: arreglado renombrando
  `%LOCALAPPDATA%\Docker\run` y `docker-secrets-engine` (`*-roto-154403`).

## 4. Diferencias con el guion de LIDR

Medidas el 23/11 con `gpt-4o-mini` y la transcripción larga (una ejecución por caso; salidas completas en
`comandos/salidas/*.json` y en `historico-s02.html`). Coste total: unas 20 llamadas, ≈ 0,10 $.

| Guion | Lo que pasa de verdad |
|---|---|
| `none` debería dar un score bajo por el ruido | 0.625. El issue «Missing breakdown table» es engañoso: **la tabla está**, pero el modelo añadió una columna `Description` y el regex exige exactamente `\| Task \| Hours \| Cost`. Sin esa cabecera tampoco suma filas. |
| inline_cleaning ~+50 tokens, score medio | +65 tokens (8.558 frente a 8.493) y **0.75**: ya produce la tabla con la cabecera esperada. |
| two_phase: score alto, ~2× latencia, ~1,5× coste | 0.75 (igual que inline). La estimación recibe 1.758 tokens; la fase 1, 7.190 + 395. Latencia 21,9 s frente a 20,2 s de `none` (no el doble). Los requisitos extraídos sí son muy buenos: SAP → BCN-Touch, depósitos, GDPR, WCAG AA. |
| Con/sin contexto | Funciona como dice el guion: **0.375 sin ejemplos** (ni título, ni tabla, ni totales) frente a **0.75 con ejemplos**. Los ejemplos pesan 1.265 tokens. |
| Formatos: «¿cuál produjo la más útil?» | **JSON se contagia**: con ejemplos en JSON, el modelo contesta con un bloque ```` ```json ```` → score **0.25**. Narrative 0.5. Markdown 0.75. Muy buen momento de clase: el formato del contexto es una instrucción implícita. |
| N ejemplos: «la calidad mejora mucho entre 1 y 3» | Tokens lineales (+≈430 por ejemplo: 7.228 / 7.676 / 8.493 / 9.388), pero el score es **0.5 / 0.625 / 0.625 / 0.625**: el salto está entre 0 y 1 y luego se estanca. La latencia es ruido (una sola ejecución). |
| STRUCTURED: «la validation.score se nos va al techo» | **0.75, no 1.0.** Aparecen todas las secciones (también riesgos) y la respuesta se acorta (568 frente a 795 tokens), pero **las filas no suman el total** (292 h frente a 320). |
| — | **En ninguna de las 19 peticiones las filas sumaron el total declarado**, tampoco con `gpt-4o` (432 frente a 418). Por eso casi todo se queda en 0.75: `hours_match` y `cost_match` fallan siempre. Es el puente natural a la S4 (salida estructurada con validadores). |
| gpt-4o-mini frente a gpt-4o | Mismo score (0.75). gpt-4o tardó **menos** (8,0 s frente a 14,6 s) y cuesta ≈ 17× (0,0293 $ frente a 0,0017 $ por estimación). |
| `max_tokens=200` corta a mitad de la tabla | Igual: `finish_reason=length`, score 0.25 y el issue «Response truncated…». |
| `thinking_budget` con OpenAI: warning en logs | Igual: `thinking_budget_ignored_for_provider provider=openai`. |
| Anthropic (haiku / sonnet, thinking) | **No ejecutado**: no hay `ANTHROPIC_API_KEY`. |
| Hands-on 5.2: «con BASIC falla, con STRUCTURED pasa» | Correcto con las salidas guardadas (0.556 / 0.778 con 9 checks). Pero **al añadir el check fallan 2 tests existentes** (`test_well_formed_estimation_passes_all_checks` y el de `end_turn`: `assert 0.889 == 1.0`): **los 5 ejemplos canónicos no tienen sección de riesgos**. Y por eso el modelo, que imita los ejemplos, no la escribe con BASIC. Buen remate: un check nuevo cambia lo que es «bien formado» y obliga a tocar ejemplos o prompt y tests. |
| PowerShell | `Get-Content -Raw` + `ConvertTo-Json` envía un objeto con propiedades de PowerShell → 422 «Input should be a valid string». Usar `[IO.File]::ReadAllText`. |

## 5. Material

| Fichero | Qué es |
|---|---|
| `deck/build_deck.py` → `Sesion02-Julian-Fernandez.pdf` | 23 diapos: portada, ROTI y «Gracias» de la plantilla de LIDR sin tocar; 20 propias con franja «En el código» y, nueva, «En los tests». Si se consigue el PDF oficial (`deck/plantilla-lidr-s02.pdf`), sus páginas entran **sin tocar** y las nuestras detrás de la que amplían (lista `ORIGINALES` del script). |
| `comandos/build_comandos.py` → `S02-comandos-y-salidas.pdf` | Para alumnos: cada comando (bash + PowerShell), salida real, cómo leerla y el test que lo comprueba. |
| `comandos/build_historico.py` → `historico-s02.html` | Las 19 respuestas guardadas en una tabla; pulsando una fila se ve la estimación completa. Para enseñar sin volver a pagar. |
| `comandos/salidas/` | Respuestas completas (`.json`), resúmenes (`.txt`), tests, logs y el hands-on 5.2. |
| `guion-julian.md` | Guion propio diapo a diapo. |
| `guion-directo.md` | Guion oficial de LIDR. |
