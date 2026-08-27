"""The asyncpg URL derived from ``DATABASE_URL`` must survive managed-Postgres
query params.

Neon (and most managed Postgres) hand out URLs with ``sslmode=require`` and
``channel_binding=require``. psycopg reads both natively; asyncpg's ``connect()``
has neither kwarg, so ``_async_database_url`` must translate ``sslmode`` into
asyncpg's ``ssl`` and drop ``channel_binding`` — otherwise the async engine dies
on first connect with ``TypeError: unexpected keyword argument 'sslmode'``.
"""

from app.foundation.persistence import database


def _with_url(monkeypatch, url: str) -> str:
    class _Settings:
        DATABASE_URL = url

    monkeypatch.setattr(database, "get_settings", lambda: _Settings())
    return database._async_database_url()


def test_swaps_psycopg_driver_token(monkeypatch):
    result = _with_url(monkeypatch, "postgresql+psycopg://u:p@localhost:5433/estimator")
    assert result == "postgresql+asyncpg://u:p@localhost:5433/estimator"


def test_plain_postgresql_url_gains_asyncpg_driver(monkeypatch):
    result = _with_url(monkeypatch, "postgresql://u:p@localhost/estimator")
    assert result == "postgresql+asyncpg://u:p@localhost/estimator"


def test_neon_style_ssl_params_are_translated(monkeypatch):
    result = _with_url(
        monkeypatch,
        "postgresql+psycopg://u:p@ep-x.eu-west-2.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require",
    )
    assert result == "postgresql+asyncpg://u:p@ep-x.eu-west-2.aws.neon.tech/neondb?ssl=require"


def test_unrelated_query_params_survive(monkeypatch):
    result = _with_url(
        monkeypatch,
        "postgresql://u:p@host/db?application_name=estimator&sslmode=verify-full",
    )
    assert result == ("postgresql+asyncpg://u:p@host/db?application_name=estimator&ssl=verify-full")


def test_non_postgres_urls_pass_through(monkeypatch):
    assert _with_url(monkeypatch, "sqlite:///./test.db") == "sqlite:///./test.db"
