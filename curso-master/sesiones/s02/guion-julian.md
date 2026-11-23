# Sesión 2 · Guion de Julián — Primeros pasos de arquitectura CAG

Martes 24/11/2026, 17:30–19:30 · edición 2026-11 · TA Santiago Gallardo. Deck: `Sesion02-Julian-Fernandez.pdf`
(23 diapos). Alumnos: `S02-comandos-y-salidas.pdf`. Histórico: `historico-s02.html`.

Todas las salidas que se citan son reales (23/11, `gpt-4o-mini`) y están en `comandos/salidas/`. **No hace falta
relanzar nada**: si no quieres gastar o va lento, enseña el histórico. Cada petición en directo cuesta ≈ 0,002 $
(gpt-4o-mini) y tarda 12–22 s.

## Antes de empezar (17:15)

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s02\estimator"
$env:Path += ";C:\Program Files\Docker\Docker\resources\bin"
docker compose -p aieng-s02live up -d
docker compose -p aieng-s02live ps
curl.exe -s http://localhost:8000/health
```

Terminal 2 (logs, a la vista toda la clase):

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s02\estimator"
docker compose -p aieng-s02live logs -f estimator
```

Terminal 1, variables y el helper `est` (probado el 23/11; **no usar `Get-Content -Raw`**, mete propiedades de
PowerShell en el JSON y da 422):

```powershell
$BASE  = "http://localhost:8000"
$TRANS = [IO.File]::ReadAllText("$PWD\app\fixtures\long_transcription.txt")
$SHORT = [IO.File]::ReadAllText("$PWD\app\fixtures\short_transcription.txt")
function est([hashtable]$extra = @{}, [string]$t = $TRANS) {
  $h = @{transcription = $t}; foreach ($k in $extra.Keys) { $h[$k] = $extra[$k] }
  $b = $h | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "$BASE/api/v1/estimate" -ContentType 'application/json; charset=utf-8' `
    -Body ([Text.Encoding]::UTF8.GetBytes($b))
}
function ver($r) { $r | Select-Object model, finish_reason, latency_ms, @{n='score';e={$_.validation.score}}; $r.validation.issues; $r.usage }
```

VS Code ya abierto con los ficheros en orden (ver el final). Histórico abierto en el navegador.

---

## Diapo 1 · Portada — Diapo 2 · Hoy (2')

Mapa de los 6 bloques. Lo importante: **los cuatro números** (`usage`, `latency_ms`, `finish_reason`,
`validation.score`) con los que se compara todo hoy.

## Diapo 3 · Bloque 1 · Errores típicos (5')

Pregunta de apertura: «¿Quién consiguió que su endpoint devolviera una estimación? ¿Y quién la leyó y pensó
"esto no se lo puedo enviar a un cliente"?». Tabla de errores. VS Code: `app/config.py:30`
(`validate_api_key_for_provider`) y `:39` (`@lru_cache`). Si más de tres tienen el mismo error, se resuelve en
pantalla.

Preguntas rápidas: cuántos ejemplos pusieron, qué formato, OpenAI o Anthropic, **¿alguien probó sin ejemplos?**
(trampa pedagógica: quien lo probó ya vio que sale genérico).

## Diapo 4 · Setup y sanity check (3')

```powershell
ver (est @{} $SHORT)          # ≈ score 0.75, 12 s
```

Salida guardada: `04_sanity_short` → `score 0.75`, `latency_ms 12623`. VS Code: `docker-compose.yml:23`
(`env_file`) y `:33` (`--reload`). Las dos reglas: el código se aplica al guardar; `.env` exige
`--force-recreate`.

Tests (gratis, 0,08 s), en otra terminal:

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s02\estimator"
uv run pytest -v
```

## Diapo 5 · Qué es CAG (3')

Pregunta: «En el system prompt de la S1, ¿le dimos información del dominio o solo el rol?». El diagrama. VS Code:
`app/context/examples.py:36` (`CANONICAL_EXAMPLES`). Contrapartida: 8.493 tokens con 3 ejemplos frente a 7.228
sin ellos, en **cada** llamada.

## Diapo 6 · Bloque 2.1 · Una petición, fichero a fichero (8')

Lanzar la petición y, mientras tarda (~20 s), recorrer los ficheros en el orden de VS Code:

```powershell
$r = est @{preprocessing = "none"}; ver $r
```

