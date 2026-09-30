output "api_url" {
  description = "HTTP API invoke URL (use as VITE_API_BASE_URL)"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "cloudfront_url" {
  description = "CloudFront URL for the SPA"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "data_bucket" {
  description = "S3 bucket storing word batches (batches/*.json)"
  value       = aws_s3_bucket.data.bucket
}

output "frontend_bucket" {
  description = "S3 bucket for the SPA assets"
  value       = aws_s3_bucket.frontend.bucket
}
