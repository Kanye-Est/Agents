# 组会论文分享方案：从 Retrieval Barrier 到真实 Skill 供应链

**推荐主讲**：

1. *Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild for LLM Systems*  
   Hongyan Chang et al.，USENIX Security 2026
2. *“Do Not Mention This to the User”: Detecting and Understanding Malicious Agent Skills in the Wild*  
   Yi Liu et al.，USENIX Security 2026

**分享目标**：不是把两篇论文各复述一遍，而是回答一个共同问题：

> 真实的 agent 供应链风险，需要同时满足“恶意供给存在”和“恶意对象能穿过中间获取门”。
> 两篇论文分别把这两半做扎实；我的工作想测它们在 agent skill acquisition 中如何接起来。

---

## 1. 为什么是这两篇

| 选择标准 | IPI | Do Not Mention |
|---|---|---|
| 正式发表质量 | USENIX Security 2026 | USENIX Security 2026 |
| 问题定义 | 指出既有 IPI 评测常跳过 retrieval barrier | 指出 agent skill 生态缺少行为确认的恶意样本测量 |
| 方法完整度 | 黑盒优化 + 11 数据集 + 8 embedding + E2E + 防御 | 98,380 规模测量 + 静态筛查 + 动态沙箱 + 人工复核 + disclosure |
| 对我研究的作用 | 方法学祖先：不能默认中间步骤自动发生 | 现实性锚点：恶意 skill 的供给不是假设 |
| 能引出的缺口 | retrieval 之后仍有 execution pipeline | 发现恶意 skill 不等于 agent 会自主获取它 |

### 候选但不作为主讲

- **SCR (`2606.15242`)**：最接近当前定位；适合用 1–2 页说明最新边界。
  优点是测中性组合、observable state change 和 simulated harmful install；
  局限是 TrustLift 从已出现的下游安装请求开始，市场与状态是 controlled simulation。
- **HalluSquatting (`2607.07433`)**：真实 agentic 应用、真实 tool invocation/RCE，实证冲击力强；
  但起点是用户明确要求 clone/install 一个资源。
- **Semantic SC (`2605.11418`)**：与已完成的 selection 实验最直接；
  但 paired functionally-equivalent selection 与我的跨域专一竞争不是同一设定。

如果组会只允许讲一篇，选 **IPI**。它最能解释研究想法来源，也最适合学习“怎样把一个 barrier
做成完整的顶会论文”。如果老师要求第二篇必须是最新直接竞品，则用 **SCR** 替换 Do Not Mention。

---

## 2. 推荐时长与结构

### 25 分钟版本

| 时间 | 内容 |
|---:|---|
| 2 min | 共同问题与两篇论文的关系 |
| 8 min | IPI：问题、方法、结果、局限 |
| 7 min | Do Not Mention：测量管线、发现、局限 |
| 4 min | SCR / HalluSquatting 最新邻居对比 |
| 3 min | 我的已有结果与待验证问题 |
| 1 min | 讨论题 |

### 只讲论文、不讲自己工作的 18 分钟版本

- IPI 8 分钟；
- Do Not Mention 7 分钟；
- 共同启示与开放问题 3 分钟。

---

## 3. Slide-by-slide 提纲

### Slide 1 — 标题与共同问题

标题建议：

> **Agent 供应链风险：恶意对象存在之后，真的能进入执行链吗？**

只讲三句话：

1. Do Not Mention 证明现实 skill registry 中确实存在行为确认的恶意供给；
2. IPI 证明“恶意内容存在”不等于“会被检索”，中间 barrier 不能跳过；
3. 我的兴趣是：对尚未安装的第三方 skill，这条 acquisition 链在哪里断。

### Slide 2 — 两篇论文如何拼起来

```text
真实恶意供给                  中间获取门                    执行后果
Do Not Mention        IPI 提供 barrier 方法模板        Skill-Inject / Poise
98,380→4,287→157      Vanilla→CEM→E2E               post-load 高风险
```

注意：这张图是研究问题拼图，不表示三篇论文的 ASR 可直接比较。

---

### Slide 3 — IPI 的问题

既有 IPI 工作常把恶意文档直接放进 context，或者构造保证会检索到的环境。
IPI 论文问的是：

> 在自然查询和真实规模语料库中，未优化的恶意文档到底会不会被检索？

核心研究动作：把 attack fragment 和 retrieval trigger 分开。

### Slide 4 — IPI 的方法

