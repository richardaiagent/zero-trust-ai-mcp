# src/orchestrator/app/clients/policy_client.py
# 역할: Policy Engine HTTP 클라이언트
# 관련 챕터: Chapter 9

import httpx
from app.config import settings


class PolicyClient:

    async def check(
        self,
        user_id: str,
        role: str,
        resource: str,
        action: str,
        context: dict = None,
    ) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.policy_engine_url}/policy/check",
                json={
                    "user_id":  user_id,
                    "role":     role,
                    "resource": resource,
                    "action":   action,
                    "context":  context or {},
                },
                headers={"X-Service-Secret": settings.service_secret},
            )
            resp.raise_for_status()
            return resp.json().get("allowed", False)
