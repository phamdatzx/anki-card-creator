#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA="$ROOT/infra"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

TF_ARGS=()
APPLY_ONLY=0
SKIP_APPLY=0

usage() {
  cat <<'EOF'
Usage: ./scripts/deploy.sh [options] [-- extra terraform args]

Build the Lambda zip, apply Terraform, build the SPA against the API URL,
sync assets to the frontend bucket, and invalidate CloudFront.

Options:
  --apply-only   Only terraform apply (no frontend sync)
  --skip-apply   Skip terraform apply; sync SPA using current outputs
  -h, --help     Show this help

Requires: terraform, aws CLI, go, npm, make
Secrets: set in infra/terraform.tfvars (see terraform.tfvars.example)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply-only) APPLY_ONLY=1; shift ;;
    --skip-apply) SKIP_APPLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; TF_ARGS+=("$@"); break ;;
    *) TF_ARGS+=("$1"); shift ;;
  esac
done

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: required command not found: $1" >&2
    exit 1
  }
}

need terraform
need aws
need go
need npm
need make
need python3

if [[ ! -f "$INFRA/terraform.tfvars" ]]; then
  echo "error: missing $INFRA/terraform.tfvars" >&2
  echo "Copy terraform.tfvars.example and set app_password / app_token." >&2
  exit 1
fi

echo "==> Building Lambda zip"
make -C "$BACKEND" zip-lambda

if [[ ! -f "$BACKEND/function.zip" ]]; then
  echo "error: expected $BACKEND/function.zip after zip-lambda" >&2
  exit 1
fi

cd "$INFRA"
if [[ ! -d .terraform ]]; then
  echo "==> terraform init"
  terraform init
fi

if [[ "$SKIP_APPLY" -eq 0 ]]; then
  echo "==> terraform apply"
  terraform apply "${TF_ARGS[@]}"
fi

API_URL="$(terraform output -raw api_url)"
FRONTEND_BUCKET="$(terraform output -raw frontend_bucket)"
CF_URL="$(terraform output -raw cloudfront_url)"
CF_ID="$(terraform output -raw cloudfront_distribution_id)"

echo "API:        $API_URL"
echo "CloudFront: $CF_URL"
echo "Frontend S3: $FRONTEND_BUCKET"

if [[ "$APPLY_ONLY" -eq 1 ]]; then
  echo "==> --apply-only set; skipping SPA build/sync"
  exit 0
fi

echo "==> Building frontend with VITE_API_BASE_URL=$API_URL"
cd "$FRONTEND"
VITE_API_BASE_URL="$API_URL" npm run build

echo "==> Syncing dist/ to s3://$FRONTEND_BUCKET"
aws s3 sync "$FRONTEND/dist/" "s3://$FRONTEND_BUCKET/" --delete

echo "==> Invalidating CloudFront $CF_ID"
aws cloudfront create-invalidation \
  --distribution-id "$CF_ID" \
  --paths "/*" >/dev/null

echo
echo "Deploy complete."
echo "Open: $CF_URL"
