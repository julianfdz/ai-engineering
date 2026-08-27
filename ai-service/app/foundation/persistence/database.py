"""SQLAlchemy engines, session factories and per-request session helpers.

Two stacks coexist on purpose:

* **Sync (psycopg)** — the Session 6 ingestion paths. They are not on the hot
  user request path (BackgroundTasks / one-shot admin operations), so we trade
  async ergonomics for simplicity and less moving infrastructure during
  teaching.
* **Async (asyncpg)** — the Session 8 RAG store (``POST /embeddings/ingest``
  and ``POST /search``). Those endpoints ARE on the real-time request path, so
  they use the async engine and never block the event loop on Postgres I/O.

Both engines read the same ``Settings.DATABASE_URL``; the async one swaps the
driver token, so a single env var configures the whole service.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def create_engine_from_settings() -> Engine:
    """Build the global engine from ``Settings.DATABASE_URL`` (singleton)."""
    return create_engine(
        get_settings().DATABASE_URL,
        pool_pre_ping=True,
        future=True,
    )


SessionLocal = sessionmaker(
    bind=create_engine_from_settings(),
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a Session and closes it on exit."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _translate_libpq_ssl_params(url: str) -> str:
    """Rewrite libpq-only SSL query params into what asyncpg understands.

    Managed Postgres (Neon, RDS, …) hands out URLs carrying ``sslmode`` and
    ``channel_binding``. psycopg (sync engine, Alembic, the LangGraph saver)
    reads them natively, but asyncpg's ``connect()`` has no such kwargs and
    SQLAlchemy passes query params through verbatim — the engine would die with
    ``TypeError: unexpected keyword argument 'sslmode'``. asyncpg's equivalent
    of ``sslmode`` is ``ssl`` (same value vocabulary); ``channel_binding`` has
    no equivalent and is dropped.
    """
    parts = urlsplit(url)
    if not parts.query:
        return url
    params = [
        ("ssl", value) if key == "sslmode" else (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key != "channel_binding"
    ]
    return urlunsplit(parts._replace(query=urlencode(params)))


def _async_database_url() -> str:
    """Derive the asyncpg URL from ``Settings.DATABASE_URL``.

    The canonical URL uses the sync driver (``postgresql+psycopg://``) because
    Alembic and the Session 6 repositories run synchronously. The RAG store
    swaps the driver token instead of introducing a second env var.
    """
    url = get_settings().DATABASE_URL
    if "+psycopg" in url:
        return _translate_libpq_ssl_params(url.replace("+psycopg", "+asyncpg"))
    if url.startswith("postgresql://"):
        return _translate_libpq_ssl_params(url.replace("postgresql://", "postgresql+asyncpg://", 1))
    return url


@lru_cache
def create_async_engine_from_settings() -> AsyncEngine:
    """Build the global async engine for the RAG store (singleton)."""
    return create_async_engine(
        _async_database_url(),
        pool_pre_ping=True,
    )


@lru_cache
def get_async_session_factory() -> async_sessionmaker:
    """Session factory for the async stack. ``expire_on_commit=False`` so ORM
    objects (e.g. the freshly persisted document id) stay readable after the
    transaction commits."""
    return async_sessionmaker(
        bind=create_async_engine_from_settings(),
        autoflush=False,
        expire_on_commit=False,
    )
