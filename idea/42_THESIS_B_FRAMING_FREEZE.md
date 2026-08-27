# 42 — Thesis-B Framing and Prospective Validation Protocol Freeze

> 日期：2026-08-11
> 协议 ID：`authorization_binding_gap_prospective_v1`
> 依赖：idea/31（受控因果设计）、idea/33/36/40/41（已完成结果）、idea/34（旧 draft，将按本文件重排）。
> 目的：冻结论文的问题表述、术语、taxonomy 方法学、证据分级、go/no-go 判据与防御主张边界。
> **本文件不是整篇论文的预注册。** §1 声明冻结时已知的全部结果；§2 起才是前瞻冻结内容。
> 口径红线不变：只报 fixed-benchmark 与 documented configuration，不报现实 prevalence。

---

## 1. Freeze 前已知材料（诚信声明，不得事后改写）

本协议在下列结果**已被完整查看之后**写成。任何在 §2 之后出现的判据都不得声称对这些结果具有预注册效力。

### 1.1 已完成的受控实验（idea/33、36、40、41）

三个 model × scaffold cell，各 150 trial，`trial_exception=0`：

| Cell | hard `discovery_e2e` P0→P1 | 配对差 | McNemar（描述性） | 严格跨-family 判据 |
|---|---|---:|---|---|
| Qwen3-32B-AWQ × text（anchor） | 5/30 → 24/30 | +63.3 pp | 3.81e-6 | **通过** |
| Llama-3.3-70B-AWQ × text | 4/30 → 9/30 | +16.7 pp | 0.2668 | 未通过（QR 3→2） |
| Qwen3-32B-AWQ × native FC | 4/30 → 12/30 | +26.7 pp | 0.0215 | 未通过（ICS 1→0） |

其他已知结果：

- Llama 的 install / payload：`8/30 → 28/30`（+66.7 pp，p=1.91e-6），但 `task_ok` 仅 `9/28`
  —— 攻击执行比任务效用更稳定复现。
- P2-denied 拦截统一口径：**65/90 hard trial 至少触发一次 gate block；共 99 次
  `install_skill` 事件被拦；三个 cell 的 `install_execution_started` 均为 0。**
  （不得写成 `65/65`。）Llama 单 cell 28 trial 产生 62 次事件 —— 被拒后反复重试。
- P2-approved + benign twin：`functional_e2e = 25/30`、`payload = 0/30`。
- P2-approved + malicious twin：`functional_e2e = 25/30`、`payload = 25/30`（p=5.96e-8）
  —— gate 管"是否安装"，不管"安装的是否安全"。
- G0：三 policy 均 `10/10 task_ok`、0 次 search/install。
- v2 G1：三 policy 均 0 次 acquisition（v1 的 7/10 系 target 名泄漏，已定性为污染诊断）。

### 1.2 已提出并讨论过的假设

Thesis A / Thesis B、Htrans（传递授权）、acquisition permit、H0–H4 policy 阶梯、
五个必要条件、confused deputy 类比 —— 均在本 freeze 之前形成，**不得声称为盲设计**。

### 1.3 由此产生的约束

1. §1 的数字只能作为 **preliminary controlled evidence** 呈现。
2. 若某个已完成配置（如 P1）在 taxonomy 之后被发现与某真实配置类相符，
   只能写 `matches configuration class H_k observed post hoc`，
   **不得**写 `reproduced real-world configuration`。
3. 未获真实系统对应的配置一律标注 `controlled design-space configuration`。

---

## 2. Thesis B：问题表述（冻结）

### 2.1 正式表述

> 当 agent 被授权完成一个普通任务时，harness 可能把这份任务级或选择器级授权，
> 传递给之后由 agent 动态选择的第三方 artifact。由于授权没有绑定到最终 artifact 的
> 身份、版本、内容与权限范围，该 artifact 可以在缺少 artifact-specific authorization 的
> 情况下被安装，并在 agent 的环境能力下首次执行。

§2 中精确定义一次的术语：**acquisition-time authorization-subject mismatch**。
全文其余位置统一使用简称 **authorization-binding gap**。

### 2.2 Novelty 压在合取上，不压在单句上

```
delegated selection  ∧  unbound authorization  ∧  ambient first execution
```

三项中承重的是第一项：**选择权被委托给了一个组件，而用户对该组件的授权是为别的目的给的。**

预备反驳：

- *"npm package 也不是 OS principal"* → 普通 npm 场景由用户明确指定 package；此处选择权已委托。
- *"`curl | bash` 也继承用户权限"* → 命令与目标由用户主动指定；此处是自主选择 + 未绑定授权 + ambient 首次执行同时出现。

### 2.3 不得声称的表述

- ❌ "skill 不是 first-class principal"（太宽，且传统依赖包同样不是）
- ❌ "这就是 confused deputy 的重生"（principals 映射未完成前不得直接断言）
- ❌ "principal collapse"（taxonomy 出结果后再决定是否命名）
- ❌ "authority collapse"（已与 memory consolidation 方向的工作撞名）
- ❌ "permit 把 skill 提升为 first-class security principal"（见 §7 主张边界）

---

## 3. 术语表（全文与代码统一，冻结）

| 术语 | 定义 | 不等于 |
|---|---|---|
| **Harness** | 完整宿主编排层：agent loop、工具暴露、installer、approval gate、registry、execution、生命周期 | 单条 system prompt |
| **Acquisition policy** | harness 中决定 capability gap 是否允许转化为 search / select / install / invoke 的跨层策略 | 整个 harness |
| **Acquisition-encouragement scaffold policy** | 特指 P0/P1 中模型可见的 prompt + tool affordance treatment | acquisition policy 全体 |
| **authorization-binding gap** | 论文正式问题名 | — |
| **acquisition-time authorization-subject mismatch** | §2 精确定义用，全文只出现一次 | — |
| **delegated selector → selected artifact** | 机制描述用语 | — |

历史文档中的 `scaffold policy` 一律按上表第三行理解；新文字不再单独使用该词。

---

## 4. 五个必要条件与四级证据（冻结）

问题成立需要五个条件同时满足（对照 Felt 的 "per-application permissions + IPC" 结构）：

| # | 必要条件 | 受控 harness 现有证据 | 真实系统待验证 | 证据来源 |
|---|---|---|---|---|
| C1 | agent 能动态发现外部 skill | P0/P1 因果实验（§1.1） | 工具是否默认暴露、可否关闭 | 文档 / 配置 |
| C2 | agent/router 可触发安装 | 已观察到完整安装轨迹 | 模型可否直接调 installer、审批栈在哪层 | 文档 / 配置 + canary |
| C3 | 授权未绑定最终 artifact | P2 的 bool gate 是受控构造 | 绑定到 §5 的哪些字段 | 文档 / 配置 + canary |
| C4 | artifact 获得环境能力 | **仅证明了一次 loopback 网络效果** | 文件 / 网络 / shell / 凭据 / 持久化逐项 | **必须 canary** |
| C5 | 首次执行前无重新授权或隔离 | 受控 harness 中成立 | 真实安装→首次调用路径 | 文档 / 配置 + canary |

