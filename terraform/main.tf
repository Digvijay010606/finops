# DAY 17: Sample infrastructure used to demonstrate pre-deployment cost estimation with Infracost
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
provider "aws" { region = "us-east-1" }

locals {
  tags = { env = var.env, team = "platform", owner = "finops@example.com", "cost-center" = "CC-1042" }   # satisfies tagging policy
}
variable "env" {
  default = "staging"
}
# PR change m5.large -> m5.xlarge shows up as a cost delta in the PR comment
variable "app_instance_type" {
  default = "m5.large"
}

resource "aws_instance" "app" {
  count         = 2
  ami           = "ami-0c02fb55956c7d316"
  instance_type = var.app_instance_type
  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }
  tags = merge(local.tags, { Name = "app-${count.index}" })
}
resource "aws_db_instance" "main" {
  identifier = "finops-demo-db"
  engine = "postgres"
  instance_class = "db.t3.medium"
  allocated_storage = 100
  username = "admin"
  password = "change-me-use-secrets-manager"
  skip_final_snapshot = true
  tags = local.tags
}
resource "aws_s3_bucket" "logs" {
  bucket = "finops-demo-logs-example"
  tags   = local.tags
}
