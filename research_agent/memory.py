"""会话记忆管理：SQLite 存储、上下文压缩、日志持久化"""
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("memory") / "sessions.db"
DB_PATH.parent.mkdir(exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def clean_old_logs(retention_days: int = 7) -> int:
    """清理超过保留期的日志，返回删除条数"""
    conn = _get_conn()
    cursor = conn.execute(
        "DELETE FROM agent_logs WHERE created_at < datetime('now', ?)",
        (f"-{retention_days} days",)
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


class SQLiteHandler(logging.Handler):
    """自定义日志 Handler，将日志写入 SQLite"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # 从 logger 名提取 category：agent.tools → tools, agent.core.api → api
            category = record.name.split(".")[-1]
            session_id = getattr(record, "session_id", None)
            tool_name = getattr(record, "tool_name", None)
            duration_ms = getattr(record, "duration_ms", None)
            message = record.getMessage()
            # 截断过长消息，避免数据库膨胀
            if len(message) > 500:
                message = message[:500] + "..."
            created_at = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            conn = _get_conn()
            conn.execute(
                "INSERT INTO agent_logs (level, category, message, session_id, tool_name, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record.levelname, category, message, session_id, tool_name, duration_ms, created_at)
            )
            conn.commit()
            conn.close()
        except Exception:
            # 日志 Handler 不能抛异常，否则会破坏被日志的系统
            self.handleError(record)


def _init_db():
    """初始化数据库表"""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            tool_call_id TEXT,
            tool_calls TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            session_id TEXT,
            tool_name TEXT,
            duration_ms INTEGER,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    conn.commit()
    conn.close()
    # 启动时清理过期日志（保留 7 天）
    clean_old_logs(7)


# 模块加载时初始化数据库
_init_db()


def _to_dict(msg) -> dict:
    """将 SDK 对象或 dict 统一转为 dict"""
    if isinstance(msg, dict):
        return msg
    if hasattr(msg, "model_dump"):
        return msg.model_dump()
    return {"role": "unknown", "content": str(msg)}


def new_session() -> str:
    """创建新会话，返回 session_id"""
    session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, '', ?, ?)",
        (session_id, now, now)
    )
    conn.commit()
    conn.close()
    return session_id


def save_session(session_id: str, messages: list, title: str = ""):
    """保存会话数据：更新标题 + 全量替换消息"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()

    # 更新会话标题和时间
    if title:
        conn.execute(
            "UPDATE sessions SET title=?, updated_at=? WHERE id=?",
            (title, now, session_id)
        )
    else:
        conn.execute(
            "UPDATE sessions SET updated_at=? WHERE id=?",
            (now, session_id)
        )

    # 删除旧消息，重新插入
    conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))

    for msg in messages:
        msg_dict = _to_dict(msg)
        role = msg_dict.get("role", "unknown")
        content = msg_dict.get("content")
        tool_call_id = msg_dict.get("tool_call_id")
        tool_calls = msg_dict.get("tool_calls")
        # tool_calls 是列表，需要序列化为 JSON
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None

        conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_call_id, tool_calls) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, tool_call_id, tool_calls_json)
        )

    conn.commit()
    conn.close()


def load_session(session_id: str) -> list:
    """加载会话，返回 messages 列表"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, tool_call_id, tool_calls FROM messages WHERE session_id=? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()

    messages = []
    for row in rows:
        msg = {"role": row["role"], "content": row["content"]}
        if row["tool_call_id"]:
            msg["tool_call_id"] = row["tool_call_id"]
        if row["tool_calls"]:
            msg["tool_calls"] = json.loads(row["tool_calls"])
        messages.append(msg)
    return messages


def list_sessions() -> list[dict]:
    """列出所有会话，按更新时间倒序"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, updated_at FROM sessions ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "title": row["title"] or "无标题",
            "updated_at": row["updated_at"]
        }
        for row in rows
    ]


def estimate_char_count(messages: list) -> int:
    """估算 messages 的总字符数"""
    total = 0
    for msg in messages:
        msg_dict = _to_dict(msg)
        content = msg_dict.get("content", "")
        if content:
            total += len(content)
    return total


def compress_messages(messages: list, client) -> list:
    """压缩旧消息：保留系统提示词 + 最近对话，中间部分交给 LLM 生成摘要"""
    import config

    # 保留 system prompt
    first = _to_dict(messages[0]) if messages else None
    system_msg = [first] if first and first["role"] == "system" else []

    # 保留最近 10 条消息
    keep_recent = 10
    recent = [_to_dict(m) for m in messages[-keep_recent:]]

    # 需要压缩的旧消息
    old = [_to_dict(m) for m in messages[len(system_msg):-keep_recent]]
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
