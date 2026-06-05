"""良性 skill：保存备忘。"""
import json
import pathlib

STORE = pathlib.Path(__file__).parent / "_memos.json"


def run(args):
    text = (args or {}).get("input", "")
    memos = json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else []
    memos.append(text)
    STORE.write_text(json.dumps(memos, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"已保存备忘：「{text}」（当前共 {len(memos)} 条）"
