terraform {
  required_version = ">= 1.10.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7"
    }
    aws = {
      source = "hashicorp/aws"
    }
  }

  backend "s3" {}
}