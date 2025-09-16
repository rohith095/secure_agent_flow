"""
AWS Lambda handler for the secure agent flow application.
This handler processes requests and runs the CrewAI workflow with AWS Bedrock.
"""

import json
import logging
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


def bedrock_agent_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Specialized handler for AWS Bedrock Agent integration.

    Args:
        event: Bedrock agent event
        context: Lambda context

    Returns:
        Bedrock agent response format
    """
    try:
        logger.info(f"Bedrock agent event: {json.dumps(event)}")

        # Extract input from Bedrock agent event format
        input_text = event.get('inputText', '')
        session_attributes = event.get('sessionAttributes', {})

        # Parse the input for context and policy requirements
        # This is a simple parser - you can make it more sophisticated
        if 'context:' in input_text and 'policy:' in input_text:
            parts = input_text.split('policy:')
            context_input = parts[0].replace('context:', '').strip()
            policy_requirements = parts[1].strip()
        else:
            context_input = input_text
            policy_requirements = session_attributes.get('policy_requirements', '')

        # Run the workflow
        crew = SecureAgentFlowCrew()
        result = crew.run_workflow(
            context_input=context_input,
            policy_requirements=policy_requirements
        )

        # Format response for Bedrock agent
        response_text = f"Secure agent flow completed. Results: {result}"

        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'function': event.get('function', ''),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': response_text
                        }
                    }
                }
            }
        }

    except Exception as e:
        logger.error(f"Error in bedrock_agent_handler: {str(e)}", exc_info=True)

        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'function': event.get('function', ''),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': f"Error processing request: {str(e)}"
                        }
                    }
                }
            }
        }

