import json

from openai import OpenAI
import config
from research_agent.tools import TOOL_FUNCTIONS, get_tools
from research_agent.memory import (
    new_session, load_session, save_session,
    list_sessions, estimate_char_count, compress_messages
)

client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.BASE_URL,
)

SYSTEM_PROMPT = """你是一个研究助手，使用 Plan-and-Execute 模式工作。

工作流程：
1. 收到研究任务后，先用 update_plan 制定搜索计划（拆解为具体步骤）
2. 逐步执行每个步骤，使用搜索和网页抓取工具收集信息
3. 根据中间结果可以调整计划（再次调用 update_plan）
4. 完成后给出综合结论，必要时保存为笔记

注意：
- 先规划再执行，不要盲目搜索
- 用简体中文回答
- 禁止编造信息，所有结论必须基于搜索到的真实内容"""


def execute_tool(tool_name: str, arguments_json: str) -> str:
    try:
        func = TOOL_FUNCTIONS[tool_name]
        args = json.loads(arguments_json)
        result = func(**args)
        return str(result)
    except Exception as e:
        return f"工具执行失败: {e}"


def agent_loop(session_id: str, user_message: str, max_iterations: int = 30) -> str:
    # 加载会话消息
    messages = load_session(session_id)

    # 新会话：添加系统提示词
    if not messages:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 添加用户消息
    messages.append({"role": "user", "content": user_message})

    # 检查是否需要压缩（阈值 100K 字符，约 50K tokens）
    if estimate_char_count(messages) > 100000:
        messages = compress_messages(messages, client)

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            tools=get_tools()
        )
        choice = response.choices[0]

        if choice.finish_reason == "stop":
            messages.append(choice.message)
            save_session(session_id, messages)
            return choice.message.content
        messages.append(choice.message)

        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            args_json = tool_call.function.arguments
            args_str = args_json if args_json else ""

            print(f"\r[工具调用] {tool_name}({args_str})", end="", flush=True)

            result = execute_tool(tool_name, args_json)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    save_session(session_id, messages)
    return "达到最大迭代次数，任务未完成"