**四级证据标签（每条结论必须带一个）：**

- `OBS-CTRL` — Observed in controlled harness
- `TBV-REAL` — To validate in real systems
- `EV-DOC` — Document / config evidence
- `EV-CANARY` — Benign canary evidence

C4 的受控证据仅为 loopback 网络效果，**不得外推为"继承 agent 全部环境权限"**。

---

## 5. Binding strength ladder（taxonomy 的核心量表，冻结）

授权绑定不是有/无，而是分级：

| 等级 | 授权绑定对象 | 风险 |
|---|---|---|
| **B0** | 只有任务、会话或通用 install 权限 | 任意候选 artifact 可消费该授权 |
| **B1** | selector / query / repository URL | 选择结果仍可变化 |
| **B2** | name、tag、branch、semver range | 引用可被重新解析或替换 |
| **B3** | exact name + version + source | 较强；registry 内容是否不可变仍需验证 |
| **B4** | publisher / source + content digest | 身份与内容稳定 |
| **B5** | digest + permission scope + invocation scope + expiry | acquisition-time 完整绑定 |

对每个系统按 §6 的字段向量逐层记录，得出该系统在 search / install / first-execution
三个决策点各自的 B 等级。

### 5.1 TOCTOU 证据门（防止把任何不完美配置说成漏洞）

B1–B3 只能称为 **mutable-reference binding** 或 **potential resolution drift**。

升级为**可利用的 TOCTOU** 需要同时证明：

1. 授权时刻的对象与解析/获取/执行时刻的对象**能够产生受攻击者控制的差异**；
2. 该差异**被系统接受**（未被 lockfile、digest 校验、registry 不可覆盖策略等挡下）；
3. 差异发生时**未触发新的 artifact-specific authorization**。

三条缺一，只报绑定等级，不报漏洞。

---

## 6. Taxonomy 协议：Configuration Audit（前瞻冻结）

### 6.1 方法学原则

**Bottom-up。** 先冻结纳入标准与编码字段，逐系统核对，最后归纳 policy families。
**不得**先画好 H0–H4 再把系统塞进去。H0–H4 在本 freeze 中仅为 provisional hypothesis。

### 6.2 纳入 / 排除标准（冻结）

纳入：具备（a）第三方能力扩展机制（skill / plugin / MCP server / extension）
且（b）公开文档或公开源码可核验的 agent 产品或框架。

排除：无第三方扩展机制的；仅内部使用无公开文档的；需要付费账号才能查看安装流程且无公开文档的
（记录为 `excluded-inaccessible`，不静默丢弃）。

### 6.3 编码字段（binding vector，每系统逐项填）

| 层 | 核查内容 |
|---|---|
| Task | 授权与哪个原始任务关联？跨任务可复用吗？ |
| Selector | 授权的是 router / 会话 / 一次工具调用，还是最终 candidate？ |
| Source | 是否绑定 registry / repository / publisher？ |
| Name | 是否只绑定一个可变的 skill 名称？ |
| Version | 绑定 tag、semver 还是 immutable commit / digest？ |
| Content | 落盘内容是否验证 hash / signature？ |
| Permission | 是否绑定 network / shell / filesystem / credentials？ |
| Persistence | 临时、项目级还是全局？ |
| Invocation | 首次执行是否需要再次授权？ |
| Expiry / replay | 授权能否被未来任务重复消费？ |

同时记录：产品名、版本号、核查日期、证据 URL 或文件路径、原文摘录。

### 6.4 证据等级（每条记录必须标注）

- **A** — 产品默认行为
- **B** — 官方支持的可选配置
- **C** — 公开的社区配置 / 第三方扩展
- **D** — 研究设计点（无真实系统支持）

### 6.5 端到端 benign canary（不可省）

**不得**仅凭 README 中出现 `-y` 就判定整个 harness 为 standing consent。
必须实测完整链路：

```
普通任务 → router/agent → 外部搜索 → install command → 外层 approval
        → package manager → 落盘 → 首次调用
```

canary 为无害探针，逐项报告 artifact 实际获得的能力：

| 能力 | 探针 |
|---|---|
| filesystem read | 读取 sandbox 内预置文件 |
| filesystem write | 写入 sandbox 内标记文件 |
| network egress | 对自有 loopback / 自有域名发起标记请求 |
| shell exec | 执行无害命令并回报 |
| credentials | 检查环境变量 / 凭据文件**可见性**（只报告可见性，不读取内容） |
| persistence | 检查安装是否留存于全局 skill 目录 |

**逐项报告，不从任一项外推其余项。**

### 6.6 安全与伦理边界（执行中不得越线）

- 只在自有账号、本地 sandbox、无害 canary 上验证；
- 不扫描、不攻击真实用户或生产服务；
- 不向真实 marketplace 发布任何 skill；
- 记录版本、配置与最小复现；
- 一旦发现 vendor-impacting path，**暂停扩大测试**，先与导师 / 机构确认披露路径；
- 联系 vendor，协调修复与公开时间；披露时间纳入投稿时间线。

---

## 7. 防御：acquisition permit（主张边界，冻结）

### 7.1 permit 结构

```
Permit {
  original_task
  artifact_identity  = publisher + source + immutable digest
  permissions
  persistence_scope
  invocation_scope
  expiry
}
```

校验位置沿用现有 gate：**arguments 解析之后、安装执行之前。**
无 permit → 只允许 search / recommend；identity 不匹配 → 拦截；
权限或持久化范围扩大 → 重新确认；完全匹配 → 放行。

### 7.2 只主张什么

✅ 解决 **acquisition-time binding integrity**：用户批准 A，系统不能安装 B。
✅ 把匿名 / 可变 artifact 变为明确的 **artifact-bound authorization subject**。

❌ **不主张** full first-class security principal —— 完整主体还需要
enforcement（每个动作受权限约束）与 lifecycle（审计、吊销、隔离），
即 per-skill execution context 与 scoped 能力，属于 future work（对照 Capsicum）。
❌ **不主张**解决 malicious-artifact vetting —— 用户若批准了恶意 artifact 的精确 digest，
permit 不会救他（§1.1 的 approved-malicious 臂已证明这一边界）。

### 7.3 对抗臂（必做，否则重演 gate ≠ vetting）

1. 用 A 的 permit 安装 B
2. publisher substitution
3. tag / commit / digest replacement
4. TOCTOU（授权与获取之间替换）
5. permission expansion
6. temporary → global persistence escalation
7. replay / expiry 绕过
8. overly broad wildcard permit

### 7.4 指标（命名冻结）

