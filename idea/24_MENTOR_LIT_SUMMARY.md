# 文献与研究进展汇报：Agent Skill Acquisition

**日期**：2026-07-24  
**用途**：导师私聊汇报的附件底稿；组会选篇依据  
**材料范围**：已收集 44 篇 PDF，正文聚焦 31 篇高相关工作；本次对最接近定位的
Semantic SC、SCR、HalluSquatting、SearchGEO、Skills That Don't Exist 回到原文重新核对。

> **汇报结论**：我已从“恶意 skill 预装后能否抢到调用”推进到“普通任务是否会触发 agent
> 自主发现、安装并调用一个尚未安装的第三方 skill”。文献复核后，不能再声称“首次研究 install”、
> “首次测 E2E”或“首次测自主触发”。目前更稳妥、可检验的问题是：
> **把普通能力任务、外部发现、真实安装/注册、调用与逐段事件日志放到同一条运行轨迹中，
> 测量 task-induced acquisition 在哪里衰减，以及现有分段指标能否外推到这条真实链路。**

---

## 1. 阅读脉络与主要认识

我的阅读不是按论文逐篇罗列，而是围绕一条生命周期组织：

```text
能力缺口 → 发起检索 → 检索命中 → 安装调用输出 → 解析/执行
        → 文件落盘 → 注册可用 → 实际调用 → 载荷与任务结果
```

这里的 **funnel（漏斗）** 只是一个测量框架：记录每一步有多少运行继续存活，
并把“模型说要做”“编排器接受调用”“系统真实执行”“文件已经安装”分开。
它不是在指责现有论文“指标算错”，而是提醒不同论文的**起点、终点和成功定义不同，数字不能直接横比**。

| 文献区域 | 代表工作与可靠结论 | 对当前研究的影响 |
|---|---|---|
| 检索瓶颈 | **IPI / Overcoming the Retrieval Barrier**（USENIX Security 2026）：11 个检索数据集、8 个 embedding 模型；Vanilla 在其主实验中无法进入 top-5，CEM 优化后在多设置接近满召回 | 提供“不要默认中间步骤会自动发生”的方法模板 |
| 真实 skill 生态 | **“Do Not Mention This to the User”**（USENIX Security 2026）：98,380 个 skill → 4,287 个静态候选 → 157 个行为确认恶意 skill；动态验证与人工复核后得到 632 个漏洞实例 | 证明恶意供给是真实生态问题，不只是合成 benchmark |
| Registry 发现/选择 | **Semantic SC**（`2605.11418`）：真实 ClawHub 样本；Discovery 86.14% pairwise win、80% Top-10；功能等价 paired selection 中对抗版本平均 77.6% | Discovery/selection 已有强邻居；我的 0%–10% 是不同竞争结构，不能声称推翻该文 |
| 装后危害 | **Skill-Inject / Poise**（`2602.20156` / `2606.07943`）：skill 已加载后，载荷成功率可很高，并可同时保持任务完成 | post-load 不是主要 novelty，可作为 acquisition 成功后的危害上界 |
| 路径组合与促装 | **SCR**（`2606.15242`）：CapFlow 的 Neutral 组合平均 ASR 33.6%；TrustLift 在模拟 skill market 中把有害安装从平均 1.10% 提至 83.89% | 不能说“SCR 只测预装 skill”；它已覆盖自主组合和模拟促装，但不从普通任务自主发现开始，也不测真实落盘/注册/调用全链 |
| 真实安装/RCE | **HalluSquatting**（`2607.07433`）：在真实 agentic 应用中测到 tool invocation / RCE；不同配置下 E2E 为 40%–100% | 不能说“首次真实 E2E”；但该文由用户明确的 clone/install 资源请求触发 |
| 推荐/命令端点 | **SearchGEO**（`2606.16821`）的 skill 部分是 18 例辅助 probe，GPT-5.4-mini 接受伪造 skill 并输出安装命令 17/18；**Skills That Don't Exist**（`2607.12340`）主测 skill 名幻觉，agent 平均 36.9%，另在明确安装指令下做 benign install PoC | 说明 recommendation / emitted command / install PoC 都已有覆盖，但不是 ordinary-task 同轨迹全链 |

