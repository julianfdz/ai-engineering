# Línea de formación · Sesión 6 · Data-driven AI: análisis y normalización

> Edición 2026-10 · jueves 19/11/2026, 17:30 · TA: Sisley Jiménez.
>
> Diapo a diapo: **qué contar**, **qué fichero abrir** (y en qué línea), **qué lanzar** y **qué sale**. Las rutas son
> relativas a `estimator/`. En VS Code (carpeta `ai-engineering-s06`): Ctrl+P con el nombre y Ctrl+G con la línea.
> Cada fichero lleva arriba una cabecera «Sesión 6 · …» con para qué sirve.
>
> - Deck: [Sesion06-Julian-Fernandez.pdf](Sesion06-Julian-Fernandez.pdf) (25 diapos).
> - Para los alumnos: [S06-comandos-y-salidas.pdf](S06-comandos-y-salidas.pdf), con cada script, su salida real y cómo leerla.
> - El material de la edición 2609 (14/10) está en `anterior-2609/`.
>
> Formato: **no se teclea código**. Se abre, se explica y se ejecuta. Ninguna demo llama a un modelo: se pueden
> repetir sin coste.

---

## Antes de empezar (10 min antes)

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s06"
```

```powershell
docker compose -p aieng-s06live up -d
```

```powershell
docker compose -p aieng-s06live ps
```

Los cinco `s06-*` en `healthy`. Luego el pre-flight (8 ✅):

```powershell
docker compose -p aieng-s06live exec estimator python scripts/preflight_s06.py
```

Si sale ❌ en `/health` justo después de tocar código, es la recarga del servicio: repetir en 10 s.

**Ventanas:** VS Code con los 25 ficheros (abajo), el deck, el PDF de comandos y el Swagger
(<http://localhost:8000/docs>). La web de Rails no tiene nada de la S6.

**VS Code, en orden de clase:** `scripts/preflight_s06.py`, `app/ingestion/architecture.py`,
`catalog/inspect.py`, `catalog/models.py`, `catalog/loader.py`, `data/catalog/catalog.yaml`,
`documents/models.py`, `loaders/filesystem.py`, `parsers/protocol.py`, `parsers/budget_json.py`,
`parsers/transcript_txt.py`, `parsers/registry.py`, `orchestrator.py`, `app/routers/ingestion.py`,
`estimator-web/…/ingestion_client.rb`, `cleaning/budget_records.py`, `cleaning/schemas.py`, `cleaning/policy.py`,
`scripts/demo_cleaning_s06.py`, `pii/analyzer.py`, `pii/recognizers.py`, `pii/pseudonymizer.py`,
`pii/mapping_store.py`, `app/persistence/models.py` y `scripts/demo_pii_s06.py`.
(`catalog/`, `documents/`, `loaders/`, `parsers/`, `cleaning/` y `pii/` cuelgan de `app/ingestion/`.)

---

## Apertura · Diapos 1-2 · 3 min

- Hoy no se vectoriza nada: se prepara el corpus para que merezca ser vectorizado.
- El viaje del dato: decidir → catalogar → ingerir → limpiar → proteger. Todo en `app/ingestion/`.

## Bloque 0 · Diapo 3 · 7 min

- «¿Qué restricción del CAG se rompió primero?». Un número, no una sensación. Rellenar la tabla con 3-4 alumnos y
  **cortar al cuarto**.
- Si nadie lo menciona: lost in the middle. El modelo siempre responde algo plausible; solo se ve midiendo.

## Bloque 1 · Errores y pre-flight · 15 min

### Diapo 4 · Errores típicos

- Dos cubetas: formato/encoding y dependencias. La de spaCy en español es la que más duele: Presidio falla en silencio.
- 💻 `scripts/preflight_s06.py` → `check_spacy_model` (l. 109).

### Diapo 5 · Pre-flight

- ⌨️ El comando de arriba. Recorrer las 8 líneas; parar en la de spaCy: «detected PER entities: ['Laura Fernández']».
- 💻 `CHECKS` (l. 179): cada chequeo es una función.

## 2.1 · Decisión arquitectónica · 15 min

### Diapo 6 · Las cuatro restricciones

- Ventana, coste, latencia y lost in the middle. Es un **AND**.
- 💻 `app/ingestion/architecture.py` → `CAGViability` (l. 48), `viable` (l. 57): `all([...])`.

### Diapo 7 · architecture.py

- 💻 `assess_cag_viability` (l. 98), `recommend_architecture` (l. 114), `PROYECTO_2` (l. 141).
- ⌨️

```powershell
docker compose -p aieng-s06live exec estimator python -m app.ingestion.architecture
```

  → `NO viable` · rojo: `context_window, latency, lost_in_the_middle` · `RAG`. El coste pasa (caché de prefijo y
  refresco semanal).
- Si preguntan: con 60.000 tokens y sin citar sale `CAG`; con 60.000 y citar, `Hybrid` (está en el PDF de comandos,
  «Prueba tú»).

### Diapo 8 · CAG, RAG o híbrido

- El árbol. Fine-tuning no es alternativa: es una capa encima. Embeddings o pgvector → «Sesión 7».
- Puente: decidido RAG, lo primero es saber qué indexar.

## 2.2 · Catálogo · 20 min

### Diapo 9 · Antipatrón

- Mezcla de versiones, fuentes podridas, huecos invisibles. El caos documental de las empresas.
- 💻 Enseñar `data/seed/`: `budgets/`, `transcripts/` y el `rate_card_2024.xlsx` suelto.

### Diapo 10 · Inspeccionar

- 💻 `catalog/inspect.py` → `FolderFacts` (l. 31), `inspect_root` (l. 68).
- ⌨️

```powershell
docker compose -p aieng-s06live exec estimator python -m app.ingestion.catalog.inspect data/seed
```

  → `seed 1 files latest=2024-01-12 formats=xlsx`: la fuente podrida.
- Las cuatro dimensiones de calidad; no se promedian.

### Diapo 11 · El catálogo es código

- 💻 `catalog/models.py` → `CatalogDecision` (l. 33), `_decision_requires_reason_when_not_include` (l. 95).
- 💻 `data/catalog/catalog.yaml`: leerlo en voz alta, no editarlo. Fuentes en l. 33, 58 y 86.
- ⌨️

```powershell
docker compose -p aieng-s06live exec estimator python -m app.ingestion.catalog.loader data/catalog/catalog.yaml
```

  → 3 fuentes, 1 incluida. El `RuntimeWarning` de la primera línea es inofensivo.
- Matiz: aquí la decisión la toma una persona; que una IA catalogue los documentos es una extensión posible, no lo
  que hace el repo.

## 2.3 · Ingesta · 20 min

### Diapo 12 · Tres capas y el Document

- Loader (bytes) → parser (uno por formato) → Document (el contrato). Varios loaders, varios parsers, un Document.
- 💻 `documents/models.py` → `DocumentMetadata` (l. 30), `Document` (l. 43): `extra="forbid"`.
- 💻 `loaders/filesystem.py` → `iter_blobs` (l. 37) · `parsers/protocol.py` → `Parser` (l. 46).

### Diapo 13 · Parsers

- 💻 `parsers/budget_json.py` → `_render_budget_markdown` (l. 59): Markdown, no `json.dumps`.
- 💻 `parsers/transcript_txt.py` → `_parse_tagged` (l. 54) y `_parse_legacy` (l. 76): no se inventa el speaker.
- XLSX, DOCX y PDF: el mismo patrón, en el repo de referencia.

### Diapo 14 · Ingesta asíncrona

- 💻 `app/routers/ingestion.py` → `create_ingestion_run` (l. 86), `get_ingestion_job` (l. 128);
  `orchestrator.py` → `ingest_source` (l. 51), el filtro del catálogo en l. 71.
- 🖥️ Swagger → *ingestion* → `POST /api/v1/ingestion/runs` → Try it out → `{"source_name": "presupuestos_json"}` →
  202 → copiar el `job_id` → `GET /api/v1/ingestion/jobs/{job_id}` → `completed`, `documents_count: 6`.
  Repetir con `rate_card_xlsx` (400 con el motivo del YAML) y `no_existe` (404).
- ⌨️ Lo mismo en PowerShell:

```powershell
$r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/ingestion/runs -ContentType 'application/json' -Body '{"source_name":"presupuestos_json"}'; $r
```

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/ingestion/jobs/$($r.job_id)" | Format-List
```

