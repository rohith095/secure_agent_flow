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
    days_back: int = Field(default=7, description="Number of days back to fetch events (default: 7)")
    specific_user: Optional[str] = Field(default=None, description="Specific IAM username to fetch events for (optional)")

class CloudTrailEventsFetcher(BaseTool):
    name: str = "CloudTrail Events Fetcher"
    description: str = "Fetches CloudTrail events for all AWS IAM users and returns well-formatted JSON"
    args_schema: Type[BaseModel] = CloudTrailFetcherInput

    def _get_all_iam_users(self):
        """Get all IAM users with pagination"""
        iam_client = boto3.client('iam', region_name='us-east-1')
        users = []

        try:
            paginator = iam_client.get_paginator('list_users')
            for page in paginator.paginate():
                users.extend(page['Users'])
        except ClientError as e:
            return {"error": f"Error getting IAM users: {str(e)}", "users": []}

        return {"users": users, "error": None}

    def _get_cloudtrail_events_for_user(self, username: str, start_time: datetime, end_time: datetime):
        """Get CloudTrail events for a specific user with pagination"""
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
                # Removed PaginationConfig to fetch all events without limits
            )

            for page in page_iterator:
                events = page.get('Events', [])
                for event in events:
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
                            # If CloudTrailEvent is not valid JSON, keep it as is
                            pass

                    all_events.append(event_data)

        except ClientError as e:
            return {"error": f"Error getting CloudTrail events for user {username}: {str(e)}", "events": []}

        return {"events": all_events, "error": None}

    def _fetch_all_events_parallel(self, iam_users, start_time, end_time):
        """Fetch CloudTrail events for all users concurrently."""
        users_data = []
        errors = []
        total_events = 0

        def fetch_user_events(user):
            username = user.get("UserName")
            return username, self._get_cloudtrail_events_for_user(username, start_time, end_time)

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
                            "error": user_events_result["error"]
                        })
                    else:
                        users_data.append({
                            "username": uname,
                            "events": user_events_result["events"]
                        })
                        total_events += len(user_events_result["events"])
                except Exception as exc:
                    errors.append(f"Exception for user {username}: {str(exc)}")
                    users_data.append({
                        "username": username,
                        "events": [],
                        "error": str(exc)
                    })
        return users_data, errors, total_events

    def _run(self, days_back: int = 1, specific_user: str = None) -> str:
        """Execute the CloudTrail events fetching logic and return JSON."""
        try:
            # Set time range for CloudTrail events
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)

            result = {
                "summary": {
                    "query_time": datetime.now().isoformat(),
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "days_back": days_back
                    },
                    "total_users_processed": 0,
                    "total_events_found": 0
                },
                "users_data": [],
                "errors": []
            }

            # Get IAM users
            if specific_user:
                # Process only specific user
                users_result = {"users": [{"UserName": specific_user}], "error": None}
            else:
                users_result = self._get_all_iam_users()

            if users_result["error"]:
                result["errors"].append(users_result["error"])
                return json.dumps(result, indent=2)

            iam_users = users_result["users"]
            result["summary"]["total_users_processed"] = len(iam_users)

            # Process all users in parallel instead of sequential processing
            if iam_users:
                users_data, parallel_errors, total_events = self._fetch_all_events_parallel(
                    iam_users, start_time, end_time
                )

                result["users_data"] = users_data
                result["errors"].extend(parallel_errors)
                result["summary"]["total_events_found"] = total_events

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