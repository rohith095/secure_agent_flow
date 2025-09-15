# Outputs for the secure agent flow deployment

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.secure_agent_flow.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.secure_agent_flow.function_name
}

output "bedrock_agent_id" {
  description = "ID of the Bedrock agent"
  value       = aws_bedrockagent_agent.secure_agent.id
}

output "bedrock_agent_arn" {
  description = "ARN of the Bedrock agent"
  value       = aws_bedrockagent_agent.secure_agent.agent_arn
}

output "bedrock_agent_name" {
  description = "Name of the Bedrock agent"
  value       = aws_bedrockagent_agent.secure_agent.agent_name
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for agent schemas"
  value       = aws_s3_bucket.agent_schemas.bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "deployment_region" {
  description = "AWS region where resources are deployed"
  value       = data.aws_region.current.name
}

output "account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}
