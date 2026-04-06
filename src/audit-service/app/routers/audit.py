# src/audit-service/app/routers/audit.py
# Chapter 6: 감사 로그 조회 API

from fastapi import APIRouter, Request, HTTPException, Header
from app.config import settings

router = APIRouter(prefix="/audit")


def _verify_service(x_service_secret: str = Header(...)):
    if x_service_secret != settings.service_secret:
        raise HTTPException(status_code=403, detail="Invalid service secret")


@router.get("/anomaly/{user_id}")
async def get_anomaly_status(
    user_id: str,
    request: Request,
    x_service_secret: str = Header(...),
) -> dict:
    _verify_service(x_service_secret)
    redis = request.app.state.redis

    hour_key  = f"anomaly:{user_id}:req_hour"
    total_key = f"anomaly:{user_id}:total"
    denied_key = f"anomaly:{user_id}:denied_total"

    req_hour, total, denied = await redis.mget(hour_key, total_key, denied_key)

    total  = int(total or 1)
    denied = int(denied or 0)

    return {
        "user_id":       user_id,
        "req_per_hour":  int(req_hour or 0),
        "denied_ratio":  denied / total,
        "total_requests": total,
    }
