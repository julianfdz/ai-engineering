# Chuleta del directo — Sesión 14 (120 min)

> Terminal siempre desde `ai-engineering-fork-julian\ai-engineering\estimator` con `set PYTHONUTF8=1`.
> UI: http://localhost:3000/rag/supervisor_estimation_runs (run #3 pausado · run #4 validado).
> Contingencia: `sesiones/s14/demos/*.txt` y `exercises/session-14/example_run_*.txt`. Los warnings `LiteLLM… botocore` son ruido.

## Antes de empezar (5 min antes)
- [ ] Docker Desktop: 5 contenedores verdes · abrir la bandeja en el navegador y comprobar que #3 sigue "esperando revisión"
- [ ] Terminal abierta en `estimator/` con `set PYTHONUTF8=1` hecho
- [ ] Deck abierto · VS Code con `app/domain/graph/supervisor/` a mano
- [ ] `uv run pytest tests/domain/graph/supervisor -q` → 90 passed (opcional, 2 s)

## Bloque 0 · Encuadre (10 min) — slides 2-5
1. **Frase de apertura:** "El módulo 5 es una escalera. Hoy pintamos los dos últimos peldaños: competición y seguridad. Y vais a ver que no son infraestructura nueva."
2. Slide 2 (escalera) → Slide 3: **"¿Quién es dueño del control flow?** S13: el orden está en `build.py`. S14: lo decide el modelo. Esa es la frontera, no el número de nodos."
3. Slide 4 (mapa maestro): "Una sola estimación recorre esto. Hoy solo tocamos tres tramos, cada uno detrás de un flag: `estimate_generator` compite, el gate se testea, y aparece `persistence_agent`."
4. Slide 5 (ORBITA): "Telemetría con QKD, COBOL de Aduanas, un login 'sencillo' con HSM. Unos componentes tienen análogos, otros no existen en el mundo. Fuerza la discrepancia a propósito."
5. Regla de oro: "Si algo choca con la arquitectura del repo, gana el repo."

## Bloque 1 · Tres fallos (15 min) — slide 6
6. **Demo:** `uv run pytest tests/domain/graph/supervisor/test_failure_modes.py -v` → 6 tests, dos por fallo (síntoma + fix).
7. Abrir `exercises/session-14/failure_modes/routing_no_converge.py::_is_legal` — **Fallo 1 ping-pong:** "el router re-elige un agente que ya actuó; solo para cuando el presupuesto fuerza `finish` (`source == "limit"`)". Fix: `and not _already_ran(target, history)`. Frase: "el presupuesto es la red; la guarda es el arreglo".
8. `state_clobber.py` — **Fallo 2:** canal `list` plano = last-write-wins → `InvalidUpdateError` en un fan-out. Fix: `Annotated[list[dict], operator.add]`. "Esto es lo que va a permitir la competición dentro de 10 minutos."
9. `interrupt_no_resume.py` — **Fallo 3:** el resume devuelve 200 pero el run sigue pausado: `thread_id` distinto. Fix: `f"s14:{estimation_id}"` en ambas llamadas (`estimate_supervisor.py::_thread_config`).
10. **Bridge:** "Con los tres claros, ya podemos añadir el primer patrón sin miedo a que el grafo se nos vaya en bucle."

## Bloque 2 · Competición (30 min) — slides 7-9
11. **Pregunta al aire (slide 7):** "Si un estimador dice 340 h y otro 190 h, ¿eso es un error o es información?"
12. Pizarra: "Un número consolidado esconde la incertidumbre. Dos estimadores con criterios REALES distintos —no adjetivos— y su distancia te dice cuánta incertidumbre estructural tiene el proyecto."
13. **Demo:** `uv run python scripts/run_supervisor_s14.py --memory --stub --compete` → señalar en la traza: `COMPETITION` (conservative ~1182 d vs aggressive ~731 d), `divergence ratio ~0.47`, `synthesized 800..1250 d`, `HUMAN REVIEW triggered: YES`.
14. **Código** (`competition.py`): las dos aristas desde `START` = paralelo real (mismo superstep) · `proposals` con reducer (el Fallo 2) · `compute_divergence` = aritmética, cero LLM (`ratio = spread / midpoint`; high ≥ 0.5, medium ≥ 0.2) · el synthesizer **nunca promedia**: rango + supuestos + preguntas.
15. Slide 9 (`agents.py::_apply_divergence_penalty`): "La divergencia no es un cuarto camino: resta confianza (`0.4 × ratio`) y salta el gate que ya teníamos. Nada nuevo aguas abajo."
16. **UI:** abrir run **#4** → señalar "Rango (competición conservador ↔ agresivo) 28–58 d" y las preguntas abiertas. "El cliente consume el rango sin cambio de contrato: viaja dentro del JSONB."
17. FAQ si preguntan: "¿por qué subgrafo dentro de un nodo?" → el supervisor enruta uno a uno; el fan-out es estático, así la estrella no se toca. "¿Y si coinciden?" → ratio 0, penalización 0: también es información.
18. **Bridge:** "Hemos añadido un agente que RAZONA distinto. Ahora añadimos uno que ESCRIBE — y ahí la seguridad deja de ser opcional."

