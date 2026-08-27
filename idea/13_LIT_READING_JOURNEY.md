# 13 — 文献阅读过程：从 IPI 到 Acquisition Barrier 科研 Idea

> **本文档性质**：不是论文列表，而是 **「我怎么读、读完怎么想、想法如何改」** 的过程记录。  
> **用途**：自己复盘、给导师讲 idea 来源、给新接手的人还原思考链。  
> **配套**：清单式阅读 → `10_PAPERS_FOR_FEASIBILITY.md`；验证表 → `12_PAPER_VALIDATION.md`；起源短版 → `01_ORIGIN.md`。  
> **最后更新**：2026-07-16  
> **阅读提示**：Phase 0–9 保留的是当时判断；其中“install 整体仍空白”“A2 搜到但拒绝安装”等口径，已由 **Phase 10** 的新文与方法学复核修正，不应单独摘引。

---

## 0. 一句话时间线

```
读 IPI「retrieval barrier」
    → 迁移到 skill「会不会被选中」
        → 做 T1–T4 PoC + selection 三档实验（0%/10%/5%）
            → 发现「跨域专一偏好」；LLM 对抗改描述打不动
                → 对照 Skill-Inject 80%：原来不是同一阶段
                    → 扩成 acquisition 四阶段（缺口→检索→安装→调用+载荷）
                        → Phase 10 验空白：显式 install E2E / 命令输出已有工作
                            → 主 idea 收窄：普通任务触发的自主 acquisition + executed 分段 E2E
```

---

## Phase 0 — 起点问题：Agent 安全里什么值得做？

### 当时的背景

- 已有 hello-agents 实验环境、T1–T4 skill 攻击 PoC（返回值注入、外泄、描述投毒、越权）。
- 导师要求：从简到难、先验证假设；觉得「想不出好办法」说明问题可能值得做。
- 同时读过 PlanInjection / WebThinker 等 agent 攻击方向，需要一个 **可迁移、有 barrier 叙事** 的切口。

### 阅读状态

尚未系统读 skill 供应链；直觉是「skill 投毒很危险」，但评测往往 **假设恶意 skill 已被调用**。

### 留下的疑问

> 如果 agent 面前有一堆良性工具，恶意 skill 真的会被选中吗？

---

## Phase 1 — 锚点论文：IPI 与 Retrieval Barrier

### 精读

| 论文 | 标识 | 读什么 |
|------|------|--------|
| **Overcoming the Retrieval Barrier: Indirect Prompt Injection in the Wild** | Chang et al., arXiv:2601.07072, USENIX Security | barrier 叙事、Vanilla/Query+/CEM、端到端 ASR |

本机 PDF：`/home/forks/AResearch/ANL/2601.07072v1.pdf`

### 读后笔记（当时）

1. **前人默认「毒文档会被检索到」**；Vanilla 检索率 ≈ **0%**。  
2. 真正瓶颈是 **retrieval**，不是注入后能不能执行。  
3. 方法：trigger（骗 embedding）+ attack fragment（真恶意）；**CEM** 黑盒优化。  
4. 优化后 Recall@5 近 **100%**；端到端外泄等仍可很高。

### 想法迁移（关键一步）

把攻击链对齐：

| IPI | Skill 场景（第一版迁移） |
|-----|--------------------------|
| 埋毒文档 | 注册恶意 skill |
| **被检索** | **被 agent 选中** |
| 进上下文 → 执行 | 调用 → 执行 |

命名：**skill selection barrier**（对标 retrieval barrier）。

### 假设（待实验）

> 不优化 description 时，恶意 skill 在多工具竞争下被选中率 ≈ 0；  
> 若优化后仍低，说明 selection 比 embedding 检索更硬，或方法不对。

### 本阶段产出

- idea 文件：`01_ORIGIN.md`、`06_KEY_CONCEPTS.md`  
- 决定：**先做 selection 三档实验**，不先上 CEM 攻 hybrid 检索。

---

## Phase 2 — Skill / MCP 基准：确认攻击面真实

### 阅读动机

selection barrier 要站得住，必须先确认：skill/MCP 投毒不是臆想，而是社区已承认的攻击面。

### 读过并吸收的核心文献

| 论文 | 标识 | 读后带走的一点 | 对 idea 的作用 |
|------|------|----------------|----------------|
| **Skill-Inject** | arXiv:2602.20156 | 最高约 **80% ASR**；skill 文件 = 指令中的指令；script > 正文 | 证明 **装载后** 很危险；供应链叙事 |
| **MCPTox** | arXiv:2508.14925 | Tool Poisoning：毒在 **description**；真实 MCP；强模型有时更脆 | 支撑 T3；metadata 可信假设可破 |
| **MSB** | arXiv:2510.15994 | 12 类 taxonomy：name-collision、preference、**false-error**、tool-transfer… | 攻击菜单，尤其 Stage2 候选 |
| **MCPSecBench** | arXiv:2508.13220 | 多平台、多攻击面 | related work / 生态真实性 |
| **AgentDojo / InjecAgent** | 2406.13352 / 2403.02691 | 工具返回不可信 → 劫持后续 | 支撑 T1、权威通道 |
| **LASM 等综述** | 2604.23338 等 | Tool / Ecosystem 分层 | 把问题标到供应链层 |

同时维护：`literature.md`（偏 slides / T1–T4 教学）。

### 读 Skill-Inject 时的第一次「不对劲」

Skill-Inject 开篇写：

> Users can **install** new skills like software packages…

但实验是：skill **已经在 agent 上下文**，测「会不会执行注入」。

**当时的处理**：先记一笔「他们默认已加载」，主实验仍做 **预装后 selection**（因为更接近 IPI 的「进上下文前一步」的简化版）。

