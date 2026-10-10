variable "name" {
  type        = string
  description = "IAM role name"
}

variable "oidc_provider_arn" {
  type        = string
  description = "ARN of the GitHub OIDC provider this role trusts"
}

variable "subjects" {
  type        = list(string)
  description = "GitHub token 'sub' values allowed to assume the role"
}

variable "policy_arns" {
  type        = list(string)
  description = "Managed policies to attach to the role"
}