- Opcional, el cliente de Rails (`estimator-web/…/ingestion_client.rb`, l. 38 y 51):

```powershell
docker compose -p aieng-s06live exec estimator-web bin/rails runner 'c = EstimatorAi::IngestionClient.new; j = c.trigger_ingestion(source_name: :presupuestos_json.to_s); p j; sleep 2; p c.job_status(j.fetch(:job_id.to_s))'
```

### Diapo 15 · Madurez documental

- 60 % fácil, de 60 a 80 % un salto enorme (lo de hoy), cerca del 100 % meses o imposible. La casa no se empieza por
  el tejado.

## 2.4 · Limpieza y validación · 15 min

### Diapo 16 · Cuatro familias de suciedad

- 💻 Abrir `data/seed/budgets/BUDGET-2024-0002.json` («eur», `12/03/2024`), `…0003` («TBD»), `…0004` (−50000).
- 💻 `cleaning/budget_records.py` → `NULL_PLACEHOLDERS` (l. 44).

### Diapo 17 · Limpiar y validar

- 💻 `cleaning/budget_records.py` → `clean_budget_records` (l. 47), fechas (l. 69), dedup (l. 79).
- 💻 `cleaning/schemas.py` → `BudgetRecord` (l. 30), `total_amount` (l. 55), `strict=True` (l. 67).
- 💻 `cleaning/policy.py` → `QUARANTINE_CHECKS` (l. 40), `DISCARD_CHECKS` (l. 45), `lazy=True` (l. 73).

