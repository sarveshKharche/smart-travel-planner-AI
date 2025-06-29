# DynamoDB Module - Smart Travel Planner AI
# On-demand billing with TTL for cost optimization

resource "aws_dynamodb_table" "agent_state" {
  name         = "${var.name_prefix}-agent-state"
  billing_mode = "PAY_PER_REQUEST"  # On-demand pricing for free tier
  
  # Primary key
  hash_key = "session_id"
  
  attribute {
    name = "session_id"
    type = "S"
  }
  
  # TTL for automatic cleanup (cost optimization)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  
  # Point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = false  # Disabled for cost optimization
  }
  
  # Server-side encryption
  server_side_encryption {
    enabled = true
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-agent-state"
    Purpose = "Travel planning session state and execution traces"
  })
}

# DynamoDB table for execution traces and audit logs
resource "aws_dynamodb_table" "execution_trace" {
  name         = "${var.name_prefix}-execution-trace"
  billing_mode = "PAY_PER_REQUEST"
  
  # Primary key
  hash_key  = "trace_id"
  range_key = "timestamp"
  
  attribute {
    name = "trace_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  attribute {
    name = "session_id"
    type = "S"
  }
  
  # Global Secondary Index for querying by session
  global_secondary_index {
    name     = "SessionIndex"
    hash_key = "session_id"
    projection_type = "ALL"
  }
  
  # TTL for automatic cleanup
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  
  # Server-side encryption
  server_side_encryption {
    enabled = true
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-execution-trace"
    Purpose = "Agent execution traces and debugging logs"
  })
}
