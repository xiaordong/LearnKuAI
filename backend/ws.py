"""WebSocket 端点：实时 Agent 交互"""
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 跟踪活跃的 agent 任务，防止同一 session 并发
_active_agents: dict[str, asyncio.Task] = {}


@router.websocket("/ws/agent/{session_id}")
async def ws_agent(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "message":
                content = data.get("content", "")
                if not content:
                    continue

                # 取消同一 session 的旧任务
                old_task = _active_agents.get(session_id)
                if old_task and not old_task.done():
                    old_task.cancel()

                # 独立 event_queue，每条消息一个
                event_queue = asyncio.Queue()

                async def relay():
                    """从 event_queue 实时中继事件到 WebSocket"""
                    while True:
                        event = await event_queue.get()
                        await websocket.send_json(event)
                        if event.get("type") in ("done", "error"):
                            break

                async def run_agent(msg: str):
                    """启动 agent 并实时中继"""
                    from backend.services.agent_service import start_agent, cancel_agent
                    # agent 和 relay 并发运行
                    agent_task = asyncio.create_task(start_agent(session_id, msg, event_queue))
                    relay_task = asyncio.create_task(relay())

                    # 等两者都结束
                    await asyncio.gather(agent_task, relay_task, return_exceptions=True)
                    _active_agents.pop(session_id, None)

                task = asyncio.create_task(run_agent(content))
                _active_agents[session_id] = task

            elif msg_type == "cancel":
                from backend.services.agent_service import cancel_agent
                cancel_agent(session_id)
                old_task = _active_agents.pop(session_id, None)
                if old_task and not old_task.done():
                    old_task.cancel()
                await websocket.send_json({"type": "error", "message": "已取消"})

    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        _active_agents.pop(session_id, None)
