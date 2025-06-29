# API Gateway Module for Smart Travel Planner

resource "aws_api_gateway_rest_api" "travel_planner_api" {
  name        = var.api_name
  description = var.api_description

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# Resource for the travel planner endpoint
resource "aws_api_gateway_resource" "travel_planner_resource" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  parent_id   = aws_api_gateway_rest_api.travel_planner_api.root_resource_id
  path_part   = "plan"
}

# POST method for travel planning
resource "aws_api_gateway_method" "travel_planner_post" {
  rest_api_id   = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id   = aws_api_gateway_resource.travel_planner_resource.id
  http_method   = "POST"
  authorization = "NONE"

  request_parameters = {
    "method.request.header.Content-Type" = true
  }
}

# Integration with Lambda function
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id = aws_api_gateway_resource.travel_planner_resource.id
  http_method = aws_api_gateway_method.travel_planner_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.lambda_invoke_arn
}

# Method response
resource "aws_api_gateway_method_response" "travel_planner_response_200" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id = aws_api_gateway_resource.travel_planner_resource.id
  http_method = aws_api_gateway_method.travel_planner_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# Integration response
resource "aws_api_gateway_integration_response" "lambda_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id = aws_api_gateway_resource.travel_planner_resource.id
  http_method = aws_api_gateway_method.travel_planner_post.http_method
  status_code = aws_api_gateway_method_response.travel_planner_response_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.lambda_integration]
}

# CORS OPTIONS method
resource "aws_api_gateway_method" "travel_planner_options" {
  rest_api_id   = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id   = aws_api_gateway_resource.travel_planner_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id = aws_api_gateway_resource.travel_planner_resource.id
  http_method = aws_api_gateway_method.travel_planner_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_response_200" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id = aws_api_gateway_resource.travel_planner_resource.id
  http_method = aws_api_gateway_method.travel_planner_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  resource_id = aws_api_gateway_resource.travel_planner_resource.id
  http_method = aws_api_gateway_method.travel_planner_options.http_method
  status_code = aws_api_gateway_method_response.options_response_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options_integration]
}

# Deployment
resource "aws_api_gateway_deployment" "travel_planner_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration,
    aws_api_gateway_integration.options_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.travel_planner_api.id
  stage_name  = var.stage_name

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.travel_planner_resource.id,
      aws_api_gateway_method.travel_planner_post.id,
      aws_api_gateway_integration.lambda_integration.id,
      aws_api_gateway_method.travel_planner_options.id,
      aws_api_gateway_integration.options_integration.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.travel_planner_api.execution_arn}/*/*"
}
