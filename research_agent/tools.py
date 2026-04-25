"""所有工具函数定义，统一返回str格式"""
import logging
import re
import threading
from datetime import datetime
from pathlib import Path

import httpx
from ddgs import DDGS

log = logging.getLogger("agent.tools")

# 线程局部变量，用于传递当前 session_id
_thread_local = threading.local()


def set_log_context(session_id: str):
    """设置当前线程的日志上下文"""
    _thread_local.session_id = session_id


def _log_info(msg: str, **extra):
    """带 session_id 的日志"""
    extra["session_id"] = getattr(_thread_local, "session_id", None)
    log.info(msg, extra=extra)


def _log_warning(msg: str, **extra):
    extra["session_id"] = getattr(_thread_local, "session_id", None)
    log.warning(msg, extra=extra)

NOTES_DIR   = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

PLAN_FILE = Path("memory") / "current_plan.md"
PLAN_FILE.parent.mkdir(exist_ok=True)

def save_note(title: str, content: str) -> str:
    # 清理文件名中的特殊字符
    title = title.replace("/", "_").replace("\\", "_")
    file_path = NOTES_DIR / f"{title}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"笔记已保存至 {file_path}"


def read_note(title: str) -> str:
    # 清理文件名，和保存时保持一致
    title = title.replace("/", "_").replace("\\", "_")
    file_path = NOTES_DIR / f"{title}.md"
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"笔记不存在: {title}"


def list_notes() -> str:
    notes = list(NOTES_DIR.glob("*.md"))
    if not notes:
        return "暂无笔记"
    return "\n".join(f.stem for f in notes)

def get_current_time()->str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def update_plan(plan: str) -> str:
    """创建或更新当前研究计划"""
    PLAN_FILE.write_text(plan, encoding="utf-8")
    return "计划已更新"


def read_plan() -> str:
    """读取当前研究计划"""
    if not PLAN_FILE.exists():
        return "当前没有研究计划"
    return PLAN_FILE.read_text(encoding="utf-8")


def search(keywords: str, region: str = "wt-wt", timelimit: str | None = None, max_results: int = 10) -> str:
    start = datetime.now()
    results = DDGS().text(
        query=keywords,
        region=region,
        timelimit=timelimit,
        max_results=max_results
    )
    elapsed = int((datetime.now() - start).total_seconds() * 1000)
    _log_info("搜索完成", tool_name="search", duration_ms=elapsed)
    formatted = []
    for i, item in enumerate(results, 1):
        formatted.append(f"{i}. [{item['title']}]({item['href']})\n  {item['body']}")
    return "\n\n".join(formatted)


def _is_safe_url(url: str) -> bool:
    """检查 URL 是否安全（禁止访问内网地址）"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname or ""
    # 禁止内网地址
    blocked = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
    if host.lower() in blocked:
        return False
    # 禁止私有 IP 段
    if host.startswith("192.168.") or host.startswith("10.") or host.startswith("172."):
        return False
    return True


def fetch_page(url: str) -> str:
    """抓取网页内容，返回纯文本"""
    start = datetime.now()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
    elapsed = int((datetime.now() - start).total_seconds() * 1000)
    if resp.status_code != 200:
        _log_warning(f"请求失败 状态码:{resp.status_code}", tool_name="fetch_page", duration_ms=elapsed)
        return f"请求失败，状态码: {resp.status_code}"
    html = resp.text
    # 先移除 style 和 script 块（连同内容）
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    # 再去掉剩余 HTML 标签
    text = re.sub(r"<[^>]+>", "", html)
    # 压缩多余空白
    text = re.sub(r"\s+", " ", text).strip()
    # 截断，防止撑爆 context window
    max_length = 5000
    if len(text) > max_length:
        text = text[:max_length] + "\n\n[内容已截断]"
    _log_info(f"抓取完成 长度:{len(text)}", tool_name="fetch_page", duration_ms=elapsed)
    return text


def get_tools():
    return [
        {
            "type":"function",
            "function":{
                "name":"get_current_time",
                "description":"获取当前日期和时间",
                "parameters":{
                    "type":"object",
                    "properties":{},
                    "required":[]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "使用 DuckDuckGo 搜索引擎搜索互联网信息，返回相关网页的标题、链接和摘要。当需要查找最新信息、事实数据或研究主题相关内容时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "搜索关键词，支持高级语法如 filetype:pdf"
                        },
                        "region": {
                            "type": "string",
                            "description": "地区代码，如 cn-zh(中国)、us-en(美国)、wt-wt(无地区限制)",
                            "default": "wt-wt"
                        },
                        "timelimit": {
                            "type": "string",
                            "description": "时间限制：d(天)、w(周)、m(月)、y(年)",
                            "enum": ["d", "w", "m", "y"]
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "返回结果数量，默认10",
                            "default": 10
                        }
                    },
                    "required": ["keywords"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_page",
                "description": "抓取指定URL的网页内容，返回纯文本。当需要获取搜索结果中某个链接的详细内容时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要抓取的网页URL"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "save_note",
                "description": "将内容保存为本地笔记文件。当需要保存研究发现、记录重要信息或生成研究报告时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "笔记标题，用作文件名"
                        },
                        "content": {
                            "type": "string",
                            "description": "笔记内容，支持Markdown格式"
                        }
                    },
                    "required": ["title", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_note",
                "description": "读取已保存的笔记文件内容。当需要回顾之前的研究记录或引用已有笔记时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "笔记标题"
                        }
                    },
                    "required": ["title"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_notes",
                "description": "列出所有已保存的笔记文件。当需要查看研究历史或确认某条笔记是否存在时使用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_plan",
                "description": "创建或更新当前研究计划。在开始研究前制定计划，或在执行过程中根据新发现调整计划时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "string",
                            "description": "研究计划内容，包含步骤列表和当前进度"
                        }
                    },
                    "required": ["plan"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_plan",
                "description": "读取当前的研究计划。当需要回顾计划进度或继续执行未完成的计划时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "search": search,
    "fetch_page": fetch_page,
    "save_note": save_note,
    "read_note": read_note,
    "list_notes": list_notes,
    "update_plan": update_plan,
    "read_plan": read_plan,
}