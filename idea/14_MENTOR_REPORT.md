# 导师汇报稿：研究问题与文献佐证的理论框架

> ⚠️ **历史快照（2026-07-15）**：HalluSquatting、SearchGEO 等新文与 A2 编排复核已改变 install 口径。当前导师汇报请使用 `17_RELATED_WORK_VISUAL_REVIEW.md`；本文件保留早期论证过程。

> **用途**：口头汇报 + 一页纸提纲  
> **日期**：2026-07-15  
> **状态**：selection barrier 已有实验；acquisition 管线已搭建；Install 为当前主空白与下一步  
> **配套**：`11_MENTOR_ONEPAGER.md`（对照表）、`12_PAPER_VALIDATION.md`（逐阶段验收）、`09_ACQUISITION_PIPELINE.md`（实验矩阵）

---

## 一、30 秒版本（开场）

Skill / MCP 让 agent 能像装软件一样扩展能力，供应链风险已被多篇工作证实。  
但现有高 ASR 工作（Skill-Inject、Poise 等）多数默认 **skill 已经加载进上下文**，测的是「装完会不会听话」。  

我们从 IPI 的 **retrieval barrier** 迁移，先验证 **skill selection barrier**（预装时跨工具竞争下几乎选不中恶意 skill），再把问题扩成完整 **acquisition 链**：缺口 → 检索 → 安装 → 调用与载荷。  

文献对 Discovery / 装后执行支撑很强；**agent 自主 install** 仍是最虚的一环。我们的 A2 冒烟也显示：**会搜、能搜到、但不装**。  
因此主贡献定位为：**量化并突破 Skill Acquisition Barrier（尤其安装门）**，而不是再做一个 post-load 高 ASR。

---

## 二、研究问题（建议这样表述）

### 2.1 核心问题（RQ）

> 在具备 **自主发现与安装 skill** 能力的 LLM agent 中，  
> 恶意 skill **从市场进入工具列表、再被调用并产生危害** 的真实瓶颈在哪里？  
> 各阶段（缺口 / 检索 / 安装 / 调用+执行）的成功率如何分解？  
> 哪些机制性诱导（而非仅改一段 description）能抬高端到端风险？

### 2.2 子问题

| 编号 | 问题 | 我们已有/计划 |
|------|------|----------------|
| RQ1 | 恶意 skill **预装**时，在多良性专一工具竞争下是否会被选中？ | 实验：0% / 10% / 5% |
| RQ2 | 有能力缺口时，agent 是否会 **search**，恶意卡片是否进 top-k？ | A2 冒烟：会搜且能搜到 |
| RQ3 | 搜到后是否会 **install**？何种通道最有效？ | 冒烟：不装；待 I1/I2/I3 对照 |
| RQ4 | 装入后，专一伪装是否利用「专一性偏好」提高调用率？载荷如何隐蔽？ | 设计对齐 ToolTweak/Poise；待 70B 英文主表 |

### 2.3 明确不声称什么（避免和导师/审稿人纠缠）

| 不说 | 原因 |
|------|------|
| 「我们比 Skill-Inject 的 80% 更难攻/更安全」 | **不是同一阶段**的 ASR |
| 「description 优化永远无效」 | ToolTweak/ToolHijacker 在 **同类候选集** 内很有效 |
| 「所有 agent 都不会装恶意 skill」 | 目前 mock + 小样本 + 单框架 |

---

## 三、问题从哪来（思考链，1 分钟）

```
IPI：前人默认毒文档会被检索到 → 实测 Vanilla≈0 → retrieval barrier
        ↓ 结构迁移
Skill：前人/评测默认恶意 skill 会被调用/已加载 → 我们问：会不会被选中？
        ↓ 实验
预装 + 跨域专一竞争：0%–10%；明确 query 从不破
        ↓ 对照文献
Skill-Inject ~80% = post-load 执行；ToolHijacker = 库内检索+选择
        ↓ 问题升级
端到端 = acquisition（进列表）+ execution（装后执行）
主空白 = 安装决策（S2）
```