### Diapo 18 · Demo

- ⌨️

```powershell
docker compose -p aieng-s06live exec estimator python scripts/demo_cleaning_s06.py
```

  → 6 ficheros, 5 filas · 3 válidas · cuarentena `BUDGET-2024-0002` · descartada `BUDGET-2024-0004 -50000`.
- La 0002 va a cuarentena por la **fecha** (pandas deduce `%Y-%m-%d` y `12/03/2024` queda `NaT`), no la del «TBD».
  La limpieza no pudo repararla y la validación la cazó: por eso son dos pasos.
- Si preguntan por `column_in_schema: 5` y `dtype('float64')`: fallos de columna (columnas no declaradas con
  `strict=True` y el importe como entero), sin fila; no mandan nada a cuarentena. Está en el PDF de comandos.

## 2.5 · PII y GDPR · 20 min

### Diapo 19 · Tres formas de filtrar

- Directa, por agregación y por inferencia. ¿Cuál es la más peligrosa? → la inferencia.
- Pseudonimizar (reversible, sigue siendo dato personal) frente a anonimizar (irreversible).

### Diapo 20 · Presidio en inglés

- Contar el fallo **antes** de abrir el código: por defecto, cero personas en nombres españoles, y en silencio.
- 💻 `pii/analyzer.py` → `build_analyzer` (l. 37) · `pii/recognizers.py` → l. 28 y 46.

### Diapo 21 · Demo

- 💻 `pii/pseudonymizer.py` → `ConsistentPseudonymizer` (l. 60), `_generators` (l. 78), derecha a izquierda
  (l. 103), `_hash` (l. 130).
- ⌨️

```powershell
docker compose -p aieng-s06live exec estimator python scripts/demo_pii_s06.py
```

  → «Javier Romero» pasa a «Pánfilo del Barros»; 20 mapeos. Falsos positivos a la vista: «Quería» y «Sí» como
  personas, `CLI-0078` sustituido por un nombre. El `BUDGET-…` nuevo es aleatorio (hoy salió `BUDGET-2023-5601`).

### Diapo 22 · Derecho al olvido

- 💻 `pii/mapping_store.py` → `PostgresMappingStore` (l. 50), `forget` (l. 69) · `persistence/models.py` → l. 40-43.
- ⌨️ La tabla sale vacía porque la demo usa el almacén en memoria:

```powershell
docker compose -p aieng-s06live exec estimator-postgres psql -U estimator -d estimator -c "SELECT entity_type, count(*) FROM pseudonym_mappings GROUP BY 1"
```

## Cierre · Diapos 23-25 · 5 min

- Cinco piezas, todas con su motivo escrito. Sesión 7: chunking, embeddings y pgvector.
- ROTI y gracias.

---

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| Docker no arranca: «Ingest server … sock.stale» | cerrar Docker, renombrar `%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine`, abrirlo |
| `/health` ❌ en el pre-flight | el servicio se está recargando: repetir en 10 s |
| La 400 de `rate_card_xlsx` no sale | revisa que el catálogo cargue (diapo 11); `docker compose -p aieng-s06live logs --tail 50 estimator` |
| Demasiados falsos positivos en la PII | es lo esperado; si molestan, contarlo como trade-off (diapo 21) |
