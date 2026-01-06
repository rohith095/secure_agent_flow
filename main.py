"""
Main entry point for the secure agent flow application.
"""

from crew_main import SecureAgentFlowCrew
from config import Config
import sys


def main():
    """Main function to run the secure agent flow workflow."""
    # print("🚀 Welcome to Secure Agent Flow!")
    # print("=" * 50)
    #
    # # Validate configuration
    # config_status = Config.validate_config()
    # if not config_status["valid"]:
    #     print(f"❌ Configuration Error: {config_status['message']}")
    #     return
    #
    # print("✅ Configuration validated successfully!")

    # Initialize the crew
    crew = SecureAgentFlowCrew()

    # Example usage - you can modify these inputs
    context_input = """
    Optimize the user permissions for AWS account with ID 364358839657.
    """

    policy_requirements = """
    Policy requirements:
    - ZSP 
    - Principle of least privilege
    """

    print("🤖 Starting the 4-agent workflow...")
    print("Agents: Roles Fetcher → Mapper → Preparer → Policy Creator")
    print("-" * 50)

    # Run the complete workflow
    result = crew.run_workflow(
        context_input=context_input
    )

    if result["success"]:
        print("✅ Workflow completed successfully!")
        print(f"📋 Result: {result['result']}")
    else:
        print("❌ Workflow failed!")
        print(f"Error: {result['error']}")
        print(f"Message: {result['message']}")


def run_individual_task(task_name):
    """Run an individual task for testing purposes."""
    # Validate configuration
    config_status = Config.validate_config()
    if not config_status["valid"]:
        print(f"❌ Configuration Error: {config_status['message']}")
        return

    crew = SecureAgentFlowCrew()

    context_input = "Sample system for testing individual task"
    policy_requirements = "Basic security policy requirements"

    result = crew.run_individual_task(
        task_name=task_name,
        context_input=context_input,
        policy_requirements=policy_requirements
    )

    if result["success"]:
        print(f"✅ Task '{task_name}' completed successfully!")
        print(f"📋 Result: {result['result']}")
    else:
        print(f"❌ Task '{task_name}' failed!")
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run individual task if specified
        task_name = sys.argv[1]
        print(f"🔧 Running individual task: {task_name}")
        run_individual_task(task_name)
    else:
        # Run complete workflow
        main()
