# 15 — 文献清单：全名 · 链接 · 明确佐证点

> ⚠️ **历史清单（2026-07-15）**：尚未纳入 Phase 10 对 install 直接邻居的完整复核。当前综述口径见 `17_RELATED_WORK_VISUAL_REVIEW.md`，最新短表见 `14_LIT_SUMMARY_TABLE.md`。

> **用途**：导师汇报 / related work / 答辩「这句话谁支持」  
> **日期**：2026-07-15  
> **读法**：先看「主张 → 用哪几篇」；再查表「论文 → 佐证哪一点」

---

## 0. 主张 → 文献速查（汇报用）

| 我们的主张 | 主要文献（见下表编号） |
|------------|------------------------|
| 前人常默认「毒内容已被检索/已加载」，真正瓶颈在中间步 | **P1 IPI**；**P8 2605.11418**；**P2 Skill-Inject**（对照 threat model） |
| Vanilla 不优化 ≈ 进不去；优化后检索可很高 | **P1**；**P5 ToolHijacker**；**P8 Discovery** |
| Tool/skill 系统常拆成 retrieval + selection | **P5**；**P7 How Many Tools**；**P8** |
| Skill **装载后**执行恶意指令 ASR 很高 | **P2**；**P3 Poise**；**P4 MCPTox** |
| 装后可用 body/旁路脚本 + 任务仍成功 | **P3**；**P2**（script > 正文） |
| 候选集内 / 同类工具间，改 description 可大幅抬选中率 | **P6 ToolTweak**；**P8 Selection**；**P5** |
| **跨域专一竞争**下通用描述很难赢（我们 0–10%） | **我们实验** + 与 P6/P8 **设定差异**对照；非文献直接报 0% |
| 安装/供应链是真实攻击面，但评测少测 agent 自主 install | **P2** 开篇；**P8** gap 表述；**P14** 在野恶意 skill |
| 工具返回 / 文档可当「权威通道」诱导后续动作 | **P9 AgentDojo**；**P10 InjecAgent**；**P11 README**；**P12 MSB** |
| 依赖 / 组合 / 信任转移可促装或抬危害 | **P13 SCR**；**P15 Skills Are Not Islands**；**P16 Dynamic** |
| 幻觉名/包名可被抢注用于获取 | **P17 HalluSquatting** |
| MCP/Skill 生态攻击 taxonomy（false-error 等） | **P12 MSB**；**P18 MCPSecBench** |
| 问题落在 Ecosystem + Tool 层 | **P19 LASM** 等综述 |

---

## 1. 核心文献表（名字 · 链接 · 佐证点）

### P1 · IPI — Retrieval Barrier（选题结构模板）

| 项 | 内容 |
|----|------|
| **全名** | *Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild for LLM Systems* |
| **作者/出处** | Chang et al.；arXiv:2601.07072；USENIX Security |
| **链接** | https://arxiv.org/abs/2601.07072 · PDF: https://arxiv.org/pdf/2601.07072 |
| **本机 PDF** | `/home/forks/AResearch/ANL/2601.07072v1.pdf`（若仍在） |
| **佐证点 1** | 前人评测常 **假设恶意文档会被检索到**；Vanilla 检索率约 **0%** → 「中间步是真实瓶颈」叙事成立 |
| **佐证点 2** | 用 **CEM** 优化 trigger 后，多数据集/多 embedding 上 Recall@5 可近 **100%** → 检索门可被系统攻破 |
| **佐证点 3** | 三档 Vanilla / Query+ / Optimized 对照结构 → 我们 skill selection 三档实验的设计模板 |
| **对应我们** | 选题迁移来源；S1 可上 CEM 的方法先例；**不是**直接测 skill install |

---

### P2 · Skill-Inject — 装载后 skill 文件攻击

