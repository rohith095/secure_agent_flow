# Secure Agent Flow

A CrewAI-based multi-agent workflow for role analysis and security policy creation. This system uses 4 specialized agents to analyze roles, map permissions, prepare data, and create comprehensive security policies.

## 🤖 Agents Overview

### 1. Roles and Details Fetcher Agent
- **Purpose**: Extracts role definitions, permissions, and access details from various sources
- **Expertise**: Identity and Access Management (IAM), RBAC systems, enterprise directories
- **Output**: Comprehensive role inventory with detailed permissions matrix

### 2. Mapping Agent
- **Purpose**: Creates relationship mappings between roles, permissions, and resources
- **Expertise**: Systems analysis, access control mapping, relationship modeling
- **Output**: Visual mappings, conflict identification, gap analysis

### 3. Prepare Agent
- **Purpose**: Structures and validates mapped data for policy creation
- **Expertise**: Data preparation, security frameworks, governance structures
- **Output**: Organized, validated datasets ready for policy generation

### 4. Policy Creator Agent
- **Purpose**: Generates comprehensive, compliant security policies
- **Expertise**: Security policy architecture, regulatory compliance, governance
- **Output**: Complete policy suite with implementation guidelines

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- (Optional) Serper API key for web search functionality

### Installation

1. Clone or set up the project directory
2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

Run the complete 4-agent workflow:
```bash
python main.py
```

Run individual agents for testing:
```bash
python main.py fetch    # Roles and Details Fetcher
python main.py map      # Mapping Agent
python main.py prepare  # Prepare Agent
python main.py policy   # Policy Creator
```

## 📁 Project Structure

```
secure_agent_flow/
├── agents.py          # Agent definitions
├── tasks.py           # Task definitions
├── crew.py            # Main crew workflow
├── main.py            # Entry point
├── config.py          # Configuration settings
├── utils.py           # Utility functions
├── .env.example       # Environment variables template
├── outputs/           # Generated outputs (created automatically)
├── logs/              # Application logs (created automatically)
└── pyproject.toml     # Project dependencies
```

## 🔧 Configuration

The system supports various configuration options through environment variables and the `config.py` file:

- **OPENAI_API_KEY**: Required for agent operations
- **OPENAI_MODEL**: Model to use (default: gpt-4)
- **SERPER_API_KEY**: Optional for web search capabilities
- **CREW_VERBOSE**: Enable detailed logging
- **DEBUG**: Enable debug mode

## 📊 Output Examples

The workflow generates several types of outputs:

1. **Role Analysis Report**: Detailed role inventory with permissions
2. **Permission Mapping**: Visual relationships and conflict analysis
3. **Structured Data**: Validated datasets for policy creation
4. **Security Policies**: Complete policy documents with implementation guides

## 🛠 Customization

### Adding New Agents
1. Define the agent in `agents.py`
2. Create corresponding tasks in `tasks.py`
3. Update the crew workflow in `crew.py`

### Modifying Tasks
Edit the task descriptions and expected outputs in `tasks.py` to match your specific requirements.

### Policy Frameworks
The system supports multiple compliance frameworks (NIST, ISO 27001, SOX, GDPR). Configure in `config.py`.

## 🔍 Advanced Usage

### Custom Context Input
```python
from crew import SecureAgentFlowCrew

crew = SecureAgentFlowCrew()
result = crew.run_workflow(
    context_input="Your system context here",
    policy_requirements="Your policy requirements"
)
```

### Programmatic Access
```python
# Run individual tasks
result = crew.run_individual_task("fetch", context_input="...")

# Access configuration
from config import config
status = config.validate_config()
```

## 📈 Monitoring and Logging

- Logs are automatically saved to the `logs/` directory
- Outputs are timestamped and saved to the `outputs/` directory
- Use the Rich console interface for enhanced terminal output

## 🤝 Contributing

1. Follow the existing code structure
2. Add type hints and docstrings
3. Test individual agents before running the full workflow
4. Update documentation for any new features

## 📋 Dependencies

Core dependencies:
- CrewAI: Multi-agent framework
- CrewAI-tools: Additional agent tools
- Rich: Enhanced terminal output
- Pandas: Data manipulation
- NetworkX: Graph analysis for role relationships

## ⚠️ Important Notes

- Ensure your OpenAI API key has sufficient credits
- The workflow runs sequentially by default for data consistency
- Large systems may require extended processing time
- Review generated policies before implementation

## 🔒 Security Considerations

- API keys are loaded from environment variables
- Sensitive data should not be hardcoded
- Generated policies should be reviewed by security professionals
- Follow your organization's data handling policies
