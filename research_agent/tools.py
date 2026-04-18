"""所有工具函数定义，统一返回str格式"""
import re
from datetime import datetime
from pathlib import Path

import httpx
from ddgs import DDGS

NOTES_DIR   = Path("notes")
NOTES_DIR.mkdir(exist_ok=True)

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


def search(keywords: str, region: str = "wt-wt", timelimit: str | None = None, max_results: int = 10) -> str:
    results = DDGS().text(
        query=keywords,
        region=region,
        timelimit=timelimit,
        max_results=max_results
    )
    formatted = []
    for i, item in enumerate(results, 1):
        formatted.append(f"{i}. [{item['title']}]({item['href']})\n  {item['body']}")
    return "\n\n".join(formatted)


def fetch_page(url: str) -> str:
    """抓取网页内容，返回纯文本"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
    if resp.status_code != 200:
        return f"请求失败，状态码: {resp.status_code}"
    # 去掉 HTML 标签，提取纯文本
    text = re.sub(r"<[^>]+>", "", resp.text)
    # 压缩多余空白
    text = re.sub(r"\s+", " ", text).strip()
    # 截断，防止撑爆 context window
    max_length = 5000
    if len(text) > max_length:
        text = text[:max_length] + "\n\n[内容已截断]"
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
        }
    ]

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "search": search,
    "fetch_page": fetch_page,
    "save_note": save_note,
    "read_note": read_note,
    "list_notes": list_notes,
}