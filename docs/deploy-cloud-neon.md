# Variante cloud — Postgres gestionado (Neon)

Alternativa al despliegue de la Sesión 15 que saca las **dos** instancias de
Postgres del VPS y las lleva a Neon. Redis se queda como contenedor: la caché
semántica exige RediSearch (Redis Stack) y los Redis gestionados habituales no
traen ese módulo. Todo lo demás (Caddy, imágenes de GHCR, systemd, el
`X-Service-Token`) es idéntico al despliegue base.

## Qué cambia y qué no

| Pieza | Antes (S15) | Con esta variante |
|---|---|---|
| `vector-db` (pgvector, corpus, checkpointer) | contenedor | base `neondb` en Neon |
| `postgres` (Rails) | contenedor | base `estimator_web_production` en Neon |
| Redis Stack | contenedor | contenedor (sin cambios) |
| Migraciones | entrypoints (`alembic` / `db:prepare`) | idéntico — corren contra Neon |
| RAM del VPS | ~2,5–3,5 GB con picos (HNSW) | ~1,5–2,5 GB, sin picos de BBDD |

## Requisitos en Neon

Un solo proyecto con **dos databases** basta:

1. `neondb` (la que trae el proyecto) — para el servicio IA. La extensión
   pgvector la crea la migración 0002 (`CREATE EXTENSION IF NOT EXISTS vector`);
   Neon la tiene disponible (≥ 0.8, con `halfvec` y HNSW).
2. `estimator_web_production` — para Rails. Créala una vez desde el SQL editor
   de Neon: `CREATE DATABASE estimator_web_production;`

Usa el **endpoint directo** (host sin `-pooler`) en ambas URLs: los dos
servicios son procesos de larga vida con pools propios, y tanto asyncpg como el
checkpointer de LangGraph usan prepared statements que un pooler en modo
transacción puede romper. El endpoint `-pooler` solo compensa con muchas
réplicas efímeras.

## Configuración

En el `.env` (local o `/opt/estimator/.env` en el VPS):

```bash
AI_SERVICE_DATABASE_URL=postgresql+psycopg://USER:PASS@ep-xxx.region.aws.neon.tech/neondb?sslmode=require&channel_binding=require
BUSINESS_DATABASE_URL=postgresql://USER:PASS@ep-xxx.region.aws.neon.tech/estimator_web_production?sslmode=require&channel_binding=require
```

Los parámetros `sslmode` / `channel_binding` son de libpq: psycopg (sync,
Alembic, el saver de LangGraph) y el gem `pg` de Rails los leen tal cual; para
el engine async (asyncpg) el servicio los traduce en `_async_database_url`
(`sslmode`→`ssl`, `channel_binding` se descarta) — cubierto por
`tests/test_database_url.py`.

## Arranque

```bash
# Desarrollo contra Neon (sin BBDD locales)
docker compose -f docker-compose.yml -f docker-compose.cloud.yml up --build

# Producción en el VPS — el override cloud SIEMPRE el último:
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
               -f docker-compose.cloud.yml up -d
```

Para systemd, `deploy/estimator.service` trae las líneas `ExecStart`/`ExecStop`
de esta variante comentadas.

Las BBDD locales no arrancan pero sus volúmenes no se tocan; se recuperan con
`docker compose --profile local-db up postgres vector-db`.

## Llevar el corpus a Neon

`scripts/restore_corpus.sh` restaura dentro del contenedor `vector-db`, que aquí
no existe. Contra Neon, el mismo dump se restaura directo con las herramientas
cliente (vale cualquier `pg_restore` moderno):

```bash
./scripts/dump_corpus.sh /tmp/corpus.dump      # en el entorno que tiene los datos

docker run --rm -i postgres:16 pg_restore \
  -d "postgresql://USER:PASS@ep-xxx.region.aws.neon.tech/neondb?sslmode=require" \
  --clean --if-exists --no-owner < /tmp/corpus.dump
```

Igual que en el flujo S15: restaurar copia los vectores ya pagados; re-ingestar
volvería a pagar los embeddings.

## Matices operativos

- **Latencia**: crea el proyecto Neon en la misma región que el VPS — la
  búsqueda híbrida hace varias queries por petición.
- **Scale-to-zero**: el checkpointer mantiene una conexión abierta
  (`min_size=1`), así que el compute de Neon no se dormirá mientras el servicio
  esté levantado. Cuenta esas horas de compute en el plan.
- **Tuning HNSW**: los flags de `command:` del contenedor `vector-db`
  (`maintenance_work_mem`, …) no aplican en Neon; para este corpus (~23 MB) la
  construcción del índice es trivial y no se nota.
- **`RUN_MIGRATIONS`**: sin cambios — con una sola réplica déjalo en `true` y
  el entrypoint migra contra Neon al arrancar.
