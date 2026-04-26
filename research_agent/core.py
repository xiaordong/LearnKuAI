import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import config
from research_agent.tools import TOOL_FUNCTIONS, get_tools, _is_safe_url, set_log_context
from research_agent.memory import (
    new_session, load_session, save_session,
    list_sessions, estimate_char_count, compress_messages,
    SQLiteHandler
)

# 分层 logger：api 记录 API 调用，agent 记录循环控制
log_api = logging.getLogger("agent.core.api")
log_agent = logging.getLogger("agent.core.agent")

# 屏蔽第三方库日志（只记录 agent.* 命名空间）
for name in ["httpx", "ddgs", "primp", "httpcore", "urllib3"]:
    logging.getLogger(name).setLevel(logging.WARNING)

# 日志配置：控制台 + SQLite，不再写文件
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        SQLiteHandler(),
        logging.StreamHandler()
    ]
)

client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.BASE_URL,
)


class MergeAdapter(logging.LoggerAdapter):
    """LoggerAdapter 的 extra 与调用时 extra 合并，而非覆盖"""
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        extra.update(kwargs.get("extra", {}))
        kwargs["extra"] = extra
        return msg, kwargs

SYSTEM_PROMPT = """你是一个研究助手，使用 Plan-and-Execute 模式工作。

工作流程：
1. 收到研究任务后，先用 update_plan 制定搜索计划（拆解为具体步骤）
2. 逐步执行每个步骤，使用搜索和网页抓取工具收集信息
3. 根据中间结果可以调整计划（再次调用 update_plan）
4. 完成后给出综合结论，必要时保存为笔记

错误处理：
- 工具调用失败时，阅读返回的 JSON 错误信息中的 hint 字段，按建议操作
- fetch_page 失败时，直接使用搜索结果中的摘要信息继续回答，不要反复重试
- 某个搜索方向失败时，换一个关键词或搜索方向

注意：
- 先规划再执行，不要盲目搜索
- 多个独立的搜索任务，在一次回复中同时发起所有 search 调用（例如：需要搜索 A、B、C 三个主题时，在同一条消息中返回 3 个 tool_calls）
- 用简体中文回答
- 禁止编造信息，所有结论必须基于搜索到的真实内容"""


def _call_api(messages: list, adapter: logging.LoggerAdapter, max_retries: int = 3) -> object:
    """调用 LLM API，支持自动重试，超时 120 秒"""
    for attempt in range(max_retries):
        try:
            start = time.time()
            response = client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                tools=get_tools(),
                timeout=120.0
            )
            elapsed_ms = int((time.time() - start) * 1000)
            adapter.info(f"API 响应 finish_reason={response.choices[0].finish_reason}",
                         extra={"duration_ms": elapsed_ms})
            return response
        except KeyboardInterrupt:
            raise  # 立即上抛，不重试
        except Exception as e:
            adapter.warning(f"API 调用失败 (第{attempt+1}次): {e}")
            if attempt < max_retries - 1:
                try:
                    time.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s
                except KeyboardInterrupt:
                    raise  # sleep 期间也能中断
            else:
                raise


def _get_tool_schema(tool_name: str) -> dict | None:
    """从 get_tools() 中查找指定工具的 schema"""
    for tool in get_tools():
        if tool["function"]["name"] == tool_name:
            return tool["function"]
    return None


def validate_tool_call(tool_name: str, arguments_json: str) -> str | None:
    """校验工具调用，返回 None 表示通过，返回字符串表示错误原因"""
    # 1. 工具名是否存在
    if tool_name not in TOOL_FUNCTIONS:
        return f"未知工具: {tool_name}，可用工具: {', '.join(TOOL_FUNCTIONS.keys())}"

    schema = _get_tool_schema(tool_name)
    if not schema:
        return f"工具 {tool_name} 的 schema 未找到"

    # 解析参数
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError:
        return f"参数 JSON 格式错误: {arguments_json}"

    params_schema = schema.get("parameters", {})
    required = params_schema.get("required", [])
    properties = params_schema.get("properties", {})

    # 2. 必填参数检查
    for key in required:
        if key not in args:
            return f"缺少必填参数: {key}"

    # 3. 参数类型检查
    type_map = {"string": str, "integer": int, "boolean": bool}
    for key, value in args.items():
        if key in properties:
            expected_type = properties[key].get("type")
            python_type = type_map.get(expected_type)
            if python_type and not isinstance(value, python_type):
                # 兼容：int 可以接受 float（JSON 数字默认解析为 float）
                if python_type == int and isinstance(value, float) and value == int(value):
                    args[key] = int(value)
                    continue
                return f"参数 {key} 类型错误: 期望 {expected_type}, 实际 {type(value).__name__}"

    # 4. URL 安全校验
    if tool_name == "fetch_page" and "url" in args:
        if not _is_safe_url(args["url"]):
            return f"请求被拒绝: 不允许访问内网地址 ({args['url']})"

    return None


def execute_tool(tool_name: str, arguments_json: str, adapter: logging.LoggerAdapter) -> str:
    try:
        func = TOOL_FUNCTIONS[tool_name]
        args = json.loads(arguments_json)
        start = time.time()
        result = func(**args)
        elapsed_ms = int((time.time() - start) * 1000)
        return str(result)
    except Exception as e:
        error_type = type(e).__name__
        adapter.error(f"工具 {tool_name} 失败 [{error_type}]: {e}",
                      extra={"tool_name": tool_name})
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": error_type,
            "tool": tool_name,
            "hint": _error_hint(tool_name, e)
        }, ensure_ascii=False)


