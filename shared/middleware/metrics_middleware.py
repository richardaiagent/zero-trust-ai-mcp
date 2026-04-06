# shared/middleware/metrics_middleware.py
# 역할: FastAPI 요청/응답 자동 메트릭 계측 미들웨어
# 관련 챕터: Chapter 13

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from shared.metrics import REQUEST_COUNT, REQUEST_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service = service_name

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - start

        REQUEST_COUNT.labels(
            service=self.service,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            service=self.service,
            endpoint=request.url.path,
        ).observe(elapsed)

        return response
