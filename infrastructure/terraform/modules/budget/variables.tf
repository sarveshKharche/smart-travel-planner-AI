variable "budget_name" {
  description = "Name of the budget"
  type        = string
  default     = "smart-travel-planner-budget"
}

variable "budget_limit" {
  description = "Budget limit in USD"
  type        = string
  default     = "50"
}

variable "budget_start_time" {
  description = "Budget start time in YYYY-MM-DD_HH:MM format"
  type        = string
  default     = "2024-01-01_00:00"
}

variable "project_tag" {
  description = "Project tag for cost filtering"
  type        = string
  default     = "smart-travel-planner"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "smart-travel-planner"
}

variable "notifications" {
  description = "Budget notification configuration"
  type = list(object({
    comparison_operator        = string
    threshold                 = number
    threshold_type            = string
    notification_type         = string
    subscriber_email_addresses = list(string)
  }))
  default = [
    {
      comparison_operator        = "GREATER_THAN"
      threshold                 = 80
      threshold_type            = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = []
    },
    {
      comparison_operator        = "GREATER_THAN"
      threshold                 = 100
      threshold_type            = "PERCENTAGE"
      notification_type          = "FORECASTED"
      subscriber_email_addresses = []
    }
  ]
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor"
  type        = string
}

variable "api_gateway_name" {
  description = "Name of the API Gateway to monitor"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table to monitor"
  type        = string
}

variable "tags" {
  description = "Tags to apply to monitoring resources"
  type        = map(string)
  default     = {}
}