| # | Fichero:línea | Qué decir |
|---|---|---|
| 1 | `app/main.py:74` | `include_router`: monta el endpoint |
| 2 | `app/routers/estimations.py:24` | Entra la petición; `GenerationOptions` (l. 26) |
| 3 | `app/schemas/estimation.py:20` | El contrato; `transcription` ≥ 50 caracteres (l. 23) → 422 gratis |
| 4 | `app/services/llm_service.py:185` | `generate_estimation`: el orquestador |
| 5 | `llm_service.py:102` y `:133` | `build_system_prompt`: la lista `sections` **es el CAG** |
| 6 | `app/context/examples.py:392` | Una fuente, tres formatos |
| 7 | `llm_service.py:264` | `_call_openai`: lo único que se paga |
| 8 | `app/services/evaluation.py:32` | El termómetro, regex sin LLM |
| 9 | vuelta a `estimations.py:42` | `validation = …` y la respuesta |

Si quieres enseñar el 422: `try { est @{num_examples = 9} } catch { $_.ErrorDetails.Message }` (gratis).

## Diapo 7 · Bloque 2.2 · La transcripción real (4')

Abrir `app/fixtures/long_transcription.txt` (5.000 palabras, Acme Foods). Con la salida de `none` (guardada:
`05_none`, **0.625**): ¿PWA, WCAG, UE? ¿SAP o BCN-Touch? Ojo al issue «Missing breakdown table»: **la tabla
está**, el modelo metió una columna `Description` y el regex (`evaluation.py:21`) pide la cabecera exacta.
Primera lección de evaluación: el termómetro también se equivoca.

## Diapo 8 · Bloques 2.3–2.4 · inline_cleaning y two_phase (9')

VS Code: `llm_service.py:66` (`INLINE_CLEANING_BLOCK`), `:142` (`extract_requirements`), `:199` (la rama).

```powershell
ver (est @{preprocessing = "inline_cleaning"})     # guardado: 0.75 · 13,0 s · 8.558 in
$r2 = est @{preprocessing = "two_phase"}; ver $r2   # guardado: 0.75 · 21,9 s · 1.758 in + 7.190/395 de fase 1
$r2.extracted_requirements
```

