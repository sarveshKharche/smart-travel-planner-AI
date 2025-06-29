# Smart Travel Planner AI - Modular Terraform Infrastructure
# AWS Free-Tier Optimized Infrastructure using modules

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "smart-travel-planner"
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
  default     = "dev"
}

variable "notification_email" {
  description = "Email address for budget and alarm notifications"
  type        = string
  default     = ""
}

# Local values
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# S3 Module
module "s3" {
  source = "./modules/s3"

  name_prefix = "${var.project_name}-${var.environment}"
  environment = var.environment
  tags        = local.common_tags
}

# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix = "${var.project_name}-${var.environment}"
  environment = var.environment
  tags        = local.common_tags
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  name_prefix          = "${var.project_name}-${var.environment}"
  environment          = var.environment
  dynamodb_table_name  = module.dynamodb.table_name
  s3_bucket_name       = module.s3.bucket_name
  tags                 = local.common_tags
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  api_name             = "${var.project_name}-api-${var.environment}"
  api_description      = "Smart Travel Planner AI API"
  stage_name           = var.environment
  lambda_function_name = module.lambda.function_name
  lambda_invoke_arn    = module.lambda.invoke_arn
  tags                 = local.common_tags
}

# Budget and Monitoring Module
module "budget" {
  source = "./modules/budget"

  budget_name          = "${var.project_name}-budget-${var.environment}"
  budget_limit         = var.environment == "prod" ? "100" : "25"
  project_tag          = var.project_name
  project_name         = var.project_name
  lambda_function_name = module.lambda.function_name
  api_gateway_name     = module.api_gateway.api_gateway_id
  dynamodb_table_name  = module.dynamodb.table_name
  tags                 = local.common_tags

  notifications = var.notification_email != "" ? [
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 80
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.notification_email]
    },
    {
      comparison_operator        = "GREATER_THAN"
      threshold                  = 100
      threshold_type             = "PERCENTAGE"
      notification_type          = "FORECASTED"
      subscriber_email_addresses = [var.notification_email]
    }
  ] : []
}

# Outputs
output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = module.api_gateway.api_gateway_url
}

output "api_gateway_endpoint" {
  description = "Full endpoint URL for the travel planner API"
  value       = module.api_gateway.api_gateway_endpoint
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.function_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "budget_name" {
  description = "Name of the budget"
  value       = module.budget.budget_name
}