### 本阶段产出

- T1–T4 PoC 与 `secskill-lab`  
- 决定用 **Vanilla / Query+ / Optimized** 三档对齐 IPI Figure 2。

---

## Phase 3 — 自己的实验：Selection Barrier 被证实，但优化失败

### 做了什么（简记）

- 6 良性 skill + 1 恶意；20 自然 query；deepseek-chat；hello-agents  
- Vanilla 0% → Query+ 10% → LLM 对抗优化 5%  
- 明确 query **从不**选恶意；仅模糊/跨域偶尔中招  

详见：`02_EXPERIMENT_RESULTS.md`、`03_CURRENT_BOTTLENECK.md`、`08_DATA_SNAPSHOT.md`

### 实验如何「逼」文献再读

| 实验事实 | 逼出的文献问题 |
|----------|----------------|
| 0%–10% vs Skill-Inject 80% | threat model 是否可比？ |
| 全能描述不如粗糙 Query+ | agent 吃「许可」还是「角色」？ |
| 5 轮 LLM 对抗无效 | ToolTweak/ToolHijacker 怎么优化成功的？ |
| 专一性偏好 | 是 feature 还是可绕？ |

### 中间错误路径（已排除，见 03）

- 评测 bug、历史污染、API 不稳、攻击者 LLM 太笨 → 都不是主因  
- 继续在「通用助手 description」上打转 → 被导师式判断：要回 **机制**，不只要文案  

### 本阶段 idea 状态

> Selection barrier **存在**；但「用 CEM 式思路只改 description 打穿明确 query」**此路不通（当前方法下）**。

---

## Phase 4 — 对照 Tool 选择攻击：原来 5% 和 80% 不在同一赛场

### 精读

| 论文 | 标识 | 读后纠正 |
|------|------|----------|
| **ToolHijacker** | arXiv:2504.19793, NDSS 2026 | 标准架构 = **retrieval + selection**；恶意 doc **已在库**；R⊕S 两段优化；ASR 常 80%+；手动注入因检索失败只有 10–30% |
| **ToolTweak** | arXiv:2510.02554 | **同类**工具间改 name+description：20%→81%；不是跨域全能 vs weather |

### 认知更新

1. **「description 优化没用」说满了** → 应改为：跨域专一竞争下全能描述没用；同类/候选内很有用。  
2. Skill-Inject 80% = **post-load 规程服从**；我们 5% = **pre-load 跨域抢选**。  
3. ToolHijacker 证明：库内场景下 **检索门** 才是端到端关键（对齐 IPI）。  
4. 我们若只有「预装 + 跨域 selection」，贡献是 **现象**（专一性偏好），方法突破不足。

### idea 转向

从「只优化 description 抢选中」转向：

> 是否缺了整段 **acquisition**（发现 → 安装 → 再选中）？

初稿方向写在：`04_NEXT_DIRECTIONS.md`（骗安装、marketplace、CEM 检索等）。

---

## Phase 5 — 拼装 Acquisition 管线：四阶段 Idea

### 思考来源（机制 + 文献碎片）

| 机制直觉 | 文献碎片 |
|----------|----------|
| 无缺口不会装 | 专一性偏好实验 |
| 搜到 ≠ 装 | A2 冒烟后坐实 |
| 装后变专一则易调 | ToolTweak / 2605.11418 Selection |
| 旁路下毒 | Skill-Inject script、Poise |
| 权威通道 | AgentDojo、MSB FE、README 攻击 |
| 渐进信任 | SCR、Skills Are Not Islands |

### 管线定稿

```
S0 缺口 → S1 检索 → S2 安装 → S3 调用 + 载荷（+ task_ok）
```

端到端：

\[
P = P(\text{search}) \times P(\text{rank}) \times P(\text{install}) \times P(\text{invoke} \land \text{payload} \land \text{task\_ok})
\]

### 工程落地（阅读与实验交错）

- `secskill-lab/acquisition/`：marketplace、search/install、8 分指标  
- A0：明确 query + 预装 → 不选恶意（锚点）  
- A2：缺口 + 市场 → **gap✓ retrieved✓ installed✗**  

### 本阶段文档

- `09_ACQUISITION_PIPELINE.md` — 作战图 + 实验矩阵  
- `11_MENTOR_ONEPAGER.md` — 对外口径  

### Idea 的一句话（当前版）

> **Skill Acquisition Barrier**：在具备 search/install 能力的 agent 上，恶意 skill 进入工具列表并被合理调用之前，存在可量化的多阶段瓶颈；文献高 ASR 多默认跳过该前半程。

---

## Phase 6 — 用文献「验收」攻击：读验证轮

### 动机

idea 成形后，要回答：**这是不是自嗨？有没有人已经做完？**

### 本轮精读重点

| 论文 | 标识 | 验收结论 |
|------|------|----------|
| **Semantic Supply-chain on SKILL.md Registry** | arXiv:**2605.11418** | **最强验收**。显式 gap=registry lifecycle before load；Discovery 86% win / Top10 80%；Selection 77.6%；可 compose |
| **Poise** | arXiv:2606.07943 | Stage3b：单行 setup+旁路、任务仍成功 ~89% ASR |
| **You Told Me to Do It** | arXiv:2603.11862 | 文档/安装说明诱导外泄 ~**85%** → 权威通道 |
| **SCR** | arXiv:2606.15242 | 组合风险；TrustLift 促装 **>83%**；渐进信任 |
| **Skills Are Not Islands** | arXiv:2607.01136 | 依赖图 → 二重依赖 |
| **Dynamic Malicious Skills** | arXiv:2606.16287 | 运行时再注毒 |
| **HalluSquatting 类** | arXiv:2607.07433 | 当时仅作 S1 备选；Phase 10 精读后升为显式 install E2E 强邻居 |
| 生态报告 | ClawHavoc / ToxicSkills 等 | 真实市场已有大量恶意 skill |