- Threat model：攻击者能投毒外部 corpus，只能黑盒查询 embedding API；
- 优化目标：提高恶意文档相对目标 query 的相似度；
- 方法：Cross-Entropy Method（CEM），维护每个 token 位置的采样分布，
  每轮保留高分 elite samples 后更新分布；
- 约束：短 trigger、有限 API 查询预算、攻击载荷保持不变。

讲法重点：不用推完整公式，只解释“黑盒采样—选优—收缩分布”。

### Slide 5 — IPI 的实验设计

- 11 个 BEIR retrieval 数据集；
- 8 个开源/闭源 embedding 模型；
- 每个数据集抽样 100 个 target queries；
- 每个 query 注入 1 个恶意文档；
- 主指标 Recall@5；
- 进一步在 RAG、agent、多 agent 系统中测 E2E。

### Slide 6 — IPI 的结果与局限

可靠表述：

- Vanilla 在主 retrieval 实验的 11 个数据集上都未进入 top-5；
- 短 trigger 在多个数据集上达到接近满召回，困难语料可通过更长 trigger 提升；
- 一个多 agent 邮件场景中，对 SSH key exfiltration 的 E2E 成功率超过 80%；
- 论文同时测了若干防御，未完全阻止 retrieval。

讨论局限：

- 攻击是 query-targeted，生成 trigger 需要能为目标 query 查询 embedding；
- “natural query”不等于任意未知用户意图；
- 检索成功仍不等于每个 downstream 系统都会执行载荷；
- 其方法适合 embedding 检索，未必直接迁移到 LLM-based skill search/selection。

### Slide 7 — IPI 对我研究的启示

可以直接讲：

> 我从它学到的不是“把 CEM 再跑一遍”，而是：不要把攻击链最难的一步当成前提。
> 我先测了 skill selection，随后发现真正需要拆的是 discovery→install→runtime。

展示自己三档结果时必须带条件：

| 条件 | 结果 |
|---|---:|
| 单模型/单框架、20 任务、恶意 skill 已预装 | |
| Vanilla | 0/20 |
| 通用 Query+ | 2/20 |
| 5 轮 LLM 优化 | 1/20 |

不要说“skill selection 比 retrieval 更安全”；只能说该设定下存在先导性 selection friction。

---

### Slide 8 — Do Not Mention 的问题与数据

论文问：公开 skill registry 里真实恶意 skill 有多少、长什么样、如何验证？

测量漏斗：

```text
98,380 个公开 skills
       ↓ 静态规则 / LLM 文本分析
4,287 个候选
       ↓ Docker 动态验证
762 个触发 runtime indicator
       ↓ 两位研究者独立复核
157 个行为确认恶意 skills
       ↓
632 个漏洞实例，覆盖 13 种实际出现的技术
```

### Slide 9 — Do Not Mention 的验证质量

- Docker 隔离执行；
- 网络、系统调用和文件系统监控；
- honeypot credentials；
- 三种触发方式：metadata-driven、LLM 生成输入、多轮调用；
- 只有观察到外泄、未授权网络、解码后隐藏功能或提权等行为才进入人工确认；
- 157/157 经披露后被 registry 移除。

讲清楚：`157/98,380 = 0.16%` 是高精度行为确认下的下界，不是“生态只有 0.16% 有风险”。

### Slide 10 — Do Not Mention 的核心发现

- 单个恶意 skill 平均包含 4.03 个漏洞/技术实例；
- 84.2% 的漏洞涉及 SKILL.md 自然语言面；
- 73.2% 的确认样本存在“文档功能与实际行为不一致”的 shadow features；
- 单一行为者贡献了 54.1% 的确认恶意 skills，说明总体统计受 campaign concentration 影响；
- 60 秒沙箱、环境检测和 dormant triggers 可能造成漏检。

### Slide 11 — Do Not Mention 对我研究的启示

它回答了：

> 外部市场里有没有真实恶意 skill？有，而且已有规模化、隐蔽化供应。

它没有回答：

> 当用户只给普通任务时，agent 是否会自主把这些第三方 skill 发现、安装并调用？

因此生态测量为 acquisition risk 提供现实性，但不能替代 acquisition E2E 实验。

---

### Slide 12 — 最新邻居校准：SCR 与 HalluSquatting

