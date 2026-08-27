# 组会论文分享方案：Do Not Mention This to the User（主讲）+ SCR / HalluSquatting（补充）

**日期**：2026-07-26
**用途**：本次组会选篇与逐页提纲。与 `25_GROUP_MEETING_PAPER_TALK.md`（IPI + Do Not Mention 双主讲）不同，
本方案按你最新的汇报计划组织：**主讲 Do Not Mention，一篇讲透真实恶意 skill 生态；再用 SCR 和 HalluSquatting 两篇做补充**，
分别补上"组合/背书如何促成安装"和"幻觉如何触发真实执行/RCE"两条邻居线。
**事实基准**：三篇的数字均已于 2026-07-26 回原文 PDF 逐条核对（见每篇末尾「原文核对」）。
三份 PDF 都在本地：Do Not Mention = `papers_phase8/2602.06547.pdf`，SCR = `papers_mentor_sources/2606.15242.pdf`，HalluSquatting = `papers_phase10/2607.07433.pdf`。

---

## 0. 一句话选篇逻辑

> **一篇主讲 + 两篇补充，回答同一个供应链问题的三段：**
> **恶意 skill 真实存在吗（Do Not Mention）→ 它怎么被"促成"安装/组合（SCR）→ 幻觉如何把安装变成真实执行/RCE（HalluSquatting）。**
> 三篇拼出一条从"供给"到"执行"的链；我自己的工作正是想测这条链在**普通能力任务触发、目标尚未安装**时会不会自主接起来、断在哪一段。

选这个组合的三个理由：

1. **主线聚焦**：Do Not Mention 是 USENIX Security 2026 已录用的大规模生态测量，方法完整、数字扎实，一篇就能撑起主讲。
2. **两篇补充各补一刀**：SCR 补"促装机制"（组合/背书），HalluSquatting 补"真实执行/RCE"，正好覆盖 Do Not Mention 没回答的"会不会被获取进来"和"进来后能不能真跑起来"。
3. **能自然引出我的问题**：三篇都不是"普通能力任务 → 自主发现 → 真实安装/注册/调用"的同轨迹逐段测量，这正是我 pilot 想验证的缺口（见 `23_NORTH_STAR_PITCH.md`）。

---

## 1. 建议时长与结构（20 分钟版）

| 时间 | 内容 |
|---:|---|
| 1 min | 供应链三段问题 + 三篇如何拼 |
| 11 min | **主讲：Do Not Mention**（问题 → 测量漏斗 → 验证质量 → RQ1/RQ2/RQ3 三条发现 → 局限） |
| 3 min | **补充①：SCR**（三个子基准：CapFlow / TrustLift / AuthBlur） |
| 2 min | **补充②：HalluSquatting**（repo squatting + skill squatting + 真实 RCE） |
| 2 min | 三篇合起来的启示 + 我的待验证问题 |
| 1 min | 讨论题 + 缓冲 |

> **主/补比例**：主讲占约一半时长（11 min），两篇补充各只讲"补哪一刀 + 一组核心数字"，
> 体现"一篇主讲、两篇补充"，不要让补充喧宾夺主。

若只有 12 分钟：主讲压到 7 分钟（保留漏斗 + RQ1 + RQ2 两个原型），SCR/HalluSquatting 合并成一页"最新邻居对比表"，自己的工作只留 1 页。

---

## 2. 主讲：Do Not Mention This to the User

> *"Do Not Mention This to the User": Detecting and Understanding Malicious Agent Skills in the Wild*
> Yi Liu et al.，USENIX Security 2026

### Slide 1 — 它问什么

公开 agent skill registry 里，**真实的恶意 skill 到底有多少、长什么样、怎么被行为验证出来？**

