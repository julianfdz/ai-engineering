# HANDOVER — estado del fork de Julián (léeme si eres una sesión nueva de IA)

Fork personal de `julianfdz` del repo del Máster en AI Engineering de LIDR.
Julián es **profesor invitado** (dará la S12 y la S14, en desorden), sin
permisos de escritura en el upstream. Este fork tiene DOS propósitos: (1) un
despliegue propio del sistema y (2) material docente propio (`curso-master/`).
El contexto técnico del proyecto en sí está en `CLAUDE.md` — este fichero
cubre lo que el fork añade y su estado operativo.

## Flujo de trabajo con Julián

- Trabaja mergeando la rama de trabajo (`claude/fork-deploy-setup-omfudo`) a
  `main` desde su máquina, y committea directamente en `main` a veces.
  **Regla para agentes: antes de cada tarea, fetch de `main` Y de la rama, y
  merge de `origin/main` a la rama si trae algo; push a la rama.** Los
  conflictos típicos vienen de notebooks guardados con outputs.
- Los mensajes de Julián suelen ser dictados por voz: interpretarlos con
  flexibilidad ("lanchhain" = LangChain, "raj" = RAG...).
- Sus commits en main llevan mensajes cortos tipo "dvdv" — normal.

## Despliegue propio (funcionando)

- **App viva**: https://estimator.mras.es — VPS propio con Portainer, detrás
  del Caddy contenedorizado del host (red externa `intrabuhonet`,
  `reverse_proxy business-backend:3000` en su Caddyfile).
- **Compose**: `docker-compose.vps-cloud.yml` (autocontenido, fork-only):
  build en el VPS, torch CPU-only vía build-arg `TORCH_CPU_ONLY` del
  Dockerfile del ai-service, sin env_file (variables en Portainer).
- **BBDD**: Neon (proyecto en eu-west-2, endpoint directo sin `-pooler`):
  `neondb` (servicio IA / pgvector) y `estimator_web_production` (Rails).
  El fix `_translate_libpq_ssl_params` en
  `ai-service/app/foundation/persistence/database.py` traduce
  `sslmode`/`channel_binding` para asyncpg (test: `tests/test_database_url.py`).
- **Pendiente conocido**: el corpus RAG NO está cargado en Neon (las pantallas
  RAG dicen "sin precedentes"); receta en `docs/deploy-cloud-neon.md`.
  La contraseña de Neon debería rotarse en algún momento (pasó por chats).

## Material docente (`curso-master/`)

- `sesiones/00-listado.md` — temario completo (17 filas, módulos).
- `sesiones/s12/` — guion propio (secciones 1–7 hechas: agente, tools,
  skills, prompts, sesión, traza, tipos→píldora; 8–10 pendientes), la guía
  oficial de LIDR (PDF + txt), y dos notebooks ejecutables:
  `agente-minimo.ipynb` y `cache-checker.ipynb` (auto-instalan el SDK).
- `pildoras/` — cag, rag, scout-retrieval (técnica bautizada aquí),
  tipos-de-agentes (ficha de 5 ejes, ReAct), memoria (jerarquía), HITL.
- `herramientas/` — alembic, jinja2, langchain-langgraph, python, notebooks,
  fastapi-fastmcp. Todos con SVGs propios en `assets/` (validados en mermaid
  9 y 11 cuando aplica).
- `dar-una-sesion.md` + `sesion.sh` (raíz) — levantar cualquier sesión en
  local con BBDD aislada por sesión (`docker compose -p aieng-sN`).
  **`sesion.sh` aún no se ha probado en una máquina real con Docker.**
- Convención de las fichas: "qué es / cómo funciona / dónde verlo en el
  proyecto", castellano, SVGs de estilo consistente (paleta slate/blue/
  green/amber, fondo #f8fafc).

## Datos operativos sueltos

- Demo docente: `examples/demo-julian/` (proyecto ficticio VetNova + guión
  por pantalla).
- El `.env` real está gitignorado; Julián lo tiene en local y en Portainer.
  NUNCA commitearlo (fork público; ya se debatió y decidió).
- Kit de despliegue portable a otras ramas: los commits del compose cloud +
  fix asyncpg (cherry-pick sobre cualquier session_N de la era 13+).
- La sesión de Claude que construyó todo esto:
  https://claude.ai/code/session_01DMSkN8gHC8V7PLvffWsu4E