### 验收表（压缩）

| 阶段 | 文献是否支持「可攻」 | 我们的位置 |
|------|----------------------|------------|
| S0 缺口 | 中（FE 等） | 已触发 search |
| S1 检索 | **强**（2605.11418 / ToolHijacker / IPI） | 关键词已够；CEM 可选增强 |
| S2 安装 | **中—主空白** | **当前断点**；主贡献候选 |
| S3 选中/执行 | **强**（正确设定下） | 装通后引用 SI/Poise |

### 必须改掉的表述（验收后）

| 旧 | 新 |
|----|-----|
| description 优化没用 | 跨域专一下全能描述没用；候选内/同类可用 |
| 我们比 Skill-Inject 更难 | 我们测他们跳过的前半程 |
| 只靠必要性卡片 | S2 应测 FE / 文档 / TrustLift |

详见：`12_PAPER_VALIDATION.md`

---

## Phase 7 — 阅读方法沉淀（以后继续用）

### 每篇必填的 5 行（防 threat model 比歪）

```
论文:
默认 skill/tool 是否已在上下文?  [是/否/部分]
有没有 search / install 动作?    [有/无]
成功是否要求用户任务仍完成?      [是/否]
优化对象是什么?                 [desc/name/body/script/trigger]
可直接进我实验的一点:           [...]
```

### 读的顺序原则

1. **先锚点（IPI）** 再迁移，避免无结构堆 citation  
2. **先现象实验** 再回头读 ToolHijacker，避免过早优化算法  
3. **高 ASR 先画 threat model 边界**，再比数字  
4. **验收轮** 找「是否有人写了同样的 gap」（2605.11418）  
5. 清单与过程分离：清单用 `10`，过程用本文 `13`

### 阅读与实验的交织（实际发生的）

```
读 IPI → 设计 selection 实验 → 跑出 0–10%
    → 读 Skill-Inject 困惑 80% → 读 ToolHijacker/ToolTweak 解惑
        → 设计 acquisition → 搭 mock → A2 断在 install
            → 读 2605.11418 / MSB / README / SCR 验收与补菜单
                → 下一步：Stage2 ablation（实验驱动再读细节）
```

**不是**「读完 30 篇再动手」，而是 **读 → 做 → 被结果逼着读 → 改 idea**。

---

## 文献地图（按 idea 角色，非发表年）

### A. 叙事祖先

| 角色 | 论文 |
|------|------|
| Barrier 叙事模板 | IPI 2601.07072 |
| 两阶段 tool 选择 | ToolHijacker 2504.19793 |
| Registry 前半程 | Semantic SC 2605.11418 |

### B. Post-load（引用，不横比 ASR）

| 角色 | 论文 |
|------|------|
| Skill 文件执行 | Skill-Inject 2602.20156 |
| 隐蔽 body 注入 | Poise 2606.07943 |
| MCP 描述投毒 | MCPTox 2508.14925 |

### C. 方法菜单（Stage2/1）

| 角色 | 论文 |
|------|------|
| 攻击 taxonomy | MSB 2510.15994 |
| 同类 selection 优化 | ToolTweak 2510.02554 |
| 文档权威 | You Told Me 2603.11862 |
| 信任转移促装 | SCR 2606.15242 |
| 依赖 | Skills Are Not Islands 2607.01136 |
| 检索 trigger | IPI / 2605.11418 Discovery |

### D. 生态真实性

| 角色 | 材料 |
|------|------|
| 在野恶意 skill | Do Not Mention 2602.06547；ToxicSkills；ClawHavoc 等 |
| 索引 | github.com/LLMSecurity/awesome-agent-skills-security |

---

## Idea 演变对照表（给导师 / 自己）

| 时间节点 | Idea 表述 | 主要依据 |
|----------|-----------|----------|
| Phase 1 | skill selection barrier ≈ IPI retrieval barrier | IPI 迁移 |
| Phase 3 | barrier 存在；优化难 | 0–10–5% 实验 |
| Phase 4 | 5%≠80%；设定不同 | Skill-Inject / ToolHijacker / ToolTweak |
| Phase 5 | acquisition 四阶段；install 可能是真瓶颈 | 机制 + A2 冒烟 |
| Phase 6 | 主贡献 = Install barrier + 跨域 selection；Discovery 可引用 2605.11418 | 验收精读 |

---

## 仍未精读完、但已挂起的（诚实）

| 论文/方向 | 为何挂起 | 何时读 |
|-----------|----------|--------|
| ToolHijacker 优化算法细节 | 先不实现 CEM | S1 要上 trigger 时 |
| MCPTox 全表跨模型 | 换模型时 | 跨后端实验前 |
| 防御类（ClawGuard 等） | 先攻后防 | 有主攻击数字后 |
| 本地 70B 相关工程文 | 见 `10_LOCAL_BACKEND_PLAN` | 部署时 |

---

## 开题 / 开篇可用的「阅读故事」三段论

**第一段（祖先）**  
IPI 表明：间接注入的真实瓶颈往往是 **能否进入上下文**（retrieval barrier），而非默认已在上下文后的执行。

**第二段（迁移与挫败）**  
我们将同一逻辑迁到 agent skill：在多工具竞争下验证 **selection barrier**（0%–10%）。同时发现 Skill-Inject 等 **~80% ASR** 评测默认 skill 已加载，与预装跨域 selection **不可比**；ToolHijacker/ToolTweak 则表明在 **库内/同类** 设定下 metadata 优化可以很强——说明我们缺的是 **acquisition 前半程的完整分解**，而非「LLM 选工具绝对安全」。

