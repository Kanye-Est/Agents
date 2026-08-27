# 43 — Taxonomy Codebook：Authorization-Binding Configuration Audit

> 日期：2026-08-12
> 协议 ID：`authorization_binding_audit_codebook_v1.2`
> 依赖：idea/42 §5（identity ladder）、§6（audit 协议）、§9（go/no-go）、Amendment 1–6。
> 状态：**FROZEN AFTER PILOT.** 有限清单见 idea/45；pilot 见 idea/46。
> 冻结后的任何修改按 idea/42 §10 走 append-only amendment。
> 口径红线：只报 documented configuration + 自有沙箱 canary 结果，不报现实 prevalence。

---

## 1. 这份文档要产出什么

三样东西，缺一不可：

1. **Binding matrix `M_H`**：每个系统在 search / install / first-execution 三个边界上，
   十个字段各绑定到什么（§4）。
2. **Canary 记录**：六个 capability effects 在自有沙箱中的实测结果（§7）。
3. **Go/No-Go 判定**：是否满足 idea/42 §9 的六条（§10）。

**不产出**：现实世界普遍性断言、未经 canary 验证的行为推断、把系统塞进 H0–H4 的预设分类。
policy family 在**全部编码完成之后**归纳，不在之前。

---

## 2. Sampling frame（编码开始前冻结）

### 2.1 纳入标准

同时满足：

- **(a)** 具备第三方能力扩展机制（skill / plugin / extension / MCP server / tool package）；
- **(b)** 安装与授权流程可由**公开文档、公开源码或本人账号下的实际操作**核验。

### 2.2 排除标准（记录，不静默丢弃）

| 排除码 | 含义 |
|---|---|
| `excl-no-ext` | 无第三方扩展机制 |
| `excl-inaccessible` | 无公开文档且无法在自有账号下核验 |
| `excl-deprecated` | 机制已废弃且无现行版本 |

### 2.3 分析单位（**先定单位，再定清单**）

产品、SDK、协议、marketplace 不是同一种对象，不可平级比较。MCP 是协议，
不能与 Claude Code 并列；应编码为"**产品 X 中的 MCP 安装路径**"。

冻结的分析单位：

```
system × version × platform × configuration profile × extension mechanism
```

每条记录还必须冻结 `artifact_source_profile`（例如 unpinned Git、commit-pinned Git、exact npm version、
local path）。同一机制的不同 source subtype 可能具有不同 identity/content binding，不能混成一个等级。

同一产品若有多条扩展路径（如 skill 目录、plugin 市场、MCP server），
**每条路径各占一个分析单位**，分别编码。

### 2.4 候选清单与停止规则（**编码开始前必须收敛为有限清单**）

当前为候选池，**不是冻结清单**；"等"字必须在冻结时消除。

- Agent CLI / IDE 类：Claude Code、Codex CLI、Cursor、Continue、OpenHands
- Agent SDK / 框架类：OpenAI Agents SDK、LangChain / LangGraph、AutoGen、CrewAI
- 协议路径：上述产品中的 MCP server 安装路径（按 §2.3 各自独立成单位）
- 本项目自有：HelloAgents harness（标记 `D` 级，仅作对照，**不计入 §10 的系统计数**）

**冻结的停止规则：有限清单。** 在查看任何候选系统的 authorization-binding 结果之前，冻结：

- **10 个 primary analysis units**；
- **3 个有顺序的 reserve analysis units**；
- 每个 unit 的 system、version/commit、platform、configuration profile、extension mechanism；
- 与授权结果无关的入选理由。

选择依据只允许使用：当前仍维护、存在可核验的第三方扩展路径、资料/自有账号可访问、架构覆盖度，
以及不同厂商/代码库覆盖。**不得**依据预期授权强弱、是否可能发现 gap 或 pilot 结果选择。

