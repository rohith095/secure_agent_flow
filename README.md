# Secure Agent Flow - AWS Bedrock Agent Deployment

A comprehensive secure agent flow application built with CrewAI and deployed to AWS Bedrock Agent for policy and role management automation.

## 🏗️ Architecture

This project deploys a multi-agent system that:
1. **Roles Fetcher Agent** - Analyzes organizational roles and access details
2. **Mapping Agent** - Maps roles to appropriate permissions and access levels  
3. **Preparer Agent** - Structures data for policy creation
4. **Policy Creator Agent** - Generates comprehensive security policies

The system is deployed as:
- **AWS Lambda Function** - Runs the CrewAI workflow
- **AWS Bedrock Agent** - Provides conversational interface
- **S3 Bucket** - Stores API schemas
- **CloudWatch** - Logging and monitoring

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** >= 1.0
3. **Python** 3.11+ 
4. **uv** package manager (will be auto-installed if not present)
5. **OpenAI API Key** for CrewAI agents

### Required AWS Permissions

Your AWS credentials need the following services:
- AWS Lambda (create, update, invoke)
- AWS Bedrock (create agents, invoke models)
- IAM (create roles and policies)
- S3 (create buckets, upload objects)
- CloudWatch (create log groups)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   git clone <your-repo>
   cd secure_agent_flow
   ```

2. **Install uv (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   ```

3. **Set up the development environment:**
   ```bash
   uv sync
   ```

4. **Configure your variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

5. **Set your OpenAI API key in terraform.tfvars:**
   ```hcl
   openai_api_key = "your-openai-api-key-here"
   ```

6. **Deploy the infrastructure:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## 📁 Project Structure

```
secure_agent_flow/
├── lambda_handler.py          # AWS Lambda handlers
├── main.py                    # Local execution entry point
├── crew.py                    # CrewAI workflow orchestration
├── agents.py                  # Agent definitions
├── tasks.py                   # Task definitions
├── config.py                  # Configuration management
├── utils.py                   # Utility functions
├── pyproject.toml             # uv package configuration
├── uv.lock                    # Dependency lock file
├── main.tf                    # Main Terraform configuration
├── variables.tf               # Terraform input variables
├── outputs.tf                 # Terraform outputs
├── terraform.tfvars.example   # Example configuration
├── deploy.sh                  # Deployment script
├── build_layer.sh            # Dependencies layer builder
└── README.md                  # This file
```

## 🔧 Package Management with uv

This project uses [uv](https://github.com/astral-sh/uv) for fast and reliable Python package management.

### Common uv commands:

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Update dependencies
uv sync --upgrade

# Run scripts in the virtual environment
uv run python main.py

# Activate the virtual environment
source .venv/bin/activate

# Install specific versions
uv add "crewai>=0.186.1"
```

### Development Setup:

```bash
# Install all dependencies including dev tools
uv sync

# Install with development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run code formatting
uv run black .

# Run type checking
uv run mypy .
```

## 🔧 Configuration

### Environment Variables

The following variables can be configured in `terraform.tfvars`:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS deployment region | `us-east-1` | No |
| `project_name` | Project name prefix | `secure-agent-flow` | No |
| `environment` | Environment (dev/staging/prod) | `dev` | No |
| `openai_api_key` | OpenAI API key | - | **Yes** |
| `lambda_timeout` | Lambda timeout in seconds | `300` | No |
| `lambda_memory_size` | Lambda memory in MB | `1024` | No |
| `bedrock_model` | Bedrock foundation model | `anthropic.claude-3-sonnet-20240229-v1:0` | No |

### Example terraform.tfvars:
```hcl
aws_region = "us-east-1"
project_name = "secure-agent-flow"
environment = "prod"
openai_api_key = "sk-..."
lambda_timeout = 300
lambda_memory_size = 1024
```

## 🎯 Usage

### Via AWS Bedrock Agent Console

1. Go to AWS Console → Amazon Bedrock → Agents
2. Find your deployed agent
3. Test with sample inputs:

```
context: Enterprise application with 500 users, role-based access control, Active Directory integration
policy: SOX compliance required, quarterly access reviews, principle of least privilege
```

### Local Development

```bash
# Install dependencies
uv sync

# Set environment variables
export OPENAI_API_KEY="your-key-here"

# Run locally
uv run python main.py

# Or activate the environment and run directly
source .venv/bin/activate
python main.py
```

### Via Lambda Function (Direct)

```python
import boto3
import json

lambda_client = boto3.client('lambda')

payload = {
    "context_input": "Enterprise system with multiple user roles...",
    "policy_requirements": "SOX and GDPR compliance requirements..."
}

response = lambda_client.invoke(
    FunctionName='secure-agent-flow-function-dev',
    Payload=json.dumps(payload)
)
```

## 🔍 Monitoring

### CloudWatch Logs
- Function logs: `/aws/lambda/secure-agent-flow-function-{env}`
- Monitor execution time, memory usage, and errors

### AWS X-Ray (Optional)
- Enable tracing in Lambda configuration for detailed performance insights

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors in Lambda**
   - Ensure all dependencies are in the layer
   - Check build_layer.sh execution with uv
   - Verify layer compatibility with Python runtime

2. **uv Installation Issues**
   - Install manually: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Ensure PATH includes `~/.cargo/bin`
   - Restart terminal after installation

3. **Dependency Conflicts**
   - Use `uv sync --upgrade` to update dependencies
   - Check `uv.lock` for version conflicts
   - Use `uv add --resolution highest` for latest versions

4. **Bedrock Model Access**
   - Ensure model access is enabled in Bedrock console
   - Check IAM permissions for bedrock:InvokeModel

### Debug Commands

```bash
# Check uv installation
uv --version

# Validate dependencies
uv sync --dry-run

# Check Terraform plan
terraform plan

# Test Lambda function
aws lambda invoke --function-name secure-agent-flow-function-dev output.json

# View logs
aws logs tail /aws/lambda/secure-agent-flow-function-dev --follow
```

## 🧪 Testing

### Unit Tests
```bash
# Run tests with uv
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Test specific components
uv run pytest tests/test_agents.py
```

### Integration Tests
```bash
# Test deployed Lambda function
aws lambda invoke --function-name secure-agent-flow-function-dev \
  --payload '{"context_input":"test","policy_requirements":"test"}' \
  response.json
```

## 🔄 Updates

To update the deployment:

1. **Code Changes**:
   ```bash
   # Update dependencies if needed
   uv sync
   
   # Redeploy
   ./deploy.sh
   ```

2. **Add New Dependencies**:
   ```bash
   # Add to project
   uv add new-package
   
   # Update build script and redeploy
   ./deploy.sh
   ```

3. **Dependency Updates**:
   ```bash
   # Update all dependencies
   uv sync --upgrade
   
   # Rebuild layer and deploy
   ./build_layer.sh
   terraform apply
   ```

## 📈 Performance Optimization

### uv Benefits
- **Fast installs**: 10-100x faster than pip
- **Reliable resolution**: Consistent dependency resolution
- **Lock files**: Reproducible builds with uv.lock
- **Single binary**: No Python required for installation

### Production Tips
```bash
# Use locked dependencies for production
uv sync --frozen

# Build optimized Lambda layer
./build_layer.sh

# Use specific Python version
uv sync --python 3.11
```
