from research_agent.core import agent_loop

user_input = input("您:")
result = agent_loop(user_input)
print(f"助手:{result}")