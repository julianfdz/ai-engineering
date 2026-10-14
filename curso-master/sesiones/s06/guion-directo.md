# Sesión 6 — Guion del directo · Fundamentos de data-driven AI

> **Nota local (Julián).** Guion oficial copiado tal cual. Las rutas del pre-flight son las del
> Mac de Antonio (`/Users/antonioperez/...`); en este PC el repo de la rama `session_06_live` va en
> una carpeta propia del fork (ver `contexto-sesion-06.md`, apartado 4). En Windows, `python3`
> suele ser `python`, y si se usa un nombre de proyecto propio (`docker compose -p aieng-s06live`)
> hay que añadirlo a **todos** los `docker compose exec` de las demos.
> Contexto y artículos de la sesión: [contexto-sesion-06.md](contexto-sesion-06.md).

> **Duración**: 120 min · **Modalidad**: flipped classroom estricto · **Rama**: `session_06_live`.
>
> **Cómo se enseña hoy**: la sesión es una **clase apoyada en código ya implementado y commiteado**. Vamos bloque a bloque explicando los *fundamentos* del módulo; cada fundamento se aterriza sobre el archivo concreto que lo encarna y se prueba con una demo. **No se implementa código en vivo** — no se teclea nada desde cero. Las demos *ejecutan* el código que ya existe.
>
> **Estado al entrar**: ejercicio previo hecho (stress test del CAG: 3 escenarios × 5 tamaños × 3 repeticiones) y los cinco articles del módulo leídos.
>
> **Estado al salir**: el alumno entiende y sabe defender las **cinco piezas** del subsistema de ingesta del `estimator/`: catálogo versionado, ingesta con `Document` canónico, limpieza + validación con Pandera, pseudonimización con Presidio y mapping table. Pgvector está instalado pero **dormido** — su activación es Sesión 7.

---

## Cómo leer este guion — leyenda de modalidad

Cada sub-bloque del Bloque 2 sigue **siempre el mismo patrón de cinco partes**. Los marcadores te dicen qué hacer en cada momento:

| Marcador | Qué es | Dónde |
| --- | --- | --- |
| **■ EL FUNDAMENTO** | El concepto del article y el problema que motiva la pieza. *Por qué* existe antes del *cómo*. | pizarra |
| **■ DÓNDE VIVE** | El archivo que encarna el fundamento. Una frase de responsabilidad + la línea "aha" + la decisión de diseño. | IDE — **leer, no teclear** |
| **■ DEMO** | Ejecutar el código existente y leer la salida. | terminal |
| **■ DEFENSA ORAL** | Las decisiones que el alumno debe poder defender ante un stakeholder. | oral |
| **■ BRIDGE** | El enlace al siguiente sub-bloque: qué queda resuelto, qué falta. | oral |

> Regla de oro del guion: **lidera con el fundamento, después abre el archivo.** Nunca al revés. Cuando abras un archivo, di en una frase *qué hace* y *por qué lo miramos ahora* antes de señalar ninguna línea.

---

## Pre-flight checklist (5 min antes del directo)

```bash
# 1. Herramientas y rama
which curl docker uv python3
docker compose version            # v2.20+ para include:
cd /Users/antonioperez/projects/ia/ai-engineering
git branch --show-current         # → session_06_live
git status                        # → clean

# 2. Stack arriba desde la raíz del monorepo (5 servicios)
docker compose up -d --build
docker compose ps                 # esperar healthy

# 3. Migraciones (idempotente)
docker compose exec estimator alembic upgrade head
docker compose exec estimator alembic current      # → 0001_session6_initial (head)

# 4. Salud del baseline previo
curl -s http://localhost:8000/health | python3 -m json.tool   # → healthy

# 5. Pre-flight script de la sesión (8 checks)
docker compose exec estimator python scripts/preflight_s06.py
# → todos ✅. El check crítico es spaCy es_core_news_md.

# 6. Smoke de los endpoints nuevos: una fuente excluida debe dar 400
curl -s -X POST http://localhost:8000/api/v1/ingestion/runs \
  -H 'Content-Type: application/json' -d '{"source_name": "rate_card_xlsx"}'
# → HTTP 400. Demuestra que el catálogo está cargado y la decisión exclude se respeta.
```

**Pestañas listas**:

- http://localhost:8000/docs — Swagger (endpoints de ingesta).
- psql: `docker compose exec estimator-postgres psql -U estimator -d estimator`.
- Terminal con `docker compose logs -f estimator` para ver los structlog del Bloque 2.3.
- Editor con cinco rutas pineadas: `app/ingestion/`, `app/routers/ingestion.py`, `app/persistence/`, `data/catalog/catalog.yaml`, `data/seed/`.

**Dos reglas innegociables del directo**:

1. **No** debatir embeddings, pgvector activo ni chunking. Respuesta única: *"Sesión 7."*
2. Todo el código nuevo es **Python en el servicio IA**. Rails aparece solo como cliente HTTP ilustrativo; decirlo **cada vez** que se ve.

---

## Bloque 0 — Apertura y anclaje · 10 min · 0:00 – 0:10

**Objetivo**: anclar la sesión en los números que el alumno trae de casa. Arrancamos con el CAG roto, no con teoría nueva.

**Modalidad**: oral + chat. Cero código abierto.

### Bienvenida y posicionamiento del módulo

> *"Bienvenidos a la Sesión 6. Dos horas, formato flipped: los cinco articles y el ejercicio del CAG ya están hechos, hoy los aplicamos. Hoy cerramos el camino del CAG y abrimos el de data-driven AI. Y atención: este módulo entero va **antes** del primer embedding. Hoy no vectorizamos nada — hoy preparamos el corpus para que **merezca** ser vectorizado. Cinco piezas, todas ya commiteadas en esta rama, todas en Python en el servicio IA. El repo de referencia con los extras se entrega al final, no antes."*

### Recogida de hallazgos del ejercicio previo

Pregunta literal al chat:

> *"¿Cuál de las cuatro restricciones del CAG se rompió **primero** en tu ejercicio, y con qué número concreto? Las cuatro: context window, coste, latencia, lost-in-the-middle. Quiero un número, no una sensación: tokens, ms, $/turn, drift event."*

