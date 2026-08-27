# 交接说明：给「专门阅读文献的智能体」

> **目的**：把此前会话中与 **文献阅读 / idea 定位 / 攻击管线** 相关的成果与未完成项，  
> 完整移交给专门负责读文献的 agent。  
> **交接日**：2026-07-16  
> **工作区**：`/home/forks/AResearch/Agent/hello-agents-lab/`

---

## 1. 你要接手的任务是什么

### 主任务（持续）

围绕科研 idea **Skill Acquisition Barrier**，继续：

1. **发现、精读、摘要** 新的相关论文  
2. **维护文献资产**（见第 3 节文件职责）  
3. **对照本 lab 实验设定**，判断新文是：支撑 / 对照 / 正交 / 已抢贡献  
4. **产出可直接用于组会/开题的叙述**，而不是堆 citation  

### 不是你的主任务（除非用户明确要求）

- 改 `secskill-lab` 实验代码、跑 A0/A2 全量  
- 实现 Stage2 攻击（假错误 / 安装诱导）  
- 本地 70B 部署（见 `10_LOCAL_BACKEND_PLAN.md`）  

实验与代码由工程/主 agent 负责；你负责 **文献闭环**。

---

## 2. 科研背景（必读，1 分钟）

### Idea（当前口径）

> 恶意 skill 在进入 agent 工具列表并被合理调用之前，存在可量化瓶颈（尤其 **install**）。  
> 文献高 ASR 多默认 skill **已加载 / 已在库**；我们测 **acquisition 前半程**。

### 四阶段管线

```
S0 缺口 → S1 检索/发现 → S2 安装 → S3 调用 + 载荷（+ task_ok）
```

### Lab 关键证据（已完成，勿与文献 80% 横比）

| 结果 | 含义 |
|------|------|
| 预装 selection 0% / 10% / 5% | 跨域专一竞争下 selection barrier |
| A2 冒烟：搜到 ✓、安装 ✗ | **Install barrier** 候选断点 |

### 贡献边界（写 related work 时必须遵守）

- **做**：分指标 acquisition；install 门；跨域 selection 现象  
- **不做主贡献**：再刷 post-load 80%+ ASR（Skill-Inject/Poise/SkillTrojan 区）  
- **不横比**：本 lab 5% vs Skill-Inject 80%（threat model 不同）

---

## 3. 已有文献资产（全部在 `idea/`）

### 必读交接文件（按优先级）

| 优先级 | 文件 | 给你的用途 |
|--------|------|------------|
| **1** | `15_LIT_ACADEMIC_BRIEF.md` | **学术汇报体综述**（组会口径，用户更满意这种） |
| **2** | `13_LIT_READING_JOURNEY.md` | 阅读过程 Phase 0–9；idea 如何演变 |
| **3** | `14_LIT_SUMMARY_TABLE.md` | 短表查 arXiv / 数字 |
| **4** | `12_PAPER_VALIDATION.md` | 攻击可行性验收 |
| **5** | `11_MENTOR_ONEPAGER.md` | 给导师一页 |
| **6** | `09_ACQUISITION_PIPELINE.md` | 四阶段作战图 + 实验矩阵 |
| **7** | `10_PAPERS_FOR_FEASIBILITY.md` | 较早可行性清单 |
| — | `00_README.md` | 全文件夹导读 |
| — | `01_ORIGIN.md` | IPI → selection 起源 |

### 本地 PDF

```
idea/papers_phase8/   # 11 篇
idea/papers_phase9/   # 7 篇
/home/forks/AResearch/ANL/2601.07072v1.pdf  # IPI
```

其余用 `https://arxiv.org/pdf/<id>`。

### 工程侧（只读了解，非你维护）

```
secskill-lab/acquisition/          # marketplace + search/install + A0/A2
secskill-lab/skills/research_malicious/weekly_brief/
secskill-lab/acquisition/results/acq_20260714_205411.json
```

---

## 4. 前任 agent 已完成的工作（文献相关）

### 4.1 精读与验收

- 对照 Skill-Inject / ToolHijacker / ToolTweak：澄清 5%≠80%  
- 验收 2605.11418 为 **pre-load 最强外部验证**  
- Phase 8：架构/在野/后门/检测/防御（约 11 篇）  
- Phase 9：MPMA / SkillAttack / SkillJect / KidnapRAG / AgentSkillOS 等  

### 4.2 产出的文档

- 过程文档 `13`（Phase 0–9）  
- 短表 `14`（用户嫌复杂后已简化）  
- **学术简报 `15`**（用户更认可的「汇报型」）  
- 导师一页 `11`、验收 `12`、管线 `09`  

### 4.3 已形成的文献三块地图（勿打乱）

