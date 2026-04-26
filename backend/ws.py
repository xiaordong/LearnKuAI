"""WebSocket 端点：实时 Agent 交互"""
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/agent/{session_id}")
async def ws_agent(websocket: WebSocket, session_id: str):
    await websocket.accept()

    event_queue = asyncio.Queue()

    try:
        while True:
            # 接收前端消息
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "message":
                content = data.get("content", "")
                if not content:
                    continue

                # 启动 agent（异步任务）
                from backend.services.agent_service import start_agent, cancel_agent
                asyncio.create_task(start_agent(session_id, content, event_queue))

                # 同时从 event_queue 读取并推送给前端
                async def relay_events():
                    while True:
                        event = await event_queue.get()
                        await websocket.send_json(event)
                        if event.get("type") in ("done", "error"):
                            break

                relay_task = asyncio.create_task(relay_events())

            elif msg_type == "cancel":
                from backend.services.agent_service import cancel_agent
                cancel_agent(session_id)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
