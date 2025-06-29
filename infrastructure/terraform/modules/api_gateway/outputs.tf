output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.travel_planner_api.id
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_api_gateway_deployment.travel_planner_deployment.invoke_url
}

output "api_gateway_endpoint" {
  description = "Full endpoint URL for the travel planner API"
  value       = "${aws_api_gateway_deployment.travel_planner_deployment.invoke_url}/plan"
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.travel_planner_api.execution_arn
}

output "deployment_stage" {
  description = "Deployment stage of the API Gateway"
  value       = aws_api_gateway_deployment.travel_planner_deployment.stage_name
}
