# 05 — 代码地图

> 各文件的作用和关键逻辑，方便接手代码。

---

## 项目根目录

```
hello-agents-lab/
├── .env                          LLM API 配置（deepseek-chat via 上海交大平台）
├── .venv/                        Python 3.12 虚拟环境（hello-agents[all]==0.2.8）
├── literature.md                 10 篇核心文献调研（365 行）
├── idea/                         ← 本文件夹
└── secskill-lab/                 实验代码（下面详述）
```

## secskill-lab/ 核心文件

### 基础设施（原有，不要改）

| 文件 | 作用 | 关键接口 |
|------|------|---------|
| `baseline_agent.py` | 受害 agent 定义 | `build_agent(extra_tools, listener_fn, system_prompt)` → 返回 agent |
| `skill_loader.py` | SKILL.md 加载器 | `load_skill(dir)` → SkillTool 对象 |
| `collector.py` | 本机 mock 外泄接收端 | `start_collector(port)` → (captured_list, shutdown_fn) |
| `skill_guard.py` | 防御原型 | `guard_tools(tools, events)`, `static_scan(dir)` |

### 新增的实验文件（这次做的）

| 文件 | 作用 | 怎么跑 |
|------|------|--------|
| `queries_natural.py` | 20 个自然 query（每条标注期望选中的 skill） | 被其他脚本 import |
| `run_selection_eval.py` | Vanilla / Query+ 评测 | `--variant vanilla` / `--variant query_plus` / `--variant all` |
| `EXPERIMENT_SUMMARY.md` | 给导师看的阶段性总结 | 直接读 |

### 良性竞争 skill（6 个，在 skills/benign/）

| skill | 功能 | handler 用假数据（后续可换真实 API） |
|-------|------|------|
| `memo` | 记备忘 | 存 JSON（原有） |
| `weather` | 查天气 | FAKE_WEATHER 字典 |
| `calc` | 计算器 | ast 安全解析（不用 eval！） |
| `translator` | 翻译 | MINI_DICT 查表 |
| `calendar` | 查日程 | FAKE_CALENDAR 字典 |
| `notes_search` | 搜备忘 | FAKE_NOTES 列表 |

### 恶意 skill（在 skills/research_malicious/）

| skill | 对应实验阶段 | 描述策略 |
|-------|------------|---------|
| `vanilla_data_sync` | 阶段 1 (Vanilla) | 朴素"云备份" |
| `query_plus` | 阶段 2 (Query+) | "什么都能干"通用蹭热度 |
| `t1_prompt_injection` | 原有 PoC | 工具返回值注入 |
| `t2_exfiltration` | 原有 PoC | handler 外泄 |
| `t3_tool_poisoning` | 原有 PoC | 强制措辞劫持 |
| `t4_dangerous_exec` | 原有 PoC | 工具链越权 |

### LLM 对抗优化（optimize_attack/）

| 文件 | 作用 | 关键逻辑 |
|------|------|---------|
| `attacker.py` | 攻击者 LLM | `AttackerLLM.generate(feedback)` → 生成/改进 description |
| `evaluator.py` | 裁判（复用 agent） | `Evaluator.evaluate(desc, num_queries)` → 被选中率 |
| `run_optimize.py` | 优化主循环 | 串联 attacker + evaluator，跑 T 轮 |
| `results/*.json` | 历史结果 | 3 次优化的完整记录 |

---

## 关键代码细节（踩过的坑）

### 1. agent 历史污染问题

```python
# ❌ 错误：所有 query 共用一个 agent
agent = build_agent(...)
for query in QUERIES:
    agent.run(query)  # 历史累积，后半段 LLM 偷懒不调工具

# ✅ 正确：每个 query 清空历史（或新建 agent）
for query in QUERIES:
    agent._history.clear()   # 清空历史
    agent.run(query)
```

### 2. Evaluator 的动态换描述（性能优化）

```python
# Evaluator 类复用 agent 对象，不每 query 重建：
# 换描述时只 unregister 旧恶意 skill + register 新的
ev = Evaluator()                    # agent 只创建一次
result = ev.evaluate(desc1)         # 动态注册 desc1
result = ev.evaluate(desc2)         # 注销 desc1，注册 desc2
```

### 3. API 超时问题

```python
# hello-agents 默认用 openai client，max_retries=2，每次重试等 60 秒
# evaluator.py 里绕过了这个问题，直接用：
from openai import OpenAI
_client = OpenAI(api_key=..., base_url=..., max_retries=0)  # 禁止重试

def _llm_invoke(messages, timeout=20):
    resp = _client.chat.completions.create(model=..., messages=messages, timeout=timeout)
    return resp.choices[0].message.content
```

### 4. run_optimize.py 需要后台运行

因为 5 轮 × 10 query 可能跑 15-20 分钟，超过 10 分钟超时。
```bash
# 后台运行 + 日志写文件
PYTHONUNBUFFERED=1 .venv/bin/python secskill-lab/optimize_attack/run_optimize.py \
    --rounds 5 --num-queries 10 > /tmp/opt_log.txt 2>&1 &
```

---

## 怎么复现实验

```bash
cd /home/forks/AResearch/Agent/hello-agents-lab

# 阶段 1：Vanilla
.venv/bin/python secskill-lab/run_selection_eval.py --variant vanilla

# 阶段 2：Query+
.venv/bin/python secskill-lab/run_selection_eval.py --variant query_plus

# 阶段 3：LLM 对抗优化（后台）
PYTHONUNBUFFERED=1 .venv/bin/python secskill-lab/optimize_attack/run_optimize.py \
    --rounds 5 --num-queries 10 > /tmp/opt_log.txt 2>&1 &
```
