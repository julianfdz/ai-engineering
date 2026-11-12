# session-5-live-guide


# Sesión 5 — Guion del directo

> **Duración**: 120 min · **Modalidad**: flipped classroom · **Proyecto**: `estimator/` (FastAPI). El `estimator-web/` aparece en mini-cameos como cliente de referencia.
**Estado al entrar**: ejercicio previo de Sesión 5 completado — memoria conversacional con ventana deslizante, `ProjectMetadata` extraído por LLM, adjuntos PDF/DOCX en `multipart/form-data`. **Todo el código de los cuatro bloques nuevos ya está implementado**; el directo es de **explicación**, no de tecleo en vivo.

**Estado al salir**: estimator con compresión híbrida (anclas + resumen + ventana), tier dinámico derivado en runtime, suite de evaluación con golden dataset, y patrón **Actor-Critic-Boss** operativo en `/sessions/{id}/estimate-acb`.


> **Nota local (Julián, 12/11/2026).** Este es el guion de LIDR tal cual. Los comandos de PowerShell adaptados, las
> rutas con línea y lo que hay que enseñar en la web están en [`guion-julian.md`](guion-julian.md). En local: worktree
> `ai-engineering-s05`, todos los comandos con `docker compose -p aieng-s05live`; modelo principal y crítico gpt-4o
> (con gpt-4o-mini las demos devolvían 502); la web lleva el Anexo D montado con «Demo presets». Diferencias reales en
> [`contexto-sesion-05.md`](contexto-sesion-05.md), sección 4.

---


## Pre-flight checklist (5 min antes del directo)

```bash
# 1. Sanity check de herramientas
which curl python3 docker
# jq opcional — el guion usa `python3 -m json.tool`

# 2. Stack levantado desde la raíz del monorepo
cd /Users/antonioperez/projects/ia/ai-engineering
docker compose up -d
docker compose ps               # esperar healthy en estimator + redis + estimator-web + postgres

# 3. Smoke test del baseline conversacional (ejercicio previo)
SID=$(curl -s -X POST http://localhost:8000/sessions | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')
echo "session:$SID"
curl -s -X POST "http://localhost:8000/sessions/$SID/estimate" \
  -F transcript='Estimar un CRM en React y Postgres para el equipo de ventas, equipo de 3 personas.' \
  -F project_type=web_saas \
  -F detail_level=medium \
  -F output_format=phases_table | python3 -m json.tool
# → debe devolver { "result": {...}, "prompt_version": "v3", "cached": false }

# 4. Smoke test del nuevo endpoint ACB
curl -s -X POST "http://localhost:8000/sessions/$SID/estimate-acb" \
  -F transcript='Refinar — añadir módulo de facturación con Stripe.' \
  -F project_type=web_saas \
  -F detail_level=medium \
  -F output_format=phases_table | python3 -m json.tool
# → debe devolver { "result": {...}, "acb": { "iterations": [...], "final_decision": "..." }, ... }

# 5. Smoke test del runner de evals (in-process)
cd estimator
uv run python -m evals.run --mode actor --limit 2
# → tabla con 2 casos, cada uno con sus 3 métricas

# 6. Pestañas listas:
#    - http://localhost:3000          → cliente Rails
#    - http://localhost:8000/docs     → Swagger del FastAPI
#    - http://localhost:8001          → RedisInsight

# 7. Verificar settings de la sesión
grep -E '^(CONVERSATIONAL_PROMPT_VERSION|ANCHOR_DETECTION_MODE|COMPRESSION_MODEL|CRITIC_MODEL|BOSS_MAX_ITERATIONS)' \
  /Users/antonioperez/projects/ia/ai-engineering/estimator/.env 2>/dev/null || \
  echo "(defaults in config.py — v3, heuristic, gpt-4o-mini, gpt-4o-mini, 2)"
```
Cada bloque trae sus propios `curl` listos para copiar-pegar.


---


## Bloque 0 — Apertura y feedback del ejercicio (0–15 min)


### 0.1 Bienvenida + roadmap (3 min)

**Qué decir**:

1. Saludo y recordatorio del flipped classroom. El material asíncrono y el ejercicio previo se asumen leídos y completados.
1. Mapa de las dos horas:
  - **Hora 1**: revisar el ejercicio (15 min) + tres aspectos avanzados sobre la base conversacional — compresión con anclas, tier dinámico, golden dataset (45 min).
  - **Hora 2**: el patrón **Actor-Critic-Boss** sobre el estimator (60 min).
1. Aviso clave: **no se teclea en directo**. Todo el código está implementado en la rama de la sesión; vamos a abrir archivos, señalar dónde están los cambios y explicar por qué.

### 0.2 Revisión de soluciones tipo del ejercicio (9 min)

El ejercicio pedía cuatro piezas: memoria conversacional con ventana deslizante, extracción de `ProjectMetadata` turno a turno, endpoints `/sessions`, y adjuntos PDF/DOCX. Vamos a abrir la solución de referencia que está en `main`, ir archivo por archivo, y comentar las decisiones que han ido apareciendo en las correcciones.


### A. Memoria conversacional — `estimator/app/sessions/models.py`

Tres clases pequeñas, en una sola unidad de datos:

```python
# sessions/models.py:27-35
class Message(BaseModel):
    """One message in the conversation history. The system prompt is NOT a
    Message — it lives outside the history because it is re-rendered each
    turn from the current ``ProjectMetadata``."""

    role: Role
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
`Message.role` es `Literal["user", "assistant"]`. **No hay rol **`**system**` en la historia — el system prompt se regenera en cada turno desde la metadata actual; almacenarlo congelado en el historial sería un bug.

```python
# sessions/models.py:37-57 (sin compresión todavía — eso es Bloque 1)
class ConversationHistory(BaseModel):
    max_turns: int = Field(default=6, ge=1)
    messages: list[Message] = Field(default_factory=list)
    anchors: list[Message] = Field(default_factory=list)      # ← Bloque 1
    summary: str | None = Field(default=None)                 # ← Bloque 1
```
En el ejercicio puro, `anchors` y `summary` no existían — la ventana deslizante era el único mecanismo. La razón de meterlas ya en el modelo desde la sesión 5 es que el bloque 1 va a montarlas encima sin tocar el contrato de `ConversationHistory` (solo añadirá una operación explícita `apply_compression`).

`MAX_CONVERSATION_TURNS` vive en `config.py:43` (`= 6`). Y se respeta vía `max_turns` en `ConversationHistory`. **Cuenta pares user+assistant**, no mensajes; un `max_turns=6` permite `messages` hasta 12 entradas.

**Cómo se llamaba al LLM** — el orden importa:

```python
# services/estimation.py:219-223 (post-sesión 5; el ejercicio era análogo)
messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
messages.extend(session.history.to_messages())
messages.append({"role": "user", "content": user_message})
```
El error frecuente: omitir el `system` o ponerlo dentro de `to_messages()`. Pierdes tier, metadata y todas las reglas — el modelo improvisa cada turno como si fuera el primero.

Tests que comprueban esto: `tests/test_sessions_window.py` (ventana no excede el cap, `messages` se mantienen alternados user/assistant).


### B. Extractor de metadata — `estimator/app/sessions/metadata_extractor.py`

```python
# sessions/metadata_extractor.py:26-44
def update_metadata(
    *,
    previous: ProjectMetadata,
    transcript: str,
    result: EstimationResult,
    llm_wrapper: LLMWrapper,
    model: str,
) -> ProjectMetadata:
    """Run the extractor and return ``previous.merge_with(extracted)``.

    On failure: log + return ``previous`` so a single bad extraction doesn't
    cascade and freeze the session.
    """
    system_prompt, user_message = render_metadata_extraction_prompt(
        transcript=transcript,
        result=result,
        previous=previous,
    )
```
Llamada estructurada con Instructor + `ProjectMetadata` como `response_model`. Modelo barato (`METADATA_EXTRACTOR_MODEL`, default `gpt-4o-mini`). `max_retries=2`, `max_tokens=1000`.

El merge en `ProjectMetadata.merge_with` (`models.py:132-153`) es **escalar-overwrite + lista-union**:

- `project_name`, `assumed_team_size`, `agreed_scope`: si el extractor produce un valor no-null, gana sobre el previo.
- `mentioned_technologies`: union case-insensitive — añadir Stripe no borra Postgres del turno anterior.
**Por qué LLM y no heurística (la pregunta del Camino A vs B de metadata)**: la heurística captura ~70% de las menciones literales pero falla con paráfrasis (“nuestro equipo es pequeño, tres personas a media jornada” no contiene “team size = 3”). Con Instructor el coste extra es modelo barato (céntimos por turno) y la robustez vale.

**Failure mode benigno**: si el LLM revienta (`metadata_extraction_failed` en logs), `update_metadata` devuelve `previous` y la conversación sigue. **No bloquear la respuesta principal por un fallo de housekeeping**.

Tests: `tests/test_sessions_metadata.py::test_two_turns_accumulate_metadata` — comprueba que dos turnos del mismo proyecto acaban con el merge correcto.


### C. Endpoints — `estimator/app/routers/sessions.py`

Tres endpoints (el cuarto, `/estimate-acb`, lo vemos en el bloque 7):

```python
# routers/sessions.py:68-74
@router.post("", response_model=CreateSessionResponse, status_code=201)
def create_session(
    store: SessionStore = Depends(get_session_store),
) -> CreateSessionResponse:
    session = store.create()
    log.info("session_created", session_id=session.session_id)
    return CreateSessionResponse(session_id=session.session_id)
```
```python
# routers/sessions.py:77-95
@router.get("/{session_id}", response_model=SessionInfoResponse)
def get_session(...):
    ...
    return SessionInfoResponse(
        session_id=session.session_id,
        message_count=len(session.history.messages),
        max_turns=session.history.max_turns,
        metadata=session.metadata,
        anchors_count=len(session.history.anchors),
        summary_chars=len(session.history.summary or ""),
        last_resolved_tier=session.last_resolved_tier,
        last_tier_rule=session.last_tier_rule,
    )
```
```python
# routers/sessions.py:173-200
@router.post("/{session_id}/estimate", response_model=EstimationResponse)
async def estimate_in_session(
    session_id: str,
    transcript: str = Form(..., min_length=20, max_length=80_000),
    project_type: ProjectType = Form(...),
    detail_level: DetailLevel = Form(...),
    output_format: OutputFormat = Form(...),
    tier: Tier | None = Form(default=None),
    attachments: list[UploadFile] = File(default_factory=list),
    ...
)
```
**Por qué multipart**: pasar transcript + ficheros en la misma petición. Eso requiere `python-multipart>=0.0.9` en `pyproject.toml:22`. Si el alumno lo olvida, FastAPI revienta en boot con `Form requires "python-multipart"`.

**Por qué **`**Tier | None**`** en el **`**tier**`** Form**: el endpoint admite tanto auto-derivado (omitir) como override explícito. Esto es el “escape hatch” del Bloque 2 — un humano puede desautorizar al resolver.

**Por qué **`**_resolve_session_and_enrich**`** está extraído** (`sessions.py:98-151`): tanto `/estimate` como `/estimate-acb` necesitan el mismo prólogo (cargar sesión, extraer texto de adjuntos, enriquecer transcript). Extraerlo en una función `async` evita duplicar el código de error-mapping (415, 422, 404).


### D. Adjuntos PDF/DOCX — `estimator/app/attachments/extractor.py`

```python
# attachments/extractor.py:32, 39-60
_SUPPORTED_EXTS = {".pdf", ".docx"}

def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            log.warning("pdf_page_extract_failed", error=str(exc)[:200])
            text = ""
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)

def _extract_docx(content: bytes) -> str:
    from docx import Document
    document = Document(io.BytesIO(content))
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)
```
Dos puntos clave:

1. **Errores por página se tragan, no abortan el PDF entero** (`pdf_page_extract_failed`). Un PDF de 30 páginas con la 14 corrupta sigue entregando 29.
1. **Truncado en el caller**: `extract_text` (líneas 63-104) limita a `MAX_ATTACHMENT_CHARS` (config). Sin esto, un brochure de 80k chars revienta el context window del modelo barato.
`enrich_transcript` (`:107-123`) envuelve cada adjunto entre fences explícitos:

```plain text
--- attachment: budget-2026.pdf ---
... texto extraído ...
--- end attachment ---
```
El LLM ve el límite y la procedencia. Sin fences, el adjunto se mezcla con el transcript del usuario y el modelo no puede distinguir qué dijo el cliente vs qué leyó del PDF.

**Camino A (multimodal directo, pasar el PDF a OpenAI/Anthropic en el **`**messages**`**) vs Camino B (extracción local con pypdf/python-docx)**:

- **A**: acopla al proveedor. Multimodal de OpenAI con PDFs ≠ multimodal de Anthropic. Cambias de proveedor y reescribes la integración.
- **B**: el wrapper LLM se mantiene agnóstico. Solo recibe texto. El extractor es un servicio aparte que se puede swappear (mañana queremos OCR, pasada queremos chunking RAG — sin tocar `estimate_conversational`).
El proyecto canoniza **Camino B**. Los alumnos que fueron por A no están “equivocados”, pero para el módulo 3 (RAG) van a tener que reescribirlo igualmente.

Tests: `tests/test_attachments_extractor.py` cubre los modos felices, el truncado, el extension no soportado, los errores por página, y el enrichment con fences.


### E. Patrones de error frecuentes en las correcciones

- Olvidar `python-multipart` en `pyproject.toml:22` y que el endpoint multipart explote en boot.
- Llamar al endpoint sin crear sesión antes — `404 session_not_found` que confunde con un bug del servidor cuando es del cliente.
- No pasar la lista `messages` con orden `[system] + history + new_user`; se omite el system y la salida queda sin tier ni metadata.
- Adjuntos enormes sin truncar (>60k chars) que tumban el context window del modelo barato.
- Hacer el `update_metadata` antes de `apply_compression` (o sin esperar al éxito de la estimación). El orden correcto: estimación → output guardrail → append → compresión → extractor de metadata. Si el orden cambia, el resumen del bloque 1 se calcula con datos que aún no estaban consolidados.

### 0.3 Preguntas abiertas (3 min)

**Pregunta para calibrar**:
> “¿Quién ha tenido problemas con el ejercicio previo y en qué punto?”
> “¿Alguien fue por el Camino A (multimodal directo)? Comentadnos cómo os ha ido el acoplamiento con OpenAI/Anthropic.”


---


## Bloque 1 — Compresión avanzada de memoria con anclas (15–30 min)

**[Slide] - Estrategias de historial**


### 1.1 El problema de la ventana deslizante (3 min)

**Qué decir**:

- La ventana deslizante del ejercicio (`MAX_CONVERSATION_TURNS=6`) funciona en conversaciones cortas. En cuanto la conversación supera 6 pares user/assistant, el turno más antiguo desaparece — y con él cualquier compromiso clave que el cliente hizo al principio (NDA firmada, alcance acordado, presupuesto tope).
- Dos modos de fallo concretos:
  1. **Pérdida de compromisos**. La sesión olvida que firmamos un NDA en el turno 1 — el modelo deja de tratar la conversación como confidencial.
  1. **Pérdida de contexto resumible**. Las decisiones de los turnos 1-3 que ya no aplican literalmente pero deberían haberse conservado como “ya acordado X” desaparecen sin huella.

### 1.2 Estrategia híbrida — resumen + anclas + ventana (4 min)

**Qué decir**:

- Tres slots dentro de `ConversationHistory`:
  - `messages` — ventana deslizante actual (lo del ejercicio).
  - `anchors: list[Message]` — turnos críticos que **nunca** se evictan.
  - `summary: str | None` — resumen acumulado de los pares no-ancla que ya salieron de la ventana.
- `to_messages()` ahora compone `[summary_envelope?] + anchors + recent_window`. La ventana ya no es el límite del contexto entero, solo del segmento “vivo”.
**Diagrama (oral)**:

```plain text
Turno 8 (con max_turns=3, t1 = "Firmamos NDA"):

  history.summary  = "El cliente describió un CRM para sales (turnos 2-4)…"
  history.anchors  = [t1_user, t1_assistant]   ← NDA, no se evicta
  history.messages = [t5,t6,t7,t8 pairs]       ← ventana actual

  to_messages() → [
    {role:user, content:"[Earlier conversation summary]\n…"},
    NDA pair,
    t5..t8 pairs
  ]