Tabular en vivo. Una fila por alumno: `restriccion_rota_primero · numero_concreto · escenario`. **Disciplina**: contar inputs en voz alta; al **cuarto**, cortar.

**Talking point clave**: *"Estos números no son anécdotas. Son la justificación arquitectónica del módulo entero. Cada pieza de hoy responde a uno de ellos."*

### Pregunta trampa: lost-in-the-middle

Si nadie lo ha reportado, introducirlo:

> *"¿Alguien detectó lost-in-the-middle? Es el modo de fallo **más** sutil: la prueba directa no lo ve, porque el modelo siempre responde algo plausible. Solo aparece cuando mides recall del dato que pusiste en el centro del contexto. Mitigarlo requiere curar el corpus o un retrieval que ponga lo relevante cerca del final — eso es Sesión 7."*

### Mapa de Data Driven AI

#### [Slide 1] - Concepto principal Data Driven AI

#### [Slide 2] - Diferencia IA Genérica - Data Driven

#### [Slide 3] - Data Driven AI (RAG) vs Fine Tuning

### Mapa de la sesión

> *"Hoy construimos cinco piezas, una por article. Decisión arquitectónica (¿CAG, RAG o híbrido?), catálogo de fuentes, subsistema de ingesta con el Document canónico, limpieza con Pandera y pseudonimización con Presidio. Las vemos en ese orden porque es el orden en que un dato viaja: primero decides la arquitectura, luego decides qué fuentes entran, luego las parseas, las limpias y por último les quitas la PII antes de tocar el vector."*

**■ BRIDGE → Bloque 1**: *"Antes del núcleo, quince minutos para desbloquear a quien venga con errores del ejercicio o del setup nuevo."*

**Riesgo a vigilar**: la recogida del chat se eterniza → cortar al cuarto input, sin excepción.

---

## Bloque 1 — Resolución de errores · 15 min · 0:10 – 0:25

**Objetivo**: desbloquear a quien llega con problemas del ejercicio o del stack nuevo. **Quince minutos innegociables**: pasado el cuarto de hora, el resto avanza aunque queden dudas individuales.

**Modalidad**: triage en chat + catálogo de errores con fix preparado.

### Triage abierto (0:10 – 0:13)

> *"¿Quién no consiguió arrancar el ejercicio? ¿Quién tiene errores del stack nuevo — unstructured, presidio, spacy es_core_news_md? Clasificad en tres cubetas: **encoding/formato**, **dependencias rotas**, **conceptuales del pre-sesión**. Atacamos en ese orden."*

### Formato y encoding (0:13 – 0:19)

- **UTF-8 vs Latin-1** (`UnicodeDecodeError` en `.txt` o CSV viejos): detectar con `chardet.detect(raw_bytes)`, releer con el encoding correcto.
- **CSV con separadores irregulares**: `pd.read_csv(path, sep=";", quotechar='"', escapechar="\\", engine="python", on_bad_lines="warn")`.
- **JSON con campos opcionales ausentes**: antipatrón `payload["x"]` → `payload.get("x")`; downstream se resuelve con `Optional` en Pydantic v2 (`x: str | None = None`).
- **Fechas en formatos múltiples**: `pd.to_datetime(serie, errors="coerce", dayfirst=True)`. `dayfirst=True` porque en España "12/03/2024" es 12 de marzo; `errors="coerce"` deja `NaT` en las irreparables. **Este es exactamente el patrón que veremos en 2.4 dentro de `cleaning/budget_records.py`** — lo señalamos aquí para que cuando llegue no sorprenda.

### Dependencias del stack (0:19 – 0:25)

- **`es_core_news_md` no descargado**: `python -m spacy download es_core_news_md`. Verificar: `nlp("Laura Fernández firmó en Madrid.").ents` debe dar PER + LOC. **Es el check más importante del preflight**: sin él, Presidio falla en silencio (lo veremos en 2.5).
- **`unstructured[all-docs]`**: primera descarga ~500 MB. Para el primer humo, `strategy="fast"`, no `hi_res`.
- **Pandera v2 — cambio de import**: `import pandera as pa` (v1) → `import pandera.pandas as pa` (v2). Primer error si copias un snippet de 2023. **Lo veremos literal en `cleaning/schemas.py`.**
- **Pydantic v2 — validadores**: `@validator` → `@field_validator` + `@classmethod`; `@root_validator` → `@model_validator(mode="after")`. **Lo veremos literal en `catalog/models.py`.**

**Protocolo anti-monopolio**: si un caso muy específico bloquea más de 3 minutos →

> *"Ese lo retomo en el canal asíncrono. Pega el traceback en el thread, lo cojo después. Seguimos."*

**■ BRIDGE → Bloque 2**: *"Errores fuera. Al núcleo: las cinco piezas."*

---

## Bloque 2 — Casos avanzados · 90 min · 0:25 – 1:55

Cinco sub-bloques, uno por article. Todos con el mismo patrón: **fundamento → dónde vive → demo → defensa → bridge**.

### [Slide 4]

---

### Sub-bloque 2.1 — Decisión arquitectónica: CAG, RAG, híbrido · 15 min · 0:25 – 0:40

> **Article 1.** El fundamento se explica en pizarra; la decisión está codificada y testeada en `app/ingestion/architecture.py`. El objetivo es convertir los hallazgos del Bloque 0 en una **decisión defendible**.

#### [Slide 5]

#### ■ EL FUNDAMENTO · pizarra

El CAG es viable solo si **las cuatro restricciones** están en verde a la vez:

1. **Context window** — ¿cabe el corpus completo?
2. **Coste** — ¿el coste/turno con prefix caching es asumible?
3. **Latencia** — ¿se queda bajo SLO con el corpus entero en contexto?
4. **Lost-in-the-middle** — ¿el modelo realmente *usa* el centro del contexto?

La decisión se toma sobre **cuatro ejes**: volumen, frecuencia de refresco, trazabilidad obligatoria, control de acceso.

#### ■ DÓNDE VIVE · `app/ingestion/architecture.py`

