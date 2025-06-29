# Budget monitoring for Smart Travel Planner

resource "aws_budgets_budget" "smart_travel_planner_budget" {
  name              = var.budget_name
  budget_type       = "COST"
  limit_amount      = var.budget_limit
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = var.budget_start_time

  dynamic "notification" {
    for_each = var.notifications
    content {
      comparison_operator        = notification.value.comparison_operator
      threshold                 = notification.value.threshold
      threshold_type            = notification.value.threshold_type
      notification_type         = notification.value.notification_type
      subscriber_email_addresses = notification.value.subscriber_email_addresses
    }
  }
}

# CloudWatch alarm for Lambda function errors
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "${var.project_name}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors for Smart Travel Planner"
  alarm_actions       = var.alarm_actions

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.tags
}

# CloudWatch alarm for API Gateway 4XX errors
resource "aws_cloudwatch_metric_alarm" "api_gateway_4xx_alarm" {
  alarm_name          = "${var.project_name}-api-gateway-4xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors API Gateway 4XX errors"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ApiName = var.api_gateway_name
  }

  tags = var.tags
}

# CloudWatch alarm for DynamoDB throttling
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttle_alarm" {
  alarm_name          = "${var.project_name}-dynamodb-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors DynamoDB throttling events"
  alarm_actions       = var.alarm_actions

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  tags = var.tags
}
