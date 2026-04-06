# src/audit-service/app/anomaly/detector.py
# Chapter 10: 행동 기반 이상탐지

import json
import logging
from datetime import datetime

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Redis에 누적된 사용자 행동 지표를 분석해서 이상 여부를 판단한다.
    탐지 기준 (Chapter 10):
      - 시간당 요청 100건 초과
      - 정책 거부율 30% 초과
      - 업무 시간 외(22시~06시) 고빈도 접근
    """

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.req_threshold     = settings.anomaly_requests_per_hour_threshold
        self.denied_threshold  = settings.anomaly_policy_denied_ratio_threshold
        self.off_start         = settings.anomaly_off_hours_start
        self.off_end           = settings.anomaly_off_hours_end

    async def record_event(self, user_id: str, event_type: str, detail: dict) -> None:
        pipe = self.redis.pipeline()
        hour_key    = f"anomaly:{user_id}:req_hour"
        denied_key  = f"anomaly:{user_id}:denied_total"
        total_key   = f"anomaly:{user_id}:total"

        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        pipe.incr(total_key)

        if event_type == "policy_decision" and not detail.get("allowed", True):
            pipe.incr(denied_key)

        await pipe.execute()

    async def analyze(self, user_id: str) -> dict:
        """이상 점수 계산 후 결과 반환"""
        hour_key   = f"anomaly:{user_id}:req_hour"
        denied_key = f"anomaly:{user_id}:denied_total"
        total_key  = f"anomaly:{user_id}:total"

        req_hour, denied, total = await self.redis.mget(hour_key, denied_key, total_key)

        req_hour = int(req_hour or 0)
        denied   = int(denied or 0)
        total    = int(total or 1)

        denied_ratio = denied / total
        current_hour = datetime.utcnow().hour
        off_hours    = (current_hour >= self.off_start or current_hour < self.off_end)

        anomalies = []
        if req_hour > self.req_threshold:
            anomalies.append(f"high_request_rate:{req_hour}/hour")
        if denied_ratio > self.denied_threshold:
            anomalies.append(f"high_denial_ratio:{denied_ratio:.2f}")
        if off_hours and req_hour > self.req_threshold // 2:
            anomalies.append(f"off_hours_access:hour={current_hour}")

        is_anomaly = len(anomalies) > 0
        if is_anomaly:
            logger.warning("anomaly_detected user=%s reasons=%s", user_id, anomalies)

        return {
            "is_anomaly":    is_anomaly,
            "anomalies":     anomalies,
            "req_per_hour":  req_hour,
            "denied_ratio":  denied_ratio,
        }
