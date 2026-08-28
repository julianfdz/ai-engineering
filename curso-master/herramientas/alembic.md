# Alembic — migraciones de esquema en Python

## Qué es

Alembic es la herramienta de **migraciones de base de datos** del ecosistema
Python/SQLAlchemy — el equivalente exacto de las migraciones de Active Record
en Rails. Resuelve este problema: el esquema de una base de datos evoluciona
(hoy una tabla nueva, mañana una columna, pasado un índice) y esos cambios
tienen que aplicarse **igual, en orden y una sola vez** en cada entorno — tu
portátil, el contenedor, la nube.

## Cómo funciona

Cada cambio es un fichero Python versionado en git, con dos funciones:
`upgrade()` (aplicar el cambio) y `downgrade()` (revertirlo). Los ficheros se
encadenan en una lista ordenada. La propia base de datos lleva la cuenta de
por dónde va en una tabla mínima llamada `alembic_version` (una sola fila con
el id de la última migración aplicada). El comando clave:

```bash
alembic upgrade head   # "llévame a la última versión"
```

Alembic compara el marcador de la base con la cadena de ficheros y ejecuta
solo lo que falte. Si no falta nada, no hace nada — es idempotente.

## Dónde verlo en el proyecto

- Los ficheros viven en `ai-service/alembic/versions/`. Leídos en orden
  cuentan la historia del máster: `0001` tablas iniciales (S6), `0002`
  extensión pgvector + `documents`/`chunks` (S8, nace el RAG), `0003` columna
  `tsvector` para full-text (S10, búsqueda híbrida), `0004` las tres
  colecciones (S10, multi-índice), `0005` índices HNSW sobre `halfvec` (S11).
- Nadie lo lanza a mano: el entrypoint del contenedor (`docker-entrypoint.sh`)
  ejecuta `alembic upgrade head` en cada arranque (togglable con
  `RUN_MIGRATIONS`). Por eso una base recién creada aparece con todas las
  tablas "sola".
- La simetría con Rails: el business-backend hace lo mismo con Active Record —
  `db/migrate/` + tabla `schema_migrations` + `db:prepare` en su entrypoint.
  Cada servicio migra la base de la que es dueño, con la herramienta de su
  ecosistema.

Más contexto sobre las dos bases de datos: `docs/infra-bbdd.md`.
