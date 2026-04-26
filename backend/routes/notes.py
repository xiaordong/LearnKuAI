"""笔记 CRUD + 下载路由"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from backend.services.note_service import get_all_notes, get_note, delete_note

router = APIRouter(tags=["notes"])


@router.get("/notes")
def api_list_notes(session_id: str | None = None):
    """获取笔记列表"""
    return get_all_notes(session_id)


@router.get("/notes/{note_id}")
def api_get_note(note_id: int):
    """获取单个笔记"""
    note = get_note(note_id)
    if not note:
        raise HTTPException(404, "笔记不存在")
    return note


@router.get("/notes/{note_id}/download")
def api_download_note(note_id: int):
    """下载笔记为 Markdown 文件"""
    note = get_note(note_id)
    if not note:
        raise HTTPException(404, "笔记不存在")
    # 过滤文件名中的特殊字符，防止头注入
    filename = note["title"].replace("/", "_").replace("\\", "_").replace('"', "'")
    return PlainTextResponse(
        content=note["content"],
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}.md"'}
    )


@router.delete("/notes/{note_id}")
def api_delete_note(note_id: int):
    """删除笔记"""
    if not delete_note(note_id):
        raise HTTPException(404, "笔记不存在")
    return {"ok": True}
