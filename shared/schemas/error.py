# shared/schemas/error.py
# 역할: 전 서비스 공통 에러 응답 포맷
# 관련 챕터: Chapter 3

from typing import Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str           # 기계가 읽는 에러 코드 (예: "RATE_LIMIT_EXCEEDED")
    message: str        # 사람이 읽는 설명
    field: Optional[str] = None   # 검증 에러 시 문제가 된 필드명
    trace_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: str
    timestamp: str