Las dos estructuras del Article 1, codificadas como un módulo más del repo (ejecutable con `python -m`, igual que `catalog/loader.py`):

```python
class CAGViability:                       # las 4 restricciones del CAG
    @property
    def viable(self) -> bool:
        return all([self.context_window_ok, self.cost_ok,
                    self.latency_ok, self.lost_in_the_middle_ok])
```

> Aha: `viable` es un `all([...])` — **es un AND, no un OR**. Una sola restricción en rojo tumba el CAG. `failing_constraints()` devuelve cuáles están en rojo.

```python
def recommend_architecture(corpus, model) -> Literal["CAG", "Hybrid", "RAG"]:
    fits_in_window      = corpus.estimated_tokens <= model.context_window * 0.7   # volumen
    cache_friendly      = corpus.refresh_frequency_days >= 7                       # frecuencia
    traceability_doable = not corpus.traceability_required                         # trazabilidad
    access_doable       = not corpus.access_control_required                       # acceso
    ...
```

> Aha: los **cuatro ejes** de la decisión. Los `PROYECTO_2` y `CURRENT_MODEL` (250K tokens / ventana 128K) viven como constantes en el mismo módulo, defendibles uno a uno.

Los números del Proyecto 2 que se defienden:

| Dato | Valor | Razón |
| --- | --- | --- |
| Volumen | ≈ 250 000 tokens | presupuestos + transcripciones + tarifas |
| Refresco | 7 días | cierre comercial semanal |
| Trazabilidad | obligatoria | citar la fuente es contractual |
| Acceso | requerido | un consultor no ve presupuestos de otro |
| Context window modelo | 128 000 tokens | gpt-4o-mini estándar |

#### ■ DEMO · terminal

```bash
docker compose exec estimator python -m app.ingestion.architecture
# Corpus 'Proyecto 2': 250,000 tokens, refresh cada 7 días, trazabilidad=True, control_acceso=True
# Modelo 'gpt-4o-mini': ventana 128,000 tokens, prefix_caching=True
#
# Viabilidad CAG: NO viable
#   Restricciones en rojo: context_window, latency, lost_in_the_middle
# Recomendación arquitectónica: RAG
```

> *"250 000 contra 128 000: el corpus no cabe ni usando el 70% útil de la ventana. Primer eje en rojo. Y la trazabilidad y el control de acceso por fila son otros dos ejes que el CAG puro no resuelve. Game over para CAG puro."*

#### ■ DEFENSA ORAL

#### [Slide 6]

- **Los cuatro ejes son AND, no OR.** Un solo eje en rojo tumba el CAG. Por eso `viable` es un `all([...])`.
- **Fine-tuning no está en el árbol.** Es una capa **ortogonal**: enseña *cómo responder*, no aporta *datos nuevos* ni resuelve trazabilidad. No mezclar ejes que no se solapan.
- **Tres opciones, no dos.** Entre CAG puro y RAG puro hay un *middle ground*: lo estable (glosario, plantillas, tarifas) por CAG, lo volátil por RAG. Es la **arquitectura híbrida residual**. Hoy vamos por RAG; en producción reservaréis un slot CAG para lo estable.

**Riesgo a vigilar**: preguntas anticipadas de embeddings/pgvector → *"Sesión 7. Hoy preparamos el corpus para que sea vectorizable."*

**■ BRIDGE → 2.2**: *"Decidido RAG, lo primero NO es cargar un parser. Lo primero es saber **qué** vamos a indexar. Eso es el catálogo."*

---

### Sub-bloque 2.2 — El catálogo de fuentes como artefacto vivo · 20 min · 0:40 – 1:00

> **Article 2.** Tres fuentes auditadas, decisión explícita por fuente, un loader tipado que valida al arrancar.

#### ■ EL FUNDAMENTO · pizarra

#### [Slide 7]

El antipatrón es **"vectorizar primero, mirar después"**. Tiene tres modos de fallo, y los tres están plantados en nuestro corpus de demo:

1. **Mezcla de versiones** — `BUDGET-2024-0005` existe en v1 y v2 con `total_amount` distinto. Si indexas los dos, el retriever devuelve ambos y el LLM elige a ojo.
2. **Fuentes podridas** — `rate_card_2024.xlsx`, `last_modified=2024-01-12`. Indexarlo = dar tarifas de hace año y medio.
3. **Gaps invisibles** — `transcripcion_2023-09-08_legacy.txt` sin speaker tags. El parser ingenuo produce basura sin avisar.

El catálogo es el cinturón que te abrochas **antes** de la vectorización.

#### ■ DÓNDE VIVE · IDE

**`app/ingestion/catalog/inspect.py`** — *produce facts del filesystem, cero opiniones.*

```python
@dataclass
class FolderFacts:
    folder: Path
    file_count: int = 0
    total_size_mb: float = 0.0
    latest_modified: datetime | None = None
    formats_detected: set[str] = field(default_factory=set)
```

> Aha: **ningún score, ninguna decisión**. Solo cuenta, suma, registra fechas y extensiones. Las opiniones van al YAML; los facts viven aquí. `inspect_root()` además camina los ficheros sueltos del root — por eso no se nos escapa el XLSX que vive a la altura de `data/seed/`.

**`app/ingestion/catalog/models.py`** — *el contrato Pydantic del catálogo.* Dos líneas "aha":

```python
class CatalogDecision(str, Enum):
    INCLUDE = "include"
    REVIEW = "review"      # ← la tercera decisión, la que evita el colapso a binario
    EXCLUDE = "exclude"
```

```python
@model_validator(mode="after")
def _decision_requires_reason_when_not_include(self) -> "CatalogSource":
    if self.decision is not CatalogDecision.INCLUDE and not self.decision_reason:
        raise ValueError(f"decision={self.decision.value} requires a non-empty decision_reason")
    return self
```

> Aha: si no es `include`, **el motivo es obligatorio o el modelo no valida**. Excluir es una decisión que se justifica, no una omisión silenciosa. (Y de paso: `@field_validator`/`@model_validator` son Pydantic v2, el cambio que avisamos en el Bloque 1.) El validador `_name_is_snake_case` obliga a `name` en snake_case **porque ese nombre es el identificador en la URL del endpoint**.

