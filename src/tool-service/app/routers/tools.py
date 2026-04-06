# src/tool-service/app/routers/tools.py
# 역할: GET /tools, POST /tools/{tool_name}/execute
# 관련 챕터: Chapter 3, 6

import time
import logging
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Body

from app.middleware.service_auth import verify_service_secret
from app.registry import get_tools_for_role
from app.executor import ToolExecutor
from app.schemas.tool import ToolExecuteRequest, ToolExecuteResponse
from shared.metrics import TOOL_EXEC_COUNT, TOOL_ERROR_COUNT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools")
_executor = ToolExecutor()


@router.get("")
async def list_tools(
    x_user_role: str = Header(...),
    _: None = Depends(verify_service_secret),
) -> dict:
    return {"tools": get_tools_for_role(x_user_role)}


@router.post("/{tool_name}/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    tool_name: str = Path(...),
    request: ToolExecuteRequest = Body(...),
    _: None = Depends(verify_service_secret),
) -> ToolExecuteResponse:
    logger.info("tool execute | name=%s user=%s", tool_name, request.user_id)
    start = time.monotonic()

    try:
        result = await _executor.run(tool_name, request.parameters)
        TOOL_EXEC_COUNT.labels(tool_name=tool_name).inc()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        TOOL_ERROR_COUNT.labels(tool_name=tool_name).inc()
        logger.error("tool error | name=%s err=%s", tool_name, e)
        raise HTTPException(status_code=500, detail=f"Tool 실행 실패: {e}")

    elapsed_ms = int((time.monotonic() - start) * 1000)
    return ToolExecuteResponse(tool_name=tool_name, result=result, execution_time_ms=elapsed_ms)
