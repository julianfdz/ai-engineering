# Sesión 14 — Sistemas multi-agente y patrones avanzados: competición, sandboxing y HITL

> Guía oficial LIDR del directo (copiada de la plataforma el 15/09/2026). Módulo 5 · 120 min · flipped classroom.
> **Entrada:** el alumno trae el pre-ejercicio — un supervisor a mano (`StateGraph` + `Command`) que enruta a cuatro agentes de mínimo privilegio, con audit trail y puerta humana condicional. Rama `session_14`.
> **Salida:** ese grafo extendido en el directo con tres patrones — competición conservador/agresivo, sandboxing de acciones irreversibles y testing del flujo humano por invariantes. Rama `session_14_live`.
> Idioma: guía en español; código, payloads, logs y prompts en inglés. Tres capas: frontend, backend de negocio (Rails), servicio IA (Python + FastAPI). Toda la lógica multi-agente vive en el servicio IA.

## Cómo leer el guion

| Marca | Qué es |
|---|---|
| `■ Criterio` | La pregunta humana que hila el bloque. |
| `■ Fundamento · pizarra` | La idea de fondo, sin editor. |
| `■ Dónde vive.` | Fichero + símbolo real (`ruta::símbolo`). |
| `■ Demo · terminal` | Comando ejecutado en vivo (primero se ve el comportamiento). |
| `■ Walkthrough · código` | Se abre el código que produce ese comportamiento. |
| `🖥️ MOSTRAR UI` | Cambio al navegador (backend de negocio Rails). |
| `■ Defensa oral / FAQ` | Preguntas probables + respuesta corta. |
| `■ Contingencia` | Qué hacer si algo falla en directo. |
| `■ Bridge` | La frase que enlaza con el bloque siguiente. |
| `[SLIDE: …]` | Punto donde hace falta apoyo visual. |

**Tesis.** El módulo 5 sube una escalera: grafo lineal → supervisor que enruta en caliente → comunicación entre agentes → intervención humana. Hoy añadimos los dos últimos peldaños — competición (la discrepancia como señal) y seguridad (sandboxing de acciones) — y comprobamos que no son infraestructura nueva: son los mismos principios aplicados a un componente que alucina.

**Caso de anclaje.** Una única transcripción recorre toda la sesión: el proyecto **ORBITA** (`exercises/session-14/sample_transcript_edge_case.txt`) — telemetría de estaciones terrenas con QKD, un mainframe COBOL de Aduanas, un "login sencillo" con driver biométrico y HSM, y un alcance que crecerá. Fuerza la discrepancia: unos componentes tienen análogos y otros no tienen precedente.

## Prerrequisitos (10–15 min antes)

```bash
git switch session_14_live
cd estimator
docker compose up -d            # opcional: la mayoría de demos corren --memory --stub
uv run pytest tests/domain/graph/supervisor -q
uv run python scripts/run_supervisor_s14.py --memory --stub --compete | tail -20
uv run python scripts/run_supervisor_s14.py --memory --stub --persist | tail -20
```

Aviso sobre `--stub`: el corpus enlatado es pequeño y genérico, casi toda estimación sale con `grounded_ratio` bajo y la puerta salta por confianza baja. Para una ejecución que NO pause: `SUPERVISOR_CONFIDENCE_THRESHOLD=0.35`.

Pre-flight: rama `session_14_live` · tests del supervisor en verde · `build_supervisor_graph(competitive=True, sandboxed=True)` arranca · trazas `exercises/session-14/example_run_{competition,persistence}.txt` presentes · Logfire opcional.

---

## Bloque 0 — Encuadre (10 min)

**Criterio.** ¿Qué frontera cruzamos hoy, y por qué el multi-agente no es "más nodos con nombres ambiciosos"?

`[SLIDE: La escalera del módulo 5 — grafo lineal → supervisor → comunicación → HITL → competición → seguridad.]`

En la S13 el orden estaba escrito en `build.py`. En el pre-ejercicio de la S14 el **modelo** lee el estado y elige el siguiente especialista, y el grafo obedece. Esa es la frontera entre workflow y sistema agéntico: **quién es dueño del control flow**. Hoy no reescribimos nada: lo extendemos por tres sitios.

`[SLIDE: EL FLUJO COMPLETO — mapa maestro: estrella supervisor → competición → gate condicional → persistencia.]`

