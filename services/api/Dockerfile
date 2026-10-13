# UZE API — monolithic FastAPI backend.
# Pattern: 2-stage python:3.12-slim + uv (from monolithic-backend analysis),
# fixed for production: non-root user, HEALTHCHECK, PORT-aware, no secrets baked.
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runner

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 10001 appuser

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY prisma ./prisma
COPY scripts/prestart.sh ./scripts/prestart.sh
RUN chmod +x ./scripts/prestart.sh \
    && chown -R appuser:appuser /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["./scripts/prestart.sh"]
