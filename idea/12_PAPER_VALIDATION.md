# 12 — 论文验证：你的攻击管线是否站得住

> **目的**：用 2025–2026 文献证据，**逐阶段验证** acquisition 攻击是否有道理、哪里已被证实、哪里仍是你的空白/风险。  
> **日期**：2026-07-15  
> **总判**：**站得住**。最强外部验证来自 arXiv:2605.11418（Discovery→Selection→Governance）；你的差异化在 **Install 决策门** 与 **跨域专一竞争**。

---

## 0. 总览：文献 vs 你的四阶段

```
你的管线          文献是否验证攻击可行性        代表工作 / 证据
────────────────────────────────────────────────────────────
S0 缺口           部分（任务/错误驱动扩展）     MSB false-error; 真实市场「缺能力就装」
S1 发现/检索      ✅ 强验证                    2605.11418 Discovery 86% win / 80% Top10
                                               ToolHijacker AHR~100%; IPI CEM
S2 安装决策       ⚠️ 部分                      真实生态有 install；实验少测「agent 自主装」
                                               README 诱导 85%（权威通道）
                                               SCR trust-transfer 促装 >83%
S3a 选中调用      ✅ 强验证（同类/候选集内）     2605.11418 Selection 77.6%
                                               ToolTweak 20%→81%; ToolHijacker 80%+
S3b 执行载荷      ✅ 强验证（已加载后）         Skill-Inject ~80%; Poise ~89%; script>正文
────────────────────────────────────────────────────────────
```

**读法**：你不是在发明不存在的攻击面；你是在把 **已被碎片验证的环节串成端到端**，并单独量化文献最虚的 **Install**。

---

## 1. 最强外部验证：Semantic Supply-chain（arXiv:2605.11418）

**论文**：*Under the Hood of SKILL.md: Semantic Supply-chain Attacks on AI Agent Skill Registry*  
Saha, Faghih, Feizi（Maryland）, 2026-05

### 他们明确说的 gap（几乎是在给你背书）

> Existing work primarily focuses on host-agent behavior **after a skill is loaded**…  
> The **registry-facing lifecycle remains underexplored**: how adversarial skills are admitted, ranked, surfaced, and selected **before execution**.

这与你的主张同构：Skill-Inject 等 = post-load；你 = pre-load lifecycle。

### 三阶段结果（直接可抄进 related work）

| 他们的阶段 | 攻击手段 | 结果 | 对应你的阶段 |
|------------|----------|------|--------------|
| **Discovery** | SKILL.md 附加短 trigger，操纵 embedding 检索 | 两两胜率 **86.14%**；Top-10 **80%**；ClawHub 风格排名平均日 **74%** 仍赢 | **S1** |
| **Selection** | 只改 description 一句话（虚假广告/祈使/信任声明等） | 功能等价的对抗变体被选中 **77.6%**（四模型） | **S3a**（装入/候选集内） |
| **Governance** | 语义改写躲扫描 | 躲过 blocking 判决 **36.5%–100%** | 你未做，可作未来工作 |

### 对你攻击的验证结论

| 你的设计 | 2605.11418 是否支持 |
|----------|---------------------|
| marketplace + search | ✅ Discovery 就是 registry 检索 |
| 优化 blurb/trigger（未来 CEM） | ✅ 短文本 trigger 即可大幅抬排名；不必一上来全 CEM |
| 装入后改 description 抢选中 | ✅ Selection 77.6%——但他们是 **功能等价二选一**，不是跨域专一工具 |
| SKILL.md 是操作文本而非说明书 | ✅ 全文结论 |
| 阶段可组合 | ✅ 文中写可 compose：过治理 → 上检索 → 被选中 |

### 他们没做、你在做的

- **没有**单独的「agent 调用 install_skill」指标（discovery 后默认进入候选，再 selection）  
- **没有**你的跨域 6 专一工具竞争设定  
→ 你的 **S2 安装门** 和 **跨域 selection barrier** 仍是可区分贡献

---

## 2. 分阶段验证详表

### S0 · 制造缺口 — 部分验证 ✅/⚠️

| 证据 | 含义 |
|------|------|
| MSB taxonomy：**False Error (FE)** | 工具返回错误可改 agent 后续规划 → 支持 I3 `NEED_SKILL` |
| MSB：**User Impersonation / Tool Transfer** | 响应通道可诱导下一步动作 |
| 真实生态（ClawHub / OpenClaw 报道） | 用户/agent 为补能力而发现安装 skill 已是常态 |
| 你的 A2 冒烟 | 缺口周报任务下 **会去 search** |

**验证结论**：缺口驱动扩展 **合理**；假错误是文献点名的攻击类，应优先做实验。

**未充分验证**：在 hello-agents 上「多大缺口才触发 search」的阈值——要靠 G1/G2/G3 消融。

---

### S1 · 发现/检索 — 强验证 ✅

