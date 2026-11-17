provider "aws" {
  profile = var.aws_profile
  region  = var.region
}

data "aws_caller_identity" "current" {}

locals {
  state_bucket_name = "${var.project}-terraform-state-${data.aws_caller_identity.current.account_id}-${var.region}"

  common_tags = {
    Project     = var.project
    Environment = "shared"
    ManagedBy   = "terraform"
  }
}