**`app/ingestion/catalog/loader.py`** — *carga y valida.* Es deliberadamente trivial:

```python
def load_catalog(path: str | Path) -> DataCatalog:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return DataCatalog.model_validate(raw)
```

> Aha: **tres líneas**. Todo el peso (reglas de decisión, unicidad de nombres) está en el modelo, no aquí. Eso es propósito: la lógica vive en un sitio testeable.

**`data/catalog/catalog.yaml`** — *el catálogo del Proyecto 2.* Leer en voz alta las tres `decision` + su `decision_reason`:

- `presupuestos_json` → **include**. PII confidencial.
- `transcripciones_txt` → **review**. Motivo: el fichero pre-2024 sin tags rompe el parser por defecto; pendiente owner sign-off.
- `rate_card_xlsx` → **exclude**. Motivo: `actuality=1`, fichero del 12/01/2024.

#### ■ DEMO · terminal

```bash
# Facts del filesystem
docker compose exec estimator python -m app.ingestion.catalog.inspect data/seed
# → budgets 6 files · transcripts 3 files · seed (xlsx) latest=2024-01-12T...

# Carga validada del catálogo
docker compose exec estimator python -m app.ingestion.catalog.loader data/catalog/catalog.yaml
# → Catalog version: 1.0.0 · Sources total: 3 · Sources included: 1
#   - presupuestos_json (json) — '...'
```

> *"Tres fuentes, **una sola incluida**. El XLSX no aparece. La transcripción tampoco — está en review. Esto es lo que enseñáis a un auditor."*

#### ■ DEFENSA ORAL

- **El script de inspección solo recoge facts.** Score y decisión son juicio humano; van al YAML, no al código.
- **Excluir es disciplina, no desidia.** El `decision_reason` obligatorio lo fuerza el modelo.
- **`review` como tercera decisión.** Sin ella, todo lo dudoso se cuela en `include`. La categoría intermedia es disciplinaria.
- **El catálogo es código, no documentación.** Se valida al arrancar (un campo mal escrito tira el servicio en startup), vive en git con history, se carga en el servicio y se puede testear. Un Notion te falla en producción.

**Riesgo a vigilar**: editar el YAML a mano en vivo se eterniza → ya está pre-redactado, solo se lee.

**■ BRIDGE → 2.3**: *"Catálogo cargado, fuente decidida. Ahora hay que **producir Documents** desde esa fuente. Eso es el subsistema de ingesta."*

---

### Sub-bloque 2.3 — Subsistema de ingesta y Document canónico · 20 min · 1:00 – 1:20

> **Article 3.** Arquitectura modular en tres capas, dos parsers reales (JSON y TXT), `Document` canónico, expuesto al cliente vía endpoint asíncrono.

#### ■ EL FUNDAMENTO · pizarra

#### [Slide 8]

Tres capas con responsabilidades separadas:

- **Loader** — produce bytes. No mira dentro. Hoy filesystem; mañana HTTP, S3, BD.
- **Parser** — bytes → Documents. Lo único que entiende el formato.
- **Normalizer** — reglas de negocio sobre Documents ya canónicos. Hoy son dos capas conceptuales que veremos en 2.4 (`cleaning/`) y 2.5 (`pii/`), no un módulo único.

El `Document` es el **contrato downstream**: todo lo que produzca la ingesta tiene esta forma, venga de JSON, TXT o PDF.

#### ■ DÓNDE VIVE · IDE

**`app/ingestion/documents/models.py`** — *el contrato canónico.*

```python
class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: str
    metadata: DocumentMetadata        # plano; lo específico de formato va en metadata.extra
```

> Aha: **modelo plano, no anidado por tipo de fuente.** Downstream nadie hace `if isinstance(doc, BudgetDocument)`. La heterogeneidad va a `extra: dict[str, Any]` — JSON mete `budget_id` ahí, TXT mete `speaker` y `timestamp`, PDF metería `page_number`. `extra="forbid"`: si un parser intenta colar un campo no declarado, Pydantic falla. **Error fuerte > error silencioso.**

**`app/ingestion/loaders/filesystem.py`** — *bytes + path relativo.* `LoadedBlob` separa `relative_path` de `bytes_`. Una `location` que no resuelve es `FileNotFoundError` **a propósito**: un catálogo que apunta a la nada es el peor tipo de roto, el silencioso.

**`app/ingestion/parsers/protocol.py`** — *Parser como Protocol, no clase abstracta.*

```python
@runtime_checkable
class Parser(Protocol):
    supported_formats: ClassVar[set[str]]
    def parse(self, blob: LoadedBlob, context: ParseContext) -> Iterable[Document]: ...
```

> Aha: **Protocol, no ABC.** Los parsers no comparten implementación — no hay método útil que heredar. Lo que comparten es la *forma*. Eso es **structural typing**: cualquier clase con `supported_formats` y `parse` cumple, sin herencia, y un fake en tests es trivial. Además, `ParseContext` se construye **una vez por run** → `ingested_at` y `source_version` constantes → eso es lo que permite dedupe por hash downstream.

**`app/ingestion/parsers/registry.py`** — *un dict format→parser.* `default_registry()` registra **solo JSON y TXT**:

```python
registry.register(BudgetJsonParser())
registry.register(TranscriptTxtParser())
# XLSX/DOCX/PDF NO se registran aquí — van en guides/session-06-reference/.
```

> Aha: añadir un formato en producción es **una línea**.

**`app/ingestion/parsers/budget_json.py`** — *parser de presupuestos.* La decisión clave:

```python
text = _render_budget_markdown(payload)    # NO json.dumps(payload)
```

> Aha: el parser emite **markdown estructurado** (H1 = `budget_id`, H2 por bloque: Cliente, Total, Fases, Notas), no un volcado JSON. ¿Por qué? Porque downstream el embedder embebe **prosa**, no key-value soup: el query "¿quién es el cliente del presupuesto X?" da mejor similitud contra `## Cliente\n- Nombre: Acme` que contra `{"client_name":"Acme"}`. **Es una decisión de retrieval que adelantamos al parser.**