## Bloque 3 · Sandboxing (30 min) — slides 10-12
19. **Criterio (slide 10):** "Un agente con capacidad de escritura puede hacer daño irreversible. ¿Cómo lo contengo sin salir del código de aplicación?" Tres capas: concesión con riesgo · validación + tenencia · auditoría de TODO.
20. **Demo 1:** `uv run python scripts/run_supervisor_s14.py --memory --stub --persist` → señalar `HUMAN REVIEW: an irreversible save_estimate is queued; the human pause authorises the write` → `decision: approve` → `AUDIT TRAIL [ok] persistence_agent tool:save_estimate … (guarded, human-authorised)`.
21. **Demo 2:** `… --violate` → señalar `[DENIED] budget_searcher tool:validate_estimate` y el evento `agent_privilege_denied`. "La llamada mala la inyecta el script, no producción: se ve la denegación real sin ensuciar el sistema. Y el run sobrevive (`SUPERVISOR_PRIVILEGE_STRICT=false`)."
22. **Código** (`sandbox.py`): `ToolRisk` + `AGENT_TOOL_GRANTS` + `verify_tool_grants()` → "rompe el ARRANQUE, no el run" (demo relámpago opcional: `python -c` añadiendo `"rogue": frozenset({"delete_all"})` → `GrantVerificationError`). `guard_action`: privilegio → args → **tenencia** (`req.estimation_id == run`) → irreversible sin approve = diferido. `execute_guarded`: audita allowed/DENIED/DEFERRED con preview redactado + digest SHA-256.
23. Slide 12 (`gate.py` 4º disparador): "Lo irreversible se enruta al MISMO gate humano. Aprobar la estimación ES autorizar el save. Rechazarla = nunca se persiste."
24. **UI:** run **#4**, audit trail → la fila `save_estimate` con badge **IRREVERSIBLE** y resultado "persisted (guarded, human-authorised)". Y en run **#3** la misma fila en **DIFERIDA** (amarillo) porque aún espera.
25. FAQ: "¿Esto es sandboxing de verdad?" → de aplicación: privilegio + argumentos + auditoría. Nada de aislamiento de proceso/SO ni secretos: eso es la S15.
26. **Bridge:** "Tenemos competición y contención. Falta asegurarnos de que la puerta humana funciona SIEMPRE, aunque la ruta la decida un modelo."

## Bloque 4 · Testing HITL (30 min) — slides 13-15
27. **Criterio (slide 13):** "Si la ruta la decide el modelo y no es determinista, ¿qué testeo? No puedo afirmar 'X corrió en el paso N'. Testeo INVARIANTES."
28. **Demo:** `uv run pytest tests/domain/graph/supervisor/test_hitl_edge_cases.py -v` → 12 tests parametrizados por las 3 señales; ninguno afirma un paso concreto.
29. Recorrer las 6 propiedades (slide 13): pausa cuando debe · estado persistido en el checkpoint · resume aplica la decisión · **nadie actuó sin precondiciones** (subsecuencia de `routing_history`, el más ilustrativo — abrir `test_no_agent_acted_before_its_preconditions`) · techo de pasos · resume idempotente (409 en el router).
30. Slide 14 (`gate.py::review_reasons`): "función PURA, sin reloj ni red: por eso `interrupt()` puede re-ejecutarla en el resume. El validador escribe HECHOS; el gate posee el VEREDICTO."
31. Slide 15: las 3 transcripciones de `exercises/session-14/edge_cases/` — cliente que no sabe lo que quiere → confianza baja · "login sencillo" para 10M sesiones → fuera de rango · relojes de estroncio → sin precedente.
32. **UI — la demo estrella:** bandeja → "Esperando revisión (1)" → abrir run **#3 (ORBITA)**: motivos verbatim (`confidence 0.00`, `save_estimate is queued`), la fila QKD "No references available", editor por componente. **Pulsar Aprobar en directo** → vuelve como *validada*, aparece el rango de competición y la fila `save_estimate` pasa de DIFERIDA a ejecutada. Frase: "el gate es una cola de trabajo, no un formulario: la mayoría de runs no pausan; solo aterrizan los que no son de fiar."
33. FAQ: "¿por qué no testeáis la ruta exacta?" → la decide un LLM; sería flaky por diseño. "¿Y si subo el umbral a 0.9?" → más pausas, más trabajo humano: es la perilla del negocio, por config, sin tocar el validador.
34. **Bridge:** "Con esto el sistema está funcionalmente completo. Cerremos el módulo y veamos qué le falta para producción."

## Bloque 5 · Cierre (5 min) — slides 16-17
35. Recap en una frase por peldaño (slide 16): grafo lineal · supervisor enjaulado · comunicación por hechos · HITL condicional · competición aritmética · seguridad de mínimo privilegio. "Ninguno es infraestructura nueva: son principios de ingeniería conocidos aplicados a un componente que alucina."
36. Puente a S15 (slide 17): "Funciona de punta a punta… en tu máquina. Sin desplegar, sin monitorizar, sin límite de coste — un run que se va en llamadas de router cuesta dinero sin que nadie lo vea. La S15 es exactamente eso."
37. Ejercicios S15 · ROTI · gracias.

## Si algo falla
- Demo online lenta o sin red → proyectar `sesiones/s14/demos/0X-….txt` (misma salida, ya comentada arriba).
- `--compete` sin divergencia visible → es el stub; enseñar la traza guardada.
- El gate NO pausa en una demo → `SUPERVISOR_PERSISTENCE_ENABLED` no propagó: relanzar el comando (nuevo proceso), no `--reload`.
- Rails caído → `docker compose -p aieng-s14live restart estimator-web` desde la carpeta del repo (30 s). API caída → `… restart estimator`.
- Quiero una run limpia que no pause → `set SUPERVISOR_CONFIDENCE_THRESHOLD=0.35` antes del comando.
