FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TELEGRAM_MODE=polling \
    APP_ENV=production \
    DATABASE_URL=sqlite:///./data/maratona_coach.db \
    SHOWCASE_ENABLED=false \
    PYTHONPATH=/app

COPY requirements-jrm.txt requirements.txt
COPY pyproject-jrm.toml pyproject.toml
COPY app ./app
COPY main.py start.sh ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install --no-deps -e . && \
    mkdir -p /app/data /app/logs

EXPOSE 8000

CMD ["sh", "start.sh"]
