# Dar una sesión (en cualquier orden) sin sufrir — `sesion.sh`

Guía para profes del máster. El problema que resuelve: cada sesión vive en su
rama (`session_12`, `session_12_live`, ...) y el flujo natural — checkout +
`docker compose up` — funciona de maravilla **hacia delante**, pero revienta al
**saltar hacia atrás** (dar hoy la 14, la semana que viene la 12): todas las
ramas comparten UN volumen de Postgres, y el alembic de una sesión antigua se
encuentra un esquema "del futuro" que no reconoce.

## La solución en una frase

**Una base de datos por sesión.** Docker lo regala con el flag `-p` (nombre de
proyecto): con `-p aieng-s12` los volúmenes se llaman `aieng-s12_...` y cada
sesión conserva su esquema y su corpus para siempre, aislados. El script
`sesion.sh` (raíz del repo) empaqueta el ritual completo.

## Uso

```bash
./sesion.sh 12          # levanta la sesión 12 (pre-ejercicio)
./sesion.sh 12 live     # el estado final del directo de la 12
./sesion.sh 14          # cambia a la 14 (para la 12 sola, sin borrar sus datos)
./sesion.sh stop        # para lo que esté corriendo
./sesion.sh list        # qué sesiones tienen ya datos en este equipo
```

Qué hace por ti: resuelve el nombre real de la rama (el repo mezcla
`session_5` y `session_05_live` — prueba ambas), comprueba que no tienes
cambios sin commitear, hace checkout, para cualquier otra sesión que estuviera
levantada (los compose antiguos fijan `container_name` y puertos: solo puede
haber una a la vez), y levanta con su proyecto aislado. Al final imprime las
URLs y el recordatorio del corpus.

## Lo que sigue siendo cosa tuya

1. **Claves**: `.env` con `OPENAI_API_KEY` — en la raíz (sesiones 15+) o en
   `estimator/.env` (anteriores). El script avisa si falta.
2. **Corpus, la primera vez en cada sesión**: cada guía dice qué sembrar
   (típicamente `scripts/build_task_corpus.py --ingest`). Cuesta céntimos y se
   hace UNA vez por sesión — queda guardado en su volumen.
3. **La primera build de cada "era" de dependencias**: hay solo dos `uv.lock`
   distintos entre las sesiones 11 y 15, así que Docker reconstruye la capa
   pesada (torch) como mucho dos veces en tu vida; el resto de cambios de rama
   compilan en segundos. Haz la primera build el día antes, no cinco minutos
   antes de clase.

## Los tres sustos típicos y su explicación

- *"Can't locate revision …"* al arrancar → estás reutilizando el volumen
  compartido antiguo (sin `-p`). Usa el script; tu volumen viejo sigue intacto.
- *Conflicto de `container_name` o puerto ocupado* → hay otra sesión levantada.
  `./sesion.sh stop` (el script ya lo hace solo al levantar).
- *El RAG dice "sin precedentes"* → esa sesión aún no sembró su corpus (paso 2).

## La propuesta de fondo (para LIDR)

Esto es un parche de profesor; la solución de verdad sería oficial: versiones
estables por sesión — imágenes etiquetadas por rama en un registry y/o
entornos desplegados (`s12.demo...`). La infraestructura ya existe (el CI
publica imágenes por SHA; un compose autocontenido tipo
`docker-compose.vps-cloud.yml` las consume). Este script y este fork son la
prueba de concepto para esa conversación.