**`app/ingestion/parsers/transcript_txt.py`** — *un formato, dos modos.*

```python
def _has_speaker_tags(text: str) -> bool:
    matches = sum(1 for line in text.splitlines() if _TURN_RE.match(line.strip()))
    return matches >= 3        # 3 líneas mínimas → es un fichero realmente tagged
```

> Aha: heurística de **3 líneas mínimas** matching para no confundir un ejemplo accidental con un fichero estructurado. Modo tagged → un `Document` por turno con `speaker`/`timestamp` en `extra`. Modo legacy → un `Document` por bloque, **sin speaker: no lo fabrico.**

> *"Mejor admitir que no sé el speaker que inventármelo. Esta es la metanorma del módulo: si no sabes, no rellenas con basura."*

**`app/ingestion/orchestrator.py`** — *pega catálogo + loader + parser.* `ingest_source(...)`. Tres garantías:

```python
if source.decision is not CatalogDecision.INCLUDE:
    raise IngestionRejected(...)        # solo include se ingiere → el router lo mapea a 400
jobs_repo.mark_running(job_id)          # transiciones pending → running → completed | failed
```

> Aha: es **síncrono**. La asincronía la añade el router con `BackgroundTask`.

**`app/routers/ingestion.py`** + **`app/schemas/ingestion.py`** — *el contrato HTTP.* El router es fino: valida contra el catálogo, crea el job, dispara `_run_in_background` y devuelve **202** con `job_id`. El background task **abre su propia Session** (la del request ya está cerrada). `GET /jobs/{id}` hace polling.

#### [Slide 9]

> Aha — **la defensa más importante del sub-bloque**: el endpoint es **asíncrono** porque la indexación es **offline**, no online. Indexar un corpus tarda minutos; una llamada síncrona tira al cliente. Esta es la **separación offline/online** del Article 1. El QUERY de Sesión 7 sí será síncrono.

#### ■ DEMO · terminal

```bash
# Lanzar la fuente incluida
curl -s -X POST http://localhost:8000/api/v1/ingestion/runs \
  -H 'Content-Type: application/json' -d '{"source_name": "presupuestos_json"}' | python3 -m json.tool
# → {"job_id": "...", "source_name": "presupuestos_json", "status": "pending"}

# Poll del estado
curl -s "http://localhost:8000/api/v1/ingestion/jobs/$JID" | python3 -m json.tool
# → {"status": "completed", "documents_count": 6, ...}

# Ramas de error: review/exclude → 400 ; desconocida → 404
curl -s -X POST .../runs -d '{"source_name": "rate_card_xlsx"}'     # → 400 source_not_included
curl -s -X POST .../runs -d '{"source_name": "no_existe"}'          # → 404 unknown_source
```

Mostrar en la otra terminal los structlog `ingestion.started` / `ingestion.completed` con `job_id` y `source_name` bindeados.

**Cameo Rails** (`estimator-web/app/services/estimator_ai/ingestion_client.rb`, ~40 líneas: `trigger_ingestion` + `job_status`):

> *"Esto es solo para ilustrar el contrato. **Cualquier cliente HTTP funciona** — curl, httpx, requests, fetch. Lo escribimos en Ruby por coherencia con el stack del programa, pero es completamente sustituible. El servicio Python es el autoritativo."*

#### ■ DEFENSA ORAL

- **Document plano** → testabilidad y homogeneidad downstream.
- **`extra: dict`** → válvula de escape sin inventar una clase por formato.
- **Protocol vs ABC** → structural typing; no hay implementación que heredar.
- **Tres capas (loader/parser/normalizer)** → cada una cambia por su cuenta; el loader no sabe de formatos, el parser no sabe de dónde vienen los bytes.
- **Async para indexación, sync para query** → offline vs online.

**Riesgo a vigilar**: que pidan un parser de PDF en vivo →

> *"PDF, DOCX y XLSX siguen exactamente este patrón y están en `guides/session-06-reference/`. Con JSON y TXT ya hemos demostrado las tres capas. No los hacemos aquí porque serían 10 minutos por formato y el patrón ya está claro."*

**■ BRIDGE → 2.4**: *"Tenemos Documents canónicos. Pero los datos siguen sucios. Ahora la capa de limpieza + validación."*

---

### Sub-bloque 2.4 — Limpieza con pandas + validación con Pandera · 15 min · 1:20 – 1:35

> **Article 4.** La limpieza es una **capa separada del parser**. La validación enruta los fallos en tres particiones.

#### ■ EL FUNDAMENTO · pizarra

#### [Slide 10]

Las **cuatro familias de suciedad**, todas plantadas a propósito en `data/seed/budgets/`:

1. **Heterogeneidad** — `currency: "EUR"` vs `"eur"` (en 0001 vs 0002).
2. **Disguised nulls** — `client_name: "TBD"` (en 0003). Sin normalizar, el LLM trata 'TBD' como un cliente real.
3. **Duplicados con divergencias** — `BUDGET-2024-0005` v1 (`total_amount: 30000`) vs v2 (32000, firmado 2 días después).
4. **Out-of-range** — `total_amount: -50000` (en 0004).

La idea central: **limpiar y validar son dos pasos distintos.** Limpieza permisiva (repara lo reparable), validación estricta (decide qué entra).

#### ■ DÓNDE VIVE · IDE

**`app/ingestion/cleaning/budget_records.py`** — *repara, no juzga.* Cinco transformaciones; dos líneas "aha":

```python
df["signed_at"] = pd.to_datetime(df["signed_at"], errors="coerce", dayfirst=True)
```

> Aha: `errors="coerce"` (no excepción) + `dayfirst=True` (España). Las fechas irreparables se vuelven `NaT`; la **validación** decidirá qué hacer con ellas. Es el patrón que adelantamos en el Bloque 1.

```python
df = df.sort_values(by=["budget_id", "signed_at"]).drop_duplicates(subset=["budget_id"], keep="last")
```