| 证据 | 数字/结论 |
|------|-----------|
| **2605.11418 Discovery** | 86% win rate；Top-10 80%；真实排名函数下仍有效 |
| **ToolHijacker** | 恶意 tool doc 检索 AHR ~96–100%（优化后） |
| **IPI** | Vanilla 检索≈0，CEM ≈100% |
| 手动 injection baseline（ToolHijacker） | 仅 ~10–30% ASR——因 **检索都进不去** |

**验证结论**：

1. 「不优化则进不了 top-k」与 IPI/ToolHijacker **一致** → 你强调 barrier 有理  
2. 优化后检索 **可以很高** → 你 A2 用关键词就能 `retrieved=1` 合理；上 CEM/trigger 是增强项不是空想  
3. 你当前不必先做 CEM：文献显示 **短 trigger + embedding** 已够发表级 Discovery 故事

---

### S2 · 安装决策 — 部分验证 ⚠️（你的主空白）

| 证据 | 支持什么 | 不支持什么 |
|------|----------|------------|
| Skill-Inject 开篇 | install like packages，供应链真实 | **不测** install 成功率 |
| **You Told Me to Do It** (2603.11862) | README/安装文档诱导 → 外泄 **~85%**；人眼 0% 检出 | 是「跟文档执行」，不是 marketplace 点安装 |
| **SCR** TrustLift | 信任转移后 **有害安装率 >83%**（文中） | 是 composition 路径，不是单次 search→install |
| 真实市场恶意 skill 规模 | ClawHavoc 等数百恶意 skill **确实被装/分发** | 多为用户安装，非严格 agent 自主 |
| 你的 A2 | **搜到但不装** | 说明 install 门真实存在 |

**验证结论**：

- 「安装是关键一步」——**生态上成立**  
- 「agent 自主 install 可被诱导」——**有旁证（文档权威、信任转移），缺直接 benchmark**  
- 你把 install **单列指标** —— **正确且有发表空间**

**对你攻击的修正**：  
S2 不要只押「必要性卡片文案」；文献更支持：

1. **工具假错误 / 依赖缺失**（MSB FE）  
2. **文档/规程权威**（README 类 85%）  
3. **信任转移**（SCR：先良性背书再促装）  

这三者应作为 Stage2 ablation 主菜单。

---

### S3a · 装入后选中 — 强验证（在正确设定下）✅

| 证据 | 设定 | 结果 |
|------|------|------|
| 2605.11418 Selection | **功能等价** 原版 vs 对抗 description | **77.6%** 选对抗版 |
| ToolTweak | **同类** 多天气工具 | 20%→**81%** |
| ToolHijacker | 库内 + 检索后 LLM 选 | **80%+** |
| MCPTox | tool metadata 投毒 | 部分模型高 ASR；强模型有时更脆 |
| **你的预装实验** | **跨域** 专一工具 + 全能恶意 | **0–10%** |

**验证结论（关键）**：

- 文献 **验证的是「候选集内 / 同类竞争」下 description 可操纵**  
- 你的 5% **不反驳**文献，说明的是另一设定：**跨域专一偏好极强**  
- 攻击正确姿势（文献+你的发现）：  
  - 装前：不必赢 weather  
  - 装后：变成 **该类任务唯一/最专一** 工具 → 进入文献有效区  

**分阶段换皮** 被这条证据 **直接支持**。

---

### S3b · 载荷执行 — 强验证 ✅

| 证据 | 结论 |
|------|------|
| Skill-Inject | post-load ASR 高；**script > 正文**（+9～18pp） |
| Poise | 单行 setup + 旁路脚本，ASR ~89%，任务仍完成 |
| Dynamic Malicious Skills (2606.16287) | 文档诱导 **运行时** 往良性 skill 里注毒，OpenHands/Claude Code 非平凡成功率 |
| 真实 ClawHub 恶意 | 外泄/stealer 等已在野 |

**验证结论**：你 Stage3 用 handler/旁路外泄 + 周报仍成功，与 Skill-Inject/Poise **同构**；不必再证明「装完后能不能打」，应 **引用** 并聚焦前端 acquisition。

---

### 渐进信任 / 二重依赖 — 验证 ✅

| 证据 | 结论 |
|------|------|
| **SCR** (2606.15242) | 隔离评测近似安全，组合路径 ASR 33%～96%+；**TrustLift 促装** 很强 |
| **Skills Are Not Islands** (2607.01136) | skill 是 **依赖图**，非孤岛；依赖隐式散落在文档/脚本 |
| Dynamic Malicious Skills | 静态扫描可过 → 运行时再变毒 |

**验证结论**：你的「先装干净 A → companion B / 旁路下毒」**不是拍脑袋**，是 2026 供应链主线叙事之一。

---

## 3. 你的攻击「哪些点被证实 / 哪些要改」

### ✅ 已被文献证实、应坚持

