# Configure the AWS provider
provider "aws" {
  region  = "us-east-1"   # You can change region if needed
  profile = "default"     # Uses credentials from `aws configure`
}

# Create an S3 Bucket
resource "aws_s3_bucket" "infra_logs" {
  bucket = "infra-lab-logs-${random_id.bucket_id.hex}"
  force_destroy = true

  tags = {
    Name        = "InfraLogBucket"
    Environment = "Dev"
    Owner       = "Maksim"
    # Deliberately missing CostCenter tag for testing
  }
}

# Random ID for unique bucket name
resource "random_id" "bucket_id" {
  byte_length = 4
}

# EC2 Instance
resource "aws_instance" "web_server" {
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2 AMI (Free Tier)
  instance_type = "t2.micro"

  tags = {
    Name        = "InfraLabEC2"
    Environment = "Dev"
    Owner       = "Maksim"
    CostCenter  = "IT"
  }
}
