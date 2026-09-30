# Word Inbox

Personal vocabulary capture app: note `{ input, type }` items behind a shared
password, store them on S3 via a Go Lambda API. Anki sync is a later phase.

```
word-inbox/
  backend/     Go Lambda + local HTTP server
  frontend/    Vite + React + TypeScript SPA
  infra/       Terraform (S3, Lambda, HTTP API, CloudFront)
  scripts/     deploy.sh
  localstack/  S3 bucket init hook for docker compose
  docker-compose.yml  local S3 (LocalStack)
```

## Quick local run

Docker only runs a local S3 (LocalStack). The backend and frontend run on the host.

### 1. Local S3 (Docker)

```bash
cd word-inbox
docker compose up -d
# S3 endpoint: http://localhost:4567, bucket word-inbox-local (created on startup)
```

Data persists in the `s3-data` volume (`docker compose down -v` wipes it).
To change the bucket name or host port, copy `.env.docker.example` to `.env`
in `word-inbox/`. If you do, export the same `S3_BUCKET` / `S3_PORT` before
running `make run-s3`.

Inspect the stored data:

```bash
docker compose exec s3 awslocal s3 ls s3://word-inbox-local/
```

### 2. Backend (Go on the host)

```bash
cd word-inbox/backend
make run-s3      # uses the local S3 above
# or
make run-local   # in-memory store, no Docker needed
# listens on :8080; defaults: APP_PASSWORD=dev-password, APP_TOKEN=dev-token
```

`cmd/local` uses the S3 store when `S3_BUCKET` is set (`S3_ENDPOINT`
overrides the AWS endpoint), otherwise the in-memory store.

### 3. Frontend (always on the host)

```bash
cd word-inbox/frontend
cp .env.example .env.development   # already points at http://localhost:8080
npm install
npm run dev
```

Open http://localhost:5173 and sign in with `dev-password`.

## API

| Method | Path | Auth | Body |
| --- | --- | --- | --- |
| `POST` | `/login` | no | `{ "password": "..." }` → `{ "token": "..." }` |
| `GET` | `/words` | Bearer | → `{ "words": [...] }` |
| `POST` | `/words` | Bearer | `{ "input": "...", "type": "normal" }` |
| `DELETE` | `/words/{id}` | Bearer | — |

Allowed `type` values: `normal`, `word_form`, `word_pattern`, `sentence`, `vietnamese`.

Each stored word:

```json
{
  "id": "uuid",
  "input": "test",
  "type": "normal",
  "createdAt": "2026-09-28T06:00:00Z",
  "syncedAt": null
}
```

## Backend tests / Lambda zip

```bash
cd word-inbox/backend
go test ./...
make zip-lambda   # writes function.zip (handler binary name: bootstrap)
```

## Deploy (Terraform)

Provisions: data S3, Lambda (`provided.al2023`), HTTP API, frontend S3 + CloudFront (default `*.cloudfront.net` / `*.execute-api` domains — no custom domain).

### Prerequisites

- Terraform >= 1.5, AWS CLI credentials with rights to create the resources above
- Go, make, npm, python3 (for packaging / SPA build)

### Configure secrets

```bash
cd word-inbox/infra
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars — set app_password and app_token (never commit this file)
```

### One-shot deploy

From `word-inbox/`:

```bash
./scripts/deploy.sh
# or non-interactive:
./scripts/deploy.sh -- -auto-approve
```

This will:

1. Build `backend/function.zip`
2. `terraform apply` in `infra/`
3. Build the SPA with `VITE_API_BASE_URL` from `api_url`
4. Sync `frontend/dist/` to the frontend bucket
5. Invalidate CloudFront `/*`

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--apply-only` | Terraform only (skip SPA sync) |
| `--skip-apply` | Reuse existing stack; rebuild/sync SPA only |
| `-- …` | Extra args passed to `terraform apply` (e.g. `-auto-approve`) |

### Outputs

After apply:

```bash
cd word-inbox/infra
terraform output
# api_url, cloudfront_url, cloudfront_distribution_id, data_bucket, frontend_bucket
```

Open `cloudfront_url` and sign in with `app_password`.

### Manual terraform only

```bash
cd word-inbox/backend && make zip-lambda
cd ../infra
terraform init
terraform apply
```

Then build/sync the SPA as in `scripts/deploy.sh` (or run `./scripts/deploy.sh --skip-apply`).

## Security note

This is a **personal** shared-password app. Anyone with the password gets the bearer token. Rotate `app_password` / `app_token` in `terraform.tfvars` and re-apply if either leaks. Do not commit `terraform.tfvars` or state files.
