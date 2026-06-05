"""Step 0 冒烟测试：验证 .env 能成功调用国产 LLM。
运行： cd hello-agents-lab && .venv/bin/python ch09/smoke_test.py
"""
from pathlib import Path
from dotenv import load_dotenv

# 加载 lab 根目录的 .env（无论从哪个目录运行都能找到）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from hello_agents import HelloAgentsLLM

llm = HelloAgentsLLM()
print(f"✅ 连接信息  provider={llm.provider} | model={llm.model} | base_url={llm.base_url}")

reply = llm.invoke([{"role": "user", "content": "用一句话介绍你自己，并说明你是哪个模型。"}])
print("🗣️  模型回复：", reply)
