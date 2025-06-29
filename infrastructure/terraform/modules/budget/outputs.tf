output "budget_name" {
  description = "Name of the created budget"
  value       = aws_budgets_budget.smart_travel_planner_budget.name
}

output "budget_arn" {
  description = "ARN of the created budget"
  value       = aws_budgets_budget.smart_travel_planner_budget.arn
}

output "lambda_error_alarm_arn" {
  description = "ARN of the Lambda error alarm"
  value       = aws_cloudwatch_metric_alarm.lambda_error_alarm.arn
}

output "api_gateway_4xx_alarm_arn" {
  description = "ARN of the API Gateway 4XX error alarm"
  value       = aws_cloudwatch_metric_alarm.api_gateway_4xx_alarm.arn
}

output "dynamodb_throttle_alarm_arn" {
  description = "ARN of the DynamoDB throttling alarm"
  value       = aws_cloudwatch_metric_alarm.dynamodb_throttle_alarm.arn
}
