"""会话记忆管理：SQLite 存储、上下文压缩、日志持久化"""
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path("memory") / "sessions.db"
DB_PATH.parent.mkdir(exist_ok=True)

# WAL 模式是持久设置，只需设置一次
_wal_initialized = False


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    global _wal_initialized
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    if not _wal_initialized:
        conn.execute("PRAGMA journal_mode=WAL")
        _wal_initialized = True
    return conn


@contextmanager
def get_db():
    """数据库连接上下文管理器，自动 commit/rollback/close"""
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def clean_old_logs(retention_days: int = 7) -> int:
    """清理超过保留期的日志，返回删除条数"""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM agent_logs WHERE created_at < datetime('now', ?)",
            (f"-{retention_days} days",)
        )
        return cursor.rowcount


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

            with get_db() as conn:
                conn.execute(
                    "INSERT INTO agent_logs (level, category, message, session_id, tool_name, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (record.levelname, category, message, session_id, tool_name, duration_ms, created_at)
                )
        except Exception:
            # 日志 Handler 不能抛异常，否则会破坏被日志的系统
            self.handleError(record)


def _init_db():
    """初始化数据库表"""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '',
                plan TEXT DEFAULT '',
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
        # 兼容迁移：为已有数据库添加 plan 列
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN plan TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 列已存在
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
    now = datetime.now()
    session_id = now.strftime("session_%Y%m%d_%H%M%S")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, '', ?, ?)",
            (session_id, now_str, now_str)
        )
    return session_id


def save_session(session_id: str, messages: list, title: str = ""):
    """保存会话数据：更新标题 + 增量保存消息"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
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

        # 查询已有消息数
        existing_count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id=?", (session_id,)
        ).fetchone()[0]

        # 压缩场景：messages 长度 < DB 数量，退回全量替换
        if len(messages) < existing_count:
            conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
            existing_count = 0

        # 增量插入：只插入新增部分
        for msg in messages[existing_count:]:
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


def load_session(session_id: str) -> list:
    """加载会话，返回 messages 列表"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content, tool_call_id, tool_calls FROM messages WHERE session_id=? ORDER BY id",
            (session_id,)
        ).fetchall()

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
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()

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


# ── Plan 按会话隔离（Issue 3） ──

def save_plan(session_id: str, plan: str):
    """保存研究计划到会话"""
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET plan=? WHERE id=?",
            (plan, session_id)
        )


def load_plan(session_id: str) -> str:
    """加载会话的研究计划"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT plan FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
    if row and row["plan"]:
        return row["plan"]
    return "当前没有研究计划"


# ── 笔记存储统一到数据库（Issue 7） ──

def save_note_db(title: str, content: str, session_id: str | None = None) -> str:
    """保存笔记到数据库，返回结果描述"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM notes WHERE title = ?", (title,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE notes SET content=?, updated_at=?, session_id=COALESCE(?, session_id) WHERE title=?",
                (content, now, session_id, title)
            )
        else:
            conn.execute(
                "INSERT INTO notes (session_id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, title, content, now, now)
            )
    return f"笔记已保存: {title}"


def read_note_db(title: str) -> str:
    """读取笔记内容"""
    with get_db() as conn:
        row = conn.execute("SELECT content FROM notes WHERE title = ?", (title,)).fetchone()
    if row:
        return row["content"]
    return f"笔记不存在: {title}"


def list_notes_db() -> str:
    """列出所有笔记标题"""
    with get_db() as conn:
        rows = conn.execute("SELECT title FROM notes ORDER BY updated_at DESC").fetchall()
    if not rows:
        return "暂无笔记"
    return "\n".join(row["title"] for row in rows)
