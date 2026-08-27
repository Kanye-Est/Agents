# 文献包与推荐精读顺序

> 整理日期：2026-07-29  
> 对应当前研究主线：ordinary capability task → external discovery → real install/registration → invocation/payload  
> 论文目录：[`papers/`](papers/)  
> 精读笔记模板：[`READING_NOTES_TEMPLATE.md`](READING_NOTES_TEMPLATE.md)  
> 逐篇精读汇总：[`DEEP_READING_FORMS.md`](DEEP_READING_FORMS.md)  
> 完整性校验：[`SHA256SUMS`](SHA256SUMS)

## 1. 收集范围与结果

- 从 `idea/*.md`、`idea/*.tex` 和 `hello-agents-lab/literature.md` 中抽取并去重出 **51 个 arXiv 编号**。
- 原来散落在 `papers_phase8/`、`papers_phase9/`、`papers_phase10/`、`papers_mentor_sources/`
  的 43 篇 PDF 已复制到本目录；原文件保留，避免旧笔记中的路径失效。
- 补下了此前缺失的 8 篇 arXiv PDF，并下载了 1 篇 Springer 开放获取综述。
- 当前共有 **52 份 PDF，全部通过 `pdfinfo` 解析检查**。
- Elsevier 综述 `10.1016/j.inffus.2025.103941` 的官方页面目前要求机构访问或购买，
  因此没有从非授权来源下载；详见本文末尾“未获取全文”。

## 2. 不建议从 52 篇的第一篇开始顺读

当前已经进入写论文和补 generalization 的阶段，最重要的是先把：

1. 方法学祖先；
2. 最接近的 novelty 邻居；
3. 指标与实验设计依据；
4. 防御和边界；

读透。下面的 18 篇是推荐的**精读主线**；其余文献先按需查阅。

### 预热：只读指定章节

| 顺序 | 论文 | 读法 | 目的 |
|---:|---|---|---|
| 0A | [2602.12430 — Agent Skills for LLMs Survey](papers/2602.12430.pdf) | 先读 architecture、acquisition、security 三节 | 统一 skill、tool、registry、acquisition 术语 |
| 0B | [2604.23338 — LASM Survey](papers/2604.23338.pdf) | 只读 Tool Execution、Ecosystem、Governance 层 | 把当前问题放进 agent 系统安全大图，不必逐篇追它的 116 篇引用 |

### 第一轮：研究定位与 novelty 边界

