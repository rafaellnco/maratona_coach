FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /data

ENV DATABASE_URL=sqlite:////data/maratona_coach.db \
    APP_ENV=production \
    PORT=8000 \
    TELEGRAM_MODE=webhook

EXPOSE 8000

# webhook = FastAPI (Fly.io) | polling = 24/7 sem URL pública (hosts free)
CMD ["sh", "-c", "if [ \"$TELEGRAM_MODE\" = \"polling\" ]; then python -m app.telegram_polling; else uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi"]