**第三段（定锚与文献空白；Phase 10 修订版）**  
Semantic Supply-chain（2605.11418）已证明 registry 上 Discovery/Selection 可被 SKILL.md 操纵；HalluSquatting 与 SearchGEO 又分别覆盖显式安装授权下的真实 E2E 和安装命令输出。我们的 idea 因而收窄为 **Skill Acquisition Barrier**：在用户只给普通任务时，测 agent 是否因能力缺口自主 search/install，并沿 emitted→executed→invoked→payload→task_ok 做分段归因。

---

## 与 idea/ 其他文档的关系

| 文件 | 关系 |
|------|------|
| `01_ORIGIN.md` | Phase 1 的浓缩版 |
| `10_PAPERS_FOR_FEASIBILITY.md` | 按阶段的 **阅读清单**（what to read） |
| `12_PAPER_VALIDATION.md` | Phase 6 的 **验收表**（does it hold） |
| `11_MENTOR_ONEPAGER.md` | 对外一页，不含过程 |
| **`13`（本文）** | **阅读过程与 idea 演变**（how we got here） |

---

## 下一步阅读（跟着实验走）

1. **Stage2 实验前**：MSB False Error / Preference 原文例子；You Told Me 注入位置消融；SCR TrustLift 设定  
2. **Install 率起来后**：2605.11418 Discovery 实现与 Poise setup 句式  
3. **写 related work 时**：按本文「文献地图 A/B/C/D」四段写，避免堆砌  

---

## Phase 8 — 第二轮新文精读（2026-07-15）

> **本轮目标**：补「架构/在野/后门/检测/防御」五条支线，避免 idea 只围着攻击论文转；  
> 看是否有人已经把 **agent 自主 install** 做成主结果（结论：**仍无**）。

### 8.1 架构与 Acquisition 术语 — 强烈相关

| 论文 | 标识 | 类型 |
|------|------|------|
| **Agent Skills for LLMs: Architecture, Acquisition, Security, and the Path Forward** | Xu & Yan, arXiv:**2602.12430** | 综述 / 框架 |

**读后要点：**

1. **Progressive disclosure 三层加载**（与你管线同构）：
   - Level 1 **Metadata 始终加载**（name/description，~30 tokens）→ 影响「何时相关 / 是否该触发」  
   - Level 2 **Instructions 触发时加载**（body）→ Skill-Inject 主战场  
   - Level 3 **Resources 按需**（scripts/assets）→ Poise / PhantomSkill 旁路  

2. **Skill Acquisition 被正式列为轴**：人类编写、自主发现（如 SEAgent）、组合合成等——**「acquisition」不是你生造的词**，综述已用。  

3. **安全段明确**：不能只看安装时是否恶意，还要看声明用途、指令、脚本、**生命周期治理**；提出 Skill Trust & Lifecycle Governance。  

4. Skills vs MCP：skill = 能力包/规程；MCP = 连接性——你把 skill 当供应链入口与此一致。  

**对 idea：**  
- 你的 S1/S3a 对应 **Level 1 元数据竞争**；S3b 对应 Level 2/3。  
- 综述承认 acquisition + lifecycle，但 **没有**给你那种「search→install 分指标 ASR」。  
- related work 可写：我们 empirically instantiate acquisition barrier under progressive disclosure。

---

### 8.2 在野恶意 Skill — 生态真实性

| 论文 | 标识 | 类型 |
|------|------|------|
| **“Do Not Mention This to the User”** | Liu et al., arXiv:**2602.06547**, USENIX Sec 2026 | 大规模测量 |
| **Context Matters / Repository-Aware…** | Holzbauer et al., arXiv:**2603.16572** | 仓库上下文检测 |
| **Agent Skills Enable… Trivially Simple PI** | Schmotz et al., arXiv:**2510.26328** | Skill-Inject 早期短文 |

**Do Not Mention 要点：**

- 扫 **98,380** skills（两大 registry），确认 **157** 恶意（632 漏洞、13 技法）；披露后 **100% 下架**。  
- 两类 archetype：**凭证外泄型** vs **决策劫持型**。  
- 高级攻击常靠 **shadow features**（公开文档没有的隐藏行为）——对齐「装时干净、用时才毒」。  
- 生命周期可跨 **安装时** 采集（E2 harvest during installation 等表述）——说明 **install 时刻本身就是攻击窗口**，不只是 load 后执行。  

**Repository-Aware 要点：**

- 高安装量 skill 关联仓库问题比例更高（文中 installs>1000 时仓库侧更高比例发现）；强调 **不能只扫 SKILL.md 单文件**。  

**2510.26328 要点（Skill-Inject 前身）：**

- 动机条列：第三方市场、非技术用户、全是 instruction、人类难审长文、可藏在相关指令里。  
- Claude Code 实验：pptx skill + backup 脚本；**「Don’t ask again」** 权限继承 → 恶意脚本无二次确认。  
- 注入放 description 或 body 都有效；脚本让行为看起来像「跑 backup」。  

**对 idea：**  
- 「恶意 skill 会进真实市场并被装」**已是事实**，不是假设。  
- 在野攻击多靠用户/生态安装；**agent 自主 install 仍是你可测的空白**。  
- 「装的时候就能偷」→ 你的 E2E 指标可把 **install 时 payload** 与 **invoke 时 payload** 分开（未来增强）。

---

### 8.3 后门与旁路形态 — Stage3 加深

