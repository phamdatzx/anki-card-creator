locals {
  data_bucket_name     = "${var.name_prefix}-data-${data.aws_caller_identity.current.account_id}"
  frontend_bucket_name = "${var.name_prefix}-web-${data.aws_caller_identity.current.account_id}"
  lambda_name          = "${var.name_prefix}-api"
  api_name             = "${var.name_prefix}-http"
  cloudfront_origin_id = "${var.name_prefix}-frontend"
}

data "aws_caller_identity" "current" {}
