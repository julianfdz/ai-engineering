# ── Julián · Sesión 2 · Tests · el servicio responde ──────────────────────────────
#
#   GET /health devuelve 200 y status=healthy.
# ──────────────────────────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
