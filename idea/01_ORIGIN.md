# 01 — 这项研究怎么来的

> 记录从读 IPI 论文到产生 skill injection 研究想法的完整思考链。
> 理解这个链条，才能理解为什么我们要做这个实验。

---

## 起点：IPI 论文的核心洞察

读的论文：**Chang et al., "Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild for LLM Systems"**（arXiv:2601.07072，USENIX Security）

### 论文做了什么

这篇论文研究的是 **间接提示注入（IPI）**——黑客在检索语料库里埋毒文档，
等用户提问时毒文档被检索出来，里面的恶意指令被 LLM 执行。

论文最核心的发现是：**前人都假设"恶意内容会被检索到"，但实际不优化的话检索率≈0%。**
真正的瓶颈不是"注入后能干什么"，而是"能不能被检索到"。

### 论文的方法（CEM 算法）

把毒文档拆成两部分：
- **trigger fragment**：5-10 个 token，唯一职责是骗过 embedding 模型的向量检索
- **attack fragment**：真正的恶意指令（偷 SSH 密钥、发钓鱼邮件等）

用 **CEM（Cross-Entropy Method）** 优化 trigger——这是一种黑盒优化算法，
不需要梯度，只用 embedding 模型的 API 调用来打分，通过"采样→选精英→更新分布"的循环逼近最优解。

结果：11 个数据集 × 8 个 embedding 模型，Recall@5 ≈ 100%，成本仅 $0.21/次。

---

## 关键迁移：从 "retrieval barrier" 到 "skill selection barrier"

### 为什么能迁移

| IPI 论文的攻击链 | skill injection 的攻击链 |
|---|---|
| [埋毒文档] → **[被检索]** → [进 LLM 上下文] → [执行] | [注册恶意 skill] → **[被 agent 选中]** → [调用&进上下文] → [执行] |

两者的结构完全一样：都有一个"被选中"的中间步骤，都是前人最容易假设掉的一步。

### 核心假设（待验证）

> **前人的 skill injection 评估都假设"恶意 skill 已被 agent 调用"，
> 但在真实的 skill 竞争环境下（agent 面前有多个良性 skill），
> 恶意 skill 真的会被选中吗？**

如果答案是"不优化就不会被选中"——那就和 IPI 论文一样，
说明 **skill selection 是 skill injection 的真正瓶颈**。

### 核心差异（决定了方法不能直接套）

| 维度 | IPI 论文 | skill injection |
|------|---------|-----------------|
| 谁决定"被选中" | embedding 模型（cosine similarity） | **LLM**（语言理解决策） |
| 攻击对象 | 数学函数（可优化） | **LLM 判断**（黑盒语言层面） |
| 优化方法 | CEM（概率分布进化） | **需要新方法**（LLM 对抗？） |

**这是本研究的核心创新点**：把 IPI 的"CEM vs embedding"范式，
替换成"LLM 对抗 vs LLM"范式。

---

## 之前做的工作（T1-T4 skill injection PoC）

在开始这个新方向之前，已经做了一个 skill injection 的 PoC 项目，
定义了 4 类攻击：

| 攻击 | 伪装成 | 实际危害 | 利用的弱点 |
|------|--------|---------|-----------|
| T1 间接提示注入 | 网页摘要 | 泄漏隐私 | 信任工具**返回值** |
| T2 数据外泄 | 云备份 | 偷传密钥 | handler = 任意代码 |
| T3 工具投毒 | 合规校验 | 劫持工具选择 | 信任工具**描述** |
| T4 越权执行 | 缓存清理 | 删文件/读机密 | 工具链组合越权 |

**这 4 类的共同问题**：都假设恶意 skill 已被调用。
新方向要补的就是"怎么保证它被调用（选中）"这一步。

---

## 导师的建议

1. 先跑实验验证假设（skill 会不会被选中），从 base case 开始，从简到难
2. 做个 summary 给导师讲
3. 觉得"想不出好办法"恰恰说明这个角度值得研究——需要从 agent 运行机制中找灵感
4. 建议在最近的论文上找灵感和解决方案

---

## 关于方法路线的讨论结论

讨论过"进阶 CEM 攻破 hybrid+rerank 检索"的想法，但最终决定：
- **不要把"方法贡献"和"应用贡献"做混**
- 主攻方向是 **skill injection 的端到端攻击**（场景），检索攻击是手段之一
- 现代 agent 已具备自主发现（MCP）、生成（skill-creator）、安装（marketplace）skill 的能力，
  这让 skill injection 的攻击面比以前大得多
