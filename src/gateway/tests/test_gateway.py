# src/gateway/tests/test_gateway.py
# 역할: Gateway 엔드포인트 기본 테스트
# 관련 챕터: Chapter 6

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_requires_auth():
    resp = client.post("/v1/chat", json={"session_id": "s1", "message": "hello"})
    assert resp.status_code == 403  # 토큰 없으면 거부
