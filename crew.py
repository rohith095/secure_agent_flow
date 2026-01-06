"""
Main crew workflow for the secure agent flow.
"""
import os

from crewai import Crew, Process
from agents import SecureAgentFlowAgents
from tasks import SecureAgentFlowTasks, send_to_websocket


class SecureAgentFlowCrew:
    """Main crew class that orchestrates the secure agent flow workflow."""

    def __init__(self):
        self.agents = SecureAgentFlowAgents()
        self.tasks = SecureAgentFlowTasks()

    def run_workflow(self, context_input="", policy_requirements="", customer_account_id=None):
        """
        Execute the complete secure agent flow workflow with cross-account support.

        Args:
            context_input (str): Initial context or system information to analyze
            policy_requirements (str): Specific policy requirements or compliance frameworks
            customer_account_id (str): Customer AWS account ID for cross-account operations

        Returns:
            dict: Results from the crew execution
        """

        # Initialize all agents
        roles_fetcher = self.agents.roles_and_details_fetcher_agent()
        policy_creator = self.agents.policy_creator_agent()

        # Define all tasks with dependencies
        fetch_task = self.tasks.fetch_roles_and_details_task(
            agent=roles_fetcher,
            context_input=context_input,
            customer_account_id=customer_account_id
        )


        policy_task = self.tasks.create_policy_task(
            agent=policy_creator,
            policy_requirements=policy_requirements,
            fetch_context="{fetch_task.output}",  # This will pass the output from fetch_task
            customer_account_id=customer_account_id
        )

        # Set up task dependency - policy_task depends on fetch_task
        policy_task.context = [fetch_task]

        initial_response = {
          "messageIdRef": 11,
          "type": 'event',
          "eventType": 'thinking',
          "eventStatus": 'loading',
          "content": 'Processing your request...',
        }
        send_to_websocket(initial_response)
        # Create and configure the crew
        crew = Crew(
            agents=[roles_fetcher, policy_creator],
            tasks=[fetch_task, policy_task],
            process=Process.sequential,
            verbose=True,
            # Disable telemetry
            share_crew=False
        )

        # Execute the workflow
        try:
            result = crew.kickoff()
            second_response = {
                "messageIdRef": 11,
                "type": 'event',
                "eventType": 'thinking',
                "eventStatus": 'completed',
                "content": 'Processed your request...',
            }
            send_to_websocket(second_response)

            send_to_websocket(result)
            return {
                "success": True,
                "result": result,
                "customer_account_id": customer_account_id,
                "message": "Secure agent flow workflow completed successfully with cross-account operations"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "customer_account_id": customer_account_id,
                "message": "Error occurred during cross-account workflow execution"
            }

    def run_individual_task(self, task_name, context_input="", policy_requirements="", customer_account_id=None):
        """
        Run an individual task for testing or debugging purposes with cross-account support.

        Args:
            task_name (str): Name of the task to run ('fetch', 'map', 'prepare', 'policy')
            context_input (str): Input context for the task
            policy_requirements (str): Policy requirements (for policy task)
            customer_account_id (str): Customer AWS account ID for cross-account operations

        Returns:
            dict: Results from the individual task execution
        """

        task_mapping = {
            'fetch': (self.agents.roles_and_details_fetcher_agent(),
                      lambda agent: self.tasks.fetch_roles_and_details_task(agent, context_input, customer_account_id)),
            'map': (self.agents.mapping_agent(),
                    lambda agent: self.tasks.create_mapping_task(agent)),
            'prepare': (self.agents.prepare_agent(),
                        lambda agent: self.tasks.prepare_data_task(agent)),
            'policy': (self.agents.policy_creator_agent(),
                       lambda agent: self.tasks.create_policy_task(agent, policy_requirements, customer_account_id=customer_account_id))
        }

        if task_name not in task_mapping:
            return {
                "success": False,
                "error": f"Invalid task name: {task_name}",
                "message": "Valid task names are: fetch, map, prepare, policy"
            }

        agent, task_func = task_mapping[task_name]
        task = task_func(agent)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential
        )

        try:
            result = crew.kickoff()
            send_to_websocket(result)
            return {
                "success": True,
                "result": result,
                "message": f"Task '{task_name}' completed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error occurred during task '{task_name}' execution"
            }


if __name__ == "__main__":
    print("Initializing SecureAgentFlowCrew")
    crew = SecureAgentFlowCrew()
    os.environ["WEBSOCKET_CONNECTION_ID"]= "123456"
    print("Starting workflow execution")
    context_input = """
    Analyze CloudTrail events for a specific AWS IAM user to understand their actual permission usage patterns.
    Based on this analysis, create a custom IAM role with minimal required permissions following the principle of least privilege.
    Then generate a Service Control Policy (SCP) that enforces security boundaries for this role."""
    result = crew.run_workflow(
        context_input=context_input,
        customer_account_id="371513194691"
    )
