# UZE Web — Next.js frontend.
# Pattern lifted from Fundio's Dockerfile (3-stage node:20-alpine, DOCKER=true
# standalone gate), fixed for Cloud Run:
#   - PORT 8080 (Cloud Run default) instead of hardcoded 3000
#   - HEALTHCHECK added (Fundio lacks it)
#   - non-root USER added (Fundio lacks it)
#   - NO secret build args — secrets come from Secret Manager at runtime.
#     Only non-secret NEXT_PUBLIC_* config may be passed as build args.
FROM node:20-alpine AS deps
RUN apk add --no-cache python3 make g++
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Non-secret public config only. Never add API keys here — they land in image layers.
ARG NEXT_PUBLIC_BASE_URL=""
ARG NEXT_PUBLIC_API_BASE_URL=""
ENV NEXT_PUBLIC_BASE_URL=${NEXT_PUBLIC_BASE_URL} \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    DOCKER=true \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

RUN corepack enable pnpm && \
    NODE_OPTIONS="--max-old-space-size=4096" pnpm run build

FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=8080
USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:${PORT:-8080}/api/health || exit 1

CMD ["node", "server.js"]