| 项 | 内容 |
|----|------|
| **全名** | *Skill-Inject: Measuring Agent Vulnerability to Skill File Attacks* |
| **作者/出处** | Schmotz et al.；arXiv:2602.20156 |
| **链接** | https://arxiv.org/abs/2602.20156 · 项目: https://www.skill-inject.com/ · 代码: https://github.com/aisa-group/skill-inject · PDF: https://arxiv.org/pdf/2602.20156 |
| **佐证点 1** | 恶意指令藏在 skill/配置文件中，agent 可执行外泄、破坏等；报告最高约 **80% ASR** → **post-load 很危险** |
| **佐证点 2** | 开篇承认用户可像装软件一样 **install** skill，但评测默认 skill **已在上下文** → 支撑我们「他们跳过 acquisition」的划分 |
| **佐证点 3** | script/可执行辅助资源往往比纯正文更危险 → 支持旁路脚本/handler 载荷设计 |
| **对应我们** | Stage3 执行面引用；**不可**与我们的 0–10% 预装 selection 横比 |

---

### P3 · Poise — 位姿感知、隐蔽 skill 注入

| 项 | 内容 |
|----|------|
| **全名** | *Poise: Position-Aware Undetectable Skill Injection on LLM Agents* |
| **作者/出处** | Hao et al.；arXiv:2606.07943 |
| **链接** | https://arxiv.org/abs/2606.07943 · PDF: https://arxiv.org/pdf/2606.07943 · HTML: https://arxiv.org/html/2606.07943v1 |
| **佐证点 1** | 单行 body 注入 + 旁路脚本，Skill-Inject 设定上 ASR 约 **89.3%**（codex+gpt-5.2 等）→ 装后执行+隐蔽可行 |
| **佐证点 2** | 成功定义含 **任务仍通过 verifier** → 我们 E2E 应报 `task_ok`，不只 payload |
| **佐证点 3** | install/setup 段、编号步骤是高触发位置 → Stage3b 载荷放置策略 |
| **对应我们** | Stage3b/3c 主方案参考文献 |

---

### P4 · MCPTox — 真实 MCP 工具描述投毒

| 项 | 内容 |
|----|------|
| **全名** | *MCPTox: A Benchmark for Tool Poisoning on Real-World MCP Servers*（亦作 Tool Poisoning benchmark 表述） |
| **作者/出处** | Wang et al.；arXiv:2508.14925；AAAI 等 |
| **链接** | https://arxiv.org/abs/2508.14925 · PDF: https://arxiv.org/pdf/2508.14925 |
| **佐证点 1** | 恶意指令嵌在 **tool metadata/description**，基于真实 MCP servers/tools → 描述是可信边界漏洞 |
| **佐证点 2** | 多 LLM agent 评测，部分模型 **高 ASR**；更强 instruction-following 可能 **更易** 被利用 |
| **佐证点 3** | 不需要恶意代码执行，仅 metadata 即可 → 支撑「装入后 description 仍危险」 |
| **对应我们** | T3/Stage3a 描述投毒；跨模型时注意强模型更脆 |

---

### P5 · ToolHijacker — 工具文档劫持（检索+选择）

| 项 | 内容 |
|----|------|
| **全名** | *ToolHijacker: Automatic and Universal Tool Hijacking with Generated Content Injection*（以 arXiv 页名为准；常作 tool document 劫持） |
| **作者/出处** | arXiv:2504.19793；NDSS 等（以页面为准） |
| **链接** | https://arxiv.org/abs/2504.19793 · PDF: https://arxiv.org/pdf/2504.19793 |
| **佐证点 1** | 明确 **retrieval + selection 两阶段** 工具使用管线 → 我们 marketplace 检索再决策 **架构同构** |
| **佐证点 2** | 手动/朴素注入 ASR 常仅中低（约 10–30% 量级，因检索进不去）；优化 tool document 后 AHR/ASR 可到 **很高（常 80%–100% 量级）** → 与 IPI「不优化进不去」一致 |
| **佐证点 3** | 攻击对象是 **已在 tool library 的文档**，不是「从零 install」→ 对比我们多测 **进库/安装门** |
| **对应我们** | S1+S3a 方法对照；related work 差异化 |

---

### P6 · ToolTweak — 迭代改 name/description 提高选中率

| 项 | 内容 |
|----|------|
| **全名** | *ToolTweak: An Attack on Tool Selection in LLM-Based Agents* |
| **作者/出处** | arXiv:2510.02554 |
| **链接** | https://arxiv.org/abs/2510.02554 · PDF: https://arxiv.org/pdf/2510.02554 |
| **佐证点 1** | 系统迭代修改 tool **name/description** 可把选中率从约 **20% 提到约 81%**（文中设定） |
| **佐证点 2** | 场景多为 **同类/可替代工具** 之间竞争 → 解释「改 metadata 有效」的适用条件 |
| **佐证点 3** | 比我们「LLM 对抗改一段全能描述」更系统的优化环 → 装后专一 description 可借鉴其优化思路 |
| **对应我们** | 修正「description 优化没用」的说法；支持 **装后 V1 专一伪装** |