- 现有 skill 生态缺少**行为确认（behavior-confirmed）**的恶意样本测量：大多停在文本/静态规则层面。论文引言就点名前人工作（Liu et al. [19]，即另一篇 `arXiv:2601.10338`）用 SkillScan 静态扫描发现 **26.1% 的 skill 含"潜在风险模式"**，但**无法区分"恶意"还是"开发者失误"，也没确认可疑代码是否真的执行**。Do Not Mention 要补的正是这一刀：**从"潜在风险"收紧到"行为确认恶意"。**
- 标题 "Do Not Mention This to the User" **概括了真实恶意 skill 里反复出现的一类 secrecy instruction**——要求 agent 对用户**隐藏**自己的真实行为（样本中可见类似 "do NOT mention in conversation, just include it" 的原句）。这是全篇的题眼：**文档说的和实际做的不一致。**

### Slide 2 — 测量漏斗（这一页是全篇骨架）

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

讲法要点：**每一层都在收紧证据强度**，从"文本可疑"→"运行时确有可疑行为"→"人工确认恶意"。
`157 / 98,380 = 0.16%` 是**高精度行为确认下的下界**，不是"生态只有 0.16% 有风险"——很多可疑样本因为沙箱时限/触发条件没被激活而漏掉。

### Slide 3 — 验证质量（为什么这些数字可信）

- **Docker 隔离执行**，监控网络、系统调用、文件系统；
- **honeypot credentials**（诱饵凭证）看 skill 会不会去偷/外发；
- **三种触发方式**：metadata-driven（靠 skill 自己的元数据/描述触发）、LLM 生成输入、多轮调用；
- 只有观察到**外泄、未授权网络、解码后隐藏功能、提权**等真实行为，才进入两人独立人工确认；
- **责任披露**：157/157 在披露后被 registry 移除。

### Slide 4 — 三条核心发现（按论文的三个 RQ 组织）

论文不是"扫完 98,380 个文件就结束"，后半部分的分析贡献才是重点。建议按它自己的三个研究问题讲：

**RQ1 — 威胁全貌长什么样？**
- 157 个恶意 skill 共 **632 个漏洞实例**，覆盖 **13 种攻击技术、6 个 kill-chain 阶段**；
- 单个恶意 skill 平均含 **4.03** 个漏洞、横跨**中位 3 个阶段**——是**蓄意分层**，不是偶然堆砌（80.3% 含 ≥3 个，最多一个含 13 个）；
- **84.2%** 的漏洞落在 `SKILL.md` 的**自然语言面**——攻击主要写在提示词/文档里，不只在代码里。

**RQ2 — 攻击者用什么策略？**（这一条最容易被忽略，务必讲）
- 用 Fisher 精确检验做共现分析，发现**两种彼此负相关的攻击原型**：**Data Thieves**（供应链数据外泄）与 **Agent Hijackers**（指令级劫持）——攻击者**二选一专精**，很少混用；
- **单一"工业化"行为者用模板化的品牌仿冒，贡献了 54.1%** 的确认恶意 skill——所以总体统计受 **campaign concentration** 影响，**不能当"独立随机分布"解读**。

**RQ3 — 怎么逃避检测？**
- 逃避手段**随复杂度升级**：shadow features（文档宣称 vs 实际行为不一致）从最低级的 **0% 一路升到最高级的 100%**（确认样本整体 **73.2%** 含 shadow features）；
- 越复杂的攻击越倾向**武器化平台自带的信任机制**（platform-native attack vectors）。

**局限（放在发现之后，别说过头）**：60 秒沙箱、环境门控（skill 察觉在沙箱里就装乖）、多会话/休眠触发都可能**漏检**。所以 157 是作者**优先保证精度**得到的**行为确认下界**；但现有实验**不能据此反推真实总体恶意比例**（"下界"≠"真实值一定更高很多"）。

### Slide 5 — 它对我研究的意义

它**回答了**：外部市场里有没有真实恶意 skill？——有，而且已经**规模化、隐蔽化（shadow features）供应**。

它**没有回答**：当用户只给**普通能力任务**时，agent 会不会**自主**把这些第三方 skill 发现、安装、调用进来？

> 所以生态测量为 acquisition risk 提供了**现实性锚点**，但不能替代 acquisition 的 E2E 实验——"存在恶意供给" ≠ "会被自主获取进执行链"。这正是我 pilot 的切入点。