> Aha: dedup tras calcular un `_content_hash` por fila. La política **"keep last by signed_at"** es una decisión de **negocio**, documentada en el código (no en un Slack). El hash distingue duplicado exacto (descarte trivial) de divergencia (decisión).

**`app/ingestion/cleaning/schemas.py`** — *valida el contrato (Pandera v2).*

```python
import pandera.pandas as pa                       # ← v2, no `import pandera as pa`
...
"total_amount": Column(float, checks=[Check.ge(0), Check.le(10_000_000)], nullable=False),
"client_name":  Column(str,   nullable=True),     # TBD→NA: cuarentena, no descarte
...
strict=True, coerce=False,
```

> Aha: el `Check.ge(0)` es lo que descarta el -50000. `client_name` `nullable=True` porque tras la limpieza 'TBD' es NA y lo queremos en **cuarentena** (quizá el comercial nos da el nombre mañana), no descartado. `strict=True`: columna no declarada = fallo. `coerce=False`: la coerción ya se hizo en limpieza; aquí el schema **checkea, no transforma**.

**`app/ingestion/cleaning/policy.py`** — *enruta los fallos a tres cubetas.*

```python
QUARANTINE_CHECKS = {"not_nullable", "no_default", "column_in_dataframe"}   # recuperable
DISCARD_CHECKS    = {"in_range", "greater_than_or_equal_to", "isin", "str_matches"}  # fatal
...
validated = BudgetRecord.validate(df, lazy=True)   # recoge TODOS los fallos, no solo el primero
```

> Aha: `lazy=True`. Sin él, Pandera levanta al primer error y no podríamos enrutar el resto de filas. `validate_with_policy()` devuelve un `ValidationResult` con `valid` / `quarantined` / `discarded` + un report JSON-serializable. Regla: si una fila toca un check de descarte, **pierde**, aunque también toque uno de cuarentena.

#### ■ DEMO · terminal

```bash
docker compose exec estimator python scripts/demo_cleaning_s06.py
# Ficheros leídos: 6
# Filas tras limpieza + dedup: 5
# Report: input_rows=5, valid_rows=3, quarantined_rows=1, discarded_rows=1
# Descartadas:  BUDGET-2024-0004  -50000
```

Lo observable, que es lo que importa:

- **6 ficheros entran, 5 llegan a validación**: el dedup colapsó las dos versiones de `BUDGET-2024-0005`, quedándose con la v2 (`signed_at` más reciente). **Política implementada en código**, no en un acta.
- **El -50000 (`BUDGET-2024-0004`) se descarta** por `Check.ge(0)`; el resto se reparte entre válidas y cuarentena según los checks. La partición exacta la imprime el report.

#### ■ DEFENSA ORAL

- **`errors="coerce"` y no excepciones** → limpieza y validación son dos pasos; la limpieza es permisiva, la validación decide.
- **Dedup por hash de contenido y no `drop_duplicates` simple** → distingue duplicado exacto de divergencia.
- **"keep last by signed_at" es política, no técnica** → viene del negocio, vive documentada en el código.
- **`lazy=True`** → recoger todos los errores para poder enrutar.
- **`strict=True` siempre en producción** → lo que se relaja ante fallos es la **política**, no el strict.

**Riesgo a vigilar**: los checks de Pandera confunden a quien la ve por primera vez → la celda ya está escrita, **se lee, no se teclea**.

**■ BRIDGE → 2.5**: *"Datos limpios y validados. **Pero todavía con PII en claro.** Eso es lo que arreglamos ahora — y es lo más delicado del módulo."*

---

### Sub-bloque 2.5 — Pseudonimización con Presidio y mapping table · 20 min · 1:35 – 1:55

> **Article 5.** Tres modos de filtración, Presidio en español, pseudonimizador consistente, mapping table persistente que hace operativo el derecho al olvido.

#### ■ EL FUNDAMENTO · pizarra

#### [Slide 11]

Tres modos de **filtración semántica** vía RAG:

1. **Directa** — un nombre/email/id aparece literal en la respuesta. Se mitiga pseudonimizando el corpus antes del embedding.
2. **Por agregación** — atributos individualmente inocuos que juntos reidentifican (CP + edad + género). Se mitiga pseudonimizando también cuasi-identificadores.
3. **Por inferencia** — el modelo *adivina* desde el lenguaje (estilo, jerga, dialecto → identidad).

Pregunta al chat: **¿cuál es la más peligrosa?** → La **inferencia**. Pseudonimizar el corpus **no** la frena: la señal está en el lenguaje, no en los identificadores.

> *"Y subrayad esto: el control de acceso del backend Rails **no** protege contra ninguno de estos modos. La defensa tiene que ocurrir **antes** del embedding, dentro del servicio IA. Hoy mitigamos las dos primeras; la inferencia la dejamos abierta como teoría."*

#### ■ DÓNDE VIVE · IDE — empezar por el FALLO

**Momento pedagógico crítico.** Antes de abrir `analyzer.py`, contar el fallo (es oral, no lo ejecutamos en directo: el `AnalyzerEngine()` por defecto se descarga ~382 MB del modelo inglés y dentro de docker ni siquiera está instalado). El propio docstring de `analyzer.py` lo documenta:

> *"Presidio por defecto monta un modelo de spaCy en inglés. Sobre nombres hispanos — 'Laura Fernández', 'Javier Romero' — devuelve **cero** entidades PERSON. Y lo peor: **falla en silencio**. Tu pipeline parece funcionar, y en producción un usuario pregunta '¿qué dijo Laura Fernández?' y el LLM responde con el nombre **sin pseudonimizar**. Has filtrado PII y no te has enterado. Por eso configuramos el español explícitamente."*

**`app/ingestion/pii/analyzer.py`** — *la corrección: Presidio en español.*

```python
@lru_cache
def build_analyzer() -> AnalyzerEngine:
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "es", "model_name": settings.PRESIDIO_SPACY_MODEL}],  # es_core_news_md
    })
    engine = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["es"])
    engine.registry.add_recognizer(BudgetIdRecognizer())
    engine.registry.add_recognizer(ClientCodeRecognizer())
    return engine
```