| 论文 | 标识 | 结果摘要 |
|------|------|----------|
| **SkillTrojan** | arXiv:**2604.06811** | skill 级后门；自动合成 3000+ 后门 skill；ASR 可至 **97.2%**，清洁任务效用保留 |
| **BadSkill** | arXiv:**2604.09378** | **model-in-skill**：包内嵌后门模型，参数语义触发；ASR **97.5–99.5%**；清洁 skill BA=100%/ASR=0% |
| **PhantomSkill** | arXiv:**2606.19191** | VulMask：恶意藏在辅助资源，伪装成漏洞形实现；ASR 约 **50–60%** 量级且降告警 |
| **ShareLock** | arXiv:**2606.27027** | MCP 多 tool 分片（Shamir）；单 tool 扫描过不了，聚合后重组；ASR **>90%** |

**对 idea：**

- Stage3 **怎么打**已经卷得很深（后门、模型毒、分片、掩码脚本）。  
- **不要**把主贡献做成「又一个 post-load 高 ASR」——和 SkillTrojan/BadSkill 撞车。  
- 应 **引用** 它们说明：一旦过 acquisition，后续危害空间极大。  
- PhantomSkill/ShareLock → 支持你「渐进/组合/旁路」叙事，作进阶非第一周。

---

### 8.4 检测与防御 — 写威胁时主动交代

| 论文 | 标识 | 要点 |
|------|------|------|
| **SkillSieve** | arXiv:**2604.06550** | ClawHub 49592 skill；三层分流检测；F1 **0.920**；$0.006/skill；Layer1 滤掉 86% |
| **AIRGuard** | arXiv:**2605.28914** | 运行时权威控制；不把 untrusted 上下文当授权；Sonnet 等 ASR 可从 30%+ 压到单位数 |

**对 idea：**

- 防御在加强 → 你的攻击需谈 **stealth / task_ok / 扫描逃逸**（2605.11418 Governance 已有）。  
- SkillSieve 主要挡「恶意 skill 提交/静态语义」；**不解决**「agent 该不该 install」的决策安全。  
- 可写：检测默认 skill 已到达客户端；我们攻击链更早（discovery→install 决策）。

---

### 8.5 Tool 检索深度 — 支撑 S1 mock

| 论文 | 标识 | 要点 |
|------|------|------|
| **How Many Tools Should an LLM Agent See?** | arXiv:**2605.24660** | 必须先 retrieval 再给 LLM；固定 K 有问题；BoR 指标 + 可学习 shortlist 深度 |

**对 idea：** marketplace top-k + agent 再决策，是 **工业默认结构**，不是玩具。

---

### 8.6 本轮总表：新文 vs 你的阶段

| 新文 | S0 | S1 | S2 | S3 | 备注 |
|------|----|----|----|----|------|
| 2602.12430 架构综述 | ○ | ● | ● 术语 | ● | acquisition 官方化；progressive disclosure |
| 2602.06547 在野 | | ○ | ● 生态 | ● | 157 恶意；装时即可害 |
| 2510.26328 早期 SI | | | ○ | ● | Don’t ask again |
| 2603.16572 仓库上下文 | | | ○ | ● 检测 | 不能只扫单文件 |
| SkillTrojan / BadSkill | | | | ●● | 极高 ASR；别撞主贡献 |
| PhantomSkill / ShareLock | | | | ● 进阶 | 旁路/组合 |
| SkillSieve / AIRGuard | | | | 防御 | 交代边界 |
| 2605.24660 How Many Tools | | ● | | | top-k 合理 |

● 强相关　○ 弱相关

---

### 8.7 本轮后 idea 微调（只改表述，不改主线）

| 仍坚持 | 新加一句 |
|--------|----------|
| 主贡献 = Acquisition / Install barrier | 对齐 **progressive disclosure Level-1 路由** 与 **registry lifecycle** |
| 不与 Skill-Inject 80% 横比 | 也不与 SkillTrojan/BadSkill 97% 横比（post-compromise 不同层） |
| Stage2 是断点 | 在野证据表明 **install 窗口**真实；需测 agent 自主路径 |
| Stage3 旁路 | 引用 PhantomSkill/Poise/SI，自己做 canary 即可 |

**仍无人替你做完的：**  
在 **同一 agent 轨迹** 上报告  
`gap × retrieved@k × installed × invoked × payload × task_ok`。

---

### 8.8 本轮 PDF 缓存

```
idea/papers_phase8/   # 11 篇（见 Phase 8 列表）
```

---

## Phase 9 — 第三轮新文：偏好操纵 / 红队 / 编排 / 多步劫持（2026-07-15）

> **本轮目标**：补 MSB 点名的 **preference manipulation** 原文、**不改 skill 的红队**、**大规模 skill 编排**、以及多步检索劫持——看是否挤压你的 Install barrier 空白。  
> **结论预告**：**空白仍在**；MPMA/SkillJect 多默认工具/skill **已暴露**；SkillAttack **不改 skill**，与你 threat model 正交。

### 9.1 MPMA — Preference Manipulation 原文（Stage2/3a 菜单）

| 论文 | 标识 |
|------|------|
| **MPMA: Preference Manipulation Attack Against Model Context Protocol** | Wang et al., arXiv:**2505.11154**, AAAI |

**设定：**

- MCP 生态下操纵 **tool name + description**，让 agent **偏好选恶意 MCP server/tool**  
- 经济动机：付费服务 / 广告收入劫持  

**两种攻击：**

| 变体 | 做法 | 效果 |
|------|------|------|
| **DPMA** | 名称/描述里直接塞操纵词（best、must use…） | ASR 常 **100%**，但 **不隐蔽** |
| **GAPMA** | 四类广告策略 + **遗传算法** 优化描述 | **高 ASR + 更高隐蔽性**（过人工/检查） |

**对 idea：**

