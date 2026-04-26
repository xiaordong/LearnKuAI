"""笔记数据库操作：替代文件系统存储"""
from datetime import datetime
from research_agent.memory import _get_conn


def save_note_db(title: str, content: str, session_id: str | None = None) -> str:
    """保存笔记到数据库，返回结果描述"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    # 检查是否已存在同名笔记
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
    conn.commit()
    conn.close()
    return f"笔记已保存: {title}"


def read_note_db(title: str) -> str:
    """读取笔记内容"""
    conn = _get_conn()
    row = conn.execute("SELECT content FROM notes WHERE title = ?", (title,)).fetchone()
    conn.close()
    if row:
        return row["content"]
    return f"笔记不存在: {title}"


def list_notes_db() -> str:
    """列出所有笔记标题"""
    conn = _get_conn()
    rows = conn.execute("SELECT title FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    if not rows:
        return "暂无笔记"
    return "\n".join(row["title"] for row in rows)


def get_all_notes(session_id: str | None = None) -> list[dict]:
    """获取笔记列表（含摘要），供 API 使用"""
    conn = _get_conn()
    if session_id:
        rows = conn.execute(
            "SELECT id, session_id, title, substr(content, 1, 200) as summary, created_at, updated_at FROM notes WHERE session_id = ? ORDER BY updated_at DESC",
            (session_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, session_id, title, substr(content, 1, 200) as summary, created_at, updated_at FROM notes ORDER BY updated_at DESC"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_note(note_id: int) -> dict | None:
    """获取单个笔记完整内容"""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_note(note_id: int) -> bool:
    """删除笔记，返回是否成功"""
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