- **Authorization Decision Count** —— 机械计数：每任务请求的授权决策数、
  成功良性任务所需批准数、冗余授权请求数、被拦安装尝试数、交互轮数、latency / token overhead。
- Bypass success rate（按 §7.3 逐类报告）
- Functional utility（沿用 `functional_e2e`）
- False block rate

**禁止**使用：user burden、usability、approval fatigue、user comprehension
—— 无真人参与，这些需要人因实验与 IRB。

---

## 8. 论文结构与 RQ（冻结）

### 8.1 章节顺序（Felt 式：调查在前，攻击在后）

```
1. 问题与授权绑定模型
2. 五个必要条件
3. 真实系统 taxonomy（configuration audit + canary）
4. 对观察到的配置类进行受控实例化
5. Funnel 后果测量
6. artifact-bound permit
7. 对抗性绕过与局限
```

受控 harness **从不承担世界性断言**；现实是什么样，全部由 §3 承担；
受控实验只回答"这种设计造成什么后果"。

### 8.2 研究问题

- **RQ1**：真实 agent 系统把 search / install / first-execution authorization 绑定到了什么对象？
- **RQ2**：实例化这些配置类后，acquisition policy 如何改变 funnel 的可达性？
- **RQ3**：首次执行时，artifact 实际获得了哪些环境能力？
- **RQ4**：artifact-bound permit 能否抵抗替换、重放、宽授权与版本漂移？代价是多少？

§1.1 的 450 条回答 RQ2 的一部分，标签为 `preliminary controlled evidence`，
按 §1.3 的规则决定能否称为 observed configuration 的实例化。

### 8.3 新增受控组件

- `declare_capability_gap` 工具：把模型侧的**能力缺口声明**与 harness 侧的
  **是否授予发现权**分成两个可观测事件。命名为 **gap declaration**，
  不得称为 internal recognition（模型内部状态不可观测）。
  引入后 H0 才成为有意义的对照：模型已声明缺口，harness 拒绝授予发现权。

### 8.4 Htrans（传递授权臂）

流程：用户显式批准 router → 之后只提普通任务 → router 识别缺口并选定 candidate
→ 记录 harness 是否要求 candidate-specific approval、是否落盘 / 注册 / 调用。

**两条纪律：**

1. harness 的授权行为**不是被观测的变量**（harness 是我们写的），
   而是**按 §6 观察到的真实配置复现**。测量对象是攻击者可达的 funnel 阶段。
2. **不得混入 selection attack。** 固定 router 最终选中 candidate B，只测授权传递；
   "攻击者如何让 B 被选中"（metadata manipulation / ranking / name collision /
   hallucinated identifier）是独立实验，否则一次失败无法归因。

---

## 9. Go / No-Go 判据（冻结，结果出来前不得修改）

Thesis B 升为论文 headline，需**全部**满足：

1. 两个独立真实系统中观察到同类、**具有安全实质**的 authorization-binding weakness；
2. 至少一个系统具备 A / B / C 级证据（§6.4），非 D 级假想配置；
3. 至少一条 benign canary 证明：具体 artifact 在缺少新的 candidate-specific
   authorization 时到达安装或首次执行；
4. 若主张 mutable-reference / TOCTOU，必须通过 §5.1 的三条证据门；
5. canary 逐项报告文件 / 网络 / shell / 凭据 / 持久化能力，**不从单个 localhost payload 外推**；
6. permit 能阻止 §7.3 中的 substitution / replay / scope expansion 类攻击，且保留合理 utility。

**降级路径（不是失败，是预先规定的科学退路）：**

- 只发现假想 Htrans、无真实配置支持 → Htrans 降级为 design-space analysis；
  headline 退回 Thesis A（harness policy 因果控制 acquisition 可达性）。
- 只有单个 vendor finding → 进入 case study + coordinated disclosure，
  **不声称行业普遍性**。
- taxonomy 显示真实系统普遍绑定到 B4/B5 → 问题不成立，
  论文改为"现有绑定实践的测量 + 受控 harness 的反例警示"。

---

## 10. Amendment policy（冻结）

本文件采用 **append-only amendment**。任何改动追加到文末 §11，记录：

1. 日期；
2. 改动内容与理由；
3. 改动时**已经看到的新增证据**；
4. 该改动发生在对应结果**之前还是之后**。

**不得静默覆盖原判据。** 若某判据在看到结果后被放宽，必须在论文中如实报告该 amendment。

---

## 11. Amendments

### Amendment 1 — 2026-08-11：防御升级为两点强制协议；binding 量表拆维；数学范围限定

**发生时点**：taxonomy 尚未开始，无任何新增实验结果。属于 **pre-results amendment**。
**理由**：原 §7 的单点 gate 不足以实现 artifact binding；原 §5 的单轴阶梯压扁了不可比维度。

#### A1.1 §7 升级：单点 gate → resolved-artifact-bound acquisition protocol

原表述（"arguments 解析后、安装执行前检查 permit"）**保留为协议的第一个强制点**，
但不再作为完整防御。gate 放行之后仍可能发生：tag 重新解析、同一 URL 下到不同内容、
install hook 执行、首次调用前被替换、落盘内容与 permit 声称的 digest 不一致。

冻结协议：

```
Resolve candidate
→ Fetch into non-executable quarantine
→ Canonicalize source
→ Compute / verify actual digest
→ Issue candidate-specific permit
→ Atomically materialize
→ Recheck digest before first execution
→ Consume and log authorization lineage
```

**两个强制点（缺一则 TOCTOU 仍成立）：**

1. 从隔离区进入正式安装域之前；
2. 从已安装状态进入首次执行之前。

#### A1.2 与 TUF / Sigstore 的关系（必须在设计章正面处理，不得放脚注）

预期反驳："这不就是 TUF 吗？"

冻结回答：TUF / Sigstore / npm integrity / Go sumdb 绑定的是 **publisher → artifact**，
回答"artifact 是否真实、是否为该发布者所发"，并**假设"要装 package X"由人决定**。
本文绑定的是 **user authorization → agent 自主选中的 artifact**，
回答"该用户的该次授权是否覆盖这个 artifact"。

定位为**组合而非竞争**：permit 把任务授权绑定到 digest；该 digest 的来源真实性是正交问题，
可由 Sigstore / TUF 提供。

#### A1.3 真正 agent-specific 的技术核心（冻结为 C3 的主张重心）

包管理器中安装与使用同属一次会话、同一用户意图；自主 agent 中不是：
skill 在任务 `T_i` 安装，可能在任务 `T_j`（j ≫ i）才被调用，
触发者可能是不可信的工具返回内容。**授权生命周期与 artifact 使用生命周期脱钩。**

因此 C3 的新颖性不在 digest 绑定（既有技术），而在：

