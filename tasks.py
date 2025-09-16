"""
Tasks definition for the secure agent flow crew.
"""

from crewai import Task


class SecureAgentFlowTasks:
    """Class containing all tasks for the secure agent flow crew."""

    def fetch_roles_and_details_task(self, agent, context_input="", customer_account_id=None):
        """
        Task for the Roles and Details Fetcher agent to extract role information from customer account.
        """
        return Task(
            description=f"""
            Optimize AWS IAM permissions by analyzing actual usage patterns from CloudTrail events in customer account.
            
            MANDATORY WORKFLOW - Execute in this exact order:
            1. **FIRST: Use CloudTrail_Events_Fetcher tool** with cross-account parameters:
               - customer_account_id: {customer_account_id or "REQUIRED - Customer AWS Account ID"}
               - cross_account_role_name: "CyberArkRoleSCA-6c116dd0-9300-11f0-bd68-0e66c6d684e1" (or specified role name)
               - external_id: Optional external ID for additional security
            2. **SECOND: Analyze CloudTrail events** to identify actual permission usage patterns and frequency
            3. **THIRD: Use AWS Role Creator tool** with cross-account parameters to create optimized custom roles in customer account
            
            Your task includes:
            - Assume cross-account role to access customer AWS account
            - Fetch CloudTrail events for all IAM users in customer account (10 hours of data)
            - Analyze actual API calls and services used by each user
            - Identify least-privilege permission requirements
            - Detect unused or excessive permissions
            - Create custom IAM roles in the CUSTOMER ACCOUNT that match actual usage patterns
            - Document permission optimization recommendations
            
            Context: {context_input}
            Customer Account ID: {customer_account_id}
            
            CRITICAL REQUIREMENTS:
            - ALWAYS provide customer_account_id parameter to both tools
            - All operations must be performed in the customer account via cross-account role assumption
            - Custom roles MUST be created in the customer account, not the management account
            - Include cross-account information in all outputs
            
            Provide a structured output with:
            - Cross-account role assumption status
            - CloudTrail analysis summary for all users in customer account
            - Actual vs assigned permissions comparison
            - Optimized custom role definitions created in customer account
            - Implementation recommendations
            """,
            agent=agent,
            expected_output="""A comprehensive AWS IAM optimization report containing:
            1. Cross-Account Access Summary
               - Customer account ID accessed
               - Role assumption success/failure status
               - Assumed role ARN details
            
            2. CloudTrail Events Analysis Summary
               - Total events analyzed per user in customer account
               - Most frequently used AWS services and actions
               - Time-based usage patterns
            
            3. Permission Usage Analysis
               - Current permissions vs actual usage comparison
               - Unused permissions identification
               - Over-privileged accounts detection
            
            4. Custom Role Definitions
               - Least-privilege role specifications
               - Role-to-user mapping recommendations
               - Permission boundaries and policies
            
            5. **CREATED_CUSTOM_ROLES** (CRITICAL for policy creation):
               - Role ARNs: List of all custom role ARNs created in customer account (format: arn:aws:iam::CUSTOMER_ACCOUNT_ID:role/ROLE_NAME)
               - Account IDs: Customer account ID for all created roles
               - Role Names: Names of the custom roles created
               - Cross-Account Info: Details about role assumption and creation
               - Example format:
                 {
                   "created_roles": [
                     {
                       "role_arn": "arn:aws:iam::CUSTOMER_ACCOUNT_ID:role/OptimizedRole1",
                       "account_id": "CUSTOMER_ACCOUNT_ID",
                       "role_name": "OptimizedRole1",
                       "created_in_customer_account": true
                     }
                   ],
                   "cross_account_info": {
                     "customer_account_id": "CUSTOMER_ACCOUNT_ID",
                     "role_assumption_success": true,
                     "assumed_role": "arn:aws:iam::CUSTOMER_ACCOUNT_ID:role/CrossAccountAccessRole"
                   }
                 }
            
            Format: Structured JSON report with actionable recommendations, cross-account details, and CREATED_CUSTOM_ROLES section for policy creation"""
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

    def create_policy_task(self, agent, policy_requirements="", fetch_context=""):
        """
        Task for the Policy Creator agent to generate comprehensive security policies.
        """
        return Task(
            description=f"""
            Generate comprehensive, compliant, and implementable security policies based on the prepared data.
            
            CONTEXT FROM ROLES AND DETAILS ANALYSIS:
            {fetch_context}
            
            Your task includes:
            1. **FIRST: Call rescan to get recently created roles** - Use the CyberArk SCA Tool with action='rescan' to scan for recently created roles by the roles_and_details_fetcher_agent
            2. **Extract custom roles from the CloudTrail analysis results** - Look for role ARNs created by the fetch task
            3. **Prepare the policy payload** in the following exact format:
               {{
                 "csp": "AWS",
                 "name": "optimized_policy_v1",
                 "description": "Policy based on CloudTrail analysis for least-privilege access",
                 "startDate": null,
                 "endDate": null,
                 "policyType": "pre_defined",
                 "roles": [
                   {{
                     "entityId": "<ROLE_ARN_FROM_ANALYSIS>",
                     "workspaceType": "account",
                     "entitySourceId": "<ACCOUNT_ID_FROM_ROLE_ARN>"
                   }}
                 ],
                 "identities": [
                   {{
                     "entityName": "naveen_kumar_bontu@cyberark.cloud.55567",
                     "entitySourceId": "09B9A9B0-6CE8-465F-AB03-65766D33B05E",
                     "entityClass": "user"
                   }}
                 ],
                 "accessRules": {{
                   "days": [
                     "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
                   ],
                   "fromTime": null,
                   "toTime": null,
                   "maxSessionDuration": 1,
                   "timeZone": "Asia/Jerusalem"
                 }}
               }}
            
            4. **Use the CyberArk SCA Tool** to create the actual policy with action='create_policy' and the prepared payload
            5. **IMPORTANT**: Replace the roles array with the custom roles created in the fetch task analysis and discovered via rescan
            6. **Extract the account ID** from the role ARN for the entitySourceId field
            
            Requirements: {policy_requirements}
            
            MANDATORY STEPS:
            1. **RESCAN FIRST**: Call CyberArk SCA Tool with action='rescan' to get recently created roles
            2. Parse the fetch context to find custom role ARNs created during CloudTrail analysis
            3. For each role ARN, extract the account ID (the number after arn:aws:iam::)
            4. Create the policy payload with the custom roles in the roles array
            5. Call the CyberArk SCA Tool with action='create_policy' and the prepared payload
            6. Include the policy creation results in your output
            
            **CRITICAL**: 
            - ALWAYS call rescan before creating policies to ensure the latest roles are available
            - Only change the "roles" array in the payload template. Keep all other fields exactly as shown in the template above.
            """,
            agent=agent,
            expected_output="""A complete security policy implementation containing:
            1. **Rescan Results** - Response from the rescan operation showing recently discovered roles
            2. **Extracted Custom Roles** - List of role ARNs found in the CloudTrail analysis and rescan results
            3. **Policy Payload** - The exact JSON payload used for policy creation
            4. **CyberArk SCA Policy Creation Results** - Response from the SCA tool showing successful policy creation
            5. **Account ID Mapping** - Mapping of role ARNs to their account IDs
            6. **Implementation Summary** - Summary of the policy created and its configuration
            
            Format: Structured report with the rescan results, policy payload, SCA tool results, and implementation details"""
        )
