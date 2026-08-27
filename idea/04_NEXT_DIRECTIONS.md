# 04 — 下一步方向与文献线索

> 这里记录所有值得尝试的方向，以及能提供灵感的论文。
> 接手者应优先看"立即可做"部分。

---

## 🟢 立即可做（不需要额外资源）

### 方向 1：从已有论文中提取多种攻击策略

目前只试了"通用助手"一种策略。从以下三篇论文中提取至少 5 种不同策略的 description，
逐个测被选中率。

**关键论文**（都在 `literature.md` 里有详细记录）：

#### 🥇 MCPTox（arXiv:2508.14925）—— 最对口
- 研究 Tool Poisoning：恶意指令嵌入 tool metadata/description
- 基于 45 个真实 MCP servers、353 个真实 tools
- 构造约 1.3k 个恶意测试用例，覆盖 10 类风险
- 评测 20 个 LLM agents，部分模型 ASR 很高
- **关键发现**：更强的 instruction-following 能力可能反而更容易被 tool poisoning 利用
- **行动**：去 GitHub 找 MCPTox 代码，把高 ASR 的恶意 description 抄过来测
- 代码搜索关键词：`MCPTox tool poisoning benchmark github`

#### 🥈 MSB - MCP Security Bench（arXiv:2510.15994）—— 给 12 种攻击角度
- 12 类攻击 taxonomy，和"被选中"最相关的：
  - **name-collision**：恶意 skill 名字和良性 skill 撞名/相似
  - **preference manipulation**：靠措辞让 agent 偏好选你
  - **tool description prompt injection**：直接在描述里写注入
  - **false-error escalation**：声称"不调用我会出错"，制造紧迫感
- **行动**：把 12 类里最相关的 4-5 类，每种写一个 description，分别测

#### 🥉 Skill-Inject（arXiv:2602.20156）—— 最贴近 SKILL.md 场景
- 202 个 injection-task pairs，最高 80% ASR
- 项目页：skill-inject.com
- 代码：github.com/aisa-group/skill-inject
- **行动**：clone 代码，看恶意 skill description 的措辞、结构、伪装层次
- 重点看：哪些 task 拿到了 80% ASR，共同特征是什么

**具体执行步骤**：
```bash
# 1. 下载论文 PDF（arXiv 可直接 wget，不需要搜索工具）
wget https://arxiv.org/pdf/2508.14925 -O /tmp/mcptox.pdf    # MCPTox
wget https://arxiv.org/pdf/2602.20156 -O /tmp/skillinject.pdf # Skill-Inject
wget https://arxiv.org/pdf/2510.15994 -O /tmp/msb.pdf         # MSB

# 2. clone 代码
git clone https://github.com/aisa-group/skill-inject /tmp/skill-inject

# 3. 提取恶意 description 模板，逐个用 evaluator 测
```

---

### 方向 2：打印并分析 agent 的完整 system prompt

当前攻击只想着"description 怎么写"，但没看过 agent 实际看到的完整 prompt 长什么样。
打印出来仔细读，可能发现结构性弱点。

```python
# 打印 agent 实际看到的 system prompt
import sys; sys.path.insert(0, 'secskill-lab')
from baseline_agent import build_agent
from skill_loader import load_skill
from pathlib import Path

benign = [load_skill(Path('secskill-lab/skills/benign') / n)
          for n in ['memo','weather','calc','translator','calendar','notes_search']]
agent = build_agent(extra_tools=benign)
print(agent._get_enhanced_system_prompt())
```

**观察重点**：
- 工具的排列顺序（恶意 skill 排第几？排前面/后面有区别吗？）
- 描述的长度差异（更长的描述是否更显眼？）
- 措辞的对比关系（良性描述 vs 恶意描述，LLM 怎么"比"的？）
- 有没有可以"钻空子"的格式特征

---

### 方向 3：构造模糊 query 密集的 query 集

当前 20 个 query 里只有 2 个模糊/跨域的（第 19、20 个）。
已知模糊 query 能被攻破。如果构造一个全是模糊 query 的集合呢？

**新 query 设计方向**：
- "帮我看看最近有什么需要关注的"
- "我下周需要准备什么"
- "帮我整理一下最近的情况"
- "有什么重要的事我可能忘了"
- "今天有什么需要我处理的"

这些都是 agent 不确定该选哪个 skill 的模糊场景，
"通用助手"或"信息整合"策略在这里可能更有效。

---

## 🟡 中期方向（需要更多工程量）

### 方向 4：改变攻击目标——从"骗选中"到"骗安装"

利用 agent 自主安装 skill 的能力（MCP 动态发现 / skill marketplace 检索）。
攻击者不直接让 agent 调用恶意 skill，而是：
1. 让 agent 去 skill 市场搜索某个 skill
2. 恶意 skill 在市场检索中排前面（这里可以用 IPI 论文的 CEM！）
3. agent 自主安装并调用

这把"骗 LLM 判断"转换成"骗向量检索"——后者 IPI 论文已经解决了。

**需要搭建**：
- 一个模拟的 skill marketplace（含检索功能）
- 让 agent 具备"搜索 skill → 安装 → 调用"的完整流程

### 方向 5：多阶段攻击

不追求一次就骗 agent 选中恶意 skill。
而是分多步：先骗它调用一个"看似无害"的中间 skill，
中间 skill 的返回值里夹带指令，引导它调用真正的恶意 skill。

这对应 IPI 论文里"多 agent 放大"的思路——信任会传递。

### 方向 6：跨框架验证

当前只在 hello-agents 测试。扩展到：
- LangChain / LangGraph
- AutoGen
- 原生 MCP agent（Claude Desktop）

看"专一性偏好"是 hello-agents 特有的，还是所有框架的通用现象。

---

## 🔴 长期方向（如果以上都突破不了）

### 方向 7：转向防御视角

如果"攻击 skill selection"确实非常难（也许是 LLM tool selection 的固有安全性），
那可以反过来研究：
- **为什么 LLM tool selection 对描述注入这么鲁棒？**
- **怎么设计 skill 系统让它天然安全？**

这本身也是一个有价值的安全研究（从攻击转向防御）。

### 方向 8：研究 hybrid+rerank 检索攻击

IPI 论文承认没攻破 hybrid+rerank。如果设计出能同时攻破
vector+BM25+reranker 的进阶 CEM，这是纯方法贡献（IPI 的直接 follow-up）。
skill injection 只是它的应用场景之一。

---

## 文献获取方式（搜索工具不可用时的备选）

当前 ZCode 的 web_search 和 web_reader 都被限流（2026-07-12 恢复）。
但可以：

1. **arXiv 直接下载 PDF**（不需要搜索）：
   ```bash
   wget https://arxiv.org/pdf/XXXX.XXXXX -O paper.pdf
   ```

2. **GitHub 直接 clone**（不需要搜索）：
   ```bash
   git clone https://github.com/xxx/yyy
   ```

3. **已有的文献调研**在 `literature.md` 里（365 行，覆盖 10 篇核心论文）

4. **IPI 论文**在 `/home/forks/AResearch/ANL/2601.07072v1.pdf`
