"""
Custom tool for creating AWS IAM custom roles with cross-account support.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from tasks import send_to_websocket


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class AWSRoleCreatorInput(BaseModel):
    """Input schema for AWS Role Creator tool."""
    role_name: str = Field(..., description="Name of the IAM role to create")
    trust_policy: Dict[str, Any] = Field(..., description="Trust policy for the role")
    permission_policies: List[Dict[str, Any]] = Field(..., description="List of permission policies to attach")
    description: Optional[str] = Field(default=None, description="Description for the role")
    max_session_duration: int = Field(default=3600, description="Maximum session duration in seconds")
    customer_account_id: Optional[str] = Field(default=None, description="Customer AWS account ID to assume role into")
    cross_account_role_name: Optional[str] = Field(default="CyberArkRoleSCA-6c116dd0-9300-11f0-bd68-0e66c6d684e1", description="Role name to assume in customer account")
    external_id: Optional[str] = Field(default=None, description="External ID for cross-account role assumption")


class AWSRoleCreator(BaseTool):
    """Tool for creating AWS IAM custom roles with specified permissions and cross-account support."""

    name: str = "AWS Role Creator"
    description: str = """
    Creates AWS IAM custom roles with specified trust policies and permission policies.
    Supports cross-account role creation by assuming a role in the customer account.
    Use this tool to create new IAM roles based on analyzed CloudTrail events and 
    least-privilege requirements in customer AWS accounts.
    """
    args_schema: type[BaseModel] = AWSRoleCreatorInput

    # Declare all fields
    aws_profile: str = "default"
    aws_region: str = "us-east-1"
    logger: Optional[logging.Logger] = None
    session: Optional[boto3.Session] = None
    iam_client: Optional[Any] = None

    def __init__(self, aws_profile: str = "default", aws_region: str = "us-east-1"):
        """Initialize the AWS Role Creator tool."""
        super().__init__(
            aws_profile=aws_profile,
            aws_region=aws_region,
            logger=logging.getLogger(__name__)
        )

        # Initialize boto3 session
        try:
            self.session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
            self.iam_client = self.session.client('iam')
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS session: {e}")
            raise

    def _assume_cross_account_role(self, customer_account_id: str, role_name: str, external_id: Optional[str] = None):
        """Assume a cross-account role and return the assumed role session."""
        role_arn = f"arn:aws:iam::{customer_account_id}:role/{role_name}"
        try:
            # Create STS client
            sts_client = boto3.client('sts')

            # Prepare assume role parameters
            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': f'RoleCreator-{datetime.now().strftime("%Y%m%d%H%M%S")}'
            }

            # Add external ID if provided
            if external_id:
                assume_role_params['ExternalId'] = external_id

            # Assume the role
            response = sts_client.assume_role(**assume_role_params)

            # Extract credentials
            credentials = response['Credentials']

            # Create session with assumed role credentials
            assumed_session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            return {
                "session": assumed_session,
                "account_id": customer_account_id,
                "role_arn": role_arn,
                "error": None
            }

        except ClientError as e:
            error_msg = f"Failed to assume cross-account role {role_arn}: {str(e)}"
            return {
                "session": None,
                "account_id": customer_account_id,
                "role_arn": role_arn,
                "error": error_msg
            }

    def _run(self,
             role_name: str,
             trust_policy: Dict[str, Any],
             permission_policies: List[Dict[str, Any]],
             description: Optional[str] = None,
             max_session_duration: int = 3600,
             customer_account_id: Optional[str] = None,
             cross_account_role_name: str = "CyberArkRoleSCA-6c116dd0-9300-11f0-bd68-0e66c6d684e1",
             external_id: Optional[str] = None) -> str:
        """
        Create an AWS IAM custom role with specified policies in customer account via cross-account access.
        """
        try:
            # Validate inputs
            if not role_name:
                return json.dumps({"error": "Role name is required"})

            if not trust_policy:
                return json.dumps({"error": "Trust policy is required"})

            if not permission_policies or len(permission_policies) == 0:
                return json.dumps({"error": "At least one permission policy is required"})

            # Validate and fix MaxSessionDuration - AWS minimum is 3600 seconds (1 hour)
            if max_session_duration < 3600:
                self.logger.warning(f"MaxSessionDuration {max_session_duration} is below AWS minimum of 3600 seconds. Setting to 3600.")
                max_session_duration = 3600
            elif max_session_duration > 43200:  # AWS maximum is 12 hours
                self.logger.warning(f"MaxSessionDuration {max_session_duration} is above AWS maximum of 43200 seconds. Setting to 43200.")
                max_session_duration = 43200

            # Initialize IAM client (default or cross-account)
            iam_client = self.iam_client
            session_info = {"cross_account": False}

            # If customer account ID is provided, assume cross-account role
            if customer_account_id:
                assume_result = self._assume_cross_account_role(
                    customer_account_id, cross_account_role_name, external_id
                )

                if assume_result["error"]:
                    return json.dumps({
                        "error": assume_result["error"],
                        "cross_account_info": {
                            "customer_account_id": customer_account_id,
                            "role_assumption_success": False
                        }
                    })

                # Use assumed session
                iam_client = assume_result["session"].client('iam')
                session_info = {
                    "cross_account": True,
                    "customer_account_id": customer_account_id,
                    "assumed_role": assume_result["role_arn"],
                    "role_assumption_success": True
                }

            # Check if role already exists
            try:
                existing_role = iam_client.get_role(RoleName=role_name)
                # Optimization: If role exists, return its details and do not recreate or attach policies
                return json.dumps({
                    "status": "already_exists",
                    "role_name": role_name,
                    "role_arn": existing_role['Role']['Arn'],
                    "role_details": existing_role['Role'],
                    "cross_account_info": session_info,
                    "message": f"Role '{role_name}' already exists in account {customer_account_id if customer_account_id else 'local'}"
                }, indent=2, cls=DateTimeEncoder)
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    return json.dumps({
                        "error": f"Error checking existing role: {str(e)}",
                        "cross_account_info": session_info
                    })

            # Create the role
            create_role_params = {
                'RoleName': role_name,
                'AssumeRolePolicyDocument': json.dumps(trust_policy, cls=DateTimeEncoder),
                'Path': '/',
                'MaxSessionDuration': max_session_duration
            }

            if description:
                create_role_params['Description'] = description

            role_response = iam_client.create_role(**create_role_params)
            role_arn = role_response['Role']['Arn']

            self.logger.info(f"Successfully created role: {role_name} in account {customer_account_id if customer_account_id else 'local'}")

            # Attach permission policies
            attached_policies = []
            for i, policy in enumerate(permission_policies):
                policy_name = f"{role_name}Policy{i+1}"

                try:
                    iam_client.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(policy, cls=DateTimeEncoder)
                    )
                    attached_policies.append(policy_name)
                    self.logger.info(f"Attached policy {policy_name} to role {role_name}")

                except ClientError as e:
                    self.logger.error(f"Failed to attach policy {policy_name}: {e}")
                    continue

            # Prepare result summary
            result = {
                "status": "success",
                "role_name": role_name,
                "role_arn": role_arn,
                "attached_policies": attached_policies,
                "total_policies_attached": len(attached_policies),
                "message": f"Successfully created role '{role_name}' with {len(attached_policies)} policies",
                "cross_account_info": session_info,
                "created_in_account": customer_account_id if customer_account_id else "local"
            }

            return json.dumps(result, indent=2, cls=DateTimeEncoder)

        except ClientError as e:
            error_msg = f"AWS IAM Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
            self.logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "cross_account_info": session_info if 'session_info' in locals() else {"cross_account": False}
            })

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "cross_account_info": session_info if 'session_info' in locals() else {"cross_account": False}
            })

    def create_least_privilege_role(self,
                                  role_name: str,
                                  service_principals: List[str],
                                  actions: List[str],
                                  resources: List[str],
                                  conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Helper method to create a least-privilege role based on analyzed CloudTrail events.

        Args:
            role_name: Name of the role
            service_principals: List of AWS services that can assume this role
            actions: List of IAM actions the role should have
            resources: List of resources the role can access
            conditions: Optional conditions for the policies

        Returns:
            String with creation status
        """
        # Create trust policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": service_principals
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        # Create permission policy
        permission_statement = {
            "Effect": "Allow",
            "Action": actions,
            "Resource": resources
        }

        if conditions:
            permission_statement["Condition"] = conditions

        permission_policy = {
            "Version": "2012-10-17",
            "Statement": [permission_statement]
        }

        return self._run(
            role_name=role_name,
            trust_policy=trust_policy,
            permission_policies=[permission_policy],
            description=f"Least-privilege role created from CloudTrail analysis"
        )

    def create_least_privilege_role_from_events(self,
                                              role_name: str,
                                              cloudtrail_events: List[Dict[str, Any]],
                                              customer_account_id: Optional[str] = None,
                                              cross_account_role_name: str = "CyberArkRoleSCA-6c116dd0-9300-11f0-bd68-0e66c6d684e1",
                                              external_id: Optional[str] = None) -> str:
        """
        Create a least-privilege role based on analyzed CloudTrail events for cross-account deployment.

        Args:
            role_name: Name of the role to create
            cloudtrail_events: List of CloudTrail events to analyze
            customer_account_id: Customer AWS account ID for cross-account operations
            cross_account_role_name: Role name to assume in customer account
            external_id: External ID for cross-account role assumption

        Returns:
            JSON string with creation results
        """
        try:
            # Analyze CloudTrail events to extract required permissions
            actions = set()
            resources = set()

            for event in cloudtrail_events:
                if event.get('event_name'):
                    # Extract service and action from event name
                    event_name = event['event_name']
                    if event.get('event_source'):
                        service = event['event_source'].replace('.amazonaws.com', '')
                        action = f"{service}:{event_name}"
                        actions.add(action)

                # Extract resources if available
                if event.get('resources'):
                    for resource in event['resources']:
                        if resource.get('ResourceName'):
                            resources.add(resource['ResourceName'])

            # If no specific resources found, use wildcard (least secure but functional)
            if not resources:
                resources.add("*")

            # Create trust policy (assume role for EC2 and Lambda by default)
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": ["ec2.amazonaws.com", "lambda.amazonaws.com"]
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }

            # Create permission policy
            permission_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": list(actions) if actions else ["s3:GetObject"],  # Fallback action
                        "Resource": list(resources)
                    }
                ]
            }

            return self._run(
                role_name=role_name,
                trust_policy=trust_policy,
                permission_policies=[permission_policy],
                description=f"Least-privilege role created from CloudTrail analysis",
                customer_account_id=customer_account_id,
                cross_account_role_name=cross_account_role_name,
                external_id=external_id
            )

        except Exception as e:
            return json.dumps({
                "error": f"Error creating role from CloudTrail events: {str(e)}",
                "role_name": role_name,
                "customer_account_id": customer_account_id
            })

    def validate_policy_syntax(self, policy: Dict[str, Any]) -> bool:
        """
        Validate IAM policy syntax using AWS IAM policy simulator.

        Args:
            policy: Policy document to validate

        Returns:
            Boolean indicating if policy syntax is valid
        """
        try:
            # Use IAM client to simulate policy validation
            self.iam_client.simulate_custom_policy(
                PolicyInputList=[json.dumps(policy)],
                ActionNames=['s3:GetObject'],  # Dummy action for validation
                ResourceArns=['arn:aws:s3:::dummy-bucket/*']  # Dummy resource
            )
            return True
        except ClientError:
            return False
        except Exception:
            return False
