# src/context-service/app/routers/context.py
# 역할: /context/{session_id} — GET(조회) / POST /turn(저장) / DELETE(삭제)
# 관련 챕터: Chapter 2, 6

from fastapi import APIRouter, Depends, Request, HTTPException
from app.schemas.context import ContextResponse, TurnRequest
from app.context_manager import ContextManager
from app.config import settings

router = APIRouter(prefix="/context")


def get_manager(request: Request) -> ContextManager:
    return ContextManager(request.app.state.redis)


@router.get("/{session_id}", response_model=ContextResponse)
async def get_context(
    session_id: str,
    user_id: str = "",
    manager: ContextManager = Depends(get_manager),
) -> ContextResponse:
    try:
        ctx = await manager.build_context(session_id, user_id)
        return ContextResponse(**ctx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨텍스트 조회 실패: {e}")


@router.post("/{session_id}/turn", status_code=204)
async def save_turn(
    session_id: str,
    body: TurnRequest,
    manager: ContextManager = Depends(get_manager),
) -> None:
    try:
        await manager.save_turn(session_id, body.user, body.assistant)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨텍스트 저장 실패: {e}")


@router.delete("/{session_id}", status_code=204)
async def delete_context(
    session_id: str,
    manager: ContextManager = Depends(get_manager),
) -> None:
    await manager.delete_session(session_id)
