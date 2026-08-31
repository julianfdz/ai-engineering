#!/usr/bin/env bash
#
# sesion.sh — levanta cualquier sesión del máster en local, sin dolor.
#
#   ./sesion.sh 12          # sesión 12 (pre-ejercicio)
#   ./sesion.sh 12 live     # sesión 12 (estado final del directo)
#   ./sesion.sh stop        # para la sesión que esté corriendo
#   ./sesion.sh list        # qué sesiones tienen ya datos en este equipo
#
# Qué resuelve: las ramas del curso comparten UN volumen de Postgres, y saltar
# a una sesión ANTERIOR revienta (su alembic ve un esquema "del futuro"). Este
# script le da a cada sesión su propio proyecto docker (-p) → su propia BBDD,
# con su esquema y su corpus, persistente entre clases. Cambiar de sesión es
# volver a ejecutar el script; volver a una ya usada tarda segundos.
#
# Requisitos: docker, git y el .env con tus claves (raíz en sesiones 15+,
# estimator/.env en las anteriores). La PRIMERA vez en cada sesión, siembra el
# corpus que pida su guía (el script te recuerda el comando).

set -euo pipefail
cd "$(dirname "$0")"

die() { echo "✗ $*" >&2; exit 1; }

# --- subcomandos utilitarios --------------------------------------------------
if [ "${1:-}" = "stop" ]; then
    running=$(docker ps --format '{{.Label "com.docker.compose.project"}}' | grep '^aieng-' | sort -u || true)
    [ -z "$running" ] && { echo "No hay ninguna sesión corriendo."; exit 0; }
    for p in $running; do
        echo "Parando $p (los datos se conservan)…"
        docker compose -p "$p" down
    done
    exit 0
fi

if [ "${1:-}" = "list" ]; then
    echo "Sesiones con datos en este equipo (volúmenes docker):"
    docker volume ls --format '{{.Name}}' | grep -oE '^aieng-[a-z0-9]+' | sort -u | sed 's/^aieng-/  · /' || echo "  (ninguna todavía)"
    exit 0
fi

# --- resolver la rama ---------------------------------------------------------
NUM="${1:?uso: ./sesion.sh <numero> [live] | stop | list}"
LIVE="${2:-}"
SUFFIX=""; [ "$LIVE" = "live" ] && SUFFIX="_live"

# El upstream mezcla nomenclaturas (session_5 vs session_05): probamos ambas.
BRANCH=""
for cand in "session_${NUM}${SUFFIX}" "session_$(printf '%02d' "$NUM")${SUFFIX}"; do
    if git ls-remote --exit-code --heads origin "$cand" >/dev/null 2>&1; then
        BRANCH="$cand"; break
    fi
done
[ -n "$BRANCH" ] || die "no existe la rama session_${NUM}${SUFFIX} (ni con cero delante). Mira: git ls-remote --heads origin | grep session"

PROJECT="aieng-s${NUM}${SUFFIX/_live/live}"

# --- checkout seguro ----------------------------------------------------------
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    die "tienes cambios sin commitear. Guárdalos (commit o stash) antes de cambiar de sesión."
fi
echo "→ Rama: $BRANCH   Proyecto docker: $PROJECT"
git fetch origin "$BRANCH" >/dev/null
git checkout "$BRANCH" >/dev/null 2>&1 || git checkout -b "$BRANCH" "origin/$BRANCH" >/dev/null
git merge --ff-only "origin/$BRANCH" >/dev/null 2>&1 || true

# --- avisos de entorno según la época -----------------------------------------
if [ -d ai-service ]; then ENV_HINT=".env (raíz)"; ENV_FILE=".env"; else ENV_HINT="estimator/.env"; ENV_FILE="estimator/.env"; fi
if [ ! -f "$ENV_FILE" ] || ! grep -q "^OPENAI_API_KEY=..*" "$ENV_FILE" 2>/dev/null; then
    echo "⚠  Falta $ENV_HINT con OPENAI_API_KEY — la app arrancará pero el LLM fallará."
fi

# --- parar cualquier otra sesión (container_name y puertos fijos chocan) ------
for p in $(docker ps --format '{{.Label "com.docker.compose.project"}}' | grep '^aieng-' | grep -v "^${PROJECT}$" | sort -u); do
    echo "→ Parando la sesión activa ($p) para dejar sitio…"
    docker compose -p "$p" down
done

# --- levantar -----------------------------------------------------------------
echo "→ Levantando (la 1ª build de una era de dependencias tarda; después, segundos)…"
docker compose -p "$PROJECT" up -d --build

AI_CONT="estimator"; [ -d ai-service ] && AI_CONT="ai-service"
echo
echo "✔ Sesión ${NUM}${SUFFIX} arriba."
echo "   Web:      http://localhost:3000"
echo "   API IA:   http://localhost:8000/docs"
echo
echo "ℹ  Si es la PRIMERA vez en esta sesión, siembra el corpus que pida su guía, p. ej.:"
echo "   docker compose -p $PROJECT exec $AI_CONT python scripts/build_task_corpus.py --ingest"