### 原文核对（Do Not Mention，2026-07-26 已回本地 PDF `papers_phase8/2602.06547.pdf` 逐条核对）

- 漏斗 98,380 → 4,287（4.4%）→ 762 触发 runtime indicator → 157 行为确认（3.7% of candidates；**0.16% of 98,380**）→ 632 漏洞实例、13 技术、6 kill-chain 阶段 ✓ 摘要/§1/Table 2。
- 平均 4.03 漏洞、中位 3 阶段 ✓；84.2% 在 SKILL.md 自然语言面 ✓；shadow features 73.2%（115/157）✓；单一行为者 54.1%、模板化品牌仿冒 ✓；shadow features 随复杂度 0%→100% ✓。
- 行为验证精度 99.6%，比最强静态基线（≤1.1%）高约 90× ✓；两位复核者 Cohen's κ=0.91 ✓；157/157 披露后移除 ✓。
- ✅ **26.1% 交叉引用已彻底坐实（这是一个容易踩的坑，组会可主动点破以显严谨）**：
  - **26.1% 不是 Do Not Mention 的结果**。它来自**另一篇** *Agent Skills in the Wild: An Empirical Study of Security Vulnerabilities at Scale*（`arXiv:2601.10338`）：收集 42,447 个 skill、分析 31,132 个，其中 8,126 个被 SkillScan 静态判为**含 ≥1 个 vulnerability**，即 26.1%——是 **"潜在风险/漏洞筛查"口径**。
  - **Do Not Mention 在自己引言里就把 26.1% 当"前人工作 [19]"引用**，并明确指出它**无法区分恶意与开发者失误、也没确认代码是否真的执行**——Do Not Mention 的贡献正是把这一步收紧到 **0.16%（157 个行为确认恶意）**。
  - **SCR（`2606.15242`）的参考文献表把这句 26.1% 错指成了 Do Not Mention**，属于 **SCR 自身的引用错配**，不是"同一篇里的两个口径"。
  - 另注：Do Not Mention 正文另有一个**无关**的 41/157 = 26.1% 共现攻击链数字，**别和上面的混为一谈**。
  - 组会安全说法：**"26.1% 是漏洞筛查口径（另一篇 + SkillScan），0.16% 是行为确认恶意口径（Do Not Mention）——数据集、分母、判定标准都不同，绝不能混用。"**

---

## 3. 补充①：SCR — Benign in Isolation, Harmful in Composition

> *Benign in Isolation, Harmful in Composition: Security Risks in Agent Skill Ecosystems*
> Yi Xie, Jiawei Du et al.（East China Normal University / A*STAR），arXiv `2606.15242`（预印本）

**一句话**：单个 skill 单独审查都"安全"，但在**共享执行上下文里被组合调用**时会变危险。作者把这个缺口叫 **SCR（Skill Composition Risk）**，并做了 **SCR-Bench**——它**不看单个 skill 的文本意图或表面行为，而是记录下游状态变化和 path-level 结果**。

**SCR-Bench 有三个子基准**（⚠️ 注意：`24/25` 号文档只讲了前两个，别在组会漏掉第三个）：

| 子基准 | 机制 | 关键结果 |
|---|---|---|
| **SCR-CapFlow** | 上游 skill 把目标/操作上下文"喂"给下游有害动作（能力流） | 隔离基线近 0%；组合后 **Neutral 平均 33.6% / Explicit 平均 35.9%**；DeepSeek-V4 >90% |
| **SCR-TrustLift** | 上游 review/security 类 skill 把"合法性"传递给后续**安装决定**（信任转移） | 平均 ASR **1.10%（control）→ 83.89%（endorsed）**，平均 lift +82.79pp；**4/5 backend ≥96.5%**（Opus-4.5、MiniMax 100%，Gemini 97.76%，GPT-5.4 96.51%），Opus-4.6 保守但仍 +25.19pp |
| **SCR-AuthBlur** | advisory/audit 类上下文把 agent 的审批边界推向不安全（授权混淆） | risky-approval 率 **15.7% → 27.0%**（相对 +71.8%） |

