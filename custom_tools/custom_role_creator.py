"""
Custom tool for creating AWS IAM custom roles.
"""
import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from crewai.tools import BaseTool


class AWSRoleCreator(BaseTool):
    """Tool for creating AWS IAM custom roles with specified permissions."""

    name: str = "AWS Role Creator"
    description: str = """
    Creates AWS IAM custom roles with specified trust policies and permission policies.
    Use this tool to create new IAM roles based on analyzed CloudTrail events and 
    least-privilege requirements.
    """

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

    def _run(self,
             role_name: str,
             trust_policy: Dict[str, Any],
             permission_policies: List[Dict[str, Any]],
             description: Optional[str] = None,
             max_session_duration: int = 3600,
             path: str = "/",
             tags: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Create an AWS IAM custom role with specified policies.

        Args:
            role_name: Name of the IAM role to create
            trust_policy: Trust policy document (assume role policy)
            permission_policies: List of permission policy documents
            description: Optional description for the role
            max_session_duration: Maximum session duration in seconds (default: 1 hour)
            path: Path for the role (default: "/")
            tags: Optional list of tags for the role

        Returns:
            String with creation status and role ARN
        """
        try:
            # Validate inputs
            if not role_name:
                return "Error: Role name is required"

            if not trust_policy:
                return "Error: Trust policy is required"

            if not permission_policies or len(permission_policies) == 0:
                return "Error: At least one permission policy is required"

            # Check if role already exists
            try:
                existing_role = self.iam_client.get_role(RoleName=role_name)
                return f"Error: Role '{role_name}' already exists with ARN: {existing_role['Role']['Arn']}"
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise e

            # Create the role
            create_role_params = {
                'RoleName': role_name,
                'AssumeRolePolicyDocument': json.dumps(trust_policy),
                'Path': path,
                'MaxSessionDuration': max_session_duration
            }

            if description:
                create_role_params['Description'] = description

            if tags:
                create_role_params['Tags'] = tags

            role_response = self.iam_client.create_role(**create_role_params)
            role_arn = role_response['Role']['Arn']

            self.logger.info(f"Successfully created role: {role_name}")

            # Attach permission policies
            attached_policies = []
            for i, policy in enumerate(permission_policies):
                policy_name = f"{role_name}Policy{i+1}"

                # Create inline policy
                try:
                    self.iam_client.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(policy)
                    )
                    attached_policies.append(policy_name)
                    self.logger.info(f"Attached policy {policy_name} to role {role_name}")

                except ClientError as e:
                    self.logger.error(f"Failed to attach policy {policy_name}: {e}")
                    # Continue with other policies even if one fails
                    continue

            # Prepare result summary
            result = {
                "status": "success",
                "role_name": role_name,
                "role_arn": role_arn,
                "attached_policies": attached_policies,
                "message": f"Successfully created role '{role_name}' with {len(attached_policies)} policies"
            }

            return json.dumps(result, indent=2)

        except ClientError as e:
            error_msg = f"AWS IAM Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
            self.logger.error(error_msg)
            return f"Error creating role: {error_msg}"

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return f"Error creating role: {error_msg}"

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