"""同步 Agent Loop 与异步 FastAPI 的桥接层

ThreadPoolExecutor 运行同步 agent_loop，
通过 queue.Queue 将事件传递到 asyncio.Queue 供 WebSocket 推送。
"""
import asyncio
import os
import queue
import signal
import threading
from concurrent.futures import ThreadPoolExecutor

from research_agent.tools import TOOL_FUNCTIONS
from backend.services.note_service import save_note_db, read_note_db, list_notes_db

# 运行时替换笔记工具为数据库版本（不修改 tools.py 源码）
TOOL_FUNCTIONS["save_note"] = save_note_db
TOOL_FUNCTIONS["read_note"] = read_note_db
TOOL_FUNCTIONS["list_notes"] = list_notes_db

executor = ThreadPoolExecutor(max_workers=4)

# 跟踪活跃任务，用于取消
_active_tasks: dict[str, threading.Event] = {}


def shutdown():
    """强制关闭线程池，不等待正在执行的任务"""
    executor.shutdown(wait=False, cancel_futures=True)


def _run_agent(session_id: str, message: str, event_queue: queue.Queue, cancel_event: threading.Event):
    """在线程中运行 agent_loop，通过 event_callback 推送事件"""
    from research_agent.core import agent_loop

    def event_callback(event: dict):
        if cancel_event.is_set():
            raise InterruptedError("任务已取消")
        event_queue.put(event)

    try:
        agent_loop(session_id, message, event_callback=event_callback)
    except InterruptedError:
        event_queue.put({"type": "error", "message": "任务已取消"})
    except Exception as e:
        event_queue.put({"type": "error", "message": str(e)})
    finally:
        event_queue.put(None)  # sentinel：结束信号


async def start_agent(session_id: str, message: str, async_queue: asyncio.Queue):
    """启动 agent 并将事件桥接到 asyncio.Queue"""
    sync_queue: queue.Queue = queue.Queue()
    cancel_event = threading.Event()
    _active_tasks[session_id] = cancel_event

    # 在线程池中运行同步 agent
    future = executor.submit(_run_agent, session_id, message, sync_queue, cancel_event)

    # 桥接：sync_queue → asyncio_queue
    while True:
        try:
            event = sync_queue.get_nowait()
        except queue.Empty:
            if future.done():
                break
            await asyncio.sleep(0.05)
            continue

        if event is None:
            break
        await async_queue.put(event)

    _active_tasks.pop(session_id, None)


def cancel_agent(session_id: str):
    """取消正在运行的 agent 任务"""
    cancel_event = _active_tasks.get(session_id)
    if cancel_event:
        cancel_event.set()