**和 IPI 的同构（理论锚点）：**

| IPI（检索注入） | 我们的 skill 设定 |
|-----------------|-------------------|
| 毒文档埋进语料库 | 恶意 skill 上架市场 |
| **能否被检索到** | **能否被发现并安装** |
| 进上下文后执行 | 进工具列表后调用与执行 |
| Vanilla≈0 / CEM≈100% | 预装 selection 0–10%；Discovery 文献可很高 |

---

## 四、理论框架：四阶段攻击链（汇报主图）

```
用户任务
   │
   ▼
[S0 能力缺口]  现有工具做不完 → 产生扩展意图
   │
   ▼
[S1 发现/检索]  search 市场 → 恶意卡片进 top-k
   │
   ▼
[S2 安装决策]  install → 进入工具列表     ★ 文献薄弱 + 我们的主切口
   │
   ▼
[S3 调用+载荷]  当专一工具被选中 → 规程/旁路执行 → 任务仍可成功
```

端到端：

\[
P(\mathrm{E2E}) = P(\mathrm{gap}) \times P(\mathrm{retrieve}) \times P(\mathrm{install}) \times P(\mathrm{invoke \land payload \land task\_ok})
\]

**方法原则**：一段一指标、一次主要改一个旋钮（避免把 selection 和 install 糊成一个 ASR）。

---

## 五、被文献佐证的理论部分（按阶段）

### 5.1 为何「装完之后」危险——已充分佐证 ✅

| 文献 | 结论 | 支撑我们什么 |
|------|------|----------------|
| **Skill-Inject** (arXiv:2602.20156) | skill 文件注入，最高约 **80% ASR** | Stage3：加载后执行面真实且严重 |
| **Poise** (arXiv:2606.07943) | 单行 body + 旁路脚本，约 **89% ASR**，任务仍完成 | Stage3：隐蔽载荷 + task_ok 指标设计 |
| **MCPTox** (arXiv:2508.14925) | tool metadata/description 投毒，真实 MCP，部分模型高 ASR | 描述可投毒；强 instruction-following 可能更脆 |
| **Dynamic Malicious Skills** 等 | 文档可诱导运行时再注入 | 装后动态下毒、旁路叙事 |

**理论命题 T1**：  
> 一旦恶意 skill 进入 agent 信任上下文，**post-load 执行**在现有 agent 协议下高度脆弱。  
> 因此端到端风险上界很大程度取决于 **能否完成 acquisition**。

---

### 5.2 为何「进上下文之前」存在 barrier——已充分佐证 ✅

| 文献 | 结论 | 支撑我们什么 |
|------|------|----------------|
| **IPI in the Wild** (arXiv:2601.07072) | Vanilla 检索≈0；优化后 Recall 近 100% | **Barrier 叙事模板**；不优化则进不了关键步骤 |
| **ToolHijacker** (arXiv:2504.19793) | 工具库 = retrieval + selection；手动注入仅中低 ASR，优化后极高 | 「先检索再选择」是标准分解；我们的 marketplace 不是玩具 |
| **How Many Tools…** (arXiv:2605.24660) | 工具过多时需限制可见集合 | 支持 search → top-k 再决策的架构合理性 |
| **2605.11418 Semantic Supply-chain** | 明确指出：已有工作偏 **loaded 之后**；registry 生命周期 underexplored | **几乎直接背书我们的问题切分** |
| 同上 Discovery | 短 trigger 操纵检索：胜率约 **86%**，Top-10 约 **80%** | S1 可攻击、可发表；CEM/trigger 是增强项 |

**理论命题 T2**：  
> Agent skill/tool 供应链存在 **pre-execution lifecycle**（发现、排序、准入）；  
> 前人高 ASR 常 **条件化在「已进入候选/已加载」** 上，端到端风险被高估或未分解。

---

### 5.3 为何「装入后改描述抢选中」在正确设定下可行——已佐证 ✅  
（同时解释我们 5% 并不矛盾）

