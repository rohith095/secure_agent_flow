"""
Agents definition for the secure agent flow crew.
"""
import os
import boto3

from crewai import Agent
from crewai_tools.adapters.mcp_adapter import MCPServerAdapter
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource

from config import Config
from custom_tools.custom_role_creator import AWSRoleCreator
from custom_tools.role_fetcher import CloudTrailEventsFetcher
from mcp import StdioServerParameters

from custom_tools.sca_tool import SCATool


class SecureAgentFlowAgents:
    """Class containing all agents for the secure agent flow crew."""

    def __init__(self):
        """Initialize the agents class with Bedrock LLM."""
        self.llm = Config.get_bedrock_llm()

    def roles_and_details_fetcher_agent(self):
        """
        Agent responsible for optimizing AWS IAM permissions by analyzing CloudTrail events
        and creating least-privilege custom roles.
        """

        return Agent(
            role="Roles and Details Fetcher",
            goal="Identify and extract comprehensive role definitions, permissions, and access details from various sources",
            backstory="""You are an expert in identity and access management with deep knowledge of 
            role-based access control (RBAC) systems. You excel at analyzing systems, documentation,
            and configurations to extract detailed information about user roles, their permissions,
            and access patterns.""",
            verbose=True,
            tools=[CloudTrailEventsFetcher(),AWSRoleCreator()],
            allow_delegation=False,
            llm=self.llm
        )

    def mapping_agent(self):
        """
        Agent responsible for mapping relationships between roles, permissions, and resources.
        """
        return Agent(
            role="Mapping Agent",
            goal="Create comprehensive mappings between roles, permissions, resources, and identify relationships and potential conflicts",
            backstory="""You are a systems analyst specialized in access control mapping and 
            relationship modeling. You have extensive experience in creating visual and logical 
            mappings of complex permission structures, identifying overlaps, conflicts, and gaps 
            in access control systems.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def prepare_agent(self):
        """
        Agent responsible for preparing and structuring data for policy creation.
        """
        return Agent(
            role="Data Preparation Agent",
            goal="Structure and prepare collected role and permission data for comprehensive policy creation",
            backstory="""You are a data analyst with expertise in information architecture and 
            policy documentation. You specialize in organizing complex access control data into 
            structured formats that can be used for creating clear, actionable security policies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def payload_generator_agent(self):
        """
        Agent responsible for generating API payloads based on knowledge base.
        """
        # Create API documentation knowledge source
        # CrewAI looks for files in a 'knowledge/' directory relative to where the script runs
        api_docs_knowledge = JSONKnowledgeSource(
            file_paths=["Secure Cloud Access APIs.json"],
            metadata={"source": "sca_api_docs", "version": "2024"}
        )
        
        return Agent(
            embedder={
                "provider": "bedrock",
                "config": {
                    "model": "amazon.titan-embed-text-v2:0",
                    "session": boto3.Session(region_name="us-east-1")
                }

            },
            role="API Payload Generator",
            goal="Generate accurate and valid API payloads based on CyberArk API schema and provided context",
            backstory="""You are an expert in generating API payloads using knowledge bases and API schemas. 
            You understand the CyberArk Secure Cloud Access API structure and can create valid, 
            well-formed JSON payloads that match the API specifications exactly. You excel at 
            extracting information from context and mapping it to the correct API payload structure.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            knowledge_sources=[api_docs_knowledge]
        )

    def policy_creator_agent(self):
        """
        Agent responsible for creating comprehensive security policies.
        """
        return Agent(
            role="Security Policy Creator",
            goal="Generate comprehensive, compliant security policies based on organizational roles and requirements",
            backstory="""You are a cybersecurity expert and policy architect with extensive 
            experience in creating enterprise security policies. You understand compliance 
            frameworks like SOX, GDPR, HIPAA, and can translate technical access controls 
            into clear, actionable policies that meet regulatory requirements.""",
            verbose=True,
            tools= [SCATool()],
            allow_delegation=False,
            llm=self.llm
        )
