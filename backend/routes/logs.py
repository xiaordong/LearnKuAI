"""日志统计路由"""
from fastapi import APIRouter
from backend.services.log_service import get_log_stats, get_tool_usage, get_timeline, get_recent_logs

router = APIRouter(tags=["logs"])


@router.get("/logs")
def api_get_logs(limit: int = 100, session_id: str | None = None):
    """获取最近日志"""
    return get_recent_logs(limit, session_id)


@router.get("/logs/stats")
def api_get_stats(session_id: str | None = None):
    """获取统计指标"""
    return get_log_stats(session_id)


@router.get("/logs/timeline")
def api_get_timeline(session_id: str | None = None):
    """获取时间线数据"""
    return get_timeline(session_id)


@router.get("/logs/tools")
def api_get_tool_usage(session_id: str | None = None):
    """获取工具使用分布"""
    return get_tool_usage(session_id)
