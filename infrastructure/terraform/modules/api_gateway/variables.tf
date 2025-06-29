variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
  default     = "smart-travel-planner-api"
}

variable "api_description" {
  description = "Description of the API Gateway"
  type        = string
  default     = "API Gateway for Smart Travel Planner AI"
}

variable "stage_name" {
  description = "API Gateway deployment stage name"
  type        = string
  default     = "prod"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to integrate"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "ARN for invoking the Lambda function"
  type        = string
}

variable "tags" {
  description = "Tags to apply to API Gateway resources"
  type        = map(string)
  default     = {}
}
