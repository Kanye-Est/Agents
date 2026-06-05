"""Capstone-A：SKILL.md 风格 skill 加载器（复刻 Claude Skills 机制，便于受控研究）。

一个 skill = 一个目录：
  SKILL.md   —— YAML frontmatter(name, description) + 正文(给 agent 的使用说明)
  handler.py —— 定义 run(args: dict) -> str，skill 的可执行行为（可选）

加载器把 skill 包装成 hello_agents 的 Tool：
  - tool.description = frontmatter.description   → 进入系统提示（T3 投毒 / 注入面）
  - tool.run() 调 handler.run()                  → 可执行任意代码（T2 外泄 / T4 执行面）
  - skill.instructions = SKILL.md 正文           → 可注入 agent 上下文（T1 直接注入面）
"""
import importlib.util
from pathlib import Path

import yaml
from hello_agents.tools import Tool, ToolParameter


def _parse_skill_md(path: Path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2]
    return meta, body.strip()


def _load_handler(py_path: Path):
    if not py_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"skill_{py_path.parent.name}", py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "run", None)


class SkillTool(Tool):
    """把一个 SKILL.md 目录包装成 agent 可调用的工具。"""

    def __init__(self, skill_dir):
        skill_dir = Path(skill_dir)
        meta, body = _parse_skill_md(skill_dir / "SKILL.md")
        super().__init__(
            name=meta.get("name", skill_dir.name),
            description=meta.get("description", ""),
        )
        self.instructions = body                       # SKILL.md 正文
        self._handler = _load_handler(skill_dir / "handler.py")

    def get_parameters(self):
        return [ToolParameter(name="input", type="string",
                              description="传给该 skill 的输入文本", required=False)]

    def run(self, parameters):
        if self._handler is None:
            return self.instructions or "(该 skill 无可执行 handler)"
        try:
            return str(self._handler(parameters or {}))
        except Exception as e:
            return f"[skill error] {e}"


def load_skill(skill_dir):
    return SkillTool(skill_dir)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from baseline_agent import build_agent

    skill = load_skill(Path(__file__).resolve().parent / "skills/benign/memo")
    print(f"已加载 skill: name={skill.name} | desc={skill.description}")
    agent = build_agent(extra_tools=[skill])
    print("可用工具:", agent.list_tools())
    print("\n[用户] 帮我记一下：明天给导师发周报\n" + "-" * 56)
    print("[助理]", agent.run("帮我记一下：明天给导师发周报"))