---

### P7 · How Many Tools — 可见工具数量与选择

| 项 | 内容 |
|----|------|
| **全名** | *How Many Tools Should an LLM Agent See?*（以 arXiv 页名为准） |
| **作者/出处** | arXiv:2605.24660 |
| **链接** | https://arxiv.org/abs/2605.24660 · PDF: https://arxiv.org/pdf/2605.24660 |
| **佐证点 1** | 工具过多时需限制每次暴露给模型的 tool 集合（深度选择 / top-K） |
| **佐证点 2** | 支持真实系统采用 **先检索/过滤再选择** → 我们的 search→top-k 不是人为降难度 |
| **对应我们** | S1 marketplace mock 的合理性 |

---

### P8 · Semantic Supply-chain / Under the Hood of SKILL.md — Registry 生命周期

| 项 | 内容 |
|----|------|
| **全名** | *Under the Hood of SKILL.md: Semantic Supply-chain Attacks on AI Agent Skill Registry* |
| **作者/出处** | Saha, Faghih, Feizi；Maryland；arXiv:2605.11418 |
| **链接** | https://arxiv.org/abs/2605.11418 · PDF: https://arxiv.org/pdf/2605.11418 |
| **佐证点 1（最重要）** | 明确 gap：已有工作主要关注 skill **加载之后**；**registry 侧生命周期**（准入、排序、暴露、选中）underexplored → **直接背书我们 pre-load 问题** |
| **佐证点 2 · Discovery** | SKILL.md 附加短 trigger 操纵 embedding 检索：两两胜率约 **86%**；Top-10 约 **80%** → S1 可被文本攻击打穿 |
| **佐证点 3 · Selection** | 只改 description 一句话，功能等价对抗变体被选中约 **77.6%**（多模型）→ **候选集内** description 可操纵 |
| **佐证点 4 · Governance** | 语义改写可不同程度绕过扫描 → 供应链治理不充分（可选 related work） |
| **佐证点 5** | **未单独**报告 agent 调用 `install` 的指标 → 我们的 **S2 Install barrier** 仍可差异化 |
| **对应我们** | related work 第一引用之一；S1/S3a 数字；差异化一句话见文末 |

---

### P9 · AgentDojo — 工具返回劫持

| 项 | 内容 |
|----|------|
| **全名** | *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents* |
| **作者/出处** | Debenedetti et al.；arXiv:2406.13352；NeurIPS Datasets 等 |
| **链接** | https://arxiv.org/abs/2406.13352 · PDF: https://arxiv.org/pdf/2406.13352 |
| **佐证点 1** | 工具返回的不可信数据可劫持 agent 后续工具调用与任务 |
| **佐证点 2** | 支撑 **权威通道**：假错误 / 依赖缺失写在 **工具返回** 里可改规划 → Stage2 的 I3 `NEED_SKILL` |
| **对应我们** | S0/S2 假错误升级；T1 间接注入 |

---

### P10 · InjecAgent — 工具集成 agent 的间接注入

| 项 | 内容 |
|----|------|
| **全名** | *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents* |
| **作者/出处** | Zhan et al.；arXiv:2403.02691；ACL Findings |
| **链接** | https://arxiv.org/abs/2403.02691 · https://aclanthology.org/2024.findings-acl.624/ · PDF: https://arxiv.org/pdf/2403.02691 |
| **佐证点 1** | 系统评测 tool-integrated agent 的 IPI；含直接危害与数据外泄意图 |
| **佐证点 2** | user tools vs attacker tools 设定 → 多工具诱导、外泄类危害可发表 |
| **对应我们** | Stage3 危害类型；间接注入 related work |

---

### P11 · You Told Me to Do It — 文档/README 诱导