| 论文 | 已经做到 | 没有覆盖 |
|---|---|---|
| SCR-CapFlow | Neutral task language；available-skill composition；observable mock state change | 外部发现与安装 |
| SCR-TrustLift | endorsement 使 simulated harmful install 平均 1.10%→83.89% | 从普通能力任务自主发现开始；真实 on-disk/registry/invoke |
| HalluSquatting | 显式 clone/install 请求下的真实 tool invocation / RCE，40%–100% | 用户没有 acquisition 意图的 ordinary task 起点 |

必须说出的自我修正：

> 我之前把 SCR 整体说成“只测预装 skill”是不准确的；TrustLift 已经测了模拟市场安装。
> 因此我的问题必须收紧到 ordinary-task 触发、外部发现、真实安装/注册/调用的同轨迹测量。

### Slide 13 — 当前研究问题

```text
ordinary capability task
  → search issued
  → target retrieved
  → install call emitted
  → parsed / executed
  → installed on disk
  → registered
  → invoked
  → payload & task_ok
```

研究问题：

1. 哪一段是稳定瓶颈？
2. tool budget / parser / permission policy / scaffold 是否比模型更决定 E2E？
3. explicit-install、simulated-install 与 ordinary-task E2E 的结果能否互相外推？

### Slide 14 — 讨论题

建议只留两个：

1. 一个“全链逐段测量”要出现什么级别的结构性结果，才够成为 security measurement paper？
2. 为了避免只做玩具市场，正式实验至少需要哪些真实系统要素：真实 registry、真实落盘、多个 scaffold，还是生产 agent？

---

## 4. 组会上必须避免的表述

| 不要说 | 改成 |
|---|---|
| “现有工作都没有测 E2E” | HalluSquatting 已测显式安装条件下的真实 E2E/RCE |
| “SCR 只组合预装 skill” | CapFlow 是 available-skill composition；TrustLift 已测 simulated market install |
| “所有论文都把单段 ASR 当成 E2E” | endpoint 与起点不同，不能直接横比或外推 |
| “我的 0%–10% 证明明确任务天然安全” | 单模型/单框架/20 任务的先导观察，需扩大验证 |
| “低安装率也一定能发论文” | 只有低且有稳定结构、可解释、可跨设置复现，才可能成为结果 |
| “research gap 就是 novelty” | gap 只提出问题；贡献要来自新测量、新现象、方法或防御 |

---

## 5. 备答：可能被问的问题

### Q1：你的 idea 会不会只是把现有阶段拼起来？

答：

> 如果只是画一条长链，确实不够。pilot 的目标是检验端点之间是否有稳定的 execution gap，
> 以及 scaffold/policy 是否系统性改变风险。只有得到可复现的结构性发现，才继续做正式论文。

### Q2：SCR 已经测安装，你还有什么不同？

答：

> SCR-TrustLift 测的是上游背书如何改变一个已出现的下游安装请求，安装发生在 simulated skill market。
> 我想测的是用户没有提出 acquisition 意图时，agent 是否会从普通能力缺口自主发起外部发现，
> 并在真实 runner 中完成 on-disk、registry 和 invocation。差异必须用同轨迹实验做出来，而不能只靠措辞。

### Q3：如果 ordinary task 下完全不安装怎么办？

答：

> “不安装”本身不够。只有当漏斗显示稳定断点，并能通过 budget/policy/scaffold 消融解释，
> 或证明显式安装/post-load 指标系统性不能外推，才有 measurement 价值；否则按预先规则 No-Go。

### Q4：为什么不直接用真实 ClawHub？

答：

> pilot 先用隔离市场保证阶段可控、状态可审计。若信号成立，正式实验必须加入真实 registry snapshot
> 或至少复刻真实 ranking/manifest/permission 流程，并在隔离目录中做真实安装验证。

### Q5：你自己的 selection 结果与 Semantic SC 的 77.6% 冲突吗？

答：

> 不冲突。Semantic SC 是功能等价 skill 的 paired choice；我的实验是“通用恶意 skill”
> 与多个跨域专一工具竞争。竞争结构不同，正好说明 selection ASR 必须连同候选集定义一起报告。

---

## 6. 论文入口

- [IPI — USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan)
- [Do Not Mention — USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/liu-yi)
- [SCR — arXiv:2606.15242](https://arxiv.org/abs/2606.15242)
- [HalluSquatting — arXiv:2607.07433](https://arxiv.org/abs/2607.07433)
- [Semantic SC — arXiv:2605.11418](https://arxiv.org/abs/2605.11418)
