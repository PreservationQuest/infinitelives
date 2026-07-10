from fastapi.testclient import TestClient

from game_evidence_graph.api.server import create_app


def test_health():
    client = TestClient(create_app())
    assert client.get("/health").json() == {"status": "ok"}