def _error_hint(tool_name: str, error: Exception) -> str:
    """根据错误类型返回修复建议"""
    hints = {
        "search": "请尝试更换关键词或稍后重试",
        "fetch_page": "网页无法访问，建议使用搜索结果中的摘要信息继续回答",
        "save_note": "检查标题是否包含特殊字符",
        "read_note": "请先用 list_notes 确认笔记是否存在",
    }
    return hints.get(tool_name, "请尝试其他方式完成任务")


def agent_loop(session_id: str, user_message: str, max_iterations: int = 30, event_callback=None) -> str:
    # 创建带 session_id 的 LoggerAdapter，后续所有日志自动关联会话
    adapter = MergeAdapter(log_agent, {"session_id": session_id})
    # 同步设置 tools 的日志上下文
    set_log_context(session_id)

    # 加载会话消息
    messages = load_session(session_id)

    # 新会话：添加系统提示词
    if not messages:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 添加用户消息
    messages.append({"role": "user", "content": user_message})
    adapter.info(f"收到消息 (会话: {session_id[-8:]})")

    # 检查是否需要压缩（阈值 50K 字符，约 25K tokens）
    if estimate_char_count(messages) > 50000:
        adapter.info("触发上下文压缩")
        messages = compress_messages(messages, client)

    # API 日志也关联同一个 session_id
    api_adapter = MergeAdapter(log_api, {"session_id": session_id})

    def _emit(event: dict):
        """安全调用 event_callback，但取消信号要往上抛"""
        if event_callback:
            event_callback(event)

    try:
        for i in range(max_iterations):
            _emit({"type": "thinking"})
            response = _call_api(messages, api_adapter)
            choice = response.choices[0]

            if choice.finish_reason == "stop":
                messages.append(choice.message)
                _emit({"type": "done", "content": choice.message.content})
                return choice.message.content
            messages.append(choice.message)

            # 并行执行同轮所有工具调用
            def _run_tool(tc):
                """执行单个工具调用，返回 (call_id, tool_name, result, duration_ms)"""
                name = tc.function.name
                args_json = tc.function.arguments or ""
                args_str = args_json

                # 设置线程局部变量，确保日志关联正确
                set_log_context(session_id)

                _emit({"type": "tool_call", "tool_call_id": tc.id, "tool": name, "args": args_str})
                adapter.info(f"调用工具: {name}({args_str[:100]})",
                             extra={"tool_name": name, "duration_ms": None})
                if not event_callback:
                    print(f"\r[工具调用] {name}({args_str})", end="", flush=True)

                # 校验
                validation_error = validate_tool_call(name, args_json)
                if validation_error:
                    adapter.warning(f"工具调用被拒绝: {validation_error}",
                                   extra={"tool_name": name})
                    return tc.id, name, f"工具调用被拒绝: {validation_error}", 0

                start_ts = time.time()
                # 单工具超时保护（30秒），防止 DDGS 等工具无限挂起
                _tool_result = [None]
                _tool_error = [None]
                def _exec():
                    try:
                        _tool_result[0] = execute_tool(name, args_json, adapter)
                    except Exception as e:
                        _tool_error[0] = e
                t = threading.Thread(target=_exec, daemon=True)
                t.start()
                t.join(timeout=30)
                if t.is_alive():
                    result = json.dumps({
                        "success": False,
                        "error": "工具执行超时（30秒）",
                        "tool": name,
                        "hint": "请尝试减少搜索范围或稍后重试"
                    }, ensure_ascii=False)
                elif _tool_error[0]:
                    result = f"执行失败: {_tool_error[0]}"
                else:
                    result = _tool_result[0]
                duration_ms = int((time.time() - start_ts) * 1000)
                _emit({"type": "tool_result", "tool_call_id": tc.id, "tool": name,
                       "result": result[:500], "duration_ms": duration_ms})
                return tc.id, name, result, duration_ms

            # 只有 1 个工具调用时直接执行，避免线程池开销
            tool_calls_list = choice.message.tool_calls
            if len(tool_calls_list) == 1:
                results = [_run_tool(tool_calls_list[0])]
            else:
                results = []
                with ThreadPoolExecutor(max_workers=min(len(tool_calls_list), 4)) as pool:
                    futures = {pool.submit(_run_tool, tc): tc.id for tc in tool_calls_list}
                    for future in as_completed(futures):
                        try:
                            results.append(future.result())
                        except Exception as e:
                            # 单个工具失败不影响其他工具，记录错误继续
                            call_id = futures[future]
                            adapter.error(f"并行工具执行失败: {e}")
                            results.append((call_id, "unknown", f"执行失败: {e}", 0))

            # 按原始 tool_call 顺序组装消息（API 要求顺序一致）
            result_map = {call_id: result for call_id, _, result, _ in results}
            for tool_call in tool_calls_list:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_map.get(tool_call.id, "执行失败")
                })

            # 循环内检查上下文大小，防止工具结果累积撑爆
            if estimate_char_count(messages) > 50000:
                adapter.info("循环内触发上下文压缩")
                messages = compress_messages(messages, client)

        adapter.warning(f"达到最大迭代次数 ({max_iterations})")
        _emit({"type": "error", "message": f"达到最大迭代次数 ({max_iterations})"})
        return "达到最大迭代次数，任务未完成"
    except KeyboardInterrupt:
        adapter.info("用户中断 Agent 循环")
        _emit({"type": "error", "message": "已中断"})
        return "已中断"
    except Exception as e:
        adapter.error(f"Agent 循环异常: {e}")
        _emit({"type": "error", "message": str(e)})
        return f"发生错误: {e}"
    finally:
        save_session(session_id, messages)
