# Configure the AWS Provider
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "secure-agent-flow"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 1024
}

variable "bedrock_model" {
  description = "Bedrock model ID for the agent"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

# Create deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_deployment.zip"

  source {
    content = templatefile("${path.module}/lambda_handler.py", {})
    filename = "lambda_handler.py"
  }

  source {
    content = templatefile("${path.module}/crew.py", {})
    filename = "crew.py"
  }

  source {
    content = templatefile("${path.module}/config.py", {})
    filename = "config.py"
  }

  source {
    content = templatefile("${path.module}/agents.py", {})
    filename = "agents.py"
  }

  source {
    content = templatefile("${path.module}/tasks.py", {})
    filename = "tasks.py"
  }

  source {
    content = templatefile("${path.module}/utils.py", {})
    filename = "utils.py"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Layer for dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename         = "dependencies.zip"
  layer_name       = "${var.project_name}-dependencies-${var.environment}"
  description      = "Dependencies for secure agent flow"

  compatible_runtimes = ["python3.9", "python3.10", "python3.11"]

  # This assumes you've created a dependencies.zip with crewai and other deps
  # You'll need to create this separately
}

# Lambda Function
resource "aws_lambda_function" "secure_agent_flow" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-function-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_handler.bedrock_agent_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      AWS_REGION     = var.aws_region
      BEDROCK_MODEL_ID = var.bedrock_model
      ENVIRONMENT    = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs,
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-function-${var.environment}"
  retention_in_days = 14
}

# Lambda Permission for Bedrock Agent
resource "aws_lambda_permission" "bedrock_agent_invoke" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.secure_agent_flow.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_bedrockagent_agent.secure_agent.agent_arn
}

# IAM Role for Bedrock Agent
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-bedrock-agent-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM Policy for Bedrock Agent
resource "aws_iam_role_policy" "bedrock_agent_policy" {
  name = "${var.project_name}-bedrock-agent-policy-${var.environment}"
  role = aws_iam_role.bedrock_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.secure_agent_flow.arn
      }
    ]
  })
}

# Bedrock Agent
resource "aws_bedrockagent_agent" "secure_agent" {
  agent_name              = "${var.project_name}-agent-${var.environment}"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  description            = "Secure Agent Flow for policy and role management"
  foundation_model       = "anthropic.claude-3-sonnet-20240229-v1:0"
  idle_session_ttl_in_seconds = 3600

  instruction = <<-EOT
You are a secure agent flow assistant that helps organizations analyze roles, map permissions, prepare data, and create security policies.

Your primary functions include:
1. Fetching and analyzing organizational roles and access details
2. Mapping roles to appropriate permissions and access levels
3. Preparing structured data for policy creation
4. Creating comprehensive security policies based on compliance requirements

When a user provides context about their system and policy requirements, you should:
- Analyze the organizational structure and roles
- Map roles to appropriate access levels
- Prepare the data in a structured format
- Generate security policies that meet compliance requirements like SOX, GDPR, etc.

Always ensure principle of least privilege and segregation of duties in your recommendations.
EOT

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Action Group for Bedrock Agent
resource "aws_bedrockagent_agent_action_group" "secure_flow_actions" {
  action_group_name = "secure-flow-actions"
  agent_id         = aws_bedrockagent_agent.secure_agent.id
  agent_version    = "DRAFT"
  description      = "Actions for secure agent flow workflow"

  action_group_executor {
    lambda = aws_lambda_function.secure_agent_flow.arn
  }

  api_schema {
    s3 {
      s3_bucket_name = aws_s3_bucket.agent_schemas.bucket
      s3_object_key  = aws_s3_object.api_schema.key
    }
  }

  depends_on = [aws_s3_object.api_schema]
}

# S3 Bucket for API schemas
resource "aws_s3_bucket" "agent_schemas" {
  bucket = "${var.project_name}-agent-schemas-${var.environment}-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "agent_schemas_versioning" {
  bucket = aws_s3_bucket.agent_schemas.id
  versioning_configuration {
    status = "Enabled"
  }
}

# API Schema for Action Group
resource "aws_s3_object" "api_schema" {
  bucket = aws_s3_bucket.agent_schemas.bucket
  key    = "secure-flow-api-schema.json"

  content = jsonencode({
    openapi = "3.0.0"
    info = {
      title   = "Secure Agent Flow API"
      version = "1.0.0"
      description = "API for secure agent flow operations"
    }
    paths = {
      "/execute-workflow" = {
        post = {
          summary = "Execute secure agent flow workflow"
          description = "Runs the complete secure agent flow with context and policy requirements"
          operationId = "executeSecureFlow"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type = "object"
                  properties = {
                    context_input = {
                      type = "string"
                      description = "System context and organizational information"
                    }
                    policy_requirements = {
                      type = "string"
                      description = "Policy requirements and compliance frameworks"
                    }
                  }
                  required = ["context_input"]
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Successful workflow execution"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type = "boolean"
                      }
                      result = {
                        type = "object"
                        description = "Workflow execution results"
                      }
                      message = {
                        type = "string"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  })

  content_type = "application/json"
}
