"""UZE monolithic API — app factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db import close_db, init_db
from src.routers import auth, events, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_prod()
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(events.router)

    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": settings.APP_NAME, "docs": "/docs", "health": "/health"}

    return app


app = create_app()