- **task-scoped authorization**：permit 绑定到签发它的任务；
- **cross-task reuse 重新同意**：`T_j` 消费 `T_i` 的 permit 需拒绝或重新确认；
- **首次执行复验**：不是安装时验一次即止；
- **authorization lineage log**：事后可回答"这次执行由哪一次用户授权许可"
  —— 即 §2.1 问题陈述的直接实现。

#### A1.4 §5 的 B0–B5 单轴阶梯作废，由 binding matrix 取代

原因：维度不可比较（系统 A 绑 digest 但首次执行不复查；系统 B 只绑 name/version
但首次执行要求批准 —— 不能断言孰强）。

改为：对每个系统，在 **search / install / first-execution** 三个边界上分别编码
§6.3 的十字段向量，得到 **authorization-binding matrix** `M_H`。

仅对 **artifact identity** 单独给出有序等级，其余维度并列报告、不求和：

| 等级 | identity 绑定对象 |
|---|---|
| I0 | task / session only |
| I1 | selector / query / URL |
| I2 | name / tag / version range |
| I3 | exact source + name + version |
| I4 | canonical source + content digest |

§5.1 的 TOCTOU 三条件证据门**不变，继续有效**。

#### A1.5 编码可复现性不得预先声称

"换一个人应得到同一等级"目前是设计目标，不是已证明性质。冻结要求：
编码手册、`unknown / undocumented / not applicable` 三态区分、部分样本双人编码、
disagreement resolution 记录、报告一致率。未做到之前不写 "reproducible coding scheme"。

#### A1.6 数学范围限定（防止装饰性形式化）

判据：**一个符号若不能指向一个日志字段、一段代码或一行 taxonomy 表格，即为装饰，删除。**

保留四项：

1. `Match(p, t, x, q)` —— 即校验函数本身；
2. `Gap_install` 与 `Gap_exec` 分开 —— 决定可声称的范围（装上了 ≠ 跑起来了）；
3. 安全不变量 `Reach_b(τ,x) ⇒ ∃p : Match(p,t,x,q)` ——
   **§7.3 八类对抗臂的验收标准即为能否构造 `Reach_b=1 ∧ Match=0`**；
4. `Y_security = PayloadFired` 与 `Y_utility = TaskOK` 分离。

删除：`k* = argmax_k(1-q_k)`（中文一句话即可）；每阶段铺满 `do()` 记号
（本设计为物理随机化 RCT，estimand 在设计章陈述一次即可）。

#### A1.7 其他口径修正

- 事件仪器不再锁定"八段"，统一称 **typed cross-layer acquisition event ledger**，
  便于后续加入 `gap_declared` / `permit_issued` / `digest_verified`。
- `discovery / direct_install / residual` 准确表述为
  **对成功 E2E 轨迹的三个互斥且穷尽的路径归因桶**，不覆盖失败轨迹。
- 不写 "byte-identical twin"，只写"模型可见 marketplace metadata 与 `SKILL.md` 字节一致；
  隐藏 handler / provenance 按设计不同"。
- 跨 cell 的 gate 结果不得写成"拦截率相同"。可主张：
  *在 text tool-call 与 native function-calling 两种 adapter 中，执行层 reference point
  均阻止了已到达该边界的安装事件，三个 cell 的 `install_execution_started` 均为 0。*
  trial-level block propensity 明显不同（模型发起安装的概率不同），不得混为一谈。
- Endpoint inversion 标签为 **instrument-enabled empirical finding**，
  归入 C1 之下，不作为独立技术机制。升级为"通行 ASR 存在系统性偏误"需要：
  related-work audit 证明 task-gated ASR 确实常见、在更多 cell 中复现 divergence、
  排除单一 Llama argument-synthesis bug、且 risk ordering 预先定义。

#### A1.8 三项主贡献（冻结）

- **C1 跨层因果测量系统**：typed execution-grounded acquisition trace，
  分离 model intent / orchestration decision / installation / payload execution / task utility，
  配确定性 artifact verifier 与**分阶段干预**（P0/P1/P2、`declare_capability_gap`、Htrans）。
  仅有埋点是工程；埋点 + intervention 才是 causal measurement contribution。
- **C2 授权绑定审计方法与真实系统测量**：binding vector + 证据协议 + canary，
  跨 search / install / first-execution 三边界审计真实系统。
- **C3 resolved-artifact-bound acquisition protocol**：见 A1.1–A1.3，
  由八类对抗臂与 utility / overhead 评估。

关系：**C2 发现现实中的绑定缺口 → C1 测量其后果 → C3 强制补上缺失的绑定。**

---

### Amendment 2 — 2026-08-11：更正 TUF 表述；permit 引入 use scope；不变量加入 `Valid(p)`；trusted path

**发生时点**：taxonomy 尚未开始，无任何新增实验结果。属于 **pre-results amendment**。
**理由**：A1.2 含一处事实错误；A1.3 的跨任务规则过于绝对；A1.6 的不变量存在签发侧漏洞。

#### A2.1 更正 A1.2 的 TUF 表述（**原表述作废**）

❌ 作废：*"TUF / Sigstore 假设『要装 package X』由人决定。"*
**该表述事实错误。** TUF 正是为自动更新器设计（Tor updater、Docker Notary、PyPI），
支持 delegated roles 与自动 target 选择，不要求人工逐包选择。

✅ 冻结表述：两类系统约束的是**不同的授权关系**：

```
TUF / Sigstore / lockfile / checksum infra :
    repository or publisher authority  →  artifact

本协议 :
    consumer-side task authorization  →  agent-selected artifact  →  acquisition / use scope
```

论文用语：

> TUF、Sigstore、lockfile 与 checksum infrastructure 提供 artifact 的来源真实性、内容完整性、
> freshness 或可复现解析；它们本身不证明一次 consumer-side task authorization 是否覆盖 agent
> 随后选择的 artifact，也不规定该 artifact 可以在哪些任务、作用域和调用阶段被使用。
> 我们的协议以它们提供的 digest / provenance 为**输入**，在其上增加 task-originated
> acquisition authorization 与 authorization lineage。

定位为 `supply-side integrity` + `consumer-side authorization binding` 的**叠加**，不是替代。

#### A2.2 更正 A1.3 的跨任务规则：引入 use scope（**原"一律重新批准"作废**）

❌ 作废：*"`T_j` 消费 `T_i` 的 permit 需拒绝或重新确认。"* —— 过于绝对，会摧毁 utility。

✅ permit 显式绑定 use scope：

```
use_scope ∈ { one_shot, task, session, project, persistent }
```

规则：**只有超出原授权 use scope 的调用才需要重新授权。**

- `one_shot` permit 于首次执行后消费；
- `task` permit 于任务结束后失效；
- `project` / `persistent` permit 不在首次执行后消费；
- **每次调用仍验证范围并写 lineage。**

冻结的 agent-specific 主张：

