# Build local HTTP API (in-memory store) for Docker Compose testing.
FROM golang:1.24-bookworm AS build

WORKDIR /src

COPY go.mod go.sum ./
ENV GOTOOLCHAIN=auto
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/api ./cmd/local

FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /
COPY --from=build /out/api /api

ENV PORT=8080 \
    APP_PASSWORD=dev-password \
    APP_TOKEN=dev-token \
    CORS_ORIGIN=http://localhost:5173

EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/api"]