| 文献 | 设定 | 结果 |
|------|------|------|
| 2605.11418 Selection | **功能等价** 二选一，改 description | 对抗版约 **77.6%** |
| **ToolTweak** (arXiv:2510.02554) | **同类** 工具间优化 name/description | 约 **20% → 81%** |
| **ToolHijacker** | 库内文档优化后检索+选择 | 常 **80%–100%** |
| **我们的实验** | **跨域** weather/calc… 与「全能」恶意 skill | **0%–10%** |

**理论命题 T3（专一性偏好 / 竞争结构）**：  
> LLM tool selection 对 **明确单域任务** 有强烈的 **专一工具偏好**；  
> 在 **跨域、已有正确答案工具** 时，通用/广告式 description 很难赢。  
> 文献高 selection ASR 多发生在 **同类候选集 / 功能等价对比** 中。  

**攻击含义（设计原则）**：  
- 装前：不必与 weather 抢「北京天气」；  
- 装后：把自己变成 **该类缺口任务的专一工具** → 进入文献已验证的有效区；  
- 因此需要 **分阶段换皮**（检索文案 / 安装话术 / 装入后 tool description / 载荷位置分离）。

---

### 5.4 安装门（S2）——生态成立、实验最虚 ⚠️ → 我们的主贡献区

| 文献/现象 | 支持 | 不足 |
|-----------|------|------|
| Skill-Inject 等开篇 | skill **像装包一样安装** 是真实使用模型 | 实验 **不测** install 率 |
| 真实 registry / ClawHub 等报告 | 恶意 skill **确实被分发、安装** | 多为用户侧，不全是 agent 自主 |
| **MSB** false-error / preference | 错误升级、偏好操纵可改后续行为 | 需我们落到 install 指标 |
| **You Told Me to Do It** (arXiv:2603.11862) | README 等文档诱导，服从可至约 **85%** | 是「跟文档执行」，近权威通道 |
| **SCR** 信任转移 | 组合/背书后有害安装可很高 | 是 composition 路径 |
| **我们的 A2** | gap✓ retrieved✓ **install✗** | 说明 install 是独立决策门 |

**理论命题 T4**：  
> **搜到 ≠ 会安装**；安装是 agent 的独立决策，需要 **必要性 / 权威通道 / 信任转移** 等信号，  
> 而不仅是 marketplace 广告文案。该门在文献中 **缺少分段 benchmark**，适合作为主贡献。

**Stage2 诱导菜单（文献映射，待实验选型）**：

| 策略 | 文献锚点 |
|------|----------|
| 广告式卡片 | 弱 baseline |
| 必要性 framing | 任务阻塞叙事 |
| 工具假错误 `NEED_SKILL` | MSB False-Error；AgentDojo 工具返回劫持 |
| 文档/规程要求安装 | README 诱导类工作 |
| 二重依赖 / companion | Skills Are Not Islands；SCR composition |

---

### 5.5 检索可优化——已佐证，但不是当前第一优先级 ✅

| 文献 | 含义 |
|------|------|
| IPI + CEM | embedding 检索可用黑盒优化打到近满分 |
| 2605.11418 Discovery | 短 trigger 即可大幅抬 registry 排名 |
| HalluSquatting 类工作 | 也可走「占模型会喊的名字」 |

**理论命题 T5**：S1 在方法上 **已被打穿过**；我们 mock 上「关键词就能搜到」合理。  
**工程优先级**：当前断在 S2 时，**先做安装对照，不上 CEM**。

---

## 六、我们自己的证据（如实汇报）

### 6.1 已完成：Selection barrier（预装设定）

| 设定 | 结果 |
|------|------|
| 6 良性 skill + 1 恶意预装；20 自然 query；deepseek-chat；hello-agents | |
| Vanilla（朴素云备份描述） | **0%** 被选中 |
| Query+（全能蹭热度） | **10%**（仅模糊/跨域） |
| LLM 对抗改描述 5 轮 | **5%** |
| 明确单域 query（天气/计算等） | **从未**被恶意 skill 抢走 |

