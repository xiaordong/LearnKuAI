"""笔记 API 服务层：供 REST API 调用的笔记查询和删除"""
from research_agent.memory import get_db


def get_all_notes(session_id: str | None = None) -> list[dict]:
    """获取笔记列表（含摘要），供 API 使用"""
    with get_db() as conn:
        if session_id:
            rows = conn.execute(
                "SELECT id, session_id, title, substr(content, 1, 200) as summary, created_at, updated_at FROM notes WHERE session_id = ? ORDER BY updated_at DESC",
                (session_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, session_id, title, substr(content, 1, 200) as summary, created_at, updated_at FROM notes ORDER BY updated_at DESC"
            ).fetchall()
    return [dict(row) for row in rows]


def get_note(note_id: int) -> dict | None:
    """获取单个笔记完整内容"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row) if row else None


def delete_note(note_id: int) -> bool:
    """删除笔记，返回是否成功"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cursor.rowcount > 0
