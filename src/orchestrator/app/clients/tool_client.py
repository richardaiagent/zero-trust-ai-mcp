# src/orchestrator/app/clients/tool_client.py
# 역할: Tool Server HTTP 클라이언트
# 관련 챕터: Chapter 4, 6

import httpx
from app.config import settings


class ToolClient:

    async def list(self, role: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.tool_server_url}/tools",
                headers={
                    "X-Service-Secret": settings.service_secret,
                    "X-User-Role": role,
                },
            )
            resp.raise_for_status()
            return resp.json().get("tools", [])

    async def execute(self, tool_name: str, parameters: dict, user_id: str, role: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.tool_server_url}/tools/{tool_name}/execute",
                json={"user_id": user_id, "role": role, "parameters": parameters},
                headers={"X-Service-Secret": settings.service_secret},
            )
            resp.raise_for_status()
            return resp.json()
