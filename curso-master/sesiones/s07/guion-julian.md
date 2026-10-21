# Guion Julián · Sesión 7 LIDR

**Antes de empezar** (PowerShell, desde el worktree de la sesión):

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s07"
```

---

**1 · Estructura del repo**

Enseñar la estructura del repo y el tema de las ramas. Recorrer las carpetas: `foundation/`, `domain/`, `generation/` (con `cag/`, `rag/`, `agentic/` y `conversation/`), `ingestion/` y `api/`. Lo de hoy vive entero en `app/generation/rag/`.

---

**2 · El chunking del ejercicio previo y los esquemas**

En el ejercicio previo se hace un chunking estructural y da buenos resultados porque el corpus es un JSON bien organizado. Con un texto más libre, el resultado sería más pobre.

Enseñar `app/generation/rag/schemas.py`:

- Los metadatos son muy importantes para mejorar el retrieval.
- La clase `Chunk` y `EmbeddedChunk`, que la extiende: básicamente es el chunk + el vector + los metadatos.

Es muy importante la calidad de los vectores y que haya poco ruido. Si los vectores están muy juntos, tienes un problema: si muchos salen con un score > 0,90, ¿con cuál te quedas?

Todo es heurístico.

Con los metadatos se pueden hacer filtros duros sobre los vectores o técnicas híbridas de recuperación.

---

**3 · Ingesta del corpus**

Con esto ya podemos hacer la ingesta de nuestro corpus. Lanzarla desde la terminal:

```powershell
$body = '{"budgets": ' + (Get-Content estimator\data\budgets_sample.json -Raw -Encoding UTF8) + '}'
```

```powershell
$r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/embeddings/ingest -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

```powershell
$r.stats
```

```powershell
$r.chunks | Select-Object -First 5 chunk_id, token_count, @{n='dims';e={$_.embedding.Count}}
```

Sale: 17 presupuestos, 60 chunks, 5970 tokens y unos 0,0001 $. Cada chunk con 1536 dimensiones.

Hay que pensar en la lógica de tu corpus para elegir la mejor estrategia, los metadatos, etc.

No indexamos las transcripciones: indexamos el output en JSON de un preprocesado de esas transcripciones. Así mejora mucho.

También es clave entender el uso que se le va a dar a esta pool de conocimiento para valorarlo.

---

**4 · La lógica del RAG y del proyecto**

Nuestro objetivo es tener una app agéntica que estime presupuestos. Por eso necesito ingestar un corpus de presupuestos verificados y preparados.

Si tenemos presupuestos malos, nos va a dar presupuestos malos.

---

**5 · Dimensiones: no obsesionarse**

No hay que obsesionarse con las dimensiones, porque tampoco aportan mucho.

Correr en la terminal la diferencia de latencia con dos tamaños de vector:

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --models small-1536,small-768 2>$null
```

Explicar qué hace la prueba: el mismo modelo (`text-embedding-3-small`) a 1536 y a 768 dimensiones, sobre los mismos chunks, comparando latencia y coseno.

Los dos dan buen resultado (coseno 0,9118 frente a 0,9117), pero la latencia del de 768 es mejor, así que para este caso es más interesante. Más dimensiones aquí no me están ayudando a afinar nada.

Es un ejemplo: hay que ver cada caso.

---

**6 · Las familias de chunking**

Explicar las familias de chunking. La típica es la mecánica: defines un tamaño y cortas.

Enseñar en la web el Chunking Lab: structural frente a fixed-size, darle a comparar y ver los resultados. Explicar qué son p50 y p95.

<http://localhost:3000/rag/chunking_comparisons/new>

Todo esto está en `app/generation/rag/chunking/strategies/`: ahí se pueden explicar las distintas técnicas implementadas, un `.py` por estrategia.

El fixed-size es un ojete.

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies structural,fixed-size --show-stats 2>$null
```

Enseñar el recursive: cómo se hace y por qué da buenos resultados. Usa separadores naturales (doble salto, párrafo, punto). También tiene un máximo de tokens, pero se puede mejorar. Nos basamos en la agrupación mental que ya tenía el humano que escribió el documento.

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies recursive --show-stats 2>$null
```

Explicar qué son los obesos y los huérfanos.

Comparar structural frente a sentence-window: sentence-window mete muchos huérfanos. Mirar el min y el max en esta vista, con el número de tokens de los chunks.

```powershell
docker compose -p aieng-s07live exec estimator python scripts/compare_chunkers.py --strategies sentence-window,structural --show-stats --queries "OAuth authentication for fintech mobile app" --show-top-k 3 2>$null
```

Todo depende de tu corpus: hay que ensayarlo y hacer pruebas.

---

**7 · Lanzar comparativas en el Chunking Lab**

Lanzar comparativas en la web del Chunking Lab. El histórico está en:

<http://localhost:3000/rag/chunking_comparisons>

Ya guardadas, para abrir sin esperar:

- **#2** · las cuatro mecánicas: "Email and password login." cuela en el top-3 de OAuth.
- **#3** · structural + hierarchical: un padre entero entra en el top-3 de GDPR.
- **#4** · structural + semantic: el coste de ingesta de semantic.
- **#5** · structural + propositional: la proposición clavada (0,84) y 752 chunks.

---

**8 · Contextual Retrieval**

Decir que Contextual Retrieval es de las técnicas que mejor funcionan según Anthropic: hasta un −67 % de fallos de retrieval combinado con BM25 y reranking.

Enseñar `app/generation/rag/chunking/strategies/contextual_retrieval.py`.

Para cada chunk, un LLM genera un contexto que se le pega delante: es un "superchunk" que lleva información de lo que lo rodea en el documento.
