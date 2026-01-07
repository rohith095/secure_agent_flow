from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from dotenv import load_dotenv
import boto3
import json
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()


class CloudTrailFetcherInput(BaseModel):
    """Input schema for CloudTrail Events Fetcher tool."""
    action: Optional[str] = Field(default="fetch_events",
                                  description="Action to perform: 'fetch_events' (default) to fetch CloudTrail data, or 'cleanup_users' to delete IAM users")
    specific_user: Optional[str] = Field(default=None,
                                         description="Specific IAM username to fetch events for (optional)")
    customer_account_id: Optional[str] = Field(default=None, description="Customer AWS account ID to assume role into")
    cross_account_role_name: Optional[str] = Field(default="CyberArkRoleSCA-3436d390-d01e-11f0-91ee-0e1617ad5923",
                                                   description="Role name to assume in customer account")
    external_id: Optional[str] = Field(default=None,
                                       description="External ID for cross-account role assumption (optional)")
    protected_users: Optional[list] = Field(default=None,
                                           description="List of usernames to protect from deletion when action='cleanup_users' (default: ['DeploymentUser', 'Hackathon', 'pro_user', 'pro_max_user'])")


class CloudTrailEventsFetcher(BaseTool):
    name: str = "CloudTrail Events Fetcher"
    description: str = (
        "Multi-purpose tool for AWS IAM management. Supports two actions: "
        "1. 'fetch_events' (default): REQUIRED FIRST STEP for AWS IAM optimization tasks. Fetches comprehensive CloudTrail events "
        "for ALL AWS IAM users in a customer account by assuming a cross-account role. "
        "Use this BEFORE any IAM role creation or permission analysis. "
        "Returns detailed activity data needed for creating least-privilege custom roles. "
        "2. 'cleanup_users': Deletes temporary IAM users after policy verification, while protecting specified users "
        "(DeploymentUser, Hackathon, pro_user, pro_max_user by default). Use this AFTER successful policy creation and verification "
        "to clean up the customer account."
    )
    args_schema: Type[BaseModel] = CloudTrailFetcherInput

    def _assume_cross_account_role(self, customer_account_id: str, role_name: str, external_id: Optional[str] = None):
        """Assume a cross-account role and return the assumed role session."""
        try:
            # Create STS client
            sts_client = boto3.client('sts')

            # Build role ARN
            role_arn = f"arn:aws:iam::{customer_account_id}:role/{role_name}"

            # Prepare assume role parameters
            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': f'CloudTrailFetcher-{datetime.now().strftime("%Y%m%d%H%M%S")}'
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
            role_arn = f"arn:aws:iam::{customer_account_id}:role/{role_name}"
            error_msg = f"Failed to assume cross-account role {role_arn}: {str(e)}"
            return {
                "session": None,
                "account_id": customer_account_id,
                "role_arn": role_arn,
                "error": error_msg
            }

    def _get_all_iam_users(self, session=None):
        """Get all IAM users with pagination using provided session or default."""
        if session:
            iam_client = session.client('iam', region_name='us-east-1')
        else:
            iam_client = boto3.client('iam', region_name='us-east-1')

        users = []

        try:
            paginator = iam_client.get_paginator('list_users')
            for page in paginator.paginate():
                users.extend(page['Users'])
        except ClientError as e:
            return {"error": f"Error getting IAM users: {str(e)}", "users": []}

        return {"users": users, "error": None}

    def _get_cloudtrail_events_for_user(self, username: str, start_time: datetime, end_time: datetime,
                                        max_events: int = 20, session=None):
        """Get CloudTrail events for a specific user with pagination and event limit using provided session."""
        if session:
            cloudtrail_client = session.client('cloudtrail', region_name='us-east-1')
        else:
            cloudtrail_client = boto3.client('cloudtrail', region_name='us-east-1')

        all_events = []

        try:
            paginator = cloudtrail_client.get_paginator('lookup_events')
            page_iterator = paginator.paginate(
                LookupAttributes=[
                    {'AttributeKey': 'Username', 'AttributeValue': username}
                ],
                StartTime=start_time,
                EndTime=end_time
            )

            for page in page_iterator:
                events = page.get('Events', [])
                for event in events:
                    # Stop if we've reached the maximum number of events
                    if len(all_events) >= max_events:
                        break

                    # Convert datetime objects to ISO format strings for JSON serialization
                    event_data = {
                        'event_id': event.get('EventId'),
                        'event_name': event.get('EventName'),
                        'event_time': event.get('EventTime').isoformat() if event.get('EventTime') else None,
                        'event_source': event.get('EventSource'),
                        'username': event.get('Username'),
                        'source_ip_address': event.get('SourceIPAddress'),
                        'user_agent': event.get('UserAgent'),
                        'aws_region': event.get('AwsRegion'),
                        'read_only': event.get('ReadOnly'),
                        'resources': event.get('Resources', []),

                        # Additional fields extracted from CloudTrailEvent JSON if available
                        'event_version': None,
                        'user_identity': None,
                        'request_parameters': None,
                        'response_elements': None,
                        'additional_event_data': None,
                        'request_id': None,
                        'event_type': None,
                        'management_event': None,
                        'recipient_account_id': None,
                        'event_category': None,
                        'tls_details': None
                    }

                    # Parse CloudTrailEvent JSON to extract additional details
                    if event.get('CloudTrailEvent'):
                        try:
                            ct_event = json.loads(event.get('CloudTrailEvent'))
                            event_data.update({
                                'event_version': ct_event.get('eventVersion'),
                                'user_identity': ct_event.get('userIdentity'),
                                'request_parameters': ct_event.get('requestParameters'),
                                'response_elements': ct_event.get('responseElements'),
                                'additional_event_data': ct_event.get('additionalEventData'),
                                'request_id': ct_event.get('requestID'),
                                'event_type': ct_event.get('eventType'),
                                'management_event': ct_event.get('managementEvent'),
                                'recipient_account_id': ct_event.get('recipientAccountId'),
                                'event_category': ct_event.get('eventCategory'),
                                'tls_details': ct_event.get('tlsDetails')
                            })
                        except (json.JSONDecodeError, TypeError):
                            pass

                    all_events.append(event_data)

                # Break out of the page loop if we've reached the max events
                if len(all_events) >= max_events:
                    break

        except ClientError as e:
            return {"error": f"Error getting CloudTrail events for user {username}: {str(e)}", "events": []}

        return {"events": all_events, "error": None}

    def _fetch_all_events_parallel(self, iam_users, start_time, end_time, session):
        """Fetch CloudTrail events for all users concurrently."""
        users_data = []
        errors = []
        total_events = 0

        def fetch_user_events(user):
            username = user.get("UserName")
            return username, self._get_cloudtrail_events_for_user(username, start_time, end_time, max_events=50,
                                                                  session=session)

        initial_response = {
            "messageIdRef": 13,
            "type": 'event',
            "eventType": 'generating',
            "eventStatus": 'loading',
            "content": 'Getting CloudTrail events ...',
        }

        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_user = {executor.submit(fetch_user_events, user): user for user in iam_users}
            for future in as_completed(future_to_user):
                user = future_to_user[future]
                username = user.get("UserName")
                try:
                    uname, user_events_result = future.result()
                    if user_events_result["error"]:
                        errors.append(user_events_result["error"])
                        users_data.append({
                            "username": uname,
                            "events": [],
                            "error": user_events_result["error"],
                            "has_activity": False,
                            "should_skip_role_creation": True,
                            "skip_reason": "Error fetching CloudTrail events"
                        })
                    else:
                        has_events = len(user_events_result["events"]) > 0
                        users_data.append({
                            "username": uname,
                            "events": user_events_result["events"],
                            "has_activity": has_events,
                            "should_skip_role_creation": not has_events,
                            "skip_reason": "No CloudTrail events found - cannot determine required permissions" if not has_events else None
                        })
                        total_events += len(user_events_result["events"])
                except Exception as exc:
                    errors.append(f"Exception for user {username}: {str(exc)}")
                    users_data.append({
                        "username": username,
                        "events": [],
                        "error": str(exc),
                        "has_activity": False,
                        "should_skip_role_creation": True,
                        "skip_reason": f"Exception occurred: {str(exc)}"
                    })

        return users_data, errors, total_events

    def _delete_iam_users(self, usernames, session=None, protected_users=None):
        """Delete IAM users in AWS, excluding protected users. Returns a list of results for each user."""
        if protected_users is None:
            protected_users = ["DeploymentUser", "Hackathon", "pro_user", "pro_max_user"]
        
        if session:
            iam_client = session.client('iam', region_name='us-east-1')
        else:
            iam_client = boto3.client('iam', region_name='us-east-1')

        results = []
        for username in usernames:
            # Skip protected users
            if username in protected_users:
                results.append({
                    "username": username,
                    "status": "skipped",
                    "reason": "User is in protected list"
                })
                print(f"Skipping protected user: {username}")
                continue
            
            try:
                iam_client.delete_user(UserName=username)
                results.append({
                    "username": username,
                    "status": "deleted"
                })
                print(f"Successfully deleted user: {username}")
            except ClientError as e:
                results.append({
                    "username": username,
                    "status": "error",
                    "error": str(e)
                })
                print(f"Error deleting user {username}: {str(e)}")
        return results

    def cleanup_iam_users(self, customer_account_id: str = None,
                         cross_account_role_name: str = "CyberArkRoleSCA-3436d390-d01e-11f0-91ee-0e1617ad5923",
                         external_id: str = None, protected_users: list = None) -> str:
        """
        Delete IAM users from AWS account, excluding protected users.
        
        Args:
            customer_account_id: Optional customer AWS account ID for cross-account operations
            cross_account_role_name: Role name to assume in customer account
            external_id: Optional external ID for cross-account role assumption
            protected_users: List of usernames to protect from deletion (default: ["DeploymentUser", "Hackathon", "pro_user", "pro_max_user"])
        
        Returns:
            JSON string with cleanup results
        """
        try:
            if protected_users is None:
                protected_users = ["DeploymentUser", "Hackathon", "pro_user", "pro_max_user"]
            
            session = None
            
            # Assume cross-account role if customer_account_id is provided
            if customer_account_id:
                assume_role_result = self._assume_cross_account_role(customer_account_id, cross_account_role_name,
                                                                     external_id)
                if assume_role_result["error"]:
                    return json.dumps({
                        "success": False,
                        "error": assume_role_result["error"],
                        "cleanup_results": []
                    }, indent=2)
                else:
                    session = assume_role_result["session"]
            
            # Get all IAM users
            users_result = self._get_all_iam_users(session)
            
            if users_result["error"]:
                return json.dumps({
                    "success": False,
                    "error": users_result["error"],
                    "cleanup_results": []
                }, indent=2)
            
            # Extract usernames
            usernames = [user.get("UserName") for user in users_result["users"]]
            
            # Delete users (protected users will be skipped)
            cleanup_results = self._delete_iam_users(usernames, session=session, protected_users=protected_users)
            
            # Summarize results
            deleted_count = sum(1 for r in cleanup_results if r["status"] == "deleted")
            skipped_count = sum(1 for r in cleanup_results if r["status"] == "skipped")
            error_count = sum(1 for r in cleanup_results if r["status"] == "error")
            
            return json.dumps({
                "success": True,
                "summary": {
                    "total_users_processed": len(cleanup_results),
                    "users_deleted": deleted_count,
                    "users_skipped": skipped_count,
                    "errors": error_count,
                    "protected_users": protected_users
                },
                "cleanup_results": cleanup_results,
                "account_id": customer_account_id if customer_account_id else "default"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error during IAM user cleanup: {str(e)}",
                "cleanup_results": []
            }, indent=2)

    def _run(self, action: str = "fetch_events", specific_user: str = None, customer_account_id: str = None,
             cross_account_role_name: str = "CyberArkRoleSCA-3436d390-d01e-11f0-91ee-0e1617ad5923",
             external_id: str = None, protected_users: list = None) -> str:
        """Execute the specified action and return JSON."""
        
        # Handle cleanup_users action
        if action == "cleanup_users":
            return self.cleanup_iam_users(
                customer_account_id=customer_account_id,
                cross_account_role_name=cross_account_role_name,
                external_id=external_id,
                protected_users=protected_users
            )
        
        # Default action: fetch_events
        try:
            # Set time range for CloudTrail events (fixed to 1 day)
            hours_back = 12  # 1 hour
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)

            result = {
                "analysis_instruction": (
                    "CloudTrail data collected successfully. Next steps: "
                    "1. **CRITICAL**: Check the 'should_skip_role_creation' flag for each user. "
                    "   DO NOT create IAM roles, identity users, or policies for users with should_skip_role_creation=True. "
                    "   Only process users with has_activity=True and should_skip_role_creation=False. "
                    "2. Analyze the events data for ACTIVE users to understand their activity patterns. "
                    "3. Identify minimum required permissions for each ACTIVE user. "
                    "4. Use AWS IAM MCP server tools to create optimized custom roles ONLY for ACTIVE users. "
                    "5. Skip any user listed in 'users_to_skip' - they have no CloudTrail activity data."
                ),
                "summary": {
                    "query_time": datetime.now().isoformat(),
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    },
                    "total_users_processed": 0,
                    "total_events_found": 0
                },
                "users_data": [],
                "errors": []
            }

            session = None

            # Assume cross-account role if customer_account_id is provided
            if customer_account_id:
                assume_role_result = self._assume_cross_account_role(customer_account_id, cross_account_role_name,
                                                                     external_id)
                if assume_role_result["error"]:
                    result["errors"].append(assume_role_result["error"])
                    return json.dumps(result, indent=2)
                else:
                    session = assume_role_result["session"]

            # Get IAM users
            if specific_user:
                # Process only specific user, but skip if it's DeploymentUser
                if specific_user == "DeploymentUser":
                    users_result = {"users": [], "error": None}
                else:
                    users_result = {"users": [{"UserName": specific_user}], "error": None}
            else:
                users_result = self._get_all_iam_users(session)
                initial_response = {
                    "messageIdRef": 12,
                    "type": 'event',
                    "eventType": 'processing',
                    "eventStatus": 'completed',
                    "content": 'Getting AWS IAM Users ...',
                }
                if users_result["error"] is None:
                    # Filter out DeploymentUser from the list
                    users_result["users"] = [user for user in users_result["users"] if
                                             user.get("UserName") != "DeploymentUser"]

            if users_result["error"]:
                result["errors"].append(users_result["error"])
                return json.dumps(result, indent=2)

            iam_users = users_result["users"]
            result["summary"]["total_users_processed"] = len(iam_users)

            # Process all users in parallel instead of sequential processing
            if iam_users:
                users_data, parallel_errors, total_events = self._fetch_all_events_parallel(
                    iam_users, start_time, end_time, session
                )

                # Calculate statistics about users with/without activity
                users_with_activity = [u for u in users_data if u.get("has_activity", False)]
                users_without_activity = [u for u in users_data if u.get("should_skip_role_creation", False)]

                result["users_data"] = users_data
                result["errors"].extend(parallel_errors)
                result["summary"]["total_events_found"] = total_events
                result["summary"]["users_with_activity"] = len(users_with_activity)
                result["summary"]["users_without_activity"] = len(users_without_activity)
                result["summary"]["users_to_skip"] = [u["username"] for u in users_without_activity]

            return json.dumps(result, indent=2)

        except Exception as e:
            error_result = {
                "error": f"Unexpected error in CloudTrail Events Fetcher: {str(e)}",
                "summary": {
                    "query_time": datetime.now().isoformat(),
                    "total_users_processed": 0,
                    "total_events_found": 0
                },
                "users_data": []
            }
            return json.dumps(error_result, indent=2)

# if __name__ == "__main__":
#     tool = CloudTrailEventsFetcher()
#     response = tool._run(days_back=1)
#     print(response)
