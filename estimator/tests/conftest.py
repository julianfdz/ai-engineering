# ── Julián · Sesión 2 · Tests · el cliente de pruebas ─────────────────────────────
#
#   TestClient llama a la app en memoria: sin Docker, sin puerto y sin red.
# ──────────────────────────────────────────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI test client configured with the application."""
    return TestClient(app)