```
                 ┌───────────── aristas de vuelta (estáticas) ─────────────┐
 transcript ─▶ supervisor ──Command(goto)──┬─▶ requirements_extractor ─────┤
 (ORBITA)      router LLM enjaulado         ├─▶ budget_searcher ────────────┤
               (pasos · legalidad ·         ├─▶ estimate_generator ─────────┤   ◀── ZOOM Bloque 2 (competición)
                fallback)                    ├─▶ coherence_validator ────────┤
                                            │      escribe HECHOS: confidence · out_of_range · grounded · divergence
                                            └─▶ finish
                                                  ▼
                                        human_review_gate                    ◀── ZOOM Bloque 4 (HITL)
                                        interrupt() SÓLO si hay señal · approve/adjust/reject
                                                  ▼
                                        persistence_agent ─▶ END             ◀── ZOOM Bloque 3 (sandboxing)
                                        (write sandboxed, guarded)
```

La estrella es el pre-ejercicio; hoy sólo cambian tres tramos — `estimate_generator` se vuelve competición (B2), el `human_review_gate` es pausa condicional (B4), y tras el gate se añade el `persistence_agent`, la única escritura contenida (B3). Todo detrás de flags (`competitive`, `sandboxed`). Regla de oro: si algo choca con la arquitectura del repo, gana el repo.

---

## Bloque 1 — Resolución de errores (15 min)

Tres fallos frecuentes del pre-ejercicio. Cada uno: demo del síntoma → fix con un `str_replace` → demo de que se arregla. Reproducciones en `exercises/session-14/failure_modes/`, fijadas por `tests/domain/graph/supervisor/test_failure_modes.py`.

`[SLIDE: Tres fallos — (1) enrutado que no converge · (2) estado que se pisa · (3) interrupt que no reanuda.]`

Demo: `uv run pytest tests/domain/graph/supervisor/test_failure_modes.py -v` (seis tests, dos por fallo: síntoma y arreglo).

### Fallo 1 — el enrutado no converge (ping-pong)
`failure_modes/routing_no_converge.py::_is_legal`. Síntoma: el supervisor rebota `requirements → budget → requirements …` y solo para por presupuesto de pasos (`source == "limit"`). Causa: aristas cíclicas + router que puede re-elegir a un agente que ya actuó. Fix: `return _inputs_ready(target, history) and not _already_ran(target, history)`. Sin la guarda, el grafo termina igual pero gasta 8 pasos y 8 llamadas: el presupuesto es la red de seguridad; la guarda es el arreglo.

### Fallo 2 — el estado se pisa (canal sin reducer)
`failure_modes/state_clobber.py::PlainState` vs `AccumulatingState`. Síntoma: dos agentes en el mismo superstep escriben al mismo canal → `InvalidUpdateError: Can receive only one value per step`, o en un resume la segunda escritura sustituye a la primera. Fix: `contributions: Annotated[list[dict], operator.add]`. Por eso `agent_contributions` y `routing_history` usan reducers en `state.py`; el fan-out de la competición depende de esto.

### Fallo 3 — el `interrupt()` no reanuda (`thread_id` mal)
`failure_modes/interrupt_no_resume.py::start_and_resume`. Síntoma: el grafo pausa, el revisor aprueba, el resume devuelve 200 — y el run sigue atascado (se creó un run nuevo). Causa: `thread_id` distinto entre invocación y resume. Fix: derivarlo igual en ambas — `{"configurable": {"thread_id": f"s14:{estimation_id}"}}` como `estimate_supervisor.py::_thread_config`.

---

## Bloque 2 — Caso avanzado 1: Competición (30 min)

📍 Zoom sobre `estimate_generator`. **Criterio.** Si un estimador dice 340h y otro 190h, ¿eso es un error o es información?

`[SLIDE: Competición — dos estimadores con priores distintos (RISK-FIRST vs REUSE-FIRST). La DIVERGENCIA es el dato, no los totales.]`

Un número consolidado esconde la incertidumbre. Dos estimadores con criterios distintos — uno pondera fricción de integraciones, deuda de especificación y certificaciones; el otro reutilización, alcance cerrado y análogos históricos — producen dos números, y su distancia dice cuánta incertidumbre estructural tiene el proyecto. La divergencia se calcula con **aritmética**; el sintetizador produce **rango + supuestos + preguntas abiertas**, nunca un promedio.

Demo: `uv run python scripts/run_supervisor_s14.py --memory --stub --compete` (contrastar con `example_run_competition.txt`: aggressive 705d, conservative 1250d, divergence ratio 0.558 (high), synthesized 750..1250d, HUMAN REVIEW triggered).

`[SLIDE: Logfire — spans "competition: conservative" y "competition: aggressive" en el MISMO superstep, luego "synthesizer".]`

**Dónde vive.** `app/domain/graph/supervisor/competition.py`.

