# Sesión 7 · Guion de Julián — Embeddings y representación vectorial

Jueves 26/11/2026, 17:30–19:30 · edición **2026-10** · TA **Sisley Jiménez**. Con este grupo diste la S5 (12/11) y
la S6 (19/11): vienen de dejar el corpus limpio, catalogado y pseudonimizado. Deck: `Sesion07-Julian-Fernandez.pdf`
(32 diapos: las 12 originales de LIDR sin tocar + 20 nuestras). Alumnos: `S07-comandos-y-salidas.pdf`. El de la
edición 2609 está en `anterior-2609/`.

Salidas reales del 24/11 en `comandos/salidas/` (coinciden con las del 21/10). **Abre los PDF en Chrome**, no en Edge.

## Antes de empezar (17:15)

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s07"
$env:Path += ";C:\Program Files\Docker\Docker\resources\bin"
docker compose -p aieng-s07live up -d
docker compose -p aieng-s07live ps
curl.exe -s http://localhost:8000/health
```

Abrir en Chrome: el deck, el PDF de comandos, `http://localhost:3000/rag/chunking_comparisons` (histórico) y
`http://localhost:3000/rag/chunking_comparisons/new`. VS Code con los ficheros en orden (al final).

---

## Diapo 1 · Portada (original) — Diapo 2 · Hoy — Diapo 3 · Para qué sirve y dónde encaja (4')

Puente con la S6, que diste tú: «el jueves pasado dejamos el corpus limpio, validado y sin PII; hoy lo convertimos en
vectores». pgvector y la búsqueda de verdad son la S8. Los dos presupuestos trampa: MONO-001 (1.391 tokens) y el MVP
de una línea.

## Diapo 4 · Tres arquitecturas (original) (4')

Estructura del repo por capas: `foundation/`, `domain/`, `generation/` (`cag/`, `rag/`, `agentic/`,
`conversation/`), `ingestion/`, `api/`. Lo de hoy vive entero en `app/generation/rag/`.

## Diapo 5 · El sanity check (5')

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare.py --text-a "Backend services" --text-b "API development"
```

Sale 0,5407. Las tres parejas: 0,5957 / 0,1920 / 0,5407. La C es la que justifica la cabecera de contexto.
VS Code: `estimator/scripts/compare.py:43`.

## Diapo 6 · Cinco patrones de error (original) (3')

Pregunta gancho: «vuestro chunker no truncó esa descripción de 1.391 tokens… ¿está bien o está mal?».

## Diapos 7-9 · Chunk, token y vector · Similitud · Modelos (10')

VS Code: `app/generation/rag/schemas.py:65` (`Chunk`) y `:78` (`EmbeddedChunk`: chunk + vector + metadatos);
`analysis/similarity.py:14`; `embedding/embedder.py:36` (0,02 $/M). Los metadatos son los que permitirán filtros
duros (S8) y búsqueda híbrida (S10). Si muchos chunks salen por encima de 0,90, ¿con cuál te quedas? Todo es
heurístico.

Ingesta en directo (≈ 0,0001 $):

```powershell
$body = '{"budgets": ' + [IO.File]::ReadAllText("$PWD\estimator\data\budgets_sample.json") + '}'
$r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/embeddings/ingest -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
$r.stats
$r.chunks | Select-Object -First 5 chunk_id, token_count, @{n='dims';e={$_.embedding.Count}}
```

17 presupuestos → 60 chunks → 5.970 tokens → 0,00012 $ · 1536 dimensiones. No indexamos transcripciones: indexamos
presupuestos ya preparados. Presupuestos malos → estimaciones malas.

## Diapo 10 · Matryoshka (original) — Diapo 11 · Dimensiones (5')

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --models small-1536,small-768 2>$null
```

24/11: 406 ms frente a 218 ms, coseno 0,9119 frente a 0,9116. No obsesionarse con las dimensiones. VS Code:
`scripts/compare_chunkers.py:166` (`run_models`). Lo que nunca: comparar 1536 con 768 (diapo 11, el 0,689).

## Diapo 12 · El chunk de nuestro proyecto (5')

VS Code: `chunking/structural.py:33` (`render_component_text`, la cabecera) y `:72` (`component_metadata`). El texto
se embebe; los metadatos van al lado para filtrar.

## Diapo 13 · Cuatro familias (original) — Diapo 14 · Cómo leer el Chunking Lab (5')

Abrir el Lab (`/rag/chunking_comparisons/new`): structural frente a fixed-size, comparar, explicar p50/p95,
huérfanos y obesos. VS Code: `chunking/base.py:56` (`Chunker`, la interfaz común) y `analysis/comparison.py:37-38`
(umbrales 20 y 800).

