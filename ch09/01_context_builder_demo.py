"""第9章 §9.3 ContextBuilder 演示：GSSC 流水线如何把多源信息拼成结构化上下文。
纯本地运行，不需要 LLM / 嵌入模型，几秒出结果。
运行: cd hello-agents-lab && .venv/bin/python ch09/01_context_builder_demo.py
"""
from hello_agents.context import ContextBuilder, ContextConfig, ContextPacket
from hello_agents.core.message import Message

# ---------- 1) 准备多源候选信息（模拟 Gather 的输入）----------
system_instructions = (
    "你是一个资深 Python 代码审查助手。"
    "只依据提供的证据作答，缺证据时明确说明。"
)

# 对话历史 → 会进入 [Context] 段
history = [
    Message(role="user", content="帮我看看 order 模块有没有问题"),
    Message(role="assistant", content="好的，我先扫描 order 相关文件。"),
]

# 额外上下文包：用 metadata["type"] 决定它进入模板的哪个分区
extra_packets = [
    ContextPacket(
        content="当前任务：审查 order.py；已发现 1 个未关闭的数据库连接，待修复。",
        metadata={"type": "task_state"},        # → [State]
    ),
    ContextPacket(
        content="证据：order.py:42 `conn = db.connect()` 之后无 conn.close()，存在连接泄漏。",
        metadata={"type": "knowledge_base"},    # → [Evidence]
    ),
]

# ---------- 2) 配置并构建 ----------
config = ContextConfig(
    max_tokens=2000,
    reserve_ratio=0.15,
    min_relevance=0.0,   # 演示用：先关掉相关性过滤，保证各源都进来（下面会解释为什么要关）
)
builder = ContextBuilder(config=config)   # 不接 memory/rag，纯演示 GSSC 结构

context = builder.build(
    user_query="order.py 有哪些隐患？怎么修？",
    conversation_history=history,
    system_instructions=system_instructions,
    additional_packets=extra_packets,
)

print("=" * 64)
print("GSSC 组装出的结构化上下文（这一整段就是要喂给 LLM 的 prompt）:")
print("=" * 64)
print(context)
print("=" * 64)
print(f"可用 token 预算 = max_tokens*(1-reserve_ratio) = "
      f"{config.max_tokens}*(1-{config.reserve_ratio}) = {config.get_available_tokens()}")
