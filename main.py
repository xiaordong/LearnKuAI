from research_agent.core import agent_loop
from research_agent.memory import new_session, list_sessions, save_session, load_session

# 会话选择
sessions = list_sessions()
if sessions:
    print("历史会话：")
    for i, s in enumerate(sessions):
        print(f"  {i+1}. [{s['updated_at']}] {s['title']}")
    print(f"  0. 新建会话")
    choice = input("请选择: ").strip()
    if choice == "0" or not choice:
        session_id = new_session()
    else:
        idx = int(choice) - 1
        session_id = sessions[idx]["id"]
else:
    session_id = new_session()

print(f"\n会话已就绪 (输入 '退出' 结束)\n")

# 对话循环
is_new = not load_session(session_id)  # 新会话标记，用于自动设标题
while True:
    user_input = input("您：")
    if user_input.lower() in ["exit", "quit", "退出"]:
        break
    result = agent_loop(session_id, user_input)
    print(f"助手:{result}")

    # 新会话的第一条消息自动设为标题
    if is_new:
        msgs = load_session(session_id)
        save_session(session_id, msgs, title=user_input[:30])
        is_new = False