```

### 1.3 Recorrido por el código (6 min)

Cuatro archivos nuevos + dos modificados. Tabla maestra:

| Archivo | Líneas | Qué es |
|---|---|---|
| `estimator/app/sessions/compression/__init__.py` | full (28 ln) | re-exporta `AnchorDetector`, `AnchorMatch`, `CumulativeSummarizer`, `CompressionPolicy`, `apply_compression` |
| `estimator/app/sessions/compression/anchors.py` | `:35-44` | tabla `_HEURISTIC_PATTERNS` |
| `estimator/app/sessions/compression/anchors.py` | `:47-54` | `AnchorMatch` dataclass |
| `estimator/app/sessions/compression/anchors.py` | `:70-108` | `AnchorDetector.detect` + `_detect_heuristic` |
| `estimator/app/sessions/compression/anchors.py` | `:110-143` | `_detect_llm` (modo opt-in) |
| `estimator/app/sessions/compression/summarizer.py` | `:26-34` | `_SummaryEnvelope` (wrapper Instructor) |
| `estimator/app/sessions/compression/summarizer.py` | `:37-89` | `CumulativeSummarizer.summarize` |
| `estimator/app/sessions/compression/policy.py` | `:31-87` | `CompressionPolicy` con `should_compress` y `apply` |
| `estimator/app/sessions/compression/policy.py` | `:90-110` | wrapper `apply_compression` (lo que usa el servicio) |
| `estimator/app/sessions/models.py` | `:37-57` | `ConversationHistory` con `messages`, `anchors`, `summary` |
| `estimator/app/sessions/models.py` | `:59-71` | `ConversationHistory.append` — **ya no auto-trimea** |
| `estimator/app/sessions/models.py` | `:73-99` | `ConversationHistory.to_messages` — compone summary + anchors + ventana |
| `estimator/app/services/estimation.py` | `:250-259` | la llamada `apply_compression(...)` tras `append(...)` |
| `estimator/app/prompts/conversation_summary/v1/system.j2` | full (13 ln) | prompt del summarizer |
| `estimator/app/prompts/conversation_summary/v1/user.j2` | full (15 ln) | template con `<previous_summary>` y `<evicted_messages>` |
| `estimator/app/routers/sessions.py` | `:57-65` | `SessionInfoResponse` con `anchors_count` y `summary_chars` |
| `estimator/app/config.py` | `:53, :55` | `ANCHOR_DETECTION_MODE` y `COMPRESSION_MODEL` |
**Anchors — qué reconocen** (`anchors.py:35-44`):

```python
_HEURISTIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("nda", re.compile(r"\b(nda|non[- ]?disclosure|under embargo|legal hold)\b", re.IGNORECASE)),
    ("signed_contract", re.compile(r"\b(signed|countersigned)\s+(the\s+)?(contract|sow|msa|agreement)\b", re.IGNORECASE)),
    ("scope_frozen", re.compile(r"\b(scope|backlog)\s+(is\s+)?(frozen|locked|final|fixed)\b", re.IGNORECASE)),
    ("budget_locked", re.compile(r"\b(budget|cap|ceiling)\s+(is\s+)?(locked|fixed|approved|capped)\s+at\b", re.IGNORECASE)),
    ("compliance", re.compile(r"\b(hipaa|gdpr|sox|pci[- ]?dss|fda|iso[- ]?27001)\b", re.IGNORECASE)),
    ("deadline_hard", re.compile(r"\bhard\s+deadline\b|\bmust\s+go\s+live\s+by\b", re.IGNORECASE)),
    ("contractual", re.compile(r"\bcontractually\s+(bound|required|obliged)\b", re.IGNORECASE)),
    ("explicit_commitment", re.compile(r"\b(we|the(client|customer))\s+(agreed|committed)\s+to\b", re.IGNORECASE)),
)
```
Ocho reglas. Curadas a mano. **Cero LLM en el camino feliz.** El comentario en `anchors.py:32-34` lo deja claro:

> The list is intentionally short — we’d rather miss than over-anchor.
Un falso negativo deja el turno bajar al summarizer (donde se condensa). Un falso positivo bloquea ese turno en el prompt verbatim para siempre — eso es lo caro.

**Detector** (`anchors.py:88-108`):

```python
def detect(self, message: Message) -> AnchorMatch:
    """Return the anchor decision plus the rules that triggered it."""
    if self.mode == "llm":
        return self._detect_llm(message)
    return self._detect_heuristic(message)

# -- implementations -------------------------------------------------

@staticmethod
def _detect_heuristic(message: Message) -> AnchorMatch:
    content = message.content or ""
    matched = [name for name, pattern in _HEURISTIC_PATTERNS if pattern.search(content)]
    if matched:
        log.info(
            "anchor_detected",
            strategy="heuristic",
            rules=matched,
            content_chars=len(content),
        )
        return AnchorMatch(is_anchor=True, matched_rules=matched)
    return AnchorMatch(is_anchor=False)
```
`matched_rules` viaja en el log y se ve en RedisInsight / consola: cuando un turno se promueve a ancla, el instructor puede explicar por qué con la regla concreta.

**El loop de compresión** (`policy.py:44-87`):

```python
def apply(self, history: ConversationHistory) -> None:
    """Mutate ``history`` in place: promote anchors and absorb the rest
    into the running summary. No-op when the window is under the cap."""

    if not self.should_compress(history):
        return

    evicted_for_summary: list[Message] = []
    promoted_anchor_rules: list[list[str]] = []

    while len(history.messages) > history.max_turns * 2:
        # Pair-safe pop: with even-length messages and alternating roles,
        # the two oldest entries are the user/assistant pair to retire.
        if len(history.messages) < 2:
            break
        user_msg = history.messages[0]
        assistant_msg = history.messages[1]

        match = self.anchor_detector.detect(user_msg)
        if match.is_anchor:
            history.anchors.append(user_msg)
            history.anchors.append(assistant_msg)
            promoted_anchor_rules.append(match.matched_rules)
        else:
            evicted_for_summary.append(user_msg)
            evicted_for_summary.append(assistant_msg)

        del history.messages[:2]

    if evicted_for_summary:
        history.summary = self.summarizer.summarize(
            previous_summary=history.summary,
            evicted=evicted_for_summary,
        )
```
Tres cosas que vale la pena señalar al alumno mientras lees el código:

1. **Pair-safe pop**: salimos en pares user/assistant. Romper esta invariante reventaría la alternancia que LiteLLM/Instructor esperan.
1. **El detector solo mira el user**. El assistant se promueve “por arrastre” si su user es ancla. Si miraras el assistant también, harías el doble de regex sin ganancia (la decisión real está en lo que el cliente dijo).
1. **Una sola llamada al summarizer** por pasada — no llamamos al LLM por cada par evictado.
**Wrapper que usa el servicio** (`policy.py:90-110`):

```python
def apply_compression(
    history: ConversationHistory,
    *,
    llm_wrapper,
    compression_model: str,
    anchor_detection_mode: str = "heuristic",
) -> None:
    detector = AnchorDetector(
        mode=anchor_detection_mode,
        llm_wrapper=llm_wrapper,
        llm_model=compression_model,
    )
    summarizer = CumulativeSummarizer(llm_wrapper=llm_wrapper, model=compression_model)
    policy = CompressionPolicy(anchor_detector=detector, summarizer=summarizer)
    policy.apply(history)
```
Una función de fachada. El servicio (`estimation.py:254`) no necesita conocer las tres clases internas.

**Punto pedagógico ESTRELLA — el cambio de contrato en **`**append()**` (`models.py:59-71`):

```python
def append(self, *, user: str, assistant: str) -> None:
    """Add one turn (user message + assistant message).

    Trim / anchor promotion / cumulative summary are NOT applied here —
    that's the job of ``CompressionPolicy.apply`` (and its wrapper
    ``apply_compression``). The service layer is responsible for invoking
    compression after each append. Keeping the data structure dumb means
    the policy is the single source of truth for the sliding window,
    anchors and summary — there is exactly one place where the LLM is
    called to decide what to forget.
    """
    self.messages.append(Message(role="user", content=user))
    self.messages.append(Message(role="assistant", content=assistant))
```
Comparativa antes/ahora:

| Antes (ejercicio) | Ahora (sesión 5 live) |
|---|---|
| `append()` trimea silenciosamente | `append()` solo añade — operación pura |
| ventana = único mecanismo de bound | `apply_compression(...)` decide ancla vs resumir |
| state-pure (sin LLM en append) | el servicio orquesta la llamada extra |
¿Por qué importa? Antes, el callsite no sabía si `append` iba a hacer una llamada al LLM o no (dependía del estado interno). Ahora la llamada al LLM es **explícita**: el que escribe el servicio ve dos líneas seguidas, `append(...)` y `apply_compression(...)`, y entiende exactamente cuándo paga el coste.

**Composición del prompt** (`models.py:73-99`):

```python
def to_messages(self) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if self.summary:
        # Wrap as a synthetic user message — most providers route this
        # cleanly through any tool-use scaffolding, and the [Earlier...]
        # bracket marks it visually so the model treats it as context.
        out.append(
            {
                "role": "user",
                "content": (
                    "[Earlier conversation summary — the recent turns "
                    "below are the live thread]\n" + self.summary
                ),
            }
        )
    for anchor in self.anchors:
        out.append({"role": anchor.role, "content": anchor.content})
    for m in self.messages:
        out.append({"role": m.role, "content": m.content})
    return out
```
El resumen entra como **mensaje sintético de role **`**user**` con un bracket explícito. ¿Por qué `user` y no `system`? Porque el system ya existe y se regenera por turno; un segundo system rompería el contrato de “uno y solo uno”. `user` sintético se rutea limpio por todos los proveedores y el bracket le dice al modelo “esto es resumen, no la pregunta actual”.

**El prompt del summarizer** (`prompts/conversation_summary/v1/system.j2`, 13 líneas):

```plain text
You are a conversation summarizer for a software estimation session.

Your job is to fold an older slice of a chat between a sales/PM person and an estimator AI into a compact running summary. The summary is later spliced back into the LLM's context as the FIRST user message, so the estimator can keep coherence on the project even after the raw turns are dropped from the sliding window.

Rules:
- Preserve durable facts: project name, team size, agreed scope changes, technology choices, mentioned constraints, deadlines, budget caps. Drop pleasantries, hedges, and stylistic noise.
- If a previous_summary exists, INTEGRATE the new evicted turns into it. The output replaces the previous summary entirely — it must include everything still relevant.
- Write in third-person past tense. Maximum 12 short sentences.
- Output plain text only. No JSON, no markdown headings, no bullet lists unless the original conversation used them and the structure adds value.
- Always answer in English.
- If a fact is contradicted by a later turn, keep the LATER version (the conversation refines itself).

You will receive the previous summary (which may be empty) and the messages being evicted, each tagged with its role.
```
Y el user template (`conversation_summary/v1/user.j2`):

```plain text
<previous_summary>
{% if previous_summary %}
{{ previous_summary }}
{% else %}
(no previous summary — this is the first compression pass)
{% endif %}
</previous_summary>

<evicted_messages>
{% for message in evicted %}
[{{ message.role }}] {{ message.content }}
{% endfor %}
</evicted_messages>

Return the updated cumulative summary that integrates the evicted messages with whatever durable facts the previous summary already captured.
```
**Lectura clave del prompt**: la regla “INTEGRATE the new evicted turns into it” — el LLM **NO** está creando un resumen de resúmenes. Está rehaciendo el resumen completo desde cero, usando como insumos `previous_summary` y `evicted_messages`. Es la única forma de evitar la degeneración del chained summarization (resumen-de-resumen-de-resumen).


### 1.4 Por qué esta solución

- **Heurístico por defecto, no LLM**. Configurable via `ANCHOR_DETECTION_MODE=llm` en `.env`. El heurístico es cero coste, determinista, auditable regla a regla, y se puede explicar al cliente. El modo LLM es el escape hatch cuando la paráfrasis es densa o el dominio cambia (“el cliente firmó las cláusulas adicionales del anexo” debería ser ancla pero no matchea ninguna regex).
- **Resumen acumulado, NO chain**. La fórmula es `prev_summary + evicted → new_summary`, todo en una sola llamada. Si encadenásemos resúmenes-de-resúmenes, perderíamos información proporcional a la profundidad de la cadena (lossy compression).
- **Failure mode benigno**. Si el summarizer revienta (`summarizer.py:73-79`), `history.summary` queda inalterado y la ventana se mantiene; nunca bloqueamos la conversación por una llamada de compresión fallida. Lo mismo para el detector LLM (`anchors.py:133-139`): exception → fallback al heurístico.
- **El log es la documentación**: cada compresión emite `history_compressed` con `promoted_anchors`, `anchor_rules`, `evicted_to_summary`, `summary_chars`. Quien revise la sesión en RedisInsight / logs puede reconstruir exactamente qué pasó turno a turno.
**Demo en vivo** (la sesión `$SID` del pre-flight):

```bash
# Enviar 8 turnos consecutivos a la misma sesión (max_turns=6 por defecto)
for n in 1 2 3 4 5 6 7 8; do
  echo "--- turn$n ---"
  curl -s -X POST "http://localhost:8000/sessions/$SID/estimate" \
    -F "transcript=Turn$n: refinamos alcance y añadimos features sobre el mismo CRM, manteniendo el mismo equipo." \
    -F project_type=web_saas \
    -F detail_level=summary \
    -F output_format=phases_table | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["result"]["summary"][:120])'
done

# Inspeccionar el estado tras la compresión
curl -s "http://localhost:8000/sessions/$SID" | python3 -m json.tool
# → message_count <= 12, anchors_count >= 0, summary_chars > 0
```
**Pregunta**:
> “¿En vuestro contexto profesional, qué información debería ser ancla? ¿Solo legal/compliance o también decisiones de producto?”


---


## Bloque 2 — Tier dinámico derivado en runtime (30–45 min)


### 2.1 Recordatorio del tier estático (2 min)

**Qué decir**:

- El artículo introdujo “tier” como una etiqueta que el caller pasa explícitamente: `tier=executive` cuando habla con el sponsor, `tier=developer` cuando habla con el equipo técnico.
- Eso es tier **estático**. Funciona, pero requiere que el cliente acierte la etiqueta — y en conversaciones largas la audiencia cambia (empieza el director comercial, sigue el PM, termina el CTO).

## [Slide] - Tiers


### 2.2 El salto: tier derivado del contexto (3 min)

**Qué decir**: el tier se infiere de pistas en el transcript + metadata acumulada:

- “NDA firmada” / “confidential” / “legal hold” → `executive` (no se reparten detalles innecesarios).
- HIPAA / GDPR / SOX / PCI-DSS → `executive` (compliance manda la audiencia).
- Equipo ≤ 2 personas → `pm` simplificado (no tiene sentido descomponer en 8 fases si el equipo es mínimo).
- Densidad técnica (`docker`, `kubernetes`, `terraform`, etc.) ≥ 2 keywords → `developer`.
- Default → comportamiento del ejercicio (v2 funcionalmente equivalente).

### 2.3 Recorrido del resolver (5 min)

Un único archivo nuevo + un template Jinja modificado:

| Archivo | Líneas | Qué es |
|---|---|---|
| `estimator/app/sessions/tier_resolver.py` | `:30-34` | enum `Tier`: EXECUTIVE / PM / DEVELOPER / DEFAULT |
| `estimator/app/sessions/tier_resolver.py` | `:37-41` | `ResolutionContext` dataclass |
| `estimator/app/sessions/tier_resolver.py` | `:44-48` | `TierRule` dataclass |
| `estimator/app/sessions/tier_resolver.py` | `:53-63` | regex: NDA, regulatorias, dev keywords |
| `estimator/app/sessions/tier_resolver.py` | `:66-96` | las cuatro predicate functions |
| `estimator/app/sessions/tier_resolver.py` | `:101-106` | cadena `_RULES` — el orden manda |
| `estimator/app/sessions/tier_resolver.py` | `:109-142` | `resolve_tier(...) -> (Tier, str)` |
| `estimator/app/prompts/estimation/v3/system.j2` | `:17-39` | bloque `<audience>` (Jinja por tier) |
| `estimator/app/services/estimation.py` | `:199-205` | llamada a `resolve_tier` + caché en `session.last_resolved_tier` |
| `estimator/app/routers/sessions.py` | `:180` | param `tier: Tier / None = Form(default=None)` |
| `estimator/app/sessions/models.py` | `:172-173` | nuevos campos en `Session`: `last_resolved_tier`, `last_tier_rule` |
**La enum** (`tier_resolver.py:30-34`):

```python
class Tier(str, Enum):
    EXECUTIVE = "executive"
    PM = "pm"
    DEVELOPER = "developer"
    DEFAULT = "default"