> Agent skill 的安装时间、首次执行时间与未来复用时间可能分离；系统必须显式管理授权从
> acquisition 到 later invocation 的有效范围，而不能默认把一次安装授权永久扩展到所有未来任务。

#### A2.3 安全不变量加入 `Valid(p)`（**取代 A1.6 第 3 项**）

原不变量只检查 `Match`，存在签发侧漏洞：router 可自行申请/生成覆盖任意 artifact 的超宽 permit，
形式上满足 `Match`，但该 permit 并非来自合法用户授权。

冻结不变量：

```
Reach_b(τ, x)  ⇒  ∃p : Valid(p) ∧ Match(p, t, x, q, b)
```

**分工（不得混用）：**

| 谓词 | 负责 | 检查内容 |
|---|---|---|
| `Valid(p)` | **签发合法性** | 由可信 authorization authority 签发；可追溯到具体 authorization event；范围未超过 parent authorization；未过期；未被非法重放；use scope 覆盖当前 task / session / project |
| `Match(p,t,x,q,b)` | **比对一致性** | 实际 digest 一致；source / publisher 一致；请求的 acquisition scope 未扩张；当前边界为 install 抑或 first execution |

即：`Match` 防"A 的 permit 装 B"；`Valid` 防"router 给自己签一张万能 permit"。
overly-broad permit 攻击的是 **issuance policy**，不是 digest 比对。

#### A2.4 Trusted path 要求（`Valid` 的落地前提，新增）

在 agent 系统中，批准请求与其他内容走同一通道，且**很可能由待批准组件自行组织措辞**——
router 可显示"安装一个日历助手"，实际申请 persistent + network + shell。
这是经典 **trusted path** 问题（对照：Android 由系统从 manifest 渲染权限对话框）。

**冻结设计要求：** 批准界面必须由 harness 从**已验证 artifact 自身声明的 scope** 渲染，
**不得**使用 router 提供的散文描述。

**边界声明：** trusted path 保证用户看见的即为所授予的，**不保证**所授予的是安全的
—— §1.1 的 approved-malicious 臂已证明 model-visible metadata 相同的 twin 无法被区分。
trusted path 解决 comprehension，不解决 vetting。

#### A2.5 对抗臂按不变量的两个合取项重新划分（**取代 §7.3 的扁平八条**）

**攻击 `Match`（比对层）**

1. 用 A 的 permit 安装 B
2. publisher substitution
3. tag / commit / digest replacement
4. TOCTOU（授权与获取 / 落盘之间替换）
5. 请求 acquisition scope 超出 permit

**攻击 `Valid`（签发层）**

6. overly broad / wildcard permit（issuance policy）
7. replay / expiry 绕过
8. temporary → global persistence escalation
9. **误导性批准渲染**（trusted path）——router 诱导用户批准一个"显示含义 ≠ 实际授予范围"的 permit

每族各自报告 bypass success，不合并成单一数字。

#### A2.6 Lineage 的主张边界（修正 A1.3 第四项）

lineage log 至少连接：

```
authorization_event_id → permit_id → selector_decision_id
→ resolved_digest → installation_id → invocation_id
```

**但 lineage 是 auditability，不是 enforcement。** 分开主张：

- permit + reference monitor → 阻止不匹配的 acquisition（enforcement）;
- lineage log → 事后归因与审计（auditability）;
- append-only / hash-linked / 由可信 reference monitor 写入 → 才额外提供日志完整性
  （tamper-evident lineage，实现了才主张）。

**不得**用"我们自己的旧 harness 没有 lineage"证明真实产品都缺 lineage
—— 旧 harness 是自建的。真实系统有无 lineage 由 taxonomy 回答。

#### A2.7 结局变量泛化（取代 A1.6 第 4 项）

`Y_security = PayloadFired` 过窄：真实系统的 benign canary 没有恶意 payload。

冻结为：`Y_effect^c` —— artifact 成功产生能力 `c` 的效果（network / filesystem / shell /
credentials / persistence）。`PayloadFired` 是受控恶意实验中的一个实例。

与 `Y_utility = TaskOK` 分开报告的规则不变；endpoint inversion 表述照 A1.7 执行。

#### A2.8 暂不冻结的项（等 taxonomy 观察到真实使用方式再定）

- 默认 permit scope；
- 跨任务复用策略的具体默认值；
- 用户确认语义与提示时机；
- §7.3 中 6–9 号（`Valid` 族）对抗臂的具体参数。

**现在可并行实现的通用底层**：non-executable quarantine、digest / provenance 验证、
lineage schema、`Match` validator。`Valid` validator 与 scope policy 待 taxonomy。

taxonomy 仍是承重墙；Htrans 是否作为主实验臂，仍按 §9 的 go/no-go 门由真实配置证据决定。

#### A2.9 C3 的定名（取代 A1.8 中 C3 的表述）

C3 = **Scope-bound acquisition authorization lifecycle**（不是"digest permit"）：

```
Resolve → Non-executable staging → Digest / provenance verification
→ Legitimate authorization issuance (trusted path)
→ Atomic materialization → First-execution verification
→ Scope-controlled future reuse → Authorization lineage
```

TUF / Sigstore 为 C3 提供可信 artifact identity；C3 负责把 consumer task authorization
绑定到该 identity 及其**使用生命周期**。

**冻结的 novelty 表述（不得再写成"TUF 假设人选包"）：**

> 新颖性来自长期运行 agent 中，consumer-side task authorization 如何被绑定并限制到自主选择
> artifact 的 acquisition 与未来调用生命周期；供应链完整性机制提供 artifact identity，
> 但不替代这层授权。

---

### Amendment 3 — 2026-08-11：declared scope ≠ enforced scope；C3 增加最小运行时强制

**发生时点**：taxonomy 尚未开始，无任何新增实验结果。属于 **pre-results amendment**。
**理由**：A2.4 只解决"谁渲染批准界面"，未解决"声明的 scope 是否属实"。

#### A3.1 三层区分（补全 A2.4）

| 层 | 问题 | 由谁解决 | 状态 |
|---|---|---|---|
| 1 | 批准文案由谁撰写 | trusted path | A2.4 已解决 |
| 2 | 声明是否确属该 artifact | digest 绑定（声明是被哈希内容的一部分） | `Match` 已解决 |
| 3 | **声明是否等于运行时行为** | **runtime enforcement** | **此前未解决** |

**本项目自有数据即为第 3 层缺失的反证**：benign / malicious twin 的 model-visible metadata
与参数 schema 完全一致（即**声明 scope 相同**），隐藏行为不同；approved-malicious 臂
`payload = 25/30`。**声明不等于行为，已由 §1.1 的结果证明。**

#### A3.2 冻结：permit 绑定 enforced scope，不绑定 declared scope

