"""Health endpoints — used by Docker HEALTHCHECK and Cloud Run."""
from fastapi import APIRouter

from src.config import settings
from src.db import prisma, redis_client
from src.schemas import APIResponse, ok

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse[dict])
async def health():
    return ok({"service": settings.APP_NAME})


@router.get("/health/deep", response_model=APIResponse[dict])
async def health_deep():
    db_ok = prisma.is_connected()
    redis_ok = False
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False
    data = {"postgres": db_ok, "redis": redis_ok}
    resp = ok(data)
    if not (db_ok and redis_ok):
        resp.status_code = 503
        resp.message = "degraded"
    return resp
