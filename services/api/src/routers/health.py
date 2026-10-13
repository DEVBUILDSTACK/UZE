"""Health endpoints — used by Docker HEALTHCHECK and Cloud Run."""
from fastapi import APIRouter

from src.config import settings
from src.db import prisma, redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME}


@router.get("/health/deep")
async def health_deep():
    db_ok = prisma.is_connected()
    redis_ok = False
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False
    return {"status": "ok" if (db_ok and redis_ok) else "degraded",
            "postgres": db_ok, "redis": redis_ok}
