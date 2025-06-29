# S3 Module - Smart Travel Planner AI
# Static assets and cached data storage

resource "aws_s3_bucket" "travel_data" {
  bucket = "${var.name_prefix}-travel-data-${random_id.bucket_suffix.hex}"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-travel-data"
    Purpose = "Static datasets and cached activity information"
  })
}

# Random suffix for bucket name uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Bucket versioning
resource "aws_s3_bucket_versioning" "travel_data" {
  bucket = aws_s3_bucket.travel_data.id
  
  versioning_configuration {
    status = "Suspended"  # Disabled for cost optimization
  }
}

# Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "travel_data" {
  bucket = aws_s3_bucket.travel_data.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bucket public access block
resource "aws_s3_bucket_public_access_block" "travel_data" {
  bucket = aws_s3_bucket.travel_data.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "travel_data" {
  bucket = aws_s3_bucket.travel_data.id
  
  rule {
    id     = "cleanup_temp_files"
    status = "Enabled"
    
    filter {
      prefix = "temp/"
    }
    
    # Delete temporary files after 7 days
    expiration {
      days = 7
    }
  }
  
  rule {
    id     = "delete_incomplete_uploads"
    status = "Enabled"
    
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# CORS configuration for web access
resource "aws_s3_bucket_cors_configuration" "travel_data" {
  bucket = aws_s3_bucket.travel_data.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
