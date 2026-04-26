"""日志聚合查询：统计、时间线"""
from research_agent.memory import _get_conn


def get_log_stats(session_id: str | None = None) -> dict:
    """获取日志统计信息"""
    conn = _get_conn()
    where = "WHERE session_id = ?" if session_id else ""
    params = (session_id,) if session_id else ()

    # API 调用数（category = api）
    api_count = conn.execute(
        f"SELECT COUNT(*) as cnt FROM agent_logs WHERE category = 'api' {('AND session_id = ?' if session_id else '')}",
        params
    ).fetchone()["cnt"]

    # 工具调用数（所有含 tool_name 的记录）
    tool_count = conn.execute(
        f"SELECT COUNT(*) as cnt FROM agent_logs WHERE tool_name IS NOT NULL {('AND session_id = ?' if session_id else '')}",
        params
    ).fetchone()["cnt"]

    # 平均耗时
    avg_duration = conn.execute(
        f"SELECT AVG(duration_ms) as avg_ms FROM agent_logs WHERE duration_ms IS NOT NULL {('AND session_id = ?' if session_id else '')}",
        params
    ).fetchone()["avg_ms"]

    # 错误率
    total = conn.execute(
        f"SELECT COUNT(*) as cnt FROM agent_logs {where}", params
    ).fetchone()["cnt"]
    errors = conn.execute(
        f"SELECT COUNT(*) as cnt FROM agent_logs WHERE level IN ('ERROR', 'WARNING') {('AND session_id = ?' if session_id else '')}",
        params
    ).fetchone()["cnt"]

    conn.close()
    return {
        "api_calls": api_count,
        "tool_calls": tool_count,
        "avg_duration_ms": round(avg_duration or 0, 1),
        "error_rate": round(errors / total * 100, 1) if total else 0,
        "total_logs": total,
    }


def get_tool_usage(session_id: str | None = None) -> list[dict]:
    """获取工具使用分布（饼图数据）"""
    conn = _get_conn()
    if session_id:
        rows = conn.execute(
            "SELECT tool_name, COUNT(*) as count FROM agent_logs WHERE tool_name IS NOT NULL AND session_id = ? GROUP BY tool_name ORDER BY count DESC",
            (session_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT tool_name, COUNT(*) as count FROM agent_logs WHERE tool_name IS NOT NULL GROUP BY tool_name ORDER BY count DESC"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_timeline(session_id: str | None = None) -> list[dict]:
    """获取日志时间线（折线图数据），按小时聚合"""
    conn = _get_conn()
    if session_id:
        rows = conn.execute(
            """SELECT strftime('%Y-%m-%d %H:00', created_at) as hour,
                      COUNT(*) as total,
                      SUM(CASE WHEN level IN ('ERROR','WARNING') THEN 1 ELSE 0 END) as errors
               FROM agent_logs WHERE session_id = ?
               GROUP BY hour ORDER BY hour""",
            (session_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT strftime('%Y-%m-%d %H:00', created_at) as hour,
                      COUNT(*) as total,
                      SUM(CASE WHEN level IN ('ERROR','WARNING') THEN 1 ELSE 0 END) as errors
               FROM agent_logs
               GROUP BY hour ORDER BY hour"""
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_logs(limit: int = 100, session_id: str | None = None) -> list[dict]:
    """获取最近日志"""
    conn = _get_conn()
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
    conn.close()
    return [dict(row) for row in rows]
