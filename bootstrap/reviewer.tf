# Read-only role the PR reviewer workflow assumes via OIDC
module "reviewer_role" {
  source            = "../modules/github-oidc-role"
  name              = "fintrack-tf-reviewer"
  oidc_provider_arn = aws_iam_openid_connect_provider.github.arn
  subjects          = ["repo:qezman/fintrack-infrastructure:pull_request"] # PR runs in the FinTrack repo only
  policy_arns       = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]           # plan only needs read access
}
