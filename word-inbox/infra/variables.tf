variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "word-inbox"
}

variable "app_password" {
  description = "Shared login password (Lambda APP_PASSWORD)"
  type        = string
  sensitive   = true
}

variable "app_token" {
  description = "Bearer token returned after login (Lambda APP_TOKEN)"
  type        = string
  sensitive   = true
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment zip (bootstrap binary)"
  type        = string
  default     = "../backend/function.zip"
}

variable "s3_prefix" {
  description = "Key prefix for batch objects (one JSON object per send)"
  type        = string
  default     = "batches/"
}