| 顺序 | 论文 | 为什么现在最该读 | 精读时必须回答 |
|---:|---|---|---|
| 1 | [2601.07072 — Overcoming the Retrieval Barrier](papers/2601.07072.pdf) | 当前 acquisition funnel 与“第一跳 barrier”最直接的方法学祖先 | 它的起点、Recall@5、CEM、E2E 分别是什么；哪些设计可迁移，哪些不能声称原创 |
| 2 | [2602.06547 — Do Not Mention This to the User](papers/2602.06547.pdf) | 给“恶意 skill 供给真实存在”做生态背书 | 98,380→4,287→157 的每层筛选定义；静态候选、行为确认恶意、漏洞实例不能混用 |
| 3 | [2605.11418 — Semantic Supply-chain on SKILL.md](papers/2605.11418.pdf) | 最强 registry discovery/selection 邻居 | Discovery 与 Selection 的候选集、分母、成功定义；为什么 80% Top-10/77.6% selection 不能外推成真实安装率 |
| 4 | [2606.15242 — SCR](papers/2606.15242.pdf) | 已覆盖中性组合与 simulated harmful install，是最容易撞 novelty 的论文 | 分开读 CapFlow 和 TrustLift；“available skill composition”与“simulated market install”的真实 endpoint 各是什么 |
| 5 | [2607.07433 — HalluSquatting](papers/2607.07433.pdf) | 显式安装意图下真实 invocation/RCE，是现有 E2E 上界 | 用户在 S0 已经授权了什么；140 trials、slug 抢注、不同 E2E 口径如何算；与你的 ordinary-task 起点差在哪 |
| 6 | [2607.12340 — Skills That Don't Exist](papers/2607.12340.pdf) | 与“普通能力问题触发 skill 推荐”最近 | 15,000 prompts 的 hallucination endpoint、RAG 防御、单例 install PoC 是否在同一实验链 |
| 7 | [2606.16821 — SearchGEO](papers/2606.16821.pdf) | 覆盖搜索证据操纵到安装命令输出 | skill probe 的样本量为何只有 18；`recommend/emitted command` 与 `executed/on-disk` 的边界 |

读完第一轮后，应能不看旧笔记，自己写出一页对比表：

```text
论文起点 | 用户是否明确要求安装 | skill 是否预装 | discovery 是否真实
       | install 是文本/模拟/真实落盘 | 是否注册并调用 | payload | task utility
```

### 第二轮：指标、实验设计和危害上界

| 顺序 | 论文 | 为什么读 | 精读时必须回答 |
|---:|---|---|---|
| 8 | [2602.20156 — Skill-Inject](papers/2602.20156.pdf) | 装后 skill-file injection 的核心基线 | 202 injection-task pairs 如何构造；skill 已加载这一前提；ASR 与正常任务完成如何同时报告 |
| 9 | [2606.07943 — POISE](papers/2606.07943.pdf) | 支撑 payload 与 task utility 必须分开测 | position-aware 机制、stealth 定义、verifier 与 89.3%/97.3% 分别在什么条件下成立 |
| 10 | [2406.13352 — AgentDojo](papers/2406.13352.pdf) | 安全成功和 clean utility 联合评估的成熟模板 | 97 tasks、629 security cases 的层级；攻击目标、utility、defense utility trade-off 如何计分 |
| 11 | [2403.02691 — InjecAgent](papers/2403.02691.pdf) | tool-integrated IPI 的 benchmark 祖先 | 1,054 cases、user/attacker tools、direct harm/exfiltration 的构造与分母 |
| 12 | [2504.19793 — ToolHijacker](papers/2504.19793.pdf) | 把 retrieval、selection 与 downstream harm 串起来 | 它是否经过安装；各阶段的攻击优化对象；“最高约 80%”对应哪一段 |
| 13 | [2510.02554 — ToolTweak](papers/2510.02554.pdf) | metadata/name/description 优化的直接依据 | 20%→81.62% 的候选竞争结构；为何同类工具选择不能外推到跨域 acquisition |
| 14 | [2510.15994 — MCP Security Bench](papers/2510.15994.pdf) | 给 false-error、preference、impersonation、over-privilege 做 taxonomy 背书 | planning→invocation→response 三阶段；每类攻击假设工具已经处于什么可见/连接状态 |

### 第三轮：现实测量与防御边界

| 顺序 | 论文 | 为什么读 | 精读时必须回答 |
|---:|---|---|---|
| 15 | [2601.10338 — Agent Skills in the Wild](papers/2601.10338.pdf) | 核对经常被误引的 26.1% | 42,447/31,132/8,126 各是什么；26.1% 是静态 vulnerability 筛查，不是行为确认恶意率 |
| 16 | [2604.02837 — Towards Secure Agent Skills](papers/2604.02837.pdf) | 为 scaffold authorization、lifecycle 和 persistent trust 提供结构化语言 | Creation/Distribution/Deployment/Execution；single approval 为什么形成持久信任 |
| 17 | [2605.28914 — AIRGuard](papers/2605.28914.pdf) | 与执行层 authority gate 最接近 | gate 的策略输入、拦截位置、攻击/utility 指标；与你的 parsed-before-execute gate 有何差异 |
| 18 | [2607.02357 — Cloak and Detonate](papers/2607.02357.pdf) | 说明 approval/gating 不等于 vetting，静态 scanner 也不够 | 8 个 scanner 的绕过评测、runtime detonation 的 TPR/FPR、真实样本与 controlled benchmark 的区别 |

## 3. 每篇精读的统一产物

不要只记“论文说了什么”。每篇至少留下一页，固定回答：

1. **起点**：用户给了什么，攻击者控制什么，skill/tool 是否已经可见或加载；
2. **终点**：推荐、命令文本、模拟状态变化、真实执行、落盘、注册、调用、payload、task success 中测到了哪一步；
3. **分母**：task、trial、attack instance、tool、skill、model run 分别是多少，百分比除的是什么；
4. **对照**：baseline 和 intervention 只差哪个变量，有没有混入 prompt/scaffold/model 变化；
5. **可背书的句子**：能支持你论文中的哪一句；
6. **不能说的句子**：最容易从该论文过度外推什么；
7. **证据位置**：页码、表号、图号和原文短语，写论文时不再靠二手笔记。

建议直接复制 [`READING_NOTES_TEMPLATE.md`](READING_NOTES_TEMPLATE.md)，每篇生成一份笔记。

## 4. 完整文献索引

### A. 与 Acquisition Gap 最接近

| 文件 | 短名 / 主题 |
|---|---|
| [2601.07072](papers/2601.07072.pdf) | Overcoming the Retrieval Barrier；retrieval barrier、CEM、野外 IPI |
| [2602.06547](papers/2602.06547.pdf) | Do Not Mention；在野恶意 agent skills 的行为确认测量 |
| [2605.11418](papers/2605.11418.pdf) | Semantic Supply-chain；registry discovery/selection/governance |
| [2606.15242](papers/2606.15242.pdf) | SCR；skill composition 与 TrustLift simulated install |
| [2606.16821](papers/2606.16821.pdf) | SearchGEO；搜索内容操纵、endorsement 与安装命令 |
| [2607.07433](papers/2607.07433.pdf) | HalluSquatting；显式安装意图下的真实 E2E/RCE |
| [2607.12340](papers/2607.12340.pdf) | Skills That Don't Exist；skill 名幻觉、推荐与 install PoC |

### B. Tool/Skill 选择、投毒与 benchmark

| 文件 | 短名 / 主题 |
|---|---|
| [2504.19793](papers/2504.19793.pdf) | ToolHijacker；tool retrieval/selection attack |
| [2505.11154](papers/2505.11154.pdf) | MPMA；MCP preference manipulation |
| [2508.13220](papers/2508.13220.pdf) | MCPSecBench；MCP 攻击 taxonomy/playground |
| [2508.14925](papers/2508.14925.pdf) | MCPTox；真实 MCP tool metadata poisoning |
| [2510.02554](papers/2510.02554.pdf) | ToolTweak；name/description 优化 |
| [2510.15994](papers/2510.15994.pdf) | MCP Security Bench；planning/invocation/response 攻击 |
| [2602.20156](papers/2602.20156.pdf) | Skill-Inject；loaded skill-file attack benchmark |
| [2603.11862](papers/2603.11862.pdf) | You Told Me to Do It；README/文档权威与隐私泄漏 |
| [2605.24660](papers/2605.24660.pdf) | How Many Tools；shortlist/top-k 与工具暴露规模 |
| [2606.07943](papers/2606.07943.pdf) | POISE；position-aware skill injection 与 task verifier |

### C. IPI 与 agent 风险评估基础

| 文件 | 短名 / 主题 |
|---|---|
| [2302.12173](papers/2302.12173.pdf) | Not What You've Signed Up For；真实 LLM 应用的 IPI 起点论文 |
| [2309.15817](papers/2309.15817.pdf) | ToolEmu；LM-emulated sandbox 与高风险工具评测 |
| [2312.14197](papers/2312.14197.pdf) | BIPIA；IPI benchmark 与 boundary-awareness defense |
| [2403.02691](papers/2403.02691.pdf) | InjecAgent；tool-integrated agents 的 IPI benchmark |
| [2406.13352](papers/2406.13352.pdf) | AgentDojo；动态安全/utility 联合评测 |
| [2607.00422](papers/2607.00422.pdf) | KidnapRAG；多跳 retrieval reasoning hijack |

### D. Skill 生态、架构与供应链测量

| 文件 | 短名 / 主题 |
|---|---|
| [2601.10338](papers/2601.10338.pdf) | Agent Skills in the Wild；SkillScan 大规模静态漏洞测量 |
| [2602.08004](papers/2602.08004.pdf) | Agent Skills: A Data-Driven Analysis；生态规模/类别/采用 |
| [2602.12430](papers/2602.12430.pdf) | Agent Skills for LLMs Survey；架构、acquisition、安全 |
| [2603.02176](papers/2603.02176.pdf) | AgentSkillOS；大规模 skill 检索、编排与 benchmark |
| [2603.11808](papers/2603.11808.pdf) | Automating Skill Acquisition；从开源仓库挖掘/生成技能 |
| [2603.16572](papers/2603.16572.pdf) | Context Matters；repository-aware skill 安全分析 |
| [2604.02837](papers/2604.02837.pdf) | Towards Secure Agent Skills；生命周期与 threat taxonomy |
| [2605.28588](papers/2605.28588.pdf) | Emerging Threats Technical Report；marketplace 风险测量 |
| [2607.00011](papers/2607.00011.pdf) | SkillSelect-Serve；skill registry 推荐/组合 |
| [2607.01136](papers/2607.01136.pdf) | Skills Are Not Islands；skill dependency/risk graph |

### E. 装后攻击、后门与组合危害

| 文件 | 短名 / 主题 |
|---|---|
| [2510.26328](papers/2510.26328.pdf) | Agent Skills Enable Trivial Prompt Injections |
| [2602.14211](papers/2602.14211.pdf) | SkillJect；自动生成恶意 skill |
| [2604.04989](papers/2604.04989.pdf) | SkillAttack；attack-path refinement red teaming |
| [2604.06811](papers/2604.06811.pdf) | SkillTrojan；skill-level backdoor |
| [2604.09378](papers/2604.09378.pdf) | BadSkill；model-in-skill poisoning |
| [2605.29354](papers/2605.29354.pdf) | Neutral Prompting；幻觉 package/pip command |
| [2606.16287](papers/2606.16287.pdf) | Dynamic Malicious Skills；运行时修改 benign skill |
| [2606.19191](papers/2606.19191.pdf) | PhantomSkill；bug-shaped malicious code |
| [2606.20023](papers/2606.20023.pdf) | Over-Privileged Tool Selection；agent 的权限偏好 |
| [2606.27027](papers/2606.27027.pdf) | ShareLock；多工具分片/threshold poisoning |
| [2607.02857](papers/2607.02857.pdf) | MOSAIC；CLI command composition attack |

### F. 防御与综述

| 文件 | 短名 / 主题 |
|---|---|
| [2602.22724](papers/2602.22724.pdf) | AgentSentry；temporal causal diagnostics/context purification |
| [2604.06550](papers/2604.06550.pdf) | SkillSieve；恶意 skill 分层筛查 |
| [2604.11790](papers/2604.11790.pdf) | ClawGuard；tool-call runtime boundary enforcement |
| [2604.23338](papers/2604.23338.pdf) | LASM Survey；LLM agent 分层攻击面 |
| [2605.28914](papers/2605.28914.pdf) | AIRGuard；runtime authority control |
| [2606.14154](papers/2606.14154.pdf) | SkillMutator；安装时扫描/变异防御 |
| [2607.02357](papers/2607.02357.pdf) | Cloak and Detonate；scanner evasion 与 runtime detonation |
| [Springer DOI 10.1007/s11416-026-00622-3](papers/doi_10.1007_s11416-026-00622-3.pdf) | 开放获取的 agent cyberattack/defense survey |

## 5. 未获取全文

**Security of LLM-based Agents Regarding Attacks, Defenses, and Applications: A Comprehensive Survey**

- DOI：<https://doi.org/10.1016/j.inffus.2025.103941>
- 出版页：<https://www.sciencedirect.com/science/article/abs/pii/S1566253525010036>
- 状态：官方页面显示需要机构访问或购买 PDF；截至 2026-07-29 未找到明确的作者开放版本。
- 建议：通过学校图书馆、机构 VPN 或向作者索取；拿到合法副本后放入 `papers/`，并更新校验文件。
