#!/bin/sh
# Runs inside LocalStack once S3 is ready; creates the dev bucket if missing.
set -eu
awslocal s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null \
  || awslocal s3 mb "s3://$S3_BUCKET"