- 直接支撑你 Stage2/3a 的 **I2 必要性 / preference** 菜单；MSB 的 PM 有了可引用主文献。  
- 优化环 = 广告模板 + GA，比你「LLM 写信息中枢」更结构化 → 可借来做 **装入后 description 优化**，不是装前跨域全能。  
- **默认工具已在 MCP 主机可见** → 仍是 post-exposure selection，**不是** search→install 全链路。  
- 经济叙事可写进 motivation：marketplace 有商业激励做 preference 操纵。

---

### 9.2 SkillAttack — 不改 skill 的红队（threat model 正交）

| 论文 | 标识 |
|------|------|
| **SkillAttack: Automated Red Teaming of Agent Skills through Attack Path Refinement** | Duan et al., arXiv:**2604.04989** |

**关键一句话：**

> 通过 **对抗性 user prompt** 利用 skill 的 **潜伏漏洞**，**不修改** skill 文件。

图 1 三种视角：

1. 改 skill 注入恶意指令（易被审计）  
2. 静态分析找洞（不能证可利用）  
3. SkillAttack：迭代 path refinement **证明确实可利用**  

**结果：**

- 对抗构造 skill：ASR **0.73–0.93**  
- 真实 skill：最高约 **0.26**  
- 闭环：漏洞分析 → 并行攻击生成 → 执行反馈 refinement  

**对 idea：**

- **正交 threat model**：他们攻击「已装好的良性 skill + 恶意用户提示」；你攻击「恶意 skill 如何进入工具箱」。  
- related work 必须写清：SkillAttack ≠ skill injection supply chain。  
- 提示：即使 skill 无毒，交互路径仍危险 → 你的防御讨论可引用；**不替代** acquisition 贡献。

---

### 9.3 SkillJect — 自动化毒 skill 生成（Stage3 方法竞品）

| 论文 | 标识 |
|------|------|
| **SkillJect: Effectively Automating Skill-Based Prompt Injection** | Jia et al., arXiv:**2602.14211** |

**要点（自摘要与章节）：**

- **首个自动化** 为 skill-enabled agent **生成毒 skill** 的框架  
- 双通道 / 反馈：失败时根据「是否执行」等反馈改写 SKILL.md（front-loaded inducement）  
- 跨 Claude Code / Codex / Gemini CLI 等平台  
- 相对手工 skill-injection 更有效  

**对 idea：**

- 与 Skill-Inject/Poise 同属 **毒 skill 内容** 线；优化的是 **装入后的诱导句**，不是 install 决策。  
- 你 Stage3 可 **引用**「自动化毒 skill 生成已有」；主实验仍做 acquisition 分指标。  
- 若以后做「装入后 description 优化」，可对标 SkillJect 反馈环 + MPMA GAPMA。

---

### 9.4 KidnapRAG — 多步检索链劫持（S1 类比强化）

| 论文 | 标识 |
|------|------|
| **KidnapRAG: Black-Box Hijacking Reasoning in Agentic RAG** | Choi et al., arXiv:**2607.00422** |

**要点：**

- 黑盒：只能发 **外部可检索毒文档**  
- 三角色文档：**Bait**（吸引首检）→ **Chain-Link**（维持错误推理链）→ **Mal-Ins**（目标答案）  
- 强调：成功 = 不仅进 top-k，还要 **多步推理链不断**  

**对 idea：**

- 与 IPI/2605.11418 Discovery 同族：**获取前半程**。  
- 多步 **Bait→Link** 可类比你的「先缺口/假错误 → 再搜 → 再装」：单步搜到不够。  
- 不直接给 install 数字，但支持 **分阶段诱导** 叙事。

---

### 9.5 AgentSkillOS — 生态规模下的 selection 系统

| 论文 | 标识 |
|------|------|
| **Organizing, Orchestrating, and Benchmarking Agent Skills at Ecosystem Scale** | Li et al., arXiv:**2603.02176**（AgentSkillOS） |

**要点：**

- skill 规模 **200 → 1K → 200K**；树检索近似 oracle selection  
- DAG 编排多 skill 优于 flat 调用  
- 问题是 **能力发现与编排效率**，不是安全  

**对 idea：**

- 反证：生态越大，**retrieval + selection 基础设施越硬** → 攻击面与你 mock marketplace **同构**。  
- 他们优化「选对 skill」；你研究「恶意 skill 如何挤进被选路径」。  
- 200K 规模下 **无 install 安全指标** → 你的空白仍在。

---

### 9.6 旁支：组合 CLI 与过度特权

| 论文 | 标识 | 一句话 | 与你 |
|------|------|--------|------|
| **MOSAIC** | arXiv:**2607.02857** | 无害 CLI 经共享状态组合致害；ASR **96.59%** | 对齐 SCR/组合；Stage3 进阶 |
| **When Lower Privileges Suffice** | arXiv:**2606.20023** | agent **过度特权选工具**；会过早 escalate | 专一/权限偏好；装后选工具时可引 |

---

### 9.7 Phase 9 总表

| 论文 | S0 | S1 | S2 | S3 | 是否吃掉你的空白 |
|------|----|----|----|----|------------------|
| MPMA 2505.11154 | | ○ | ● 偏好文案 | ● 选中 | 否（已暴露工具） |
| SkillAttack 2604.04989 | | | | ● 交互利用 | 否（不改 skill） |
| SkillJect 2602.14211 | | | ○ | ● 毒 skill 生成 | 否（post-load 内容） |
| KidnapRAG 2607.00422 | ● 多步 | ● | | | 否（RAG 文档） |
| AgentSkillOS 2603.02176 | | ● 检索系统 | ○ | ● 编排 | 否（无安全 install） |
| MOSAIC / Privilege | | | | ● | 否 |

● 强　○ 弱

---

