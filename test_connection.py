from crewai import LLM

model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"

llm = LLM(
    model=model_id
)

print(llm.call("how"))
