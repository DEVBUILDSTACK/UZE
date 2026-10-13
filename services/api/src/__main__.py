"""Entrypoint: python -m src"""
import uvicorn

from src.api import create_app
from src.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.api:create_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