1. **Pre-load lifecycle 值得做**（2605.11418 自己写 gap）  
2. **检索可优化到很高**（Discovery / ToolHijacker / IPI）  
3. **候选集内 description 可操纵**（Selection 77.6%、ToolTweak）  
4. **装后执行危险**（Skill-Inject / Poise）  
5. **权威通道 > 广告**（README 85%；MSB FE；SCR 信任转移）  
6. **组合/依赖攻击**（SCR、Skills Are Not Islands）  
7. **分段指标** 合理（2605.11418 也分阶段报告）

### ⚠️ 文献要求你修正的表述

| 旧说法（易被打） | 修正后 |
|------------------|--------|
| description 优化没用 | **跨域专一竞争下** 全能描述没用；**同类/功能等价候选** 下很有用 |
| 我们比 Skill-Inject 难 | 我们测的是 **他们默认跳过的前半程** |
| 安装必然很难 | 生态上 skill **会被装**；难的是 **agent 自主 install 决策**，需单独测 |
| 只靠必要性卡片就能装 | 应并列测 **FE / 文档 / TrustLift** |

### 🔬 仍主要靠你自己实验的

| 点 | 为何文献不够 |
|----|----------------|
| hello-agents 上 `install_skill` 诱导率 | 无同 harness 公开数字 |
| 缺口 query 分布 vs gap_triggered | 需你矩阵 A/B |
| 跨域专一偏好是否跨模型 | 需 ≥2 后端 |
| E2E：Discovery×Install×Invoke×Payload | 无人完整报乘积 |

---

## 4. 攻击可行性评分（基于本轮精读）

| 阶段 | 可行性 | 文献信心 | 你 lab 进度 | 建议 |
|------|--------|----------|-------------|------|
| S0 缺口 | 高 | 中 | A2 已触发 search | 加 FE |
| S1 检索 | **很高** | **高** | 关键词已够 | 可选 trigger/CEM 增强 |
| S2 安装 | **中–高**（方法选对才高） | 中（旁证多、直测少） | **当前断点** | **主实验** |
| S3a 调用 | 装后专一则高 | 高 | weekly_brief 已专一 | 装通后复测 |
| S3b 载荷 | 高 | 高 | handler 外泄已通 | 引用 Poise/SI |
| 渐进/依赖 | 高 | 高 | 未做 | Stage2 通后再做 |

**端到端攻击**：**可行**，条件是 S2 用对通道；不是「改 description 硬抢明确 query」。

---

## 5. 与 2605.11418 的「差异化一句话」（汇报用）

> 2605.11418 证明：registry 上 **Discovery 与 Selection 仅靠 SKILL.md 文本就可被操纵**（86% / 77%）。  
> 我们进一步在 **agent 运行时** 量化：从「搜到候选」到「真正 install 进工具列表」之间是否还有 **Install barrier**，以及跨域专一工具竞争下的 selection 行为——这是 registry 论文与 Skill-Inject post-load 评测都未单独报告的乘积环节。

---

## 6. 建议阅读优先级（验证攻击用）

| 优先级 | 论文 | arXiv | 用途 |
|--------|------|-------|------|
| P0 | Semantic Supply-chain SKILL.md | **2605.11418** | 整条 pre-load 叙事 + Discovery/Selection 数字 |
| P0 | Skill-Inject | 2602.20156 | post-load；划清边界 |
| P0 | ToolHijacker | 2504.19793 | 检索+选择两段优化 |
| P1 | ToolTweak | 2510.02554 | 同类 selection 上限 |
| P1 | MSB | 2510.15994 | Stage2 攻击类型菜单 |
| P1 | You Told Me to Do It | 2603.11862 | 权威通道 85% |
| P1 | SCR | 2606.15242 | 渐进信任 / 促装 |
| P2 | Skills Are Not Islands | 2607.01136 | 依赖图 |
| P2 | Dynamic Malicious Skills | 2606.16287 | 运行时下毒 |
| P2 | Poise | 2606.07943 | Stage3b 形态 |

下载：

```bash
wget https://arxiv.org/pdf/2605.11418 -O /tmp/semantic_skill_registry.pdf
```

代码（他们开源意向）：github.com/ShoumikSaha/agent-skill-security

---

## 7. 最终裁决

| 问题 | 答案 |
|------|------|
| 你的攻击有没有道理？ | **有。** 生命周期分解与 2605.11418 对齐，post-load 危险与 Skill-Inject 对齐。 |
| 最硬的外部证据？ | Discovery 86%、Selection 77.6%、post-load ~80%、README 85%。 |
| 你最该坚持的贡献？ | **Install barrier + 跨域 selection barrier + 分指标 E2E** |
| 你最该改的实现？ | Stage2 上 **FE / 文档 / TrustLift**，不要只卷全能 description |
| 能否继续做？ | **能。** 文献不是挡路，是在说：前半程值得做，且你卡的装门正是空白。 |

---

*关联：`11_MENTOR_ONEPAGER.md`（对外口径）、`09_ACQUISITION_PIPELINE.md`（实验矩阵）、`10_PAPERS_FOR_FEASIBILITY.md`（阅读清单）。*