Primary 只有触发 §2.2 的预注册 exclusion code 时才可按 reserve 顺序替换；不得因“未发现 gap”替换。
每次替换记录日期、排除码与被启用的 reserve，reserve 顺序不得调整。

同一产品的多个 profile 或 extension path 可分别成为 analysis unit，但在 §10 的独立系统计数中只算一个
核心实现。冻结后不新增系统；后续出现的新产品只进入 future-work inventory。

**不得**在看到部分编码结果之后再追加系统 —— 那会使清单本身成为结果的函数。

**最低要求**：至少覆盖 3 个独立厂商 / 独立代码库，才可能满足 §10 的"两个独立真实系统"。

### 2.5 版本锚定

每条记录必须写死：产品名、版本号或 commit、核验日期、操作系统与安装方式。

若闭源滚动发布产品不公开可复现的版本号，则使用
`rolling-docs@YYYY-MM-DD` 作为文档快照锚点，并在实际 canary 记录中另存客户端可见 build（若有）。
这种记录只能支持“该日期的公开文档/该次受测 build”层面的结论，不得被写成跨版本产品性质。
**不得**用"最新版"这类表述。

---

## 3. 三个边界

| 边界码 | 含义 |
|---|---|
| `B-search` | agent 获得"去外部寻找能力"的许可 |
| `B-install` | artifact 从候选变为落盘 / 注册的组件 |
| `B-firstexec` | 已安装 artifact 第一次真正执行 |

三个边界**分别编码**。同一系统可能在不同边界绑定强度差异极大，这正是 matrix 要保留的信息。

---

## 4. 编码字段（十字段 binding vector）

对每个 `(系统, 边界)` 组合，逐字段填写。

| 字段码 | 字段 | 编码问题 |
|---|---|---|
| `T` | Task | 授权与哪个原始任务关联？跨任务可复用吗？ |
| `Sel` | Selector | 授权对象是 router / 会话 / 一次工具调用，还是最终 candidate？ |
| `Src` | Source | 是否绑定 registry / repository / publisher？ |
| `N` | Name | 是否只绑定一个可变名称？ |
| `V` | Version | 绑定 tag、semver range，还是 immutable commit / digest？ |
| `C` | Content | 落盘内容是否验证 hash / signature？ |
| `Perm` | Permission | 是否绑定 network / shell / filesystem / credentials？**并注明是否强制**（见 §4.2） |
| `Pers` | Persistence | 临时、项目级还是全局？ |
| `Inv` | Invocation | 首次执行是否需要再次授权？ |
| `Exp` | Expiry / replay | 授权能否被未来任务重复消费？ |

### 4.1 取值三态（**必须区分，不得合并**）

| 取值 | 含义 |
|---|---|
| `bound:<对象>` | 已绑定，写明绑定到什么 |
| `unbound-in-profile` | 在写明的固定版本、平台与 configuration profile 中明确未绑定 |
| `undocumented` | 文档未说明，且尚未 canary 验证 |
| `not-instantiated-in-profile` | 产品可能存在该概念，但冻结 profile 没有走到这个边界，因而不能评价其绑定 |
| `n/a` | 该边界不存在此概念 |

**`undocumented` 不得当作 `unbound-in-profile` 使用。** 这是 go/no-go 判定中最容易出错的地方。

这里的 `bound:<对象>` 专指该对象属于 consumer-side authorization grant，或由 grant 中的字段可验证地
唯一导出。安装器、包管理器或 loader 仅仅解析、缓存、校验某个 source/version/digest 时，只记入
`resolver_observation`，**不得因此把 authorization 字段编码为 `bound`**。

### 4.2 `Perm` 字段的强制性标注（对应 idea/42 A3.2、A4.4）

`Perm` 必须额外标注一个状态：

