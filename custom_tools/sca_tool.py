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

from tasks import send_to_websocket

load_dotenv()
import os
import requests
import json
import time

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
RESCAN_URL = f"{SCA_POLICY_URL}cloud/rescan"
JOB_STATUS_URL = f"{SCA_POLICY_URL}integrations/status"

REQUEST_TIMEOUT_SEC = 30

class SCAToolInput(BaseModel):
    """Input schema for SCA Tool."""
    action: str = Field(..., description="Action to perform: 'create_policy', 'create_identity_user', or 'rescan'")
    policy_payload: Optional[Dict[str, Any]] = Field(default=None, description="Payload for policy creation")
    identity_payload: Optional[Dict[str, Any]] = Field(default=None, description="Payload for identity user creation")
    tenant_endpoint: Optional[str] = Field(default=None, description="Tenant endpoint for identity operations")
    service_user_id: Optional[str] = Field(default=None, description="Service user ID for identity operations")
    service_password: Optional[str] = Field(default=None, description="Service password for identity operations")

class SCATool(BaseTool):
    name: str = "CyberArk SCA Tool"
    description: str = (
        "Tool for creating policies, identity users, and rescanning cloud resources in CyberArk SCA. "
        "Supports three actions: 'create_policy' for creating SCA policies, "
        "'create_identity_user' for creating identity users using CyberArk Identity, "
        "and 'rescan' for rescanning cloud resources to get recently created roles."
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
        """Create a policy using the provided payload and wait for job completion."""
        try:
            token = self.get_sca_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-API-Version": "2.0"
            }
            resp = requests.post(CREATE_POLICY_URL, json=policy_payload, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            policy_response = resp.json()

            # Extract job_id from the response
            job_id = policy_response.get('job_id')
            if not job_id:
                self.logger.error("No job_id found in create_policy response")
                return policy_response

            self.logger.info(f"Policy creation initiated with job_id: {job_id}")

            # Wait for job completion
            job_status = self.wait_for_job_completion(job_id)

            # Return combined response with policy details and final job status
            return {
                "policy_response": policy_response,
                "job_id": job_id,
                "final_status": job_status,
                "success": job_status.get('status', '').lower() in ['success', 'completed']
            }

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
                "Content-Type": "application/json",
                "X-IDAP-NATIVE-CLIENT": "Web", "Accept": "*/*"
            }
            identity_url = f"{SCA_BASE_URL}/CDirectoryService/CreateUser"
            resp = requests.post(identity_url, json=identity_payload, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.logger.error(f"Error creating identity user: {e}")
            raise

    def get_job_status_debug_mode(self, job_id: str) -> Dict[str, Any]:
        """Get job status in debug mode."""
        try:
            token = self.get_sca_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                'jobId': job_id,
                'debug': "true"
            }
            resp = requests.get(JOB_STATUS_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.logger.error(f"Error getting job status: {e}")
            raise

    def wait_for_job_completion(self, job_id: str, max_wait_time: int = 300, poll_interval: int = 10) -> Dict[str, Any]:
        """Wait for job completion by polling job status until Success or Failure."""
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                status_response = self.get_job_status_debug_mode(job_id)
                job_status = status_response.get('status', '').lower()

                if job_status == 'success':
                    self.logger.info(f"Job {job_id} completed successfully")
                    return status_response
                elif job_status == 'failure':
                    self.logger.error(f"Job {job_id} failed")
                    raise RuntimeError(f"Job {job_id} failed: {status_response}")
                elif job_status == 'inprogress':
                    self.logger.info(f"Job {job_id} still in progress")
                    time.sleep(poll_interval)
                else:
                    self.logger.warning(f"Unknown job status: {job_status}")
                    time.sleep(poll_interval)

            except Exception as e:
                self.logger.warning(f"Error polling job status for {job_id}: {e}")
                time.sleep(poll_interval)

        self.logger.warning(f"Job {job_id} polling timed out after {max_wait_time} seconds")
        final_status = self.get_job_status_debug_mode(job_id)
        if final_status.get('status', '').lower() == 'failure':
            raise RuntimeError(f"Job {job_id} failed after timeout: {final_status}")
        return final_status

    def rescan(self) -> Dict[str, Any]:
        """Rescan cloud resources to get recently created roles and wait for completion."""

        try:
            token = self.get_sca_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "cloudProvider": 0,
                "accountType": "All"
            }
            resp = requests.post(RESCAN_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SEC)
            resp.raise_for_status()
            rescan_response = resp.json()

            # Extract job_id from the response
            job_id = rescan_response.get('jobId')
            if not job_id:
                self.logger.error("No job_id found in rescan response")
                return rescan_response

            self.logger.info(f"Rescan initiated with job_id: {job_id}")

            # Wait for job completion
            job_status = self.wait_for_job_completion(job_id)

            # Return combined response with rescan details and final job status
            return {
                "rescan_response": rescan_response,
                "job_id": job_id,
                "final_status": job_status,
                "success": job_status.get('status', '').lower() in ['success', 'completed']
            }

        except Exception as e:
            self.logger.error(f"Error rescanning cloud resources: {e}")
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
            tenant_endpoint, service_user_id, service_password = get_aws_secret()
            return self.create_identity_user(tenant_endpoint, service_user_id, service_password, identity_payload)

        elif action == "rescan":
            return self.rescan()

        else:
            raise ValueError(f"Unknown action: {action}. Supported actions: 'create_policy', 'create_identity_user', 'rescan'")

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
# if __name__ == "__main__":
#     sca_tool = SCATool()
#     payload = {
#         "Name": "test_user_1@cyberark.cloud.55567",
#         "Mail": "test_user_1@test.com",
#         "Password": "abcD1234",
#         "InEverybodyRole": True,
#         "InSysAdminRole": False,
#
#     }
#     result = sca_tool._run("create_identity_user", identity_payload=payload)
