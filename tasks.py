"""
Tasks definition for the secure agent flow crew.
"""
import os

from crewai import Task

from websocket_handler import send_message_to_connection


def send_to_websocket(message):
    """Placeholder function to send messages to a WebSocket."""
    # Implement WebSocket sending logic here
    send_message_to_connection(connection_id=os.environ['WEBSOCKET_CONNECTION_ID'], message=message)
    print(f"WebSocket message: {message}")


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
               - cross_account_role_name: "CyberArkRoleSCA-3436d390-d01e-11f0-91ee-0e1617ad5923" (or specified role name)
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

            Format: Structured JSON report with actionable recommendations, cross-account details, and CREATED_CUSTOM_ROLES section for policy creation""",
            callback=send_to_websocket
        )


    def generate_policy_payload_task(self, agent, fetch_context=""):
        """
        Task for the Payload Generator agent to create policy creation payloads dynamically.
        """
        return Task(
            description=f"""
            Generate valid JSON payload(s) for creating CyberArk SCA policies based on the analyzed data.
            
            CONTEXT FROM PREVIOUS TASKS:
            {fetch_context}
            
            Your task includes:
            1. **Extract Key Information** from the context:
               - Created identity user names and their details
               - Custom role ARNs created in the customer account
               - Account IDs from the role ARNs
               - IAM username to identity user mapping
            
            2. **Search Knowledge Base** for the correct API payload structure:
               - Look for "create policy" or "post-policies" endpoint
               - Understand the exact schema for AWS IAM policy creation
               - Identify all required and optional fields
            
            3. **Generate Complete Policy Payload(s)** following this structure:
               - Use "AWS" as the csp (cloud service provider)
               - Create descriptive policy names like: "optimized_policy_<iam_username>_v1"
               - Set policyType to "pre_defined"
               - Map custom role ARNs to the roles array with:
                 * entityId: the complete role ARN
                 * workspaceType: "account"
                 * entitySourceId: the account ID extracted from the role ARN
               - Map created identity users to the identities array with:
                 * entityName: the created identity user name
                 * entitySourceId: "09B9A9B0-6CE8-465F-AB03-65766D33B05E"
                 * entityClass: "user"
               - Set accessRules with:
                 * days: all days of the week
                 * fromTime: null
                 * toTime: null
                 * maxSessionDuration: 1
                 * timeZone: "Asia/Jerusalem"
            
            4. **Create One Payload per IAM User-Role Combination** to ensure proper mapping
            
            5. **Validate the Payload** against the knowledge base schema to ensure all required fields are present
            
            CRITICAL REQUIREMENTS:
            - Generate valid JSON that exactly matches the API schema from your knowledge base
            - Extract account IDs from role ARNs (the numeric part after arn:aws:iam::)
            - Use the CREATED identity user names from the context, not placeholder values
            - Ensure each payload is complete and ready to be sent to the API
            - Output ONLY the JSON payload(s), no additional text or markdown formatting
            """,
            agent=agent,
            expected_output="""One or more complete, valid JSON payloads for policy creation. Each payload should be a complete JSON object following the CyberArk SCA create policy API schema.

Example format:
{
  "csp": "AWS",
  "name": "optimized_policy_user1_v1",
  "description": "Policy based on CloudTrail analysis for least-privilege access",
  "startDate": null,
  "endDate": null,
  "policyType": "pre_defined",
  "roles": [
    {
      "entityId": "arn:aws:iam::123456789012:role/CustomRole1",
      "workspaceType": "account",
      "entitySourceId": "123456789012"
    }
  ],
  "identities": [
    {
      "entityName": "user1@cyberark.cloud.18917",
      "entitySourceId": "09B9A9B0-6CE8-465F-AB03-65766D33B05E",
      "entityClass": "user"
    }
  ],
  "accessRules": {
    "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "fromTime": null,
    "toTime": null,
    "maxSessionDuration": 1,
    "timeZone": "Asia/Jerusalem"
  }
}