| 项 | 内容 |
|----|------|
| **全名** | *You Told Me to Do It: Measuring Instructional Text-induced Private Data Leakage in LLM Agents*（以 arXiv 页名为准） |
| **作者/出处** | arXiv:2603.11862 |
| **链接** | https://arxiv.org/abs/2603.11862 · PDF: https://arxiv.org/pdf/2603.11862 |
| **佐证点 1** | 高权限 agent 对 adversarial README/安装文档类指令服从率可至约 **85%** 量级 |
| **佐证点 2** | 人眼难以识别 → 「文档权威通道」比用户旁白推销更危险 |
| **对应我们** | Stage2 **I4 文档权威**；修正「只靠广告卡片」的假设 |

---

### P12 · MSB — MCP Security Bench taxonomy

| 项 | 内容 |
|----|------|
| **全名** | *MCP Security Bench (MSB): Benchmarking Attacks Against Model Context Protocol in LLM Agents* |
| **作者/出处** | arXiv:2510.15994 |
| **链接** | https://arxiv.org/abs/2510.15994 · PDF: https://arxiv.org/pdf/2510.15994 |
| **佐证点 1** | 覆盖 planning → invocation → response 的 MCP 攻击评测 |
| **佐证点 2** | Taxonomy 含 **name-collision、preference manipulation、tool description injection、false-error escalation、tool-transfer** 等 → Stage2/S3 攻击菜单 |
| **佐证点 3** | **False-error** 点名「用错误信息改变后续行为」→ 直接支持 `NEED_SKILL` 实验 |
| **对应我们** | Stage2 ablation 设计依据 |

---

### P13 · SCR — 组合风险与信任转移

| 项 | 内容 |
|----|------|
| **全名** | *Benign in Isolation, Harmful in Composition: Security Risks in Agent Skill Ecosystems*（SCR） |
| **作者/出处** | arXiv:2606.15242 |
| **链接** | https://arxiv.org/abs/2606.15242 · PDF: https://arxiv.org/pdf/2606.15242 |
| **佐证点 1** | 单 skill 隔离评测可显得安全，**组合路径** 危害显著上升（文中高 ASR 区间） |
| **佐证点 2** | **TrustLift** 等：信任转移后 **有害安装** 可被大幅抬高（文中 >83% 量级表述）→ 渐进信任/先良性再促装 |
| **对应我们** | 二重依赖、companion、渐进信任叙事 |

---

### P14 · Do Not Mention This to the User — 在野恶意 skill 测量

| 项 | 内容 |
|----|------|
| **全名** | *“Do Not Mention This to the User”: Detecting and Understanding Malicious Agent Skills in the Wild* |
| **作者/出处** | Liu et al.；arXiv:2602.06547；USENIX Security 2026 等 |
| **链接** | https://arxiv.org/abs/2602.06547 · PDF: https://arxiv.org/pdf/2602.06547 |
| **佐证点 1** | 大规模扫描 registry 发现确认恶意 skill、多种攻击技术 → **真实世界会装/会传播** |
| **佐证点 2** | 原型含外泄类与决策劫持类 → 危害类型与我们 T2/外泄对齐 |
| **对应我们** | 问题现实意义；「安装会发生」的生态证据（多为生态/用户侧，非纯 agent 自主 benchmark） |

---

### P15 · Skills Are Not Islands — 依赖图

| 项 | 内容 |
|----|------|
| **全名** | *Skills Are Not Islands: Measuring Dependency and Risk in Agent Skill Supply Chains* |
| **作者/出处** | arXiv:2607.01136 |
| **链接** | https://arxiv.org/abs/2607.01136 · PDF: https://arxiv.org/pdf/2607.01136 |
| **佐证点 1** | skill 存在 **依赖关系**，风险可传递 |
| **佐证点 2** | 依赖信息常散落在文档/脚本中 → companion / 二重依赖攻击面真实 |
| **对应我们** | Stage2 I5 依赖诱导；供应链叙事 |

---

### P16 · Dynamic Malicious Skills — 运行时再注毒

| 项 | 内容 |
|----|------|
| **全名** | *Dynamic Malicious Skills in Agentic AI* |
| **作者/出处** | arXiv:2606.16287 |
| **链接** | https://arxiv.org/abs/2606.16287 · PDF: https://arxiv.org/pdf/2606.16287 |
| **佐证点 1** | skill 文档中的指令可诱导 agent 在运行时向 **原本良性** 的 skill 注入有害逻辑 |
| **佐证点 2** | 在 OpenHands / Claude Code 等有非平凡成功率 → 静态「看起来干净」不够 |
| **对应我们** | 渐进信任后下毒；旁路/运行时载荷 |

