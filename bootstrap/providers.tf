terraform {
  required_version = ">=1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.81"
    }
  }
  backend "s3" {
    bucket       = "tf-reviewer-state-722965867897"
    key          = "bootstrap/terraform.tfstate" # path of this config's state inside the bucket
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true # S3-native locking
  }

}

provider "aws" {
  region = var.region
}

