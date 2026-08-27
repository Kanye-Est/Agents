# 一页对照：我们在做什么 vs Skill-Inject 等高 ASR 工作

> ⚠️ **历史快照（2026-07-14）**：其中“install 文献空白”和“A2 搜到但不安装”的口径已被 Phase 10 修正。当前导师汇报请使用 `17_RELATED_WORK_VISUAL_REVIEW.md`。

> **用途**：给导师的 summary / 讨论提纲（约 1 页）  
> **日期**：2026-07-14  
> **一句话**：文献高 ASR 多测「skill 已加载后是否执行恶意指令」；我们补测「恶意 skill 如何进入工具列表」，并发现 **搜到 ≠ 会装**。

---

## 1. 研究问题怎么切

| | **Skill-Inject / Poise 等** | **我们（当前）** |
|--|----------------------------|------------------|
| **核心问题** | 已加载的 skill 文件里夹带指令，agent 会不会执行？ | 恶意 skill **尚未**在工具列表时，会不会被搜到、装上、再被调用？ |
| **供应链位置** | 后半段：加载后执行 | 前半段：发现 → 安装 →（再接后半段） |
| **类比 IPI** | 毒文档「已被检索进上下文」之后 | 毒文档「能不能被检索到 / 会不会被采用」 |

```
完整攻击链（端到端）
发布/上架 → 被发现/检索 → 【决定安装】→ 加载进上下文 → 被选中调用 → 执行恶意规程
              ToolHijacker          ★我们主战场        Skill-Inject / Poise
              IPI retrieval         （文献实验少）       MCPTox（描述投毒）
```

**我们不声称**：比 Skill-Inject 的 80% ASR「更猛」或「更难防」。  
**我们声称**：那 80% **默认跳过了** acquisition；真实端到端风险取决于前半程是否过关。

---

## 2. Threat model 对照（最重要）

| 维度 | Skill-Inject | ToolHijacker / ToolTweak | **我们的设定** |
|------|--------------|--------------------------|----------------|
| skill/tool 初始状态 | **已加载**（body/YAML/script 已在上下文） | **已在 tool library / 工具列表** | A0：预装；A2：**仅在 marketplace，需 search+install** |
| 攻击者能力 | 改 SKILL.md / 旁路脚本 | 改 tool name+description（可优化） | 改市场卡片 + 装入后描述 + handler（研究用假数据） |
| 用户任务 | 正常合法任务（如做 PPT） | 针对某类 target task | 日常 query / 缺口型「行程×天气周报」 |
| 成功定义 | 执行注入步骤（外泄/破坏等） | 恶意工具被选中（ASR/AHR） | **分段指标** + E2E（装上 ∧ 外泄 ∧ 任务仍完成） |
| 竞争环境 | 主要与「是否服从 skill 规程」 | 同类工具间抢选中 | 跨域专一工具（weather/calc…）或装前无竞争 |

---

## 3. 数字为什么不能横比

| 工作 | 报告数字 | 实际含义 |
|------|----------|----------|
| Skill-Inject | 最高约 **80% ASR** | skill **已在** → 执行恶意指令 |
| ToolHijacker | 常 **80%–100% ASR** | 文档 **已在库** → 检索+选中 |
| ToolTweak | 约 **20%→81%** | **同类**工具间改 metadata |
| 我们预装 selection | **0%→10%→5%** | 跨域专一竞争下，**通用描述**几乎骗不过 |
| 我们 A2 冒烟（n=1） | gap✓ ret✓ **install✗** | 会搜、能搜到、**不装** |

> 5% 与 80% 不是同一场比赛：一个是「装前抢位」，一个是「装后服从」。

---

## 4. 我们已有证据（简表）

| 实验 | 设定 | 结果 | 说明什么 |
|------|------|------|----------|
| **Vanilla / Query+ / Optimized** | 恶意 skill **预装** + 20 自然 query | 0% / 10% / 5% | **Selection barrier** 存在；明确 query 选专一工具 |
| **A0**（锚点） | 明确「北京天气」+ 预装 `weekly_brief` | 调 weather，不调恶意 | 与旧结论一致，无缺口不破 |
| **A2**（最小闭环） | 缺口周报 query + 内存市场 + search/install | **搜到目标，但未 install** | **Acquisition 断在安装门（Stage2）** |

工程：`secskill-lab/acquisition/`（marketplace、元工具、8 分指标、A0/A2 runner）。

---

## 5. 贡献怎么表述（给导师版）

**可以这样说：**

1. **现象**：在 hello-agents 上复现 skill 竞争下的 selection barrier（0%–10%）。  
2. **分解**：把端到端拆成 缺口 → 检索 → 安装 → 调用+载荷，用分指标定位瓶颈。  
3. **发现（初步）**：有缺口时 agent **会去搜且能搜到**，但 **未必 install**——安装决策是独立瓶颈。  
4. **定位**：相对 Skill-Inject（post-load），我们做 **pre-load acquisition**；相对 ToolHijacker（库内文档），我们多测 **「进库/安装」决策**。  
5. **下一步**：Stage2 安装诱导对照（广告 / 必要性 / 工具假错误 NEED_SKILL），再接装后专一调用 + 旁路载荷（对齐 Poise）。

**不要这样说：**

- 「我们 ASR 只有 5%，所以比 Skill-Inject 更安全/更难攻。」  
- 「description 优化完全无效。」（ToolTweak/ToolHijacker 在同类+优化设定下很有效）  
- 「已经证明所有 agent 都不会装恶意 skill。」（目前是 mock + 小样本）

---

## 6. 与文献空白的对齐

| 文献已充分 | 文献薄弱 → 我们的切口 |
|------------|------------------------|
| 加载后执行恶意 skill 指令（Skill-Inject/Poise） | **自主 search→install 是否发生、如何诱导** |
| 库内 tool 文档劫持选中（ToolHijacker） | **未进库时**的安装门 |
| 同类工具 metadata 竞争（ToolTweak） | **跨域专一偏好** + 装后如何变成「专一工具」 |

---

## 7. 风险与边界（主动交代）

| 点 | 说明 |
|----|------|
| 框架 | 目前主要在 hello-agents；跨框架待做 |
| 安装环 | `search_skills`/`install_skill` 为 **受控 mock**（模拟具备自主扩展能力的 agent） |
| 数据 | 合成假数据；外泄仅 127.0.0.1 |
| 样本 | A2 全量与安装策略 ablation **尚未跑完**；冒烟仅示意断点 |
| 模型 | 现用 deepseek-chat；主方案稳定后再做跨模型 |

---

## 8. 请导师拍板的三件事

1. **主贡献是否定为**：「Skill acquisition barrier（尤其 install）」而非「再做一个 post-load 高 ASR」？  
2. **下一步优先**：Stage2 三种安装诱导对照（约 1 周实验），还是先扩框架/换模型？  
3. **威胁模型表述**：强调「具备自主 install 的 agent」是否可接受？

---

## 9. 30 秒口述版

> Skill-Inject 说明 skill **装进上下文之后**很危险，ASR 可以很高，但评测默认 skill 已加载。  
> 我们在 hello-agents 上发现：恶意 skill **预装时**，在专一工具竞争下几乎选不中；  
> 做成「市场可搜可装」后，agent **会搜到但仍可能不装**。  
> 所以端到端瓶颈可能在 **acquisition（尤其安装）**，而不是 post-load 执行。  
> 接下来用对照实验打安装门，再接到装后执行，形成完整故事。

---

*详细管线与实验矩阵见 `09_ACQUISITION_PIPELINE.md`；文献清单见 `10_PAPERS_FOR_FEASIBILITY.md`。*