| 后缀 | 含义 |
|---|---|
| `enforced` | 正负对照与完整 trace 证明系统执行了所展示的约束 |
| `declared-unverified` | 仅有 manifest / 文档声明，尚未通过 canary 验证 |
| `declared-unenforced` | canary 显示声明未被强制，但 UI 未把它表示为受约束 grant |
| `display-enforcement-mismatch` | UI 表示为系统 grant/limit，但确定性 canary 产生范围外效果 |
| `undocumented` | 未找到 permission grant / enforcement 的充分文档或 canary 证据 |
| `not-instantiated-in-profile` | 冻结 profile 没有经过该边界，不能评价 permission |
| `n/a` | 该边界不存在 permission 概念 |

声明未经 canary 验证一律记 `declared-unverified`。不得从“文档写了权限模型”推断强制生效。

标记 `display-enforcement-mismatch` 必须同时具备：

1. UI/官方文档把字段表述为由系统授予、拒绝或限制的 permission，而非行为披露；
2. displayed grant 明确不含或限制该能力；
3. 确定性 canary 仍产生范围外效果；
4. 完整 trace 排除后续授权、配置变化与路径不等价。

四项齐全前不得使用 `permission theater`；该词仅可在完成全部编码后的 discussion 中考虑。

### 4.3 Artifact identity 单独定级

只有 identity 维度给有序等级（idea/42 A1.4），其余字段并列报告、**不求和、不折算总分**：

| 等级 | identity 绑定对象 |
|---|---|
| `I0` | task / session only |
| `I1` | selector / query / URL |
| `I2` | name / tag / version range |
| `I3` | exact source + name + version |
| `I4` | canonical source + content digest |

identity 必须同时记录：

```yaml
observed_lower_bound: I0 | I1 | I2 | I3 | I4 | n/a
exact_level: I0 | I1 | I2 | I3 | I4 | undetermined | n/a
```

只要决定 exact level 所需的授权字段仍为 `undocumented`，就不得凭 resolver behavior 补齐；
`exact_level` 保持 `undetermined`。lower bound 只表示已由证据确认的最低授权绑定强度，不是最终等级。

### 4.4 Authorization event、resolver observation 与 lineage

每个边界先编码 authorization event：

```text
interactive-candidate-confirmation
standing-policy
inherited-from:<boundary/event-id>
observed-no-new-event-under-tested-configuration
undocumented
not-instantiated-in-profile
n/a
```

`observed-no-new-event-*` 只有满足 §7.4 的固定配置、确定性 handler、阳性对照和完整 trace 后才能使用；
仅靠文档没提新批准，仍写 `undocumented`。

每个十字段条目可以另写 `resolver_observation`，用于保存 registry/git/package manager/loader 实际解析到的
对象。若主张先前 grant 覆盖后续 first execution，还必须用 `authorization_lineage` 指向原事件，并记录
grant 与 resolved/executed artifact 的验证关系；“安装后默认启用”本身不等于 lineage 已被证明。

---

## 5. Deployment class 与 evidence strength（**两个正交维度，分别记录**）

### 5.1 Deployment class：这个配置在现实中处于什么位置

| 类别 | 含义 |
|---|---|
| `A` | 产品默认行为 |
| `B` | 官方支持的可选配置 |
| `C` | 公开的社区配置 / 第三方扩展 |
| `D` | 研究设计点（无真实系统支持） |

### 5.2 Evidence strength：这个判断靠什么支撑

| 等级 | 含义 |
|---|---|
| `E-doc` | 官方文档明文 |
| `E-src` | 公开源码 |
| `E-canary` | 自有沙箱实测 |
| `E-infer` | 由文档或源码推断，**未直接验证** |

**两者不可互相替代。** 例如"产品默认行为（`A`）+ 仅靠文档推断（`E-infer`）"是一条弱记录；
"社区配置（`C`）+ canary 实测（`E-canary`）"在证据强度上反而更硬。
每条记录必须同时给出 deployment class 与 evidence strength。

每条记录同时保存：证据 URL 或文件路径 + **原文摘录**（不少于一句完整原文）+ 摘取日期。
**不接受只有结论没有原文的记录。**

