# Build from the repository root so the add-on package can be copied in:
#   docker compose -f word-inbox/docker-compose.yml up -d --build
FROM node:22-slim AS frontend
WORKDIR /src
COPY word-inbox/frontend/package.json word-inbox/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY word-inbox/frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    STATIC_DIR=/app/static
WORKDIR /app
COPY word-inbox/server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# The server imports the add-on's pure modules directly.
COPY anki_card_creator/ ./anki_card_creator/
COPY word-inbox/server/word_inbox/ ./word_inbox/
COPY --from=frontend /src/dist ./static
VOLUME ["/data"]
EXPOSE 8088
CMD ["uvicorn", "--factory", "word_inbox.app:app", "--host", "0.0.0.0", "--port", "8088"]
