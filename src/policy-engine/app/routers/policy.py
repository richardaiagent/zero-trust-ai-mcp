# src/policy-engine/app/routers/policy.py
# 역할: /policy/check — OPA 서버에 Rego 정책 평가 위임
# 관련 챕터: Chapter 9

import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.policy import PolicyCheckRequest, PolicyCheckResponse
from app.middleware.service_auth import verify_service_secret
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/check", response_model=PolicyCheckResponse)
async def check_policy(
    request: PolicyCheckRequest,
    _: None = Depends(verify_service_secret),
) -> PolicyCheckResponse:
    # OPA 서버에 정책 평가 요청 (Zero Trust: 결정론적 규칙 기반)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.opa_url}/v1/data/mcp/authz/allow",
                json={
                    "input": {
                        "user_id":  request.user_id,
                        "role":     request.role,
                        "resource": request.resource,
                        "action":   request.action,
                        "context":  request.context,
                    }
                },
            )
            response.raise_for_status()
            result = response.json()
            allowed = result.get("result", False)

    except httpx.TimeoutException:
        # OPA 타임아웃 → fail-closed (거부)
        logger.error("OPA timeout — denying request for safety")
        allowed = False
    except Exception as e:
        logger.error("OPA error: %s — denying request for safety", e)
        allowed = False

    logger.info(
        "policy check | user=%s role=%s resource=%s allowed=%s",
        request.user_id, request.role, request.resource, allowed,
    )

    return PolicyCheckResponse(
        allowed=allowed,
        reason="allowed" if allowed else "policy_denied",
    )
