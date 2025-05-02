terraform {
  backend "s3" {
    bucket         = "cloud-monitoring-bucket"
    key            = "cloud/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.regionname
}