### 9.8 本轮后 idea 状态（无方向性改动）

```
仍无人报告完整：
  gap_triggered × retrieved@k × installed × invoked × payload × task_ok
  在「agent 自主 search+install」设定下

Phase 9 新增可引用武器：
  S2 文案     ← MPMA (DPMA/GAPMA) + 广告策略
  S2 正交对照 ← SkillAttack（不改 skill）
  S3 内容优化 ← SkillJect 反馈环
  S1 多步     ← KidnapRAG Bait/Chain
  规模动机    ← AgentSkillOS 200K skills
```

**实验优先级不变：** Stage2 install 诱导（FE / 文档 / TrustLift / **GAPMA 式广告+进化**）。

---

### 9.9 PDF 位置

```
idea/papers_phase9/
  2505.11154.pdf  # MPMA
  2604.04989.pdf  # SkillAttack
  2602.14211.pdf  # SkillJect
  2607.00422.pdf  # KidnapRAG
  2603.02176.pdf  # AgentSkillOS
  2607.02857.pdf  # MOSAIC
  2606.20023.pdf  # Over-privileged selection
```

---

## Phase 10 — install 近邻工作验空白（2026-07-16）

### 10.1 本轮问题

Phase 8–9 的结论是「agent 自主 install 仍无人单独报告」。本轮不再泛搜 skill 攻击，而是专门检查三件事：

1. 是否已有 agent 在真实 skill marketplace 中完成安装；
2. 是否已有论文报告 install intent / install command 的 ASR；
3. 这些结果是否发生在**普通任务触发的能力缺口**下，而非用户明确说“请安装 X”。

本轮结论要求修正旧口径：**广义 install 路径已有人测；真正仍缺的是 task-induced、agent-initiated acquisition 的分段端到端测量。**

---

### 10.2 HalluSquatting — 广义 install E2E 已被覆盖

**Beware of Agentic Botnets: Scalable Untargeted Promptware Attacks via Universal and Transferable Adversarial HalluSquatting**（arXiv:2607.07433）

- 场景：攻击者抢注 agent 容易幻觉或错误解析出的 skill slug；用户随后要求安装某个 display name。
- 平台：OpenClaw、ZeroClaw、NanoClaw；覆盖真实检索、下载、安装、tool invocation / RCE。
- 结果：不同 agent/model 下 skill fetch 与 tool invocation 可达 40%–100%；部分组合达到 10/10 fetch、10/10 invocation。
- 机制：resolver 可能直接把 display name 映射到攻击者 slug，也可能先搜 marketplace 再自动选择 top-1。

**五项核对**

1. 默认已加载恶意 skill？否。
2. 是否真的 search/install？是，含真实 marketplace 路径和下载。
3. 是否测 task_ok？不是本文重点；主要终点是 fetch、invocation、RCE。
4. 优化对象是什么？幻觉名 / display-name-to-slug 解析与抢注。
5. 是否吃掉本 idea？**吃掉“从未有人做过 install E2E”的宽泛说法；未吃掉 S0。** 其触发是用户明确下达 install 请求，不是 agent 在普通任务中自行判断能力不足并发起 acquisition。

**定位修正**

HalluSquatting 不应再只写成「S1 备选」。它是 install 路径的直接强邻居，也是显式安装授权场景的上界/对照组。

---

### 10.3 SearchGEO — install command endorsement 已有分模型 ASR

**How Much Can We Trust LLM Search Agents? Measuring Endorsement Vulnerability to Web Content Manipulation**（arXiv:2606.16821）

- 主任务是测搜索 agent 会不会被多源伪证据操纵；共评估 13 个搜索后端。
- 其 agent-skill 辅助实验直接检查：面对伪造 skill 推荐证据，agent 是否给出**精确安装命令**。
- 18 个跨生态 Mode 2B case 中：Claude Sonnet 4.6 为 0/18，GPT-5.4-mini 为 17/18，GPT-5.5 为 16/18。
- 三个相互独立、内容一致的伪来源比单一重复来源更有效，说明 source diversity / consensus 是 Stage2 的重要通道。

**五项核对**

1. 默认已加载恶意 skill？否。
2. 是否真的 search/install？使用 mock search；终点是安装命令输出，**未执行安装**。
3. 是否测 task_ok？否。
4. 优化对象是什么？搜索证据层的多源一致性，而非 SKILL.md 本体。
5. 是否吃掉本 idea？**覆盖 install intent / command-emission ASR，不覆盖 install execution、invoke、payload，也不是普通任务下的自主能力补齐。**

这意味着后续指标不能把自然语言中的“建议安装”、生成 install tool call、tool call 被框架解析、安装实际落盘混成一个 `installed`。

---

### 10.4 Skills That Don’t Exist — recommendation→显式安装的交付链

**Skills That Don’t Exist: A Large-Scale Study of Hallucinated Skill Recommendation in LLM Agents**（arXiv:2607.12340）

- 15,000 个 prompts、12 种配置中，agent 平均产生约 36.9% 的 hallucinated skill recommendation；真实开发者问题子集约 43.1%。
- RAG 可把幻觉率从 40.8% 降到 3.2%，但正确推荐仍约只有六分之一。
- 威胁模型是先收集反复出现的幻觉 skill 名，再抢注对应仓库或条目。
- benign PoC 中，研究者注册一个占位 skill；agent 推荐后，研究者**再明确指示 agent 安装**，agent 才搜索 GitHub 并安装。

**五项核对**

1. 默认已加载恶意 skill？否。
2. 是否真的 search/install？大规模实验只测 recommendation；另有 n=1、明确授权后的真实安装 PoC。
3. 是否测 task_ok？否。
4. 优化对象是什么？稳定幻觉出的 skill 名与 name squatting。
5. 是否吃掉本 idea？证明 recommendation→delivery 可行，但没有给出普通任务触发的自主安装 ASR，也没有完整分段 E2E。

