"""会话 CRUD 路由"""
from fastapi import APIRouter, HTTPException
from research_agent.memory import new_session, list_sessions, load_session, save_session

router = APIRouter(tags=["sessions"])


@router.get("/sessions")
def api_list_sessions():
    """列出所有会话"""
    return list_sessions()


@router.post("/sessions")
def api_create_session():
    """创建新会话"""
    session_id = new_session()
    return {"id": session_id}


@router.get("/sessions/{session_id}")
def api_get_session(session_id: str):
    """获取会话详情（含消息列表）"""
    messages = load_session(session_id)
    if not messages:
        raise HTTPException(404, "会话不存在")
    return {"id": session_id, "messages": messages}


@router.delete("/sessions/{session_id}")
def api_delete_session(session_id: str):
    """删除会话"""
    from research_agent.memory import _get_conn
    conn = _get_conn()
    conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    cursor = conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(404, "会话不存在")
    return {"ok": True}


@router.patch("/sessions/{session_id}")
def api_update_session(session_id: str, body: dict):
    """更新会话标题"""
    title = body.get("title", "")
    if not title:
        raise HTTPException(400, "标题不能为空")
    from research_agent.memory import _get_conn
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    cursor = conn.execute(
        "UPDATE sessions SET title=?, updated_at=? WHERE id=?",
        (title, now, session_id)
    )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(404, "会话不存在")
    return {"ok": True}