`[SLIDE: Esquema competición — fan-out paralelo (2 aristas desde START) → synthesizer, con divergence→confidence→gate.]`

```
                        ┌──▶ conservative_estimator ──┐   (RISK-FIRST)
   brief ────▶ START                                  ├──▶ synthesizer ──▶ (low..high, driving_assumptions, open_questions)
                        └──▶ aggressive_estimator  ────┘   (REUSE-FIRST)      ┌ compute_divergence() ARITMÉTICA
   proposals: Annotated[list, operator.add]  ◀── fan-in por reducer         └ ratio ─▶ _apply_divergence_penalty ─▶ confidence ─▶ gate
```

1. Subgrafo con fan-out/fan-in real: `build_competition_subgraph()` — dos aristas desde `START`, join en `synthesizer`; ambos escriben a `proposals: Annotated[list[dict], operator.add]`.
2. Prompts sustantivamente distintos: `_CONSERVATIVE_SYSTEM_PROMPT` vs `_AGGRESSIVE_SYSTEM_PROMPT` — criterios, no adjetivos.
3. `compute_divergence(proposals)`: `spread`, `ratio = spread / midpoint`, `level` (high ≥ 0.5, medium ≥ 0.2). Cero LLM (`test_divergence_is_pure_arithmetic`).
4. El synthesizer no promedia: `SynthesizedEstimate` impone rango + `driving_assumptions` + `open_questions`.

`agents.py::competitive_estimate_generator` sustituye el nodo manteniendo el nombre `estimate_generator` (router, `_ORDER`, privilegios no se tocan). `_apply_divergence_penalty`: `penalty = SUPERVISOR_DIVERGENCE_PENALTY * ratio` → divergencia alta → confianza baja → salta el gate del pre-ejercicio. Nada nuevo aguas abajo.

FAQ: ¿por qué subgrafo dentro de un nodo? El supervisor enruta uno a la vez; el fan-out paralelo es un patrón estático — dentro del nodo el paralelismo es real y la estrella no se toca. ¿Trampa darle la divergencia al synthesizer? Al revés: el hecho aritmético lo pone el código. ¿Y si coinciden? ratio ≈ 0, penalización 0: la ausencia de discrepancia también es información.

🖥️ UI: `/rag/supervisor_estimation_runs/<id>` — `_completed.html.erb` muestra "Rango (competición conservador ↔ agresivo) 750–1250d" y preguntas abiertas, sin cambio de contrato. Contingencia: `example_run_competition.txt`.

---

## Bloque 3 — Caso avanzado 2: Sandboxing a nivel de agente (30 min)

📍 Zoom sobre `persistence_agent`. **Criterio.** Un agente con capacidad de escritura puede hacer daño irreversible. ¿Cómo lo contengo sin salir del código de aplicación (nada de despliegue ni aislamiento de proceso — eso es la S15)?

`[SLIDE: Tres capas de contención — (1) privilegio con RIESGO · (2) validación de argumentos + tenencia · (3) auditoría de TODA intención, incluidas las denegadas.]`

1. Concesión con riesgo: cada tool `READ`/`WRITE`/`IRREVERSIBLE`; un chequeo que falla el arranque si una concesión es incoherente.
2. Validación antes de ejecutar, incluida tenencia: el `estimation_id` de la acción coincide con el del run.
3. Auditoría de toda intención con efectos — incluidas las denegadas — con redacción de datos sensibles.

Regla que cierra el círculo: las acciones irreversibles se enrutan al mismo gate humano. La pausa que revisa la estimación **es** la autorización de la escritura.

Demos: `--persist` (HUMAN REVIEW: "an irreversible save_estimate is queued; the human pause authorises the write" → approve → AUDIT `[ok] persistence_agent tool:save_estimate estimate persisted (guarded, human-authorised)`) y `--violate` (fila `[DENIED] budget_searcher tool:validate_estimate` + evento `agent_privilege_denied`; la llamada la inyecta el script, no producción).

**Dónde vive.** `app/domain/graph/supervisor/sandbox.py`.

`[SLIDE: Esquema sandboxing — ActionRequest → guard_action (privilegio·args·tenencia·irreversible) → execute_guarded → {allowed|DENIED|DEFERRED}; irreversible → gate → persistence_agent.]`

