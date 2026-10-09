variable "region" {
  description = "AWS region for S3 bucket"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  type        = string
  description = "prefix for resource names"
  default     = "tf-reviewer"
}

variable "lock_table_state" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
  default     = "tf-review-Terraform-locks"
}
