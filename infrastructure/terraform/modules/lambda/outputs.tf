# Lambda Module Outputs

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.travel_planner.function_name
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.travel_planner.arn
}

output "invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  value       = aws_lambda_function.travel_planner.invoke_arn
}

output "function_url" {
  description = "Function URL if created"
  value       = aws_lambda_function.travel_planner.function_name
}
