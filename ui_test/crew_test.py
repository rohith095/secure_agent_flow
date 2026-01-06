"""
Complete knowledge-based crew test example.
"""
from crewai import Agent, Task, Crew
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
import sys
import os

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
    role="Security Compliance Analyst",
    goal="Analyze AWS IAM configurations and provide recommendations based on security best practices and compliance requirements",
    backstory="""You are an experienced security analyst specializing in cloud infrastructure
    security and compliance. You have deep knowledge of AWS IAM best practices and various
    compliance frameworks including SOC 2 and GDPR. You excel at identifying security gaps
    and providing actionable recommendations that balance security with operational needs.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    knowledge_sources=[iam_knowledge, compliance_knowledge]
)

# Create test task
test_task = Task(
    description="""
    Analyze the following AWS IAM scenario and provide security recommendations:
    
    Scenario:
    A development team has been using shared IAM user credentials with full administrator access
    for deploying applications to production EC2 instances. The credentials are rotated manually
    every 6 months. There's no MFA enabled, and the team accesses AWS from various locations.
    The company needs to achieve SOC 2 compliance.
    
    Your analysis should include:
    1. Identify security risks in the current setup
    2. Provide specific recommendations based on AWS IAM best practices
    3. Explain how to align with SOC 2 compliance requirements
    4. Suggest an implementation roadmap with priorities
    
    Use your knowledge base extensively to support your recommendations with specific
    best practices and compliance requirements.
    """,
    agent=test_agent,
    expected_output="""A comprehensive security analysis report containing:
    
    1. Risk Assessment
       - List of identified security risks with severity ratings
       - Potential impact of each risk
    
    2. Best Practice Violations
       - Specific AWS IAM best practices being violated
       - References from knowledge base
    
    3. Compliance Gaps
       - SOC 2 requirements not being met
       - Specific controls needed
    
    4. Recommendations
       - Prioritized list of actionable recommendations
       - Implementation steps for each recommendation
       - Expected security improvements
    
    5. Implementation Roadmap
       - Phase 1 (Immediate): Critical security fixes
       - Phase 2 (Short-term): Important improvements
       - Phase 3 (Long-term): Optimization and automation
    
    Format: Clear, structured report with specific action items"""
)

# Create crew
crew = Crew(
    agents=[test_agent],
    tasks=[test_task],
    verbose=True
)

# Execute crew
print("=" * 80)
print("Starting Knowledge-Based Crew Execution")
print("=" * 80)
print("\nAgent: Security Compliance Analyst")
print("Knowledge Sources: AWS IAM Best Practices, Security Compliance Requirements")
print("\nExecuting analysis...\n")

result = crew.kickoff()

print("\n" + "=" * 80)
print("Crew Execution Completed")
print("=" * 80)
print("\nResult:")
print(result)

