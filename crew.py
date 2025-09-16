"""
Main crew workflow for the secure agent flow.
"""

from crewai import Crew, Process
from agents import SecureAgentFlowAgents
from tasks import SecureAgentFlowTasks


class SecureAgentFlowCrew:
    """Main crew class that orchestrates the secure agent flow workflow."""

    def __init__(self):
        self.agents = SecureAgentFlowAgents()
        self.tasks = SecureAgentFlowTasks()

    def run_workflow(self, context_input=""):
        """
        Execute the complete secure agent flow workflow.

        Args:
            context_input (str): Initial context or system information to analyze

        Returns:
            dict: Results from the crew execution
        """

        # Initialize all agents
        roles_fetcher = self.agents.roles_and_details_fetcher_agent()
        # mapper = self.agents.mapping_agent()
        # preparer = self.agents.prepare_agent()
        # policy_creator = self.agents.policy_creator_agent()

        # Define all tasks with dependencies
        fetch_task = self.tasks.fetch_roles_and_details_task(
            agent=roles_fetcher,
            context_input=context_input
        )

        # mapping_task = self.tasks.create_mapping_task(agent=mapper)

        # prepare_task = self.tasks.prepare_data_task(agent=preparer)

        # policy_task = self.tasks.create_policy_task(
        #     agent=policy_creator,
        # )

        # Create and configure the crew
        crew = Crew(
            agents=[roles_fetcher],
            tasks=[fetch_task],
            process=Process.sequential,
            verbose=True,
            # Disable telemetry
            share_crew=False
        )

        # Execute the workflow
        try:
            result = crew.kickoff()
            return {
                "success": True,
                "result": result,
                "message": "Secure agent flow workflow completed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error occurred during workflow execution"
            }

    def run_individual_task(self, task_name, context_input="", policy_requirements=""):
        """
        Run an individual task for testing or debugging purposes.

        Args:
            task_name (str): Name of the task to run ('fetch', 'map', 'prepare', 'policy')
            context_input (str): Input context for the task
            policy_requirements (str): Policy requirements (for policy task)

        Returns:
            dict: Results from the individual task execution
        """

        task_mapping = {
            'fetch': (self.agents.roles_and_details_fetcher_agent(),
                      lambda agent: self.tasks.fetch_roles_and_details_task(agent, context_input)),
            'map': (self.agents.mapping_agent(),
                    lambda agent: self.tasks.create_mapping_task(agent)),
            'prepare': (self.agents.prepare_agent(),
                        lambda agent: self.tasks.prepare_data_task(agent)),
            'policy': (self.agents.policy_creator_agent(),
                       lambda agent: self.tasks.create_policy_task(agent, policy_requirements))
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
            process=Process.sequential,
            verbose=True
        )

        try:
            result = crew.kickoff()
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

    print("Starting workflow execution")
    context_input = """
    Fetches CloudTrail events for only Hackathon_bad_user and returns well-formatted JSON and then create a custom role based on 
    the permissions usage form the events """
    result = crew.run_workflow(
        context_input=context_input,
    )
