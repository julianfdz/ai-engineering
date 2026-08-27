# Despliegue VPS + Neon — `docker-compose.vps-cloud.yml`

Variante de despliegue en un **fichero compose único y autocontenido** (no se
apila sobre `docker-compose.yml`): las imágenes se construyen en la propia
máquina, las dos bases de datos viven en Neon, Redis Stack se queda como
contenedor (la caché semántica exige RediSearch, que los Redis gestionados
habituales no traen) y el TLS lo termina el reverse proxy que ya corre en el
host. Sin CI, sin registry, sin Caddy propio — pensado para operarse desde
Portainer.

## Qué cambia respecto al despliegue de la S15 (`prod`)

| Pieza | S15 (EC2 + CI) | Esta variante |
|---|---|---|
| Imágenes | CI las publica en GHCR, la instancia hace `pull` | se **construyen** en el VPS |
| `vector-db` / `postgres` | contenedores | bases en **Neon** |
| Caddy | contenedor del stack | el **proxy del host** (red externa) |
| Variables | `.env` en `/opt/estimator` | env vars del stack de Portainer |
| Migraciones | entrypoints | idéntico — corren contra Neon |

## Requisitos en Neon

Un solo proyecto con dos databases:

1. `neondb` — servicio IA. pgvector (≥ 0.8, con `halfvec` y HNSW) lo crea la
   migración 0002.
2. `estimator_web_production` — Rails (`CREATE DATABASE estimator_web_production;`
   desde el SQL editor si no existe).

Usa el **endpoint directo** (host sin `-pooler`): los servicios mantienen pools
de larga vida y tanto asyncpg como el checkpointer de LangGraph usan prepared
statements que un pooler en modo transacción puede romper. Los parámetros
`sslmode`/`channel_binding` de las URLs los leen psycopg y el gem `pg` tal
cual; para asyncpg el servicio los traduce en `_async_database_url`
(`sslmode`→`ssl`, `channel_binding` fuera — pinned por
`tests/test_database_url.py`).

## Red del proxy del host

Solo `business-backend` se une a la red externa del proxy (`intrabuhonet` en el
compose; cámbiala si tu red se llama distinto). El servicio IA y Redis quedan
en la red interna del stack — la frontera de siempre. En el Caddyfile del host:

```
estimator.tu-dominio.com {
    encode gzip zstd
    reverse_proxy business-backend:3000
}
```

`APP_DOMAIN` debe ser ese mismo dominio (Rails lo exige en
`RAILS_ALLOWED_HOSTS`; si no cuadra, 403 a todo con `/up` verde).

## Despliegue con Portainer

Stack tipo **Repository**: URL del fork, compose path
`docker-compose.vps-cloud.yml`, y en *Environment variables* las variables del
`.env` de despliegue (no hay `env_file`: el `.env` está gitignorado y no existe
en el clon). Obligatorias: `OPENAI_API_KEY`, `APP_DOMAIN`, `SECRET_KEY_BASE`,
`AI_SERVICE_DATABASE_URL`, `BUSINESS_DATABASE_URL`; recomendadas:
`AI_SERVICE_TOKEN`, `RETRIEVAL_API_KEY`, `ESTIMATE_API_KEY`.

A mano, lo mismo es:

```bash
docker compose -f docker-compose.vps-cloud.yml up -d --build
```

La primera build del servicio IA es pesada (torch): disco y, si la RAM anda
justa, swap. Al primer arranque los entrypoints migran contra Neon
(`RUN_MIGRATIONS=true`).

**Torch CPU-only (solo esta variante).** Este compose pasa el build-arg
`TORCH_CPU_ONLY=true` al Dockerfile del servicio IA: tras el `uv sync`, el
builder sustituye el wheel de torch que fija el lockfile (que arrastra el
runtime CUDA de NVIDIA, varios GB) por el wheel CPU de la MISMA versión desde
`download.pytorch.org/whl/cpu`, y desinstala `nvidia-*`/`triton`. El
comportamiento es idéntico — torch solo existe para el reranker de la S10, que
corre en CPU, y en el VPS no hay GPU — y la imagen queda aproximadamente a la
mitad. El arg por defecto es `false`, así que CI, el flujo EC2 de la S15 y
cualquier otra build siguen bit a bit como antes; `pyproject.toml` y `uv.lock`
no se tocan, de modo que sincronizar con el upstream nunca conflictúa por esto.

## Llevar el corpus a Neon

El mismo dump de `scripts/dump_corpus.sh` se restaura directo contra Neon:

```bash
docker run --rm -i postgres:16 pg_restore \
  -d "postgresql://USER:PASS@ep-xxx.region.aws.neon.tech/neondb?sslmode=require" \
  --clean --if-exists --no-owner < /tmp/corpus.dump
```

Restaurar copia los vectores ya pagados; re-ingestar volvería a pagar los
embeddings.

## Matices operativos

- **Latencia**: proyecto Neon en la misma región que el VPS — la búsqueda
  híbrida hace varias queries por petición.
- **Scale-to-zero**: el checkpointer mantiene una conexión abierta
  (`min_size=1`); el compute de Neon no se dormirá con el servicio levantado.
- **Tuning HNSW**: los flags que el compose base pasa a `vector-db`
  (`maintenance_work_mem`, …) no aplican en Neon; con el corpus de ~23 MB la
  construcción del índice es trivial.
- **RAM del VPS**: sin bases de datos quedan ~1,5–2,5 GB de servicios
  (el grueso, el servicio IA con torch), sin los picos de las builds de HNSW.
