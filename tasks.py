"""
Tasks definition for the secure agent flow crew.
"""

from crewai import Task


class SecureAgentFlowTasks:
    """Class containing all tasks for the secure agent flow crew."""

    def fetch_roles_and_details_task(self, agent, context_input=""):
        """
        Task for the Roles and Details Fetcher agent to extract role information.
        """
        return Task(
            description=f"""
            Optimize AWS IAM permissions by analyzing actual usage patterns from CloudTrail events.
            
            MANDATORY WORKFLOW - Execute in this exact order:
            1. **FIRST: Use CloudTrail_Events_Fetcher tool** to gather comprehensive activity data for ALL IAM users
            2. **SECOND: Analyze CloudTrail events** to identify actual permission usage patterns and frequency
            3. **THIRD: Use AWS IAM MCP server tools** to create optimized custom roles based on analysis
            
            Your task includes:
            - Fetch CloudTrail events for all IAM users (the tool is now fixed to 1 day of data)
            - Analyze actual API calls and services used by each user
            - Identify least-privilege permission requirements
            - Detect unused or excessive permissions
            - Create custom IAM roles that match actual usage patterns
            - Document permission optimization recommendations
            
            Context: {context_input}
            
            DO NOT use AWS IAM MCP server tools until CloudTrail analysis is complete.
            ALWAYS include the ctx parameter when calling AWS IAM MCP server tools.
            
            Provide a structured output with:
            - CloudTrail analysis summary for all users
            - Actual vs assigned permissions comparison
            - Optimized custom role definitions
            - Implementation recommendations
            """,
            agent=agent,
            expected_output="""A comprehensive AWS IAM optimization report containing:
            1. CloudTrail Events Analysis Summary
               - Total events analyzed per user
               - Most frequently used AWS services and actions
               - Time-based usage patterns
            
            2. Permission Usage Analysis
               - Current permissions vs actual usage comparison
               - Unused permissions identification
               - Over-privileged accounts detection
            
            3. Custom Role Definitions
               - Least-privilege role specifications
               - Role-to-user mapping recommendations
               - Permission boundaries and policies
            
            
            Format: Structured JSON report with actionable recommendations"""
        )


    def create_mapping_task(self, agent):
        """
        Task for the Mapping agent to create relationship mappings.
        """
        return Task(
            description="""
            Create comprehensive mappings between roles, permissions, and resources based on the fetched data.
            
            Your task includes:
            1. Map roles to specific permissions
            2. Create resource access matrices
            3. Identify permission overlaps and conflicts
            4. Map role inheritance and delegation patterns
            5. Create visual relationship diagrams
            6. Identify potential security gaps or excessive permissions
            7. Document cross-role dependencies
            
            Use the output from the Roles and Details Fetcher agent as your primary input.
            
            Focus on:
            - Clear relationship visualization
            - Conflict identification
            - Gap analysis
            - Optimization opportunities
            """,
            agent=agent,
            expected_output="""A comprehensive mapping document containing:
            1. Role-to-permission mapping matrix
            2. Resource access control matrix
            3. Role hierarchy visualization
            4. Conflict and overlap analysis
            5. Security gap identification
            6. Permission optimization recommendations
            7. Cross-role dependency mapping
            
            Format: Structured diagrams, matrices, and analysis report"""
        )

    def prepare_data_task(self, agent):
        """
        Task for the Prepare agent to structure and validate the mapped data.
        """
        return Task(
            description="""
            Structure, validate, and organize the mapped role and permission data for policy creation.
            
            Your task includes:
            1. Validate data consistency and completeness
            2. Structure data according to policy framework requirements
            3. Organize information by business functions and security domains
            4. Create standardized role and permission definitions
            5. Prepare compliance mapping templates
            6. Identify policy creation priorities
            7. Structure data for automated policy generation
            
            Use the mapping output as your primary input and ensure:
            - Data quality and consistency
            - Compliance framework alignment
            - Policy generation readiness
            - Clear categorization and prioritization
            """,
            agent=agent,
            expected_output="""A structured and validated dataset containing:
            1. Standardized role definitions
            2. Normalized permission structures
            3. Business function categorization
            4. Security domain organization
            5. Compliance framework mapping
            6. Policy creation roadmap
            7. Data quality validation report
            
            Format: Structured templates and validated datasets ready for policy creation"""
        )

    def create_policy_task(self, agent, policy_requirements=""):
        """
        Task for the Policy Creator agent to generate comprehensive security policies.
        """
        return Task(
            description=f"""
            Generate comprehensive, compliant, and implementable security policies based on the prepared data.
            
            Your task includes:
            1. Create role-based access control (RBAC) policies
            2. Generate permission assignment policies
            3. Develop access review and certification procedures
            4. Create role lifecycle management policies
            5. Design segregation of duties policies
            6. Develop incident response procedures for access violations
            7. Create compliance monitoring and reporting policies
            
            Requirements: {policy_requirements}
            
            Ensure policies are:
            - Aligned with industry standards and frameworks
            - Implementable with existing systems
            - Clear and actionable
            - Compliant with relevant regulations
            - Scalable and maintainable
            """,
            agent=agent,
            expected_output="""A complete security policy suite containing:
            1. Role-Based Access Control (RBAC) Policy
            2. Permission Assignment and Management Policy
            3. Access Review and Certification Procedures
            4. Role Lifecycle Management Policy
            5. Segregation of Duties Policy
            6. Access Violation Incident Response Procedures
            7. Compliance Monitoring and Reporting Policy
            8. Implementation guidelines and timelines
            
            Format: Professional policy documents with clear procedures, responsibilities, and compliance requirements"""
        )
