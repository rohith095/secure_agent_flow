"""
AWS Lambda handler for the secure agent flow application.
This handler processes requests and runs the CrewAI workflow with AWS Bedrock.
"""

import json
import logging
import os
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    from crew import SecureAgentFlowCrew
    from config import Config
except ImportError as e:
    logger.error(f"Import error: {e}")


    # For Lambda deployment, these modules should be available
    # Define fallback classes to prevent NameError
    class SecureAgentFlowCrew:
        def run_workflow(self, **kwargs):
            raise RuntimeError("SecureAgentFlowCrew not available")


    class Config:
        @staticmethod
        def validate_config():
            return {"valid": False, "message": "Config module not available"}


def agent_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler function for secure agent flow.

    Args:
        event: Lambda event containing the request data
        context: Lambda context object

    Returns:
        Dict containing the response with statusCode and body
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Extract input from the event
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        os.environ["WEBSOCKET_CONNECTION_ID"] = event.get('requestContext', {}).get('connectionId', "123456")
        context_input = body.get("context_input")

        # Validate configuration
        config_status = Config.validate_config()
        if not config_status["valid"]:
            logger.error(f"Configuration error: {config_status['message']}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Configuration error',
                    'message': config_status['message']
                })
            }

        # Initialize and run the crew
        logger.info("Initializing SecureAgentFlowCrew")
        crew = SecureAgentFlowCrew()

        logger.info("Starting workflow execution")
        result = crew.run_workflow(
            context_input=context_input
        )

        logger.info("Workflow completed successfully")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'result': result,
                'message': 'Secure agent flow executed successfully'
            })
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