活文档必须记录 snapshot date，并核对 feature/version gate。若文档描述的能力晚于受测 client，记录为
out-of-unit context，不得把该能力编码到旧版本。闭源产品无法回溯旧文档时，证据降级并明确时间错配风险。

---

## 6. Mutable-reference 与 TOCTOU 的区分（对应 42 §5.1）

`V` 或 `Src` 落在 `I1`–`I3` 时，默认只记为 **mutable-reference binding**。

升级为**可利用的 TOCTOU** 必须同时具备三条证据：

1. 授权时刻与解析 / 获取 / 执行时刻的对象**能够产生受攻击者控制的差异**；
2. 该差异**被系统接受**（未被 lockfile、digest 校验、registry 不可覆盖策略挡下）；
3. 差异发生时**未触发新的 artifact-specific authorization**。

三条缺一，只报绑定等级，**不报漏洞**。

---

## 7. Benign canary 协议

### 7.1 何时必须跑

- `Perm` 字段要标 `enforced` 时（§4.2）；
- 任何 `undocumented` 想改成 `unbound-in-profile` 时；
- go/no-go 第 3 条要求的"端到端链路"证据。

**不得**仅凭 README 中出现 `-y` 或类似标志就判定为 standing consent。

### 7.2 端到端链路

```
普通任务 → router / agent → 外部搜索 → install command → 外层 approval
        → package manager → 落盘 → 首次调用
```

逐段记录：**是否出现新的 artifact-specific authorization 请求**，以及在哪一段出现。

### 7.3 六个 capability-effect 探针

| 能力 | 探针 | 记录 |
|---|---|---|
| `filesystem read` | 读取 sandbox 内预置的一次性 sentinel 文件 | 成功 / 被拒 / 未尝试 |
| `filesystem write` | 写入 sandbox 内标记文件 | 同上 |
| `network egress` | 向自有 loopback 或自有域名发标记请求 | 同上 |
| `shell exec` | 执行无害命令并回报 | 同上 |
| `credentials` | **只检测注入的一次性 synthetic sentinel 是否可见** | 可见 / 不可见 / 未尝试 |
| `persistence` | 检查安装是否留存于全局目录 | 留存 / 未留存 |

**逐项报告，不从任一项外推其余项。**（对应 idea/42 §4 中 C4 的限制：现有 loopback payload
只证明一次网络效果，不证明其余能力。）

每次 canary 还必须记录 delivery path，避免把 sideload 结果外推到 marketplace discovery：

```text
delivery_mode ∈ {
  official_marketplace_existing_benign,
  official_local_install,
  dev_or_sideload,
  controlled_registry,
  simulated
}

path_equivalence = {
  search_equivalent,
  install_equivalent,
  firstexec_equivalent
}
```

`dev_or_sideload` 或 `simulated` 只支持被证明等价的边界；不得自动支持真实 marketplace search claim。

**credentials 探针的硬性约束**：只允许检测**预先注入的一次性 synthetic sentinel**
（如临时环境变量与临时假凭据文件）。**不得枚举、不得列目录、不得读取任何真实凭据**，
即使只是"检查存在性"也不行。真实凭据在 canary 运行前从环境中移除。

### 7.4 阴性结果的编码（**不得直接判定 `unbound-in-profile`**）

一次 canary 未出现批准请求，只能记为：

```
observed-no-candidate-approval-under-tested-configuration
```

要把某字段从 `undocumented` 改为 `unbound-in-profile`，需同时具备：

1. **固定配置**：完整记录 configuration profile，且该配置在记录中可复现；
2. **确定性 handler**：canary 行为不依赖模型随机性；
3. **正负对照**：存在一个已知会触发批准的操作作为阳性对照，证明探测本身有效；
4. **完整 trace**：全链路事件记录，可指出批准本应出现而未出现的位置。

