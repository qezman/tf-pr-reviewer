output "state_bucket" {
  value = aws_s3_bucket.state.id
}

output "github_oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}

output "reviewer_role_arn" {
  value = module.reviewer_role.arn
}
