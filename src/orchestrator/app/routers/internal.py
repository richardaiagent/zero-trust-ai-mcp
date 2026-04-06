# src/orchestrator/app/routers/internal.py
# 역할: /internal/v1/invoke — Gateway에서만 호출 (X-Service-Secret 필수)
# 관련 챕터: Chapter 3, 6

import logging
from fastapi import APIRouter, Depends, HTTPException
from app.middleware.service_auth import verify_service_secret
from app.core.flow import OrchestrationFlow
from app.schemas.internal import InvokeRequest, InvokeResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/v1")
_flow = OrchestrationFlow()


@router.post("/invoke", response_model=InvokeResponse)
async def invoke(
    request: InvokeRequest,
    _: None = Depends(verify_service_secret),
) -> InvokeResponse:
    logger.info("invoke | session=%s user=%s", request.session_id, request.user_id)
    try:
        result = await _flow.run(
            session_id=request.session_id,
            user_id=request.user_id,
            role=request.role,
            message=request.message,
            request_id=request.request_id,
        )
    except Exception as e:
        logger.exception("orchestration failed: %s", e)
        raise HTTPException(status_code=500, detail="오케스트레이션 처리 실패")

    return InvokeResponse(
        session_id=request.session_id,
        message=result["message"],
        sources=result.get("sources", []),
        model_used=result.get("model_used", "unknown"),
        request_id=request.request_id,
    )


@router.get("/health")
async def health():
    return {"status": "ok", "model_available": True}