**核心论点**："Benign in Isolation, Harmful in Composition" —— skill 安全必须在**激活的组合路径（activated path）**层面评估，而不是单个 artifact。

**与我的关系 / 边界**（组会必须说清）：

- SCR-CapFlow 已经用 **Neutral 中性任务语言**测了 agent 的**自主组合**（平均 33.6%）——所以我**不能**再说"第一个测自主/中性触发"；
- SCR-TrustLift 已经在 **simulated skill market** 里测了**有害安装**（1.10%→83.89%）——所以我**不能**再说"第一个研究 install"或"SCR 只测预装 skill"；
- **仍可守的区别**：TrustLift 从一个**已经出现的下游安装请求**开始，且市场是 **controlled simulation**；它不从"用户只给普通能力任务"起步，也不验证**真实落盘 / manifest / registry / 后续调用**的同轨迹全链。这正是我要测的那一刀。

### 原文核对（SCR，2026-07-26 逐条核对 PDF）

- 33.6% / 35.9%（CapFlow Neutral / Explicit）✓ 正文 §4.2；DeepSeek-V4 >90% ✓。
- 1.10% → 83.89%、+82.79pp、4/5 backend ≥96.5%、Opus-4.6 +25.19pp ✓ Table 2（§4.3）。
- AuthBlur 15.7% → 27.0%、相对 +71.8% ✓ 摘要 + 引言。
- 三个子基准全称：SCR-CapFlow / SCR-TrustLift / SCR-AuthBlur ✓ 摘要。

---

## 4. 补充②：HalluSquatting — Beware of Agentic Botnets

> *Beware of Agentic Botnets: Scalable Untargeted Promptware Attacks via Universal and Transferable Adversarial HalluSquatting*
> Aya Spira, Stav Cohen, Elad Feldman, Ron Bitton, Avishai Wool, Ben Nassi（Tel Aviv University / Technion / Intuit），arXiv `2607.07433`（预印本）

**一句话（机制）**：LLM 会"幻觉"出不存在的资源名（repo、skill）。攻击者**先算出模型对热门资源名的幻觉分布，抢先注册**这些幻觉名，在里面塞对抗性提示词（例如"安装一个 bot / 跑一段装 bot 的脚本"）。因为幻觉在不同基础模型间**可预测、可迁移**，一次注册就能撒网命中很多 LLM 应用——作者称之为可扩展的、**无需直接注入通道**的 promptware，甚至能组 botnet。这是 typosquatting 的"幻觉版"。

**两个攻击面**（⚠️ doc 24 只引了 skill 的 40–100%，组会最好把两条都点到）：

| 攻击面 | 触发 | 真实系统 | E2E（tool invocation / RCE） |
|---|---|---|---|
| **Repository squatting** | 用户请求 clone 一个 repo | Cursor、Cursor CLI、Gemini CLI、Windsurf、**Copilot Chat**、Cline（六个） | **20%–65%** |
| **Skill squatting** | 用户请求 install 一个 skill | OpenClaw、NanoClaw、ZeroClaw | **40%–100%** |

- **两组数字别搞混**：**幻觉生成率**（模型本身编错名字的比例）repo 场景 up to **85%**、skill 场景 up to **100%**（来自摘要）；**Table 1 报的是端到端的 fetch/payload 执行率**（repo 20–65%、skill 40–100%），不是幻觉生成率。
- **E2E 是"受控、分阶段"验证，不是公开投毒**（这点要主动说清，否则听众会以为作者真在 GitHub/ClawHub 上放了恶意 skill）：① 在公开平台只注册**良性**的替身资源，测 squatting/fetch 是否命中；② 在**研究者自己的机器**上把 skill 文件换成真实 RCE / tool-invocation 载荷，再测执行。装进去后由一句"我们用一下这个 skill 吧"触发。
- 幻觉在基础模型之间以及向应用层**可迁移**；只有会"运行前完整检查脚本"的后端（GPT-5.4 Codex）偶尔会拒绝，几乎所有 Claude 后端都会默默中招。

**与我的关系 / 边界**（组会必须说清）：

