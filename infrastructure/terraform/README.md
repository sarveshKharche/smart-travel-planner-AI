# Smart Travel Planner AI - Infrastructure

This directory contains the Terraform infrastructure-as-code for deploying the Smart Travel Planner AI to AWS.

## 🏗️ Architecture Overview

The infrastructure follows a modular design with the following components:

- **Lambda Function**: Serverless compute for the AI agents
- **API Gateway**: RESTful API interface
- **DynamoDB**: State storage and session management
- **S3**: File storage and Lambda deployment packages
- **CloudWatch**: Monitoring and alerting
- **AWS Budget**: Cost management and alerts

## 📁 Module Structure

```
modules/
├── lambda/          # Lambda function and IAM roles
├── api_gateway/     # API Gateway REST API
├── dynamodb/        # DynamoDB table for state storage
├── s3/             # S3 bucket for data storage
└── budget/         # Budget monitoring and CloudWatch alarms
```

## 🚀 Quick Deployment

### Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** >= 1.0 installed
3. **Lambda deployment package** built and available

### Step 1: Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### Step 2: Review and Customize Variables

Copy and customize the variables:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your specific values
```

### Step 3: Plan Deployment

```bash
terraform plan -var-file="terraform.tfvars"
```

### Step 4: Deploy Infrastructure

```bash
terraform apply -var-file="terraform.tfvars"
```

## ⚙️ Configuration Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `aws_region` | AWS region for deployment | `us-east-1` |
| `project_name` | Name prefix for all resources | `smart-travel-planner` |
| `environment` | Environment name | `dev`, `staging`, `prod` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `lambda_timeout` | Lambda timeout in seconds | `300` |
| `lambda_memory_size` | Lambda memory in MB | `1024` |
| `budget_limit_usd` | Monthly budget limit | `50` |
| `budget_alert_email` | Email for budget alerts | `""` |

### Budget Configuration

```hcl
budget_limit_usd = "100"
budget_alert_email = "admin@example.com"
budget_threshold_percentages = [80, 100]
```

### Security Configuration

```hcl
lambda_reserved_concurrency = 10
enable_xray_tracing = true
enable_detailed_monitoring = true
```

## 🌍 Environment-Specific Deployments

### Development Environment

```bash
terraform apply -var="environment=dev" -var="budget_limit_usd=25"
```

### Production Environment

```bash
terraform apply -var="environment=prod" -var="budget_limit_usd=200" -var="enable_detailed_monitoring=true"
```

## 📊 Monitoring and Alerting

The infrastructure includes comprehensive monitoring:

### CloudWatch Alarms

- **Lambda Errors**: Triggers when error rate > 5 in 5 minutes
- **API Gateway 4XX**: Triggers when 4XX errors > 10 in 5 minutes  
- **DynamoDB Throttling**: Triggers on any throttling events

### AWS Budgets

- **Cost Alerts**: Email notifications at 80% and 100% of budget
- **Forecasted Overage**: Alerts when forecasted to exceed budget

### Logs

- **Lambda Logs**: Retained for 14 days (configurable)
- **API Gateway Logs**: Access and execution logs
- **CloudTrail**: API calls and resource changes

## 🔧 Module Details

### Lambda Module

**Location**: `modules/lambda/`

**Resources**:
- Lambda function with configurable runtime and memory
- IAM role with least-privilege permissions
- CloudWatch log group with retention

**Key Features**:
- Automatic dependency management
- Environment variable injection
- VPC configuration (optional)
- Reserved concurrency (optional)

### API Gateway Module

**Location**: `modules/api_gateway/`

**Resources**:
- REST API with CORS enabled
- Lambda integration with proxy
- Deployment with stage management
- Rate limiting and throttling

**Key Features**:
- Automatic CORS configuration
- Request/response transformation
- Caching (optional)
- WAF integration (optional)

### DynamoDB Module

**Location**: `modules/dynamodb/`

**Resources**:
- DynamoDB table with TTL
- GSI for query optimization
- Backup configuration

**Key Features**:
- Pay-per-request billing
- Point-in-time recovery
- Server-side encryption
- Auto-scaling (for provisioned mode)

### S3 Module

**Location**: `modules/s3/`

**Resources**:
- S3 bucket with versioning
- Server-side encryption
- Public access blocking
- Lifecycle policies

**Key Features**:
- Secure by default
- Cost optimization
- Cross-region replication (optional)

### Budget Module

**Location**: `modules/budget/`

**Resources**:
- AWS Budget with email alerts
- CloudWatch alarms for services
- SNS topics for notifications

**Key Features**:
- Multi-threshold alerting
- Cost and usage tracking
- Anomaly detection (optional)

## 🛠️ Advanced Configuration

### Custom Domain Setup

```hcl
# Add to your terraform.tfvars
api_custom_domain = "api.yourdomain.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/abc123"
```

### VPC Configuration

```hcl
# Add VPC configuration for Lambda
lambda_vpc_config = {
  subnet_ids         = ["subnet-abc123", "subnet-def456"]
  security_group_ids = ["sg-abc123"]
}
```

### Multi-Region Deployment

```hcl
# Deploy to multiple regions
provider "aws" {
  alias  = "us-west-2"
  region = "us-west-2"
}

module "west_coast_deployment" {
  source = "./modules"
  providers = {
    aws = aws.us-west-2
  }
  # ... configuration
}
```

## 🔒 Security Best Practices

### IAM Permissions

- All IAM roles follow least-privilege principle
- Cross-service permissions are explicitly defined
- No wildcard permissions in production

### Encryption

- DynamoDB encrypted at rest with AWS KMS
- S3 bucket encrypted with AES-256
- Lambda environment variables encrypted

### Network Security

- S3 buckets block public access
- API Gateway with rate limiting
- Optional VPC deployment for Lambda

## 💰 Cost Optimization

### Free Tier Usage

The infrastructure is designed to stay within AWS Free Tier limits:

- **Lambda**: 1M requests/month, 400,000 GB-seconds
- **DynamoDB**: 25 GB storage, 25 WCU, 25 RCU
- **API Gateway**: 1M API calls/month
- **S3**: 5 GB storage, 20,000 GET requests

### Cost Monitoring

```hcl
# Set strict budget limits
budget_limit_usd = "10"  # Very conservative limit
budget_threshold_percentages = [50, 80, 100]
```

### Resource Cleanup

```bash
# Destroy all resources when no longer needed
terraform destroy -var-file="terraform.tfvars"
```

## 🔄 CI/CD Integration

### GitHub Actions

The included GitHub Actions workflow:

1. **Validates** Terraform syntax
2. **Plans** infrastructure changes
3. **Applies** changes on merge to main
4. **Manages** multiple environments

### Terraform State

For production use, configure remote state:

```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "smart-travel-planner/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## 📚 Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-basic-concept.html)

## 🆘 Troubleshooting

### Common Issues

**Issue**: `Error creating Lambda function: InvalidParameterValueException`
**Solution**: Ensure the deployment package exists and is in the correct S3 location.

**Issue**: `Error: AccessDenied when accessing S3 bucket`
**Solution**: Check IAM permissions and bucket policies.

**Issue**: `DynamoDB throttling errors`
**Solution**: Switch to on-demand billing or increase provisioned capacity.

### Getting Help

1. Check the [Terraform documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
2. Review AWS service quotas and limits
3. Enable debug logging: `TF_LOG=DEBUG terraform apply`
4. Use AWS CloudFormation console to inspect resource relationships

## 📄 License

This infrastructure code is part of the Smart Travel Planner AI project and follows the same license terms.
