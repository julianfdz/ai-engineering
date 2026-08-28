# Pack de demo — proyecto simulado "VetNova"

Material para enseñar la app desplegada (`https://estimator.mras.es`) con un
proyecto ficticio pero creíble: **VetNova**, una red de clínicas veterinarias
que quiere portal de clientes + integración con su software de gestión + app
móvil + panel analítico. Cuatro componentes bien diferenciados a propósito:
es lo que hace lucir tanto la estimación clásica como los flujos agénticos
(que descomponen el proyecto pieza a pieza).

Dos ficheros:

| Fichero | Para qué pantalla |
|---|---|
| `brief-estimacion.txt` | El formulario clásico de estimación (párrafos, corto) |
| `transcripcion-reunion.txt` | Los flujos RAG/agénticos (transcripción de reunión completa) |

## Guión por pantalla

### 1. Estimación clásica (Sesión 4) — `/estimations/new`

Pega `brief-estimacion.txt`, tipo `web_saas`, detalle `medium`. Qué señalar:
- La salida es **JSON estructurado validado** (fases que suman el total — es un
  validador Pydantic, no suerte), no texto libre.
- **Truco de la caché**: envía EXACTAMENTE lo mismo otra vez → respuesta
  instantánea marcada como cacheada (caché exacta por SHA-256). Cambia una
  palabra sin cambiar el significado → caché semántica.

### 2. Guardrails (Sesión 3) — mismo formulario

Pega algo con PII, p. ej.:
> Necesito una web para mi clínica. Soy Ana Ruiz, DNI 51234567L, teléfono
> 612 345 678, y mi tarjeta es 4111 1111 1111 1111.

→ rechazo 400 con el motivo en el flash. Buen momento para explicar que el
guardrail corre ANTES de gastar un céntimo de LLM.

### 3. Chat conversacional (Sesión 5) — `/chat_sessions`

Arranca con el brief y luego aprieta con seguimientos que fuerzan memoria:
- «¿Y si quitamos la app móvil, cuánto baja?»
- «El cliente quiere entrar antes de primavera, ¿qué recortarías?»

### 4. Flujos RAG y agénticos (Sesiones 9–14) — necesitan corpus (ver abajo)

Con `transcripcion-reunion.txt` como entrada:
- **Wizard RAG** (`/rag/estimation_runs`, S9–S10): reformulación → estructura
  libre → revisión humana → horas por consenso de históricos. Señalar los
  badges de fiabilidad por tarea (verde/rojo según haya precedente histórico).
- **Grafo LangGraph** (`/rag/graph_estimation_runs`, S13): el flujo PAUSA dos
  veces esperando aprobación humana — la pausa sobrevive a un reinicio del
  contenedor (checkpointer en Postgres/Neon).
- **Supervisor** (`/rag/supervisor_estimation_runs`, S14): aquí decide el
  MODELO qué agente corre en cada paso — enseñar el `_routing_trace` (quién
  decidió qué y por qué) y el audit trail de herramientas.

### 5. Ajustes — cambio de modelo en caliente

Cambia `PRIMARY_MODEL` desde la pestaña Ajustes y repite la estimación: sin
redeploy, y las cachés particionan por modelo (no se mezclan respuestas).

## Corpus para las pantallas RAG (una vez)

Las pantallas del bloque 4 buscan en presupuestos históricos; sin corpus
responden «sin precedentes». Cargarlo cuesta céntimos (embeddings de ~1,5k
tareas con `text-embedding-3-small`) y se hace una vez:

1. En LOCAL, con el stack del curso levantado y `AI_SERVICE_TOKEN` vacío:
   `docker compose exec ai-service python scripts/build_task_corpus.py --ingest`
   (y opcionalmente `scripts/build_multi_index_corpus.py` para la S10).
2. Volcar: `./scripts/dump_corpus.sh /tmp/corpus.dump`
3. Restaurar contra Neon:
   `docker run --rm -i postgres:16 pg_restore -d "postgresql://...neondb?sslmode=require" --clean --if-exists --no-owner < /tmp/corpus.dump`

## Nota

Proyecto y personas 100% ficticios. El sector (healthcare/veterinaria) está
elegido a propósito: el corpus sintético del curso incluye `healthcare`, así
que la búsqueda de precedentes encuentra análogos razonables.
