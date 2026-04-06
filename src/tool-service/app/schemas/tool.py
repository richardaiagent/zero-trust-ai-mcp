# src/tool-service/app/schemas/tool.py
# 역할: Tool 실행 요청/응답 스키마
# 관련 챕터: Chapter 3, 6

from typing import Any
from pydantic import BaseModel


class ToolExecuteRequest(BaseModel):
    user_id: str
    role: str
    parameters: dict[str, Any]
    request_id: str = ""


class ToolExecuteResponse(BaseModel):
    tool_name: str
    result: Any
    execution_time_ms: int
