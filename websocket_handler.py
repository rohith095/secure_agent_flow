import json
import boto3
import time
from datetime import datetime
import logging
from config import Config

llm = Config.get_bedrock_llm()

apigateway_client = boto3.client('apigatewaymanagementapi',
                                         endpoint_url='https://0zix02p6af.execute-api.us-east-1.amazonaws.com/hackathon')

import threading
from concurrent.futures import ThreadPoolExecutor

def lambda_handler(event, context):
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    apigateway_client.meta.config.endpoint_url = "wss://0zix02p6af.execute-api.us-east-1.amazonaws.com/hackathon"

    if route_key == '$connect':
        return handle_connect(connection_id)
    elif route_key == '$disconnect':
        return handle_disconnect(connection_id)
    elif route_key == 'sendMessage':
        return handle_send_message(connection_id, event)
    elif route_key == 'startExecution':
        return handle_start_execution(connection_id, event)
    return {'statusCode': 400, 'body': 'Unknown route'}

def handle_connect(connection_id):
    welcome_message = {
        'type': 'system',
        'message': 'Connected to execution logger',
        'timestamp': datetime.now().isoformat()
    }
    send_message_to_connection(connection_id, welcome_message)
    return {'statusCode': 200, 'body': 'Connected'}

def handle_disconnect(connection_id):
    return {'statusCode': 200, 'body': 'Disconnected'}

def handle_send_message(connection_id, event):
    body = json.loads(event.get('body', '{}'))
    message = body.get('message', '')
    response_message = {
        'type': 'echo',
        'message': f"Received: {message}",
        'timestamp': datetime.now().isoformat()
    }
    send_message_to_connection(connection_id, response_message)
    return {'statusCode': 200, 'body': 'Message sent'}

def handle_start_execution(connection_id, event):
    body = json.loads(event.get('body', '{}'))
    task_name = body.get('taskName', 'Unknown Task')
    simulate_execution_with_logs(connection_id, task_name)
    return {'statusCode': 200, 'body': 'Execution started'}

def simulate_execution_with_logs(connection_id, task_name):
    send_log_message(connection_id, 'info', f"🚀 Starting execution: {task_name}")
    steps = [
        ("Initializing environment...", 1),
        ("Loading configuration...", 0.5),
        ("Connecting to services...", 1),
        ("Processing data...", 2),
        ("Generating results...", 1.5),
        ("Finalizing output...", 0.5)
    ]
    for step, delay in steps:
        send_log_message(connection_id, 'info', f"⏳ {step}")
        time.sleep(delay)
    send_log_message(connection_id, 'success', f"✅ Task completed: {task_name}")
    result_message = {
        'type': 'result',
        'taskName': task_name,
        'status': 'completed',
        'result': f"Task '{task_name}' executed successfully",
        'timestamp': datetime.now().isoformat()
    }
    send_message_to_connection(connection_id, result_message)

def send_log_message(connection_id, level, message):
    log_message = {
        'type': 'log',
        'level': level,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    send_message_to_connection(connection_id, log_message)

def send_message_to_connection(connection_id, message):
    try:
        skip_llm = False
        if hasattr(message, 'raw') or hasattr(message, 'description'):
            # TaskOutput object
            agent_name = getattr(message, 'agent', '')
            result_data = getattr(message, 'raw', None) or getattr(message, 'description', None)
        else:
            # Fallback: treat as string
            task_name = ''
            agent_name = ''
            result_data = message

        # Only summarize if result_data is present
        if result_data:
            # Choose prompt based on task/agent
            if 'Roles and Details Fetcher' in agent_name:
                prompt = f"""
                Summarize this AWS IAM analysis task in 4 brief points:
                1. Searching for IAM users (mention count found)
                2. Found IAM users with their usernames and activity status
                3. Number of CloudTrail events analyzed (mention total count)
                4. Custom roles created in AWS (show role names and ARNs only)

                Task output: {result_data}

                Format as numbered list with minimal details only.
                """
            elif 'Mapping Agent' in agent_name:
                prompt = f"""
                Summarize this mapping task in 2 brief points:
                1. Created identity users in cyber identity (show names only)
                2. Created policy details (show role, identity, and policy name only)

                Task output: {result_data}

                Format as numbered list with minimal details only.
                """
            elif result_data["eventType"] == "thinking":
                skip_llm = True
                ws_message = result_data
            else:
                prompt =  f"""
Summarize this task output in 4-5 brief bullet points as a visually appealing HTML snippet.
Use inline CSS for a modern card-style look (rounded corners, soft shadow, padding, nice font).
Only include the summary content inside a <div> with styling.

Task output: {result_data}

Format: HTML with inline CSS, no explanations.
"""
            if not skip_llm:
                # Get LLM summary
                try:
                    llm_summary = llm.call(prompt)

                    llm_summary = str(llm_summary)
                except Exception as llm_error:
                    print(f"LLM error: {llm_error}")
                    llm_summary = "Summary generation failed - showing original result"

                # Prepare message for WebSocket
                ws_message = {
                    'agent': agent_name,
                    "type": "stream",
                    "isStreamEnd": True,
                    'content': llm_summary,
                    'result': result_data,
                    'timestamp': datetime.now().isoformat()
                }
        connection_id = "RC05ScAzIAMCIBw="
        # Send to WebSocket
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(ws_message, default=str)
        )
    except apigateway_client.exceptions.GoneException:
        pass
    except Exception as e:
        print(f"Error sending message: {e}")

# if __name__ == '__main__':
#     try:
#         apigateway_client = boto3.client('apigatewaymanagementapi',
#                                          endpoint_url='https://0zix02p6af.execute-api.us-east-1.amazonaws.com/hackathon')
#         apigateway_client.post_to_connection(
#             ConnectionId="RCYeycVoIAMCJBQ=",
#             Data=json.dumps("hi Rajat", default=str)
#         )
#     except Exception as e:
#         print(e)