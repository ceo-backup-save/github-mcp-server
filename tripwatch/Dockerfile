FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8787 \
    TRIPWATCH_HOST=0.0.0.0 \
    TRIPWATCH_DB=/data/tripwatch.db

WORKDIR /app
COPY . .

RUN mkdir -p /data \
    && useradd --create-home --uid 10001 app \
    && chown -R app:app /app /data

USER app
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/api/health', timeout=4)"

CMD ["python3", "app.py"]
