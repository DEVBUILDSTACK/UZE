"""UZE API settings — single source of truth for env.

Canonical names (do not invent variants):
  DATABASE_URL   Neon Postgres pooled connection string (required)
  DIRECT_URL     Neon direct connection string for migrations (required in prod)
  REDIS_URL      Redis connection string, e.g. redis://redis:6379/0 (required)
  SECRET_KEY     HS256 JWT signing key (required in prod)
  PORT           HTTP port (default 8000; Cloud Run injects 8080)
  APP_NAME       Service name for logs/health
  DEBUG          true/false — never gates destructive actions
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "uze-api"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = ""  # required in prod; fail fast below
    DIRECT_URL: str = ""    # required in prod for prisma migrate
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "dev-only-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # RAG embeddings (OpenAI-compatible API; key stays in Secret Manager)
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Resend (transactional email: OTP login codes, UZEMARKET outreach)
    RESEND_API_KEY: str = ""
    RESEND_SENDER_EMAIL: str = ""
    RESEND_SENDER_NAME: str = "UZEMARKET"

    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    def validate_prod(self) -> None:
        """Fail fast on missing production config. Called at startup."""
        missing = [
            name for name in ("DATABASE_URL", "DIRECT_URL")
            if not getattr(self, name)
        ]
        if not self.DEBUG and missing:
            raise RuntimeError(
                f"Missing required env vars: {', '.join(missing)}. "
                "See .env.example."
            )
        if not self.DEBUG and self.SECRET_KEY == "dev-only-change-me":
            raise RuntimeError("SECRET_KEY must be set in production.")


settings = Settings()