> Aha: configuración **explícita en español** + `@lru_cache` (cargar el modelo spaCy es lento, ~300 ms; singleton). Los recognizers custom se registran eagerly: el caller no tiene que acordarse.

Con esta configuración, el analyzer en español **sí** detecta: `[PERSON Laura Fernández, LOC Madrid]`.

**`app/ingestion/pii/recognizers.py`** — *los identificadores del dominio.* `BudgetIdRecognizer` (`\bBUDGET-\d{4}-\d{4}\b`) y `ClientCodeRecognizer` (`\bCLI-\d{4}\b`), ambos `score=0.95`, `supported_language="es"`.

> Aha: Presidio detecta PERSON/EMAIL/LOC de fábrica, pero `BUDGET-2024-0001` y `CLI-0042` son nuestros. Sin recognizer custom, el corpus se vectoriza con esos ids en claro. Score 0.95 porque el regex es muy específico.

**`app/ingestion/pii/pseudonymizer.py`** — *mismo valor → mismo pseudónimo, siempre.* Tres líneas "aha":

```python
self._generators = {"PERSON": self._faker.name, "EMAIL_ADDRESS": self._faker.ascii_company_email, ...}
results.sort(key=lambda r: r.end, reverse=True)          # reemplazo derecha→izquierda
original_hash = self._hash(original_value)               # HMAC-SHA256 con salt
```

> Aha: (1) generadores **por tipo** — PERSON → nombre español verosímil, no `[PERSON]` genérico. (2) sort por end-offset descendente para que las ediciones tardías no desplacen los offsets tempranos. (3) lo que entra al store es el **HMAC**, no el valor.

**`app/ingestion/pii/mapping_store.py`** — *Protocol + dos implementaciones.* `MappingStore` Protocol; `PostgresMappingStore` (producción) e `InMemoryMappingStore` (tests/scripts). Ambos idempotentes: misma `(entity_type, hash)` → mismo pseudónimo.

**`app/persistence/models.py`** + **`alembic/versions/0001_session6_initial.py`** — *la mapping table.*

```python
UniqueConstraint("entity_type", "original_hash", name="uq_mappings_entity_hash")
```

> Aha: en la tabla se guarda `original_hash`, **nunca el plaintext**. El UNIQUE hace la concurrencia segura sin lock explícito: dos workers ven el mismo nombre, uno inserta, el otro lee al ganador. Y la imagen es `pgvector/pgvector:pg16`: la extensión vector está **instalada pero dormida** (no hay `CREATE EXTENSION vector`); se activa en S07 con una migración. Hoy: cero pgvector activo, para no rehacer infra después.

**`app/config.py`** — `PRESIDIO_SPACY_MODEL`, `PSEUDONYM_FAKER_LOCALE`, `PSEUDONYM_HASH_SALT` (rotables por env).

#### ■ DEMO · terminal + psql

```bash
docker compose exec estimator python scripts/demo_pii_s06.py
# --- Texto pseudonimizado (primeros 400 chars) ---
# [09:15:02] Pánfilo del Barros: ... presupuesto BUDGET-2027-3764 ...
# --- Mappings aplicados (20) ---
#   PERSON         → Purificación Rivero Arjona
#   EMAIL_ADDRESS  → dalila38@instalaciones.org
#   LOCATION       → Teruel
#   ...
```

> El script pseudonimiza la transcripción real `transcripcion_2025-02-03_betanorte.txt`: nombres, emails, `BUDGET-...` y `CLI-...` quedan reemplazados por pseudónimos verosímiles y **consistentes** (mismo valor → mismo pseudónimo).

Con la mapping table persistente (`PostgresMappingStore`):

```bash
docker compose exec estimator-postgres psql -U estimator -d estimator \
  -c "SELECT entity_type, count(*) FROM pseudonym_mappings GROUP BY 1"
```

**Falsos positivos** (saldrán — Presidio en español es así):

> *"Presidio probabilístico en español etiqueta a veces palabras ambiguas como PERSON. No es un bug, es un trade-off. Mitigarlo en producción: subir el score threshold, añadir deny-list, o usar es_core_news_lg. Para hoy lo dejamos vivo: el punto es ver el sistema funcionando, incluidos sus modos de fallo."*

#### ■ DEFENSA ORAL

- **Pseudonimización reversible, no anonimización irreversible** → `[PERSON]` genérico tira la similitud cosenoidal un 15-25%; un nombre verosímil preserva la estructura semántica.
- **Consistencia por valor original, no por chunk** → la misma "Laura Fernández" da el mismo pseudónimo en todos los documentos, hasta que se borre del store.
- **Generadores específicos por tipo** → cada entidad mantiene su forma.
- **Mapping store separado, encriptado, con su propio control de acceso** → no vive con el corpus vectorial.
- **GDPR Art. 17** → *"Sin la mapping table, borrar los datos de un cliente es **imposible**: están embebidos en miles de chunks. Con ella, un `DELETE FROM pseudonym_mappings WHERE original_hash=...` invalida el bind con la identidad original, dejando el corpus intacto. La pseudonimización reversible es la pieza que hace el derecho al olvido operativamente posible."*

**Riesgo a vigilar**: si los FP de Presidio son disruptivos →

> *"Estoy viendo más falsos positivos de los que esperaba; cambio a `transcripcion_2025-02-03_betanorte.txt`, está más limpio."*

**■ BRIDGE → Bloque 3**: *"Cinco piezas. El corpus ya está listo para vectorizar."*

---

## Bloque 3 — Cierre del módulo y bridge · 5 min · 1:55 – 2:00

**Modalidad**: plano del instructor. Cero coding.

### Recap de las cinco piezas

| # | Pieza | Dónde vive | Article |
| --- | --- | --- | --- |
| 1 | Decisión arquitectónica (RAG, híbrido residual) | `app/ingestion/architecture.py` | 1 |
| 2 | Catálogo versionado, 3 fuentes auditadas | `data/catalog/catalog.yaml` + `app/ingestion/catalog/` | 2 |
| 3 | Ingesta + `Document` canónico + endpoint asíncrono | `app/ingestion/{loaders,parsers,orchestrator.py}` + `app/routers/ingestion.py` | 3 |
| 4 | Limpieza + Pandera + reparar/cuarentena/descartar | `app/ingestion/cleaning/` | 4 |
| 5 | Pseudonimización GDPR-grade + mapping table | `app/ingestion/pii/` + `app/persistence/` | 5 |

