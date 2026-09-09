FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8787

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY frontend ./frontend

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8787

CMD ["sh", "-c", "uvicorn stateguard.app:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8787}"]
