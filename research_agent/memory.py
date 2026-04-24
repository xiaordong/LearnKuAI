"""会话记忆管理：对话持久化、加载、压缩"""
import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)


def new_session() -> str:
    """创建新会话，返回 session_id"""
    session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    _write_file(session_id, messages=[], title="")
    return session_id


def save_session(session_id: str, messages: list, title: str = ""):
    """保存会话数据（自动将 SDK 对象转为 dict）"""
    serializable = []
    for msg in messages:
        if isinstance(msg, dict):
            serializable.append(msg)
        elif hasattr(msg, "model_dump"):
            serializable.append(msg.model_dump())
        else:
            serializable.append({"role": "unknown", "content": str(msg)})
    _write_file(session_id, messages=serializable, title=title)


def load_session(session_id: str) -> list:
    """加载会话，返回 messages 列表"""
    file_path = MEMORY_DIR / f"{session_id}.json"
    if not file_path.exists():
        return []
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return data["messages"]


def list_sessions() -> list[dict]:
    """列出所有会话，按更新时间倒序"""
    sessions = []
    for f in sorted(MEMORY_DIR.glob("*.json"), reverse=True):
        data = json.loads(f.read_text(encoding="utf-8"))
        sessions.append({
            "id": data["id"],
            "title": data.get("title", "无标题"),
            "updated_at": data["updated_at"]
        })
    return sessions


def estimate_char_count(messages: list) -> int:
    """估算 messages 的总字符数"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if content:
            total += len(content)
    return total


def compress_messages(messages: list, client) -> list:
    """压缩旧消息：保留系统提示词 + 最近对话，中间部分交给 LLM 生成摘要"""
    import config

    # 保留 system prompt
    system_msg = [messages[0]] if messages and messages[0]["role"] == "system" else []

    # 保留最近 10 条消息
    keep_recent = 10
    recent = messages[-keep_recent:]

    # 需要压缩的旧消息
    old = messages[len(system_msg):-keep_recent]
    if not old:
        return messages

    # 格式化旧消息为文本
    old_text = ""
    for msg in old:
        role = msg["role"]
        content = msg.get("content", "")
        if content:
            old_text += f"{role}: {content}\n"

    # 调用 LLM 生成摘要
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=[{"role": "user", "content": f"请用简洁的中文总结以下对话的关键信息（保留重要事实、数据和结论）：\n\n{old_text}"}],
        max_tokens=1000
    )
    summary = response.choices[0].message.content

    return system_msg + [
        {"role": "system", "content": f"[历史对话摘要]\n{summary}"}
    ] + recent


def _write_file(session_id: str, messages: list, title: str):
    """内部：写入会话文件"""
    file_path = MEMORY_DIR / f"{session_id}.json"

    if file_path.exists():
        old_data = json.loads(file_path.read_text(encoding="utf-8"))
        created_at = old_data["created_at"]
        if not title:
            title = old_data.get("title", "")
    else:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    session_data = {
        "id": session_id,
        "title": title,
        "created_at": created_at,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages
    }
    file_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
