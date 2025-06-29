# DynamoDB Module Outputs

output "table_name" {
  description = "Name of the main DynamoDB table"
  value       = aws_dynamodb_table.agent_state.name
}

output "table_arn" {
  description = "ARN of the main DynamoDB table"
  value       = aws_dynamodb_table.agent_state.arn
}

output "trace_table_name" {
  description = "Name of the execution trace table"
  value       = aws_dynamodb_table.execution_trace.name
}

output "trace_table_arn" {
  description = "ARN of the execution trace table"
  value       = aws_dynamodb_table.execution_trace.arn
}
