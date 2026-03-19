# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# System deps: ffmpeg for rendering, curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in a dedicated layer for cache efficiency
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose FastAPI default port
EXPOSE 8000

# Readiness check: probe /health/ready every 30s, 3 retries, 10s timeout
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1

# Default: run Uvicorn with 2 workers. Override in docker-compose or k8s.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
