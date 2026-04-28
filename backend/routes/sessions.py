"""会话 CRUD 路由"""
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from research_agent.memory import new_session, list_sessions, load_session, save_session, get_db

router = APIRouter(tags=["sessions"])


class SessionUpdate(BaseModel):
    """更新会话标题的请求体"""
    title: str = Field(min_length=1, description="会话标题")


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
    with get_db() as conn:
        conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        cursor = conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        if cursor.rowcount == 0:
            raise HTTPException(404, "会话不存在")
    return {"ok": True}


@router.patch("/sessions/{session_id}")
def api_update_session(session_id: str, body: SessionUpdate):
    """更新会话标题"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE sessions SET title=?, updated_at=? WHERE id=?",
            (body.title, now, session_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(404, "会话不存在")
    return {"ok": True}