**结论**：在 **跨域专一竞争** 下，不优化或仅通用描述优化 → **selection barrier 成立**。

### 6.2 已完成：Acquisition 最小闭环（工程 + 冒烟）

| 组件 | 状态 |
|------|------|
| marketplace + `search_skills` / `install_skill` | 已实现 |
| 8 分指标（gap / retrieved / install / invoke / payload / task_ok / E2E） | 已实现 |
| A0：明确 query + 预装 | 调 weather，不调恶意（锚点一致） |
| A2：缺口周报 + 市场 | **会搜、搜到、不装**（断在 Stage2） |

**样本说明**：A2 全量与安装策略 ablation **尚未完成**；冒烟用于定位断点，不作最终 ASR。

### 6.3 进行中

- 本地 **L40 + Llama-3.3-70B AWQ** 替换卡顿 API，英文主表  
- Stage2：广告 / 必要性 / `NEED_SKILL` 对照  
- 与 Skill-Inject 的 threat model 差异写进论文 related work

---

## 七、贡献表述（建议口径）

1. **现象贡献**：在多工具 agent 上证实 **skill selection barrier**（跨域专一竞争下 0%–10% 量级），并指出与 Skill-Inject 类 **post-load 高 ASR 不可横比**。  
2. **问题贡献**：提出并操作化 **Skill Acquisition Barrier** 四阶段分解与分指标，对齐 IPI 的 barrier 叙事与 2605.11418 的 registry lifecycle gap。  
3. **实证贡献（进行中）**：展示有缺口时 **检索可过、安装独立失败**；系统对比安装诱导通道。  
4. **设计原则**：分阶段换皮 + 装后专一化 +（规划中）Poise 式隐蔽载荷，把攻击从「硬刚明确 query 的 selection」转为「补能力路径上的 acquisition」。

---

## 八、请导师拍板的三件事

1. **主贡献是否定为**：「Skill Acquisition Barrier（尤其 Install）」——而不是再追 post-load 80% ASR？  
2. **下一步优先**：Stage2 安装诱导对照（约 1 周级实验），还是先跨框架 / 换模型扩表？  
3. **威胁模型**：强调「具备 **自主 search+install** 的 agent」（受控 mock 模拟 marketplace）是否可接受为论文设定？

---

## 九、口头汇报结构建议（8–10 分钟）

| 时间 | 内容 |
|------|------|
| 1 min | 30 秒版本 + 为何不是再做 Skill-Inject |
| 2 min | 完整链 vs 文献切在哪（画四阶段图） |
| 2 min | IPI 迁移 + selection 三档数字 |
| 2 min | 文献佐证表：S1/S3 强、S2 虚；2605.11418 一句话 |
| 2 min | A2 断在 install；下一步安装对照 + 70B 英文 |
| 1 min | 请导师拍板三点 |

---

## 十、关键引用速查（汇报备用）

| 简称 | 标识 | 一句话 |
|------|------|--------|
| IPI | arXiv:2601.07072 | retrieval barrier + CEM |
| Skill-Inject | arXiv:2602.20156 | 已加载 skill 注入，~80% ASR |
| Poise | arXiv:2606.07943 | 位姿感知 body 注入，~89% ASR |
| ToolHijacker | arXiv:2504.19793 | tool 库 retrieval+selection |
| ToolTweak | arXiv:2510.02554 | 迭代改 metadata，20%→81% |
| MCPTox | arXiv:2508.14925 | 真实 MCP tool poisoning |
| MSB | arXiv:2510.15994 | 含 false-error 等 taxonomy |
| Semantic Supply-chain | arXiv:2605.11418 | registry Discovery/Selection；指出 post-load 偏见 |
| README 诱导 | arXiv:2603.11862 | 文档权威通道 ~85% |

---

*本文由 idea/01–13 与实验记录综合整理，供导师讨论；数字以原始 JSON / 实验文档为准。*