---

### P17 · HalluSquatting / Agentic Botnets — 幻觉名抢注

| 项 | 内容 |
|----|------|
| **全名** | *Beware of Agentic Botnets: Scalable Untargeted Promptware Attacks via Universal and Transferable Adversarial HalluSquatting*（以 arXiv 页名为准） |
| **作者/出处** | arXiv:2607.07433 |
| **链接** | https://arxiv.org/abs/2607.07433 · PDF: https://arxiv.org/pdf/2607.07433 |
| **佐证点 1** | Agent 会幻觉包名/skill 名并尝试获取；攻击者预注册这些名字可劫持安装路径 |
| **佐证点 2** | 文中 skill 安装相关幻觉率可极高 → S1 **名称先验** 路径，可与 CEM 并列 |
| **对应我们** | Stage1 方案 R2；不依赖 embedding 时的发现手段 |

---

### P18 · MCPSecBench — MCP 系统化基准

| 项 | 内容 |
|----|------|
| **全名** | *MCPSecBench: A Systematic Security Benchmark and Playground for Testing Model Context Protocols* |
| **作者/出处** | arXiv:2508.13220 |
| **链接** | https://arxiv.org/abs/2508.13220 · PDF: https://arxiv.org/pdf/2508.13220 |
| **佐证点 1** | 多攻击面、多平台；大量攻击至少攻破一个 provider |
| **佐证点 2** | MCP 安全是系统层问题 → related work 生态真实性 |
| **对应我们** | 背景与 taxonomy 引用 |

---

### P19 · LASM 综述 — 分层攻击面

| 项 | 内容 |
|----|------|
| **全名** | *A Systematic Survey of Security Threats and Defenses in LLM-Based AI Agents: A Layered Attack Surface Framework* |
| **作者/出处** | arXiv:2604.23338 |
| **链接** | https://arxiv.org/abs/2604.23338 · PDF: https://arxiv.org/pdf/2604.23338 |
| **佐证点 1** | Layered Attack Surface：含 Tool Execution、Ecosystem 等层 |
| **佐证点 2** | 便于把我们的问题标到 **Ecosystem（skill 供应链）+ Tool Execution** |
| **对应我们** | 开题/背景一页图 |

---

### P20 · 早期 IPI 奠基（可选引用）

| 项 | 内容 |
|----|------|
| **全名** | *Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection* |
| **作者/出处** | Greshake et al.；arXiv:2302.12173；AISec |
| **链接** | https://arxiv.org/abs/2302.12173 · PDF: https://arxiv.org/pdf/2302.12173 |
| **佐证点** | 间接提示注入经典工作；工具/外部内容不可默认信任 |
| **对应我们** | 背景引用；AgentDojo/InjecAgent 的前序 |

---

### P21 · Anthropic Agent Skills 工程文（非论文，机制）

| 项 | 内容 |
|----|------|
| **全名** | *Equipping agents for the real world with agent skills* |
| **链接** | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| **佐证点** | 工业界定义 skill 为可安装扩展；SKILL.md 成为操作规程 |
| **对应我们** | 威胁模型「自主扩展能力」的产品侧动机 |

---

### P22 · 索引仓库

| 项 | 内容 |
|----|------|
| **全名** | Awesome Agent Skills Security |
| **链接** | https://github.com/LLMSecurity/awesome-agent-skills-security |
| **佐证点** | 持续更新的 attacks/defenses/benchmarks 入口 |
| **对应我们** | 补文献、找 follow-up |

---

## 2. 按我们四阶段：文献 → 佐证点一览

