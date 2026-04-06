# src/audit-service/app/subscriber.py
# Chapter 4: Redis Pub/Sub 감사 이벤트 구독자

import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.schemas.audit import AuditEvent, AuditEventType
from app.anomaly.detector import AnomalyDetector

logger = logging.getLogger(__name__)

AUDIT_CHANNEL = "mcp:audit:events"


async def run_subscriber(redis: aioredis.Redis) -> None:
    """
    Redis Pub/Sub 채널을 구독하고 이벤트를 처리한다.
    백그라운드 태스크로 실행된다.
    """
    detector = AnomalyDetector(redis)
    pubsub   = redis.pubsub()
    await pubsub.subscribe(AUDIT_CHANNEL)
    logger.info("audit subscriber started channel=%s", AUDIT_CHANNEL)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data  = json.loads(message["data"])
            event = AuditEvent(**data)
            await _handle_event(event, detector)
        except Exception as exc:
            logger.error("audit event processing failed: %s", exc)


async def _handle_event(event: AuditEvent, detector: AnomalyDetector) -> None:
    logger.info(
        "audit event_type=%s session=%s user=%s trace=%s",
        event.event_type, event.session_id, event.user_id, event.trace_id,
    )

    # 행동 지표 누적
    await detector.record_event(event.user_id, event.event_type, event.detail)

    # 이상 탐지가 의미 있는 이벤트 타입에만 분석 수행
    if event.event_type in (
        AuditEventType.policy_decision,
        AuditEventType.request_received,
    ):
        result = await detector.analyze(event.user_id)
        if result["is_anomaly"]:
            logger.warning(
                "ANOMALY_DETECTED user=%s anomalies=%s",
                event.user_id, result["anomalies"],
            )
