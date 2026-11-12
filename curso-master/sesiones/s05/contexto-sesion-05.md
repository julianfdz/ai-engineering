# Sesión 5 — Funcionalidades avanzadas (contexto)

> Material de Julián para la clase del 12/11/2026. Fuente: el Notion de LIDR (edición 2026-09, donde la dio Manuel
> Lemos) en `LIDR\edicion-26-09\s05-funcionalidades-avanzadas\` y la rama `session_05_live` del repo.

## 1. De qué va

Segunda mitad del bloque «producto IA»: el estimador ya conversa (ejercicio previo) y hoy se le añaden cuatro cosas,
todas **ya implementadas** (la clase es de explicar y ejecutar, no de teclear):

| Bloque | Qué | Dónde |
|---|---|---|
| 1 | Compresión híbrida de memoria: resumen + anclas + ventana | `app/sessions/compression/` |
| 2 | Tier de audiencia deducido en cada turno (executive / pm / developer / default) | `app/sessions/tier_resolver.py` + `prompts/estimation/v3` |
| 3 | Golden dataset (16 casos) y tres métricas deterministas | `estimator/evals/` |
| 4-7 | Patrón Actor-Critic-Boss en `POST /sessions/{id}/estimate-acb` | `services/critic.py`, `services/boss.py`, `schemas/critic.py`, `schemas/acb.py` |

Antes: S4 (productos IA avanzados: caché semántica, guardrails). Después: S6 (Data-driven AI), que abre el módulo de
datos y RAG.

## 2. Ejercicio previo (rama `session_5`)

Memoria conversacional con ventana deslizante (6 pares), `ProjectMetadata` extraída por LLM en cada turno, endpoints
`/sessions` en multipart y adjuntos PDF/DOCX con extracción local.

## 3. En local

- Worktree `ai-engineering-fork-julian\ai-engineering-s05`, rama `session_05_live_local` (sale de
  `origin/session_05_live`). Proyecto docker `aieng-s05live`, contenedores `s05-*`, puertos 8000 / 3000 / 6379 / 8001 / 5432.
- Imagen ligera (sin torch): compila en ~1 min.
- `estimator/.env` (no se sube) con la clave de OpenAI, `PRIMARY_MODEL=gpt-4o` y `CRITIC_MODEL=gpt-4o`.
- `docker-compose.override.yml` con nombres `s05-*` y montaje de `estimator/evals`.
- `estimator-web/bin/*` y `Procfile.dev` a LF.
- La S10 está parada (`docker compose -p aieng-s10live stop`), con sus volúmenes intactos.

## 4. Diferencias con el guion de LIDR

- **gpt-4o-mini no sirve como modelo principal aquí**: devolvía 502 en varias demos (no cuadra la suma de las fases
  ni con 6 reintentos de Instructor). Con gpt-4o funcionan todas.
- **Transcripciones cortas → «Out of scope»**: las del guion («Estimar un CRM en React y Postgres…») a veces se
  rechazan por vagas. Los ejemplos de la web llevan versiones algo más completas.
- **El tier executive tiende a «Out of scope»**: el caso 007 del golden set falla en los dos modos.
- **La web oficial de la rama no tiene el Anexo D** (selector de tier, modo ACB, panel con tier/anclas/resumen, traza
  ACB). Está implementado en nuestra rama, con 6 **Demo presets** (uno por demo).
- `evals/run.py`: `main()` está en la l. 163 y `_run_case_in_process` en la 112 (el guion dice 97 y 52). Todas las líneas de nuestro guion y de las diapos ya cuentan la cabecera de 11 líneas que lleva cada fichero.

## 5. Resultados verificados (12/11/2026, gpt-4o)

| Demo | Resultado |
|---|---|
| Baseline CRM | 51.000 €, 12 semanas, 5 fases, prompt v3 |
| Compresión, 8 turnos | ventana máx. 12 mensajes; turno 7 → 2 anclas (NDA); turno 8 → resumen de 908 caracteres |
| Tier sin NDA / con NDA / técnico | `default` / `executive (nda_detected)` / `developer (technical_audience)` |
| ACB CRM + Stripe (crítico gpt-4o) | `accept` en la iteración 0 |
| ACB marketplace imposible (crítico gpt-4o) | `reject → synthesize` o `needs_iteration → accept` según la ejecución |
| ACB CRM + Stripe (crítico gpt-4o-mini) | 3 × `needs_iteration` → `synthesize`; `math_error` falso (las fases sí sumaban 57.000) |
| Golden set, 8 casos | actor **5/8**, ACB **6/8** (gana el 004; el 007 falla en los dos) |

Hallazgos para comentar en clase:

- El tier vuelve a `default` en el turno 2 aunque el NDA siga anclado: el resolver no mira las anclas.
- «Equipo de 2 personas» no da `pm` en el primer turno: la metadata se actualiza después de resolver el tier.
- El crítico puede devolver `accept` con un issue `critical`: el validador no lo impide.

## 6. Material

| Pieza | Fichero |
|---|---|
| Línea de formación (código, comandos, interfaz) | [`guion-julian.md`](guion-julian.md) |
| Guion de LIDR con nota local | [`guion-directo.md`](guion-directo.md) |
| Deck (23 diapos, franja grande «En el código») | [`Sesion05-Julian-Fernandez.pdf`](Sesion05-Julian-Fernandez.pdf) · generador [`deck/build_deck.py`](deck/build_deck.py) |
| Capturas de la web | `curso-master/assets/s05-ui-*.png` |

Las Google Slides oficiales de la sesión solo abren con la cuenta de LIDR; el deck es propio.
