"""
sca_tool.py: Custom tool for CyberArk SCA policy creation
"""
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from requests.auth import HTTPBasicAuth
import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict, Type, Optional
import logging
from crewai.tools import BaseTool

load_dotenv()
import os
import requests
import json

# Configuration
SCA_BASE_URL = os.getenv('SCA_BASE_URL', 'https://ady7840.id.cyberark-everest-integdev.cloud')
SCA_CLIENT_ID = os.getenv('SCA_CLIENT_ID', 'YOUR_CLIENT_ID')
SCA_CLIENT_SECRET = os.getenv('SCA_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
SCA_USERNAME = os.getenv('SCA_USERNAME', 'YOUR_USERNAME')
SCA_PASSWORD = os.getenv('SCA_PASSWORD', 'YOUR_PASSWORD')

# Endpoints
AUTH_URL = f"{SCA_BASE_URL}/oauth2/token/scadev"
SCA_POLICY_URL = "https://navi-test-sca.cyberark-everest-integdev.cloud/api/"
CREATE_POLICY_URL = f"{SCA_POLICY_URL}policies/create-policy"

REQUEST_TIMEOUT_SEC = 30

class SCAToolInput(BaseModel):
    """Input schema for SCA Tool."""
    action: str = Field(..., description="Action to perform: 'create_policy' or 'create_identity_user'")
    policy_payload: Optional[Dict[str, Any]] = Field(default=None, description="Payload for policy creation")
    identity_payload: Optional[Dict[str, Any]] = Field(default=None, description="Payload for identity user creation")
    tenant_endpoint: Optional[str] = Field(default=None, description="Tenant endpoint for identity operations")
    service_user_id: Optional[str] = Field(default=None, description="Service user ID for identity operations")
    service_password: Optional[str] = Field(default=None, description="Service password for identity operations")

class SCATool(BaseTool):
    name: str = "CyberArk SCA Tool"
    description: str = (
        "Tool for creating policies and identity users in CyberArk SCA. "
        "Supports two actions: 'create_policy' for creating SCA policies, "
        "and 'create_identity_user' for creating identity users using CyberArk Identity."
    )
    args_schema: Type[BaseModel] = SCAToolInput

    logger: Optional[logging.Logger] = None

    def __init__(self):
        super().__init__(logger= logging.getLogger(__name__))


    def get_sca_access_token(self) -> str:
        """Get SCA access token using client credentials."""
        try:
            headers = {'Content-Type': 'multipart/form-data', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br',
                       'Connection': 'keep-alive'}
            body = {'grant_type': 'client_credentials', 'scope': 'full'}

            response = requests.post(AUTH_URL, data=body, json=headers,
                                     auth=HTTPBasicAuth(SCA_USERNAME, SCA_PASSWORD))
            return response.json()['access_token']
        except Exception as e:
            self.logger.error(f"Error getting SCA access token: {e}")
            raise



    def get_identity_access_token(self, tenant_endpoint: str, service_user_id: str, service_password: str) -> str:
        """Get identity access token using service credentials."""
        try:
            auth_headers = HTTPBasicAuth(service_user_id, service_password)
            body = {'grant_type': 'client_credentials', 'scope': 'api'}
            auth_url = f'{tenant_endpoint}/oauth2/platformtoken'

            auth_res = requests.post(
                auth_url,
                auth=auth_headers,
                verify=True,
                data=body,
                timeout=REQUEST_TIMEOUT_SEC
            )
            auth_res.raise_for_status()
            return auth_res.json()["access_token"]
        except Exception as e:
            self.logger.error(f"Error getting identity access token: {e}")
            raise

    def create_policy(self, policy_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a policy using the provided payload."""
        try:
            token = self.get_sca_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-API-Version": "2.0"
            }
            resp = requests.post(CREATE_POLICY_URL, json=policy_payload, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.logger.error(f"Error creating policy: {e}")
            raise

    def create_identity_user(self, tenant_endpoint: str, service_user_id: str,
                           service_password: str, identity_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create an identity user using the provided payload."""
        try:
            token = self.get_identity_access_token(tenant_endpoint, service_user_id, service_password)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            identity_url = f"{SCA_BASE_URL}/CDirectoryService/CreateUser"
            resp = requests.post(identity_url, json=identity_payload, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.logger.error(f"Error creating identity user: {e}")
            raise

    def _run(self, action: str, policy_payload: Optional[Dict[str, Any]] = None,
             identity_payload: Optional[Dict[str, Any]] = None,
             tenant_endpoint: Optional[str] = None, service_user_id: Optional[str] = None,
             service_password: Optional[str] = None) -> Dict[str, Any]:
        """Execute the specified action."""

        if action == "create_policy":
            if not policy_payload:
                raise ValueError("policy_payload is required for create_policy action")
            return self.create_policy(policy_payload)

        elif action == "create_identity_user":
            tenant_endpoint,service_user_id,service_password = get_aws_secret()
            return self.create_identity_user(tenant_endpoint, service_user_id, service_password, identity_payload)

        else:
            raise ValueError(f"Unknown action: {action}. Supported actions: 'create_policy', 'create_identity_user'")

def get_aws_secret(secret_name="d6f344b7-5ea6-4351-87c4-8a1141e486a9.integdev.Identity", region_name="us-east-1"):
    """Retrieve a secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret["endpoint"], secret["service_user_id"], secret["service_user_pass"]
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e
    except json.JSONDecodeError as e:
        print(f"Error parsing secret JSON: {e}")
        raise e

# def main():
#     """Example usage of the SCA Tool."""
#     # Sample policy payload
#     policy_payload = {
#         "csp": "AWS",
#         "name": "test_policy_v1",
#         "description": "Test policy created via SCA Tool",
#         "startDate": None,
#         "endDate": None,
#         "policyType": "pre_defined",
#         "roles": [
#             {
#                 "entityId": "arn:aws:iam::148628765294:role/PileusRole",
#                 "workspaceType": "account",
#                 "entitySourceId": "148628765294",
#                 "organizationId": "148628765294"
#             }
#         ],
#         "identities": [
#             {
#                 "entityName": "naveen_kumar_bontu@cyberark.cloud.55567",
#                 "entitySourceId": "09B9A9B0-6CE8-465F-AB03-65766D33B05E",
#                 "entityClass": "user"
#             }
#         ],
#         "accessRules": {
#             "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
#             "fromTime": None,
#             "toTime": None,
#             "maxSessionDuration": 1,
#             "timeZone": "Asia/Jerusalem"
#         }
#     }
#
#     try:
#         # Create SCA tool instance
#         sca_tool = SCATool()
#
#         # Create policy
#         result = sca_tool._run("create_policy", policy_payload=policy_payload)
#         print("Policy created successfully:")
#         print(json.dumps(result, indent=2))
#
#     except Exception as e:
#         print(f"Error: {e}")
#
if __name__ == "__main__":
    sca_tool = SCATool()
    payload = {
        "Name": "test_user_1@cyberark.cloud.55567",
        "Mail": "test_user_1@test.com",
        "Password": "abcD1234",
        "InEverybodyRole": True,
        "InSysAdminRole": False,

    }
    result = sca_tool._run("create_identity_user", identity_payload=payload)