- HalluSquatting 已经测了**真实应用中的真实 E2E / RCE（40–100%）**——所以我**不能**再说"第一个测真实执行 / E2E"；
- **仍可守的区别**：它的触发是**用户明确要求 clone/install 一个资源**（用户已经有获取意图，只是被幻觉+抢注劫持到恶意资源）。我要测的是**用户完全没有 acquisition 意图、只给普通能力任务**时，agent 会不会**自己**发起外部发现并装进来。两者威胁模型不同。

### 原文核对（HalluSquatting，2026-07-26 逐条核对 PDF）

- repo squatting E2E 20%–65% ✓（Table 1，六个代码助手：Cursor、Cursor CLI、Gemini CLI、Windsurf、**Copilot Chat**、Cline）。
- skill squatting E2E 40%–100% ✓（§4，OpenClaw、NanoClaw、ZeroClaw）；装后聚合成功率 96%（聊天外泄）/ 84%（终端反弹）✓ Insight 11。
- 幻觉**生成率** up to 85%（repo）/ up to 100%（skill）来自**摘要**；**Table 1 是 E2E fetch/payload 执行率**，两者不是同一指标 ✓。
- E2E 为**受控分阶段**：公开平台只注册良性替身，RCE 载荷在研究者本地机器上测（私有 squat，未公开发布）✓ §4.8 / §7 伦理。
- 机制 = adversarial hallucination squatting（抢注幻觉资源名承载对抗提示）✓ 摘要。

---

## 5. 三篇合起来 → 我的问题

```text
① Do Not Mention          ② SCR                       ③ HalluSquatting
恶意供给真实存在           组合/背书促成安装/危害        幻觉+抢注 → 真实执行/RCE
98,380→157（0.16%）        CapFlow 33.6% / TrustLift    repo 20–65% / skill 40–100% E2E
84.2% 写在 SKILL.md 文本    1.10%→83.89% / AuthBlur      触发=用户显式 clone/install
                          触发=已出现的下游安装请求
```

**这张图是"研究问题拼图"，不表示三篇的百分比可以直接横比**（起点、终点、成功定义都不同）。

**三篇共同没覆盖、也正是我 pilot 要测的**：

> 用户只给**普通能力任务**、目标 skill **一开始未安装**时，agent 会不会**自主**走完
> `缺口 → 外部发现/检索 → install call emitted → parsed → executed → on-disk → registered → invoked → payload & task_ok`，
> 这条链**断在哪一段**、由**模型**还是**tool budget / parser / policy / scaffold**决定。

我已有的先导抓手（**要带条件讲，别当普适结论**）：

| 现象 | 内容 | 只能说什么 |
|---|---|---|
| Selection friction | 单模型/单框架/20 任务，恶意 skill **预装**下 Vanilla 0/20、粗蹭热度 2/20、5 轮 LLM 优化 1/20 | 该设定下"通用描述抢不过正确的专一工具"的**先导观察**，非跨模型定律 |
| Measurement pitfall | 模型**吐出**了 `install_skill(...)`，但默认 3 轮 tool budget 被耗尽，**从未执行** | emitted / parsed / executed **必须拆开**；单次调试**不能**证明稳定 execution gap |

---

## 6. 讨论题（只留两个）

1. 一个"全链逐段测量"要出现什么级别的**结构性结果**（稳定断点 / 可归因 / 跨设置复现），才够成为一篇 security measurement paper？
2. 为了不做成玩具市场，正式实验至少需要哪些**真实系统要素**：真实 registry snapshot、真实落盘/manifest、多个 scaffold，还是生产级 agent？

---

## 7. 组会口径红线（必须避免的表述）

