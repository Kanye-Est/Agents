# 06 — 关键概念对照表

> IPI 论文术语 ↔ skill injection 对应物。
> 理解这张表，才能把 IPI 的思路迁移到 skill injection。

---

## 核心结构对照

| 概念 | IPI 论文（retrieval 场景） | 本项目（skill selection 场景） |
|------|--------------------------|------------------------------|
| **攻击载体** | 毒文档（ planted in corpus） | 恶意 skill（注册到 agent 工具列表） |
| **"被选中"的决策者** | embedding 模型 | LLM（agent 的 tool selection） |
| **决策机制** | cosine similarity（数学函数） | LLM 语言理解（读描述→推理→输出 TOOL_CALL） |
| **决策的输入** | query 向量 vs 文档向量 | 用户 query vs 所有 skill 的 description |
| **瓶颈名称** | retrieval barrier | **skill selection barrier** |
| **攻击的"前半段"** | trigger fragment（骗检索） | 恶意 description（骗 agent 选中） |
| **攻击的"后半段"** | attack fragment（恶意指令） | handler.py（恶意代码执行） |

---

## 方法对照

| 概念 | IPI 论文 | 本项目 |
|------|---------|--------|
| **优化方法** | CEM（Cross-Entropy Method） | LLM 对抗 LLM |
| **优化对象** | 10 个 token 的 trigger | skill 的 description 文字 |
| **打分函数 f(x)** | cosine_sim(E(query), E(x ∥ D_adv)) | 被选中率（跑 N 个 query 后命中比例） |
| **采样/生成** | 从概率矩阵采样 N 个序列 | 攻击者 LLM 生成 K 个候选描述 |
| **选精英** | top-λ 高分序列 | 被选中率最高的描述 |
| **更新/改进** | 用精英频率更新概率矩阵 | 反馈中招/未中招 query 给攻击者 LLM |
| **反馈信息** | 纯分数 | 分数 + 具体 query 文本 + 竞争对手描述 |

---

## 三档 baseline 对照

| 档位 | IPI 论文 | 本项目 | 结果对比 |
|------|---------|--------|---------|
| **Vanilla** | 不优化的毒文档 | 朴素描述的 data_sync | IPI: ≈0% / 我们: **0%** ✅ 一致 |
| **Query+** | 把 query 当 trigger | "什么都能干"通用描述 | IPI: 中等 / 我们: **10%** |
| **Optimized** | CEM 优化的 trigger | LLM 对抗生成的描述 | IPI: ≈100% / 我们: **5%** ⚠️ 差距大 |

---

## 实验设计对照

| 设计要素 | IPI 论文 | 本项目 |
|---------|---------|--------|
| **query 来源** | BEIR benchmark（11 数据集，每集 100 query） | 合成的 20 个自然 query |
| **竞争环境** | 百万级文档语料库 | 6 个良性 skill + 1 内置工具 |
| **注入数量** | 1 篇毒文档（stealth） | 1 个恶意 skill（stealth） |
| **评估指标** | Recall@5（毒文档在 top-5 里吗） | 被选中率（agent 调用了恶意 skill 吗） |
| **端到端指标** | ASR（SSH 密钥被偷了吗） | exfil_happened（collector 收到密钥了吗） |
| **embedding 模型** | 8 个（OpenAI/Voyage/Qwen3/Contriever/GTE） | 不适用（用 LLM 决策，不用 embedding） |
| **LLM** | GPT-4o, GPT-4o-mini, Qwen3, LLaMA-3, Vicuna | deepseek-chat |

---

## 关键差异（为什么方法不能直接套）

### 1. 决策机制不同
- IPI 的 retrieval 是**数学函数**（cosine similarity），可以优化
- skill selection 是 **LLM 决策**，没有梯度、没有公式，是黑盒语言理解

### 2. 攻击粒度不同
- IPI 的 trigger 是 **token 级**（10 个离散 token，CEM 在词表上优化）
- skill 的 description 是**句子级**（一段完整的自然语言文字）

### 3. 防御特性不同
- IPI 没有发现"明确 query 是天然防线"这个现象
- skill selection 有**专一性偏好**：agent 对明确 query 100% 选对专一工具

### 4. 优化难度不同
- IPI 的 CEM 拿到 ≈100%（几乎完美）
- LLM 对抗优化只拿到 5%（非常难突破）
- 这可能是 skill selection 本身比 retrieval 更安全，也可能是方法不对