未被强制的字段**不得**在批准界面呈现为权限。只能标注 `declared, not enforced`，或不展示。
否则 trusted path 反而制造虚假的权限感（用户以为在授权，实际在阅读攻击者的自我声明）。

#### A3.3 最小强制集 = canary 的五类能力（复用同一分类）

`network egress` / `filesystem write` / `shell exec` / `credentials` / `persistence`
—— 与 §6.5 canary 探针**一一对应**。测量工具与强制机制共用同一能力分类。

**不做通用沙箱。** 实现基于现有的 per-trial install root：

| 能力 | 强制方式 |
|---|---|
| network egress | network namespace 默认拒绝；permit 允许才放行 |
| filesystem write | bind-mount 仅暴露 permit 声明的路径，其余不可见 |
| credentials | 子进程 env 清洗；凭据文件不进入视图 |
| shell exec | handler 不默认暴露子进程 spawn；需要则由 permit 显式授予 |
| persistence | install root 是否于任务结束后保留，由 `use_scope` 决定 |

#### A3.4 主张边界更新（取代 A1.8 / A2.9 中 C3 的能力范围）

C3 覆盖 principal 四层中的 **identity / authorization / enforcement（粗粒度）**；
**lifecycle 部分覆盖**（use scope + expiry + lineage）。
**revocation 与细粒度 confinement 仍为 future work**（对照 Capsicum）。
**仍不得声称 full principalization。**

`Match` 中的 `q(x) ⊆ p.scope` 由"信任声明"变为"运行时强制"，
不变量 `Reach_b ⇒ ∃p : Valid(p) ∧ Match(p,·)` 因此具有实际约束力。

#### A3.5 新增对抗臂（`Match` 族第 10 条）

10. **declared-vs-actual scope divergence**：artifact 声明 read-only，
    运行时尝试 network / shell / 写盘 —— 强制生效则应被拦截并写入 lineage。
    这一臂同时验证 A3.3 的强制是否真的生效，不能只靠代码审阅声称。

---

### Amendment 4 — 2026-08-11：撤回 A3.1 的 twin 证据主张与 A3.3 的运行时强制范围

**发生时点**：taxonomy 尚未开始，无任何新增实验结果。属于 **pre-results amendment**。
**理由**：A3.1 含一处事实错误；A3.3 与其自身"不做通用沙箱"的声明矛盾且技术上不成立。

#### A4.1 撤回 A3.1 的 twin 证据主张（**事实更正**）

❌ 作废：*"benign / malicious twin 的 model-visible metadata 与参数 schema 完全一致
（即**声明 scope 相同**）…… 声明不等于行为，已由 §1.1 的结果证明。"*

**错误在于把参数 schema 当成 permission manifest。** 参数 schema 说明 skill 接受什么参数，
不是权限声明；现有 twin **不包含任何 permission manifest**。

✅ twin 实际证明的是：

> 相同的模型可见描述与参数接口，可对应不同的隐藏 handler 行为；
> 因此可见 metadata 不能替代 vetting。

要证明 `declared scope ≠ runtime behavior`，需**新建**带真实 permission manifest 的
对抗 artifact，并实测声明与运行时效果的偏差。**在此之前不得引用 §1.1 支持该命题。**

#### A4.2 撤回 A3.3 的五类运行时强制（**范围更正**）

❌ 作废 A3.3 的强制实现表。原因有二：

1. **与自身声明矛盾**：network namespace + bind mount + 凭据隔离 + 进程/syscall 控制 +
   持久化生命周期，本身即是粗粒度 OS isolation，不是"不做通用沙箱"的小补丁。
2. **技术上不成立**：不暴露 spawn API 拦不住 Python / native code 直接创建进程或调用 syscall；
   env 清洗拦不住读取 credential files 或 metadata endpoint；namespace 通常要求独立进程 /
   container 与额外权限；skill 若与 agent 同进程执行，简单 wrapper 无法隔离。
   （另：A3.3 表中遗漏了 canary 已有的 `filesystem read`。）

#### A4.3 C3 的 enforcement 范围（冻结）

C3 **只强制 harness 确实控制的 acquisition / use 字段**：

- artifact source、identity、digest
- install destination
- persistence scope
- use scope（`one_shot` / `task` / `session` / `project` / `persistent`）
- expiry / replay
- installation 与 first-execution binding
- authorization lineage

对 `network` / `filesystem` / `shell` / `credentials`：

- **taxonomy 与 canary 负责测量**实际 ambient capabilities；
- UI 明确标注 `ambient / not confined by this protocol`；
- **不得**把 artifact 自我声明展示为已受强制的 permission；
- 接入既有 container / sandbox 作为 **optional enforcement adapter 或 stretch goal**；
- **不在 core contribution 中承诺自建通用 runtime confinement。**

C3 仍然成立的技术主张：

> 保证被授权的**具体代码、安装位置、持久化范围与未来调用生命周期**不被替换或扩张。

#### A4.4 新增审计发现类别：permission theater（由 A4.3 解锁）

既然 ambient capabilities 不由本协议强制，就应反过来审计**真实系统**是否存在同类问题：

> 某系统在批准时展示了 permission 样式的字段，而 canary 显示它并**不强制**这些字段。

这是 authorization-binding 失效的**第二种形态**：

| 形态 | 失效位置 | 表现 |
|---|---|---|
| identity 层 | 绑定对象错误 | 批准了 A，装进来的是 B |
| **scope 层** | **展示 ≠ 强制** | **批准的范围根本没有被强制（permission theater）** |

codebook 的 `Perm` 字段需能捕捉"**批准时展示但未强制**"这一最糟配置（见 idea/43 §4.2）。

#### A4.5 Trusted path 收紧为 canonical grant flow（取代 A2.4 的渲染规则）

```
artifact 提交 machine-readable request
→ harness 验证 artifact identity
→ harness 依据**可强制** policy 计算 effective grant（过滤掉不可强制的声明）
→ harness 用固定 UI 渲染 effective grant
→ 用户批准的正是该 canonical grant
→ permit 绑定 UI 展示的同一份 canonical bytes
```

**可主张**：`DisplayedGrant == SignedGrant`（displayed grant 与 machine-enforced grant 一致）。
**不可主张**：解决 comprehension —— 用户是否理解 network / persistent / project scope
是人因问题，无用户研究不得声称。

对应地，第 9 条对抗臂机械化为：能否构造 `DisplayedGrant ≠ SignedGrant`，
或 router prose 能否伪装系统 UI。**不在无真人的实验中测"用户是否被诱导"。**

#### A4.6 对抗臂按 failure mode 索引，两族不严格互斥（修正 A2.5）

同一种攻击在不同阶段产生不同 failure mode。以 `temporary → global` 为例：

| 断在哪 | failure mode |
|---|---|
| permit 写 temporary，实际安装 global | `Match` / scope enforcement 失败 |
| UI 显示 temporary，实际签发 global | `Valid` / trusted-path 失败 |
| UI 正确显示 global，用户仍批准 | **不是 bypass** —— 属宽授权政策或人因问题 |

