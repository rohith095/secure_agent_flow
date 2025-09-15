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
            Analyze the provided system or documentation to extract comprehensive role and permission details.
            
            Your task includes:
            1. Identify all user roles present in the system
            2. Extract detailed permissions for each role
            3. Document access levels and restrictions
            4. Identify role hierarchies and inheritance patterns
            5. Note any special access conditions or temporary permissions
            6. Document role assignment criteria and processes
            
            Context: {context_input}
            
            Provide a structured output with:
            - Complete list of roles with descriptions
            - Detailed permissions matrix
            - Access level documentation
            - Role hierarchy mapping
            - Special conditions and exceptions
            """,
            agent=agent,
            expected_output="""A comprehensive report containing:
            1. Roles inventory with detailed descriptions
            2. Permissions matrix showing role-to-permission mappings
            3. Access level documentation (read, write, admin, etc.)
            4. Role hierarchy structure
            5. Special access conditions and exceptions
            6. Role assignment criteria and processes
            
            Format: Structured JSON or detailed markdown report"""
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
