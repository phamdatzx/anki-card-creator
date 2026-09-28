# Word Inbox

Personal vocabulary capture app: note `{ input, type }` items behind a shared
password, store them on S3 via a Go Lambda API. Anki sync is a later phase.

```
word-inbox/
  backend/     Go Lambda + local HTTP server (+ Dockerfile)
  frontend/    Vite + React + TypeScript SPA
  infra/       Terraform (S3, Lambda, HTTP API, CloudFront)
  scripts/     deploy.sh
  docker-compose.yml
```

## Quick local run

### 1. Backend (in-memory store)

**Option A — Docker (recommended for API testing)**

```bash
cd word-inbox
docker compose up --build
# API: http://localhost:8080
# defaults: APP_PASSWORD=dev-password, CORS for http://localhost:5173
```

Optional env overrides: copy `.env.docker.example` to `.env` in `word-inbox/`, or export `APP_PASSWORD` / `APP_TOKEN` / `CORS_ORIGIN`.

**Option B — Go on the host**

```bash
cd word-inbox/backend
export APP_PASSWORD=dev-password
export APP_TOKEN=dev-token
export CORS_ORIGIN=http://localhost:5173
make run-local
# listens on :8080
```

### 2. Frontend (always on the host)

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