```
  persistence_agent ── ActionRequest(agent, tool=save_estimate, args, estimation_id, step)
       ▼
  guard_action(req, state)  PURO, determinista
     1) privilegio  tool ∈ AGENT_TOOL_GRANTS[agent] ?        no ─▶ DENIED
     2) argumentos  args es objeto · save requiere 'estimate' no ─▶ DENIED
     3) TENENCIA    req.estimation_id == state.estimation_id  no ─▶ DENIED
     4) riesgo      IRREVERSIBLE y sin approve?              sí ─▶ requires_human_approval
       ▼ allowed
  execute_guarded ─▶ sink (escritura) ──▶ AUDIT structlog {allowed | DENIED | DEFERRED} (preview REDACTADO + digest SHA-256)
  verify_tool_grants() ◀── en build_supervisor_graph: si la tabla es incoherente, ROMPE EL ARRANQUE
```

Capa 1: `ToolRisk(StrEnum)`, `TOOL_RISK` (`save_estimate = IRREVERSIBLE`), `AGENT_TOOL_GRANTS` (deriva de `AGENT_PRIVILEGES` + `persistence_agent → {save_estimate}`), `verify_tool_grants()` → `GrantVerificationError` en el arranque. Demo relámpago: añadir `"rogue": frozenset({"delete_all"})` y llamar `verify_tool_grants()`.
Capa 2: `guard_action(req, state) -> GuardDecision` — privilegio → argumentos → tenencia → si `IRREVERSIBLE` sin aprobación, `requires_human_approval`.
Capa 3: `execute_guarded(req, state)` — registra allowed/denied/deferred con `estimation_id`, preview redactado (`_redact`), digest SHA-256; escritura a un sink inyectable (por defecto en memoria — sin BBDD, eso es S15).

`gate.py::review_reasons` 4º disparador: `if state.get("persist_requested"): reasons.append("an irreversible save_estimate is queued; the human pause authorises the write")`. `persistence_agent` tras el gate, arista `human_review_gate → persistence_agent → END`. Una estimación rechazada nunca se persiste (queda `deferred`).

FAQ: ¿por qué la escritura en su propio agente? Aislar la capacidad: los cuatro de lectura no pueden guardar ni por accidente. `SUPERVISOR_PRIVILEGE_STRICT=false`: la denegación devuelve un envelope y queda visible; `true` levanta `PrivilegeViolation`. ¿Sandboxing "de verdad"? A nivel de aplicación; no hay aislamiento de proceso ni de SO ni gestión de secretos — eso es S15.

🖥️ UI: `_audit_trail.html.erb` resalta `save_estimate` con badge **IRREVERSIBLE** y **DIFERIDA** en amarillo si esperaba aprobación. Test: `test_sandbox.py::test_estimation_id_mismatch_is_denied`.

---

## Bloque 4 — Caso avanzado 3: Testing del flujo HITL con edge cases (30 min)

📍 Zoom sobre `human_review_gate`. **Criterio.** Si la ruta la decide el modelo y no es determinista, ¿qué testeo? Invariantes.

`[SLIDE: Testear invariantes, no el camino — la pausa salta cuando debe · el estado persiste · el resume continúa con la decisión · ningún agente actuó sin precondiciones · el presupuesto se respetó · el resume es idempotente.]`

`[SLIDE: Esquema HITL — validator escribe HECHOS → review_reasons (4 disparadores, PURO) → interrupt() SÓLO si hay motivos → resume(approve/adjust/reject) → _apply_decision.]`

```
  coherence_validator escribe HECHOS ──▶ review_reasons(state)  PURA (interrupt() la re-ejecuta en el resume)
  confidence · out_of_range ·            ├ confidence < THRESHOLD ?
  grounded_components · persist_requested├ out_of_range ?            ¿algún motivo?
                                         ├ grounded/total < MIN_RATIO ?   no → auto-approve → END
                                         └ persist_requested ?            sí → interrupt({reasons}) ⏸ awaiting_human_review
                                                                                 Command(resume={decision}) approve/adjust/reject → _apply_decision
```

`gate.py::review_reasons` — tres disparadores base (confianza < umbral, fuera de rango, grounded/total < ratio mínimo) + el 4º de escritura. `gate.py::_apply_decision`: `reject` → `"rejected"` (estimate intacto: es evidencia); `adjust` → aplica `estimate_overrides` y rederiva `total_engineer_days` de los componentes; `approve` → `"validated"`.

Edge cases en `exercises/session-14/edge_cases/`: `low_confidence.txt`, `out_of_historical_range.txt` ("login sencillo" para 10M de sesiones), `no_precedent.txt` (relojes ópticos de estroncio).