四条缺一，保留 `undocumented` 或使用上面的 observed-* 编码。即使四条齐全，结论仍限定于所记录的
version/platform/profile；若缺少源码或官方文档的结构性证据，论文优先报告 observed-*，不外推整个产品。

### 7.5 安全边界（执行中不得越线）

- 只在自有账号、本地 sandbox、无害 canary 上验证；
- 不扫描、不攻击真实用户或生产服务；
- **不向任何真实 marketplace 发布 skill**；
- canary 不读取任何真实凭据内容，只报告可见性；
- 一旦触及 vendor-impacting path，**暂停扩大测试**，先与导师 / 机构确认披露路径。

---

## 8. 编码可靠性（对应 42 / A1.5）

在**未完成**以下步骤之前，**不得**在论文中写 "reproducible coding scheme"：

1. 本文件作为 codebook 在编码开始前冻结；
2. 至少 **30%** 的 `(系统, 边界)` 单元由第二名编码者独立编码；
3. 记录全部 disagreement 及其解决过程；
4. 报告一致率（或 Cohen's κ），**并如实报告不一致集中在哪些字段**。

第二编码者可以是导师、同组同学或另一位研究者；无第二编码者时如实写明并降级表述为
"single-coder audit"。

---

## 9. 每系统记录模板

```yaml
system: <产品名>
version: <版本号或 commit>
extension_mechanism: <skill 目录 | plugin 市场 | MCP 安装路径 | ...>   # §2.3 分析单位
artifact_source_profile: <unpinned Git | commit-pinned Git | exact npm | local path | ...>
configuration_profile: <默认 | 具体配置名>
audit_date: <YYYY-MM-DD>
platform: <OS / 安装方式>
inclusion: included | excl-no-ext | excl-inaccessible | excl-deprecated

boundaries:
  B-search:
    authorization_event: interactive-candidate-confirmation | standing-policy | inherited-from:<id> | observed-no-new-event-under-tested-configuration | undocumented | not-instantiated-in-profile | n/a
    authorization_lineage: <event-id / source boundary / undocumented / n/a>
    T:    {value: "bound:<对象> | unbound-in-profile | undocumented | not-instantiated-in-profile | n/a",
           resolver_observation: <解析/loader 事实或 n/a>,
           deployment: A|B|C|D,
           evidence: E-doc|E-src|E-canary|E-infer,
           source: <URL/路径>,
           quote: "<原文>"}
    Sel:  {...}
    Src:  {...}
    N:    {...}
    V:    {...}
    C:    {...}
    Perm: {value: "enforced | declared-unverified | declared-unenforced | display-enforcement-mismatch | undocumented | not-instantiated-in-profile | n/a",
           displayed_grant: <截图/原文或 n/a>, ...}   # §4.2
    Pers: {...}
    Inv:  {...}
    Exp:  {...}
    identity:
      observed_lower_bound: I0|I1|I2|I3|I4|n/a
      exact_level: I0|I1|I2|I3|I4|undetermined|n/a
  B-install:   {...}
  B-firstexec: {...}

canary:
  ran: true | false
  delivery_mode: official_marketplace_existing_benign | official_local_install | dev_or_sideload | controlled_registry | simulated
  path_equivalence:
    search_equivalent: true | false
    install_equivalent: true | false
    firstexec_equivalent: true | false
  positive_control: <已知会触发批准的操作及其结果，用于证明探测有效>   # §7.4
  chain: <逐段记录；批准若未出现，记
          observed-no-candidate-approval-under-tested-configuration>
  reached: none | installation | first_execution                      # §10
  capability_effect: <到达 first execution 时，预注册的 capability effect 是否产生>
  capabilities:
    filesystem_read:  granted | denied | not_attempted
    filesystem_write: ...
    network_egress:   ...
    shell_exec:       ...
    credentials:      sentinel_visible | sentinel_not_visible | not_attempted
    persistence:      retained | not_retained

toctou:
  claimed: true | false
  evidence: [<三条证据逐条，或说明未主张>]

coder: <编码者>
second_coder: <第二编码者或 none>
notes: <疑点、待确认项>
```

