from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_auth_disabled_when_no_key_configured():
    assert client.get("/api/tickers").status_code == 200


def test_rejects_missing_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    assert client.get("/api/tickers").status_code == 401


def test_rejects_wrong_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    assert client.get("/api/tickers", headers={"X-API-Key": "nope"}).status_code == 401


def test_accepts_correct_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret123")
    assert client.get("/api/tickers", headers={"X-API-Key": "secret123"}).status_code == 200


def test_chat_is_rate_limited():
    for _ in range(4):
        assert client.post("/api/chat", json={"question": "hi"}).status_code == 422
    r = client.post("/api/chat", json={"question": "hi"})
    assert r.status_code == 429
    assert "retry-after" in r.headers