```
Hereda de `str` — eso permite usarla directamente en form params y en JSON sin `.value` por todas partes.

**Las regex** (`tier_resolver.py:53-63`):

```python
_NDA_PATTERN = re.compile(
    r"\b(nda|non[- ]?disclosure|confidential|under embargo|legal hold)\b", re.IGNORECASE
)
_REGULATORY_PATTERN = re.compile(
    r"\b(hipaa|gdpr|sox|pci[- ]?dss|fda|iso[- ]?27001|ccpa)\b", re.IGNORECASE
)
_DEV_KEYWORDS_PATTERN = re.compile(
    r"\b(docker|kubernetes|k8s|microservice|microservices|terraform|iac|"
    r"helm|grpc|graphql|kafka|airflow|spark|rabbitmq)\b",
    re.IGNORECASE,
)
```
Tres puntos:

1. **NDA incluye **`**confidential**` — el cliente que dice “esto es confidencial” sin firmar NDA formal aún cuenta como executive.
1. **Regulatorias incluyen CCPA** (California) además de las europeas. Cuando los alumnos pregunten por LOPD/AEPD, la respuesta es “regex es trivial de ampliar — añade el literal y un test”.
1. **Dev keywords es lista larga**. `gRPC`/`graphql`/`kafka`/`airflow`/`spark`/`rabbitmq` señalan equipos técnicos que esperan profundidad.
**Las predicates** (`tier_resolver.py:66-96`):

```python
def _has_nda(ctx: ResolutionContext) -> bool:
    if _NDA_PATTERN.search(ctx.transcript):
        return True
    if ctx.metadata.agreed_scope and _NDA_PATTERN.search(ctx.metadata.agreed_scope):
        return True
    return False


def _has_regulatory_context(ctx: ResolutionContext) -> bool:
    if _REGULATORY_PATTERN.search(ctx.transcript):
        return True
    if ctx.metadata.agreed_scope and _REGULATORY_PATTERN.search(ctx.metadata.agreed_scope):
        return True
    for tech in ctx.metadata.mentioned_technologies:
        if _REGULATORY_PATTERN.search(tech):
            return True
    return False


def _is_small_team(ctx: ResolutionContext) -> bool:
    return (
        ctx.metadata.assumed_team_size is not None
        and ctx.metadata.assumed_team_size <= 2
    )


def _technical_audience(ctx: ResolutionContext) -> bool:
    hits = _DEV_KEYWORDS_PATTERN.findall(ctx.transcript)
    # Require at least two distinct technical keywords to flip — single
    # mentions ("we run on docker") are too noisy for tier promotion.
    return len(set(t.lower() for t in hits)) >= 2
```
**Sutil pero importante**:

- `_has_nda` y `_has_regulatory_context` miran **transcript Y metadata**. Si el cliente dijo “HIPAA” en el turno 1 y luego cinco turnos sin mencionarlo, `agreed_scope` lo conserva (el extractor del Bloque 0.2-B lo metió). La regulatory persiste.
- `_technical_audience` exige **≥ 2 keywords distintas**. Una sola mención (“lo desplegamos en docker”) **no** flipea a developer tier — es demasiado común en cualquier conversación.
- `_is_small_team` necesita que `assumed_team_size` esté seteado. Si el cliente aún no lo dijo (metadata vacía), no dispara.
**La cadena ordenada** (`tier_resolver.py:101-106`):

```python
_RULES: tuple[TierRule, ...] = (
    TierRule("nda_detected", Tier.EXECUTIVE, _has_nda),
    TierRule("regulatory_context", Tier.EXECUTIVE, _has_regulatory_context),
    TierRule("technical_audience", Tier.DEVELOPER, _technical_audience),
    TierRule("low_budget_pm", Tier.PM, _is_small_team),
)
```
**El orden importa**: si un cliente menciona NDA y además dice que su equipo es de dos personas, lo correcto es `executive` (no `pm`). Por eso NDA va primero. Cuando un alumno pregunte “¿por qué NDA antes que small_team?”, la respuesta es: porque la audiencia que firma NDA no quiere detalle PM por equipo pequeño, quiere la cifra defendible y el riesgo legal.

`**resolve_tier**` (`tier_resolver.py:109-142`):

```python
def resolve_tier(
    *,
    transcript: str,
    metadata: ProjectMetadata,
    override: Tier | None = None,
) -> tuple[Tier, str]:
    """Return ``(tier, rule_name)``.

    Precedence:
        1. ``override`` (caller-provided) wins.
        2. Else, the rule chain is evaluated in order — first hit wins.
        3. Else, ``DEFAULT``.
    """
    ctx = ResolutionContext(transcript=transcript, metadata=metadata, override=override)

    if override is not None:
        log.info("tier_resolved", tier=override.value, rule="explicit_override")
        return override, "explicit_override"

    for rule in _RULES:
        try:
            if rule.predicate(ctx):
                log.info("tier_resolved", tier=rule.tier.value, rule=rule.name)
                return rule.tier, rule.name
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "tier_rule_predicate_failed",
                rule=rule.name,
                error_type=type(exc).__name__,
                error=str(exc)[:120],
            )

    log.info("tier_resolved", tier=Tier.DEFAULT.value, rule="default")
    return Tier.DEFAULT, "default"