---

## 2. 我已经做出的进展

### 2.1 已完成：预装条件下的 selection 实验

- 环境：HelloAgents + deepseek-chat；6 个良性专一 skill + 1 个恶意 skill；20 个自然任务。
- 三档描述：Vanilla `0/20`、通用 Query+ `2/20`、5 轮 LLM 对抗优化 `1/20`。
- 中招集中在模糊/跨域任务；本样本中明确单域任务均选择了专一工具。

这组结果支持一个**先导观察**：在“已有正确专一工具”的竞争结构里，仅靠把恶意 skill
描述成“全能助手”很难抢到调用。它还不是跨模型普适结论，因为目前只有单模型、单框架和 20 个任务。

### 2.2 已搭建：Acquisition 最小链路

- 已有 marketplace、`search_skills`、`install_skill` 和阶段日志雏形。
- 一次 A2 调试中，模型输出了 `install_skill(...)`，但默认 3 轮 tool budget 已耗尽，
  调用没有进入真实执行。
- 这说明 `call_emitted` 与 `install_executed` 必须拆开；目前它只是**发现测量问题的调试证据**，
  还不能写成“execution gap 稳定存在”的研究结论。

---

## 3. 研究定位：哪些话不能说，什么问题仍值得测

### 3.1 已明确放弃的表述

| 不再声称 | 原因 |
|---|---|
| “第一个研究 agent skill install” | SCR-TrustLift、HalluSquatting、SearchGEO、Skills That Don't Exist 均已覆盖不同形式的安装或安装端点 |
| “第一个测真实执行 / E2E” | HalluSquatting 已在真实应用中测 tool invocation 与 RCE；SCR 用 observable mock state-change 计分 |
| “第一个测自主 / 中性触发” | SCR-CapFlow Neutral 已测中性任务语言下的自主组合 |
| “现有论文都把单段 ASR 冒充 E2E” | 这是没有证据的过度概括；准确说法是各文的起点与 endpoint 不同，不能脱离条件直接横比 |
| “SCR 的 skill 都是预装的” | 只适用于 CapFlow 的 available-skill 组合；TrustLift 已测 simulated market 中的有害安装 |

### 3.2 当前可守、但仍需系统检索验证的问题

> **在已核对的最接近工作中，尚未看到一篇同时满足以下条件：**
>
> 1. 用户只给普通能力任务，不要求 search / install / skill；
> 2. 目标 skill 在任务开始时尚未安装；
> 3. agent 需从外部市场自主发现和检索；
> 4. 安装由真实 runner 解析并执行，且用文件、manifest、registry 三重状态验证；
> 5. 同一条轨迹继续测到调用、载荷与用户任务是否完成；
> 6. 对每个阶段做可审计的逐段归因。

这比“两个条件的合取”更准确：真正可能有价值的不是一个狭窄措辞，而是
**task-induced acquisition 的同轨迹、系统级测量**。

需要特别说明：**research gap 本身不是论文贡献。** 顶会价值取决于 pilot 是否得到以下至少一种稳定结果：

- ordinary task 下出现跨任务、跨模型可复现的真实自主安装；
- emitted、executed、on-disk、registered 之间存在结构化落差，且能归因到 tool budget、parser、policy 或 scaffold；
- post-load / explicit-install 的高成功率无法预测 ordinary-task E2E，且差异可量化；
- 一个简单 acquisition gate 或 provenance policy 能显著降低风险且保持任务效用。

如果所有阶段都低、没有结构、换模型/框架也无稳定差异，就应 No-Go，而不是把“低 ASR”强行包装成结论。