1. **Post-load 执行** — 已充分（SI / Poise / Trojan…）  
2. **库内/同类选择** — 已充分（ToolHijacker / ToolTweak / MPMA…）  
3. **Pre-load / 安装** — 有旁证、**缺 agent 自主 install 分指标** ← idea 切口  

---

## 5. 你接手后应做的具体工作

### 持续例行

1. **扫新文**（关键词建议）  
   - agent skill marketplace / registry / supply chain  
   - skill install / acquisition / progressive disclosure  
   - tool selection preference / MCP poisoning  
   - skill injection / SKILL.md  

2. **每篇必填 checklist**（写入笔记）

```
论文:
默认 skill/tool 是否已在上下文?  [是/否/部分]
有没有 search / install 动作?    [有/无]
成功是否要求用户任务仍完成?      [是/否]
优化对象是什么?                 [desc/name/body/script/trigger]
可直接进 lab 实验的一点:        [...]
是否吃掉我们的空白?             [否/部分/是→说明]
```

3. **更新文件规则**  
   - 新精读 → 追加 `13` 的 **Phase 10+**（过程）  
   - 新条目 → 更新 `14` 短表（保持简单）  
   - 若改变 idea 定位 → 改 `15` 学术简报 + 通知用户  
   - PDF → `idea/papers_phaseN/`  

4. **输出风格（用户偏好）**  
   - 用户 **不满意** 过宽、字段过多的 md 大表  
   - 用户 **更要** 学术汇报型：分块叙述 + 定位图 + 空白 + 口述稿  
   - 默认以 `15` 的体例为准；`14` 只作查表  

### 优先待办（文献侧）

| ID | 任务 | 说明 |
|----|------|------|
| L1 | 专找 **agent 自主 install / skill marketplace install ASR** | 验证空白是否仍在 |
| L2 | 深挖 Stage2 通道原文例子 | MSB False Error 实例；You Told Me 注入位置；SCR TrustLift 设定细节 |
| L3 | MPMA GAPMA 四广告策略原文模板 | 供实验抄 description |
| L4 | 维护「最少引用集」 | 见 `15` 附录，有更好主引用则替换 |
| L5 | 若出现直接竞品 | 写 1 页 threat model 差异，更新 `15` §3–6 |

### 暂不优先

- 再堆 post-load 后门高 ASR 论文（除非用户要防御综述）  
- 与 SkillAttack 混谈（正交：不改 skill）  

---

## 6. 关键词与 arXiv 种子（续搜用）

```
seed (已精读，勿当新发现):
2601.07072 IPI | 2602.20156 Skill-Inject | 2504.19793 ToolHijacker
2510.02554 ToolTweak | 2605.11418 Semantic SC | 2602.12430 Skills Survey
2505.11154 MPMA | 2602.06547 Do Not Mention | 2606.07943 Poise
2606.15242 SCR | 2603.11862 You Told Me | 2510.15994 MSB

search queries:
"agent skill" install marketplace registry
"skill selection" OR "tool selection" preference MCP
"SKILL.md" supply chain OR poisoning
"acquisition" agent skills progressive disclosure
false-error tool agent install dependency
```

索引：https://github.com/LLMSecurity/awesome-agent-skills-security

---

## 7. 给文献 agent 的系统提示（可复制）

```
你是本项目的文献智能体。工作区：hello-agents-lab/idea/。

科研 idea：Skill Acquisition Barrier
  S0 缺口 → S1 检索 → S2 安装 → S3 调用+载荷
  主空白：agent 自主 install 的分指标量化；勿与 Skill-Inject 80% 横比。

必读：15_LIT_ACADEMIC_BRIEF.md、13_LIT_READING_JOURNEY.md、14_LIT_SUMMARY_TABLE.md。

输出要求：
- 优先学术汇报体（分块/定位/空白/口述），少用超宽表格
- 每篇新文填 threat model checklist
- 更新 13（Phase N）、14（短表）、必要时 15
- PDF 存 idea/papers_phaseN/
- 发现直接竞品时先报告用户再改 idea 口径

不做：大规模改实验代码；不声称 post-load 新 SOTA ASR 为本贡献。
```

---

## 8. 成功标准（文献 agent 何时算完成一轮）

一轮「继续读文献」至少交付：

1. 新文列表（标题 + arXiv + 一句话）  
2. 与 S0–S3 / 空白的关系（支撑 or 威胁 idea）  
3. 更新后的 `13` 或 `15` 补丁  
4. （可选）给主 agent 的 **可执行实验提示** 1–3 条  

---

## 9. 联系人信息（项目内）

- 用户偏好：中文；汇报清楚 > 表格花哨  
- 实验约束：合成数据、外泄仅 127.0.0.1；模型曾用 deepseek-chat  
- 导读入口：`idea/00_README.md`

---

**交接完成标志**：文献 agent 已读本文件 + `15` + `13` 最新 Phase，并能用自己的话复述 idea 空白与三块文献地图。