```
**Tres detalles vale la pena marcar**:

1. **Devuelve tupla **`**(Tier, str)**`. El segundo elemento es el nombre de la regla — esto es la explainability que va al panel lateral del cliente Rails: “executive (nda_detected)”. Si solo devolvieras el tier, el alumno frente al cliente no sabría justificar la elección.
1. **Override gana siempre y registra **`**rule="explicit_override"**`. El log preserva la trazabilidad.
1. **Las predicates están envueltas en try/except**. Si mañana añadimos una predicate que llame al LLM y revienta, el resolver no se cae — pasa a la siguiente regla. Graceful degradation.
**Cómo se conecta al prompt** (`prompts/estimation/v3/system.j2:17-39`):

```plain text
<audience>
The resolved tier for this turn is {{ tier }}. Adapt your output:
{% if tier == "executive" %}
- Audience: C-level / sponsor. They want a defensible bottom line, not implementation detail.
- Tone: corporate, concise, no jargon. No code identifiers, no library names unless the user used them first.
- Risk first: lead with the top three risks and their mitigations BEFORE the numbers.
- Confidence: be honest. If anything makes the estimate brittle, say so in the summary.
- Numbers: still produce the structured fields below, but keep ``phases`` to 3-4 items maximum and use plain-English phase names ("Discovery", "Build", "Launch") not technical milestones.
{% elif tier == "pm" %}
- Audience: project manager / delivery lead. They will reuse this in planning software.
- Tone: pragmatic, milestone-oriented. Each phase summary mentions who is involved and what the deliverable is.
- Cap ``phases`` at 4. Keep ``confidence_pct`` conservative (lean down 10 points if uncertain).
- Mention dependencies explicitly when they affect sequencing.
{% elif tier == "developer" %}
- Audience: tech lead / engineering manager. They want enough detail to plan stories.
- Tone: technical but not pedantic. Name stack components, integration points, infra assumptions.
- Per phase, call out the riskiest technical assumption in the summary (max one sentence).
- It is OK to push ``phases`` to 6-8 items if the work is genuinely multi-stream.
{% else %}
- Audience: general / mixed stakeholders. Keep balance between business and technical framing.
- Default behaviour (no tier-specific adjustments).
{% endif %}
</audience>
```
**Punto pedagógico — Jinja en lugar de prompts separados**: si tuviéramos cuatro prompts (`v3_exec.j2`, `v3_pm.j2`, `v3_dev.j2`, `v3_default.j2`), cualquier cambio común (un fix de `<scope>` o `<rules>`) lo replicaríamos cuatro veces. Aquí mantenemos UN prompt con el contrato común y solo varía el bloque `<audience>`. Trade-off: el template gana complejidad Jinja, pero gana mantenibilidad.

**Cómo se llama desde el servicio** (`services/estimation.py:197-205`):

```python
# 2. Resolve the audience tier. Override (when the caller passed one)
#    wins; otherwise the rule chain decides from transcript + metadata.
resolved_tier, rule = resolve_tier(
    transcript=transcript,
    metadata=session.metadata,
    override=tier,
)
session.last_resolved_tier = resolved_tier.value
session.last_tier_rule = rule
```
Después se pasa al `render_conversational_prompt` (líneas `:209-217`) como kwarg `tier=resolved_tier`. El loader (en `prompts/loader.py`) extrae el `.value` y lo inyecta en el template Jinja como `{{ tier }}`.


### 2.4 Por qué esta solución

- **Override explícito gana siempre**. Si el cliente pasa `tier=pm` por API o por el dropdown del front, la cadena no se evalúa. Es el “escape hatch”: el resolver es un heurístico y debe poder ser desautorizado por un humano que sepa más sobre la audiencia real de esta llamada.
- **NDA precede a **`**_is_small_team**`. La cadena se evalúa en orden; cuando una regla coincide, las siguientes no corren. Hemos puesto NDA / regulatory antes que small_team porque “equipo pequeño dentro de un proyecto con NDA” no es PM tier, es executive con menos team.
- **Explainability como ciudadano de primera**. `resolve_tier` devuelve `(Tier, rule_name)`. El panel lateral del cliente lo muestra: “executive (nda_detected)”. Cuando el alumno vea un tier que no esperaba, el “porqué” está al lado.
- **Heurístico también aquí**. Nada de LLM-classifier para el tier (a diferencia del anchor detector, que sí tiene modo opt-in). El tier cambia el tono, no la corrección: un falso developer en lugar de pm sigue siendo una respuesta correcta, solo con tono levemente off. El coste de un LLM extra por turno aquí no compensa.
**Demo en vivo** (misma transcripción con y sin NDA):

```bash
SID2=$(curl -s -X POST http://localhost:8000/sessions | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')

# Sin NDA → tier default
curl -s -X POST "http://localhost:8000/sessions/$SID2/estimate" \
  -F transcript='Estimar plataforma de e-commerce con catálogo de 5000 productos y checkout con Stripe.' \
  -F project_type=web_saas -F detail_level=medium -F output_format=phases_table \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print("summary:",d["result"]["summary"][:150])'
curl -s "http://localhost:8000/sessions/$SID2" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("tier:",d["last_resolved_tier"],"rule:",d["last_tier_rule"])'

SID3=$(curl -s -X POST http://localhost:8000/sessions | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')

# Misma idea pero menciona NDA → tier executive
curl -s -X POST "http://localhost:8000/sessions/$SID3/estimate" \
  -F transcript='Heads-up, firmamos NDA antes de la llamada. Estimar plataforma de e-commerce con catálogo de 5000 productos y checkout con Stripe.' \
  -F project_type=web_saas -F detail_level=medium -F output_format=phases_table \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print("summary:",d["result"]["summary"][:150])'
curl -s "http://localhost:8000/sessions/$SID3" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("tier:",d["last_resolved_tier"],"rule:",d["last_tier_rule"])'
```
Comparar los dos summaries en pantalla: el segundo viene con tono ejecutivo (sin jerga, lead con riesgo) y fases más agregadas. **Mismo prompt-base, audiencia distinta**.

**Pregunta**:
> “Si os parece, ¿cuándo el override explícito tiene sentido y cuándo es mejor confiar en el resolver?”


---


## Bloque 3 — Golden dataset + DeepEval (45–60 min)


### 3.1 Por qué evaluar como un test suite (3 min)

**Qué decir**:

- Hemos añadido tres aspectos avanzados al pipeline. Cada uno puede romper en silencio: un cambio en el `<audience>` de v3 puede degradar todos los tiers pero seguir pasando los tests unitarios.
- Los **golden datasets** son a un sistema LLM lo que las suites de regresión son a un sistema clásico: capturan comportamiento esperado a nivel de input-output, no a nivel de código.
- Tres reglas de oro:
  1. **El dataset vive comiteado**. No es un Notion ni un Google Sheet — diff-able y versionado.
  1. **Las métricas son deterministas siempre que se pueda**. Una métrica que cambia de respuesta entre runs sin que cambie el código es inútil.
  1. **Una métrica LLM-judge es complementaria, nunca el primer escalón**. Activable bajo demanda.

### 3.2 El dataset (4 min)

| Archivo | Líneas | Qué es |
|---|---|---|
| `estimator/evals/__init__.py` | full (34 ln) | re-exporta `GoldenCase`, `load_dataset`, las tres métricas y `run_all_metrics` |
| `estimator/evals/dataset.py` | `:12-15` | enums `Literal` para `ProjectTypeStr`, `DetailLevelStr`, `OutputFormatStr`, `TierStr` |
| `estimator/evals/dataset.py` | `:18-40` | `GoldenCase` Pydantic |
| `estimator/evals/dataset.py` | `:46-49` | `load_dataset` |
| `estimator/evals/golden_dataset.json` | full | 16 casos |
| `estimator/pyproject.toml` | dev-deps | `deepeval>=1.0` (opt-in) |
**El schema de un caso** (`dataset.py:18-40`):

```python
class GoldenCase(BaseModel):
    """One transcript + the expected envelope around the model's reply.

    Most checks are loose ranges instead of exact equality: an LLM has
    legitimate latitude in how it scopes a phase. The goal is to catch
    obvious regressions (out-of-budget, missing tech, wrong tier), not to
    pin every digit.
    """

    id: str = Field(min_length=3, max_length=64)
    transcript: str = Field(min_length=20, max_length=80_000)
    project_type: ProjectTypeStr
    detail_level: DetailLevelStr = "medium"
    output_format: OutputFormatStr = "phases_table"
    tier: TierStr = "auto"

    expected_out_of_scope: bool = False
    expected_in_summary: list[str] = Field(default_factory=list)
    expected_technologies_any_of: list[str] = Field(default_factory=list)
    expected_phase_count_range: tuple[int, int] | None = None
    expected_cost_range_eur: tuple[int, int] | None = None
    expected_duration_weeks_range: tuple[int, int] | None = None
    expected_tier: TierStr | None = None  # asserted against last_resolved_tier
```
Casi todos los `expected_*` son **rangos o listas opcionales**, no igualdades. Eso es deliberado.

**Distribución del dataset** (16 casos, abrir y mostrar):

| Mix | Conteo |
|---|---|
| Por tipo: web_saas | 7 |
| Por tipo: internal_tool | 4 |
| Por tipo: mobile_app | 2 |
| Por tipo: data_pipeline | 2 |
| Out-of-scope adversariales | 2 (vago + prompt injection) |
| Tier executive esperado (NDA / HIPAA / GDPR / PCI-DSS) | 4 |
| Tier developer esperado (microservicios + k8s + kafka…) | 1 |
| Tier pm esperado (equipo ≤ 2) | 1 |
| Detail level `detailed` | 4 |
| Detail level `summary` | 5 |
| Resto `medium` | 7 |
**Ejemplo de caso “feliz”** (case-001 del JSON):

```json
{
  "id": "case-001-web-saas-crm",
  "transcript": "We want a B2B CRM called Nimbus for the sales team. Contacts, deal pipeline, basic reporting. Stack: React + Postgres. Team of 3.",
  "project_type": "web_saas",
  "detail_level": "medium",
  "output_format": "phases_table",
  "expected_in_summary": ["CRM"],
  "expected_technologies_any_of": ["React", "Postgres"],
  "expected_phase_count_range": [3, 6],
  "expected_cost_range_eur": [15000, 80000],
  "expected_duration_weeks_range": [4, 16]
}
```
**Punto pedagógico**: `expected_cost_range_eur: [15000, 80000]` permite latitud. El LLM tiene espacio razonable para discrepar; el test atrapa cuando la estimación se va fuera de proporción. Si en cambio pusiéramos `expected_cost_eur: 42000`, casi todos los runs fallarían — el modelo varía legítimamente entre runs.


### 3.3 Las métricas (5 min)

| Archivo | Líneas | Métrica |
|---|---|---|
| `estimator/evals/metrics.py` | `:18-23` | `MetricResult` dataclass |
| `estimator/evals/metrics.py` | `:26-62` | `SchemaAdherenceMetric` |
| `estimator/evals/metrics.py` | `:65-100` | `CostBoundsMetric` |
| `estimator/evals/metrics.py` | `:103-144` | `ContentRecallMetric` |
| `estimator/evals/metrics.py` | `:147` | `_DEFAULT_METRICS` (tupla de instancias) |
| `estimator/evals/metrics.py` | `:150-153` | `run_all_metrics` |
**MetricResult — el contrato de salida**:

```python
@dataclass
class MetricResult:
    name: str
    score: float
    passed: bool
    details: str
```
`score` es 1.0 si pasa, 0.0 si no. **Binario por diseño**: no jugamos a “score parcial” salvo en el LLM-judge opcional. Una métrica con scores entre 0.3 y 0.7 no te dice qué arreglar — la métrica binaria con `details` poblado, sí.

**SchemaAdherenceMetric** (`:26-62`):

```python
class SchemaAdherenceMetric:
    """The actor's structured output and the validators are already enforced
    by Instructor; this metric exists to flag if any of those guarantees
    *regress* (e.g. a future change drops a validator). It also checks the
    phase count against the expected range, when provided."""

    name = "schema_adherence"

    def evaluate(self, case: GoldenCase, result: EstimationResult) -> MetricResult:
        problems: list[str] = []

        phase_sum = sum(p.cost_eur for p in result.phases)
        if phase_sum != result.total_cost_eur:
            problems.append(
                f"phases sum ({phase_sum}) != total_cost_eur ({result.total_cost_eur})"
            )

        if (
            result.confidence_pct < 30
            and not result.summary.startswith(OUT_OF_SCOPE_PREFIX)
        ):
            problems.append("low confidence missing 'Out of scope:' prefix")

        if case.expected_phase_count_range:
            lo, hi = case.expected_phase_count_range
            if not (lo <= len(result.phases) <= hi):
                problems.append(
                    f"phase count{len(result.phases)} outside [{lo},{hi}]"
                )

        score = 1.0 if not problems else 0.0
        return MetricResult(...)
```
**PASS** ⇔ los tres checks pasan: sum-de-fases coherente, OoS prefix cuando confidence < 30, phase count dentro del rango esperado (si se especifica). **FAIL** ⇔ cualquiera de los tres falla — el detalle dice cuál.

¿Por qué esta métrica si Instructor ya valida `phases_sum_matches_total`? Porque protege contra **regresiones futuras**: si alguien quita los validators de `EstimationResult` mañana, los unit tests pueden seguir verdes pero esta métrica caza la pérdida del invariante en runs reales.

**CostBoundsMetric** (`:65-100`):

```python
def evaluate(self, case: GoldenCase, result: EstimationResult) -> MetricResult:
    problems: list[str] = []

    if case.expected_out_of_scope:
        if result.total_cost_eur != 0 or result.total_duration_weeks != 1:
            problems.append(
                "expected out-of-scope envelope (cost=0, duration=1), got "
                f"cost={result.total_cost_eur}, weeks={result.total_duration_weeks}"
            )
    else:
        if case.expected_cost_range_eur:
            lo, hi = case.expected_cost_range_eur
            if not (lo <= result.total_cost_eur <= hi):
                problems.append(...)
        if case.expected_duration_weeks_range:
            ...
```
**PASS** ⇔ si el caso es OoS, el resultado es exactamente `(cost=0, weeks=1)` — el envelope OoS del schema. Si NO es OoS, `total_cost_eur` y `total_duration_weeks` caen dentro de los rangos esperados (si los hay). **FAIL** ⇔ outliers de coste/duración o un OoS mal-formado.

**ContentRecallMetric** (`:103-144`):

```python
def evaluate(self, case: GoldenCase, result: EstimationResult) -> MetricResult:
    if case.expected_out_of_scope:
        return MetricResult(
            name=self.name, score=1.0, passed=True,
            details="skipped — case is out-of-scope by design",
        )

    haystack = " ".join(
        [result.summary] + [phase.summary + " " + phase.name for phase in result.phases]
    ).lower()

    missing_summary = [
        term for term in case.expected_in_summary if term.lower() not in haystack
    ]

    tech_hit = True
    if case.expected_technologies_any_of:
        tech_hit = any(t.lower() in haystack for t in case.expected_technologies_any_of)
    ...
```
**PASS** ⇔ OoS-skip (auto-pass para los adversariales) **O** todos los `expected_in_summary` aparecen en el “haystack” (summary + todos los phase summaries y nombres) **Y** al menos uno de `expected_technologies_any_of` aparece (si la lista no está vacía). Case-insensitive.

¿Por qué `any_of` en tecnologías y no `all`? Porque el LLM legítimamente puede preferir “PostgreSQL” sobre “Postgres” o “Node.js” sobre “Node” — exigir `all` produce falsos negativos. `any_of` captura “al menos una de las tecnologías esperadas se cita”.

**Decisión a justificar**: las tres métricas son **propias**, no DeepEval. `deepeval>=1.0` está en `pyproject.toml:35` como dev dep y disponible como `LLMJudgeMetric` opcional, pero el flujo principal funciona sin él. Razón: una métrica que necesita una API key cada vez que corre no se ejecuta. Determinismo > sofisticación.


### 3.4 Ejecución y lectura de resultados (3 min)

**El runner** (`evals/run.py`):

```python
# evals/run.py:97-103
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("actor", "acb"), default="actor")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--http", default=None, help="Base URL for HTTP mode (e.g. http://localhost:8000)")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
```
Cuatro flags:

- `-mode actor|acb`: contra `/sessions/{sid}/estimate` o `/sessions/{sid}/estimate-acb`.
- `-limit N`: corre solo los primeros N casos. **Lo que usamos en el directo para no esperar 16 LLM calls × 2**.
- `-http URL`: salir a HTTP real en lugar del `TestClient` in-process. Útil cuando quieres medir latencia real con el `estimator` containerizado.
- `-output FILE`: graba el JSON de detalle para diffear runs.
**Transport por defecto: in-process** (`run.py:52-66`):

```python
def _run_case_in_process(case: GoldenCase, mode: Mode) -> tuple[dict[str, Any], int]:
    """Hit the endpoint through ``TestClient`` (in-process)."""
    with TestClient(app) as client:
        # Each case gets a fresh session so they don't contaminate each other.
        sid = client.post("/sessions").json()["session_id"]
        endpoint = (
            f"/sessions/{sid}/estimate-acb"
            if mode == "acb"
            else f"/sessions/{sid}/estimate"
        )
        ...
```
Cada caso → sesión nueva → un único `/estimate` o `/estimate-acb`. **Los casos no se contaminan entre sí** (de lo contrario el bloque 1 inflaría la conversación turno a turno y los rangos se romperían).

**Comando real para el directo**:

```bash
cd estimator
uv run python -m evals.run --mode actor --limit 8 --output /tmp/actor.json
```
**Salida esperada** (formato real, `_format_row` en `run.py:89-94`):

```plain text
Running 8 cases against mode=actor
case-001-web-saas-crm        |   1432 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=PASS(1.00)
case-002-mobile-loyalty      |   1789 ms | schema_adherence=PASS(1.00) | cost_bounds=FAIL(0.00) | content_recall=PASS(1.00)
case-003-internal-tool-hr    |   1655 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=PASS(1.00)
case-004-data-pipeline-etl   |   2104 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=FAIL(0.00)
case-005-web-saas-vague      |    991 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=PASS(1.00)
case-006-web-saas-injection  |   1010 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=PASS(1.00)
case-007-internal-nda        |   1832 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=PASS(1.00)
case-008-web-saas-hipaa      |   2378 ms | schema_adherence=PASS(1.00) | cost_bounds=PASS(1.00) | content_recall=PASS(1.00)

Summary
  6/8 cases passing all metrics
  schema_adherence: 8/8
  cost_bounds: 7/8
  content_recall: 7/8
```
**Discusión en vivo** — abrir `/tmp/actor.json` y mirar los `rows[].metrics[].details` de los que fallaron:

- `case-002-mobile-loyalty | cost_bounds=FAIL(0.00)` → leer el `details`: probablemente `cost 145000 EUR outside [25000, 120000]`. ¿Es outlier legítimo del modelo o rango mal calibrado? Lectura en vivo: la app de fidelización con integración PoS API a menudo se va a >100k — quizás calibremos el rango a `[25000, 160000]`.
- `case-004-data-pipeline-etl | content_recall=FAIL(0.00)` → `details: none of ['Snowflake', 'dbt'] mentioned anywhere`. ¿El LLM se olvidó de nombrar las tecnologías o el resumen las parafraseó (“data warehouse” en lugar de “Snowflake”)? Esto sí es señal real — el modelo ha perdido especificidad.
**Qué NO captura la suite actual**: tono ejecutivo vs developer, calidad de las “assumptions” en `detail_level=detailed`, ausencia de hallucinations sutiles. Para eso está el `LLMJudgeMetric` (no instanciado por defecto) y el Bloque 6 (Critic).

**Pregunta**:
> “Mirando el dataset, ¿qué tipo de transcripción añadiríais para cubrir algo que vuestro proyecto recibe en producción y que ahora mismo no estaría representado?”


---


## Bloque 4 — Recordatorio del fundamento Actor-Critic-Boss (60–70 min)


### 4.1 Anclaje en Building Effective Agents (5 min)

**Qué decir**:

- El patrón viene del artículo *Building Effective Agents* (Anthropic). Tres roles, mismo modelo o modelos distintos, separación estricta de responsabilidades.
- **Actor**: produce un candidato a respuesta. No decide si es válido.
- **Critic**: audita el candidato. No produce respuesta nueva, solo señala defectos estructurados.
- **Boss**: decide qué hacer con la auditoría — aceptar, iterar (re-llamar al actor con el feedback), o sintetizar un fallback.
- Lo importante: **ninguno de los tres conoce el rol de los otros**. El actor escribe como si fuera la respuesta final. El critic audita como si fuera externo. El boss orquesta sin meter prompt-engineering propio.
**Diagrama** (pintar en pantalla mientras se explica):

```plain text
                  ┌─────────────────────────────────────────────┐
                  │   POST /sessions/{id}/estimate-acb           │
                  │   transcript + project_type + tier?          │
                  └────────────────────┬────────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────────┐
                  │ Boss.run(max_iterations=3)                   │
                  └───────────────────┬─────────────────────────┘
                                      │
              ┌──── iteración 0 ──────┼──── iteración 1..N-1 ────┐
              │                       │                          │
              ▼                       │                          ▼
   ┌────────────────────┐             │              ┌──────────────────────┐
   │ Actor              │             │              │ Actor (con feedback)  │
   │ estimate_with_acb  │             │              │ <critic_feedback>     │
   │  ::_actor(None)    │             │              │  inyectado en el      │
   │ → EstimationResult │             │              │  user.j2              │
   └──────────┬─────────┘             │              └──────────┬───────────┘
              │                       │                         │
              ▼                       │                         ▼
   ┌────────────────────┐             │              ┌──────────────────────┐
   │ Critic.review      │             │              │ Critic.review         │
   │ → CriticFeedback   │             │              │ → CriticFeedback      │
   │   { verdict,       │             │              │   { verdict, issues } │
   │     issues[],      │             │              └──────────┬───────────┘
   │     confidence }   │             │                         │
   └──────────┬─────────┘             │                         ▼
              │                       │              ┌──────────────────────┐
              ▼                       │              │ Boss._decide          │
   ┌────────────────────┐             │              │  → accept ? synth?    │
   │ Boss._decide(...)   │            │              └──────────┬───────────┘
   │  iterations_left=1  │            │                         │
   └─┬───────────┬──────┬┘            │              ┌──────────┴────────┐
     │           │      │             │              │                   │
   accept     iterate synth           │           accept              synth
     │           │      │             │              │                   │
     └─return────┘  (loop)            │              └─return────────────┘
                  ▼                                  ↑
            (con feedback) ──────────────────────────┘
```
> Con `BOSS_MAX_ITERATIONS=3` el bucle puede tener hasta tres rondas (un borrador inicial + dos retries dirigidos por el Critic); el diagrama dibuja la primera y la última iteración. La rama central “(loop con feedback)” se repite tantas veces como iteraciones queden.

### 4.2 Los dos modos de fallo que evita (5 min)

**Qué decir**:

1. **Bucle infinito (sin Boss)**. Si solo tenemos actor+critic en loop, no hay condición de parada — el critic siempre puede encontrar algo. El Boss aporta el límite duro (`max_iterations`) y el fallback.
1. **Sesgo de confirmación (sin Critic estructurado)**. Si el critic devuelve texto libre, el actor “interpreta” el feedback y termina añadiendo párrafos defensivos. Con feedback estructurado (`field_path`, `severity`, `category`), el actor sabe **qué campo concreto** rehacer.
**Pregunta**:
> “¿Habéis tenido casos en agentes propios donde el modelo se auto-confirma y empieza a justificarse en lugar de corregirse?”


---


## Bloque 5 — Actor (70–80 min)


### 5.1 La pieza que ya tenemos, releída (5 min)

**Qué decir**:

- El **actor** del patrón ACB **es** el `estimate_conversational` que construimos en el ejercicio y extendimos en los bloques 1-2.
- No hay código nuevo de actor en esta sesión. Lo que cambia es **el contrato**.
**Archivo a abrir y señalar**: `estimator/app/services/estimation.py::estimate_conversational` (líneas 171-275). Recorrido por pasos con líneas reales:

| Paso | Líneas | Qué señalar |
|---|---|---|
| 1. Input guardrail | `:195` | `check_input(transcript, openai_client=self.openai_client)` — guardrail de entrada (Sesión 3) |
| 2. Resolve tier | `:199-205` | `resolve_tier(...)` → cachea en `session.last_resolved_tier` y `session.last_tier_rule` (Bloque 2) |
| 3. Render prompt v3 | `:209-217` | `render_conversational_prompt(version="v3", tier=resolved_tier, ...)` |
| 4. Build messages | `:221-223` | `[system] + session.history.to_messages() + new_user` — orden crítico |
| 5. LLM call | `:234-237` | `llm_wrapper.complete_structured_chat(messages, response_model=EstimationResult)` |
| 6. Output guardrail | `:248` | `enforce_scope_response(result)` — filter policy |
| 7a. Append + compress | `:253-259` | `history.append(...)` seguido de `apply_compression(...)` (Bloque 1) |
| 7b. Update metadata | `:263-269` | `update_metadata(...)` — extractor con merge (Bloque 0.2-B) |
| 8. Return | `:271-275` | `EstimationResponse(result, prompt_version=..., cached=False)` — siempre `cached=False` en modo conversacional |
**Punto pedagógico — order matters**:

```python
# services/estimation.py:248-269
# 5. Output guardrail (filter policy: normalises low-confidence answers).
result = enforce_scope_response(result)

# 6. Append the turn to the history. The append is a pure data
#    operation now — compression (anchor promotion + cumulative
#    summary + sliding window) is the next, explicit step.
session.history.append(user=user_message, assistant=result.model_dump_json())
apply_compression(
    session.history,
    llm_wrapper=self.llm_wrapper,
    compression_model=self.compression_model,
    anchor_detection_mode=self.anchor_detection_mode,
)

# 7. Second-pass extractor refreshes ProjectMetadata. Failure is
#    swallowed inside update_metadata (returns previous unchanged).
session.metadata = update_metadata(
    previous=session.metadata,
    transcript=transcript,
    result=result,
    llm_wrapper=self.llm_wrapper,
    model=self.metadata_extractor_model,
)
```
El orden **OutputGuardrail → Append → Compress → UpdateMetadata** es importante:

- Si appendaras antes del output guardrail, una respuesta low-confidence sin “Out of scope:” prefix entraría en la historia “como si nada” y contaminaría el próximo turno.
- Si comprimieras antes de updateMetadata, podrías evictar turnos cuyos hechos aún no se han incorporado al `agreed_scope` — pérdida de información.

### 5.2 El cambio de contrato — Actor dentro de ACB (5 min)

**Qué decir**:

- En el endpoint `/estimate`, el output del actor **es la respuesta final** — sale directo al cliente.
- En el endpoint `/estimate-acb`, el mismo actor produce un **candidato**. Su output pasa al critic antes de salir. Si el boss decide iterar, el actor se vuelve a llamar con feedback estructurado inyectado en el prompt.
**Archivo a abrir y señalar**: `estimator/app/services/estimation.py::estimate_with_acb` (líneas 277-391).

**El closure **`**_actor**` (líneas 320-349):

```python
def _actor(critic_feedback: CriticFeedback | None) -> EstimationResult:
    system_prompt, user_message = render_conversational_prompt(
        description=transcript,
        project_type=project_type,
        detail_level=detail_level,
        output_format=output_format,
        metadata=session.metadata,
        version=self.conversational_prompt_version,
        tier=resolved_tier,
        critic_feedback=critic_feedback,
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(session.history.to_messages())
    messages.append({"role": "user", "content": user_message})

    draft, meta = self.llm_wrapper.complete_structured_chat(
        messages=messages,
        response_model=EstimationResult,
    )
    log.info(
        "acb_actor_draft",
        with_critic_feedback=critic_feedback is not None,
        issues_in_feedback=(
            len(critic_feedback.issues) if critic_feedback is not None else 0
        ),
        confidence_pct=draft.confidence_pct,
        total_cost_eur=draft.total_cost_eur,
        **meta,
    )
    return enforce_scope_response(draft)
```
**Punto pedagógico — el actor es EL MISMO en ambos modos**. La única diferencia es que `render_conversational_prompt` ahora recibe `critic_feedback=critic_feedback` (que será `None` en la primera iteración y un `CriticFeedback` en las siguientes). El template v3 (`user.j2:7-15`) decide si embeber el bloque `<critic_feedback>` o no:

```plain text
{% if critic_feedback %}
<critic_feedback>
A previous version of your estimation was reviewed by an independent auditor. Address the following issues before producing the next answer; do not repeat the same mistakes.

{% for issue in critic_feedback.issues %}
- [{{ issue.severity }}] {{ issue.category }} at `{{ issue.field_path }}`: {{ issue.description }}{% if issue.suggested_fix %} (suggested fix: {{ issue.suggested_fix }}){% endif %}
{% endfor %}
</critic_feedback>
{% endif %}
```
**Cero rama en el código Python del actor**. Si añadiéramos un `if mode == 'acb': do_something` dentro del actor, romperíamos la simetría — y la pieza tendría dos comportamientos que mantener.

**La persistencia — solo el resultado final** (líneas 366-375):

```python
# 6. Persist the final result into the session (single turn append).
session.history.append(
    user=transcript, assistant=final_result.model_dump_json()
)
apply_compression(
    session.history,
    llm_wrapper=self.llm_wrapper,
    compression_model=self.compression_model,
    anchor_detection_mode=self.anchor_detection_mode,
)
```
**Decisión clave**: la sesión persiste solo el `final_result` (lo que el Boss aprobó o sintetizó). Los borradores intermedios son throwaway. Si guardáramos cada borrador:

- El `to_messages()` del próximo turno se haría con drafts descartados.
- El usuario vería N mensajes del asistente por una sola petición — UX rota.
- La memoria conversacional se llenaría de candidatos rechazados como si fueran historia.
Esto es invisible en un unit test típico pero crítico en producción: la traza del Boss (`acb.iterations`) viaja en la **respuesta** (el cliente puede mostrarla), pero NO en el **estado** de la sesión.

**Pregunta**:
> “¿Veis algún caso donde sí queráis ver los borradores intermedios? Pensad en debugging vs experiencia de usuario.”


---


## Bloque 6 — Critic (80–95 min)


### 6.1 Schema del feedback (5 min)

| Archivo | Líneas | Qué es |
|---|---|---|
| `estimator/app/schemas/critic.py` | `:17-25` | `CriticIssueCategory` — siete categorías Literal |
| `estimator/app/schemas/critic.py` | `:28` | `CriticIssueSeverity` — critical / major / minor |
| `estimator/app/schemas/critic.py` | `:31` | `CriticVerdict` — accept / needs_iteration / reject |
| `estimator/app/schemas/critic.py` | `:34-47` | `CriticIssue` con `field_path` apuntando al campo concreto del result |
| `estimator/app/schemas/critic.py` | `:50-75` | `CriticFeedback` + validator `iteration_requires_blocking_issue` |
**Las siete categorías** (`critic.py:17-25`):

```python
CriticIssueCategory = Literal[
    "math_error",
    "hallucination",
    "scope_mismatch",
    "phase_imbalance",
    "missing_assumption",
    "unrealistic_estimate",
    "tier_mismatch",
]
```
`Literal` (no `Enum`): no necesitamos métodos ni iteración; necesitamos restricción exhaustiva en JSON. Instructor valida que el modelo produzca exactamente una de estas siete strings.

**Severity y verdict** (`critic.py:28, 31`):

```python
CriticIssueSeverity = Literal["critical", "major", "minor"]
CriticVerdict = Literal["accept", "needs_iteration", "reject"]
```
Tres severities, tres verdicts. **No** son lo mismo: severity es por-issue, verdict es del review completo. La diferencia importa porque el validator del schema obliga consistencia (ver más abajo).

**CriticIssue** (`critic.py:34-47`):

```python
class CriticIssue(BaseModel):
    """A single defect flagged by the Critic.

    ``field_path`` uses dotted/bracket notation referring to the estimation
    under review (``phases[2].cost_eur``, ``summary``, ``total_cost_eur``).
    The Boss may forward this verbatim into the actor's next-iteration
    prompt so the model knows what to change.
    """

    category: CriticIssueCategory
    severity: CriticIssueSeverity
    field_path: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=5, max_length=500)
    suggested_fix: str | None = Field(default=None, max_length=300)
```
**Punto pedagógico ESTRELLA — **`**field_path**`. La diferencia entre un critic útil y uno inútil es que el primero dice **dónde** está el defecto. Ejemplos:

| field_path | Significado |
|---|---|
| `summary` | el párrafo de resumen |
| `total_cost_eur` | el total |
| `phases[2].cost_eur` | el coste de la tercera fase |
| `phases[0].summary` | el sumario de la primera fase |
| `phases[5].duration_weeks` | la duración de la sexta fase |
El Boss inyecta este `field_path` literal en el prompt del actor en la siguiente iteración (vía `user.j2:11-13`). El modelo sabe **qué campo concreto** retocar.

**CriticFeedback + validator** (`critic.py:50-75`):

```python
class CriticFeedback(BaseModel):
    """Top-level Critic output. The Boss treats this as authoritative.

    Validator: ``needs_iteration`` requires at least one critical/major
    issue. If the Critic flags only minor issues, it should accept — minor
    issues alone are not worth burning another actor call.
    """

    verdict: CriticVerdict
    issues: list[CriticIssue] = Field(default_factory=list, max_length=12)
    confidence_in_review: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def iteration_requires_blocking_issue(self) -> "CriticFeedback":
        if self.verdict == "needs_iteration":
            blocking = [i for i in self.issues if i.severity in {"critical", "major"}]
            if not blocking:
                raise ValueError(
                    "verdict 'needs_iteration' requires at least one issue with "
                    "severity in {critical, major}; minor-only issues should accept"
                )
        if self.verdict == "reject" and not self.issues:
            raise ValueError(
                "verdict 'reject' requires at least one issue describing why"
            )
        return self
```
**Dos invariantes**:

1. `needs_iteration` → al menos un issue `critical` o `major`. Si solo hay `minor`, debe ser `accept`. Razón: iterar el actor cuesta una llamada LLM. Solo merece la pena por defectos que cambian la estimación, no por nits estilísticos.
1. `reject` → al menos un issue. No puedes rechazar sin justificación.
Si el LLM produce un `CriticFeedback` que viola estos invariantes, Instructor re-promptea hasta 3 veces (configurado en `services/critic.py:57`).


### 6.2 Prompt del crítico (6 min)

**System prompt** (`prompts/critic/v1/system.j2`, 29 líneas):

```plain text
You are an independent auditor of software estimations. You did NOT produce the estimation under review; your job is to find defects in it.

You will receive: the original transcript, the project metadata accumulated across turns, the resolved audience tier, and the estimation under review. Return a STRUCTURED feedback object — never free text.

<heuristics>
Inspect the estimation against these checks. One issue per defect; do not bundle. Default to **minor** severity unless the issue would lead a delivery lead to make a materially worse decision.

1. **math_error** — sum of phase.cost_eur ≠ total_cost_eur, or sum of phase.duration_weeks ≠ total_duration_weeks. Critical (the actor's validators should already catch this; a math_error here means a regression).
2. **hallucination** — any concrete fact in the summary or phase summaries that contradicts (or invents) the transcript / metadata. Critical when it would mislead a stakeholder; major only when it is a plausible but unsourced specific that materially changes the answer; otherwise minor.
3. **scope_mismatch** — the estimation includes (or excludes) work the user clearly described / excluded. Major when the mismatch changes totals by >20%; minor otherwise.
4. **phase_imbalance** — any single phase larger than **75%** of total cost AND no phase summary justifying it. Major. Below 75% — or with any narrative justification in the phase summary — is acceptable; do not flag.
5. **missing_assumption** — only major when ``detail_level`` is "detailed" AND phases carry **no** explicit assumptions or risks at all. Fewer than 3 risks while at least one risk is present is **minor**, not major.
6. **unrealistic_estimate** — totals fall outside conservative-industry rates given the team-size and scope (developer week ≈ 32h × 62.5 EUR/h). Major only if off by >**50%**; minor between 30%-50%; ignore below 30% (normal estimation noise).
7. **tier_mismatch** — the framing breaks the audience contract for the resolved tier (executive output full of jargon, developer output devoid of technical detail, etc). Minor unless the answer is genuinely unusable for the resolved tier — only then major.
</heuristics>

<verdict_rules>
- ``accept``: no critical/major issues found. Minor issues are advisory and do NOT block acceptance.
- ``needs_iteration``: at least one critical/major issue exists AND you believe an actor re-attempt with this feedback can fix it. **If the estimation is internally consistent (totals match, no hallucinated facts) and the only complaints are stylistic, presentational, or about granularity, you MUST `accept`.** The bar for ``needs_iteration`` is: would a delivery lead reading this estimation make a materially worse decision because of this defect?
- ``reject``: the estimation is fundamentally wrong (e.g. the user asked for X and got Y; the project is mis-typed). Use sparingly.
</verdict_rules>

<rules>
- Do not rewrite the estimation. Only flag what is wrong.
- ``field_path`` MUST point at a concrete field of the estimation result. Examples: ``summary``, ``total_cost_eur``, ``phases[0].duration_weeks``, ``phases[2].summary``.
- ``suggested_fix`` is a one-sentence hint, optional. Skip it when you cannot suggest anything concrete.
- If everything looks correct, return ``verdict="accept"`` with an empty ``issues`` list. Be honest.
- **False positives waste actor calls AND degrade user experience.** When in doubt between major and minor, choose minor. When in doubt between ``accept`` and ``needs_iteration``, choose ``accept``. A reasonable estimate with one debatable choice is better than an extra round trip.
- ``confidence_in_review`` reflects how sure you are about your own review (0..100). Lower it when the transcript was vague or the metadata was thin.
</rules>
```
Recorrido sugerido (abrir y leer en pantalla, **señalando**):

- **Línea 1**: identidad — “auditor independiente”. Inicial del prompt determina el rol completo.
- **Bloque **`**<heuristics>**`** (líneas 5-15)**: las siete categorías con criterios concretos. Lo que aplica el modelo, no Python.
- **Bloque **`**<verdict_rules>**`** (líneas 17-21)**: las tres salidas y cuándo elegir cada una.
- **Bloque **`**<rules>**`** (líneas 23-29)**: las prohibiciones (no reescribir, no inventar field_path, ser honesto).
**User prompt** (`prompts/critic/v1/user.j2`, 27 líneas):

```plain text
<original_transcript>
{{ transcript }}
</original_transcript>

<project_metadata>
- project_name: {{ metadata.project_name or "unknown" }}
- assumed_team_size: {{ metadata.assumed_team_size or "unknown" }}
{% if metadata.mentioned_technologies %}- mentioned_technologies: {{ metadata.mentioned_technologies | join(", ") }}
{% else %}- mentioned_technologies: none
{% endif %}- agreed_scope: {{ metadata.agreed_scope or "not yet agreed" }}
</project_metadata>

<resolved_tier>{{ tier }}</resolved_tier>

<estimation_under_review>
summary: {{ result.summary }}
confidence_pct: {{ result.confidence_pct }}
total_duration_weeks: {{ result.total_duration_weeks }}
total_cost_eur: {{ result.total_cost_eur }}
phases:
{% for phase in result.phases %}
- index {{ loop.index0 }}: {{ phase.name }} | {{ phase.duration_weeks }}w | {{ phase.cost_eur }} EUR
  summary: {{ phase.summary }}
{% endfor %}
</estimation_under_review>

Audit this estimation. Return a structured ``CriticFeedback`` per the schema. Be specific in ``field_path``.
```
**Lectura clave**: el `index {{ loop.index0 }}` en cada phase es lo que permite al modelo emitir `phases[2].cost_eur` con índice correcto.

**Decisiones a justificar oralmente**:

- Las heurísticas viven en el **prompt**, no en código Python. Razón: queremos que el modelo aplique juicio cualitativo. Un `phase_imbalance` “razonable” no siempre es 60% — depende del proyecto (una migración a Snowflake puede tener legítimamente el 70% del coste en una sola fase de ETL). El código solo enforce el **schema**, no la calidad.
- El verdict tiene **tres valores, no dos**. `reject` ≠ `needs_iteration`: si el actor se equivocó de tipo de proyecto (pedías mobile, te dio web), iterar no arregla nada. El Boss directamente sintetiza.

### 6.3 El servicio Critic y el fallback gracioso (4 min)

**Archivo**: `estimator/app/services/critic.py` (78 líneas, full file).

**La clase** (`:28-31`):

```python
class Critic:
    def __init__(self, *, llm_wrapper, model: str) -> None:
        self.llm_wrapper = llm_wrapper
        self.model = model
```
Ningún estado más allá del wrapper + modelo. El Critic **no recuerda** entre invocaciones — auditor independiente cada vez.

**El método **`**review**` (`:33-77`):

```python
def review(
    self,
    *,
    transcript: str,
    metadata: ProjectMetadata,
    tier: Tier,
    result: EstimationResult,
) -> CriticFeedback:
    system_prompt, user_message = render_critic_prompt(
        transcript=transcript,
        metadata=metadata,
        tier=tier,
        result=result,
    )

    try:
        feedback, meta = self.llm_wrapper.complete_structured_chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_model=CriticFeedback,
            model_override=self.model,
            max_tokens=1500,
            max_retries=3,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "critic_failed_fallback_accept",
            error_type=type(exc).__name__,
            error=str(exc)[:200],
        )
        # Degraded: pretend the critic accepted with zero confidence so
        # the Boss returns the actor's output unchanged.
        return CriticFeedback(verdict="accept", issues=[], confidence_in_review=0)

    log.info(
        "critic_completed",
        verdict=feedback.verdict,
        issue_count=len(feedback.issues),
        confidence=feedback.confidence_in_review,
        model=meta.get("model"),
        latency_ms=meta.get("latency_ms"),
    )
    return feedback
```
**Punto pedagógico clave — el fallback gracioso** (`:59-67`):

Si el Critic revienta (timeout, validation insistente, rate limit), **NO bloqueamos al usuario**. Devolvemos un `CriticFeedback(verdict="accept", issues=[], confidence_in_review=0)`. El Boss recibirá un “accept” sintético y devolverá el draft del actor sin tocarlo. El `confidence_in_review=0` es la pista para quien lea los logs: este accept es degradado, no genuino.


### 6.4 Por qué no devuelve texto libre

- Texto libre habría sido la opción “natural” — pedirle al modelo “audita esta estimación, dime qué está mal”. Funciona en demo, falla en producción:
  - **No es procesable**. El Boss tendría que parsear prosa para saber si iterar o no.
  - **El actor lo malinterpreta**. Texto libre invita al actor a “responder al critic” en lugar de corregir.
  - **No es auditable**. Cuando algo va mal, no sabes qué categoría dominó las decisiones del Boss.
- El schema estructurado se valida con Instructor (`max_retries=3` en `services/critic.py:57`) — si el modelo no produce el formato, Instructor re-promptea. Termina haciendo el trabajo, o cae al fallback.
**Pregunta**:
> “Si tuvierais que añadir una octava categoría al `CriticIssueCategory`, ¿cuál sería para vuestro dominio?”


---


## Bloque 7 — Boss (95–110 min)


### 7.1 Tres rutas (4 min)

El Boss es un autómata de tres estados sobre el verdict del Critic + el budget de iteraciones restantes. La tabla viene directa de `Boss._decide` (`services/boss.py:105-114`):

| Critic verdict | iterations_left | Boss decision | Acción |
|---|---|---|---|
| `accept` | — | `accept` | return current |
| `reject` | — | `synthesize` | `_synthesize_fallback(current, review)` |
| `needs_iteration` | > 0 | `iterate` | feedback ← review; loop |
| `needs_iteration` | 0 | `synthesize` | `_synthesize_fallback(current, feedback)` |
**Punto pedagógico**: la simetría entre `reject` y “needs_iteration sin budget” — ambas terminan en `synthesize` porque ambas significan “no podemos producir algo bueno con este actor en este contexto”. `reject` es la versión rápida (“ni intentes iterar, está fundamentalmente mal”); budget-exhausted es la versión lenta (“lo intentamos N veces y no convergió”).


### 7.2 Recorrido del orquestador (8 min)

| Archivo | Líneas | Qué es |
|---|---|---|
| `estimator/app/schemas/acb.py` | `:15` | `BossDecision` Literal (accept / iterate / synthesize) |
| `estimator/app/schemas/acb.py` | `:18-29` | `ACBIteration` — registro por iteración |
| `estimator/app/schemas/acb.py` | `:32-35` | `BossTrace` — el log completo |
| `estimator/app/schemas/estimation.py` | `:119-130` | `ACBResponse` extends `EstimationResponse` + `acb: BossTrace` |
| `estimator/app/services/boss.py` | `:38-39` | type aliases `ActorCallable`, `CriticCallable` |
| `estimator/app/services/boss.py` | `:42-48` | `Boss.__init__` (valida `max_iterations >= 1`) |
| `estimator/app/services/boss.py` | `:50-101` | `Boss.run` — loop principal |
| `estimator/app/services/boss.py` | `:105-114` | `Boss._decide` — routing en 9 líneas |
| `estimator/app/services/boss.py` | `:116-156` | `Boss._synthesize_fallback` — devuelve el último borrador del actor con caveats del audit en el summary y confianza recortada |
| `estimator/app/services/estimation.py` | `:277-391` | `estimate_with_acb` — wiring del actor closure + critic + boss |
| `estimator/app/prompts/estimation/v3/user.j2` | `:7-15` | bloque condicional `<critic_feedback>` |
| `estimator/app/routers/sessions.py` | `:203-236` | endpoint `POST /sessions/{id}/estimate-acb` |
**Los type aliases** (`boss.py:38-39`):

```python
ActorCallable = Callable[[CriticFeedback | None], EstimationResult]
CriticCallable = Callable[[EstimationResult], CriticFeedback]
```
El Boss recibe **funciones**, no objetos. Eso lo desacopla totalmente del actor y del critic — puedes inyectar fakes en tests sin construir clases mock complicadas.

**Las DTOs** (`schemas/acb.py:15-35`):

```python
BossDecision = Literal["accept", "iterate", "synthesize"]


class ACBIteration(BaseModel):
    """Audit record for a single actor+critic round.

    Persisted in the response so the caller can show the full trace in the UI
    (or in a debug panel) and so we can reason about the system end-to-end.
    """

    iteration: int = Field(ge=0)
    decision_after: BossDecision
    critic_verdict: str
    critic_confidence: int = Field(ge=0, le=100)
    issue_summary: list[str] = Field(default_factory=list)


class BossTrace(BaseModel):
    iterations: list[ACBIteration] = Field(default_factory=list)
    final_decision: BossDecision
    iterations_run: int = Field(ge=0)
```
`BossDecision` ≠ `CriticVerdict`. El Boss traduce:

| Critic produce | Boss decide |
|---|---|
| `"accept"` | `"accept"` |
| `"reject"` | `"synthesize"` |
| `"needs_iteration"` (con budget) | `"iterate"` |
| `"needs_iteration"` (sin budget) | `"synthesize"` |
**El constructor** (`boss.py:42-48`):

```python
class Boss:
    """Stateless orchestrator. One ``run`` per estimation."""

    def __init__(self, *, max_iterations: int = 2) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        self.max_iterations = max_iterations
```
`max_iterations >= 1` es invariante validada en construcción. `=0` sería un Boss que nunca corre — bug silencioso.

**El loop principal** (`boss.py:50-101`):

```python
def run(
    self,
    *,
    actor: ActorCallable,
    critic: CriticCallable,
) -> tuple[EstimationResult, BossTrace]:
    trace = BossTrace(final_decision="accept", iterations_run=0)
    feedback: CriticFeedback | None = None
    current: EstimationResult | None = None

    for iteration in range(self.max_iterations):
        current = actor(feedback)
        review = critic(current)

        decision = self._decide(review, iterations_left=(self.max_iterations - iteration - 1))
        trace.iterations.append(
            ACBIteration(
                iteration=iteration,
                decision_after=decision,
                critic_verdict=review.verdict,
                critic_confidence=review.confidence_in_review,
                issue_summary=[
                    f"[{i.severity}]{i.category} @{i.field_path}"
                    for i in review.issues[:5]
                ],
            )
        )
        trace.iterations_run = iteration + 1
        log.info(
            "boss_iteration",
            iteration=iteration,
            decision=decision,
            verdict=review.verdict,
            issues=len(review.issues),
        )

        if decision == "accept":
            trace.final_decision = "accept"
            return current, trace
        if decision == "synthesize":
            trace.final_decision = "synthesize"
            return self._synthesize_fallback(current, review), trace

        # decision == "iterate" → loop with feedback
        feedback = review

    # Loop exhausted: last actor result with critic still flagging issues.
    trace.final_decision = "synthesize"
    log.info("boss_iteration_budget_exhausted", iterations=self.max_iterations)
    # ``current`` must exist because max_iterations >= 1.
    assert current is not None
    return self._synthesize_fallback(current, feedback), trace
```
Cinco cosas a señalar mientras se lee:

1. `**feedback**`** empieza en **`**None**`. La primera llamada al actor es sin feedback. Si quisieras una variante “Critic-first” (el actor SIEMPRE recibe instrucciones de un revisor pre-llamado), invertirías el orden — pero entonces el primer actor call ya es de por sí “iterativo” sin que haya pasado nada.
1. `**issue_summary[:5]**` — solo los primeros 5 issues entran a la traza. El cap evita JSON gigantesco en respuestas con 12 issues marginales.
1. `**trace.iterations_run = iteration + 1**` — contador, no índice. Para que el cliente Rails muestre “2 iterations” no “1”.
1. **El return de **`**decision == "synthesize"**` está antes del `feedback = review`. Si llegamos a `synthesize` no necesitamos pasar feedback a una próxima iteración (no la habrá).
1. `**assert current is not None**` después del loop. Defensiva: `max_iterations >= 1` garantiza que pasamos al menos una vez por el cuerpo del for, así que `current` está seteado. Si alguien futuro relaja ese invariante, este assert le avisa.
`**_decide**` (`boss.py:105-114`):

```python
@staticmethod
def _decide(review: CriticFeedback, *, iterations_left: int) -> BossDecision:
    if review.verdict == "accept":
        return "accept"
    if review.verdict == "reject":
        return "synthesize"
    # needs_iteration
    if iterations_left > 0:
        return "iterate"
    return "synthesize"
```
Nueve líneas. Sin ramas innecesarias. Cualquier alumno que abra el archivo entiende la política en 10 segundos. Si la política creciera (e.g., “needs_iteration con confidence < 30 → synthesize”), se queda aquí — no migra al `run`.

`**_synthesize_fallback**` (`boss.py:116-156`):

```python
@staticmethod
def _synthesize_fallback(
    last_result: EstimationResult,
    last_feedback: CriticFeedback | None,
) -> EstimationResult:
    """When the Boss cannot accept, return the actor's last draft annotated
    with the Critic's open issues and a reduced confidence — never an empty
    envelope.

    Rationale: discarding the draft hides the best available answer behind
    a placeholder ("Out of scope"). The honest signal that the loop did not
    converge already travels in ``BossTrace.final_decision == "synthesize"``
    and the audit panel; the user is better served by an estimation with
    caveats than by zeroed-out numbers.
    """
    if last_feedback is None or not last_feedback.issues:
        # Defensive branch: no feedback to attach. Return the draft with a
        # minimal note so callers can still see that this came out of the
        # synthesize path.
        note = "⚠ Open caveats from independent review: (no detail available)\n\n"
        new_summary = (note + last_result.summary)[:1200]
        return last_result.model_copy(update={"summary": new_summary})

    issue_lines = [
        f"- [{issue.severity}]{issue.category} ({issue.field_path}):{issue.description}"
        for issue in last_feedback.issues
    ]
    caveats_block = (
        "⚠ Open caveats from independent review (loop did not fully converge):\n"
        + "\n".join(issue_lines)
        + "\n\n"
    )
    new_summary = (caveats_block + last_result.summary)[:1200]
    # Floor at 30 to stay above ``LOW_CONFIDENCE_THRESHOLD`` — going below
    # would trigger the schema validator that demands an "Out of scope:"
    # summary prefix, which contradicts the whole point of returning a
    # usable annotated draft.
    reduced_confidence = max(30, last_result.confidence_pct // 2)
    return last_result.model_copy(
        update={
            "summary": new_summary,
            "confidence_pct": reduced_confidence,
        }
    )
```
**Tres observaciones**:

1. **El summary lleva los issues como markdown bullets antepuestos al borrador real del actor**. El usuario lee exactamente qué se le advirtió y a continuación la estimación que el actor produjo.
1. **NO se fuerza prefijo “Out of scope:”**. Las cifras del actor (phases, total_cost_eur, total_duration_weeks) se preservan; solo se recorta la `confidence_pct` a la mitad, con piso de 30 para no caer bajo `LOW_CONFIDENCE_THRESHOLD`. La señal honesta de “no convergió” la aporta el `BossTrace.final_decision == "synthesize"` y el panel ACB en la UI, no un envelope cero.
1. **Trim a 1200 chars**. Si el Critic produjo 12 issues con descripciones largas, el summary completo (caveats + draft) se trunca antes de violar `Field(max_length=1200)`. Defensivo.
**El bloque **`**<critic_feedback>**`** que conecta todo** (`prompts/estimation/v3/user.j2:7-15`):

```plain text
{% if critic_feedback %}
<critic_feedback>
A previous version of your estimation was reviewed by an independent auditor. Address the following issues before producing the next answer; do not repeat the same mistakes.

{% for issue in critic_feedback.issues %}
- [{{ issue.severity }}] {{ issue.category }} at `{{ issue.field_path }}`: {{ issue.description }}{% if issue.suggested_fix %} (suggested fix: {{ issue.suggested_fix }}){% endif %}
{% endfor %}
</critic_feedback>
{% endif %}
```
Condicional Jinja. **Aparece SOLO si **`**critic_feedback**`** está presente**. En la iteración 0 está ausente; en la iteración 1+ está poblado. Cero rama en Python — toda la lógica vive en el template.


### 7.3 Por qué esta solución

- `**BOSS_MAX_ITERATIONS=3**`** por defecto** (`config.py:63`). Tres iteraciones es el mínimo razonable: un borrador inicial + dos retries dirigidos por el Critic. Con sólo dos rondas (la configuración original) el actor rara vez consigue cerrar todas las issues estructuradas en una única re-llamada, y el bucle caía al synthesize sin que el alumno viera convergencia. El coste extra es 1-2 LLM calls en el peor caso y compensa la mejora de tasa de aceptación.
- **Synthesize devuelve el último borrador del actor anotado con los caveats del Critic, NO un envelope OoS**. La honestidad del audit la aporta el `BossTrace.final_decision == "synthesize"` y el panel ACB en la UI; descartar el borrador silenciaría la mejor información disponible para el usuario y producía pantallas con coste=0 que se leían como “ha fallado”. Política actual: preservar phases/totales del actor, anteponer la sección “⚠ Open caveats” al summary, recortar `confidence_pct` a la mitad con piso de 30 para no caer en la zona OoS.
- **El Critic puede fallar y el Boss lo absorbe**. Critic.review tiene su propio fallback (Bloque 6.3); devuelve `CriticFeedback(verdict="accept", ..., confidence_in_review=0)` cuando el LLM revienta. El Boss recibe ese accept y devuelve el actor draft sin tocarlo. Graceful degradation end-to-end.
- **Boss es stateless**. Cada `Boss.run` es independiente. Nada en `Boss` recuerda entre estimaciones — toda la memoria conversacional vive en `Session.history`, no en el orquestador. Si quisieras paralelizar dos endpoints ACB a la vez, no hay shared mutable state.
**Demo en vivo** (con un transcript que provoque issues — depende del modelo, puede ser solo accept):

```bash
SID_ACB=$(curl -s -X POST http://localhost:8000/sessions | python3 -c 'import sys,json;print(json.load(sys.stdin)["session_id"])')

curl -s -X POST "http://localhost:8000/sessions/$SID_ACB/estimate-acb" \
  -F transcript='Estimar plataforma compleja: marketplace de servicios con pagos, KYC, chat, app móvil, panel admin, multi-idioma. Equipo de 2 personas en 6 semanas.' \
  -F project_type=web_saas -F detail_level=detailed -F output_format=phases_table \
  | python3 -m json.tool | head -60
```
Ver el campo `acb.iterations`: cada entrada con su verdict, confidence y issue_summary. **Y luego un curl al modo actor con el mismo transcript** para comparar.


---


## Bloque 8 — Trade-offs medibles + cierre (110–120 min)


### 8.1 Antes/después con el golden dataset (5 min)

**Comando**:

```bash
cd estimator
uv run python -m evals.run --mode actor --output /tmp/actor.json
uv run python -m evals.run --mode acb   --output /tmp/acb.json

# Comparar
python3 -c '
import json
a = json.load(open("/tmp/actor.json"))
b = json.load(open("/tmp/acb.json"))
print(f"actor:  {a[\"cases_passing\"]}/{a[\"cases_total\"]} passing")
print(f"acb:    {b[\"cases_passing\"]}/{b[\"cases_total\"]} passing")
print()
print(f"actor avg latency: {sum(r.get(\"latency_ms\",0) for r in a[\"rows\"]) / max(len(a[\"rows\"]),1):.0f} ms")
print(f"acb   avg latency: {sum(r.get(\"latency_ms\",0) for r in b[\"rows\"]) / max(len(b[\"rows\"]),1):.0f} ms")
'
```
**Lectura típica** (orientativa — depende del modelo):

| Modo | Cases passing | Avg latency | Avg LLM calls / turn |
|---|---|---|---|
| actor | 12/16 | ~1.5s | 2 (actor + extractor) |
| acb | 13-14/16 | ~3.5s | 4-5 (actor + critic + (1-2 iters) + extractor) |
> **Aviso**: estas cifras se midieron con `BOSS_MAX_ITERATIONS=2` y la rúbrica original del Critic. Tras la re-calibración actual (`BOSS_MAX_ITERATIONS=3`, umbrales relajados, bias-to-accept), la columna “cases passing” de ACB sube por dos efectos compuestos: más aceptaciones genuinas del Critic y un fallback que ya no devuelve OoS sino el borrador con caveats. Re-medir con `uv run python -m evals.run --mode acb` antes del directo y actualizar la tabla.
**Discusión** (no leer la tabla — discutirla):

- ACB **no garantiza** mejor calidad en todos los casos. Cuando el actor primer-tiro ya estaba bien, ACB añade latencia y coste sin ganancia.
- Los casos que ACB mejora son los que el Critic detecta como `phase_imbalance` o `math_error` — el feedback estructurado le da al actor algo concreto que cambiar.
- Los casos donde ACB **degrada** son los que el Critic se equivoca en su review (false positive de `hallucination`, por ejemplo) y mete al actor en una iteración innecesaria. Con la nueva política de synthesize (no-OoS), un “degrade” se ve como una estimación con caveats — el usuario decide; antes era directamente una pantalla de “Out of scope” sin números.

### 8.2 Cuándo el patrón es overkill (3 min)

**Qué decir**:

- **No usar ACB para**: estimaciones rápidas de baja confianza (la pena cae sobre todo en latencia), conversaciones muy cortas (1-2 turnos) donde el riesgo de phase_imbalance es bajo, contextos donde el coste por llamada importa más que la calidad marginal.
- **Sí usar ACB para**: estimaciones críticas (cliente importante, contrato grande), proyectos con compliance o NDA (tier executive donde un error de cifra cuesta caro), cualquier punto donde el alumno construya un agente de **escritura** que pueda contradecirse a sí mismo entre turnos (auditar es la antítesis de inventar).

### 8.3 Conexión con módulo 5 + despedida (2 min)

**Qué decir**:

- En el **módulo 5** veremos orquestación de varios agentes, no solo dos roles (actor+critic) sino árboles de decisión con sub-agentes especializados. ACB es el peldaño escolar de esa progresión.
- **Entregables**:
  - El código de la sesión está en la rama `session_5`.
  - El ejercicio de la próxima sesión (módulo 3) introducirá RAG real sobre los adjuntos. Plazo: ver Notion / Discord.
- **Gracias y abrir Q&A**.
**Pregunta de cierre**:
> “Si tuvierais que añadir un cuarto rol al patrón ACB para vuestro dominio, ¿cuál sería? ¿Por qué?”


---


## Anexo A — Tabla maestra de archivos creados / modificados

Verificado contra `git status` en la rama `session_05_live` el día del directo.


### Estimator (FastAPI)

| Path | Tipo | Bloque | Cambio |
|---|---|---|---|
| `estimator/app/sessions/compression/__init__.py` | new | 1 | re-exporta las cuatro piezas + `apply_compression` |
| `estimator/app/sessions/compression/anchors.py` | new | 1 | `_HEURISTIC_PATTERNS`, `AnchorMatch`, `AnchorDetector` |
| `estimator/app/sessions/compression/summarizer.py` | new | 1 | `_SummaryEnvelope`, `CumulativeSummarizer` |
| `estimator/app/sessions/compression/policy.py` | new | 1 | `CompressionPolicy`, `apply_compression` wrapper |
| `estimator/app/sessions/tier_resolver.py` | new | 2 | `Tier`, `_RULES`, `resolve_tier` |
| `estimator/app/sessions/models.py` | modified | 1, 2 | nuevos slots `anchors`/`summary` en `ConversationHistory`; `last_resolved_tier`/`last_tier_rule` en `Session`; `append()` ya no auto-trimea |
| `estimator/app/prompts/conversation_summary/v1/system.j2` | new | 1 | prompt del summarizer (13 ln) |
| `estimator/app/prompts/conversation_summary/v1/user.j2` | new | 1 | template con `<previous_summary>` y `<evicted_messages>` |
| `estimator/app/prompts/estimation/v3/system.j2` | new | 2, 5 | v3 con bloque `<audience>` |
| `estimator/app/prompts/estimation/v3/user.j2` | new | 5, 7 | user template con bloque condicional `<critic_feedback>` |
| `estimator/app/prompts/critic/v1/system.j2` | new | 6 | prompt del Critic (29 ln) |
| `estimator/app/prompts/critic/v1/user.j2` | new | 6 | template con `<original_transcript>`, `<estimation_under_review>` etc. |
| `estimator/app/prompts/loader.py` | modified | 1, 2, 6 | añadir `render_conversation_summary_prompt`, ampliar v3 con tier/critic_feedback, `render_critic_prompt` |
| `estimator/app/schemas/critic.py` | new | 6 | `CriticIssueCategory`, `CriticIssue`, `CriticFeedback` |
| `estimator/app/schemas/acb.py` | new | 7 | `BossDecision`, `ACBIteration`, `BossTrace` |
| `estimator/app/schemas/estimation.py` | modified | 7 | añadir `ACBResponse(EstimationResponse)` con campo `acb: BossTrace` |
| `estimator/app/services/critic.py` | new | 6 | `Critic.review` con fallback gracioso |
| `estimator/app/services/boss.py` | new | 7 | `Boss.run`, `_decide`, `_synthesize_fallback` |
| `estimator/app/services/estimation.py` | modified | 1, 2, 5, 7 | extender `estimate_conversational` con tier + compresión; nuevo `estimate_with_acb` |
| `estimator/app/routers/sessions.py` | modified | 1, 2, 7 | exponer `anchors_count`/`summary_chars`/`last_*_tier` en `SessionInfoResponse`; param `tier` en endpoints; endpoint `/estimate-acb` |
| `estimator/app/dependencies.py` | modified | todos | pasar `CRITIC_MODEL`/`BOSS_MAX_ITERATIONS`/etc. al constructor del servicio |
| `estimator/app/config.py` | modified | todos | 5 nuevas variables Session 5 live (ver Anexo B) |
| `estimator/evals/__init__.py` | new | 3 | re-exporta `GoldenCase`, `load_dataset`, las tres métricas, `run_all_metrics` |
| `estimator/evals/dataset.py` | new | 3 | `GoldenCase` Pydantic + loader |
| `estimator/evals/metrics.py` | new | 3 | `SchemaAdherenceMetric`, `CostBoundsMetric`, `ContentRecallMetric` |
| `estimator/evals/run.py` | new | 3, 8 | CLI runner (`--mode`, `--limit`, `--http`, `--output`) |
| `estimator/evals/golden_dataset.json` | new | 3 | 16 casos curados |
| `estimator/pyproject.toml` | modified | 3 | añadir `deepeval>=1.0` (dev) |
| `estimator/tests/test_compression_anchors.py` | new | 1 | tests del detector heurístico + LLM fallback |
| `estimator/tests/test_compression_policy.py` | new | 1 | tests del loop de compresión |
| `estimator/tests/test_sessions_models.py` | modified | 1 | actualizar — `append()` ya no auto-trimea |
| `estimator/tests/test_sessions_metadata.py` | modified | 0.2 | tests del extractor cubriendo el merge |
| `estimator/tests/test_sessions_window.py` | modified | 0.2 | tests de ventana respetando el nuevo contrato |
| `estimator/tests/test_tier_resolver.py` | new | 2 | tests de las 4 reglas + override + chain |
| `estimator/tests/test_prompts_v3.py` | new | 2 | render del template v3 con cada tier |
| `estimator/tests/test_critic.py` | new | 6 | schema validators + fallback gracioso |
| `estimator/tests/test_boss_orchestration.py` | new | 7 | accept primer pass, iterate+accept, synth budget, reject inmediato, trace por iter |
| `estimator/tests/test_sessions_acb.py` | new | 7 | endpoint `/estimate-acb` end-to-end |
| `estimator/tests/test_evals_metrics.py` | new | 3 | unit tests de las tres métricas |
| `estimator/tests/test_evals_run.py` | new | 3 | smoke del runner |
| `estimator/tests/conftest.py` | modified | todos | extender `FakeLLMWrapper` con `register_response_for` |

### Estimator-web (Rails)

| Path | Tipo | Bloque | Cambio |
|---|---|---|---|
| `estimator-web/app/services/estimator_ai/client.rb` | modified | todos | `estimate_in_session_acb`, `build_estimate_body` con tier opcional |
| `estimator-web/app/controllers/chat_sessions_controller.rb` | modified | todos | params `mode`/`tier`; `refresh_metadata_snapshot` persistiendo `runtime_snapshot` |
| `estimator-web/app/views/chat_sessions/_form.html.erb` | modified | 2, 7 | dropdown “Audience tier” + radio “Estimation mode” |
| `estimator-web/app/views/chat_sessions/_metadata_panel.html.erb` | modified | 1, 2 | tier resuelto + rule + anchors_count + summary_chars |
| `estimator-web/app/views/chat_sessions/_estimation_result.html.erb` | modified | 7 | `<details>` expander con la traza ACB por iteración |
| `estimator-web/app/models/chat_session.rb` | modified | 1, 2 | `remote_session_snapshot` accessor sobre `runtime_snapshot` |
| `estimator-web/db/migrate/20260518120000_add_runtime_snapshot_to_chat_sessions.rb` | new | 1, 2 | columna `runtime_snapshot :jsonb null:false default:{}` |
| `estimator-web/db/schema.rb` | modified | 1, 2 | regenerated tras la migración |
| `estimator-web/test/services/estimator_ai/client_test.rb` | modified | todos | tests del modo ACB + tier opcional |
| `estimator-web/test/controllers/chat_sessions_controller_test.rb` | modified | todos | tests del switch mode + refresh_metadata_snapshot |
**Total**: 30 archivos nuevos + 13 modificados en `estimator/`, 7 modificados + 1 nuevo en `estimator-web/`.


---


## Anexo B — Variables de entorno nuevas

| Variable | Default | Bloque | Notas |
|---|---|---|---|
| `ANCHOR_DETECTION_MODE` | `heuristic` | 1 | Pon `llm` para activar el clasificador (1 llamada cheap-model extra por turno). |
| `COMPRESSION_MODEL` | `gpt-4o-mini` | 1 | Modelo usado por el summarizer. |
| `CONVERSATIONAL_PROMPT_VERSION` | `v3` | 2 | Volver a `v2` deshabilita audience + critic_feedback sin romper nada. |
| `CRITIC_MODEL` | `gpt-4o-mini` | 6 | El Critic es cheap por diseño. |
| `BOSS_MAX_ITERATIONS` | `3` | 7 | Define el budget de re-actor calls tras la 1ª crítica. Bajar a 1 deja al Boss prácticamente como pass-through; subir más allá de 3 raramente compensa (coste lineal con upside marginal). |
`get_settings()` es un singleton cacheado con `lru_cache`: cambiar `.env` requiere `docker compose up -d --force-recreate estimator`, no basta con `--reload`.


---


## Anexo C — Curls de respaldo

```bash
# Crear sesión
curl -s -X POST http://localhost:8000/sessions | python3 -m json.tool

# Estimación actor — tier auto-derivado
curl -s -X POST "http://localhost:8000/sessions/$SID/estimate" \
  -F transcript='Estimar plataforma de e-commerce con catálogo de 5000 productos y checkout con Stripe.' \
  -F project_type=web_saas -F detail_level=medium -F output_format=phases_table \
  | python3 -m json.tool

# Estimación actor con override explícito a executive
curl -s -X POST "http://localhost:8000/sessions/$SID/estimate" \
  -F transcript='Estimar plataforma de e-commerce con catálogo de 5000 productos y checkout con Stripe.' \
  -F project_type=web_saas -F detail_level=medium -F output_format=phases_table \
  -F tier=executive | python3 -m json.tool

# Estimación ACB con tier auto-derivado
curl -s -X POST "http://localhost:8000/sessions/$SID/estimate-acb" \
  -F transcript='Plataforma compleja: marketplace de servicios con pagos, KYC, chat, app móvil, panel admin, multi-idioma. Equipo de 2 personas en 6 semanas.' \
  -F project_type=web_saas -F detail_level=detailed -F output_format=phases_table \
  | python3 -m json.tool

# Inspección de la sesión (panel + tier resuelto + anchors + summary)
curl -s "http://localhost:8000/sessions/$SID" | python3 -m json.tool

# Adjunto PDF en multipart (escenario real del cliente Rails)
curl -s -X POST "http://localhost:8000/sessions/$SID/estimate" \
  -F transcript='Aquí adjunto el brief funcional. Estima en consecuencia.' \
  -F project_type=web_saas -F detail_level=medium -F output_format=phases_table \
  -F attachments=@/tmp/brief.pdf | python3 -m json.tool

# Evals (in-process — usa TestClient)
cd /Users/antonioperez/projects/ia/ai-engineering/estimator
uv run python -m evals.run --mode actor --limit 5
uv run python -m evals.run --mode acb   --limit 5

# Evals (HTTP — útil para medir latencia real contra el container)
uv run python -m evals.run --mode actor --http http://localhost:8000

# Evals (16 cases completos a fichero, para diffear runs)
uv run python -m evals.run --mode actor --output /tmp/actor.json
uv run python -m evals.run --mode acb   --output /tmp/acb.json
```

---


## Anexo D — Cambios en el cliente Rails

Resumen de lo que el alumno puede hacer sin tocar Python:

- **Form**: nuevo dropdown “Audience tier” (`auto/executive/pm/developer/default`) + radio “Estimation mode” (`actor` / `actor-critic-boss`).
- **Panel lateral**: tier resuelto + rule disparada, anchors_count, summary_chars.
- **Resultado**: si la estimación viene del modo ACB, debajo aparece un `<details>` con la traza por iteración (verdict, confidence, issues).

### D.1 Cliente HTTP — `app/services/estimator_ai/client.rb`

**Nuevo método** para el endpoint ACB (`client.rb:61-71`):

```ruby
# ACB variant: same contract; the response carries an ``acb`` field with
# the iteration trail. Surfaces a richer view of how the estimation was
# produced (verdict + issues per iteration).
def estimate_in_session_acb(session_id, request, attachments: [], tier: nil)
  raise ArgumentError, "request must be valid" unless request.valid?
  response = multipart_conn.post(
    "/sessions/#{session_id}/estimate-acb",
    build_estimate_body(request, attachments, tier)
  )
  handle_response(response)
end
```
**Construcción del body** (`client.rb:75-94`):

```ruby
def build_estimate_body(request, attachments, tier)
  body = {
    "transcript"    => request.transcript,
    "project_type"  => request.project_type,
    "detail_level"  => request.detail_level,
    "output_format" => request.output_format
  }
  # ``tier`` is opt-in; FastAPI treats omission as "auto-derive".
  body["tier"] = tier if tier.present? && tier != "auto"

  Array(attachments).compact.each do |file|
    body["attachments"] = [] unless body["attachments"].is_a?(Array)
    body["attachments"] << Faraday::Multipart::FilePart.new(
      file.tempfile,
      file.content_type || "application/octet-stream",
      file.original_filename
    )
  end
  body
end
```
**Tres detalles**:

1. `**tier**`** es opcional**: solo se pasa si está presente y no es “auto”. FastAPI trata la ausencia como auto-derive (Bloque 2).
1. `**Faraday::Multipart::FilePart**` — viene de la gema `faraday-multipart` (`Gemfile:24-25`). Si el alumno olvida la gema, el endpoint multipart explota en runtime.
1. `**build_estimate_body**`** es compartido** entre `estimate_in_session` (modo actor) y `estimate_in_session_acb`. Cualquier futura propiedad nueva en el contrato se añade aquí una vez.

### D.2 Controller — `app/controllers/chat_sessions_controller.rb`

**El switch de modo** (`chat_sessions_controller.rb:37-52`):

```ruby
attachments = Array(params[:attachments]).compact_blank
tier = params[:tier].presence
mode = params[:mode].to_s == "acb" ? "acb" : "actor"
client = EstimatorAi::Client.new
payload =
  if mode == "acb"
    client.estimate_in_session_acb(
      @chat_session.remote_session_id, @request,
      attachments: attachments, tier: tier
    )
  else
    client.estimate_in_session(
      @chat_session.remote_session_id, @request,
      attachments: attachments, tier: tier
    )
  end
```
**Whitelist defensiva**: `mode == "acb" ? "acb" : "actor"` — cualquier valor que no sea exactamente `"acb"` cae al actor. Esto evita que un alumno pasando `?mode=destroy_all` haga algo inesperado.

**El refresh del snapshot** (`chat_sessions_controller.rb:124-133`):

```ruby
def refresh_metadata_snapshot(chat_session)
  info = EstimatorAi::Client.new.get_session(chat_session.remote_session_id)
  chat_session.update!(
    latest_metadata: info["metadata"] || {},
    runtime_snapshot: info.except("metadata") || {},
    turn_count: (info["message_count"] || 0) / 2
  )
rescue StandardError => e
  Rails.logger.warn("Failed to refresh metadata snapshot:#{e.message}")
end
```
**Cómo se reparte la información**:

- `latest_metadata`: la sub-clave `metadata` del `SessionInfoResponse` (project_name, team_size, technologies, agreed_scope).
- `runtime_snapshot`: todo lo demás del response (anchors_count, summary_chars, last_resolved_tier, last_tier_rule, message_count, max_turns). El panel lateral del Bloque 1+2 lo lee.
- `turn_count`: derivado — `message_count / 2` porque cada turno son dos mensajes.
- **El rescue StandardError**: si FastAPI está fuera o el endpoint da 404, no rompemos la creación de `Estimation` que ya pasó. El snapshot es nice-to-have.

### D.3 Formulario — `app/views/chat_sessions/_form.html.erb`

**Dropdown de tier** (`_form.html.erb:83-95`):

```plain text
<div>
  <%= label_tag:tier,"Audience tier",class:"block text-sm font-bold mb-1 text-white/90"%>
  <%=select_tag:tier,
options_for_select([
["Auto (resolve from context)","auto"],
["Executive","executive"],
["Project Manager","pm"],
["Developer","developer"],
["Default","default"]
],"auto"),
class:"..."%>
  <p class="text-xs text-white/50 mt-1">Auto detects NDA / compliance / team size and adapts the prompt.</p>
</div>
```
**Mode fieldset** (`_form.html.erb:98-114`):

```plain text
<fieldset class="border border-white/10 rounded-md p-4">
  <legend class="text-xs uppercase tracking-tight text-white/50 font-bold px-2">Estimation mode</legend>
  <div class="flex gap-6 mt-1">
    <label class="flex items-center gap-2 text-sm text-white/90 cursor-pointer">
      <%=radio_button_tag:mode,"actor",true,
class:"accent-brand"%>
      Actor only
      <span class="text-xs text-white/50">(1 LLM call)</span>
    </label>
    <label class="flex items-center gap-2 text-sm text-white/90 cursor-pointer">
      <%=radio_button_tag:mode,"acb",
class:"accent-brand"%>
      Actor-Critic-Boss
      <span class="text-xs text-white/50">(2–5 LLM calls, audited)</span>
    </label>
  </div>
</fieldset>
```
**Decisiones de UX**:

- `actor` viene checked por defecto (3er arg `true` en `radio_button_tag`). El usuario solo opta-in en ACB.
- Las etiquetas “(1 LLM call)” y “(2–5 LLM calls, audited)” comunican coste/calidad sin necesidad de tooltip.

### D.4 Panel lateral — `app/views/chat_sessions/_metadata_panel.html.erb`

**Snapshot section** (`_metadata_panel.html.erb:5-27`):

```plain text
<%if chat_session.persisted?%>
  <p class="text-xs text-white/70 font-mono break-all"><%= chat_session.remote_session_id%></p>
  <p class="text-xs text-white/50 mt-1">Turns: <%= chat_session.turn_count%></p>
  <% snapshot= chat_session.remote_session_snapshot%>
  <%if snapshot.present?%>
    <div class="mt-2 space-y-1 text-xs text-white/70">
      <%if snapshot["last_resolved_tier"].present?%>
        <p>
          Tier:
          <span class="font-bold text-white"><%= snapshot["last_resolved_tier"]%></span>
          <%if snapshot["last_tier_rule"].present?%>
            <span class="text-white/50">(<%= snapshot["last_tier_rule"]%>)</span>
          <%end%>
        </p>
      <%end%>
      <%if (snapshot["anchors_count"]||0).positive?%>
        <p>Anchors kept: <span class="font-bold text-white"><%= snapshot["anchors_count"]%></span></p>
      <%end%>
      <%if (snapshot["summary_chars"]||0).positive?%>
        <p>Summary chars: <span class="font-bold text-white"><%= snapshot["summary_chars"]%></span></p>
      <%end%>
    </div>
  <%end%>
<%end%>
```
**Esto es lo que el alumno ve cuando algo falla en el tier**: si esperaba “executive” pero el panel dice `Tier: default`, sabe que ninguna regla disparó. Si dice `Tier: executive (nda_detected)`, sabe que el resolver detectó NDA. La explainability vive aquí.


### D.5 Traza ACB — `app/views/chat_sessions/_estimation_result.html.erb`

**El expander** (`_estimation_result.html.erb:71-93`):

```plain text
<% acb= estimation.response_payload.is_a?(Hash) ?estimation.response_payload["acb"] :nil%>
<%if acb.is_a?(Hash)&& acb["iterations"].is_a?(Array)%>
  <details class="rounded-md border border-white/10 bg-ink/30 p-3">
    <summary class="cursor-pointer text-xs uppercase tracking-tight text-white/70 font-bold">
      Actor-Critic-Boss trace — final: <%= acb["final_decision"]%>,
      <%= acb["iterations_run"]%> iteration(s)
    </summary>
    <ol class="mt-3 space-y-2 text-xs text-white/80">
      <% acb["iterations"].eachdo|it|%>
        <li class="rounded bg-ink/40 p-2">
          <div class="font-bold text-white">
            Iteration <%= it["iteration"]%> — verdict: <%= it["critic_verdict"]%>
            <span class="text-white/50">(confidence <%= it["critic_confidence"]%>)</span>
          </div>
          <%Array(it["issue_summary"]).eachdo|issue_line|%>
            <div class="mt-1 text-white/70 font-mono"><%= issue_line%></div>
          <%end%>
          <div class="mt-1 text-white/50">Boss decision: <%= it["decision_after"]%></div>
        </li>
      <%end%>
    </ol>
  </details>
<%end%>
```
**Tres puntos de UX**:

1. `**<details>**`** colapsable**: la traza no estorba al estimador feliz. Solo se abre si el usuario quiere auditar.
1. `**acb**`** solo está presente en respuestas del modo ACB** — el guard `acb.is_a?(Hash)` hace que el expander no aparezca en estimaciones del modo actor.
1. **El **`**issue_summary**`** viene del Boss** (`boss.py:71-74`): `f"[{i.severity}] {i.category} @ {i.field_path}"`. Esto es exactamente lo que se renderiza en `font-mono`. Si el alumno lee la traza ve la categoría del Critic, no prosa generada — auditoría real.

### D.6 Persistencia — modelo + migración

**ChatSession model** (`app/models/chat_session.rb`, 18 líneas, full):

```ruby
# A conversational session anchored to a remote (FastAPI) session_id.
# The full message history lives in the FastAPI process memory; here we keep
# the metadata snapshot of the latest turn (for the side panel) and the count
# of turns so the UI can show "turn N of N" when useful.
class ChatSession < ApplicationRecord
  has_many :estimations, dependent: :nullify

  validates :remote_session_id, presence: true, uniqueness: true

  def latest_metadata_hash
    latest_metadata.is_a?(Hash) ? latest_metadata : {}
  end

  # Snapshot of the GET /sessions/:id response (tier, anchors, summary
  # chars). Used by the side panel.
  def remote_session_snapshot
    runtime_snapshot.is_a?(Hash) ? runtime_snapshot : {}
  end
end
```
**Los dos accessor wrappers** existen porque Postgres devuelve `nil` para JSON columns vacías en algunos paths; el `.is_a?(Hash)` mantiene siempre un Hash para los templates.

**Migración** (`db/migrate/20260518120000_add_runtime_snapshot_to_chat_sessions.rb`, full):

```ruby
class AddRuntimeSnapshotToChatSessions < ActiveRecord::Migration[8.0]
  def change
    # Stores the full GET /sessions/:id payload from FastAPI:
    # last_resolved_tier, last_tier_rule, anchors_count, summary_chars,
    # plus message_count. Read by the side panel and tests.
    add_column :chat_sessions, :runtime_snapshot, :jsonb, null: false, default: {}
  end
end
```
**Por qué JSONB y no columnas separadas**: el contrato del snapshot puede crecer en futuras sesiones. Una columna JSON nos da flexibilidad sin migración adicional cada vez que FastAPI añada un campo al `SessionInfoResponse`. Trade-off: pierdes índices SQL — aceptable porque las queries son por `chat_session_id`, no por contenido del snapshot.


### D.7 Cómo extender a otro stack

Si un alumno pregunta “¿y si yo no uso Rails?”, la respuesta es: nada de lo de arriba es Rails-específico. Lo que importa es:

1. Llamada multipart al backend con `transcript` + `tier?` + `attachments[]`.
1. Diferenciar dos endpoints (`/estimate` y `/estimate-acb`) por un flag del front (radio/checkbox/select).
1. Después de cada respuesta, hacer `GET /sessions/{id}` y persistir lo nuevo (`last_resolved_tier`, etc.) para el panel.
1. Renderizar el `acb` opcional en la respuesta.
Cualquier stack (Next.js, Django, Flask + HTMX, Svelte) reproduce esto con cuatro funciones equivalentes. Lo que NO debe hacerse: llamar directo a OpenAI/Anthropic desde el front. El cliente solo habla con la API del estimator.


---


## Mantenimiento de este guion

Antes de cada directo, verificar que **todos** los `archivo:línea` citados en
el guion siguen vigentes. La lista exhaustiva:

```bash
cd /Users/antonioperez/projects/ia/ai-engineering/estimator

# --- Bloque 0.2 (ejercicio) ---
grep -nE 'class Message|class ConversationHistory|class ProjectMetadata|class Session|def append|def to_messages|def is_empty|def merge_with|last_resolved_tier|last_tier_rule' app/sessions/models.py
grep -nE 'def update_metadata' app/sessions/metadata_extractor.py
grep -nE 'create_session|get_session|estimate_in_session|_resolve_session_and_enrich|class SessionInfoResponse' app/routers/sessions.py
grep -nE '_SUPPORTED_EXTS|def _extract_pdf|def _extract_docx|def extract_text|def enrich_transcript' app/attachments/extractor.py

# --- Bloque 1 (compresión) ---
grep -nE '_HEURISTIC_PATTERNS|class AnchorMatch|class AnchorDetector|def detect|def _detect_heuristic|def _detect_llm' app/sessions/compression/anchors.py
grep -nE 'class _SummaryEnvelope|class CumulativeSummarizer|def summarize' app/sessions/compression/summarizer.py
grep -nE 'class CompressionPolicy|def should_compress|def apply|def apply_compression' app/sessions/compression/policy.py
wc -l app/prompts/conversation_summary/v1/system.j2 app/prompts/conversation_summary/v1/user.j2

# --- Bloque 2 (tier) ---
grep -nE 'class Tier|class ResolutionContext|class TierRule|_NDA_PATTERN|_REGULATORY_PATTERN|_DEV_KEYWORDS_PATTERN|def _has_nda|def _has_regulatory_context|def _is_small_team|def _technical_audience|_RULES|def resolve_tier' app/sessions/tier_resolver.py
grep -n '<audience>' app/prompts/estimation/v3/system.j2

# --- Bloque 3 (evals) ---
grep -nE 'class GoldenCase|def load_dataset|ProjectTypeStr|DetailLevelStr|OutputFormatStr|TierStr' evals/dataset.py
grep -nE 'class MetricResult|class SchemaAdherenceMetric|class CostBoundsMetric|class ContentRecallMetric|_DEFAULT_METRICS|def run_all_metrics' evals/metrics.py
grep -nE 'def main|add_argument|Mode = Literal|_run_case' evals/run.py
# Confirma que el JSON tiene 16 casos
python3 -c "import json; print(len(json.load(open('evals/golden_dataset.json'))), 'cases')"

# --- Bloque 5 (Actor wiring) ---
grep -nE 'def estimate_conversational|def estimate_with_acb|def _actor|check_input|resolve_tier|render_conversational_prompt|enforce_scope_response|apply_compression|update_metadata' app/services/estimation.py

# --- Bloque 6 (Critic) ---
grep -nE 'CriticIssueCategory|CriticIssueSeverity|CriticVerdict|class CriticIssue|class CriticFeedback|iteration_requires_blocking_issue' app/schemas/critic.py
grep -nE 'class Critic|def review' app/services/critic.py
wc -l app/prompts/critic/v1/system.j2 app/prompts/critic/v1/user.j2

# --- Bloque 7 (Boss) ---
grep -nE 'BossDecision|class ACBIteration|class BossTrace' app/schemas/acb.py
grep -nE 'ActorCallable|CriticCallable|class Boss|def __init__|def run|def _decide|def _synthesize_fallback' app/services/boss.py
grep -nE 'class ACBResponse' app/schemas/estimation.py
grep -nE 'critic_feedback' app/prompts/estimation/v3/user.j2
grep -nE 'estimate_in_session_acb' app/routers/sessions.py

# --- Config + deps ---
grep -nE 'ANCHOR_DETECTION_MODE|COMPRESSION_MODEL|CONVERSATIONAL_PROMPT_VERSION|CRITIC_MODEL|BOSS_MAX_ITERATIONS|METADATA_EXTRACTOR_MODEL|MAX_CONVERSATION_TURNS|MAX_ATTACHMENT_CHARS' app/config.py
grep -nE 'def get_estimation_service' app/dependencies.py

# --- Anexo D (Rails) ---
cd ../estimator-web
grep -nE 'def create_session|def get_session|def estimate_in_session|def estimate_in_session_acb|def build_estimate_body' app/services/estimator_ai/client.rb
grep -nE 'def create|def refresh_metadata_snapshot|params\[:mode\]|params\[:tier\]' app/controllers/chat_sessions_controller.rb
grep -nE 'label_tag :tier|select_tag :tier|radio_button_tag :mode' app/views/chat_sessions/_form.html.erb
grep -nE 'last_resolved_tier|last_tier_rule|anchors_count|summary_chars|remote_session_snapshot' app/views/chat_sessions/_metadata_panel.html.erb
grep -nE 'acb\[|iterations_run|final_decision|critic_verdict' app/views/chat_sessions/_estimation_result.html.erb
cat app/models/chat_session.rb
cat db/migrate/20260518120000_add_runtime_snapshot_to_chat_sessions.rb
```
Si el código se ha movido entre sesiones, actualizar las tablas
`archivo:línea` antes del directo (10 min de mantenimiento que ahorran 30 min
de improvisación con un alumno frustrado preguntando “¿pero dónde está esa
función?”).

Tras un cambio mayor (nueva regla de tier, nueva categoría de Critic), correr:

```bash
cd estimator
uv run pytest -v
uv run python -m evals.run --mode actor --limit 16 --output /tmp/sanity.json
uv run python -m evals.run --mode acb   --limit 8  --output /tmp/sanity-acb.json
```
Los tests deben quedar verdes y el eval no debería bajar más de 1-2 casos
respecto al run de calibración previo. Si baja más, el cambio merece una
revisión antes de subirlo a directo.

**Cómo validar que los snippets embebidos en el guion siguen siendo correctos**:

```bash
# Extraer todos los snippets de archivo:línea de la guía
grep -oE '[a-zA-Z_/.]+\.(py|j2|rb|erb)(:[0-9]+(-[0-9]+)?)?' guides/session-5-live-guide.md | sort -u
```
Abrir media docena de muestras al azar y confirmar que el código en esas
líneas dice lo que la guía pretende citar. Si encuentras una discrepancia,
ten en cuenta que reescribir la sección suele ser más rápido que parchear el
guion al lado del código.
