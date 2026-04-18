from research_agent.core import  agent_loop
while True:
    user_input = input("您：")
    if user_input.lower() in ["exit","quit","退出"]:
        break
    result = agent_loop(user_input)
    print(f"助手:{result}")