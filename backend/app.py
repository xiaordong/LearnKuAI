"""FastAPI 入口：CORS、路由注册、启动事件"""
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import sessions, notes, logs
from backend.ws import router as ws_router

app = FastAPI(title="LearnKuAI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(ws_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
