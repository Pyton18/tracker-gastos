# Spend Tracker — API (FastAPI + pipeline)
# Build: docker build -t spend-tracker-api .
# Run:  docker run -p 8000:8000 -e PORT=8000 spend-tracker-api

FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# pdfplumber / pandas wheels are fine on slim; no extra system libs required for typical PDFs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Base app config (paths, flags). Ejemplos for categorías/objetivos — session copies from these at runtime.
COPY config/ config/
COPY src/ src/
COPY mvp_web/ mvp_web/

# Writable storage for ephemeral sessions (override with TG_STORAGE_ROOT in prod)
ENV TG_STORAGE_ROOT=/data/storage
RUN mkdir -p /data/storage

EXPOSE 8000

CMD sh -c 'uvicorn mvp_web.main:app --host 0.0.0.0 --port ${PORT:-8000}'