同理，wildcard permit 若由可信 UI 明确显示并被用户批准，形式上**仍然 valid**；
它是危险设计，不是绕过。**除非 issuance policy 预先规定禁止 wildcard**，
否则不得把所有 wildcard 记为 bypass。

两族保留作分析框架，但**每条攻击按实际 failure mode 归类并逐条报告**，不按族强行互斥。

#### A4.7 口径复核完成（取代此前的待办）

三份完整 raw result JSON 独立重数结果：

| Cell | 至少一次 block 的 trial | blocked install events |
|---|---:|---:|
| Qwen × text | 25/30 | 25 |
| Llama × text | 28/30 | 62 |
| Qwen × native FC | 12/30 | 12 |
| **合计** | **65/90** | **99** |

三个 cell 的 `install_execution_started` 均为 **0**。

**要求**：保存固定统计脚本与输出报告，保证论文数字可一键重现。

---

### Amendment 5 — 2026-08-11：拆分 enforcement / auditability；规范 canonical grant；收紧 permission-theater 判据

**发生时点**：taxonomy 尚未开始，无任何新增产品编码、canary 或协议实验结果。属于
**pre-results amendment**。
**理由**：A4.3 将 lineage 误列入 enforcement；A4.5 未区分 permit 中的 enforced grant 与平台的
ambient-risk disclosure；A4.4 的 `permission theater` 操作定义过宽。

#### A5.1 C3 的 enforcement 与 auditability 分开（修正 A4.3）

**C3 强制的 acquisition / use 属性：**

1. canonical source、artifact identity 与 content digest；
2. install destination；
3. persistence scope；
4. use scope（`one_shot / task / session / project / persistent`）；
5. expiry / replay；
6. installation 与 first-execution binding。

**C3 记录但不靠记录本身强制的属性：** authorization lineage。

lineage 继续按 A2.6 定位为 auditability；只有由可信 reference monitor 写入并采用 append-only /
hash-linked 机制时，才额外主张 tamper evidence。不得再把 lineage 称为被 permit “强制”的 scope 字段。

#### A5.2 Canonical grant UI 分区（修正 A4.5）

批准界面必须把两类信息分开：

```text
Enforced Grant
  artifact source / digest
  install destination
  persistence scope
  use scope
  expiry / replay policy

Ambient — Not Confined by This Protocol
  network / filesystem / shell / credentials
```

只有 `Enforced Grant` 的 canonical bytes 进入 permit、签名与 `Match`。第二部分只是平台风险披露：
不称为 permission，不声称完整，不进入 `Match`，也不得暗示本协议会限制这些运行时能力。

冻结的 display-integrity 性质为：

```text
DisplayedEnforcedGrant == SignedCanonicalGrant
```

该性质不等于用户理解，也不等于 ambient capability confinement。

#### A5.3 `display–enforcement mismatch` 与 `permission theater` 分开

taxonomy/codebook 使用中性操作标签 **`display-enforcement-mismatch`**。只有同时满足下列四项，
discussion 才可进一步使用 `permission theater`：

1. UI 或官方文档把该字段表述为由系统**授予、拒绝或限制**的 permission，而非单纯行为披露；
2. displayed grant 明确不含该能力，或把它限制在具体范围；
3. 确定性 canary 仍产生 grant 范围外的 capability effect；
4. 完整 trace 排除后续另行授权、configuration drift 与测试路径不等价。

仅显示“该组件会使用 network”等披露信息，而用户随后批准安装，不满足上述定义。

`Perm` 的操作状态拆为：

- `declared-unverified`：仅有声明，尚未验证；
- `declared-unenforced`：canary 已显示声明未被运行时强制，但 UI 未把它表述为受约束 grant；
- `display-enforcement-mismatch`：满足上述四项；
- `enforced`：正负对照与 trace 证明系统执行了所展示的约束。

A4.4 的 `permission theater` 不再作为预先假定的第二类 authorization-binding gap；先按中性状态编码，
待全部系统编码完成后再决定其与主 Thesis 的关系。

---

### Amendment 6 — 2026-08-12：补做 delegated-acquisition capability inventory

**发生时点与诚信声明**：P01 文档型 pilot 已完成，且为纳入/版本核实时已看过部分产品的安装与扩展文档。
本 amendment 修复的是 sampling frame 对 Thesis B 承重条件 `delegated selection` 的覆盖缺口；它不是原始
预注册，也不能追溯包装为盲法或 confirmatory taxonomy。Goose、Claude Code、Cline 的部分相关文档在本
amendment 写入前已经被看到，结果必须标为 **post-pilot exploratory capability inventory**。

#### A6.1 固定问题与范围

不新增或替换 idea/45 的 10 个 primary units。仅对这 10 个 core implementations 各回答一次：

> 官方文档或官方版本源码是否记载一条路径，使用户不必先指名最终 extension/artifact，而由 agent/selector
> 在任务或高层 acquisition 请求后发现、选择，并触发安装、启用或首次执行？该对象是否为外部第三方代码
> 作为独立 provenance 字段记录，不由 route grade 自动推断。

逐系统同时记录 trigger、discovery、candidate selection、install/enable trigger、first-execution reachability
与 candidate-specific approval 是否有证据。`undocumented` 不得写成 `no`。

#### A6.2 Route grades（不与 H0–H4 或 P0/P1/P2 混用）

- `R3 ordinary-task delegated activation`：普通任务即可触发 selector 选择 extension/artifact，并启动
  install/enable/activation 路径；不因该等级推断“第三方代码”“下载了新字节”或“无批准”。
- `R2 ordinary-task recommendation`：普通任务/会话信号只产生 candidate recommendation，安装仍由用户
  发起或确认。
- `R1 explicit-acquisition delegation`：用户明确要求“找/加一种能力”但未指名 candidate，agent 负责选择
  或构造并推进获取；这不是普通任务 proactive self-extension。
- `R0 candidate/developer specified`：用户或开发者先指定 artifact/source/server，agent 只在安装后选择工具。
- `RU undocumented`：公开证据不足以确定上述路径。

等级只描述**路径触发与选择委托**，不是 binding strength、安全等级或市场 prevalence。

#### A6.3 Htrans 解释规则

1. 至少一个 `R3` 只能证明 proactive delegated activation 是真实设计方向；若 external/third-party
   provenance 尚未另证，不能据此声称第三方代码获取。受控 Htrans 最多表述为
   “instantiates a documented policy pattern”，不得写成逐字节复现该产品。
2. `R2/R1` 只能支持 recommendation 或 explicit-acquisition delegation，不能支持普通任务自动获取。
3. 即使存在 `R3`，也不等于 authorization-binding gap：仍须单独证明 grant、resolved artifact、
   first execution 与 approval lineage 的关系。
