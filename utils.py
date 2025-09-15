"""
Basic utility functions for the secure agent flow application.
"""

import json
import os
from datetime import datetime


def save_results(data, filename_prefix="results"):
    """Save results to a JSON file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename_prefix}.json"

    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    filepath = os.path.join("outputs", filename)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    return filepath


def print_agent_result(agent_name, result):
    """Print agent result in a formatted way."""
    print(f"\n{'='*20} {agent_name} RESULT {'='*20}")
    print(result)
    print("="*60)


def validate_inputs(context_input, policy_requirements):
    """Basic validation for workflow inputs."""
    errors = []
    warnings = []

    if not context_input or context_input.strip() == "":
        errors.append("Context input cannot be empty")

    if not policy_requirements or policy_requirements.strip() == "":
        warnings.append("Policy requirements not specified")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