If multiple IAM users exist, provide multiple complete JSON objects separated by newlines.""",
            callback=send_to_websocket
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
            
            Format: Structured diagrams, matrices, and analysis report""",
            callback=send_to_websocket

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
            
            Format: Structured templates and validated datasets ready for policy creation""",
            callback=send_to_websocket

        )

    def create_policy_task(self, agent, policy_requirements="", fetch_context="", customer_account_id=None):
        """
        Task for the Policy Creator agent to generate comprehensive security policies.
        """
        return Task(
            description=f"""
            Generate comprehensive, compliant, and implementable security policies based on the prepared data.
            
            CONTEXT FROM ROLES AND DETAILS ANALYSIS:
            {fetch_context}
            
            CUSTOMER ACCOUNT ID: {customer_account_id}
            
            Your task includes:
            1. **FIRST: Call rescan to get recently created roles** - Use the CyberArk SCA Tool with action='rescan' to scan for recently created roles by the roles_and_details_fetcher_agent
            2. **SECOND: Extract IAM user and role mapping** from the fetch context and rescan results
            3. **THIRD: Create identity users for each IAM user** - Use CyberArk SCA Tool with action='create_identity_user' for each IAM user found in the analysis. 
               IMPORTANT: Pass customer_account_id='{customer_account_id}' to access secrets in the customer account
            4. **FOURTH: Extract custom roles from the CloudTrail analysis results** - Look for role ARNs created by the fetch task
            5. **FIFTH: Prepare the policy payload** with the dynamically created identity users and custom roles
            6. **SIXTH: Use the CyberArk SCA Tool** to create the actual policy with action='create_policy' and the prepared payload
            
            MANDATORY STEPS FOR IDENTITY USER CREATION AND POLICY CREATION:
            1. **RESCAN FIRST**: Call CyberArk SCA Tool with action='rescan' to get recently created roles
            2. **Extract IAM user details** from fetch context and identify the iam_user_role_mapping section
            3. **Create identity users**: For each IAM user found, call CyberArk SCA Tool with action='create_identity_user' using this payload format:
               {{
                 "action": "create_identity_user",
                 "identity_payload": {{
                   "Name": "<IAM_USERNAME>@cyberark.cloud.18917",
                   "Mail": "<IAM_USER_EMAIL>",
                   "Password": "abcD1234",
                   "InEverybodyRole": True,
                   "InSysAdminRole": False
                 }},
                 "customer_account_id": "{customer_account_id}"
               }}
               Where <IAM_USERNAME> is replaced with the actual IAM username and <IAM_USER_EMAIL> with the user's email
               CRITICAL: Always pass customer_account_id to access secrets from customer account via cross-account role
            4. **Extract the dynamically generated policy payload(s)** from the generate_payload_task output
            5. **Verify the payload structure**: Ensure the generated payload has all required fields:
               - csp, name, description, policyType
               - roles array with entityId, workspaceType, entitySourceId
               - identities array with created identity user names
               - accessRules with days, maxSessionDuration, timeZone
            6. **Create separate policies** for each generated payload
            7. **Call the CyberArk SCA Tool** with action='create_policy' for each policy payload
            8. **Extract policy ID** from each policy creation response (look for 'policyId' or 'policy_id' in the response)
            9. **Verify created policies**: For each created policy, call CyberArk SCA Tool with action='get_policy' and the extracted policy_id to retrieve and verify the policy details
            10. **Document verification results**: Include the complete policy details from the get_policy API to confirm the policy was created correctly
            
            Requirements: {policy_requirements}
            
            **CRITICAL REQUIREMENTS**: 
            - ALWAYS call rescan before creating identity users and policies
            - Create identity users BEFORE creating policies
            - Maintain proper mapping between IAM users, identity users, and custom roles
            - Create one policy per IAM user-role combination for precise access control
            - Use the created identity user details in the policy identities array
            - Extract account IDs from role ARNs for the entitySourceId field in roles array
            - Generate unique policy names for each user using pattern: optimized_policy_<iam_username>_v1
            """,
            agent=agent,
            expected_output="""A complete security policy implementation containing:
            1. **Rescan Results** - Response from the rescan operation showing recently discovered roles
            2. **IAM User-Role Mapping** - Extracted mapping from fetch context showing IAM users and their associated custom roles
            3. **Identity User Creation Results** - Results from creating identity users for each IAM user with the following format:
               - IAM Username: original IAM username
               - Created Identity Name: <iam_username>@cyberark.cloud.55567
               - Associated Custom Role: ARN of the custom role for this user
            4. **Generated Policy Payloads** - The dynamically generated JSON payloads from the generate_payload_task (must include entitySourceId for identities)
            5. **CyberArk SCA Policy Creation Results** - Response from the SCA tool showing successful policy creation for each user-role combination, including:
               - Job IDs for tracking
               - Policy IDs for each created policy
               - Final job status (success/failure)
            6. **Policy Verification Results** - Results from calling get_policy API for each created policy, containing:
               - Policy ID used for retrieval
               - Complete policy details retrieved from the API
               - Verification status (success/failure)
               - Policy metadata (name, description, status, etc.)
               - Policy configuration (roles, identities, access rules)
            7. **User-Role-Policy Mapping** - Complete mapping showing:
               - IAM Username
               - Created Identity User Name and ID
               - Associated Custom Role ARN
               - Created Policy ID and Name
               - Policy verification status
            8. **Implementation Summary** - Summary of all policies created, verified, and their configurations
            
            Format: Professional policy documents with clear procedures, responsibilities, and compliance requirements""",
            callback=send_to_websocket
        )