| 阶段 | 文献 | 明确佐证 |
|------|------|----------|
| **S0 缺口** | P12 MSB (false-error) | 错误信息可改变后续规划 |
| | P9 AgentDojo | 工具返回可劫持后续动作 |
| | 我们 A2 | 缺口任务下会触发 search |
| **S1 检索** | P1 IPI | Vanilla≈0 / 优化后近满分 |
| | P5 ToolHijacker | 检索进不去则整体 ASR 低；优化后极高 |
| | P8 Discovery | 短 trigger 约 86% win / Top-10 80% |
| | P7 How Many Tools | top-k 可见集合合理 |
| | P17 HalluSquatting | 名称先验抢注路径 |
| **S2 安装** | P8 自述 gap | registry lifecycle 实验不足 |
| | P2 开篇 vs 实验 | 提 install，但不测 install 率 |
| | P11 README | 文档权威 ~85% 服从 |
| | P12 false-error / preference | 安装诱导菜单 |
| | P13 SCR TrustLift | 信任转移促装 |
| | P14 在野 | 恶意 skill 真实被装/传播 |
| | **我们 A2** | 搜到 ≠ 会装（实验） |
| **S3a 调用** | P6 ToolTweak | 同类 20%→81% |
| | P8 Selection | 功能等价 77.6% |
| | P5 ToolHijacker | 库内选中高 ASR |
| | P4 MCPTox | description 投毒 |
| | **我们 0–10%** | 跨域专一竞争下的 barrier（自有） |
| **S3b 载荷** | P2 Skill-Inject | post-load ~80% |
| | P3 Poise | 旁路+task_ok ~89% |
| | P16 Dynamic | 运行时再注毒 |

---

## 3. 汇报时「一句话 + 链接」卡片（可直接念）

1. **IPI (2601.07072)**  
   https://arxiv.org/abs/2601.07072  
   → 「不优化则检索失败；barrier 在中间步。」

2. **Skill-Inject (2602.20156)**  
   https://arxiv.org/abs/2602.20156  
   → 「装载后 ASR 可到约 80%，但默认已加载。」

3. **Poise (2606.07943)**  
   https://arxiv.org/abs/2606.07943  
   → 「装后单行+旁路约 89%，且任务仍成功。」

4. **Under the Hood of SKILL.md (2605.11418)**  
   https://arxiv.org/abs/2605.11418  
   → 「文献承认 post-load 偏多；Discovery/Selection 文本可操纵（~86%/77%）；缺单独 install 门。」

5. **ToolHijacker (2504.19793)**  
   https://arxiv.org/abs/2504.19793  
   → 「工具=检索+选择；文档优化后劫持率极高。」

6. **ToolTweak (2510.02554)**  
   https://arxiv.org/abs/2510.02554  
   → 「同类工具间改 name/desc 可选中率提到约 81%。」

7. **MSB (2510.15994)**  
   https://arxiv.org/abs/2510.15994  
   → 「false-error 等 taxonomy 直接指导安装诱导实验。」

8. **You Told Me to Do It (2603.11862)**  
   https://arxiv.org/abs/2603.11862  
   → 「文档/安装说明权威通道，服从可约 85%。」

9. **SCR (2606.15242)**  
   https://arxiv.org/abs/2606.15242  
   → 「组合与信任转移可显著抬高有害安装/危害。」

10. **MCPTox (2508.14925)**  
    https://arxiv.org/abs/2508.14925  
    → 「真实 MCP 上 description 投毒有效。」

---

## 4. 差异化金句（挂文献）

> **2605.11418** 证明：registry 上仅靠 SKILL.md 文本即可操纵 **Discovery（~86%）与 Selection（~77%）**。  
> **Skill-Inject / Poise** 证明：skill **进入上下文之后** 执行面 ASR 可到 **~80–90%**。  
> 我们在 agent 运行时进一步量化：**从「检索命中」到「install 进工具列表」** 是否仍存在独立瓶颈，以及在 **跨域专一工具竞争** 下预装 selection 是否接近失败（我们测得 0–10%）——  
> 这是 registry 论文与 post-load 评测都 **未单独乘积报告** 的环节。

---

## 5. 批量下载（可选）

```bash
mkdir -p /tmp/skill-acq-papers && cd /tmp/skill-acq-papers
for id in 2601.07072 2602.20156 2606.07943 2508.14925 2504.19793 \
          2510.02554 2605.24660 2605.11418 2406.13352 2403.02691 \
          2603.11862 2510.15994 2606.15242 2602.06547 2607.01136 \
          2606.16287 2607.07433 2508.13220 2604.23338 2302.12173
do
  wget -q -O "${id}.pdf" "https://arxiv.org/pdf/${id}" && echo "ok $id" || echo "fail $id"
done
```

---

*数字以各论文原文为准；「约 xx%」用于汇报量级，写论文时请回 PDF 表格精确引用。*
