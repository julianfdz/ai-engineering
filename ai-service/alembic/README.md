# ¿Qué es Alembic? (nota de apoyo para quien no viene de Python)

Alembic es la herramienta de **migraciones de esquema** del ecosistema Python —
el equivalente exacto de las migraciones de Active Record en Rails. Cada cambio
en la base de datos (una tabla nueva, una columna, un índice) es un fichero
versionado en `versions/`, con una función `upgrade()` que lo aplica y una
`downgrade()` que lo revierte, encadenados en orden. La propia base de datos
lleva la cuenta de por dónde va en una tablita llamada `alembic_version`:
al ejecutar `alembic upgrade head` ("llévame a la última"), Alembic compara y
aplica solo lo que falte — igual, en orden y una sola vez, en cualquier entorno.
En este proyecto ni siquiera hace falta lanzarlo a mano: el entrypoint del
contenedor lo ejecuta en cada arranque (`RUN_MIGRATIONS=true`).

Los ficheros de `versions/` cuentan además la historia del máster: `0001` crea
las tablas iniciales (S6), `0002` activa la extensión pgvector y crea
`documents`/`chunks` (S8, nace el RAG), `0003` añade la columna `tsvector`
para búsqueda full-text (S10, búsqueda híbrida), `0004` parte el corpus en
tres colecciones (S10, multi-índice) y `0005` construye los índices HNSW
sobre `halfvec` (S11). Leerlos en orden es leer cómo evolucionó el sistema.
