"""Prisma client + Redis lifecycle for the UZE API."""
from prisma import Prisma
from redis import asyncio as aioredis

from src.config import settings

prisma = Prisma()
redis_client: aioredis.Redis | None = None


async def init_db() -> None:
    global redis_client
    await prisma.connect()
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_db() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
    if prisma.is_connected():
        await prisma.disconnect()