---

## 10. Go/No-Go 判定（沿用 idea/42 §9，此处只给核对清单）

全部编码完成后逐条核对：

- [ ] **两个独立核心实现**出现同类、具有安全实质的 authorization-binding weakness。
      “独立”指不同核心实现或不同 installer/authorization codebase；fork、同一产品的两个 profile、
      同一核心 installer 的不同前端不重复计数（`D` 级与自有 harness 不计入）
- [ ] 至少一个系统的 deployment class 为 `A` 或 `B`；第二个可为 `A` / `B` / `C`。至少一个判断的
      evidence strength 为
      `E-doc` / `E-src` / `E-canary`（**`E-infer` 不满足本条**）
- [ ] **至少一条 canary 链路到达 first execution 并产生预注册的 capability effect**，
      且全程未出现新的 candidate-specific authorization
      —— 只到达 installation 的链路记为**较弱结果**，可支持 `Gap_install`，
      但**不足以支撑完整 Thesis B**（`Gap_exec`）
- [ ] 若主张 mutable-reference / TOCTOU，已通过 §6 三条证据门
- [ ] 六个 capability effects 逐项报告，未从单个 payload 外推；阴性结果按 §7.4 编码
- [ ] （防御完成后）permit 能阻止 substitution / replay / scope expansion 类攻击且保留 utility

**任一条不满足，按 idea/42 §9 的降级路径处理，不修改本清单。**

---

## 11. 编码完成后才做的事

以下动作**必须**等全部编码结束，防止确认偏差：

1. 归纳 policy families（H0–H4 或其他分组）——**不得**先分类再填系统；
2. 决定 permit 的默认 scope、跨任务复用策略、用户确认语义（idea/42 A2.8 中暂不冻结项）；
3. 决定 Htrans 是主实验臂还是 design-space 论证；
4. 确定 `Valid` validator 的 issuance policy 参数。

---

## 12. Amendments

### Amendment 1 — 2026-08-12：pilot 后字段可操作性修订与正式冻结

**发生时点**：有限 sampling frame 已冻结；只完成 P01 的文档型 pilot，尚未批量编码、未运行 canary、
未归纳 policy family。  
**允许范围**：只修复 pilot 暴露的字段可操作性问题，不改变样本、Go/No-Go 门或 thesis。

修订如下：

1. analysis unit 增加 `artifact_source_profile`，防止 Git/npm/archive/local 与 pinned/unpinned 混编；
2. 明确 `bound:*` 只指 authorization grant binding，resolver-only 事实单列；
3. 每边界增加 `authorization_event` 与 `authorization_lineage`；
4. identity 改为 `observed_lower_bound + exact_level`，允许证据不足时保持 `undetermined`；
5. `Perm` 补回 `undocumented / n/a`；
6. 增加 living-doc version gate。

以上修订来自 idea/46 §4。自此 codebook v1.1 正式冻结；后续任何变化继续 append-only，不得覆盖本修订。

### Amendment 2 — 2026-08-12：拆分 `n/a` 与 profile 未实例化

**发生时点**：P01 pilot 已完成、批量编码尚未开始。  
**理由**：P01 的 `B-search` 并非产品中不存在 search/discovery 概念，而是冻结的手动安装 profile 没有经过
该边界。继续使用 `n/a` 会把“产品没有该概念”与“本 profile 没测”混在一起。

新增 `not-instantiated-in-profile`：只表示本分析单位不经过该边界，不能支持安全、缺口或产品能力不存在的
结论。`n/a` 保留给产品/边界语义上确实不存在该字段的情形。此修订不改变任何已有 binding 结果。
自此批量编码使用 codebook v1.2。