> *"Cada pieza versionada en git, cada decisión documentada en código: la exclusión del XLSX tiene motivo, la cuarentena de la transcripción legacy tiene motivo, la política de dedup tiene motivo, el modelo de Presidio en español tiene motivo. **Eso es data-driven AI.**"*

### Estado del corpus

> *"El corpus está listo para vectorizar, y lo está de forma **defendible**. Si viene legal a preguntar qué tenéis y por qué — hay respuesta. Si viene compliance por el derecho al olvido — hay respuesta. Si viene un cliente por de dónde sale un precio — hay respuesta. Defendible ante legal, comercial, técnico y regulatorio."*

### Bridge a Sesión 7

> *"Sesión 7 abrimos con este corpus: **chunking, embeddings, espacio vectorial.** Partimos los Documents, los embebemos y los metemos en pgvector — esa extensión que hoy está dormida y que se activa con **una sola migración Alembic**. El trabajo de hoy es el cimiento; Sesión 7 levanta las paredes."*

### Entrega del repo de referencia

> *"El repo de referencia con los parsers extra (XLSX, DOCX, PDF) está en el canal del programa. Patrón idéntico al de los parsers de hoy — leedlos como ejemplo. Gracias. Hasta Sesión 7."*

---

# Apéndice — Resumen ejecutivo

> Para repaso rápido antes del directo.

## Artefactos (todos ya commiteados en `session_06_live`)

| Ruta | Descripción |
| --- | --- |
| `app/ingestion/catalog/` | `models.py` (Pydantic v2), `loader.py`, `inspect.py`. |
| `app/ingestion/documents/models.py` | `Document` + `DocumentMetadata` canónicos. |
| `app/ingestion/loaders/filesystem.py` | `FileSystemLoader` + `LoadedBlob`. |
| `app/ingestion/parsers/` | `protocol.py`, `registry.py`, `budget_json.py`, `transcript_txt.py`. |
| `app/ingestion/cleaning/` | `budget_records.py`, `schemas.py` (Pandera v2), `policy.py`. |
| `app/ingestion/pii/` | `analyzer.py`, `recognizers.py`, `pseudonymizer.py`, `mapping_store.py`. |
| `app/ingestion/architecture.py` | Decisión CAG/RAG/híbrido (Article 1): `CAGViability`, `recommend_architecture`, `PROYECTO_2`. Ejecutable: `python -m app.ingestion.architecture`. |
| `app/ingestion/orchestrator.py` | `ingest_source()`. |
| `app/persistence/` | `database.py`, `models.py`, `repositories/{jobs,mappings}.py`. |
| `app/routers/ingestion.py` + `app/schemas/ingestion.py` | Endpoints POST/GET + schemas. |
| `alembic/versions/0001_session6_initial.py` | `pseudonym_mappings`, `ingestion_jobs`. |
| `data/catalog/catalog.yaml` | Catálogo con 3 fuentes auditadas. |
| `data/seed/` | 6 JSON + 3 TXT + 1 XLSX, con las cuatro familias de suciedad y PII sintética. |
| `scripts/preflight_s06.py` | 8 checks pre-directo. |
| `scripts/demo_cleaning_s06.py` | Driver de la demo 2.4 (limpieza + Pandera). `python scripts/demo_cleaning_s06.py`. |
| `scripts/demo_pii_s06.py` | Driver de la demo 2.5 (pseudonimización en español). `python scripts/demo_pii_s06.py`. |
| `tests/test_architecture.py` | Test de la decisión 2.1 (recomienda RAG, lógica AND). |
| `estimator-web/app/services/estimator_ai/ingestion_client.rb` | Cliente Rails ilustrativo. |

## Settings de Sesión 6 (`app/config.py`)

| Setting | Valor por defecto | Propósito |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://estimator:estimator@localhost:5433/estimator` | Postgres (pgvector dormido). |
| `CATALOG_PATH` | `Path("data/catalog/catalog.yaml")` | Ubicación del catálogo. |
| `INGESTION_DATA_ROOT` | `Path("data/seed")` | Raíz para resolver `CatalogSource.location`. |
| `PRESIDIO_SPACY_MODEL` | `"es_core_news_md"` | Modelo spaCy — crítico: el default inglés no detecta nombres hispanos. |
| `PSEUDONYM_FAKER_LOCALE` | `"es_ES"` | Locale Faker para pseudónimos verosímiles. |
| `PSEUDONYM_HASH_SALT` | `"change-me-in-prod"` | HMAC salt, rotable por env. |

## Decisiones de diseño cerradas (con justificación)

| Decisión | Elegido | Por qué |
| --- | --- | --- |
| Persistencia mapping table | Postgres con imagen `pgvector/pgvector:pg16`, extensión vector **dormida** | El servicio gana su capa relacional sin re-trabajo en S07; la extensión se activa con una migración. |
| Formato catálogo | **YAML** | Legibilidad + comentarios; cargado con `yaml.safe_load` + validado con Pydantic v2. |
| Endpoint ingesta | POST `/api/v1/ingestion/runs` (202) + GET `/jobs/{id}`, async con `BackgroundTasks` | REST canónico; asincronía obligada por ser indexación offline. |
| Estructura de directorios | `app/ingestion/{catalog,documents,loaders,parsers,cleaning,pii}` + `app/persistence/` | Capas conceptuales explícitas + persistencia separada. No hay módulo `normalizers/`: las dos capas conceptuales son `cleaning/` y `pii/`. |
| Parsers en vivo | Solo JSON y TXT | XLSX/DOCX/PDF en el repo de referencia; el patrón ya queda demostrado con dos formatos. |
| Comportamiento ante `review`/`exclude` en el endpoint | 400 igual que `exclude`, con `decision_reason` en el payload | Solo `include` permite ingerir. |