Hands-on (3'): editar `INLINE_CLEANING_BLOCK` (añadir «extract budget and deadlines explicitly»), guardar,
mirar `Reloading...` en los logs y repetir.

## Diapo 9 · Lo que devuelve la fase 1 (2')

El `extracted_requirements` real: BCN-Touch (no SAP), depósitos configurables, GDPR con exportación y borrado,
WCAG AA. «Más llamadas no siempre es mejor»: aquí two_phase empata con inline_cleaning en score.

## Diapo 10 · Bloque 3.1 · Con y sin contexto (5')

```powershell
ver (est @{use_examples = $false})   # guardado: 0.375 · sin título, sin tabla, sin totales
ver (est @{use_examples = $true})    # guardado: 0.75
```

VS Code: `llm_service.py:121`. Frase: «El modelo es el mismo. La pregunta es la misma. Lo único que cambió es el
contexto inyectado. **Esto** es CAG».

## Diapo 11 · Bloque 3.2 · Formato (8')

```powershell
foreach ($f in "markdown","json","narrative") { $r = est @{example_format = $f}; "$f  in=$($r.usage.input_tokens)  score=$($r.validation.score)" }
```

Guardado: markdown 0.75 / json **0.25** / narrative 0.5. Con JSON **responde en JSON** (abrir
`11_formato_json` en el histórico). VS Code: `examples.py:408`, `:419`, `:437`. Hands-on: cada uno elige formato.

## Diapo 12 · Bloque 3.3 · Cantidad (8')

```powershell
foreach ($n in 0,1,3,5) { $r = est @{num_examples = $n}; "n=$n in=$($r.usage.input_tokens) out=$($r.usage.output_tokens) ms=$($r.latency_ms) score=$($r.validation.score)" }
```

Guardado: 7.228 / 7.676 / 8.493 / 9.388 tokens; score 0.5 / 0.625 / 0.625 / 0.625. **No coincide con el guion**
(«mejora mucho entre 1 y 3»): aquí el salto es de 0 a 1 y luego plano. Decirlo tal cual: una ejecución por fila
es poco; la tendencia de tokens es lo sólido. VS Code: `examples.py:387`, `schemas/estimation.py:33`.

## Diapo 13 · Bloque 3.4 · BASIC → STRUCTURED (5')

```powershell
ver (est)    # BASIC, guardado: 0.625, falta «Total cost»
```

En VS Code, `llm_service.py:63`: cambiar a `ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_STRUCTURED`, **guardar**, enseñar
`WatchFiles detected changes … Reloading` en la terminal de logs, y:

```powershell
ver (est)    # STRUCTURED, guardado: 0.75, con riesgos, 568 tokens de salida
```

**Al terminar, volver a poner `PROMPT_OUTPUT_BASIC`** (la rama local está en BASIC).

## Diapo 14 · Lo que el prompt no arregla: las sumas (3')

Tabla de declarado frente a suma de filas. Ninguna de las 19 peticiones cuadró, ni con gpt-4o. VS Code:
`evaluation.py:81` y `:87` (tolerancias). Puente a la S4: validadores en el schema que re-preguntan al modelo.

## Diapo 15 · Bloque 4.1 · Tier de modelo (8')

```powershell
foreach ($m in "gpt-4o-mini","gpt-4o") { ver (est @{model = $m}) }
```

Guardado: los dos 0.75; gpt-4o 8,0 s frente a 14,6 s y ≈ 17× más caro (0,0293 $ frente a 0,0017 $). Anthropic:
**no hay clave**, no se puede enseñar en directo. Explicar el `@lru_cache` (`config.py:39`) y
`docker compose -p aieng-s02live up -d --force-recreate estimator`.

## Diapo 16 · Bloque 4.2 · max_tokens y thinking (6')

```powershell
ver (est @{max_tokens = 200})                                    # length · 0.25
ver (est @{thinking_budget = 2000; max_tokens = 6000} $SHORT)    # se ignora con OpenAI
```

En la terminal de logs sale `thinking_budget_ignored_for_provider provider=openai`. VS Code: `llm_service.py:278`
y `:226`, y `:321` para el camino de Anthropic.

## Diapo 17 · Bloque 5.1 · Tres niveles de evaluación (4')

«Imaginad 100 estimaciones: ¿cuántas son buenas?». Nivel 1 automatizable (lo de hoy), 2 semiautomático,
3 humano. VS Code: `evaluation.py:94` (`checks`) y `:104` (`score`). Enseñar `$r2.validation` (two_phase).

## Diapo 18 · Bloque 5.2 · Hands-on: has_risks_section (10')

Los alumnos editan `app/services/evaluation.py` (booleano, `checks`, `issues`, `StructureCheck(...)`) y
`app/schemas/estimation.py:75`. **No editar en la rama local durante la clase** si luego hay que repetir demos;
si se hace, `git checkout -- app` al terminar.

Lo que pasa (probado en una copia, salidas `27`–`29`): reevaluando, BASIC 0.556 y STRUCTURED 0.778; **y fallan 2
tests existentes** (`assert 0.889 == 1.0`) porque los ejemplos canónicos no tienen riesgos. Discusión: ¿añadir
riesgos a los ejemplos o pedirlos en el prompt?

## Diapo 19 · Los tests de la sesión (3')

`uv run pytest -v`: 21 tests en 0,08 s, sin red. El falso de `_call_openai` (`tests/test_estimate_endpoint.py:35`)
recorre el mismo camino que la petición real. Uno solo:
`uv run pytest tests/test_evaluation.py::test_missing_table_is_detected -v`.

## Diapo 20 · Recapitulación — Diapo 21 · Sesión 3 (5')

La respuesta de entrevista. Lo que falta: fallback, streaming, registro persistente e interfaz → S3. Nada se
descarta.

## Diapo 22 · ROTI — Diapo 23 · Gracias

---

## Ficheros en VS Code (orden de clase)

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s02\estimator"
code . -g docker-compose.yml:23 -g app/config.py:30 -g app/main.py:74 -g app/routers/estimations.py:24 -g app/schemas/estimation.py:20 -g app/services/llm_service.py:102 -g app/context/examples.py:36 -g app/services/evaluation.py:32 -g app/fixtures/long_transcription.txt:1 -g tests/test_estimate_endpoint.py:35 -g tests/test_evaluation.py:13 -g tests/test_examples_format.py:21
```

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| Docker Desktop no arranca («…sock.stale: El sistema no tiene acceso al archivo») | Matar procesos de Docker, renombrar a la vez `%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine`, relanzar. Nunca «Reset to factory defaults». |
| 422 «Input should be a valid string» desde PowerShell | Se leyó con `Get-Content -Raw`. Usar `[IO.File]::ReadAllText`. |
| `/health` no responde justo tras guardar código | Es la recarga de uvicorn: repetir a los 10 s. |
| Cambié el prompt y no se aplica | Mirar la terminal de logs: debe salir `Reloading...`. Si no, `docker compose -p aieng-s02live up -d`. |
| Cambié `.env` y sigue igual | `docker compose -p aieng-s02live up -d --force-recreate estimator`. |
| OpenAI lento o caído | Enseñar `historico-s02.html` (todas las respuestas reales guardadas). |
| 500 «LLM call failed» | `docker compose -p aieng-s02live logs --tail=50 estimator` y ver el error real (saldo, clave, modelo). |
| Piden Anthropic | No hay clave en el `.env`: explicarlo con el código (`_call_anthropic`, l. 302 y 321). |

## Después de clase

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s02\estimator"
git status    # que ACTIVE_OUTPUT_PROMPT siga en BASIC y no haya restos del hands-on
docker compose -p aieng-s02live down
```