论文中“installation is not a real barrier”更接近威胁判断；其大规模实验并未直接把这个命题做成 install execution 基准，因此不能把该句当作 install barrier 已被系统否定。

---

### 10.5 邻接结果（不作为主竞品）

- **Harmless Yet Harmful / NPA（2605.29354）**：skill 内容可诱导 coding LLM 幻觉包名并输出 `pip install` 命令；其 Pip Install ASR 是**文本中出现命令**，不是命令被执行。
- **Towards Secure Agent Skills（2604.02837）**：给出 Creation–Distribution–Deployment–Execution 生命周期与 single-approval 风险；属于架构/威胁 taxonomy，不是 install 决策基准。
- **Automating Skill Acquisition（2603.11808）**：这里的 acquisition 指从 GitHub 挖掘并生成 skill，不是 agent 从 marketplace 做安装决策。
- **Buildrix / SkillSelect-Serve / SkillMutator**：分别提供发布安装 CLI、registry selection/composition、安装时扫描；都能支撑生态动机，但不回答本工作主问题。

---

### 10.6 空白重写：从“无人测 install”收窄到 S0 + executed E2E

**旧说法（不再安全）**

> 文献没有单独报告 install，agent 自主 install 仍是空白。

**新说法（可用于论文）**

> 现有工作已经证明：（i）显式用户安装请求可被 identifier squatting 劫持并完成真实安装与调用；（ii）伪造搜索证据可使部分 agent 输出精确安装命令；（iii）幻觉 skill 推荐可以在后续显式授权下转化为安装。尚缺的是 **task-induced autonomous acquisition**：用户只给普通任务、未明确要求安装时，agent 是否因能力缺口自行检索并执行安装，以及该过程如何沿 `gap_triggered → retrieved@k → install_call_emitted → install_executed → invoked → payload → task_ok` 逐段衰减。

因此，真正的 threat-model 区分是：

```
显式 install 请求（HalluSquatting）      → 已有真实 E2E
推荐 / 安装命令输出（SearchGEO 等）      → 已有 intent ASR
普通任务 → agent 自发补能力 → 实际安装   → 仍缺系统分段基准
```

---

### 10.7 对实验设计的直接要求

1. **三组触发条件**：显式安装（上界）、推荐后显式确认（中间组）、普通任务能力缺口（主实验）。
2. **拆开安装指标**：`install_recommended`、`install_call_emitted`、`install_call_parsed`、`install_executed`、`installed_on_disk`。
3. **保留后半链**：安装不是终点；继续报告 `invoked`、`payload`、`task_ok` 及条件概率。
4. **加入证据通道**：把 SearchGEO 的多源一致性作为 Stage2 操纵，与 FE / README / TrustLift 并列。
5. **跨模型报告**：SearchGEO 的 0/18 与 17/18 表明 install endorsement 高度依赖 backend，不能只报单模型均值。

**当前 A2 的方法学勘误**

现有 A2 原始回复末尾已经生成 `install_skill` tool call，但框架默认三轮工具预算先被 `calendar → weather → search_skills` 用完，最后的 install call 没有再被解析/执行。因此 A2 当前只能支持：

```
已触发检索 + 已生成 install intent/tool call + 编排器截断执行
```

它**不能**支持“模型搜到后行为上拒绝安装”。修复迭代预算并重跑之前，不应把 A2 写成 Install barrier 的实证结论；这也进一步说明必须区分 emitted、parsed 与 executed。

---

### 10.8 PDF 位置

```
idea/papers_phase10/
  2607.07433.pdf  # HalluSquatting
  2606.16821.pdf  # SearchGEO
  2607.12340.pdf  # Skills That Don't Exist
  2605.29354.pdf  # Neutral Prompting Attacks（邻接）
```

---

## 附录：阅读阶段总索引（Phase 0–10）

| Phase | 主题 | 关键文献 |
|-------|------|----------|
| 0–1 | IPI → selection barrier 迁移 | 2601.07072 |
| 2 | Skill/MCP 基准 | Skill-Inject, MCPTox, MSB |
| 3 | 自实验 0/10/5% | lab |
| 4 | 设定校准 | ToolHijacker, ToolTweak |
| 5 | Acquisition 四阶段 | 自建 mock |
| 6 | 验收 | 2605.11418, Poise, SCR… |
| 8 | 架构/在野/后门/检测 | 2602.12430, 2602.06547, SkillTrojan… |
| 9 | 偏好/红队/编排/多步 | **MPMA, SkillAttack, SkillJect, KidnapRAG, AgentSkillOS** |
| 10 | install 近邻验空白与口径收窄 | **HalluSquatting, SearchGEO, Skills That Don't Exist** |

---

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-07-15 | 初版：汇总 Phase 0–6 阅读过程与 idea 演变；挂接 2605.11418 验收轮 |
| 2026-07-15 | **Phase 8**：11 篇新文（架构/在野/后门/检测/防御/检索深度）；确认 install 决策仍是空白 |
| 2026-07-15 | **Phase 9**：MPMA / SkillAttack / SkillJect / KidnapRAG / AgentSkillOS / MOSAIC / Privilege；正交 threat model 划清 |
| 2026-07-16 | **Phase 10**：发现显式 install E2E 与 command-emission ASR 已有直接工作；将空白收窄为普通任务触发的 agent-initiated、executed、分段 E2E，并记录 A2 编排截断勘误 |

*若继续读新论文，请在本文件追加 Phase 10+ 或修订记录，保持「过程文档」而不是只改清单。*