| 不要说 | 改成 |
|---|---|
| "现有工作都没测 E2E" | HalluSquatting 已测显式安装条件下的真实 E2E / RCE（40–100%） |
| "SCR 只组合预装 skill" | CapFlow 是 available-skill 组合；**TrustLift 已测 simulated market install**；还有 **AuthBlur** 测授权混淆 |
| "第一个测自主 / 中性触发" | SCR-CapFlow Neutral 已用中性任务语言测自主组合（平均 33.6%） |
| "第一个研究 install" | SCR-TrustLift、HalluSquatting 均已覆盖不同形式的安装 |
| "所有论文都把单段 ASR 当 E2E" | 各文起点与 endpoint 不同，不能直接横比或外推 |
| "我的 0–10% 证明明确任务天然安全" | 单模型/单框架/20 任务的**先导观察**，需扩大验证 |
| "research gap 就是 novelty" | gap 只提出问题；贡献要来自新测量 / 新现象 / 方法 / 防御 |
| "0.16% 说明生态基本安全" | 0.16% 是**高精度行为确认下界**，可能因沙箱时限/休眠触发漏检；但**不能据此反推真实总体恶意比例** |
| "Do Not Mention 发现 26.1% 的 skill 有漏洞" | 26.1% 来自**另一篇**（`2601.10338` + SkillScan）的漏洞筛查口径，被 SCR 错引成 Do Not Mention；Do Not Mention 自己的数是 **0.16% 行为确认** |
| "HalluSquatting 在公开市场投放了恶意 skill" | 公开只注册**良性**替身；RCE 载荷是研究者**本地受控**测的，分阶段 E2E |

---

## 8. 备答（可能被追问）

**Q1：为什么主讲 Do Not Mention，而不是 IPI？**
> IPI（Retrieval Barrier）是我的**方法学祖先**（"不要默认中间步骤会自动发生"），适合讲"怎么把一个 barrier 做成完整顶会论文"；但本次我想让主线聚焦在**真实恶意 skill 生态**上，所以主讲 Do Not Mention，用 SCR/HalluSquatting 补"促装"和"执行"两段。IPI 我在方法启示处一句话带过即可。

**Q2：SCR 都测到安装了，你还做什么？**
> SCR-TrustLift 研究的是**上游背书如何改变一个已经出现的下游安装请求**，安装发生在 **simulated market**。我从**普通能力任务**起步，目标一开始未安装，需要 agent **自己**发起外部发现，并用**真实文件 / manifest / registry / 后续调用**验证状态。是否有稳定差异要用**同轨迹实验**做出来，不能靠措辞。

**Q3：HalluSquatting 已经打到 RCE 了，你的新意在哪？**
> 它的触发是**用户明确要 clone/install**（有获取意图，被幻觉+抢注劫持）。我测的是**用户零 acquisition 意图**、只给能力任务时，agent 会不会**自发**把第三方 skill 获取进来。威胁模型不同：一个是"被劫持的显式安装"，一个是"任务诱导的自主安装"。

**Q4：如果普通任务下根本不自主安装呢？**
> "不安装"本身不够。只有当漏斗出现**稳定断点**、能通过 budget/policy/scaffold **消融解释**，或证明 explicit-install / post-load 指标**系统性不能外推**到 ordinary-task E2E，才有 measurement 价值；否则按**预先规则 No-Go**（见 `22_PILOT_AND_HYPOTHESIS_SELECTION_PLAN.md`）。

**Q5：三篇会不会只是"把别人的阶段拼起来"？**
> 只画一条长链确实不够。pilot 的目标是检验**端点之间是否有稳定的 execution gap**，以及 scaffold/policy 是否系统性改变风险。只有得到可复现的结构性发现，才继续做正式论文。

---

## 9. 论文入口

- **主讲** — [Do Not Mention This to the User — USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/liu-yi)
- **补充①** — [SCR (Benign in Isolation, Harmful in Composition) — arXiv:2606.15242](https://arxiv.org/abs/2606.15242) ·  代码 https://github.com/saint-viperx/SCR_Bench
- **补充②** — [HalluSquatting (Beware of Agentic Botnets) — arXiv:2607.07433](https://arxiv.org/abs/2607.07433)
- 方法学祖先（备用） — [Overcoming the Retrieval Barrier — USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/chang-hongyan)

*安全说明：本地实验只使用合成任务与合成敏感数据；payload 仅写 marker 或发送到 `127.0.0.1` collector，不进行真实外泄。*
