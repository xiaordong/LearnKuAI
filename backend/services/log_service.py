"""日志聚合查询：统计、时间线"""
from research_agent.memory import get_db


def _build_query(base: str, session_id: str | None = None, extra_where: str = "") -> tuple[str, tuple]:
    """构建带可选 session_id 过滤的 SQL 查询"""
    where_parts = []
    params: list = []
    if extra_where:
        where_parts.append(extra_where)
    if session_id:
        where_parts.append("session_id = ?")
        params.append(session_id)
    where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    return base.replace("{where}", where), tuple(params)


def get_log_stats(session_id: str | None = None) -> dict:
    """获取日志统计信息"""
    with get_db() as conn:
        api_count = conn.execute(
            *_build_query(
                "SELECT COUNT(*) as cnt FROM agent_logs WHERE category = 'api' {where}",
                session_id
            )
        ).fetchone()["cnt"]

        tool_count = conn.execute(
            *_build_query(
                "SELECT COUNT(*) as cnt FROM agent_logs WHERE tool_name IS NOT NULL {where}",
                session_id
            )
        ).fetchone()["cnt"]

        avg_duration = conn.execute(
            *_build_query(
                "SELECT AVG(duration_ms) as avg_ms FROM agent_logs WHERE duration_ms IS NOT NULL {where}",
                session_id
            )
        ).fetchone()["avg_ms"]

        total = conn.execute(
            *_build_query("SELECT COUNT(*) as cnt FROM agent_logs {where}", session_id)
        ).fetchone()["cnt"]

        errors = conn.execute(
            *_build_query(
                "SELECT COUNT(*) as cnt FROM agent_logs WHERE level IN ('ERROR', 'WARNING') {where}",
                session_id
            )
        ).fetchone()["cnt"]

    return {
        "api_calls": api_count,
        "tool_calls": tool_count,
        "avg_duration_ms": round(avg_duration or 0, 1),
        "error_rate": round(errors / total * 100, 1) if total else 0,
        "total_logs": total,
    }


def get_tool_usage(session_id: str | None = None) -> list[dict]:
    """获取工具使用分布（饼图数据）"""
    with get_db() as conn:
        if session_id:
            rows = conn.execute(
                "SELECT tool_name, COUNT(*) as count FROM agent_logs WHERE tool_name IS NOT NULL AND session_id = ? GROUP BY tool_name ORDER BY count DESC",
                (session_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT tool_name, COUNT(*) as count FROM agent_logs WHERE tool_name IS NOT NULL GROUP BY tool_name ORDER BY count DESC"
            ).fetchall()
    return [dict(row) for row in rows]


def get_timeline(session_id: str | None = None) -> list[dict]:
    """获取日志时间线（折线图数据），按小时聚合"""
    sql = """SELECT strftime('%Y-%m-%d %H:00', created_at) as hour,
              COUNT(*) as total,
              SUM(CASE WHEN level IN ('ERROR','WARNING') THEN 1 ELSE 0 END) as errors
              FROM agent_logs {where}
              GROUP BY hour ORDER BY hour"""
    with get_db() as conn:
        query, params = _build_query(sql, session_id)
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_recent_logs(limit: int = 100, session_id: str | None = None) -> list[dict]:
    """获取最近日志"""
    with get_db() as conn:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM agent_logs WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [dict(row) for row in rows]
