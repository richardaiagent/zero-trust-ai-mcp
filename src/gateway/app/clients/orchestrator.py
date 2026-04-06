# src/gateway/app/clients/orchestrator.py
# 역할: Orchestrator 내부 HTTP 클라이언트
# 관련 챕터: Chapter 6

import httpx
from app.config import settings


class OrchestratorClient:
    _timeout = 30.0

    async def invoke(
        self,
        session_id: str,
        message: str,
        user_id: str,
        role: str,
        request_id: str,
    ) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{settings.orchestrator_url}/internal/v1/invoke",
                json={
                    "session_id": session_id,
                    "message":    message,
                    "user_id":    user_id,
                    "role":       role,
                    "request_id": request_id,
                },
                headers={"X-Service-Secret": settings.service_secret},
            )
            resp.raise_for_status()
            return resp.json()

    async def stream(self, session_id: str, message: str, user_id: str, role: str, request_id: str):
        """SSE 스트리밍 응답 제너레이터"""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                f"{settings.orchestrator_url}/internal/v1/stream",
                json={
                    "session_id": session_id,
                    "message":    message,
                    "user_id":    user_id,
                    "role":       role,
                    "request_id": request_id,
                },
                headers={"X-Service-Secret": settings.service_secret},
            ) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk
