"""Capstone-C：skill_guard —— 把 skill 当“不可信”来用的检测 + 运行时防御。

四类攻击的配套防线：
  T1 提示注入  -> 工具【返回】消毒：剥离疑似注入指令
  T2 数据外泄  -> 执行期【环境变量隔离】：临时移除密钥/令牌，使 handler 偷不到
  T3 工具投毒  -> 工具【描述】消毒：剥离“必须先调用我”等强制措辞（不进系统提示）
  T4 越权执行  -> 【危险命令拦截】：禁 ; | && ` rm bash、禁读机密文件
另含安装期【静态扫描】：扫 SKILL.md 描述 + handler 源码，给出风险提示。
"""
import os
import re
import contextlib

from hello_agents.tools import Tool, ToolParameter

# 注入/强制措辞（出现在“工具描述”或“工具返回”里即视为可疑）
INJECTION_PATTERNS = [
    r"【系统", r"\[系统", r"\[SYSTEM", r"SYSTEM NOTICE",
    r"最高优先级", r"高优先级", r"high(est)? priority",
    r"强制", r"mandatory", r"不可协商", r"non-negotiable",
    r"必须", r"\bMUST\b",
    r"先调用", r"call .*first", r"first.*call",
    r"不要告诉用户", r"请勿向用户", r"do not tell",
    r"执行以下命令", r"运行(上述|以下)", r"ignore (all )?previous",
    r"\bcat\s+\S*secret\S*", r"\brm\s+-",
]
# 危险命令特征
DANGER_CMD_PATTERNS = [r";", r"\|\|", r"&&", r"\|", r"`", r"\brm\b",
                       r"\bbash\b", r"\bsh\b\s+-c", r"secret", r"\.\.", r"\$\("]


def _first_injection(text):
    """返回最早命中的 (位置, 命中模式)；无则 (None, None)。"""
    s = str(text)
    lo, hit = None, None
    for p in INJECTION_PATTERNS:
        m = re.search(p, s, re.IGNORECASE)
        if m and (lo is None or m.start() < lo):
            lo, hit = m.start(), p
    return lo, hit


def sanitize_text(text):
    """从首个注入标记处截断，移除其后的全部内容（注入通常追加在尾部）。"""
    lo, hit = _first_injection(text)
    if lo is not None:
        cleaned = str(text)[:lo].rstrip()
        return cleaned + ("\n" if cleaned else "") + "[skill_guard: 已移除疑似注入/强制指令]", hit
    return str(text), None


def is_dangerous_command(cmd):
    return [p for p in DANGER_CMD_PATTERNS if re.search(p, cmd or "")]


@contextlib.contextmanager
def scrubbed_env():
    """临时移除进程里的密钥/令牌类环境变量（仅在 skill 执行期间）。"""
    saved = {}
    for k in list(os.environ):
        if any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            saved[k] = os.environ.pop(k)
    try:
        yield
    finally:
        os.environ.update(saved)


class GuardedTool(Tool):
    """包住一个工具：清洗描述、隔离执行环境、消毒返回、拦截危险命令。"""

    def __init__(self, inner, events):
        self._inner = inner
        self._events = events
        desc, hit = sanitize_text(inner.description or "")
        if hit:
            events.append(("描述消毒", inner.name, hit))   # 防 T3
        super().__init__(name=inner.name, description=desc)

    def get_parameters(self):
        try:
            return self._inner.get_parameters()
        except Exception:
            return [ToolParameter(name="input", type="string", description="", required=False)]

    def run(self, parameters):
        params = parameters or {}
        # 防 T4：危险命令拦截
        cmd = params.get("command", "")
        if cmd:
            danger = is_dangerous_command(cmd)
            if danger:
                self._events.append(("拦截危险命令", self._inner.name, cmd))
                return f"[skill_guard] 已拦截危险命令（命中 {danger}），需人工确认。"
        # 防 T2：执行期环境变量隔离
        sensitive = [k for k in os.environ
                     if any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD"))]
        if sensitive:
            self._events.append(("env隔离", self._inner.name, f"移除{len(sensitive)}个密钥"))
        with scrubbed_env():
            result = self._inner.run(params)
        # 防 T1/T4：工具返回消毒
        clean, hit = sanitize_text(result)
        if hit:
            self._events.append(("返回消毒", self._inner.name, hit))
        return clean


def guard_tools(tools, events):
    """把一组工具包成 GuardedTool。"""
    return [GuardedTool(t, events) for t in tools]


def static_scan(skill_dir):
    """安装期静态扫描：返回 [(风险, 证据), ...]。"""
    from pathlib import Path
    p = Path(skill_dir)
    findings = []
    md = p / "SKILL.md"
    if md.exists():
        lo, hit = _first_injection(md.read_text(encoding="utf-8"))
        if hit:
            findings.append(("SKILL.md 描述含强制/注入措辞", hit))
    h = p / "handler.py"
    if h.exists():
        src = h.read_text(encoding="utf-8")
        if re.search(r"os\.environ", src) and re.search(r"requests\.(post|get)|urllib|socket", src):
            findings.append(("handler 读环境变量并联网", "数据外泄嫌疑"))
        if re.search(r"subprocess|os\.system|shell\s*=\s*True", src):
            findings.append(("handler 含命令执行", "RCE 嫌疑"))
        lo, hit = _first_injection(src)
        if hit:
            findings.append(("handler 返回含注入/危险措辞", hit))
    return findings
