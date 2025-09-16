import json
import boto3
import time
from datetime import datetime
import logging

apigateway_client = boto3.client('apigatewaymanagementapi')

import threading
from concurrent.futures import ThreadPoolExecutor


class WebSocketLogHandler(logging.Handler):
    def __init__(self, connection_id):
        super().__init__()
        self.connection_id = connection_id
        self.executor = ThreadPoolExecutor(max_workers=1)

    def emit(self, record):
        try:
            log_entry = self.format(record)
            level = record.levelname.lower()

            # Use thread pool to avoid event loop issues
            self.executor.submit(
                send_log_message,
                self.connection_id,
                level,
                log_entry
            )
        except Exception:
            pass  # Don't break logging if WebSocket fails

    def close(self):
        self.executor.shutdown(wait=True)
        super().close()

def lambda_handler(event, context):
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    domain_name = event.get('requestContext', {}).get('domainName')
    stage = event.get('requestContext', {}).get('stage')
    apigateway_client.meta.config.endpoint_url = f"https://{domain_name}/{stage}"

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
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message, default=str)
        )
    except apigateway_client.exceptions.GoneException:
        pass
    except Exception:
        pass