Demo: `uv run pytest tests/domain/graph/supervisor/test_hitl_edge_cases.py -v` — 12 tests parametrizados por las tres señales, ninguno afirma un paso concreto:
- `test_each_signal_trips_the_pause` — `snapshot.next == ("human_review_gate",)` y el motivo correcto.
- `test_paused_state_is_persisted_in_the_checkpoint`.
- `test_resume_continues_with_the_human_decision_in_state` — `status == "validated"`, `next == ()`.
- `test_no_agent_acted_before_its_preconditions` — el orden de despacho leído de `routing_history` es subsecuencia de la escalera de dependencias, cualquiera que fuese el orden que pidió el modelo.
- `test_step_budget_was_never_exceeded`.
- `test_second_resume_on_a_finished_run_does_not_corrupt_it` — idempotencia (el router devuelve 409).

Todo network-free: los fakes (`conftest.py::FakeWrapper`, `wire`) escriptan router y retrieval; cada señal se fuerza controlando los hechos.

FAQ: ¿por qué no la ruta exacta? Porque la decide un LLM; sería flaky por diseño. ¿Las transcripciones disparan las señales de verdad? Contra retrieval + LLM reales sí; en tests se fuerza. ¿Idempotencia en producción? 409 en `POST …/{id}/resume`.

🖥️ UI: `/rag/supervisor_estimation_runs` — bandeja (`awaiting_review`, más antiguo primero); un run pausado muestra motivos verbatim + editor por componente + approve/adjust/reject. El gate es una cola de trabajo, no un formulario. Subir `SUPERVISOR_CONFIDENCE_THRESHOLD` a 0.9 → más pausas: la perilla del negocio.

---

## Bloque 5 — Cierre (5 min)

`[SLIDE: Recap del módulo 5 — grafo lineal → supervisor → comunicación → HITL → competición → seguridad.]`

- Grafo lineal (S13): orden en el código.
- Supervisor (S14 pre): el modelo decide el siguiente paso, enjaulado (pasos + legalidad + fallback).
- Comunicación: el estado tipado es la pizarra; los hand-overs pasan hechos, no conversación.
- HITL: la puerta condicional que para solo cuando los números no son de fiar.
- Competición: la discrepancia entre dos priores como señal — aritmética, no juicio del modelo.
- Seguridad: mínimo privilegio + validación + auditoría alrededor del único agente que escribe; lo irreversible pasa por el humano.

`[SLIDE: Puente a la S15 — funcionalmente completo pero corre en LOCAL: sin desplegar, sin monitorizar, sin límite de coste.]`

---

## Apéndice

| # | Bloque | Min | Demo clave | UI |
|---|---|---|---|---|
| 0 | Encuadre | 10 | pizarra | — |
| 1 | Resolución de errores | 15 | `pytest test_failure_modes.py -v` | — |
| 2 | Competición | 30 | `run_supervisor_s14.py --stub --compete` | `_completed` (rango + preguntas) |
| 3 | Sandboxing | 30 | `--persist` y `--violate` | `_audit_trail` (IRREVERSIBLE / DIFERIDA) |
| 4 | Testing HITL | 30 | `pytest test_hitl_edge_cases.py -v` | bandeja `/supervisor_estimation_runs` |
| 5 | Cierre | 5 | pizarra | — |

Errores previsibles: `--compete` sin divergencia → corpus stub homogéneo (usar ORBITA o bajar umbral) · el gate no pausa con `--persist` → `SUPERVISOR_PERSISTENCE_ENABLED` no propagó (recrear proceso) · `GrantVerificationError` al arrancar → comportamiento correcto, corrige la tabla · demo lenta/sin red → trazas `example_run_*.txt` · test HITL flaky → se testeó el camino, no un invariante.

Artefactos de `session_14_live`: `supervisor/competition.py`, `supervisor/sandbox.py`, `agents.py` (`competitive_estimate_generator`, `persistence_agent`, `_apply_divergence_penalty`), `gate.py` (4º disparador), `build.py` (flags + `verify_tool_grants`), `schemas.py` (`EstimateProposal`, `SynthesizedEstimate`), `config.py` (`SUPERVISOR_COMPETITION_ENABLED`, `SUPERVISOR_DIVERGENCE_PENALTY`, `SUPERVISOR_PERSISTENCE_ENABLED`), `scripts/run_supervisor_s14.py` (`--compete`/`--persist`), `exercises/session-14/{failure_modes,edge_cases}/`, trazas `example_run_{competition,persistence}.txt`, tests `test_{failure_modes,competition,sandbox,hitl_edge_cases}.py`, vistas Rails `_completed`/`_audit_trail`.

Límites: sí competición + divergencia aritmética, sandboxing de aplicación, irreversibles al gate, testing por invariantes. No despliegue, Docker, cloud, CI/CD, aislamiento de proceso/SO, secretos de runtime — S15. No se toca la referencia de `session_14` ni la lógica interna del backend de negocio.
