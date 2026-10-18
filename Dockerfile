# syntax=docker/dockerfile:1
# One image for Railway: the FastAPI server, which also serves the built web
# app from the same origin (see app/core/frontend.py).

# ---- 1. Build the web app (web/dist) ----
FROM node:24-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# Empty base URL: the app calls /api on the same origin it was loaded from.
ENV VITE_API_BASE_URL=""
RUN npm run build

# ---- 2. API server ----
FROM python:3.14-slim AS app
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /srv

# Dependencies first, so code changes don't reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY --from=web /web/dist ./static

# Production by default: the server refuses to start without a real
# HACCP_JWT_SECRET_KEY. Uploads go to /data/uploads (mount a volume at /data)
# when HACCP_STORAGE_BACKEND=local.
ENV PATH="/srv/.venv/bin:$PATH" \
    HACCP_ENVIRONMENT=production \
    HACCP_FRONTEND_DIST_DIR=/srv/static \
    HACCP_LOCAL_STORAGE_DIR=/data/uploads

EXPOSE 8000
# Bring the database up to date, then serve. Migrations are idempotent, so
# running them on every start is safe, and it doesn't depend on the host
# honouring a separate pre-deploy step. If they fail, the server never starts
# and the previous deploy keeps serving. Railway sets $PORT and terminates HTTPS.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
