"""第9章 收尾 demo：NoteTool（结构化笔记/持久记忆）+ TerminalTool（JIT 检索）。
顺带暴露一个真实安全问题：TerminalTool 的"安全白名单"可被轻易绕过（Capstone T4/T2 预览）。
运行: cd hello-agents-lab && .venv/bin/python ch09/02_note_terminal_demo.py
"""
import os
import pathlib
from hello_agents.tools import NoteTool, TerminalTool

# ========================= Part 1: NoteTool =========================
print("=" * 60)
print("【NoteTool】结构化笔记 / 持久记忆（对应 9.2.3 结构化笔记）")
print("=" * 60)
note = NoteTool(workspace="ch09/_notes_demo")
print(note.run({"action": "create", "title": "审查 order.py",
                "content": "发现未关闭的 DB 连接，存在泄漏。",
                "note_type": "blocker", "tags": ["security", "db"]}))
print(note.run({"action": "create", "title": "任务进度",
                "content": "已扫描 3/5 个文件。", "note_type": "task_state"}))
print(note.run({"action": "summary"}))
print(note.run({"action": "search", "query": "order"}))

# ===================== Part 2: TerminalTool (JIT) ====================
print("\n" + "=" * 60)
print("【TerminalTool】JIT 即时文件检索（沙箱内，正常用法）")
print("=" * 60)
sandbox = pathlib.Path("ch09/_sandbox_demo")
sandbox.mkdir(parents=True, exist_ok=True)
(sandbox / "app.py").write_text("def login():\n    pass  # TODO: add rate limit\n", encoding="utf-8")
term = TerminalTool(workspace=str(sandbox))
print("[ls -la]\n" + term.run({"command": "ls -la"}))
print("[grep -rn TODO .]\n" + term.run({"command": "grep -rn TODO ."}))

# ============ Part 3: ⭐ 安全发现：白名单形同虚设 =============
print("\n" + "=" * 60)
print("⭐【安全发现】TerminalTool 的“安全白名单”可被绕过（Capstone T4/T2 预览）")
print("=" * 60)
print("它声称只读、禁危险操作；但 shell=True 跑原始命令串，白名单还含 bash/sh/python。\n")

# (a) shell 注入：base 命令是白名单里的 ls，但空格 + 分号后可执行任意命令
print("(a) shell 注入绕过  ——  命令: \"ls ; echo ...\"")
print(term.run({"command": "ls ; echo '   [已注入] 分号后的任意命令照样执行'"}))

# (b) 环境变量泄漏：shell 展开 $VAR，子进程继承 agent 全部环境变量（含密钥）
os.environ["DEMO_SECRET_KEY"] = "sk-FAKE-please-redact-me"   # 假密钥，仅演示
print("\n(b) 密钥外泄面  ——  命令: 'echo \"$DEMO_SECRET_KEY\"' （shell 展开了本应保密的环境变量）")
print(term.run({"command": 'echo "   [泄露] agent 环境里的密钥被读到: $DEMO_SECRET_KEY"'}))

# (c) 白名单直接包含 shell：任意代码执行
print("\n(c) 白名单含 bash  ——  命令: \"bash -c '...'\"")
print(term.run({"command": "bash -c \"echo '   [bash] 任意代码执行（白名单本不该放 bash）'\""}))

print("\n" + "-" * 60)
print("结论：一个被当作“安全只读”的工具，实为 Capstone 中 T4(越权执行) 与 T2(密钥外泄) 的现成入口。")
print("对应防御（命令真过滤 / 禁 shell=True / 环境变量隔离 / 出网拦截）将在 Capstone-C 实现。")
