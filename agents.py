"""
Agents definition for the secure agent flow crew.
"""

from crewai import Agent


class SecureAgentFlowAgents:
    """Class containing all agents for the secure agent flow crew."""

    def roles_and_details_fetcher_agent(self):
        """
        Agent responsible for fetching roles and details from various sources.
        """
        return Agent(
            role="Roles and Details Fetcher",
            goal="Identify and extract comprehensive role definitions, permissions, and access details from various sources",
            backstory="""You are an expert in identity and access management with deep knowledge of 
            role-based access control (RBAC) systems. You excel at analyzing systems, documentation, 
            and configurations to extract detailed information about user roles, their permissions, 
            and access patterns.""",
            verbose=True,
            allow_delegation=False
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
            allow_delegation=False
        )

    def prepare_agent(self):
        """
        Agent responsible for preparing and organizing data for policy creation.
        """
        return Agent(
            role="Prepare Agent",
            goal="Structure, validate, and organize mapped role and permission data for optimal policy creation",
            backstory="""You are a data preparation specialist with expertise in security policy 
            frameworks and governance structures. You excel at taking complex, mapped security data 
            and organizing it into structured formats that enable effective policy creation.""",
            verbose=True,
            allow_delegation=False
        )

    def policy_creator_agent(self):
        """
        Agent responsible for creating comprehensive security policies.
        """
        return Agent(
            role="Policy Creator",
            goal="Generate comprehensive, compliant, and implementable security policies based on structured role and permission data",
            backstory="""You are a senior security policy architect with deep expertise in 
            regulatory compliance, security frameworks (like NIST, ISO 27001, SOC 2), and 
            enterprise governance. You specialize in translating technical access control 
            requirements into clear, actionable policies.""",
            verbose=True,
            allow_delegation=False
        )
