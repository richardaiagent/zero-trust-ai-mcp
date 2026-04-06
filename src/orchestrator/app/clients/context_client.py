# src/orchestrator/app/clients/context_client.py
# 역할: Context Service HTTP 클라이언트
# 관련 챕터: Chapter 6

import httpx
from app.config import settings


class ContextClient:

    async def get(self, session_id: str, user_id: str) -> dict:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.context_service_url}/context/{session_id}",
                params={"user_id": user_id},
                headers={"X-Service-Secret": settings.service_secret},
            )
            if resp.status_code == 404:
                return {"conversation_history": [], "user_role": None}
            resp.raise_for_status()
            return resp.json()

    async def save_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.context_service_url}/context/{session_id}/turn",
                json={"user": user_msg, "assistant": assistant_msg},
                headers={"X-Service-Secret": settings.service_secret},
            )