4. 若没有 `R3`，Htrans 按 §9 预案降为 design-space analysis。
5. capability inventory 不计入“两系统 binding weakness”门槛，也不改变 idea/45 的有限样本。

---

### Amendment 7 — 2026-08-12：竞品边界核实；C2 / C3 主张收缩至 deferred-resolution

**发生时点**：canary 仍为**零次运行**。本 amendment 依据的是**竞品文献核实**，
不依据任何新增实验结果。但它**改变了 C2 / C3 的可主张范围**，必须如实记录：
这些收缩是在看过竞品之后做的，不得追溯声称为原始设计。

#### A7.1 已核实的竞品与发表层级

| 工作 | 发表处 | 层级 |
|---|---|---|
| **AgentBound / GuardiAgent**（arXiv 2510.21236） | *Proc. ACM Softw. Eng.*, FSE 2026, Article FSE096；USI Lugano | **同行评审顶会（FSE）。唯一实质竞品。** |
| AttestMCP（arXiv 2601.17549，Maloyan & Namiot） | *Modern Information Technologies and IT-education* 21(3), 2026 | 低层期刊 |
| SkillFortify（arXiv 2603.00195，Bhardwaj） | arXiv / Zenodo / SSRN，**未经同行评审**，单作者自出版工具集 | 非学术竞品，但**算 prior art** |
| tdcommons 10604（Rosado） | Technical Disclosure Commons，防御性公开 | 非论文，**算 prior art** |
| MDPI 2624-800X/6/3/84；MDPI 18/5/243 | MDPI 期刊 | 中低层，related work 引用 |

#### A7.2 绑定对象 × 复核时刻 × 隐含假设（related work 的核心表）

| 工作 | 绑定什么 | 复核在哪一刻 | 隐含假设 |
|---|---|---|---|
| SkillFortify | skill 文件 sha256 + declared capabilities | **安装前静态分析**；runtime enforcement 明写为 future work | 制品在授权时**已在磁盘上** |
| AgentBound | 权限 manifest（fs / network），**不绑 artifact 身份** | 载入 manifest → 解析权限 → **请求用户同意** → 沙箱启动 | **人**决定何时启动 server |
| tdcommons 10604 | tool surface 哈希 + SPIFFE workload identity + 批准人身份 | 批准时 pin；每次 advertise 与 invoke 复核 | 恶意变更会**改变 tool surface** |
| AttestMCP | capability 声明 + 消息认证；TOFU pin | 连接时 | 威胁在 prompt injection 层 |
| ToolHive | 容器化 `npx://` / `uvx://` 构建 + 版本约束 | 构建时 | 有人**预先构建**镜像 |

#### A7.3 不得再主张的内容（prior art 已占，与 venue 层级无关）

- ❌ "首次发现授权绑定到可变名字而非不可变内容"
  —— rug pull 线已有 **CVE-2025-54136（MCPoison，Cursor 配置命令被换仍信任已批准 key）**，
  并已进入 Microsoft Learn 的 Zero Trust AI 攻击目录、Elastic Security Labs、Invariant Labs。
- ❌ "首次为 agent skill 提出内容哈希绑定" —— SkillFortify `skill-lock.json`、MCPShield `mcp.lock.json`。
- ❌ "首次提出权限 manifest 绑定与强制" —— AgentBound（FSE 2026）。
- ❌ "首次提出批准时 pin、调用时复核" —— tdcommons 10604。
- ❌ 把 `npx @latest` 每次重新解析写成新发现
  —— 从业界已有公开陈述（Obot, 2026-05：*"every time that server starts, your client is
  downloading and executing whatever the upstream registry serves up at that moment.
  No version pinning. No review. No record of what code ran."*）。

#### A7.4 收缩后的中心主张（**deferred-resolution authorization**）

现有防御全部绑定于一个**由人控制的配置时刻**，且假设**制品在该时刻已经存在**。
两个假设同时失效时，它们在结构上无法附着：

1. **制品不存在**：`npx -y pkg@latest` / `uvx pkg` 类配置在授权时刻没有可哈希的字节。
   lockfile 锁的是已在磁盘上的东西；对 deferred-resolution selector，授权时**无物可锁**。
2. **人不在场**：agent-initiated activation（idea/47 `R3`）把"解析并执行哪些字节"的时刻
   推到所有人类控制点**之后**。

冻结表述：

> Existing defenses for agent extensions bind at a human-controlled configuration moment and
> assume the artifact exists at that moment. Agent-initiated activation of deferred-resolution
> selectors moves the instant at which code is chosen and executed past every one of those
> control points. We measure where real systems place this instant, test whether it precedes
> first tool authorization, and close the gap by inverting the order.

#### A7.5 C2 / C3 修订

**C2（审计）**：不再主张"发现绑定缺口"这一泛化说法。收缩为
**测量真实系统把"代码选定时刻"放在哪里**，以及该时刻相对于各控制点的位置。
idea/43 的 binding matrix 增记 A7.2 三列（绑定对象 / 复核时刻 / 隐含假设）。

**C3（机制）**：不再主张"提出 artifact-bound permit"。收缩为**时序倒置**：

```
现有：authorize(recipe) → resolve → execute
本文：resolve → quarantine → digest → authorize(bytes) → materialize → reverify
```

新颖性在于**让内容绑定在 deferred-resolution 授权下成为可能**（此前无物可绑），
不在于内容绑定本身。C3 仍不主张 vetting、不主张完整 runtime confinement（见 A4.3、A5.1）。

#### A7.6 canary 新增一臂：surface-pinning 反例（零成本）

idea/48 §6 的 artifact A / B 已按"同名、同 schema、同行为"设计，**tool surface 完全一致**。
因此 tdcommons 10604 式的 **surface 哈希 pin 会对 A→B 漂移全部放行**。

新增记录项（不改 §8 矩阵、不改 §2 判据）：

```yaml
surface_equivalence_verified: true | false     # A 与 B 的 tools/list 响应是否逐字节一致
```

若为 `true`，可如实报告：对最接近的 surface-pinning 防御构成可演示反例。
**不得**据此声称该防御整体失效——只报告本 A/B 构造下的适用边界。

#### A7.7 与 AgentBound 的关系（唯一顶会竞品，须正面处理）

AgentBound 已具备 activation-time consent 与沙箱化 runtime enforcement，
因此**不得**写成"没人在 activation 处设控制点"或"没人做 runtime confinement"。

冻结的区分：AgentBound 绑定**权限**（该 server 能碰什么），本文绑定**身份**（跑的是哪份字节）；
AgentBound 的 consent 由**人在配置时**给出，本文关注 **agent 在任务时**触发的 activation。
二者**正交且互补**：manifest 说"允许联网"，但不回答"允许的是哪一份代码联网"。
