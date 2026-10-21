# ── Stage 1: Build Frontend SPA ──────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder
WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python Backend & Gunicorn Server ────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PORT=7860 \
  HOST=0.0.0.0

# Install runtime dependencies for LightGBM and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libgomp1 \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create user with UID 1000 (standard for Hugging Face Spaces)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
  PATH=/home/user/.local/bin:$PATH

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository code
COPY . .
RUN pip install --no-cache-dir -e .

# Copy compiled frontend assets from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

# Give ownership to non-root user
RUN chown -R user:user /app
USER user

EXPOSE 10000 7860 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:${PORT:-10000}/api/health || exit 1

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 2 --timeout 120 backend.app:app"]