---

## 4. 组会精讲建议

### 主推荐：两篇均为 USENIX Security 2026

#### ① *Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild for LLM Systems*

- **为什么选**：正式顶会论文；问题定义、分阶段测量、CEM 黑盒优化和真实 E2E 验证都完整。
- **与我的关系**：这是 selection barrier 与 acquisition funnel 的方法来源。讲完后能自然解释：
  我不是简单复制它的 CEM，而是迁移它“不要跳过中间门”的研究方法。
- **组会最值得讨论**：一个单段 barrier 何时能升级成完整论文？它如何用规模、优化方法、E2E 和防御评估把故事做厚？

#### ② *“Do Not Mention This to the User”: Detecting and Understanding Malicious Agent Skills in the Wild*

- **为什么选**：正式顶会论文，且直接研究 agent skill 供应链；98,380→4,287→157 的测量漏斗、动态沙箱验证、人工复核和 responsible disclosure 都很扎实。
- **与我的关系**：它回答“恶意 skill 是否真实存在”，但不回答“普通任务会不会让 agent 自主把它获取进来”。
  因此它与 IPI 正好形成“真实恶意供给 + 中间获取门”的组合。
- **组会最值得讨论**：如何把大规模生态测量、行为确认和攻击链 taxonomy 做成可信的 security measurement paper？

### 为什么不把 SCR / HalluSquatting 作为主讲两篇

它们是**定位上更近的必读邻居**，应在组会比较页中重点讲，但截至 2026-07-24 的公开页面仍是 arXiv
预印本。若组会的首要标准是论文成熟度和可复用的方法论，优先讲两篇已录用的 USENIX 工作更稳妥。

如果老师希望第二篇必须是“最新、最贴近当前想法”，则把第 ② 篇替换为 **SCR**：
它最能迫使我说明“模拟促装/skill composition”与“ordinary-task 外部 acquisition 同轨迹测量”的区别。
HalluSquatting 更适合放在对比页，作为“显式安装意图下真实 E2E 已经能打到 RCE”的上界。

---

## 5. 下一步与希望老师给的反馈

### 近期计划

1. 修 instrumentation：可配置 tool budget；拆分 emitted / parsed / executed / on-disk / registered / invoked；
2. 使用临时目录、manifest 和 registry 验证“真实安装”，避免只看模型文本；
3. 先做 60–100 runs 的小 pilot，覆盖 ordinary / explicit-install / no-gap / irrelevant controls；
4. 根据预先规则做 Go/No-Go，再决定是否扩模型、框架和任务家族。

### 希望老师重点判断

1. **研究问题是否值得继续**：把贡献定位为 task-induced autonomous acquisition 的系统测量，
   而不是“首次 install”或单纯攻击成功率；
2. **pilot 是否足以决定 Go/No-Go**：先验证阶段衰减有没有稳定结构，再投入正式实验；
3. **组会选篇是否采用 IPI + Do Not Mention**：一篇讲 barrier 方法，一篇讲真实 skill 生态，
   最后用 SCR / HalluSquatting 比较页引出我的边界。

---

## 6. 核心论文链接

- [Overcoming the Retrieval Barrier — USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan)
- [“Do Not Mention This to the User” — USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/liu-yi)
- [Semantic SC — arXiv:2605.11418](https://arxiv.org/abs/2605.11418)
- [SCR — arXiv:2606.15242](https://arxiv.org/abs/2606.15242)
- [HalluSquatting — arXiv:2607.07433](https://arxiv.org/abs/2607.07433)
- [SearchGEO — arXiv:2606.16821](https://arxiv.org/abs/2606.16821)
- [Skills That Don't Exist — arXiv:2607.12340](https://arxiv.org/abs/2607.12340)

*安全说明：本地实验只使用合成任务与合成敏感数据；payload 仅写 marker 或发送到
`127.0.0.1` collector，不进行真实外泄。*