## Diapos 15-20 · Las mecánicas (15')

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies structural,fixed-size --show-stats 2>$null
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies recursive --show-stats 2>$null
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies sentence-window,structural --show-stats --queries "OAuth authentication for fintech mobile app" --show-top-k 3 2>$null
```

- fixed-size (`strategies/fixed_size.py:26`): línea base; solo parte MONO-001.
- recursive (`recursive.py:30`, los separadores): 23 chunks, mezcla componentes. Se apoya en cómo agrupó el texto
  quien lo escribió.
- sentence-window (`sentence_window.py:27`): 34 huérfanos; «Email and password login.» se cuela en el top-3 de
  OAuth.
- structural: el top-3 son los tres componentes del proyecto de banca.

Histórico guardado (sin esperar): **#2** las cuatro mecánicas (lo del «Email and password login.»).

## Diapos 21-24 · Semantic, propositional, contextual (12')

No se relanzan: histórico **#4** (semantic) y **#5** (propositional: la proposición clavada a 0,84 y 752 chunks).
Contextual Retrieval necesita clave de Anthropic, que no hay: números del informe (0,14 $, 203 s).
VS Code: `strategies/contextual_retrieval.py:55`. Anthropic: hasta −67 % de fallos de retrieval con BM25 y reranking.

## Diapos 25-26 · Hierarchical (5')

Histórico **#3**: un padre entero entra en el top-3 de GDPR. VS Code: `strategies/hierarchical.py:28`.

## Diapo 27 · Late chunking (2') — Diapo 28 · Cuadro de mando (5')

Tabla completa:

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies structural,fixed-size,recursive,sentence-window,hierarchical --queries all --output-table 2>$null
```

Pregunta del día: ¿con qué estrategia salís hoy a producción y qué mediríais antes de cambiarla?

## Diapo 29 · Los tests del Chunking Lab (3')

```powershell
docker compose -p aieng-s07live exec estimator-web bin/rails test -v test/models/rag test/controllers/rag test/services/estimator_ai/embeddings_client_test.rb
```

23 tests en 1,5 s, sin llamar a OpenAI. Las estrategias Python no tienen tests: se miden con números.

## Diapo 30 · Cierre y S8 (original) — 31 ROTI — 32 Gracias

---

## Ficheros en VS Code (orden de clase)

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s07"
code . -g estimator/scripts/compare.py:43 -g estimator/app/generation/rag/schemas.py:65 -g estimator/app/api/embeddings.py:34 -g estimator/app/generation/rag/embedding/embedder.py:36 -g estimator/app/generation/rag/analysis/similarity.py:14 -g estimator/scripts/compare_chunkers.py:166 -g estimator/app/generation/rag/chunking/structural.py:33 -g estimator/app/generation/rag/chunking/base.py:56 -g estimator/app/generation/rag/analysis/comparison.py:37 -g estimator/app/generation/rag/chunking/strategies/fixed_size.py:26 -g estimator/app/generation/rag/chunking/strategies/recursive.py:30 -g estimator/app/generation/rag/chunking/strategies/sentence_window.py:27 -g estimator/app/generation/rag/chunking/strategies/semantic.py:32 -g estimator/app/generation/rag/chunking/strategies/propositional.py:51 -g estimator/app/generation/rag/chunking/strategies/contextual_retrieval.py:55 -g estimator/app/generation/rag/chunking/strategies/hierarchical.py:28 -g estimator-web/app/controllers/rag/chunking_comparisons_controller.rb:31
```

Si `code` no abre ventana: lanzar antes `& "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe" .` y repetir con
`code -r`.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| Docker no arranca («…sock.stale: El sistema no tiene acceso al archivo») | Matar los procesos de Docker y renombrar a la vez `%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine`. Nunca «Reset to factory defaults». |
| Avisos de botocore/LiteLLM en la terminal | Añadir `2>$null` al comando. |
| `--strategies all` aborta | Falta la clave de Anthropic (contextual_retrieval): listar las estrategias a mano. |
| sentence-window falla por NLTK | Los datos `punkt` vienen en la imagen local; si se reconstruye, revisar el Dockerfile de la rama local. |
| El Lab tarda | Propositional tarda unos 3 minutos: enseñar el histórico (#2 a #5). |
| La cuadrícula blanca en el PDF | Es Edge: abrir en Chrome. |

## Después de clase

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s07"
docker compose -p aieng-s07live down
```
