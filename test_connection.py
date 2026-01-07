from crewai import LLM

model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

llm = LLM(
    model=model_id
)

print(llm.call("how"))
