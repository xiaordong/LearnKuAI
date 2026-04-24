import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)

def new_session():
    session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    session_data = {
        "id": session_id,
        "title":"",
        "created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message":[],
    }
    file_path = MEMORY_DIR / f"{session_id}.json"
    file_path.write_text(json.dumps(session_data,ensure_ascii=False,indent=2),encoding="utf-8")
    return session_id

def save_session(session_id:str,message:list,title:str = ""):
    file_path = MEMORY_DIR / f"{session_id}.json"
    if file_path.exists():
        old_data = json.loads(file_path.read_text(encoding="utf-8"))
        created_at = old_data.get("created_at")
        if not title:
            title = old_data.get("title","")
    else:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    session_data = {
        "id": session_id,
        "title": title,
        "created_at": created_at,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
    }
    file_path.write_text(json.dumps(session_data,ensure_ascii=False,indent=2),encoding="utf-8")
    return session_id

if __name__ == "__main__":
    sid = new_session()
    save_session(sid,[{"role":"user","content":"test"}],title="test_title")