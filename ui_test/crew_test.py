"""
Complete knowledge-based crew test example.
"""
from crewai import Agent, Task, Crew
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
import sys
import os
import boto3

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Initialize LLM
llm = Config.get_bedrock_llm()

# Create knowledge source about AWS IAM best practices
iam_knowledge = StringKnowledgeSource(
    content="""
    AWS IAM Best Practices:
    
    1. Grant Least Privilege:
       - Start with minimum permissions and grant additional permissions as needed
       - Use IAM Access Analyzer to validate policies
       - Regularly review and remove unnecessary permissions
    
    2. Enable MFA (Multi-Factor Authentication):
       - Require MFA for all human users
       - Use MFA for privileged operations
       - Consider hardware MFA for root accounts
    
    3. Use IAM Roles Instead of Long-term Credentials:
       - Use IAM roles for applications running on EC2
       - Use IAM roles for cross-account access
       - Avoid embedding access keys in code
    
    4. Rotate Credentials Regularly:
       - Set up credential rotation policies
       - Remove unused credentials
       - Monitor credential age with IAM credential reports
    
    5. Use Policy Conditions for Extra Security:
       - Restrict access by IP address
       - Require SSL/TLS for API calls
       - Limit access based on time of day
       - Use tags for attribute-based access control
    
    6. Monitor and Audit:
       - Enable CloudTrail for API logging
       - Set up alerts for suspicious activities
       - Regular access reviews and audits
       - Use AWS Config to track configuration changes
    """,
    metadata={"source": "aws_iam_best_practices", "version": "2024"}
)

# Create API documentation knowledge source
api_docs_knowledge = JSONKnowledgeSource(
    file_paths=["Secure Cloud Access APIs.json"],
    metadata={"source": "sca_api_docs", "version": "2024"}
)

# Create a knowledge source about security compliance
compliance_knowledge = StringKnowledgeSource(
    content="""
    Security Compliance Requirements:
    
    SOC 2 Requirements:
    - Access control and authentication mechanisms
    - Logging and monitoring of system activities
    - Regular security assessments and audits
    - Incident response procedures
    - Change management processes
    
    GDPR Requirements:
    - Data minimization principle
    - Right to access, rectification, and erasure
    - Data protection by design and by default
    - Privacy impact assessments
    - Data breach notification within 72 hours
    
    Common Security Controls:
    - Implement role-based access control (RBAC)
    - Encrypt data at rest and in transit
    - Regular security training for staff
    - Vulnerability management program
    - Business continuity and disaster recovery plans
    """,
    metadata={"source": "compliance_frameworks", "version": "2024"}
)

# Create test agent with knowledge
test_agent = Agent(
    embedder={
        "provider": "bedrock",
        "config": {
            "model": "amazon.titan-embed-text-v2:0",
            "session": boto3.Session(region_name="us-east-1")
        }
    },
    role="api payload former",
    goal="Generate accurate API payloads based on provided prompts and knowledge sources",
    backstory="you are an expert in generating API payloads using knowledge bases and best practices.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    knowledge_sources=[api_docs_knowledge]
)

# Create test task
test_task = Task(
    description="""
    Based on the following user request, generate the appropriate API payload(s) using your knowledge base:
    
    User Request: {prompt}
    
    Instructions:
    1. Search your knowledge base for relevant API endpoints
    2. Identify all APIs that match the user's request
    3. Generate complete, valid JSON payloads for each API
    4. Include all required fields and provide example values
    5. Add comments explaining each field's purpose
    6. Ensure the payloads follow the exact structure from the knowledge base
    """,
    agent=test_agent,
    expected_output="""A comprehensive response containing:
    1. List of relevant API endpoints found
    2. Complete JSON payload for each API
    3. Explanation of each payload structure
    4. Example values that make sense for the use case
    
    Format: JSON with explanations"""
)

# Create crew
crew_inside = Crew(
    agents=[test_agent],
    tasks=[test_task],
    verbose=True
)

# Execute crew
print("=" * 80)
print("Starting Knowledge-Based Crew Execution")
print("=" * 80)
print("\nAgent: API Payload Former")
print("Knowledge Sources: Secure Cloud Access APIs")
print("\nExecuting analysis...\n")

# prompt = "give me list of policies response model"
# result = crew_inside.kickoff(inputs={"prompt": prompt})

print("\n" + "=" * 80)
print("Crew Execution Completed")
print("=" * 80)
print("\nResult:")
# print(result)
