locals {
  lambda_zip_abs = abspath("${path.module}/${var.lambda_zip_path}")
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "api" {
  function_name = local.lambda_name
  role          = aws_iam_role.lambda.arn
  handler       = "bootstrap"
  runtime       = "provided.al2023"
  architectures = ["x86_64"]
  timeout       = 15
  memory_size   = 128

  filename         = local.lambda_zip_abs
  source_code_hash = filebase64sha256(local.lambda_zip_abs)

  environment {
    variables = {
      APP_PASSWORD = var.app_password
      APP_TOKEN    = var.app_token
      S3_BUCKET    = aws_s3_bucket.data.bucket
      S3_PREFIX    = var.s3_prefix
      CORS_ORIGIN  = "https://${aws_cloudfront_distribution.frontend.domain_name}"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_s3,
  ]
}
