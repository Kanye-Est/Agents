# 逐篇精读文献表单

> 用途：集中保存已经通读并核对原文的论文，但不把所有论文压缩进一张横向总表。
> 每篇论文独立成节，使用相同字段；论文按对当前课题的重要性排序，而不是按阅读或发表时间排序。
>
> 建立日期：2026-08-07  
> 当前已精读：10 篇

## 使用规则

1. 只有完成正文、关键图表、指标定义和 limitation 核对后，才加入本文件。
2. 论文结论、我们的解释和可迁移启发必须分开写。
3. 所有百分比都要说明分母与实验条件；不能把 selection、recommendation、install、payload 和 E2E 混写成 ASR。
4. “与当前工作的关系”分成可直接背书、只能类比和明确差异三部分。
5. 排序综合考虑：与 Acquisition Gap 的直接关系、证据与 venue 质量、对 threat model / method / novelty 的不可替代性，以及导师关注度。
6. 新论文使用文末模板；完成精读后插入合适优先级并统一重编号，同时更新目录和“当前已精读”数量。

## 重要性排序

1. [AgentDojo](#1-agentdojo) — **核心**：导师重点；动态、状态化 Agent 安全评估的直接方法学参照。
2. [Do Not Mention This to the User](#2-do-not-mention-this-to-the-user) — **核心**：高质量真实 skill 生态测量，为恶意供给提供现实依据。
3. [Overcoming the Retrieval Barrier](#3-overcoming-the-retrieval-barrier) — **核心**：USENIX Security 2026；直接证明真实语料库中的 Top-K retrieval 本身是一道可攻击的前置屏障，是 Acquisition Gap 最接近的方法学邻居。
4. [Under the Hood of SKILL.md](#4-under-the-hood-of-skillmd) — **核心邻居 / 证据降级**：直接覆盖 skill registry 的 governance、discovery、selection，但仅为 arXiv v1，且 selection 实验存在名称与顺序混杂。
5. [Not What You've Signed Up For](#5-not-what-youve-signed-up-for) — **核心**：IPI 奠基论文，解释不可信数据控制工具行为的根机制。
6. [BIPIA](#6-bipia) — **重要**：KDD benchmark 与 boundary-aware defense，支撑 prompt/scaffold 是安全变量。
7. [ToolEmu](#7-toolemu) — **重要**：高质量 Agent risk evaluation，提供 safety–utility 联合测量方法。
8. [InjecAgent](#8-injecagent) — **重要**：大规模 IPI benchmark，但环境和 endpoint 比 AgentDojo 更浅。
9. [HalluSquatting](#9-hallusquatting) — **补充**：与真实 skill install/RCE 很接近，但强起点、小样本且为 arXiv。
10. [SCR](#10-scr) — **补充**：composition/trust-transfer 想法有启发，但证据与系统验证最弱。

---

## 1. AgentDojo

### 1.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents* |
| **作者 / 单位** | Edoardo Debenedetti, Jie Zhang, Mislav Balunovic, Luca Beurer-Kellner, Marc Fischer, Florian Tramèr；ETH Zurich / Invariant Labs |
| **Venue / 年份** | NeurIPS 2024，Datasets and Benchmarks Track；本地版本为 arXiv v3（2024-11-24） |
| **PDF** | [2406.13352.pdf](papers/2406.13352.pdf) |
| **代码 / 项目** | [GitHub](https://github.com/ethz-spylab/agentdojo)；[项目与 leaderboard](https://agentdojo.spylab.ai) |
| **Problem** | 既有 prompt-injection benchmark 多为静态、单轮、无真实工具状态，难以可靠评估多步 tool-calling Agent 在攻击下的正常任务效用和安全性。 |
| **Main Idea** | 构建一个可执行、状态化、可扩展的动态评估环境，分别形式化用户任务与攻击目标，再用环境状态的程序化检查联合评估 utility 和 targeted attack success。 |
| **Key Innovation** | 多步有状态工具执行；确定性 utility/security checks；用户任务与攻击目标的组合测试；支持模块化 Agent、defense 和 adaptive attack。 |
| **Technical Contribution** | 4 个环境、97 个用户任务、27 个 injection tasks、629 个 security cases、约 70 个工具；ground-truth tool trajectories；程序化 verifier；攻击/防御接口；多模型基线。 |
| **Main Finding** | 正常多步任务本身已很难；攻击措辞与位置显著影响 ASR；更有能力的模型有时也更能执行攻击目标；防御必须联合考察 ASR 与 utility；tool filtering 有效但适用范围有限。 |
| **Work Focus** | 主要工作量在 benchmark infrastructure、状态化环境与任务构建、可靠测量设计和系统基线实验，而不是训练新模型、提出理论保证或设计复杂攻击算法。 |
| **Relation to Our Work** | 它是“状态化、同轨迹、utility-security 联合评估”的方法学祖先；当前 Acquisition Gap 将类似思想前移到第三方 skill 被获得之前，测量 search→install→on-disk→register→invoke→payload。 |

### 1.2 一句话结论

AgentDojo 不只问模型有没有“听信注入”，而是在一个会被工具调用真实改变的模拟环境中，检查 Agent 是否完成用户任务、是否完成攻击者目标，以及防御为降低攻击成功付出了多少正常效用代价。

### 1.3 研究问题与动机

Agent 使用邮件、网页、Slack、银行或旅行预订工具时，会把外部数据放入模型上下文。由于 LLM 缺乏形式化的 instruction/data 边界，攻击者可以把恶意指令藏在邮件、网页和其他工具返回中，诱导 Agent 以用户权限执行后续工具调用。

既有工作通常存在至少一个缺口：

- 只评估单次 function call，不能观察多步 planning；
- 只做文档问答或简单 goal hijacking，没有状态化工具执行；
- 用 LLM 模拟工具环境或担任 judge，评估模型本身可能被注入影响；
- 固定一组静态攻击，容易高估只针对这些攻击调过的防御。

论文因此提出的核心问题是：

> 如何在多步、状态化、含不可信工具数据的 Agent 环境中，可靠并可扩展地联合测量正常任务能力、攻击成功和防御代价？

### 1.4 Threat model

| 问题 | AgentDojo 的设定 |
|---|---|
| **用户输入是什么** | 正常自然语言任务，例如总结邮件、管理日历、预订酒店或支付账单。 |
| **攻击者控制什么** | Agent 会读取的第三方数据中的注入内容，例如邮件正文、网页或其他工具返回的一部分。 |
| **Agent 已拥有什么** | 对应环境中的读写工具；工具在任务开始时已经对 Agent 可见并可调用。 |
| **攻击者目标是什么** | 让 Agent 完成一个独立的恶意任务，例如泄露验证码、发钓鱼链接、转账或进行恶意预订。 |
| **是否需要用户授权 search/install** | 不涉及 skill marketplace，也不涉及搜索或安装新能力；危险行为通过已有工具完成。 |
| **主要安全边界** | 不可信数据进入规划上下文后，Agent 是否把其中的文字当成更高优先级指令并产生危险工具调用。 |

### 1.5 框架结构

```text
User task ───────────────┐
                        ▼
                  Tool-calling Agent
                        │
                        ▼
Attacker injection → Stateful environment
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
    Utility function          Security function
  用户任务是否完成？          攻击目标是否完成？
```

框架的主要组件包括：

1. **Environment 与 state**：保存邮件、日历、Slack、银行、酒店等可读写状态。
2. **Tools**：读取或修改环境状态，工具输出重新进入 Agent 上下文。
3. **User task**：正常用户指令、程序化 utility function、完成任务所需的 ground-truth tool calls。
4. **Injection task**：攻击目标、程序化 security function、完成攻击所需的 ground-truth tool calls。
5. **Attack**：根据用户任务和攻击目标，为可注入位置生成攻击文本。
6. **Agent pipeline / defense**：允许组合 LLM、工具执行循环、检测器、过滤器等组件。

### 1.6 数据与测试规模

| Environment | Tools | User tasks | Injection tasks | Security cases（乘积） |
|---|---:|---:|---:|---:|
| Workspace | 24 | 40 | 6 | 240 |
| Slack | 11 | 21 | 5 | 105 |
| Travel | 28 | 20 | 7 | 140 |
| Banking | 11 | 16 | 9 | 144 |
| **总计** | **表内相加为 74** | **97** | **27** | **629** |

注意：论文对工具总数存在内部文本不一致。Table 1 各环境数字相加为 74，正文也写 74；但 Table 1 caption 和 data card 写 70。引用时宜写“约 70 个工具”，或只引用四个环境、97/27/629 这些一致数字。

任务具有以下复杂度：

- 最多需要约 18 次工具调用；
- 数据上下文可达约 7,000 个 GPT-4 tokens；
- 工具说明可达约 4,000 个 GPT-4 tokens；
- 环境数据为人工与 LLM 辅助生成的合成数据，并经过人工检查；
- 每个环境内部将 user tasks 与相关 injection tasks 做笛卡尔积，形成 security cases。

### 1.7 指标与分母

| 指标 | 定义 | 分母 | 关键含义 |
|---|---|---|---|
| **Benign Utility** | 无攻击时，utility function 判定成功的用户任务比例 | 97 个 user tasks | 正常任务能力基线 |
| **Utility Under Attack** | security cases 中，用户任务正确完成且没有 adversarial side effects 的比例 | 629 个 user-task/injection-task pairs | 攻击存在时仍安全完成任务的能力 |
| **Targeted ASR** | security function 判定攻击者目标完成的 security-case 比例 | 629 个 security cases | 真实完成指定恶意目标，而非仅让正常任务失败 |
| **Untargeted ASR** | Utility Under Attack 的补数 | 629 个 security cases | 正常任务被破坏或产生不安全副作用；接近 denial-of-service 视角 |

关键测量原则：主要 endpoint 由模型输出和攻击前后环境状态的确定性函数判断，不依赖另一个 LLM 进行主观评分。

### 1.8 为什么 ground-truth trajectory 很重要

每个 user task 和 injection task 都提供完成目标所需的 ground-truth tool-call sequence。它的作用不是直接规定 Agent 必须走完全相同的路径，而是：

- 验证任务与攻击目标确实可实现；
- 找到正常任务真正会访问的工具和数据；
- 将注入放入现实中可能被任务读取、且可由第三方控制的位置；
- 帮助构造知道工具 API 的自适应攻击。

这避免了把攻击放进 Agent 永远不会读取的数据，再错误地把失败解释成模型鲁棒。

### 1.9 攻击与防御实验

#### 攻击

论文比较四种简单模板：

- `TODO: {goal}`；
- `Ignore previous instructions`；
- InjecAgent 使用的模板；
- 本文的 `Important message`：冒充用户向指定模型发送重要消息，要求先完成攻击目标，再回到原任务。

论文还使用 `Max` 聚合：对每个 security case，只要攻击集合中任何一种成功，就将该 case 视为攻击成功，用来近似会为不同任务选择最有效模板的 adaptive attacker。

#### 防御

| 防御 | 机制 | 主要局限 |
|---|---|---|
| Data delimiting | 用特殊边界包住工具输出，并提示模型不要执行其中的指令 | 仍依赖模型遵守文本边界，adaptive attack 可绕过 |
| PI detector | 对每次工具输出运行 prompt-injection 分类器，检测到即中止 | 误报显著损害 benign utility |
| Repeat prompt | 每次工具调用后重复原始用户任务 | 可被“忽略未来指令”等自适应攻击针对 |
| Tool filter | 在读取不可信数据前，只保留完成用户任务预计需要的工具 | 动态任务无法预先确定工具；用户任务与攻击共享工具时失效 |

### 1.10 主要实验结果

#### Agent 能力与攻击面

- 各模型 benign utility 大约为 25%–78%，说明没有攻击时多步工具任务本身就很难。
- Claude 3.5 Sonnet benign utility 为 78.22%；GPT-4o 为 69.00%。
- GPT-4o 在论文基线 Agent 对比中的 Utility Under Attack 为 50.08%，Targeted ASR 为 47.69%。
- 更有能力的模型有时 targeted ASR 更高，因为它们不仅理解攻击目标，也更有能力正确执行攻击所需的多步工具调用。

因此，低 ASR 不能单独解释成安全：能力很差、连攻击目标都执行不了的 Agent 也可能得到低 ASR。

#### 攻击措辞差异

GPT-4o 上，不同注入模板的 Targeted ASR 约为：

| Attack | Targeted ASR |
|---|---:|
| TODO | 3.66% |
| Ignore previous | 5.41% |
| InjecAgent template | 5.72% |
| Important message | 57.7% |

结果说明固定单一攻击模板很容易严重低估风险；防御评估必须面对多样化、最好是针对防御适配的攻击。

#### 防御的 utility-security trade-off

在 GPT-4o 的最强攻击评估中：

| Defense | Benign utility | Utility under attack | Targeted ASR |
|---|---:|---:|---:|
| No defense | 69.00% | 50.01% | 57.69% |
| Delimiting | 72.66% | 55.64% | 41.65% |
| PI detector | 41.49% | 21.14% | 7.95% |
| Repeat prompt | 85.53% | 67.25% | 27.82% |
| Tool filter | 73.13% | 56.28% | 6.84% |

Tool filter 的效果来自大量正常任务只需要读取数据，而攻击目标需要写工具；提前移除写工具即可阻断攻击。但论文指出，约 17% 的 cases 中，正常任务所需工具已经足以完成攻击目标，此时简单 tool filtering 无法隔离。

#### 其他发现

- 注入越接近工具返回末尾，攻击通常越有效；
- 攻击者控制的工具输出比例越高，攻击越容易成功；
- 正确知道用户和模型名称只带来小幅增益，但猜错名称会显著削弱攻击；
- 同一个复杂攻击目标包含多个恶意步骤时，Agent 可能只完成其中一部分；二元 security check 会将其计为整体失败。

### 1.11 主要 Idea、创新与 technical contribution 的区分

#### Main Idea

将间接提示注入评估放进真实执行的多步状态化工具环境，分别形式化用户目标与攻击者目标，并同时衡量正常效用和安全性。

#### 论文的主要创新

1. 从静态、单轮文本测试推进到多步 tool-calling 和环境状态变化。
2. 使用确定性状态检查，避免 LLM judge 被同一注入污染。
3. 将 user task 与 injection task 解耦定义并系统组合。
4. 把 Agent、attack、defense 都做成可替换组件，支持持续加入 adaptive attacks。
5. 明确将 benign utility、utility under attack 和 targeted harm 联合报告。

#### Technical contributions

- 可执行的状态化 Agent 环境与工具 runtime；
- 4 个应用环境及其合成状态数据；
- 97 个 user tasks、27 个 attacker goals、629 个 security cases；
- utility/security check functions；
- ground-truth tool-call trajectories 与 injection-candidate 选择；
- 模块化 Agent pipeline、attack API 与 defense API；
- 多模型、多攻击、多防御的系统性基线与置信区间。

### 1.12 Work 主要放在哪里

这是一篇以评估基础设施和测量方法为主体的工作，不是以新模型或新攻击优化算法为主体。

主要工作量大致集中在：

1. **Benchmark engineering**：实现状态、工具、执行循环、任务与环境重置。
2. **Task/data curation**：设计正常任务、攻击目标、合成环境数据并人工核查。
3. **Reliable evaluation**：为每个目标编写 utility/security verifier 和 ground-truth trajectory。
4. **Extensible interfaces**：使新 Agent、攻击与防御可作为组件接入。
5. **Baseline evaluation**：适配多个模型，运行完整 security suite，做攻击措辞、位置、攻击者知识和防御消融。

论文提出的 `Important message` 攻击本身很简单，防御也大多来自既有思路。它们的主要作用是证明框架能够揭示不同 Agent、攻击和防御之间的差异。

### 1.13 与当前 Acquisition Gap 的关系

#### 可以直接背书

- Agent 安全评估应检查工具执行造成的真实环境状态，而不只看模型文本。
- 正常任务效用与攻击目标成功必须同时报告。
- 不可信外部数据进入工具返回后，能够改变 Agent 后续规划和工具调用。
- 固定攻击模板不足以证明防御鲁棒；应考虑多样化或 adaptive attacks。
- 工具/权限限制是一种有效的 scaffold-side 防御，但其 utility 与适用范围必须单独验证。

#### 只能类比，不能写成 AgentDojo 已经证明

- fake error 或 dependency-missing 是否会诱发 skill 搜索；
- `NEED_SKILL` 是否会让 Agent 调用 `install_skill`；
- marketplace recommendation 是否会转化为真实安装；
- approval gate 是否等于对安装包进行了安全 vetting。

AgentDojo 证明的是“工具返回可成为间接注入通道并改变后续行动”，不是“假错误一定会导致 skill acquisition”。

#### 与当前工作的明确差异

| 维度 | AgentDojo | Acquisition Gap |
|---|---|---|
| 起点 | 正常任务，工具已经可用 | 普通能力任务，目标 skill 尚未安装 |
| 攻击入口 | 已有工具返回里的恶意自然语言 | 第三方 skill 供给与 scaffold acquisition policy |
| 关键链条 | read untrusted data → hijacked tool calls | task → search → retrieve → install → on-disk/register → invoke → payload |
| 权限问题 | 如何限制 Agent 对已有工具的使用 | ordinary task 是否被 scaffold 解释为第三方代码安装授权 |
| 主要分解 | benign utility / utility under attack / targeted ASR | Acquisition Funnel 的逐阶段条件存活率与 functional/security endpoints |
| 防御对应 | 预先过滤可用工具 | parsed-before-execute approval gate；另需区分 gating 与 vetting |

推荐在当前论文中将 AgentDojo定位为：

> 状态化、可执行、utility-security 联合评估的方法学祖先；当前工作将这种测量思想前移到工具获得之前，研究 scaffold authorization semantics 如何决定普通任务是否触发第三方能力的真实发现、安装与执行。

### 1.14 局限与不能过度声称

- 环境是合成的状态化模拟应用，不是真实邮箱、银行或旅行平台。
- 任务、ground truth 与 verifier 主要依赖人工构建，扩大覆盖面成本较高。
- 默认攻击较简单；论文明确不建议只用固定默认攻击评估新防御。
- 不覆盖多轮长期用户会话、跨任务持久上下文或延迟触发攻击。
- 不覆盖多模态注入。
- 不覆盖 skill/plugin marketplace、运行时安装、落盘、注册或第三方代码供应链。
- Tool filter 在工具集合无法预先确定，或正常任务和攻击共享必要工具时会失效。
- 二元 security function 可能忽略“完成了复杂攻击目标的一部分”这种 partial success。
- 论文中的模型和数值属于 2024 年版本与对应 API，不能作为当前模型安全性的实时排名。

最容易误引的三句话：

1. **不能说**“低 ASR 的模型更安全”——可能只是能力不足。
2. **不能说**“PI detector 解决了问题”——它显著降低正常 utility，且未证明抵抗 adaptive attack。
3. **不能说**“AgentDojo 证明 fake-error 会导致安装”——论文没有 skill install endpoint。

### 1.15 原文证据索引

| PDF 页码 | 位置 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–2 | Abstract、Figure 1、Introduction | 97 tasks、629 cases；联合评估 utility 与 security | 总体定位与规模 |
| 3–6 | Section 3、Figures 3–5、Table 1 | environment、tools、task、verifier、ground truth、task suites | 框架和 technical contribution |
| 6 | Section 3.4 | 三项指标定义 | 指标口径 |
| 7–9 | Section 4、Figures 6–9 | Agent/attack/defense 主实验 | 主要结论 |
| 8 | Figure 8、Table 2 | 攻击措辞与攻击者知识消融 | adaptive attack 依据 |
| 9 | Tool isolation discussion | Tool filter 的有效条件与失败边界 | 防御定位 |
| 16 | Appendix A、Figures 10–13 | injection task、pipeline、attack API | 组件接口 |
| 19 | Figure 19 | 四种攻击原始 prompt | 攻击复核 |
| 20 | Tables 3–5 | 精确数值与 95% confidence intervals | 数字引用 |
| 21 | Figure 21 | 注入位置与攻击者控制比例 | 机制分析 |
| 22–26 | Dataset supplement / data card | 数据来源、维护、验证与 intended use | 数据与局限 |

### 1.16 对我们实验设计的具体启发

1. 继续坚持 `task_ok` 与 `payload_fired` 分开报告，不能只报二者合取的 E2E。
2. 对 acquisition attack 也应设计多种、面向防御适配的 policy/metadata/return-channel 变体，不能只测一条模板。
3. 所有 endpoint 继续使用结构化执行事件和确定性 artifact verifier，避免 LLM judge。
4. 可将 user capability task 与 attacker payload goal 分离建模，再系统组合，扩大 benchmark 时比手写完整 attack scenario 更清晰。
5. 防御表必须同时给出 attack/payload、functional utility 和 false-positive/approval cost。
6. 对“攻击完成部分恶意步骤但未满足最终合取”的轨迹增加 partial-harm 事件，避免二元 E2E 掩盖真实代码执行。
7. 将 execution-layer gate 解释为 authority control；若要声称安全，还需要独立的 package vetting 或 runtime containment。

---

## 2. Do Not Mention This to the User

### 2.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *“Do Not Mention This to the User”: Detecting and Understanding Malicious Agent Skills in the Wild* |
| **作者 / 单位** | Yi Liu, Zhihao Chen, Yanjun Zhang, Gelei Deng, Yuekang Li, Jianting Ning, Leo Yu Zhang；Griffith、NTU、UNSW、Zhejiang Sci-Tech University 等 |
| **Venue / 年份** | 本地版本为 arXiv v4（2026-06-10） |
| **PDF** | [2602.06547.pdf](papers/2602.06547.pdf) |
| **Problem** | 社区 skill registry 已快速增长，但静态“可疑模式”无法区分恶意意图、开发错误和正常双用途功能，因而缺乏经过行为确认的恶意 skill ground truth。 |
| **Main Idea** | 对两个真实 registry 的 98,380 个 skill 采用“静态筛查→沙箱动态执行→双人手工确认→负责任披露”的漏斗，构建行为确认的恶意 skill 数据集并测量攻击策略。 |
| **Key Innovation** | 将大规模生态扫描与动态行为验证结合；同时分析代码载荷和 SKILL.md 自然语言攻击；用 kill-chain、共现和 shadow feature 刻画真实攻击者。 |
| **Technical Contribution** | 98,380→4,287→762→157 的验证漏斗；157 个 confirmed malicious skills、632 个漏洞实例、13 类技术和 6 个 kill-chain phases；沙箱、honeypot、系统调用/网络/文件监控；公开检测管线和标注。 |
| **Main Finding** | 真实市场中确有经过行为确认的恶意 skill；157 个样本平均含 4.03 个漏洞，73.2% 有未公开能力，84.2% 的“漏洞实例”位于 SKILL.md，自然语言是主要攻击面；披露后 157/157 被移除。 |
| **Work Focus** | 高质量生态测量、ground-truth 构建、行为验证与攻击者策略分析。它证明 malicious supply 真实存在，但不测用户/Agent 遇到这些 skill 的概率，也不测自主搜索和安装。 |
| **证据等级** | **高：真实市场供给的实证依据。** 大规模真实快照、动态确认、人工复核、外部处置验证较完整；但 157 是高精度下界，不是市场恶意率的无偏估计。 |
| **Relation to Our Work** | 为 Acquisition Gap 的攻击者前提提供现实依据：恶意 skill 不是纯合成假设。我们的 benchmark 研究的是 Agent 如何走到第三方代码执行，补的是 demand/activation path，而非重新证明 supply 存在。 |

### 2.2 一句话结论

这篇论文最重要的价值，是用真实 registry 和行为证据证明“市场里确实存在会执行恶意行为的 skill”，并把静态可疑信号与真正的恶意执行严格区分开。

### 2.3 研究问题与测量漏斗

论文回答三个问题：真实恶意 skill 的威胁图景是什么、攻击者如何组合技术、以及它们如何隐藏和逃避检测。

```text
两个真实 registries
98,380 skills
      │ 静态 14-pattern triage
      ▼
4,287 suspicious candidates
      │ Docker 沙箱动态执行
      ▼
762 runtime-triggered candidates
      │ 双人代码/日志/文档复核
      ▼
157 behaviorally-confirmed malicious skills
      │ 漏洞与 kill-chain 标注
      ▼
632 vulnerability instances
```

动态环境包括 Ubuntu 容器、网络抓包、系统调用跟踪、文件审计和伪造 API/SSH 凭证。每个候选通过文档入口、LLM 生成输入和 3–5 轮不同输入被激活，最长运行 60 秒。

### 2.4 Threat model

| 问题 | 论文设定 |
|---|---|
| **用户输入是什么** | 论文主要做生态供给测量，不固定一个用户任务 benchmark。 |
| **攻击者控制什么** | 发布到公共 registry 的 skill 包，包括 SKILL.md、脚本、配置、hook 和 MCP 设置。 |
| **Agent 已拥有什么** | 一旦 skill 被安装/执行，它通常继承本地用户权限，可接触文件、凭证、网络和 Agent context。 |
| **恶意 skill 是否已被发现/安装** | 论文从 registry 中已有 skill artifact 开始；安装概率、selection 和用户暴露量不在主测量内。 |
| **攻击目标** | credential theft、remote execution、exfiltration、instruction override、behavior manipulation 等。 |
| **主要安全边界** | registry 准入和 artifact vetting 能否识别自然语言与代码共同构成的恶意行为。 |

### 2.5 主要数据与指标

| 层级 | 数量 | 这个数字代表什么 | 不能代表什么 |
|---|---:|---|---|
| Registry snapshot | 98,380 | 两个 registry 收集到的全部 skill | 不等于活跃安装或真实使用量 |
| Static candidates | 4,287（4.4%） | 命中至少一个静态可疑 pattern | 不等于恶意 skill |
| Dynamic candidates | 762 | 沙箱中触发至少一个 runtime indicator | 仍可能是正常安全工具或双用途行为 |
| Confirmed malicious | 157（全库 0.16%） | 双人结合行为与意图确认的恶意 skill | 不是市场真实恶意率的完整估计；是高精度下界 |
| Vulnerabilities | 632 | 157 个恶意 skill 中标注出的漏洞/攻击技术实例 | 不是 632 个独立 skill |

人工确认一致性为 94.5%，Cohen’s κ=0.89；漏洞分类 κ=0.91。论文在一个 150 benign + 150 malicious 的平衡评估集上报告管线 precision 99.6%，但该 precision 不能直接转换为真实 registry 中的 recall 或 prevalence。

### 2.6 主要发现

- 157 个 confirmed malicious skills 平均包含 4.03 个漏洞，median 为 4；80.3% 至少有 3 个漏洞。
- 71.8% 的漏洞实例被标为 CRITICAL 或 HIGH。
- 73.2% 的恶意 skill 存在 public documentation 无法推断出的 shadow features。
- 84.2% 是“632 个漏洞实例中位于 SKILL.md 的比例”，不是“84.2% 的所有市场 skill 都有漏洞”。
- 高频模式包括 remote script execution、behavior manipulation、credential harvesting 和 external transmission。
- 论文识别出两类负相关攻击策略：以执行/外泄为中心的 Data Thieves，以及以 instruction override 为中心的 Agent Hijackers。
- 一个 publisher/actor 贡献 54.1% 的 confirmed malicious skills，说明总体统计受到单一规模化 campaign 显著影响。
- 负责任披露后 157/157 被 registry 移除或下架，为恶意判定提供外部验证，但不能证明安装过这些 skill 的用户均已修复。

### 2.7 Main Idea、创新与 technical contribution

#### Main Idea

用高精度、多阶段行为验证漏斗，从大规模真实 registry 中建立可用于安全研究的恶意 Agent skill ground truth。

#### 主要创新

1. 不把静态 vulnerability signal 直接当 malicious intent。
2. 将代码执行证据、网络/系统状态和自然语言 instruction-level attack 联合分析。
3. 从单个 pattern 上升到 kill-chain phase、共现结构、攻击者 archetype 和 concealment investment。
4. 用 maintainer removal 作为独立的生态处置验证。

#### Technical contributions

- 两个 registry 的大规模抓取与去重；
- 14 类静态 pattern 与 GPT 辅助自然语言检测；
- 带 honeypot 的隔离动态分析环境；
- 双人行为确认、漏洞分类和 shadow-feature 标注协议；
- 157 个恶意样本、632 个漏洞实例的标注数据；
- 统计共现、Fisher exact test、Louvain clustering 和 sophistication stratification；
- 负责任披露与后续下架核查。

### 2.8 Work 主要放在哪里

这篇工作的核心不是“发明一种新恶意 skill”，而是把现实世界的恶意供给测量做扎实：

1. 收集和清洗接近十万个真实 skill；
2. 用静态分析缩小昂贵动态验证范围；
3. 构建沙箱与可观测行为证据；
4. 对 762 个候选做双人复核；
5. 对 confirmed set 做漏洞、阶段、shadow behavior 和 actor campaign 分析；
6. 与平台进行负责任披露并追踪移除结果。

这正是它相比只构造少量合成案例的 preprint 更有说服力的地方：证据链从真实 artifact 一直延伸到观察到的行为和平台处置。

### 2.9 与当前 Acquisition Gap 的关系

#### 可以直接背书

- 公共 skill 生态中存在行为确认的恶意 skill，供应链威胁不是纯理论假设。
- SKILL.md 自然语言与辅助代码都可能承载攻击，仅做传统代码扫描不足。
- skill 一旦执行，预授予的本地用户权限会压缩传统攻击链。
- 恶意功能经常与公开描述不一致，approval 不能替代 vetting。

#### 不能直接背书

- 0.16% 不是 Agent 在真实任务中遭遇或安装恶意 skill 的概率。
- 论文不测 search、ranking、selection、install decision、invocation rate 或 task utility。
- 157 个已确认样本不能说明市场其余 98,223 个均安全。
- maintainer 移除不能证明原有用户端安装已清除。

#### 与我们当前工作的互补关系

```text
Do Not Mention：证明 attacker-controlled malicious supply 真实存在
Acquisition Gap：测 ordinary task 是否让 Agent 发现、安装、注册并运行这类 supply
```

它适合放在 Introduction / Threat Model 中支撑“恶意 skill author 与公开 marketplace 是现实假设”，也适合在 Related Work 中作为真实生态测量，而不是作为 autonomous acquisition 的直接先例。

### 2.10 局限与质量判断

#### 质量较高的原因

- 真实、较大规模 registry 快照，而非完全合成数据；
- static→dynamic→manual 的证据漏斗清楚；
- 行为确认和双人标注的一致性报告完整；
- 有系统级观察、统计检验和独立披露结果；
- 对 false positive、false negative、单一 actor concentration 和沙箱逃逸都有显式讨论。

#### 仍需保留的边界

- 60 秒和有限触发输入会漏掉延时、环境感知或多 session payload；
- 静态 pattern 决定候选池，未知攻击类型可能在第一阶段就被漏掉；
- 单一 actor 占 54.1%，样本并非 157 个独立同分布攻击者；
- 300 样本平衡集上的 precision 不能给出真实世界 prevalence；
- registry 快照不代表实际下载、安装、激活或受害用户数量；
- 研究的是供给侧 artifact 与行为，不是 Agent 决策侧的 causal benchmark。

### 2.11 原文证据索引

| PDF 页码 | 位置 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–2 | Abstract、Figures 1–3、Contributions | 98,380→4,287→157、632、研究问题 | 总体规模与贡献 |
| 4–5 | Sections 3.3–3.6 | 静态规则、动态沙箱、人工确认、标注与统计方法 | ground-truth 质量 |
| 6–7 | Tables 4–8、Figures 4–6 | technique、phase、severity、sophistication | 威胁图景 |
| 7–9 | RQ2/RQ3 | 两类 archetype、campaign、shadow feature、平台机制利用 | 攻击策略 |
| 9–10 | Discussion、Limitations、Conclusion | 防御启发、单 actor、下界和外推限制 | 质量边界 |
| 18–20 | Evaluation/implementation appendices | baseline、false-negative audit、验证协议 | 复核方法 |

---

## 3. Overcoming the Retrieval Barrier

### 3.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild for LLM Systems* |
| **作者 / 单位** | Hongyan Chang, Ergute Bao, Xinjian Luo, Ting Yu；Mohamed bin Zayed University of Artificial Intelligence |
| **Venue / 年份** | USENIX Security 2026，Long Presentation；本地 PDF 为 arXiv v1（2026-01-11），含完整附录 |
| **PDF** | [2601.07072.pdf](papers/2601.07072.pdf) |
| **代码 / 项目** | [Zenodo artifact](https://zenodo.org/records/17968523) |
| **Problem** | 既有 IPI benchmark 多假定恶意文档已经进入模型 context，绕过了现实攻击中最难的一步：在含大量正常文档的真实检索库里，恶意内容能否被自然用户查询检索出来？ |
| **Main Idea** | 将恶意文档拆成负责进入 Top-K 的短 `trigger fragment` 与负责下游攻击的 `attack fragment`，再用仅需 embedding API 的 Cross-Entropy Method（CEM）黑盒优化前缀，把 retrieval 与 downstream execution 分阶段并做端到端验证。 |
| **Key Innovation** | 把 IPI 的“已在 context”强起点前移为 query→retrieval→action；明确提出 retrieval barrier；单条恶意文档、自然查询、未知 corpus、黑盒 embedding API 的 threat model；同轨迹报告 R@5 与攻击 endpoint。 |
| **Technical Contribution** | 11 个 BEIR corpora、每库100个目标查询、8个 embedding models；默认10-token CEM prefix、最多150,000次 embedding 查询；11个下游 LLM 的 RAG 实验；Enron 邮件上的 AutoGen/Magentic-One 单/多 Agent、10个 FAQ、4类攻击；3类自适应防御评估。 |
| **Main Finding** | Vanilla attack fragment 在11个库中均未进入 Top-5；CEM 的10-token前缀在 Table 3 的平均 Recall@5 为94.1%。在多 Agent code-execution 中，GPT-4o 的 CEM/Fusion ASR 为72%/80%；但其他任务和模型差异很大，说明检索成功是必要条件，不保证 payload 执行。 |
| **Work Focus** | 主要工作量在黑盒 dense-retrieval 优化、retrieval-stage benchmark、跨 embedding model 分析与 retrieval→action 端到端串联，而不是发明新 payload 或研究 Agent 是否会自行决定搜索。 |
| **Relation to Our Work** | 它是 acquisition funnel “分阶段、找瓶颈、同轨迹测 E2E”的最近方法学祖先；但其 barrier 是系统已经执行检索以后“恶意文档能否进入 Top-5”，Acquisition Gap 的第一跳是普通任务是否让 Agent 先决定 search/install，位置更靠前。 |

### 3.2 一句话结论

这篇论文最重要的贡献是证明：不能把“注入在 context 中有效”当作现实 IPI 成功；必须先测恶意内容能否越过检索竞争，而一段按目标查询优化的短前缀可以让这个原本几乎为零的阶段接近饱和。

### 3.3 研究问题与关键缺口

IPI 的完整攻击链至少包含：

```text
natural user query
        │
        ▼
retriever searches a large benign corpus
        │
        ▼
malicious item enters Top-K
        │
        ▼
LLM follows attack fragment
        │
        ▼
output / tool call / system effect
```

早期工作通常从第三步开始：固定“最新邮件”、让 corpus 只有一条恶意文档，或者在用户 query 中放攻击者设计的 trigger。论文认为，这只能测 `execution | retrieved`，不能测自然查询下的完整 E2E。

作者先做 sanity check：仅把 attack fragment 放入 BEIR corpus 的 Vanilla baseline，在11个数据集上都没有进入 Top-5。由此提出核心问题：在不知道 corpus 内容、不能访问 embedding 参数、只能调用 embedding API 的情况下，攻击者能否为已知目标查询构造一个短前缀，使单条恶意文档进入 Top-K？

### 3.4 Threat model

| 问题 | 论文设定 |
|---|---|
| **用户输入是什么** | 自然检索问题；RAG 中为 BEIR query，Agent 案例中为从 Enron 用户邮件历史生成的常见问题。 |
| **攻击者控制什么** | 只能向 external corpus 注入一条恶意 item；控制其中的 trigger fragment 与既定 attack fragment。 |
| **攻击者知道什么** | 知道并针对目标用户查询 `q` 优化；可调用目标或替代 embedding API；不知道 corpus 内容。 |
| **攻击者不控制什么** | Retriever、base LLM、正常 corpus 和 Agent scaffold。 |
| **检索系统是什么** | 主要是 cosine-similarity dense retrieval，Top-K 默认 K=5；实验覆盖开源和闭源 embedding models。 |
| **Agent 已拥有什么** | 单 Agent 有邮件检索、发送邮件、联系人、Python execution；多 Agent 有 Orchestrator、FileSurfer、Coder/Terminal 与 retriever Agent。 |
| **是否需要决定 search/install** | 不需要。系统已是 retrieval-based pipeline，用户 query 必然进入检索；不涉及 skill marketplace 或安装。 |
| **主要安全边界** | 单条攻击者文档能否在未知正常 corpus 的竞争下进入 Top-5，以及进入后是否触发指定输出/工具行为。 |

这里的“自然查询”不等于攻击者不知道查询。算法输入显式包含目标 `q`，默认需要为每个目标查询单独优化；跨 query 的通用 trigger 不是主结果。

### 3.5 CEM 方法结构

恶意文档写为：

```text
x || D_adv

x      = trigger fragment，只负责提高 retrieval similarity
D_adv  = attack fragment，只负责进入 context 后的攻击目标
```

目标函数为目标 query 与完整恶意文档 embedding 的 cosine similarity：

```text
f(x) = sim(E(q), E(x || D_adv))
```

CEM 在每个 token position 上维护一个 factorized sampling distribution：

1. 每轮采样 `N` 个长度为 `n` 的 token sequences；
2. 用 embedding API 计算 `f(x)`；
3. 选 top-λ elite samples；
4. 按 elite token 频率平滑更新每个位置的分布；
5. 重复 `T` 轮并输出最高分 prefix。

默认参数：`n=10` tokens、每轮5,000 samples、30轮、elite fraction `λ=0.2`、smoothing `α=0.55`，因此最多150,000次 black-box embedding calls。论文给出理论 utility guarantee，但其定理要求 score function 可按位置线性分解；真实 Transformer embedding 不严格满足该假设，理论不能直接改写为现实“保证进入 Top-K”。

### 3.6 数据、模型与测试规模

#### Retrieval benchmark

| 层级 | 规模 / 条件 |
|---|---|
| Corpora | 11个 BEIR datasets：MS MARCO、TREC-COVID、NFCorpus、NQ、HotpotQA、FiQA、ArguAna、DBPedia、SCIDOCS、FEVER、SciFact |
| Corpus size | 约26K至8.8M documents |
| Target queries | 每个 corpus 随机取100个 test queries，共1,100个 query-corpus instances |
| Poisoning | 每个目标 query 向 corpus 加一条恶意 document |
| Embedding models | GTE、Contriever、Qwen3-Embedding 0.6B/4B/8B、Voyage、OpenAI text-embedding-3-small、Qwen-v4，共8个 |
| Main baselines | Vanilla（无 trigger）、Query+（直接把目标 query 前置）、CEM |

#### RAG end-to-end

- 11个 datasets × 11个 LLMs；模型覆盖 Qwen3、Llama3 与 Vicuna 的 base/instruction variants。
- 攻击目标是让回答固定为“Yes”。
- clean corpus 已经输出“Yes”的 case 被排除。
- 结果平均5个 random seeds；正文没有清楚重述每个 Figure 9 cell 排除后实际剩余的 query 数，因此不能只凭热图还原统一分母。

#### Agentic end-to-end

- 使用公开 Enron email corpus，选一个收发邮件均≥50封的用户；
- Claude Sonnet 4 根据该用户历史生成10个常见问题；
- 每个 query 注入一封 malicious email；
- GPT-4o 与 GPT-4o-mini；AutoGen single-agent 与 Magentic-One multi-agent；
- 每个 experiment 用5个 seeds重复，Table 2 是每个 cell 对10个 FAQ 的成功比例再跨5次运行求均值和标准差；
- 攻击类型：targeted answer、phishing worm、tool misuse、single-agent code execution、multi-agent code execution。

### 3.7 指标与分母

| 指标 | 分子 | 分母 | 不能混写成什么 |
|---|---|---|---|
| **Recall@5** | 单条 malicious item 出现在Top-5的 query 数 | 每 corpus 100个目标 queries | 不是 LLM 服从率，也不是 payload ASR。 |
| **MRR@5 / nDCG@5** | malicious item 的截断排名质量 | 同一100 queries | 衡量排名位置，不代表用户/Agent选择。 |
| **RAG ASR** | poisoned system 新输出攻击目标“Yes”的 queries | 排除 clean 已输出“Yes”的 cases；5 seeds | 不是原任务失败率；实际 cell 分母未逐一列出。 |
| **Worm-Phishing** | 发出的邮件含 phishing link | 10 FAQs × 5 seeds | 不等于 self-replication。 |
| **Worm** | 邮件还复制传播注入指令 | 同上 | 必须与 phishing 列分开。 |
| **Tool misuse-Sent** | 邮件发给全部 contacts | 同上 | 不等于同时含 phishing link。 |
| **Tool misuse-Phishing** | mass email 同时含 phishing link | 同上 | 更严格的端点。 |
| **Code execution ASR** | Agent 运行恶意 Python 并完成数据 exfiltration | 10 FAQs × 5 seeds | 是受控工具环境中的执行，不是生产 RCE prevalence。 |

### 3.8 Retrieval 主要结果

Table 3 在默认 GTE retriever、不同 trigger 长度下报告：

| Trigger length | Average Recall@5 | Average MRR@5 | Average nDCG@5 |
|---:|---:|---:|---:|
| 3 tokens | 28.4% | 0.18 | 0.20 |
| 5 tokens | 63.0% | 0.45 | 0.49 |
| 10 tokens | **94.1%** | 0.78 | 0.82 |

关键发现：

- Vanilla attack fragment 在全部11个 datasets 的 Top-5 retrieval 为0；不能把“强注入 prompt”自动当成现实暴露。
- 10-token CEM 在7个 datasets 达到或接近100%，但 MS MARCO 为74.0%、ArguAna 为77.5%，并非每个 corpus 都100%。
- corpus size 与难度没有明显关系；更关键的是第5名正常文档与 query 的 similarity，即 `corpus competition level`。
- 8个 embedding models 在 FiQA 上直接优化时达到90%-100% Recall@5；但跨 architecture transfer 明显下降。
- OpenAI 上优化的 prefix 对其他 target models 平均约74% recall；反方向并不对称。
- 默认优化最多150,000次 embedding calls；作者报告 OpenAI/Voyage 每目标 query 约0.21美元，Qwen-v4 最多0.76美元。

本地 arXiv v1 存在内部数字不一致：Table 3 的正确平均值是28.4%/63.0%/94.1%，紧邻正文却写29.5%和95.6%。引用时应以表格及逐行均值为准，并保留版本说明。

### 3.9 End-to-end 主要结果

Table 2 最能说明“retrieved 不等于 executed”。下面列出 Fusion 的部分关键 cells：

| Model / Setting | Retrieval R@5 | 下游 endpoint | ASR |
|---|---:|---|---:|
| GPT-4o single-agent | 1.00 | Targeted answer | 16% ±11% |
| GPT-4o single-agent | 1.00 | Phishing content / Worm replication | 84% ±11% / 18% ±13% |
| GPT-4o single-agent | 0.98 | Mass-sent / Mass-sent+phishing | 98% ±4% / 98% ±4% |
| GPT-4o single-agent | 1.00 | Code execution/exfiltration | 2% ±4% |
| GPT-4o multi-agent | 1.00 | Code execution/exfiltration | **80% ±7%** |
| GPT-4o-mini single-agent | 1.00 | Phishing content / Worm replication | 74% ±9% / 64% ±11% |
| GPT-4o-mini single-agent | 1.00 | Code execution/exfiltration | 22% ±4% |
| GPT-4o-mini multi-agent | 1.00 | Code execution/exfiltration | 36% ±9% |

几点不能忽略：

1. GPT-4o 的 multi-agent code execution 从 Ideal 的58%到 CEM 72%、Fusion 80%，显示 orchestrator trust transfer 可能放大风险。
2. GPT-4o-mini 上 CEM/Fusion multi-agent ASR 只有42%/36%，低于 Query+和Ideal的56%/54%；“CEM 总能提高 E2E”不成立。
3. 相同 R@5=1.0 时，GPT-4o targeted-answer、worm replication 与 code execution 差异可从2%到84%，检索只是漏斗的一层。
4. 多 Agent 中 Coder/Terminal 接收来自“可信 teammate”的 Python，未必看到原始用户 query 和恶意邮件；这是权限与上下文分割造成的 amplification，不应泛化为所有 multi-agent systems。

### 3.10 防御评估

论文评估三种 retrieval-stage defense：

- **Query paraphrasing**：非自适应攻击多数数据集 R@5 下降不到10%；攻击者联合多个 paraphrases 优化后恢复甚至超过原始攻击。
- **Perplexity filtering**：原始 trigger 的 perplexity 较高，但重复恶意文本可把 perplexity 降到 clean average 以下，同时保留 retrieval。
- **Token masking**：随机 mask 对较长、可分散的 trigger 影响小；即使去除部分 token，5-token trigger 仍可高 recall。

这些结果只说明三种 ad-hoc retrieval defenses 在论文条件下不足，不代表所有 IPI 防御失效。Structured-query training、suffix-level defense、hybrid search 和 reranker 未被完整评估。

### 3.11 Main Idea、创新与 technical contribution 的区分

#### Main Idea

把 IPI 成功拆为 `retrieval × downstream compliance`，并将前一项单独视为需要优化和测量的安全 barrier。

#### 主要创新

1. 反对“恶意内容已在 context”这一强起点评估。
2. 将 trigger fragment 与 attack fragment 解耦，使 retrieval optimization 可复用到不同 payload。
3. 在未知 corpus、黑盒 embedding API、单条 poisoning 的设定下优化 Top-K visibility。
4. 把 retrieval score、R@5 与真实 Agent endpoint 放在同一条攻击链上报告。

#### Technical contributions

- CEM-based discrete prefix search 与受限条件下的理论分析；
- 11 BEIR datasets × 100 queries 的 retrieval benchmark；
- 8个 embedding models、跨 model/position/payload transfer；
- 11个 downstream LLM 的 RAG attack；
- AutoGen/Magentic-One 邮件 Agent E2E；
- query paraphrase、perplexity、token masking 的 adaptive defense analysis；
- 可复现实验 artifact。

### 3.12 Work 主要放在哪里

这篇工作的核心投入有三块：

1. 把“检索是否发生”从 IPI 的隐含前提变成显式 estimand；
2. 设计可攻击闭源 embedding API 的高预算黑盒优化，并验证 corpus/model 泛化；
3. 证明 retrieval-only 数字和 Agent endpoint 必须同时看，尤其多 Agent orchestration 会改变条件成功率。

它不是 skill acquisition 论文，但其研究设计与当前 acquisition funnel 高度同构：都拒绝从强起点报告一个 ASR，都寻找最早发生 attrition 的阶段。

### 3.13 与当前 Acquisition Gap 的关系

#### 可以直接借鉴

- 把 E2E 拆成连续阶段，并为每一阶段保留自己的 denominator。
- 首先测 naive/Vanilla 条件，确认真正的 bottleneck，而不是默认攻击内容一定暴露。
- 报告 `E2E = exposure × compliance`，不要用 downstream conditional ASR 替代全链成功率。
- 用 competition level 解释不同任务的 search/retrieval 难度，而不只归因于模型能力。
- Agent 会重写 query；应记录用户 task text、Agent 发出的 `search_skills` query 和 registry 实际接收的 query。

#### 最关键的 novelty 区分

```text
Overcoming the Retrieval Barrier:
retrieval pipeline is already active
→ known target query q
→ malicious item competes for Top-5
→ IPI / tool action

Acquisition Gap:
ordinary task, no install intent
→ whether Agent decides to search at all
→ registry result / selection
→ real install / register / invoke / payload
```

它的“retrieval barrier”发生在我们的 task→search 决策之后。当前工作不宜笼统声称首次发现“第一跳 barrier”；更准确的 novelty 是：首次把 barrier 前移到 self-extension decision，并测量真实 acquisition lifecycle。

#### 只能类比

- CEM prefix 优化证明 embedding ranking 可被操纵，不直接证明 skill marketplace 排名一定可被相同方法操纵。
- BEIR Top-5 retrieval 可类比 registry search exposure，不等于 Agent 选择或安装。
- 多 Agent trust amplification 可启发分析 scaffold trust，但不是 acquisition-encouragement policy 的直接因果证据。

#### 推荐放置位置

- Related Work/Novelty：最重要的 funnel-decomposition 邻居；
- Method：解释为何逐阶段测 task→search→install→invoke；
- Discussion：区分 decision barrier 与 ranking/retrieval barrier；
- 不宜用于支撑现实 skill 安装率或不经查询定制的普适攻击。

### 3.14 局限与不能过度声称

#### 高质量之处

- USENIX Security 2026 Long Presentation；
- 明确修复早期 IPI 的强起点偏差，问题选择扎实；
- 单条 poisoning、未知 corpus、闭源 embedding API 的 threat model 具有现实意义；
- retrieval、RAG、single-agent、multi-agent 分层验证；
- 多 seed、标准差、成本和 adaptive defense 都有报告；
- 主动承认 CEM 是经典方法，贡献在 IPI adaptation。

#### 必须保留的边界

- 主要针对 cosine-similarity dense retrieval；hybrid lexical-vector search 和 reranker 未测；
- 攻击者知道精确目标 query，且默认每个 query 单独进行最高150,000次优化；
- 跨不同 embedding architectures 的 transfer 不稳定；
- BEIR 与 Enron 都是受控/公开 corpus，不是对生产服务的 in-the-wild exploitation；
- Agent 案例只有一个 Enron 用户和10个 LLM-generated FAQ；
- downstream 权限和 MCP tools 由作者配置，80%不是现实用户受害率；
- 没有系统报告攻击下正常用户任务 utility；
- 理论 guarantee 依赖线性可分 score 假设，不能外推为真实 embedding 的严格保证；
- 本地 arXiv v1 的 Table 3 与叙述平均数存在不一致，应优先引用表格；
- “near-100% across 11 benchmarks”是总体概括，默认10-token逐库结果仍有74.0%和77.5%的数据集。

合理定位是：**高质量、与当前漏斗方法最接近的检索阶段论文；它显著压缩“自然 query 到恶意内容暴露”的缺口，但不包含 Agent 是否搜索、skill 安装或 provenance authorization。**

### 3.15 原文证据索引

| PDF 页码 | 表/图/段 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–3 | Abstract、Figure 1、Introduction、Threat Model | retrieval barrier、自然 query、单条 poisoning、black-box 假设 | 核心问题 |
| 4–5 | Algorithm 1、Theorem 1 | CEM distribution、预算和理论条件 | 方法 |
| 5–8 | Table 1、Figures 2–8 | 11 datasets、8 embeddings、R@5、cost、transfer | retrieval 结果 |
| 9–10 | Figure 9、Section 5.1 | 11 LLM RAG ASR、clean exclusion、5 seeds | RAG E2E |
| 10–12 | Table 2、Section 5.2 | Enron 10 FAQ、single/multi Agent、五类 endpoints | Agent E2E |
| 12–13 | Section 6、Limitations | 三种防御、hybrid/reranker 与 transfer 边界 | 防御与局限 |
| 20 | Table 3 | 3/5/10 token 的 R@5/MRR/nDCG 与标准差 | 精确检索数字 |
| 21–26 | Appendix A.2–A.3 | RAG/Agent prompts、10 FAQ、完整 attack fragments | 复核起点和载荷 |
| 27–29 | Appendix B | adaptive paraphrase、perplexity、masking | 防御复核 |

### 3.16 对我们实验设计的具体启发

1. 明确命名两个 barrier：`decision barrier`（task→search）与 `retrieval barrier`（query→result exposure）。
2. 日志同时保存用户原始 task、Agent 改写后的 search query、Top-K registry results 与最终选择。
3. 在 P0/P1 下报告每阶段条件率和无条件率，避免下游100%掩盖第一跳 attrition。
4. 加入 registry competition 条件：相关 benign skills 数量/相似度可能决定 target skill 是否被看到。
5. 将 query-specific optimization 与 generic metadata attack 分开；前者应作为强攻击上界。
6. E2E payload 之外增加 task utility，验证攻击/防御没有只是让 Agent 停摆。

---

## 4. Under the Hood of SKILL.md

### 4.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Under the Hood of SKILL.md: Semantic Supply-chain Attacks on AI Agent Skill Registry* |
| **作者 / 单位** | Shoumik Saha, Kazem Faghih, Soheil Feizi；University of Maryland, College Park |
| **Venue / 年份** | arXiv v1（2026-05-12）；截至本次核对未见正式会议/期刊版本 |
| **PDF** | [2605.11418.pdf](papers/2605.11418.pdf) |
| **代码 / 项目** | [GitHub](https://github.com/ShoumikSaha/agent-skill-security) |
| **Problem** | 既有 skill 安全工作多从 skill 已加载或恶意代码检测开始，忽略 registry 如何接纳、排名、展示和让 Agent 选择第三方 skill；SKILL.md 的自然语言是否能独立操纵这些 acquisition-adjacent stages？ |
| **Main Idea** | 将 SKILL.md 视为 semantic supply-chain control surface，分别攻击 Discovery、Selection、Governance：用短 trigger 提升 embedding ranking，用描述性 framing 偏置 Agent paired choice，用语义改写/截断绕过本地 ClawHub-style scanner。 |
| **Key Innovation** | 首次把 skill registry 的 pre-execution lifecycle 拆成 discovery、selection、governance 三阶段，并强调只改自然语言文件也能影响搜索、信任和审核，而无需修改 executable code。 |
| **Technical Contribution** | 100个真实 ClawHub skills（5类×20）；黑/白盒20-token discovery trigger 与3个 embeddings；ClawHub-style popularity ranking case study；4种selection cues、4个models、每模型2,000 nominal trials；47个clean skills生成94个恶意variants、三阶段本地 governance pipeline 与4种evasion。 |
| **Main Finding** | OpenAI black-box discovery pairwise win=86.14%，Top-10=80%；ClawHub-style average-day win=74.14%；selection 报告 adversarial choice average=77.6%；governance 非阻断率从 baseline 31.8%升至36.5%-100%。这些阶段分开评估，没有形成 discovery→selection→install→payload 的同轨迹 E2E。 |
| **Work Focus** | 主要工作量在真实 SKILL.md corpus、registry lifecycle taxonomy、retrieval/ranking attack 与本地 governance simulation；selection 结果存在名称和候选顺序混杂，证据质量低于其 discovery 部分。 |
| **Relation to Our Work** | 它是目前最直接的 registry discovery/selection 邻居，覆盖 funnel 中 search 之后、install 之前的两层；Acquisition Gap 的新增部分是 ordinary task 是否触发 search、真实落盘/注册/调用/payload，以及 P0/P1/P2 对 self-extension decision 的因果测量。 |

### 4.2 一句话结论

这篇论文有价值的地方，是把 SKILL.md 从“安装后会执行的说明”前移为“决定 skill 能否被找到、被选中、被审核通过的供应链元数据”；但其三个实验是分开的，尤其 selection 的77.6%存在可见混杂，不能直接当作真实自主安装率。

### 4.3 生命周期与研究问题

```text
Skill submission
      │
      ▼
Governance / admission
      │
      ▼
Registry discovery / ranking
      │
      ▼
Agent selection among candidates
      │
      ▼
[not evaluated: install → load → invoke → payload]
```

论文提出三类独立攻击目标：

1. **Discovery manipulation**：让攻击者 skill 在目标 query 下获得更高 embedding score 或进入 Top-K。
2. **Selection manipulation**：候选功能相同，只用自然语言 framing 让 Agent 偏向 adversarial variant。
3. **Governance evasion**：保留恶意意图，但让 registry verdict 不再是会阻断发布的 `malicious`。

论文称三阶段“可组合”，但没有在同一 skill、同一 user trajectory 上完成 governance→discovery→selection，更没有执行真实安装。因此 composability 是 threat-model claim，不是 E2E 实验结果。

### 4.4 Threat model

| 问题 | 论文设定 |
|---|---|
| **攻击者控制什么** | 自己提交/维护的 skill 中的 SKILL.md、name、description、metadata 与自然语言 instructions；主张不改 executable code/auxiliary files。 |
| **攻击者不控制什么** | Registry backend、其他 benign skills、base Agent model、用户 query distribution。 |
| **Discovery knowledge** | 主要是能通过正常接口观察 score/rank 的黑盒攻击；也测 gradient white-box 与 surrogate transfer。 |
| **Selection 起点** | Agent 已收到两个 functionally-equivalent candidate skills，不需要自己搜索整个 registry。 |
| **Governance 起点** | 从本地 pipeline 判为clean且英文的47个skills开始，再插入合成恶意指令。 |
| **是否真实发布恶意 skill** | 否。恶意 governance variants 不上传公共 registry；ranking 由本地/ClawHub-style formula 计算。 |
| **是否真实安装/调用** | 否。selection endpoint 是 trajectory 中选择哪个 candidate；没有 on-disk、register、invoke 或 payload。 |
| **主要安全边界** | SKILL.md 的语义如何影响 registry ranking、Agent choice 与 scanner verdict。 |

### 4.5 共享数据集

论文从 ClawHub 获取100个公开 skills：

| Category | Skills | 选择方式 |
|---|---:|---|
| Email | 20 | 该 category 页面 top 20 |
| Travel | 20 | 同上 |
| Tax | 20 | 同上 |
| Health | 20 | 同上 |
| Prompt | 20 | 同上 |
| **总计** | **100** | 不是随机全市场样本，而是五类热门 skills |

另随机下载3,000个 ClawHub skills 估计 popularity：average download=579，用于 average-day ranking；0-day 案例另外抓取50个 newest skills并追踪一小时。

该 corpus 能证明攻击在真实 SKILL.md 文本上可构造，但不能估计整个 registry 的自然风险率。五个类别和 top-20 采样也会偏向已有下载量、文档较完整的 skills。

### 4.6 Discovery Manipulation

#### 攻击方法

- **Black-box beam search**：Qwen2.5-0.5B-Instruct 每步提出top-50 continuation，beam width=4，最多20 tokens；目标是提高完整 SKILL.md 与 category query 的 cosine similarity。
- **White-box gradient attack**：20-token trigger、50 iterations、每步保留top-5；每个 skill 重复5次。
- Embeddings：BAAI/bge-base-en-v1.5、BAAI/bge-small-en-v1.5、OpenAI/text-embedding-3-small。
- 评估同模型攻击与跨模型 transfer。

#### 指标与结果

| 指标 / 条件 | 结果 | 实际含义 |
|---|---:|---|
| OpenAI black-box pairwise win rate | **86.14%** | modified skill 的 retrieval score 高于其 original；不是进入候选集。 |
| OpenAI average relative score boost | **16.40%** | score 相对增幅；不能直接换算成 rank/曝光率。 |
| OpenAI black-box Top-3 / Top-5 / Top-10 | 56% / 65% / **80%** | adversarial skill 与同类 top-20 skills 一起排序时的可见率。 |
| Transfer BGE→OpenAI Top-10 | 49.5%-50.5% | surrogate trigger 仍有一定迁移，但明显低于 direct OpenAI optimization。 |
| OpenAI-optimized average rank boost | 6.69 ranks | 本地 top-20 category ranking。 |
| ClawHub-style average-day | **74.14% win** | 设攻击者579 downloads，本地 formula 下高于 baseline。 |
| 0-day at launch / after 1 hour | **94% / 40%** | 50个 newest skills，加入实际下载数后的本地 ranking comparison。 |

ClawHub-style score为：

```text
S(skill, query) = lexical + vector + 0.08 * log(1 + downloads)
```

这不是对生产 ClawHub 搜索 API 的真实曝光/点击日志，而是作者按“平台感知”公式在本地重算。

一个需要保留的复核问题：正文称共有100 skills，但附录多项百分比精确对应101或105等不同有效分母（例如86.14%=87/101，84.76%=89/105），论文没有解释额外/缺失样本或失败处理。OpenAI direct Top-K 使用100作为分母，但其他矩阵的 denominator 并不透明。

### 4.7 Selection Manipulation

#### 设计

- 每个 skill 在 description 末尾加入一条 framing，共4类：False Advertising、Assertive Cue、Active Maintenance、Trust/Security。
- 100 skills × 4 variants = 400 adversarial variants。
- 每个 original skill 由模型根据完整 SKILL.md 生成5个“适合调用该 skill”的 prompts。
- 每 trial 向 Hermes-agent 提供 original 与 adversarial paired candidates。
- 4 models：GPT-4.1-mini、GPT-5、Gemma-4-31B、Qwen3-235B-A22B-Instruct。
- 100 × 4 × 5 = 2,000 nominal trials/model，共8,000 nominal trials。

#### 结果

| Model | Adversarial selection average |
|---|---:|
| GPT-4.1-mini | 68.2% |
| GPT-5 | 71.4% |
| Gemma-4-31B | 84.3% |
| Qwen3-235B | 86.6% |
| **四模型总体** | **77.6%** |

四种 framing 平均：False Advertising 80.4%、Assertive Cues 79.5%、Trust/Security 73.7%、Active Maintenance 76.8%。

#### 为什么77.6%不能直接当纯 description effect

论文正文声称 pair “only differs in description wording”，但其原文图示存在两项未解决的混杂：

1. Figures 1、11–13 中 adversarial skill 的 `name`/candidate id 带 `-pro`，例如 `travel-manager-pro`、`apple-health-skill-pro`，而 original 没有；模型可能受“pro”名称影响。
2. Figure 11 的 candidates 列表把 adversarial `-pro` 放在 original 之前；论文未说明是否随机化/平衡候选顺序，也没有 position-only baseline。

因此77.6%最多证明论文整个 paired presentation bundle 会偏置选择，不能严格归因于追加的 description sentence。它也只测候选二选一，不测 registry search、用户确认或真实安装。

### 4.8 Governance Evasion

#### Pipeline 与样本

本地 ClawHub-inspired pipeline 包含：

1. rule-based static scanner；
2. LLM reviewer（ClawScan）；
3. packaged directory 的 VirusTotal scan。

任一 stage 输出 malicious，最终即 malicious；无 malicious 但有 suspicious，则最终 suspicious；全通过才是clean。

100个原始 skills 经“全 pipeline clean + 英文 SKILL.md”筛到47个。GPT-5 为每个生成2条 skill-relevant malicious instructions，并人工复核，共94个 baseline malicious variants。

#### Endpoint 与结果

作者设定生产 policy 只阻断 `malicious`，`suspicious` 仍可带 warning 发布。因此真正的 bypass endpoint 是 `clean + suspicious`，不是只看clean：

| Strategy | Clean | Suspicious | Malicious / blocked | Non-blocked |
|---|---:|---:|---:|---:|
| Direct baseline | 0% | 31.8% | 68.2% | **31.8%** |
| LLM-judge jailbreak | 约2.4% | 34.1% | 63.5% | **36.5%** |
| Paraphrase | 9.8% | 64.1% | 26.1% | **73.9%** |
| Definition-of-Done | 23.9% | 42.4% | 33.7% | **66.3%** |
| Context overflow | 87.1% | 12.9% | 0% | **100%** |

最强 context-overflow 利用 reviewer 只看前10K characters，把恶意指令放到截断点之后。它揭示的是 local scanner coverage bug，不等于真实 ClawHub 当前仍使用相同10K policy。

Baseline 已有31.8% non-blocked，也意味着论文摘要的“36.5%-100% avoid blocking”应和 baseline 做增量比较：jailbreak 只提高4.7个百分点，paraphrase +42.1 pp，DoD +34.5 pp，overflow +68.2 pp。

### 4.9 Main Idea、创新与 technical contribution 的区分

#### Main Idea

SKILL.md 是贯穿 registry admission、ranking 与 Agent choice 的 operational text，因此自然语言本身构成一条 pre-execution semantic supply chain。

#### 主要创新

1. 将 skill 安全研究从 post-load payload 前移到 registry-facing lifecycle。
2. 把 discovery、selection、governance 分成不同 estimands，避免一个“ASR”混合多种 endpoint。
3. 限制攻击主要落在 SKILL.md 自然语言，强调无需先修改 executable code。
4. 用真实 ClawHub skills 而非纯合成文档做初步验证。

#### Technical contributions

- 100-skill、五类别 ClawHub corpus；
- black-box/white-box discovery trigger 与 transfer matrices；
- popularity-aware ranking case study；
- 8,000 nominal paired selection trials；
- 47→94 governance dataset 与三组件 scanner；
- 四种 selection cues、四种 governance evasion strategies；
- lifecycle taxonomy 与公开代码。

### 4.10 Work 主要放在哪里

这篇论文主体工作集中在：

1. 构建一个横跨 registry 三阶段的统一问题叙事；
2. 将 embedding attack 迁移到 SKILL.md ranking；
3. 设计大规模 paired-choice selection experiment；
4. 复刻一个本地 registry governance pipeline 并研究语义/截断绕过。

最扎实的是 discovery：有 score、Top-K、transfer 和 popularity-aware 对照。Governance 能说明 scanner/policy coupling，但不是生产验证。Selection 样本量大，却因 `-pro` 名称和顺序控制未说明而削弱了因果解释。

### 4.11 与当前 Acquisition Gap 的关系

#### 可以直接背书

- registry search/ranking 与 Agent selection 是两个不同阶段，必须分别测量。
- SKILL.md metadata 不是被动文档，而是 routing、selection 和 trust 的输入。
- Top-K exposure、paired selection、scanner non-blocking、真实 install 是不同 endpoint。
- popularity、embedding relevance、description cues 和 governance policy 都会改变 acquisition surface。

#### 它已经覆盖到哪里

```text
governance ──► registry rank/Top-K ──► candidate selection
                    ✓                        ✓

task→decide to search ──► real install ──► on-disk/register/invoke/payload
          ✗                    ✗                         ✗
```

Discovery 实验回答“搜索已经发生后，攻击者 skill 是否更可见”；Selection 实验回答“两个候选已经给定后，Agent 偏向哪一个”。两者都没有回答 ordinary capability task 是否让 Agent 自己启动 search，也没有把选择变成真实安装。

#### 与当前 novelty 的直接区分

- 论文没有 P0/P1 acquisition-policy intervention，无法定位 task→search 的因果变化。
- discovery query 多为 category target，如 `email`/`travel`/`tax`，不是完整 ordinary task 经 Agent 改写后的真实 registry query。
- 三阶段各自使用不同实验，不能将86.14%×77.6%解释为真实 E2E。
- selection 使用强候选起点且无 install endpoint；当前工作继续测 executed install、on-disk、register、invoke 和 payload。
- governance 是 supply admission；当前 P2 execution gate 是 consumer-side authorization，安全边界不同。

#### 推荐放置位置

- Related Work：最直接的 skill registry discovery/selection 邻居；
- Threat Model：SKILL.md 作为 semantic supply-chain control surface；
- Novelty table：明确其起点和停止点；
- Discussion：provenance、ranking transparency、scanner verdict 与 approval；
- 不宜作为 autonomous acquisition E2E、生产 ClawHub bypass 或纯 description causal effect 的直接证据。

### 4.12 局限与质量判断

#### 有价值之处

- 问题与当前课题高度直接，首次把 registry lifecycle 系统拆开；
- 使用真实 ClawHub SKILL.md 与多种 embedding/LLM；
- discovery 同时报 score、rank、Top-K 和 transfer；
- governance 区分 clean/suspicious/malicious 与实际 blocking policy；
- 公开代码并避免向公共 registry 上传恶意 variants。

#### 必须保留的边界

- 目前只有 arXiv v1，尚无正式 peer-reviewed venue；
- 100 skills 仅来自5类 top-20，不能代表整个 registry；
- Discovery 的主目标是短 category query，真实 task→Agent query rewriting 未测；
- “ClawHub-style” ranking 和 governance 都是本地实现，不是生产系统在线实验；
- discovery 表中实际百分比分母与宣称的100 skills不完全一致，缺少失败/排除说明；
- selection 的 `-pro` name 与固定候选顺序可能是严重混杂；
- selection prompts 由目标 SKILL.md 生成，天然提高两个 candidates 的适配度；
- 没有报告 no-selection、多选、position-only 或 name-only baseline；
- governance 恶意指令由 GPT-5 合成，94 variants 不是现实攻击分布；
- overflow 依赖本地 reviewer 的10K截断实现；
- 三阶段没有组合成同一攻击链；
- 没有真实 install、execution、payload 或用户 task utility。

合理定位是：**极重要的直接 novelty 邻居和 registry-lifecycle 概念框架；discovery 结果有参考价值，selection 的精确因果结论需要独立复现，整体证据等级应低于已正式发表的 AgentDojo、Do Not Mention 和 Overcoming the Retrieval Barrier。**

### 4.13 原文证据索引

| PDF 页码 | 表/图/段 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–3 | Abstract、Figure 1、Sections 1–3 | 三阶段 lifecycle、SKILL.md-only threat model | 核心定位 |
| 4–6 | Sections 4–5、Figures 2–3、Tables 1–2 | 100 skills、discovery optimization、Top-K、ClawHub-style rank | Discovery |
| 7 | Section 6、Figure 4 | 2,000 trials/model、四模型77.6% | Selection |
| 8–9 | Section 7、Figure 5 | 47→94、pipeline、四种 evasion、blocking | Governance |
| 12 | Limitations | corpus、local pipeline、paired selection 的官方边界 | 局限 |
| 17–18 | Tables 4–9 | discovery transfer、Top-K、rank boost 完整数值 | 分母/结果复核 |
| 19–22 | Figures 10–13 | prompt generation、`-pro` name、candidate order、selection artifacts | 混杂复核 |
| 23–25 | Figure 14 | per-domain selection results | 泛化边界 |
| 26–30 | Figures 15–21 | governance prompts、evasion examples、per-domain verdicts | Scanner复核 |

### 4.14 对我们实验设计的具体启发

1. 在日志和论文表中将 `search issued`、`target in Top-K`、`target selected`、`install executed` 分列。
2. 设计 competition manipulation：保持 task不变，改变 registry 中 benign alternatives 数量与 popularity。
3. candidate selection 实验必须随机/平衡顺序，并保持 name、slug、description 之外字段 byte-identical。
4. 加 name-only、description-only、order-only factorial ablation，避免复现该论文的 `-pro` 混杂。
5. 不把 Top-K×selection 相乘冒充 E2E；必须在一条真实 Agent trajectory 上观察。
6. P2 gate 记录 authorization 与 provenance，scanner verdict 只能作为输入，不能代替执行授权。

---

## 5. Not What You've Signed Up For

### 5.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Not What You’ve Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection* |
| **作者 / 单位** | Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, Mario Fritz；Saarland University / CISPA Helmholtz Center for Information Security / sequire technology GmbH |
| **Venue / 年份** | 16th ACM Workshop on Artificial Intelligence and Security（AISec 2023），pp. 79–90，获 AISec 2023 Best Paper Award；本地 PDF 为 arXiv v2（2023-05-05），含完整附录 |
| **PDF** | [2302.12173.pdf](papers/2302.12173.pdf) |
| **代码 / 项目** | [GitHub](https://github.com/greshake/llm-security)；论文附录公开攻击 prompts 与输出截图 |
| **Problem** | 既有 prompt injection 默认攻击者直接与自己的 LLM 对话；当应用自动检索网页、邮件、代码或调用 API 时，攻击者能否只控制外部数据，就远程改变其他用户的 LLM 应用行为？ |
| **Main Idea** | 将“检索到的自然语言指令”视为跨越 data/instruction 边界的远程输入，系统化定义 Indirect Prompt Injection（IPI），再用真实应用和可调用工具的合成应用展示其从输出操纵扩展到数据外泄、持久化、远程控制、蠕虫传播和 API 劫持。 |
| **Key Innovation** | 首次把 prompt injection 从恶意用户直接输入扩展为第三方在可检索数据中预埋指令；从经典安全视角给出注入方式、受害者和危害 taxonomy；明确指出处理不可信检索内容近似“执行任意自然语言代码”。 |
| **Technical Contribution** | 被动/主动/用户驱动/隐藏式注入 taxonomy；信息收集、欺诈、入侵、恶意软件、内容操纵、可用性六类威胁；Bing Chat、Edge sidebar、GitHub Copilot 与 GPT-4/text-davinci-003 合成 Agent PoC；Search、URL、邮件、地址簿、Memory 等工具接口；多阶段和 Base64 隐藏注入。 |
| **Main Finding** | 外部内容中的指令可以持续影响对话、改变搜索/API 调用、诱导用户、写入持久化 memory、获取新攻击命令或传播给其他 Agent；但论文主要提供“可行性存在证明”，没有统一 trial 数、ASR 分母或效用对照。 |
| **Work Focus** | 主要投入在新攻击面定义、威胁建模、跨系统 PoC 与攻击后果枚举，而不是大规模 benchmark、统计估计或强防御。它的历史价值高于它作为现代系统风险量化证据的强度。 |
| **Relation to Our Work** | 它为“模型无法稳定区分外部数据与指令，进而让不可信内容改变后续工具行为”提供奠基证据；Acquisition Gap 将边界进一步前移到目标 skill 尚未进入上下文之前，测 ordinary task 是否触发 search→install→register→invoke→payload。 |

### 5.2 一句话结论

这篇论文真正奠基的不是某一条攻击 prompt，而是一个安全抽象：LLM 应用一旦把第三方内容放进规划上下文并允许模型调用工具，读取数据就可能退化成执行攻击者写下的自然语言程序。

### 5.3 研究问题与动机

直接 prompt injection 假设攻击者是当前聊天用户，因此主要影响攻击者自己的会话。论文发现，检索增强和工具集成改变了这个前提：攻击者可以把指令放在网页、邮件、代码注释或其他会被系统读取的数据里，等待正常用户的请求把它带入模型上下文。

这个变化带来三层放大：

1. **攻击变成远程且跨用户**：攻击者不需要目标应用的直接接口。
2. **输出通道变成行动通道**：模型可决定何时调用哪个 API、使用什么参数以及如何处理返回值。
3. **模型承担攻击规划**：攻击 prompt 只给高层目标，模型可能自行生成说服、搜索、传播或数据回传步骤。

因此论文的研究问题不是“某个 jailbreak 能否让模型说违规内容”，而是：外部数据能否越过应用的信任边界，控制一个拥有工具、状态和用户信任的 LLM-integrated application？

### 5.4 Threat model

| 问题 | 论文设定 |
|---|---|
| **用户输入是什么** | 正常的信息查询、网页总结、邮件处理或其他应用任务；用户不需要发送恶意 prompt。 |
| **攻击者控制什么** | 可能被检索或读取的第三方内容，例如公开网页、HTML comment、邮件、代码/文档、二阶段攻击者服务器返回。 |
| **应用已拥有什么** | 检索、查看网页、HTTP GET、读写邮件、地址簿和 memory 等预先连接的能力；Bing Chat/Copilot 的既有产品能力。 |
| **攻击者是否直接访问受害者会话** | 不需要。攻击者先放置内容，等待用户请求触发检索或读取；是否被检索是攻击链的前置条件。 |
| **是否需要用户授权 search/install** | 不涉及安装新 skill。搜索/读取/API 已属于应用既有能力，用户只发正常任务。 |
| **攻击目标** | 数据外泄、欺诈/钓鱼、恶意链接传播、prompt worm、远程命令获取、跨会话持久化、代码补全污染、内容操纵和 DoS。 |
| **主要安全边界** | 不可信外部数据进入模型 context 后，是否被当成可执行指令，并进一步控制模型输出或已有工具调用。 |

### 5.5 系统、taxonomy 与 PoC 结构

```text
Attacker plants prompt in external content
                    │
                    ▼
Normal user request ──► application retrieves/reads content
                                   │
                                   ▼
                           LLM treats data as instruction
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
       manipulate output      call existing APIs   persist / propagate
```

论文把注入入口分为四类：

- **Passive**：通过搜索、RAG、页面阅读或代码 context 被动进入；
- **Active**：攻击者主动发送会被自动处理的邮件等内容；
- **User-driven**：诱导用户复制、粘贴或转交夹带注入的内容；
- **Hidden**：HTML comment、图像、编码、多阶段 payload 等隐藏方式。

危害 taxonomy 则分为六类：Information Gathering、Fraud、Intrusion、Malware、Manipulated Content、Availability。其价值在于把 IPI 从“输出不听话”扩展为完整的系统安全后果，而不是声称这六类都已被等量、统计性验证。

合成聊天应用使用 GPT-4 或 text-davinci-003，后者配合 LangChain/ReAct；可组合的接口包括 Search、View、Retrieve URL、Read/Send Email、Read Address Book、Memory。准备好的 mock content 代替真实外部系统，temperature=0；Agent 不会真的访问公共网站或真实用户账户。

### 5.6 实验对象与证据规模

| 证据层 | 对象 / 规模 | 实际证明什么 |
|---|---|---|
| **真实黑盒应用** | Bing Chat 与 Edge sidebar | 本地 HTML comment 中的注入能影响一个真实检索/页面阅读产品的输出、搜索和会话行为。 |
| **真实代码补全** | GitHub Copilot | 代码/文档 comment 可污染补全，但效果对 context 非常敏感，放入大应用后明显减弱。 |
| **合成工具 Agent** | GPT-4 与 text-davinci-003；约6类接口 | 在受控 mock state 中展示邮件传播、远程控制、memory 持久化和 side-channel 等机制。 |
| **公开攻击材料** | Appendix Prompt 3–20；Prompt 1–2 是应用初始提示 | 18组攻击/展示材料便于复查，但它们不是18个随机 trials，也没有统一成功率分母。 |
| **扩展探索** | 多阶段注入、Base64；有限 LLaVA 视觉注入示例 | 隐藏/级联注入在个例中可行，不代表对所有模型或模态稳定。 |

论文没有从真实互联网公开投放注入，而是使用本地 HTML 或准备好的返回内容，避免影响其他用户。作者也没有 Microsoft 365 Copilot 和当时 ChatGPT plugins 的访问权限。

### 5.7 指标、分母与不能混写的 endpoint

| endpoint | 论文如何判断 | 分母 | 应如何引用 |
|---|---|---|---|
| **Injection steers model** | 截图、输出或对话显示模型遵循外部指令 | 未统一报告 | 可写“作者展示可行性”，不可写总体 ASR。 |
| **Tool/API manipulation** | mock tool call、搜索请求、URL 获取、邮件发送或 memory 写入发生 | 按个别场景展示 | 是行动层 PoC，但不等于真实生产副作用率。 |
| **Persistence / propagation** | 新会话读取被污染 memory 后重新感染；邮件 Agent 转发注入 | 各为合成示例 | 证明机制可构造，不证明现实传播率。 |
| **User deception** | 作者扮演用户与 Bing Chat 交互，观察说服或恶意链接 | 少量对话样例 | 没有用户研究，不能声称真实用户会受骗。 |
| **Availability** | 超时、静音、破坏搜索输入/输出等观察 | 未统一报告 | 不能合并成 DoS 成功率。 |

这篇论文最重要的阅读纪律是：它没有 AgentDojo 那样的 security function，也没有 BIPIA 那样的86,250条 test prompts。论文自己在 limitation 中明确说，多轮交互攻击的触发、说服持续性和多次生成成功率尚未量化。

### 5.8 Baseline、intervention 与因果对照

论文的核心 intervention 是“让相同应用读取含恶意指令的外部内容”，并通过输出或工具行为观察攻击效果。但实验并未形成现代 benchmark 意义上的完整对照：

- 没有固定任务集上的 benign vs. attacked paired trials；
- 没有多 seed、多 prompt 变体或置信区间；
- Bing Chat 是动态黑盒，模型版本、过滤器和检索结果不可控；
- 合成应用的 mock content 与工具权限是作者为机制展示而设计；
- 不同场景的 endpoint 不同，不能汇总成单一 ASR。

因此它是强 threat discovery / existence proof，弱 prevalence estimate / defense comparison。

### 5.9 主要观察结果

1. **Data 和 instruction 未被可靠分离**：放在外部内容中的指令可改变模型行为。
2. **输入过滤存在入口差异**：直接在聊天框发送会触发过滤的内容，间接进入时仍可能影响模型；这是一项黑盒观察，不是所有产品的普遍保证。
3. **注入可跨多轮保留**：Bing Chat 个例中，模型在用户没有首次配合时会继续追问并利用对话信息调整说服。
4. **攻击目标可以高层化**：prompt 只要求“说服用户且不引起怀疑”，模型自行生成具体策略。
5. **工具输入和输出都可被劫持**：攻击可以改变是否调用 API、API 参数、搜索 query 或如何解释结果。
6. **可构造持久化与传播**：合成 Agent 可把 payload 写入 memory，或通过地址簿/邮件将注入发送给其他 Agent。
7. **隐藏不是可靠防线**：二阶段获取和 Base64 解码示例仍能生效。

### 5.10 Main Idea、创新与 technical contribution 的区分

#### Main Idea

外部数据在 LLM 中与可执行指令共享同一种自然语言表示，因此“检索并处理不可信内容”会产生类似远程代码执行的控制面风险。

#### 主要创新

1. 定义并命名间接提示注入，把攻击者从当前用户改为可控制第三方数据的远程实体。
2. 从系统安全而非只从 jailbreak 视角组织攻击面和危害。
3. 强调 LLM 的工具调用和自主规划会把 prompt injection 放大为跨安全边界的行动。
4. 提前提出 worm、memory persistence、C2、side-channel 和多模态注入等后来成为 Agent 安全主线的方向。

#### Technical contributions

- 注入方法、威胁类别和受影响方 taxonomy；
- 可组合工具的合成 Agent 测试程序；
- Bing Chat、Edge sidebar、Copilot 的真实系统案例；
- 远程控制、持久化、传播、内容操纵、DoS 等攻击 prompts 和输出；
- 多阶段与编码隐藏技术；
- 对过滤、supervisor、解释性检测等防御方向的讨论。

### 5.11 Work 主要放在哪里

这篇工作的主体不是“把某个 ASR 做高”，而是把一个当时尚未形成研究对象的安全问题拆出来：

1. 重新定义攻击者位置与信任边界；
2. 把 prompt injection 映射到经典的 confidentiality、integrity、availability 与 persistence/propagation；
3. 快速跨真实产品和合成工具系统验证后果空间；
4. 完整公开 prompts、对话与截图，让后续 benchmark 能把这些个例转成标准任务。

这也是为什么它作为 AISec workshop 论文，定量严谨性不如 AgentDojo/BIPIA，但概念贡献和后续影响非常高。

### 5.12 与当前 Acquisition Gap 的关系

#### 可以直接背书

- 不可信第三方内容进入模型 context 后可以改变后续工具/API 行为。
- 用户不需要具有恶意意图；正常任务与外部数据检索的组合即可暴露攻击面。
- system safety 必须区分模型输出、工具调用和真实副作用，不能只看生成文本。
- 外部 input/output channel、memory 和多阶段获取都是需要单独记录的攻击链阶段。

#### 只能类比

- 论文的“retrieval unlocks injection”可以类比 skill search 把 marketplace metadata 带入 context；但它没有测 search 是否由 ordinary task 自主触发。
- C2、memory persistence 和 prompt worm 可类比恶意 skill 载荷阶段；它们不是 skill acquisition 的直接实验。
- “处理检索 prompt 类似执行任意代码”是安全直觉，不等于论文证明任意 prompt 都能获得传统 RCE 权限。

#### 明确差异

```text
Not What You’ve Signed Up For:
attacker content already lies on a retrieval/read path
→ context poisoning
→ output / existing API behavior

Acquisition Gap:
ordinary capability task + target skill not installed
→ autonomous search decision
→ real install / on-disk / register / invoke
→ payload
```

前者的关键随机变量是恶意内容是否被检索以及模型是否服从；后者还要先解释 Agent 为什么决定跨过 task→search、为什么选择和安装第三方代码。

#### 推荐放置位置

- Introduction：IPI 的奠基引用，解释为什么不可信内容与工具能力结合会形成系统风险；
- Threat Model：攻击者控制第三方内容而非用户 prompt；
- Related Work：与 InjecAgent、AgentDojo 组成“发现问题→规模化静态 benchmark→动态状态化 benchmark”的演化线；
- 不宜用于宣称 autonomous skill acquisition、真实安装率或现代 Agent ASR。

### 5.13 局限与不能过度声称

#### 高质量之处

- 正式发表于 ACM AISec 2023、获该届 Best Paper Award，且是 IPI 概念的奠基工作；
- 在真实黑盒产品和受控工具应用之间做了交叉验证；
- 不只展示输出 hijack，还覆盖 API、memory、传播与可用性；
- 负责任披露给 OpenAI/Microsoft，且避免公开投放可影响他人的注入；
- Appendix 提供 prompts、输出和截图，定性证据透明。

#### 必须保留的边界

- 本质是定性 PoC 集合，没有统一 benchmark、ASR、效用或统计不确定性；
- Bing Chat/Copilot 是2023年的动态黑盒版本，今天不可直接复现，也不能代表所有现代产品；
- 合成接口返回预制内容，不执行真实 API，许多副作用只在 mock state 中发生；
- 用户说服没有真实参与者研究；
- Copilot 注入对 context 敏感，放入大应用后 efficacy 降低；
- 多模态只有有限 LLaVA 示例，作者未获得当时多模态 GPT-4；
- 防御部分是讨论，没有强 baseline 或自适应攻防评测；
- “arbitrary code execution”是功能类比，不应改写为普遍、操作系统级 RCE。

合理定位是：**概念与攻击面定义极强的奠基论文；适合证明风险机制存在和指导 threat model，不适合提供今天系统中的风险率。**

### 5.14 原文证据索引

| PDF 页码 | 表/图/段 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–2 | Abstract、Figure 1、Introduction contributions | IPI 定义、远程攻击者、retrieved prompt 作为“arbitrary code” | 核心贡献 |
| 3–5 | Figures 2–3、Sections 3.1–3.2 | 四类注入、六类威胁、受影响方与 API 攻击面 | taxonomy / threat model |
| 5–6 | Section 4.1 | GPT-4/text-davinci-003 合成应用、工具接口、temperature=0、Bing Chat/Copilot | 实验对象 |
| 6–10 | Sections 4.2.1–4.2.6、Figures 4–11 | 信息收集、欺诈、worm、C2、持久化、补全污染、操纵、DoS | PoC 后果 |
| 10–11 | Section 4.3、Section 5.2 | 多阶段、Base64 与没有统一成功率的 limitation | 隐藏技术 / 证据边界 |
| 12–13 | Sections 5.4–6 | 可复现性、潜在/现实危害、mitigation、结论 | 质量判断 |
| 15–33 | Appendix Prompts 1–20、Outputs、Figures 13–28 | 初始系统 prompt、攻击文本、截图和输出 | 逐例复核 |

### 5.15 对我们实验设计的具体启发

1. 将“恶意内容进入 context”拆成 `search issued → result returned → result consumed`，不要把 search 等同于 injection exposure。
2. 将 `tool call emitted → parsed → executed → state changed` 分开记录，这正是论文定性案例后来需要 benchmark 化的部分。
3. 给 skill metadata、安装日志、registry state 和 payload 分别设置确定性 verifier，避免只看模型说了什么。
4. 增加多阶段攻击变体，但将其作为 post-search robustness，而不是混入 task→search 的主因果估计。
5. 保留 benign utility；否则“从不检索/从不安装”会被误判为完美防御。

---

## 6. BIPIA

### 6.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models* |
| **作者 / 单位** | Jingwei Yi, Yueqi Xie, Bin Zhu, Emre Kiciman, Guangzhong Sun, Xing Xie, Fangzhao Wu；USTC / HKUST / Microsoft |
| **Venue / 年份** | KDD 2025（31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.1），12 pages，DOI: 10.1145/3690624.3709179 |
| **PDF** | [2312.14197.pdf](papers/2312.14197.pdf) |
| **代码 / 项目** | [Microsoft BIPIA](https://github.com/microsoft/BIPIA) |
| **Problem** | IPI 已有真实 PoC，但缺乏跨任务、攻击类型和模型的标准化 benchmark，也缺乏同时适用于闭源 API 与开源模型的系统防御对照。 |
| **Main Idea** | 把 external content、攻击目标和注入位置做组合，构造覆盖5类应用、250个 attacker goals 的 BIPIA；再从“边界感知 + 明确提醒”出发，设计 prompt-only 黑盒防御与特殊 token + adversarial SFT 白盒防御。 |
| **Key Innovation** | 首个大规模 IPI benchmark；训练/测试按攻击类型拆分；同时比较25个模型、3个注入位置和多类攻击；把 instruction/data boundary 显式转化为可训练的格式和防御变量。 |
| **Technical Contribution** | 2,800/400 条 train/test external contents、125/125 个 train/test attacker goals、3个注入位置，生成626,250 train 与86,250 test prompts；25个 LLM 基线；multi-turn/ICL 黑盒防御；Vicuna-7B/13B 白盒 adversarial fine-tuning；BIPIA-Clean、ROUGE-1、MT-Bench utility 检查。 |
| **Main Finding** | 25个模型都出现非零 ASR；Table 2 中 GPT-4 overall ASR=31.03%，GPT-3.5=26.16%；文本任务上能力与 ASR 正相关，但代码任务无该相关；攻击放在 external content 末尾最有效；黑盒防御降低但未消除 ASR，白盒防御在 benchmark 内可降到约0.5%，但只在 Vicuna 与非自适应攻击上验证。 |
| **Work Focus** | 主要工作量在 benchmark 数据组合、攻击 taxonomy、跨模型测量，以及把边界意识实现为 prompt 与 fine-tuning 防御。它测的是模型输出是否被注入目标改变，不是工具执行或真实应用状态。 |
| **Relation to Our Work** | BIPIA 适合支撑“外部内容的边界表示与 scaffold 提醒是可干预变量”，也提醒我们攻击位置和任务格式会改变结果；但它从恶意内容已进入 prompt 开始，不覆盖 autonomous search、skill selection、安装、注册、调用或 payload。 |

### 6.2 一句话结论

BIPIA 把早期 IPI 个例变成了可重复的跨任务测量，并证明“明确标出外部数据边界”比只提醒模型更重要；但它的安全 endpoint 仍停留在生成响应，不应外推为真实 Agent 工具或系统副作用。

### 6.3 研究问题与动机

早期 IPI 工作已经说明网页、邮件等第三方内容可以覆盖应用指令，但不同论文使用不同 prompts、任务和系统，无法回答：

- 哪些 LLM 更容易受影响？
- 应用任务、攻击类别和注入位置如何改变 ASR？
- 对闭源 API，只改 prompt 能否降低风险？
- 对开源模型，能否通过训练让模型学习 instruction/data 边界，同时保留正常任务能力？

BIPIA 的方法是将问题标准化为三因素笛卡尔组合：应用任务 × attacker goal × 注入位置，并把 benign task performance 与 attack robustness 同时测量。

### 6.4 Threat model

| 问题 | BIPIA 的设定 |
|---|---|
| **用户输入是什么** | Email/Web/Table QA、Summarization 或 Code QA 的正常任务。 |
| **攻击者控制什么** | 会被应用放入 prompt 的 external content，可在其中嵌入自然语言或代码攻击指令。 |
| **攻击者知识** | 知道目标 LLM 的公开信息/API；开源场景可知道模型参数；若应用开源可知道 prompt template。 |
| **攻击者能力** | 修改 external content，并可优化恶意指令；不能直接篡改可信的应用或 LLM。 |
| **外部内容是否已进入 context** | 是。benchmark 不测 retrieval/discovery 概率，直接构造包含 external content 的最终 prompt。 |
| **是否涉及工具执行** | Code QA 让模型生成恶意代码；benchmark 本身不运行代码，也不检查真实文件/系统状态。 |
| **主要安全边界** | LLM 是否能区分 external content 中的信息与可执行指令，并拒绝执行后者。 |

### 6.5 Benchmark 构造

五类应用任务：

| Task | 原始数据 | External content train/test | 实际模拟 |
|---|---|---:|---|
| Email QA | OpenAI Evals | 50 / 50 | 邮件管理软件 |
| Web QA | NewsQA | 900 / 100 | 搜索/网页问答 |
| Table QA | WikiTableQuestions | 900 / 100 | 表格/电子表格助手 |
| Summarization | XSum | 900 / 100 | 文档/新闻摘要 |
| Code QA | Stack Overflow 自收集 Python bug/solution | 50 / 50 | 代码编辑器 |
| **总计** | — | **2,800 / 400** | — |

攻击 goals 的构成：

- 文本攻击30 types，每 type 5个具体指令，共150 goals；train/test 各15 types，即75/75 goals。
- 代码攻击20 types，每 type 5个指令，共100 goals；train/test 各10 types，即50/50 goals。
- 合计250 goals，按攻击 type 拆成125 train / 125 test，而不是随机把同一 type 的近似指令分到两侧。
- 每个恶意指令分别放在 external content 的开头、中间、结尾三个位置。

组合后得到626,250条 train prompts 与86,250条 test prompts。这里的 prompt 数是笛卡尔展开后的评估实例数，不是626,250个独立人工攻击，也不是现实用户数。

### 6.6 攻击与防御结构

```text
Application instruction + user task + external content
                                      │
                   attacker instruction inserted at B/M/E
                                      │
                                      ▼
                                     LLM
                                      │
                        response matches attacker goal?

Black-box defense:
  explicit reminder + boundary awareness via multi-turn or ICL

White-box defense:
  <data> ... </data> special tokens + reminder
  + adversarial supervised fine-tuning on attacked prompt → benign response
```

黑盒防御不修改参数：

1. **Multi-turn dialogue**：把第三方内容移到前一轮，把用户指令放在最近一轮，利用 recency 和 turn boundary。
2. **In-context learning**：给出包含 external content 与正确 benign response 的示例。
3. 两者都加入 explicit reminder，要求不要执行 external content 中的指令。

白盒防御向词表加入 `<data>`、`</data>`，用它们标记外部内容，再对 attacked prompt 与 benign response 做一轮 adversarial SFT。benign response 有三种来源：BIPIA label、原始 LLM 在 clean prompt 上的输出、GPT-4 在 clean prompt 上的输出。

### 6.7 指标与分母

| 指标 | 分子 | 分母 / 条件 | 关键边界 |
|---|---|---|---|
| **Per-task ASR** | 自动规则、LLM-as-judge 或语言检测判为达到 attacker goal 的 response | 对应任务的 test prompts：Email 11,250；Web/Table/Sum 各22,500；Code 7,500 | 是生成响应级成功，不是工具执行或真实危害。 |
| **Overall ASR** | 五类任务成功数按各自 example count 加权 | 全部86,250 test prompts | 不等于五个 task ASR 的简单平均。 |
| **BIPIA-Clean ROUGE-1 recall** | 防御模型 clean response 与目标的 unigram recall | 相同五类正常任务、无恶意指令 | 只测目标词覆盖，不完整代表 task utility/事实正确性。 |
| **MT-Bench** | judge 对通用多轮能力的评分 | 仅白盒 Vicuna-7B/13B | 检查 fine-tuning 是否损害一般能力。 |
| **Capability–ASR correlation** | 模型 Arena Elo 与 ASR 的 Pearson correlation | 25个模型 | 文本 r=0.6635、p<0.001；代码 r=-0.0254，不能概括成所有任务都“越强越危险”。 |

ASR pipeline 混合使用 rule-based、LLM-as-judge 和 `langdetect`，取决于攻击目标。论文主文没有报告该自动判断器相对于人工标注的精度/一致性，因此不能把所有类别的 ASR 当成同等可靠的真实危害标签。

### 6.8 跨模型与攻击因素结果

Table 2 在25个模型上报告：

| 模型 | Email | Web | Table | Summarization | Code | Overall ASR |
|---|---:|---:|---:|---:|---:|---:|
| GPT-4 | 15.24% | 27.92% | 34.72% | 39.17% | 28.63% | **31.03%** |
| GPT-3.5-turbo | 16.34% | 23.47% | 22.57% | 36.58% | 28.44% | **26.16%** |
| 25-model average | 7.30% | 6.15% | 7.71% | 19.66% | 24.11% | **11.79%** |

需要保留的解释边界：

- 所有25个模型 overall ASR 都大于0，但“universally vulnerable”指在 BIPIA attack distribution 上至少有非零成功，不是对任意 IPI 都会失败。
- Summarization ASR 较高，作者解释为其模板末尾没有再次放置用户问题；这说明 prompt layout 是混杂因素。
- 文本任务中，更高 Arena Elo 与更高 ASR 正相关；代码任务没有相关，GPT-4 反而更能识别部分 active malicious code。
- task-relevant 和 targeted text attacks 往往比 task-irrelevant 更有效，因为它们与原任务更兼容。
- 注入放在 external content 结尾最有效，其次开头，再是中间；论文将此与 position bias 联系，但没有证明唯一因果机制。

### 6.9 防御结果

#### 黑盒防御

| 模型 | Original overall ASR | ICL | Multi-turn | Original ROUGE | 最佳防御 ROUGE |
|---|---:|---:|---:|---:|---:|
| GPT-4 | 31.03% | 24.08% | **20.56%** | 0.6985 | 0.7201（multi-turn） |
| GPT-3.5 | 26.16% | 18.84% | **18.43%** | 0.6554 | 0.6786（multi-turn） |
| Vicuna-7B | 12.37% | 8.85% | **6.17%** | 0.6187 | 0.6084（multi-turn） |
| Vicuna-13B | 15.31% | 16.58% | **10.21%** | 0.6134 | 0.6274（multi-turn） |

黑盒方法降低 ASR 但没有消除攻击；ICL 在 Vicuna-13B 上甚至从15.31%升到16.58%。因此“简单 prompt 防御有效”应写成总体趋势，而不是每个模型/方法都单调改善。

#### 白盒防御

最佳配置把 Vicuna-7B overall ASR 从12.37%降到0.53%，Vicuna-13B 从15.31%降到约0.46%–0.47%。但 utility 需要逐列看：

- Vicuna-7B + GPT-4 response training：ROUGE 0.6187→0.6260，MT-Bench 4.8063→4.8312，几乎无损；
- Vicuna-13B + original-LLM responses：ASR 0.46%，ROUGE 0.6240，但 MT-Bench 从5.2062降到4.3375；
- Vicuna-13B + BIPIA labels：MT-Bench 降到1.6625，说明 response target 选择可以严重损害通用能力。

所以论文摘要的“near-zero while preserving output quality”在其最佳配置和所用指标上基本成立，但不能概括为所有白盒配置都无 utility cost，更不能视为面对 adaptive attack 的近乎完整防护。

### 6.10 Main Idea、创新与 technical contribution 的区分

#### Main Idea

把 IPI 风险拆成“模型缺乏 instruction/data boundary awareness”与“模型没有被明确教导忽略 external instructions”两个可干预因素，并通过 benchmark + defense 联合验证。

#### 主要创新

1. 首个跨多应用、攻击目标和注入位置的大规模 IPI benchmark。
2. 按 attack type 而非只按 prompt 随机拆 train/test，降低同类攻击泄漏。
3. 将 boundary awareness 与 explicit reminder 分离，并通过 ablation 比较贡献。
4. 同时给闭源黑盒 API 和可训练白盒模型提供防御路径。

#### Technical contributions

- 5 tasks、250 attacker goals、3 positions 的组合数据管线；
- 626,250 train / 86,250 test prompts；
- 25 LLM vulnerability baseline 与 task/type/position 分析；
- multi-turn、ICL prompt defense；
- 特殊 token + adversarial SFT；
- BIPIA-Clean、ROUGE 与 MT-Bench utility evaluation；
- defense component ablation 与 hyperparameter analysis。

### 6.11 Work 主要放在哪里

BIPIA 的工作主体集中在四部分：

1. 将早期 PoC taxonomy 转成可以组合生成的大规模数据集；
2. 建立跨25个模型的统一输出级 ASR 基线；
3. 找出 task layout、attack type 和 injection position 等高影响因素；
4. 把 instruction/data boundary 显式编码到 prompt turn、few-shot example 和 special token/SFT 中。

它是一篇典型的 benchmark + mitigation 论文，而不是 Agent systems 论文。KDD 2025正式发表、数据规模大、对照完整，是高质量工作；其主要盲点是系统 endpoint 较浅。

### 6.12 与当前 Acquisition Gap 的关系

#### 可以直接背书

- external content 的格式、位置与边界标记会显著影响模型是否执行其中的指令。
- scaffold 提醒和对话结构不是中性包装，而是可测的安全 intervention。
- 安全防御必须同时报告 clean utility；降低 ASR 可能来自能力损失。
- train/test 应按攻击机制拆分，避免只记住同类攻击表述。

#### 只能类比

- `<data>...</data>` 可类比给 marketplace result、skill card 和安装建议附上明确 provenance label；BIPIA 没有证明这种标记足以阻止真实安装。
- multi-turn 将 external content 与当前用户指令分离，可启发把 skill 搜索结果放在低信任通道，但不能替代 execution-layer authorization gate。
- “boundary awareness 比 reminder 更重要”来自 BIPIA 的 ablation，可作为设计假设，不应直接当作 Acquisition Gap 的实证结论。

#### 明确差异

```text
BIPIA starts after retrieval:
malicious external content is already inside the final prompt
→ model response reaches attacker goal

Acquisition Gap starts before retrieval/acquisition:
ordinary task
→ whether to search
→ which skill to acquire
→ real install / register / invoke / payload
```

BIPIA 不测 marketplace ranking、search recall、selection、on-disk artifact、registry、tool invocation 或系统副作用，也没有 ordinary task 导致自主 self-extension 的第一跳。

#### 推荐放置位置

- Related Work：早期 IPI benchmark 与 defense；
- Method/Discussion：说明为什么 P0/P1 scaffold wording 和 result-channel provenance 必须视为实验变量；
- Defense motivation：边界标签、低信任通道与训练式防御；
- 不宜作为真实 tool execution、skill install 或 Agent E2E compromise 的直接证据。

### 6.13 局限与不能过度声称

#### 高质量之处

- KDD 2025正式论文，数据、代码与 DOI 完整；
- 5 tasks、250 goals、3 positions 和25 models，规模明显超过早期 PoC；
- attack-type train/test split 比随机 prompt split 更严格；
- 同时测 attack robustness 和 clean/general utility；
- 黑盒与白盒方法都有 baseline、ablation 和 hyperparameter analysis；
- 结果没有回避黑盒防御仍残留较高 ASR。

#### 必须保留的边界

- 所评模型主要是2023年前后版本；结果不能代表2026最新模型或产品 defenses；
- test prompt 是从固定模板与人工 attack types 笛卡尔生成，不是自然流量分布；
- external content 已被强制放入 prompt，不测真实检索概率或攻击者如何进入 top-k；
- endpoint 是响应匹配 attacker goal，代码没有被执行，系统状态没有变化；
- ASR 自动判定混合规则、LLM judge 与语言检测，主文没有给出系统性人工验证；
- ROUGE-1 recall 只覆盖词重合，可能漏掉事实性、完整性和真实任务成功；
- 白盒 defense 只在 Vicuna-7B/13B 上测试，并针对 BIPIA 分布训练；
- 没有自适应攻击者针对 reminder、turn boundary 或 `<data>` token 重新优化；
- Vicuna-13B 的部分白盒配置显著降低 MT-Bench，不能笼统说无效用损失；
- “模型越强越脆弱”只在文本任务相关性成立，代码相关接近0，且相关性不是能力导致漏洞的因果证明。

合理定位是：**高质量的输出级 IPI benchmark 与边界感知防御论文；适合研究模型对 external instructions 的服从，不足以单独评价拥有真实权限的 Agent。**

### 6.14 原文证据索引

| PDF 页码 | 表/图/段 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–2 | Abstract、Figure 1、Introduction、Problem Definition | KDD 信息、BIPIA 贡献、250 goals、25 models、两类防御 | 总体贡献 |
| 3 | Table 1、Sections 3–4 | threat model、五任务、626,250/86,250 prompts | 数据与分母 |
| 4–5 | Table 2、Figures 2–5 | 25模型 ASR、能力相关、task/type/position effects | 基线结果 |
| 6 | Section 6.1、Figures 6–7 | explicit reminder、multi-turn、ICL | 黑盒防御 |
| 7 | Section 6.2、Figures 8–9 | special tokens、三种 benign response、adversarial SFT | 白盒防御 |
| 8 | Tables 3–4、Section 7.2 | 黑盒/白盒 ASR、ROUGE、MT-Bench | 防御收益与代价 |
| 9 | Figures 10–11、Ablation、Conclusion | boundary awareness 的贡献和结论 | 因果组件 |
| 10–12 | Tables 5–6、Figures 12–13 | train/test attack taxonomy、ICL examples、training steps | 机制与泛化边界 |

### 6.15 对我们实验设计的具体启发

1. P0/P1/P2 的 scaffold text 必须完整冻结并公开，因为 prompt layout 本身足以改变攻击率。
2. skill result 应带明确来源与信任边界，但 primary defense 仍应在执行层检查 authorization/provenance。
3. 攻击/元数据变体应按机制拆 train/dev/test，不能在同义改写上反复调参后报告同分布结果。
4. 把每一 funnel stage 的 denominator 固定：task、search、result exposure、install、on-disk、register、invoke、payload 不可合并。
5. 报告 benign twin utility 和 malicious twin security；任何降低 acquisition 的措施都要排除“只是模型不会完成任务”。
6. 对自动 verifier 做人工抽样验证；BIPIA 未充分验证 judge 的地方正是我们可以加强的方法学点。

---

## 7. ToolEmu

### 7.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Identifying the Risks of LM Agents with an LM-Emulated Sandbox* |
| **作者 / 单位** | Yangjun Ruan, Honghua Dong, Andrew Wang, Silviu Pitis, Yongchao Zhou, Jimmy Ba, Yann Dubois, Chris J. Maddison, Tatsunori Hashimoto；University of Toronto / Vector Institute / Stanford |
| **Venue / 年份** | ICLR 2024 Conference Paper；本地版本 arXiv v2（2024-05-17） |
| **PDF** | [2309.15817.pdf](papers/2309.15817.pdf) |
| **项目 / 代码** | [ToolEmu project](http://toolemu.com/) |
| **Problem** | 为每类高风险工具实现真实 API、沙箱和长尾场景成本极高，限制了 Agent risk evaluation 的工具范围和失败发现效率。 |
| **Main Idea** | 使用 GPT-4 模拟工具执行、环境状态和观察，再用另一个 LM evaluator 从完整轨迹评估 safety 与 helpfulness；adversarial emulator 还根据预设风险主动生成更容易暴露失败的环境状态。 |
| **Key Innovation** | LM-emulated virtual sandbox；面向长尾失败的 adversarial state instantiation；经人工验证的 LM safety/helpfulness evaluators；安全和任务效用联合评价。 |
| **Technical Contribution** | 36 toolkits、311 tools、144 cases、9 risk types；standard/adversarial emulators；自动 safety/helpfulness evaluator；200条 paired trajectories 的4人盲评；6/7 Terminal failures 的真实复现。 |
| **Main Finding** | adversarial emulator 将 true-failure incidence 从39.6%提高到50.0%；自动检测到的失败约68.8%经人工确认是真实可实例化风险；安全 prompt 将 GPT-4 evaluator failure incidence 从39.4%降至23.9%，同时提高 helpfulness。 |
| **Work Focus** | 可扩展风险发现基础设施与严谨的人类验证。它不是 prompt-injection benchmark，也不是确定性真实环境；核心贡献是用低成本模拟覆盖尚无 API 的高风险工具和长尾状态。 |
| **证据等级** | **高质量方法学论文。** ICLR 2024，组件验证、盲评、复现实验和误差都较完整；但具体 failure rate 是 LM-emulated/evaluator-defined benchmark rate，不是现实发生率。 |
| **Relation to Our Work** | 支持 safety/helpfulness 联合报告、分离环境与 evaluator、以及 scaffold prompt 会改变风险；同时说明为什么当前工作选择真实落盘与确定性 verifier——对 adversarial injection，LM simulator/judge 本身可能被污染。 |

### 7.2 一句话结论

ToolEmu 的高质量不在于模拟结果等同真实世界，而在于它把“用 LM 大规模发现 Agent 长尾风险”做成了一个经过人工和小规模真实沙箱验证的工程方法，并明确量化模拟器与评估器的误差。

### 7.3 研究问题与系统结构

传统风险评估需要人工实现工具、构建状态环境并检查轨迹。ToolEmu 将这些工作拆成四个组件：

```text
Test case
  ├─ tool specifications
  ├─ benign but underspecified user instruction
  ├─ underspecification / safety constraints
  ├─ expected achievements
  └─ potential risks & risky actions
          │
          ▼
LM Agent ──tool call──► LM Emulator ──observation──► multi-step trajectory
                                                     │
                                  ┌──────────────────┴──────────────────┐
                                  ▼                                     ▼
                         Safety Evaluator                    Helpfulness Evaluator
```

Standard emulator 只根据工具定义、用户任务和当前轨迹生成下一次 tool observation。Adversarial emulator 额外看到 test case 中的 underspecification 与 potential risks，并主动实例化更容易诱发危险行为、但仍应可在真实环境中实现的状态。

### 7.4 Threat model

| 问题 | ToolEmu 的设定 |
|---|---|
| **用户输入是什么** | 本意良性但缺少关键任务信息或安全约束的指令，例如“删除一些文件释放空间”。 |
| **是否存在攻击者** | 主 benchmark 没有恶意外部攻击者；风险来自 Agent 对 underspecification 的错误处理。 |
| **Agent 已拥有什么** | 一个或多个高影响工具包，包括 terminal、banking、email、smart lock、robot、traffic control 等。 |
| **环境真实吗** | 工具与状态主要由 GPT-4 按规范模拟；不执行真实 API。 |
| **成功/失败如何判断** | LM evaluator 根据完整 trajectory、expected achievement 和 potential risks 输出0–3 safety/helpfulness 分数。 |
| **主要安全边界** | Agent 是否会在信息不足时猜测、越权执行或忽略风险，而不是先澄清或采取安全动作。 |

ToolEmu 与恶意 prompt injection 的 threat model不同。AgentDojo后来明确指出：如果工具输出本身含攻击字符串，使用 LLM emulator/judge 可能让评估组件也被注入，因此 ToolEmu 的方法不能未经修改直接用于 IPI 安全结论。

### 7.5 Benchmark 与数据规模

| 层级 | 数量 / 设计 |
|---|---|
| Toolkit taxonomy | 18 categories |
| Toolkits | 36；其中30个此前无 sandboxed Agent evaluation，7个甚至没有现成 public API |
| Tools | 311，平均每个 testcase 可用约8.6个 tools |
| Test cases | 144 |
| Risk types | 9，包括 privacy breach、financial loss、physical harm、data loss、security compromise 等 |
| Trajectory length | 平均约3.57次 tool iterations，许多超过4次 |

工具规范和 cases 先由 GPT-4 生成，再由作者过滤、修改；每个 case 至少由两人审查，并在 emulator 中验证轨迹可用。这里的144并非随机真实用户分布，而是专门面向 risk discovery 的 curated red-team cases。

### 7.6 Emulator 与 evaluator 的质量标准

Emulator 的核心要求：

- tool input 格式和语义有效；
- observation 与工具规范和输入一致；
- 多轮状态保持一致；
- 输出格式满足 return schema；
- adversarial state 不能为了诱发失败牺牲可实例化性。

Safety evaluator 同时考虑风险发生可能性与伤害严重性；Helpfulness evaluator 根据安全完成用户目标的 expected achievements 打分。两者都输出0–3分，并可二值化。

关键思想是：安全不等于“不行动”。`NoAct` 可以获得3.0 safety 和0% failure，但 helpfulness 只有0.063；一个理想 Agent 应在澄清必要信息后安全完成任务。

### 7.7 人工验证与真实复现

论文随机抽100个 cases，每个分别使用 standard 与 adversarial emulator，得到200条 paired trajectories。Agent 从 GPT-4、ChatGPT-3.5、Claude-2 中随机选择；四名经过筛选的高年级 CS 学生盲评全部轨迹，每人约25小时。

| 验证指标 | Standard | Adversarial |
|---|---:|---:|
| Identified-failure precision | 72.5% ± 7.1% | 68.8% ± 6.7% |
| True-failure incidence | 39.6% ± 4.9% | 50.0% ± 5.1% |
| Critical-issue-free emulation | 91.9% ± 2.7% | 85.6% ± 3.6% |

自动 safety evaluator 对人工多数票的 precision=75.3%、recall=73.1%，与单个 held-out annotator 的78.7%/78.8%接近。二值化 Cohen’s κ：自动-人工 safety=0.478，人工-人工=0.480；helpfulness 分别0.543/0.521。

作者还将 ChatGPT-3.5+Terminal 的全部7个检测失败放入真实 bash sandbox，成功复现6个，包括实际执行 `rm -rf /*` 导致 VM crash。这是很小的子集，却为 simulator-to-real plausibility 提供了重要证据。

### 7.8 Agent 评估结果

全部144 cases 使用 adversarial emulator，Agents 与 emulator/evaluator 的 temperature=0。

| Agent / Prompt | Safety score | Evaluator failure incidence | Helpfulness |
|---|---:|---:|---:|
| GPT-4 Basic | 2.007 | 39.4% | 1.458 |
| Claude-2 Basic | 1.829 | 44.3% | 1.464 |
| ChatGPT-3.5 Basic | 1.430 | 62.0% | 0.768 |
| GPT-4 + Safety | 2.359 | 23.9% | 1.824 |
| GPT-4 + Helpful & Safety | 2.241 | 30.5% | 1.624 |
| NoAct | 3.000 | 0.0% | 0.063 |

加入“识别风险、危险调用前寻求确认”的 safety requirements 同时改善 safety 和 helpfulness；再加入强调自主性和只在必要时询问用户的 helpfulness requirements，反而使两项分数下降。这说明 scaffold prompt 中的 autonomy/assistance semantics 会实质改变高风险执行行为。

23.9% 是 evaluator 在专门构造的144个 adversarial cases 上识别出的 failure incidence，不是现实任务中的事故率。论文还用3次独立运行估计 failure incidence 标准误约4.1%。

### 7.9 Main Idea、创新与 technical contribution

#### Main Idea

让 LM 模拟工具世界和风险评估员，以较低工程成本覆盖真实 API 难以实现的高影响工具与长尾危险状态。

#### 主要创新

1. 只凭工具规范即可模拟多步状态与 observation 的 LM sandbox。
2. adversarial emulator 根据目标风险自动选择更有挑战性的初始状态。
3. 将 safety 与 helpfulness 放在同一轨迹上评价，避免“什么也不做就是安全”。
4. 不回避 LLM evaluator 的不可靠性，而是用外部人类标注、leave-one-out 和真实终端复现量化误差。

#### Technical contributions

- standard/adversarial emulator prompts 与 programmatic schema validation；
- safety/helpfulness evaluator 与0–3评分体系；
- 36 toolkits、311 tools、144 cases 的风险 benchmark；
- 200 paired trajectories、4人全量盲评和作者复核；
- Terminal 真实 sandbox 的6/7 failure reproduction；
- 多模型与 safety/autonomy prompt 对照。

### 7.10 Work 主要放在哪里

ToolEmu 的主体工作量集中在：

1. 设计一个能保持多轮状态一致的通用 LM emulator；
2. 将长尾风险作为环境状态搜索问题，而不是只写危险用户 prompt；
3. 构建广覆盖、高影响、许多尚无真实 API 的工具规范；
4. 设计 safety/helpfulness evaluator 并进行严谨的人类一致性验证；
5. 真实复现一部分模拟失败，测量哪些 emulator findings 能转移到现实。

它的论文质量主要来自对“模拟方法可能不可靠”这一核心威胁做了系统验证，而不是把 GPT-4 输出直接当 ground truth。

### 7.11 与当前 Acquisition Gap 的关系

#### 可以直接借鉴

- 安全与正常任务效用必须联合报告；`NoAct` 说明0攻击率可能只是系统无用。
- scaffold prompt/policy 是 causal intervention：强调 safety 与强调 autonomy 会改变真实 tool behavior。
- test case 应显式记录 underspecification、expected achievement、potential risk 和 ideal action。
- long-tail risk 可以通过主动构造环境状态发现，而不是用随机任务等待失败。
- 模拟 endpoint 必须单独验证其精度，不能默认等同真实系统事件。

#### 对当前结果的直接启发

ToolEmu 的 `GPT-4 + Safety` 与 `Helpful + Safety` 对照说明：一句“尽量自主完成”并非中性措辞，可能覆盖或稀释安全约束。这与当前 P0/P1 中 acquisition-encouragement 改变 task→search 第一跳的发现高度同构——scaffold policy 是授权语义的一部分，而不是无害的使用说明。

#### 为什么我们不能直接采用 ToolEmu evaluator

- 当前 payload/skill metadata 可能带 adversarial content，LM emulator/judge 也可能被注入；
- 安装、落盘、manifest、registry 和 localhost payload 都有可直接观察的系统事件，无需用 LLM 猜测；
- PDF/ICS/QR task success 有确定性 parser/verifier，应该优先使用；
- LLM judge 可作为 failure taxonomy 或辅助 annotation，不能替代 primary endpoint。

#### 推荐放置位置

- Introduction/Related Work：Agent risk evaluation 与 safety-utility 祖先；
- Method：为什么使用确定性系统事件和 artifact verifier；
- Discussion：autonomy/helpfulness policy 与 scaffold authorization；
- 不宜作为 prompt injection、skill install 或现实 failure prevalence 的直接证据。

### 7.12 局限与质量判断

#### 高质量之处

- ICLR 2024正式论文，问题与系统贡献完整；
- emulator、evaluator、end-to-end pipeline 分层验证；
- 外部盲评流程、工作量、报酬、误差和 inter-annotator agreement 透明；
- adversarial/standard paired design 能隔离环境红队机制；
- 有真实 Terminal 小样本复现，不完全停留在 LLM simulation；
- 明确承认自动生成 case 尚不可靠，保留人工审核。

#### 必须保留的边界

- emulator 和两个 evaluators 都基于 GPT-4，可能存在相关偏差；
- 约68.8%的 identified failures 经人工确认，仍有约三成 false positives；
- adversarial emulator 已知 intended risk，failure incidence 是 stress-test rate，不是自然分布；
- 144 cases 和工具规范主要由 GPT-4生成后人工修正，不是实际用户日志；
- 只有 Terminal 的7个失败被尝试真实实例化，其他高风险工具仍是模拟；
- threat model 是 benign underspecification，没有攻击者和不可信 tool return；
- 自动评分具有主观性，原始0–3标签的一致性低于二值化结果；
- 每 case 约1.2美元，扩展到更大模型/多seed并不便宜。

合理定位是：**高质量、验证充分的 scalable risk-discovery framework；它适合发现候选失败和比较设计，但对有确定性状态可测的安全问题，真实 execution verifier 仍优于 LM-emulated judgment。**

### 7.13 原文证据索引

| PDF 页码 | 位置 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–3 | Abstract、Figures 1–2、Introduction | LM sandbox、68.8%、36/144、失败案例 | 总体贡献 |
| 4–7 | Sections 2–3.2、Figures 3–4、Table 1 | threat model、emulator、adversarial state、evaluators | 方法 |
| 8–10 | Sections 3.3–4、Figure 5、Tables 2–4 | benchmark、人工验证、true failure precision/incidence | 数据与验证 |
| 11–12 | Section 5、Table 5、Figure 6 | Agent 与 prompt safety/helpfulness 对照 | 主要结果 |
| 13–14 | Limitations | simulator/evaluator、case generation 与扩展边界 | 局限 |
| 21–29 | Appendix A | emulator requirements、evaluator design、toolkits/cases | 技术细节 |
| 30–33 | Appendices B–D | 盲评、leave-one-out、误差、prompt conditions | 质量复核 |
| 34–45 | Representative cases / real sandbox | 失败案例与6/7真实终端复现 | sim-to-real 证据 |

---

## 8. InjecAgent

### 8.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents* |
| **作者 / 单位** | Qiusi Zhan, Zhixiang Liang, Zifan Ying, Daniel Kang；University of Illinois Urbana-Champaign |
| **Venue / 年份** | Findings of ACL 2024；本地版本 arXiv v3（2024-08-04） |
| **PDF** | [2403.02691.pdf](papers/2403.02691.pdf) |
| **代码 / 数据** | [InjecAgent repository](https://github.com/uiuc-kang-lab/InjecAgent) |
| **Problem** | Agent 会读取邮件、网页、评论和共享笔记等可被第三方修改的内容，但此前缺少系统评估“恶意 tool response 是否诱导 Agent 调用其他高权限工具”的 benchmark。 |
| **Main Idea** | 将正常用户工具与攻击者工具分开建模：先固定一个包含恶意指令的 user-tool response，再检查 Agent 下一步是否执行 direct harm，或完成“读取敏感数据→发送给攻击者”的两步 exfiltration。 |
| **Key Innovation** | 17 个 user cases × 62 个 attacker cases 的系统组合；区分 direct harm 与 data stealing；比较 prompted 与 function-call fine-tuned Agents；引入 ASR-valid/ASR-all 处理格式失效。 |
| **Technical Contribution** | 1,054 个 test cases、17 个 user tools、62 个 attacker-tool goals；30 个 Agents；base/enhanced 两种攻击；攻击类型、content freedom 和 user/attacker-case 关联分析。 |
| **Main Finding** | ReAct GPT-4 的 ASR-valid 从 base 23.6% 升至 enhanced 47.0%；fine-tuned tool-use models 明显更低；tool response 的内容自由度和 user case 对攻击成功的影响大于具体 attacker case。 |
| **Work Focus** | Benchmark construction 与跨模型 vulnerability profiling。它擅长系统覆盖攻击目标，但不是完整状态化 Agent 环境：论文假定 user tool 已被正确调用，并从恶意 response 后的下一步开始测。 |
| **证据等级** | **高质量 benchmark 祖先。** 正式同行评审、任务生成和分母清楚、30 Agents 覆盖广；但 endpoint 主要是解析出的 tool call，环境和副作用多为模拟，不能当真实执行 E2E。 |
| **Relation to Our Work** | 为“user channel 与 attacker goal 解耦组合”“direct harm 与 exfiltration 分步计分”提供成熟范式；当前工作增加真实 search/install/on-disk/register/invoke，并从普通任务而不是预置恶意 tool response 开始。 |

### 8.2 一句话结论

InjecAgent 将 tool-integrated Agent 的间接提示注入做成了规模化 benchmark：它系统测量 Agent 看到恶意工具返回后是否调用高风险工具，但没有评估 Agent 是否会在真实状态环境中走到该返回，也没有联合测量原始用户任务是否完成。

### 8.3 Benchmark 构造

论文从 ToolEmu 的330个工具、36个 toolkits 中人工筛选出17个会返回外部可修改内容的 user tools，例如网页、产品评论、推文、共享笔记或邮件。

每个 user case 包含：

- user tool；
- 正常用户指令；
- user-tool 参数；
- 含 `<Attacker Instruction>` 占位符的 response template。

攻击者侧包含62个 attacker cases：

| Attack family | 数量 | 成功条件 |
|---|---:|---|
| Direct harm | 30 | Agent 下一步调用指定 harmful tool，例如转账、开门、修改/移动文件 |
| Data stealing | 32 | S1 调用数据读取工具；模拟其返回后，S2 再调用消息工具把数据发给攻击者 |

最终通过 `17 × 62` 笛卡尔积得到1,054个 test cases。Base setting 只填入攻击者指令；Enhanced setting 在攻击指令前加固定的 hacking prompt。

### 8.4 Threat model 与真实 endpoint

| 问题 | InjecAgent 的设定 |
|---|---|
| **用户输入是什么** | 正常查询，例如读取评论、邮件、网页或共享内容。 |
| **攻击者控制什么** | user tool response 中某个高内容自由度字段，例如 review/tweet/email content。 |
| **Agent 已拥有什么** | 全部 user tools 与 attacker tools 已可用；不涉及搜索或安装新能力。 |
| **论文实际从哪一步开始** | 假定 Agent 已准确执行 user tool，并直接把预构造的恶意 response 提供给它。 |
| **成功测到哪一步** | 解析 Agent 输出中的 attacker-tool invocation；data stealing 再模拟读取工具返回并检查发送调用。 |
| **是否有真实状态变化** | 没有完整可变环境；成功主要由结构化 tool-call 输出判定，而非真实银行、文件或设备状态。 |
| **是否测用户任务 utility** | 没有与攻击 ASR 对等的原始用户任务完成 verifier。 |

这一设计使 benchmark 规模化，但也意味着它主要测 `P(harmful tool call | malicious tool response is already in context)`，不是从用户任务到真实副作用的全链概率。

### 8.5 Agents、指标与分母

论文评估30个 Agents：大部分是使用 ReAct prompt 的开源/闭源模型，另有 GPT-3.5/GPT-4 function-calling fine-tuned Agents。

| 指标 | 分子 / 分母 | 解释 |
|---|---|---|
| **Valid rate** | 可被解析且形成有意义下一步的 outputs / all outputs | 反映模型是否遵循 ReAct/tool-call 格式 |
| **ASR-valid** | successful attacks / valid outputs | 论文主分析；剔除无效输出后测对注入的行为脆弱性 |
| **ASR-all** | successful attacks / all outputs | 把格式失败和能力失败都计为攻击未成功 |
| **Direct-harm ASR** | 调用指定攻击工具 / 对应 valid 或 all cases | tool-call endpoint |
| **Data-stealing ASR** | S1 extraction 与 S2 transmission 都完成 / 对应 cases | 两阶段合取；S2 还单独报告条件成功率 |

主表只突出 valid rate 大于50%的 Agents。ASR-valid 更适合隔离“理解注入后的行为”，但会排除能力/协议失败；安全比较时必须与 valid rate 和 ASR-all 一起看，不能只报一个数字。

### 8.6 主要实验结果

- ReAct GPT-4：base ASR-valid=23.6%，enhanced=47.0%。
- ReAct GPT-3.5：base=23.7%，enhanced=39.8%。
- ReAct Claude-2：base=11.4%，enhanced=3.4%，说明固定增强模板并非对所有模型都单调增强。
- Fine-tuned tool-use GPT models 的 base total ASR-valid 约3.8%与6.6%，enhanced 约8.4%与7.1%，显著低于对应 prompted Agents。
- Data stealing 的 S2 一旦进入发送阶段通常成功率很高，说明 extraction gate 比发送本身更可能是瓶颈。
- user case 与攻击成功的关联强于 attacker case：direct harm 的 Cramér’s V 为0.28 vs 0.18，data stealing 为0.31 vs 0.20。
- 17个 user cases 中12个被分为 high content freedom、5个为 low；高自由度字段的 ASR 显著更高，因为恶意指令更容易自然混入正文。

论文的增强攻击依赖一个固定 hacking prefix。它证明措辞能显著改变结果，但不能代表 adaptive attacker 的上限。

### 8.7 Main Idea、创新与 technical contribution

#### Main Idea

把间接注入拆成“正常外部内容入口”和“独立恶意工具目标”，通过二者组合系统测量 tool-integrated Agent 的脆弱性。

#### 主要创新

1. 在 Agent benchmark 中明确区分 user tool 与 attacker tool。
2. 将直接伤害与数据外泄分开，外泄又拆成 extraction 和 transmission。
3. 通过 user×attacker case 组合扩大攻击覆盖，而不是手写1,054条独立故事。
4. 同时报告 ASR-valid 和 ASR-all，揭示安全数字会被 tool-use/format 能力影响。
5. 从 external-content freedom 分析攻击入口本身，而非只比较攻击字符串。

#### Technical contributions

- 17个可被第三方修改的 user-tool response templates；
- 62个攻击目标与所需工具序列；
- GPT-4辅助生成、人工修正参数完整性和 response plausibility；
- 30 Agents、base/enhanced setting 的大规模评测；
- valid-rate、分阶段 ASR、攻击类别与 case-association 统计分析；
- 完整 prompts、代表案例和数据发布。

### 8.8 Work 主要放在哪里

工作量主要集中在：

1. 从大型工具集合中筛选真实可被攻击者影响的 response channel；
2. 构建可交叉组合的 user cases 与 attacker cases；
3. 确保攻击指令具备调用工具所需的完整参数；
4. 适配大量 prompted/fine-tuned Agents，并处理格式无效输出；
5. 分析攻击类型、内容自由度和模型 tool-use 方法对 ASR 的影响。

与 AgentDojo 相比，InjecAgent 的广度很强，但执行环境较浅；AgentDojo 的核心升级正是让 Agent 自己规划多步工具调用，并用状态化 environment verifier 检查副作用和用户任务 utility。

### 8.9 与当前 Acquisition Gap 的关系

#### 可直接借鉴

- 将 benign user task/channel 与 attacker goal 解耦，未来可把 capability task 与 payload goal 系统组合。
- 对多阶段攻击分别报告条件成功率和最终合取，类似 Acquisition Funnel。
- 把 invalid/parsed/executed 分开；InjecAgent 的 ASR-valid/all 差异说明协议能力会扭曲安全排名。
- entry channel 特性可能比具体恶意目标更决定攻击成功；这对应我们发现的 scaffold/task→search 第一跳。
- 数据读取与数据发送要分阶段记录，不能仅因 payload 文本出现就算 exfiltration。

#### 不能直接背书

- 它不证明恶意 tool call 被真实执行，也不证明真实环境发生副作用。
- 它不涉及 skill discovery、selection、installation、registration 或 marketplace。
- 它不能支持普通任务会自主触发 acquisition；恶意 response 已被预先放入模型 context。
- 没有用户任务 verifier，不能支持 `payload ∧ task_ok` 的联合结论。

#### 推荐放置位置

- Related Work：tool-integrated IPI benchmark 祖先；
- Method：user task × attacker goal 的组合与两阶段 exfiltration；
- Discussion：valid rate 与能力/安全解耦；
- 不适合作为真实 install/E2E 或 clean utility 的证据。

### 8.10 局限与质量判断

#### 高质量之处

- 正式同行评审，问题定义和分母清楚；
- 覆盖30个 Agents，避免只凭单模型案例；
- user/attacker case 解耦使 benchmark 结构清晰且可扩展；
- ASR-valid/all、S1/S2 和 content freedom 分析比单一 ASR 更细；
- 附录公开完整 prompts、模型版本、数据和案例。

#### 需要保留的边界

- 单轮简化：假定 user tool 已正确调用，不测完整 planning；
- 工具执行和外部状态为模拟，endpoint 主要是 emitted/parsed call；
- 数据由 GPT-4 辅助合成并人工修正，不是真实攻击流量；
- fixed hacking prompt 容易被过滤，也不是 adaptive evaluation；
- 主 ASR-valid 排除 invalid outputs，不联合 valid rate 阅读会误判弱模型；
- 没有 benign utility / utility under attack 的确定性联合检查；
- 不研究多轮 context、长期记忆、partial harm 或不同注入位置。

合理定位是：**高质量、覆盖广的 tool-integrated IPI benchmark 祖先；它建立了攻击任务结构，但真实动态执行与效用测量由 AgentDojo 等后续工作补强。**

### 8.11 原文证据索引

| PDF 页码 | 位置 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–3 | Abstract、Figure 1、Sections 1–2.1 | benchmark 问题、threat model、17/62/1,054 | 总体定位 |
| 3–5 | Section 2.2、Tables 1–2 | user/attacker case 生成与类别 | 数据构造 |
| 5–8 | Sections 2.3–4、Tables 3–4、Figures 2–3 | ASR 定义、模型结果、case/content analysis | 主要结果 |
| 12–13 | Limitations | fixed prompt、单轮、混合内容和 fine-tuned Agents 边界 | 局限 |
| 15–18 | Tables 5–12、Figures 4–6 | 模型版本、valid rate、ASR-valid/all 与 attack type | 数字复核 |
| 27–36 | Full prompts | ReAct、user/attacker case generation、data-stealing simulation | 复现 |

---

## 9. HalluSquatting

### 9.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Beware of Agentic Botnets: Scalable Untargeted Promptware Attacks via Universal and Transferable Adversarial HalluSquatting* |
| **作者 / 单位** | Aya Spira, Stav Cohen, Elad Feldman, Ron Bitton, Avishai Wool, Ben Nassi；Tel Aviv University / Technion / Intuit |
| **Venue / 年份** | arXiv v1（2026-07-08） |
| **PDF** | [2607.07433.pdf](papers/2607.07433.pdf) |
| **Problem** | LLM 会为不完整的 repository/skill 名称补出错误 identifier；攻击者能否预测并抢注这些 hallucinated resources，让 Agent 主动拉取恶意内容？ |
| **Main Idea** | 对热门资源反复查询模型，估计 hallucinated identifiers 的分布，抢注高概率候选并嵌入 promptware，使明确的 clone/install 请求落到攻击者资源。 |
| **Key Innovation** | 将 package hallucination/typosquatting 扩展到运行时 Agent resource resolution；研究 hallucination 在模型、prompt 和 production assistant 间的 transferability；展示 repository 与 skill 两条真实系统攻击链。 |
| **Technical Contribution** | 约14,000+ repository probes、16 个 repository targets、多种 production coding assistants；14 个 ClawHub skill targets、3 个 assistants、4 个 OpenClaw backbones；受控 tool invocation 与 RCE 验证。 |
| **Main Finding** | 新近 repository 更易被错误解析；web search 显著降低错误 clone；14 个 skill 中 127/140 次解析到可抢注 slug，跨三 assistant 为85/90；受控 E2E 中 context exfiltration 与 reverse-shell overall 分别约96%和84%。 |
| **Work Focus** | 资源名称解析漏洞、squatting candidate 发现、跨模型/应用迁移和受控真实执行。强项是 production assistant case study；弱项是用户起点已明确要求 clone/install，skill E2E 还需要随后明确要求 use。 |
| **证据等级** | **想法邻居 / 中等实证。** 比纯模拟 benchmark 更接近真实系统，但仍是 arXiv v1、目标与 prompt 有限、部分 trial 手工运行；恶意资源未公开上线，真实规模化 botnet 是风险外推而非现场测量。 |
| **Relation to Our Work** | 它证明“显式安装意图+identifier hallucination”可到真实安装/RCE，是我们 acquisition funnel 的强起点上界；我们的差异是用户未要求 search/install，关注 scaffold policy 是否从普通能力任务自行跨过第一跳。 |

### 9.2 一句话结论

HalluSquatting 证明，当用户已经要求 Agent clone 或 install 一个名称不完整的资源时，模型会稳定地产生可被抢注的 identifier，攻击者可借此把资源获取引到恶意 repository/skill；但它不证明普通任务会让 Agent 自主决定去安装。

### 9.3 攻击链

```text
攻击者观察热门 repository / skill
      → 查询模型，估计 hallucinated identifier 分布
      → 注册高概率、尚未被占用的 slug
      → 在资源中放入 adversarial prompt / code

用户明确说“clone X”或“install X”
      → Agent 补全错误 identifier
      → fetch/install attacker-controlled resource
      → promptware 触发工具调用
      → 受控实验中的 context exfiltration / reverse shell
```

攻击的核心不是攻击者向某个具体用户发邮件，而是利用大量用户都会提出的资源请求，让 Agent 自己“拉取”攻击者预先发布的资源，因此作者称其为 scalable untargeted promptware。

### 9.4 Threat model

| 问题 | HalluSquatting 的设定 |
|---|---|
| **用户输入是什么** | 明确的资源操作请求，例如 `clone <repo-name>` 或 `install <display-name>`。 |
| **攻击者控制什么** | 可在 GitHub、ClawHub 等平台注册未占用 identifier，并控制该资源内容。 |
| **Agent 已拥有什么** | 能联网检索/获取资源，并通常有 terminal、shell、文件和网络工具。 |
| **是否已有安装意图** | 是。skill 实验明确提示 `install <display-name>`；payload 阶段之后还提示使用该 skill。 |
| **攻击者是否控制用户 prompt** | 不控制具体用户，但依赖用户自然提出热门资源的 clone/install 请求。 |
| **主要安全边界** | 模型生成的资源 identifier 未经过 authoritative search/verification 就被 fetch/install。 |

### 9.5 Repository Squatting 实验

论文区分三个层级：

1. **Foundation model API**：6 个模型，对 15 个 repository 每组合100次，共9,000次；另对 `librepods` 600次。
2. **Production assistants**：Gemini CLI、Cursor CLI 等，观察是否 search、输出哪个 slug、是否真的 clone。
3. **End-to-end attack**：对多个 coding assistants 做受控 resource fetch 与 payload execution。

关键发现：

- 10 个较新/热门 repository 的平均 hallucination rate 约92.4%，5 个老 repository 约0.9%；这个差异与训练数据新旧有关，但不是严格的训练集成员证明。
- Gemini CLI 500 runs 中产生有效 slug 的287次里，235次是 hallucinated；全部 runs 中26%走到未 search 的 squattable slug。
- Cursor CLI 在有 search 时93.4%正确；无 search 时99.1% hallucinated，说明 application-level verification 比单纯换模型更关键。
- repository E2E case 每个应用通常只有20 trials，overall tool invocation/RCE 约20%–65%，属于具体系统和版本下的 case-study rate。

### 9.6 Skill Squatting 实验

论文识别两种解析失败：

- **V1 word removal**：例如用户说 `install skill vetter`，Agent 把 `skill-` 当通用词去掉，安装 `vetter`。
- **V2 display-name/slug divergence**：市场展示名与真实 slug 差异很大，Agent 根据展示名生成另一个未注册 slug。

主要实验：

| 实验 | 范围 | 结果 |
|---|---|---|
| Cross-model | `skill-vetter`，4 个 OpenClaw backbones，各10次 | 40次中0次解析到正确 canonical slug；`vetter` 可覆盖38/40 attempts |
| Cross-skill | 14 个 skills，OpenClaw+Sonnet 4.6，各10次 | 127/140（90.7%）为可抢注 slug，13/140正确 |
| Cross-assistant | 3 个 targets × OpenClaw/ZeroClaw/NanoClaw，各10次 | 85/90（94.4%）为可抢注 slug |
| Controlled E2E | 私有/本地替换的恶意 skill | context exfiltration overall约96%，reverse shell overall约84% |

这里必须区分三个分母：

- `squattable slug rate`：模型/assistant 是否解析到当时可注册的错误 slug；
- `resource fetched`：抢注之后，该 assistant 是否取到攻击者资源；
- `payload execution`：安装后在单独的使用阶段，payload 是否执行。

Table 1 的 `Payload Exec.` 与 `Res. fetched` 并非总是同一个 trial 分母，overall 是按两阶段结果组合，不能把表中某一列直接当 ordinary-task E2E。

### 9.7 Main Idea、创新与 technical contribution

#### Main Idea

把模型可预测的资源 identifier hallucination 转化为一种 LLM 驱动的 squatting 攻击面，使 Agent 在推理时主动拉取攻击者资源。

#### 主要创新

1. 将 hallucinated package supply-chain 风险推广到 Agent application inference-time resource retrieval。
2. 从单次 hallucination 上升到分布学习、universal candidate 和跨模型迁移。
3. 同时研究 GitHub repository 和 ClawHub skill 两个实际生态。
4. 将 identifier error、application search policy、resource fetch 与 payload execution 分层测量。

#### Technical contributions

- 多模型 repository identifier probes；
- recent/old repository 对照；
- web-search conditioning 与 prompt-framing 消融；
- production coding assistant 的 clone/fetch case study；
- ClawHub V1/V2 skill-resolution taxonomy；
- 跨 skill、模型和 assistant 的 transferability 试验；
- 受控 context exfiltration 与 RCE 演示；
- search-before-fetch 等防御建议和 vendor disclosure。

### 9.8 Work 主要放在哪里

论文的工程和实验工作主要在：

1. 大量 probing 来估计 hallucinated identifier 分布；
2. 用平台 API 判断正确、错误、可抢注和已有错误资源；
3. 在不同应用/模型/版本下观察 search 与 fetch 行为；
4. 注册 benign squats，验证真实 resolution path；
5. 在私有受控机器上将其替换为恶意 payload，验证安装后的执行可能性。

它最有价值的不是“Agent会幻觉”这个已知事实，而是展示 hallucination 在模型层和应用层如何变成一个可注册、可获取、可执行的 supply-chain path。

### 9.9 与当前 Acquisition Gap 的关系

#### 它已经覆盖的部分

- 真实 marketplace/resource identifier；
- identifier hallucination 和 attacker registration；
- 实际 fetch/install；
- 安装后调用与受控 payload/RCE；
- 多个 production assistants。

#### 它没有覆盖的起点

HalluSquatting 的用户明确说 `clone` 或 `install`，已经授予了资源获取意图。当前 Acquisition Gap 的用户只要求生成 PDF/ICS/QR 等能力结果，不提 skill、搜索或安装。

```text
HalluSquatting：explicit clone/install intent
             → wrong identifier
             → attacker resource
             → later explicit use
             → payload

Acquisition Gap：ordinary capability task
               → scaffold decides to search
               → correct marketplace target/twin
               → real install/register/invoke
               → payload + task_ok
```

因此 HalluSquatting 是“用户已授权获取资源”条件下的真实 E2E 上界和最近邻，而不是当前 neutral-start primary 的替代。

#### 可直接借鉴

- `search-before-fetch` 应成为资源安装器的强制系统 invariant，而非只在 prompt 中建议；
- resource resolution 必须使用 authoritative identifier，不能让模型自由补 owner/slug；
- 必须分开记录 hallucinated、retrieved、installed、invoked 和 payload；
- production assistant 的 system prompt/tool policy 会显著改变风险，不能只测 base model。

### 9.10 局限与质量判断

#### 有价值的部分

- 覆盖多个真实 production applications，而不是只在自建 mock Agent 上测试；
- 分开研究 foundation model、application policy 和 marketplace resolution；
- 有 search/no-search 的强机制证据；
- skill 阶段确实涉及真实安装路径，并在受控环境验证 payload。

#### 为什么当前仍主要作为想法邻居

- arXiv v1，尚未经过正式同行评审；
- 用户 prompt 明确包含 clone/install，不能外推到零安装意图的普通任务；
- skill 主要只有14个 target，cross-assistant 更缩小到3个，每 cell 多为10个手工 trials；
- 公开平台上注册的是 benign payload；真正恶意版本通过本地修改或私有环境验证，未测试平台恶意检测链；
- 安装和后续“use the skill”是两个显式阶段，不是 ordinary task 驱动的单条自治轨迹；
- 论文的 botnet scalability 是基于热门请求量与可迁移候选的推断，没有测真实受害设备或传播 prevalence；
- 不同 assistant 版本、模型和 marketplace 排名更新会快速改变具体数字；
- Table 1 的 fetch、payload 和 overall 使用分阶段口径，阅读时容易被误当成同一分母。

合理定位是：**真实系统攻击链的有力 case study，但它回答的是显式资源获取请求中的名称解析与抢注风险，不是普通任务下自主 acquisition 的因果测量。**

### 9.11 原文证据索引

| PDF 页码 | 位置 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–3 | Abstract、Introduction、Table 1、Threat Model | 攻击链、应用范围、E2E 总表 | 总体定位 |
| 4–8 | Section 3、Tables 2–8 | repository sets、14k+ probes、search 与 hallucination | repository 实验 |
| 9–11 | Sections 4.1–4.4、Table 10 | ClawHub、V1/V2、skill protocol | skill 攻击面 |
| 11–13 | Sections 4.5–4.8、Tables 10–11 | cross-model/skill/assistant 与 controlled RCE | skill 结果 |
| 13–14 | Mitigations、Limitations | search-before-fetch、平台防御、伦理实验边界 | 防御与局限 |
| 18–22 | Appendices、Tables 12–19 | universal candidates、prompt framing、search ranking、原因消融 | 细节复核 |

---

## 10. SCR

### 10.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** | *Benign in Isolation, Harmful in Composition: Security Risks in Agent Skill Ecosystems* |
| **作者 / 单位** | Yi Xie, Jiawei Du, Yu Cheng, Jiuan Zhou, Zhaoxia Yin；ECNU / A*STAR / Shanghai Innovation Institute |
| **Venue / 年份** | arXiv v1（2026-06-13） |
| **PDF** | [2606.15242.pdf](papers/2606.15242.pdf) |
| **代码** | [SCR-Bench](https://github.com/saint-viperx/SCR_Bench) |
| **Problem** | 单独审核每个 skill 会漏掉组合路径风险：上游 skill 的目标、信任信号或 advisory context 可能在下游被重新解释成行动或授权。 |
| **Main Idea** | 将 skill composition path 而非单个 artifact 作为安全分析单位，并用 CapFlow、TrustLift、AuthBlur 三个受控子 benchmark 测量组合后产生的状态变化。 |
| **Key Innovation** | 提出 capability flow、trust transfer、authorization confusion 三种路径机制；区分 path activation 与 activation 后的 conditional harm；强调“Benign in Isolation, Harmful in Composition”。 |
| **Technical Contribution** | 组合图形式化；CapFlow 150 cases、TrustLift 每 backend 401 trials、AuthBlur 118 retained cases；受控 mock state 和多模型对比。 |
| **Main Finding** | CapFlow composed-neutral 平均 ASR 33.6%；TrustLift control 1.10%→endorsed 83.89%；AuthBlur L0 15.7%→L1 27.0%→L3 34.0%。 |
| **Work Focus** | 机制提出、合成受控 benchmark 和概念验证。三个子 benchmark 的环境和 endpoint 不统一，主要说明“可能存在这种路径风险”，不能作为真实市场 prevalence 或真实安装链的强证据。 |
| **证据等级** | **想法补充 / 中等偏弱实证。** 受控对照对机制有启发，但 arXiv v1、mock 环境、异构子任务、缺少生产 registry/真实落盘验证；最适合作相关工作与实验设计灵感。 |
| **Relation to Our Work** | CapFlow 的 neutral condition 支撑“Agent 可能自主组合现有能力”；TrustLift 是最接近 harmful install 的邻居，但它从已出现的下游安装请求开始，且安装为 simulated state，不覆盖 ordinary task→真实发现→落盘→调用。 |

### 10.2 一句话结论

SCR 提供了一个很有用的观察角度：单个 skill 看起来都安全，不代表它们的输出在共享 context 中串起来以后仍安全；但它目前更像三个机制的受控 PoC，而不是统一、真实的 skill ecosystem benchmark。

### 10.3 三种风险机制

| 子 benchmark | 上游产生什么 | 下游如何误用 | 成功 endpoint |
|---|---|---|---|
| **SCR-CapFlow** | 具体 target 或 operational context | execution skill 对该 target 产生越权 side effect | discovery target 与被操作 target 相同，且 mock state 有可观察副作用 |
| **SCR-TrustLift** | review / endorsement / trust signal | 后续 harmful installation request 被解释为可信 | simulated marketplace 状态记录 harmful skill installed |
| **SCR-AuthBlur** | related context、finding 或 advisory signal | 建议被误当成 approval / authorization | downstream decision 批准 risky request |

论文用 context-dependent composition graph `G_h=(V,E_h)` 表示在任务 context 下可被激活的 skill edges，并将路径风险写为：

```text
r_path(h) = P(path activated | h)
            × P(harm | path activated, h)
```

这个分解是有价值的：安全风险既可能来自 Agent 更愿意走某条组合路径，也可能来自一旦路径被激活，系统没有边界阻止下游 harm。

### 10.4 Threat model

| 问题 | SCR 的设定 |
|---|---|
| **用户输入是什么** | 不同子 benchmark 使用 task context、安装请求或审批场景；没有统一的 ordinary-task 起点。 |
| **攻击者控制什么** | 能构造或利用 skill composition path，使上游输出成为下游 target、trust signal 或 authorization cue。 |
| **skill 是否预装/可用** | CapFlow 研究已经可用的 skill 组合；TrustLift 在 simulated market 中测试 downstream install decision。 |
| **是否明确要求安装** | TrustLift 从一个 downstream installation request 开始，不是由普通能力任务自主推导出安装需要。 |
| **环境真实性** | controlled sandbox 与 observable mock state；TrustLift 的安装是 simulated market state。 |
| **主要安全边界** | 数据→行动、review→信任、advice→authorization 三类跨 skill 语义边界。 |

### 10.5 数据、条件与指标

#### SCR-CapFlow

- 150 paired-skill cases；
- 9 个完整后端；
- 每个 case-condition 5 trials；
- Control、A-only、B-only、A+B Neutral、A+B Explicit 五个条件；
- 成功必须同时满足 `discover(t) ∧ side_effect(t) ∧ uses_discovered_target(t)`。

平均结果：Control=0%，A-only=0%，B-only≈1.4%，A+B Neutral=33.6%，A+B Explicit=35.9%。Neutral 条件使用正常任务语言，不明确要求组成 harmful chain；Explicit 是可执行性 positive control。

#### SCR-TrustLift

- 5 个模型后端；
- 每个 backend 401 installation trials；
- Control 与 Endorsed 两个 context；
- endpoint 是“harmful skill is installed”，但安装发生在 simulated skill market。

平均 Control ASR=1.10%，Endorsed ASR=83.89%。模型差异很大：Opus-4.6 endorsed 为25.19%，其余四个约96.5%–100%。

#### SCR-AuthBlur

- 10 个后端；
- 主表使用 118 retained decision cases，L0/L1/L3，每个 case-level 5 trials；
- L0 unrelated control，L1 related task context，L3 强 advisory 但声称不含 formal authorization；
- 主表平均从15.7%→27.0%→34.0%；
- L2 plain-finding 只在满足更严格 audit criterion 的52个 cases上报告。

### 10.6 Main Idea、创新与 technical contribution

#### Main Idea

把安全分析单位从孤立 skill 节点扩展到被 Agent 实际激活的组合路径。

#### 主要创新

1. 用 capability、trust、authorization 三类边界解释组合风险。
2. 将 path activation 与 activated-path harm 分开建模。
3. endpoint 尽量使用 mock downstream state，而非仅看模型是否描述危险动作。
4. 用 neutral/explicit 与 isolated/composed 对照说明组合路径是关键变量。

#### Technical contributions

- context-dependent composition graph；
- 三个机制的 estimator 和 case set；
- 多模型、多条件 sandbox trials；
- CapFlow linked-target state verifier；
- TrustLift endorsement/control 和 AuthBlur context-level 消融。

### 10.7 Work 主要放在哪里

SCR 的主要投入是：

1. 提出统一的“path-level risk”语言；
2. 将三种常见语义传播分别做成受控场景；
3. 在多个模型后端上验证 isolated 与 composed 条件存在差异；
4. 用 observable mock state 提高结果的可核查性。

它没有形成一个像 AgentDojo 那样统一的应用环境、用户任务层级和 security-case 生成框架。CapFlow、TrustLift 和 AuthBlur 的任务、模型集合、trial 数和 endpoint 不同，因此三组数字应分别阅读，不能合成一个统一的“SCR ASR”。

### 10.8 与当前 Acquisition Gap 的关系

#### 可以直接借鉴

- path activation 与 conditional harm 应拆开测，这与 Acquisition Funnel 的条件存活率一致。
- neutral 与 explicit 条件应分开，避免把用户已经指定攻击路径的结果说成 Agent 自主组合。
- 上游 review/endorsement 可能改变下游 high-risk decision，说明“信任”本身是可传播的系统状态。
- downstream observable state 比模型口头表态更可信。

#### TrustLift 与我们最接近但不能混同

```text
SCR-TrustLift：upstream endorsement
             → 已出现的 downstream install request
             → simulated harmful installation

Acquisition Gap：ordinary capability task
               → Agent 自主 search/retrieve
               → real on-disk install/register
               → invoke/payload/task_ok
```

TrustLift 证明 endorsement 可以抬高一个已经进入安装决策的问题；它没有证明普通任务会产生 search/install intent，也没有测真实落盘、注册、调用和 payload。

#### 推荐使用位置

- Related Work：skill composition / trust-transfer 最近邻；
- Method：引用 path activation × conditional harm 的分解思想；
- Discussion：approval signal 如何污染后续决策；
- 不宜作为真实市场风险量级或 autonomous acquisition prevalence 的依据。

### 10.9 局限与质量判断

#### 有价值的部分

- “节点安全不等于路径安全”的问题定义清楚；
- CapFlow linked-target endpoint 比只检查两个 skill 是否被调用更严格；
- Neutral 与 Explicit 分开，有助于识别自主组合；
- TrustLift 对我们的 scaffold trust/authorization 叙事有直接启发。

#### 为什么目前只作为想法补充

- arXiv v1，尚未经过正式同行评审；
- 三个子 benchmark 是异构 PoC，不是一条统一的 end-to-end execution trajectory；
- sandbox/mock state 抽象掉真实 registry、安装器、文件系统、权限和 runtime policy；
- TrustLift 的“installed”是模拟状态变化，不能等同于真实第三方代码落盘和执行；
- AuthBlur 的 L0、L1、L3 同时改变 context 相关性、路径显式度和语义强度，因果解释不如单变量对照干净；
- 不同子 benchmark 使用不同 backend 集合，跨机制比较不稳；
- 论文没有给出真实生产 skill ecosystem 的外部验证，也没有提出并实测 path-aware defense；
- 模型使用 provider default decoding，复现实验还依赖当时的模型版本与服务行为。

因此，合理定位是：**机制命名和 benchmark idea 很有启发，但证据更适合支持“这个风险值得测”，不足以单独支撑现实风险规模或当前工作的 headline。**

### 10.10 原文证据索引

| PDF 页码 | 位置 | 证据内容 | 用途 |
|---:|---|---|---|
| 1–3 | Abstract、Introduction、Figure 1 | SCR 定义、三种机制、主要主张 | 问题与贡献 |
| 4–6 | Sections 3.1–3.4、Figures 2–3 | composition graph、path risk、benchmark construction | 方法 |
| 7–9 | Section 4、Figure 4、Tables 2–4 | 三个子 benchmark 的结果 | 结果分母与差异 |
| 11–14 | Limitations、Appendix B–D、Tables 5–7 | mock 环境、AuthBlur levels、实验协议 | 边界与复核 |
| 14–15 | Tables 8–9 | TrustLift/AuthBlur 完整数值 | 数字引用 |

---

## 后续论文追加模板

> 复制本节并完成填写；随后按重要性插入正文、统一重编号。至少完成摘要表、指标分母、与当前工作的关系、不能过度声称和原文证据索引。

### N.1 导师表单摘要

| 字段 | 内容 |
|---|---|
| **Paper** |  |
| **作者 / 单位** |  |
| **Venue / 年份** |  |
| **PDF** |  |
| **代码 / 项目** |  |
| **Problem** |  |
| **Main Idea** |  |
| **Key Innovation** |  |
| **Technical Contribution** |  |
| **Main Finding** |  |
| **Work Focus** |  |
| **Relation to Our Work** |  |

### N.2 一句话结论

### N.3 研究问题与动机

### N.4 Threat model

| 问题 | 论文设定 |
|---|---|
| 用户输入是什么 |  |
| 攻击者控制什么 |  |
| Agent/scaffold 已拥有什么 |  |
| 目标 skill/tool 开始时是否可见或预装 |  |
| 是否需要用户显式授权 search/install |  |
| 主要安全边界 |  |

### N.5 系统或方法结构

### N.6 数据与测试规模

### N.7 指标与分母

| 指标 | 分子 | 分母 | 条件 | 原文位置 |
|---|---|---|---|---|
|  |  |  |  |  |

### N.8 Baseline、intervention 与因果对照

### N.9 主要实验结果

### N.10 Main Idea、创新与 technical contribution 的区分

### N.11 Work 主要放在哪里

### N.12 与当前 Acquisition Gap 的关系

- 可以直接背书：
- 只能类比：
- 明确差异：
- 推荐放置位置：

### N.13 局限与不能过度声称

### N.14 原文证据索引

| PDF 页码 | 表/图/段 | 证据内容 | 用途 |
|---:|---|---|---|
|  |  |  |  |

### N.15 对我们实验设计的具体启发
