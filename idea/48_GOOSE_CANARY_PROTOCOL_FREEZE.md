# 48 — Goose Canary Protocol Freeze

> 日期：2026-08-12
> 协议 ID：`goose_activation_binding_canary_v1`
> 依赖：idea/42 Amendment 1–6；idea/43 v1.2；idea/45（P06）；idea/47（route grade `R3-activation`）
> 状态：**FROZEN BEFORE ANY RUN.** 本文件定稿之前未执行任何 canary run。
> 冻结后的任何修改按 idea/42 §10 走 append-only amendment，记录日期、理由与当时已见证据。
> 口径红线：只报本受测 build 与本冻结 profile 的结果；不报产品跨版本性质，不报行业 prevalence。

---

## 1. 诚信声明：冻结时已知与未知

### 1.1 已知（文档 / 源码层，来自 idea/47 与其引用）

- Goose v1.45.0 的 Extension Manager 默认启用；官方文档展示普通任务触发搜索、选择并启用 extension。
- `search_available_extensions` 搜索的是 Goose 配置中**已登记但未启用**的 extension，不是开放互联网市场。
- `manage_extensions` 找到配置后调用 `add_extension`；对 stdio extension，后者启动命令。
- 默认 Auto mode 对所有工具调用直接放行；Approve / Smart 模式对 `manage_extensions` 要求确认。
- 动态 activation 为 session-scoped，不写回默认配置；同一 session 内相同配置的 active extension 不重复启动；
  disable 后重新 enable 或新 session 会再次 spawn。
- MCP stdio 传输规范要求 client 启动 server 子进程；现行 SDK 为先 spawn、再完成 initialization、再 `listTools()`。

**以上均在本冻结之前看到，本协议不得声称对它们是盲设计。**

### 1.2 未知（本协议的前瞻对象）

**零次 canary 已执行。** 下列全部为未观测量，本文件对它们构成前瞻预注册：

- activation 批准框实际显示哪些字段；
- 用户选择后系统缓存的 effective grant 绑定到哪个键、什么范围、有无过期；
- admission 时系统是否解析或绑定过 artifact digest；
- activation 时解析出的 artifact 是否可与 admission 时刻不同且被接受；
- MCP initialization 阶段是否可产生预注册 capability effect，以及它与 first extension-tool approval 的先后；
- resolver 是否重新查询 registry 或命中缓存。

---

## 2. 研究问题与三级判据（冻结）

### 2.1 一句话

> 一次 extension admission 授权，在普通任务触发的 activation 与首次执行时，是否仍绑定同一个 artifact；
> 以及首次代码效果是否先于首次 extension-tool authorization。

### 2.2 三级判据（逐级升级，不得跳级）

**第一级 — 顺序结果（ordering result）**

```
InitEffect_timestamp  <  FirstToolApproval_timestamp
```

其中 `InitEffect` **必须**是预注册 capability effect（§5.2），**不得**用身份自报事件充当。
若该 cell 无 first-tool approval（如 Auto mode），记为
`no_first_tool_approval_in_profile`，顺序判据成立但须同时注明批准缺席。

**第二级 — Authorization-reference drift**

```
ResearcherObservedArtifact_admission = A
∧ RuntimeArtifact_activation        = B
∧ GrantBoundOnlyToMutableSelector
```

成立即可称 **authorization-reference drift** / **deferred-resolution authorization**。
**不得**称 TOCTOU。

**第三级 — TOCTOU 候选**

```
SystemCheckedOrBound(A)
∧ RuntimeArtifact = B
∧ AttackerControls(A → B)
∧ ¬NewArtifactGrant
```

四条齐备才进入 idea/42 §5.1 的三条件门复核；通过后方可称可利用 TOCTOU。

### 2.3 关键区分（写死，防止越级）

| 量 | 含义 |
|---|---|
| `researcher_observed_digest_at_admission` | 研究者在 admission 时刻自行解析得到的 digest，**实验 ground truth** |
| `system_bound_digest` | 系统实际纳入授权对象的 digest |

**二者不可互换。** 若 `system_bound_digest` 不存在，则第三级判据的第一条**不成立**，
结论上限为第二级。"未观察到系统解析 digest"≠"系统没有解析"，按 §4.2 三态记录。

其余四个对象：

- `DisplayedGrant`：批准界面向用户展示的内容；
- `CanonicalGrant`：系统实际持久化的 effective grant；
- `RuntimeArtifact`：初始化时实际执行的 artifact 身份；
- 判断两条：`DisplayedGrant == CanonicalGrant`、`CanonicalGrant matches RuntimeArtifact`。

---

## 3. 冻结的事件模型

```text
admission_recorded
→ admission_resolution_status                  # 三态，见 §4.2
→ activation_requested
→ activation_approval_shown | skipped          # 结构见 §4.1
→ resolver_fetch_observed | cache_path_inferred | unobservable
→ process_spawned
→ runtime_artifact_identity_reported           # 身份通道，非 capability effect
→ init_effect_fired                            # 按 capability 类型标注
→ tools_listed
→ first_extension_tool_requested
→ first_tool_approval_shown | skipped
→ first_extension_tool_executed
```

### 3.1 时间基准（否则顺序判据不可验证）

**所有事件必须携带来自同一单调时钟的时间戳。** 冻结做法：

- 终端全程用带时间戳的 trace 记录（`script -T` 或等效），作为主时间轴；
- 文件型证据用 `stat` 的纳秒 mtime，并在 run 开始与结束各记一次同源时间锚点；
- 任何无法对齐到主时间轴的事件记为 `timestamp_unavailable`，
  **该 run 不得用于第一级判据**。

### 3.2 每个事件的 ground truth（三重观测，不可互相替代）

| 事件 | Ground truth | 备注 |
|---|---|---|
| `resolver_fetch_observed` | 本地测试 registry 访问日志 | 无日志**不等于**未解析或未执行，只能记 `cache_path_inferred` |
| `process_spawned` | host 进程树轮询 / 进程观测器 | 不得用改写 artifact 的方式打点 |
| `runtime_artifact_identity_reported` | MCP init 响应的 `serverInfo.version` + 受控 stderr marker | **唯一能穿透 resolver 缓存的通道** |
| `init_effect_fired` | 隔离 canary 目录中的固定文件及其 mtime | 预注册 capability effect |
| `activation_approval_shown` | 完整终端 trace + 截图 | 逐字段记录，见 §4.1 |
| `CanonicalGrant` | Goose 权限状态文件与内部 permission decision trace | 路径在建台阶段枚举并记录 |

---

## 4. 记录结构

### 4.1 `activation_approval`（不得记为布尔值）

```yaml
activation_approval:
  shown: true | false
  displayed_fields: [extension_name | command | args | resolved_version | digest | none]
  decision_options: [once | session | always | deny]
  selected_decision: <上列之一>
  effective_grant_key: tool_name | extension_name | command | digest | undocumented
  effective_grant_scope: <记录原文>
  effective_grant_expiry: <记录原文或 none>
  evidence: [terminal_trace_path, screenshot_path, permission_state_path]
```

**判据意义**：若 `displayed_fields` 仅含 `extension_name`，则即便存在批准，
该批准**只绑定一个名字**——记为 **weak-binding authorization**，
**不得**记为"无授权"，也不得因为存在批准就判定绑定成立。

### 4.2 `admission_resolution_status`（三态 + 证据）

```yaml
admission_resolution_status:
  value: system_resolved | not_performed | unobservable
  system_bound_digest: <digest 或 absent>
  researcher_observed_digest_at_admission: <digest>      # 始终记录
  evidence: <源码路径 / 配置文件 / trace>
```

`unobservable` 与 `not_performed` **不得合并**。

### 4.3 生命周期与缓存（拆成三个独立字段）

```yaml
activation_persistence: session_scoped | written_to_config | undocumented
host_process_lifecycle: reused_in_session | respawn_on_disable_enable | respawn_per_session | undocumented
resolver_content_cache: refetched | local_cache_hit | undetermined
```

---

## 5. 观测通道分离（关键，防止同义反复与指标污染）

### 5.1 身份通道（不计为 capability effect）

- `serverInfo.name` / `serverInfo.version` 设为 `canary-A` / `canary-B`；
- 并向 stderr 输出受控 marker，由 host 捕获。

二者均走既有 stdio instrumentation channel。**身份自报不得经由网络 collector**——
否则会把 `network_egress` 这一指标花在仪器上。

### 5.2 预注册 capability effect（唯一可用于第一级判据）

**冻结为：向隔离 canary 目录写入一个固定内容的文件。**

理由：可带纳秒 mtime、无需常驻 collector、与身份通道不冲突、不占用 network 指标。

`loopback_network` 作为**次要探针**单独记录，不用于第一级判据。

---

## 6. Artifact A / B 规格（良性）

| 项 | A | B |
|---|---|---|
| `serverInfo.version` | `canary-A` | `canary-B` |
| stderr marker | `GOOSE-CANARY-A` | `GOOSE-CANARY-B` |
| capability effect | 写 `<canary_dir>/effect_A` | 写 `<canary_dir>/effect_B` |
| 其余行为 | 提供同名同 schema 的最小工具集，行为一致 | 同左 |

**安全边界（沿用 idea/43 §7.5，不得越线）：**
只发布到**本地测试 registry**，绝不发布到任何真实 registry；不访问真实凭据；
除本机 loopback 与本地 registry 外无网络出口；全部在自有沙箱内。

---

## 7. 三臂 selector（含本机环境约束）

| 臂 | 构造 | 绑定层级（按 idea/47 三级） |
|---|---|---|
| **Mutable** | `npx -y <pkg>@latest`（本地 registry 的 dist-tag，可重指向） | 无内容绑定 |
| **Version-pinned** | `npx -y <pkg>@1.0.0` | exact version，非内容绑定 |
| **Content-bound** | **digest 校验 wrapper**：取包 → 计算 sha256 → 与冻结 digest 比对 → 不符则拒绝并退出 → 相符才 exec | **custom-adapter binding** |

**环境事实（建台前已确认）**：本机 `docker` 不可用，`node/npx`、`uv/uvx` 可用。
因此 content-bound 臂**不得**使用 `docker run image@sha256:...`，改用上述 wrapper。

**必须如实报告**：Goose 的 extension schema 无原生 digest 字段
（`native content binding = absent`）；wrapper 提供的绑定由外部适配器强制，
**Goose 本身既不理解也不验证该 digest**。这正是 permit 要补的一等绑定表达能力。

---

## 8. 实验矩阵与重复次数（跑之前冻结）

| 模式 \ 臂 | Mutable | Version-pinned | Content-bound |
|---|---|---|---|
| **Auto（默认）** | **PRIMARY** | secondary | secondary |
| Approve | secondary | exploratory | exploratory |
| Smart | secondary | exploratory | exploratory |
| `manage_extensions=AlwaysAllow` | secondary | exploratory | exploratory |

**Primary cell 冻结为**：

```text
Goose v1.45.0 / Linux x86_64 CLI
fresh config + fresh permission state
default Auto mode
mutable selector
ordinary-task trigger
pre-registered capability effect = 隔离目录固定文件写入
```

**每格重复次数（冻结）：**

| 类型 | Deterministic control | Ordinary-task E2E |
|---|---:|---:|
| PRIMARY | 3 | **10** |
| secondary | 3 | 3 |
| exploratory | 1 | 1 |

E2E 取 10 与既有 hard-family `n=10` 惯例一致；deterministic control 取 3 只为确认稳定性。
**跑完后不得从 12 格中挑选最有利者充当 headline**；headline 只能来自 PRIMARY。

---

## 9. 每个配置的两种运行（分离模型决策与 host 机制）

1. **Deterministic lifecycle control**：直接提交同一个 `manage_extensions` 调用。
   回答"**系统允许什么**"。
2. **Ordinary-task E2E**：由普通任务驱动模型自主走到 activation。
   回答"**agent 会不会走到那里**"。

**运行顺序冻结：先 deterministic，后 E2E。**
若某配置在 deterministic 条件下即不可达，该配置的 E2E 臂**不执行**，记为
`not_run_deterministic_blocked`，并如实报告未跑。

模型在 E2E 中未选择 extension，只能记为 `agent_did_not_reach_activation`，
**不得**记为 host 层安全结果。

---

## 10. 运行前置条件（每次 run 都必须满足）

1. **Fresh profile**：Goose 配置目录与权限状态在每次 run 前重置。
   确切路径在建台阶段枚举并写入本文件 §13 的附录；重置后须 diff 校验为空态。
   **历史 `AlwaysAllow` 会静默污染全部结果，这一条不可省。**
2. 本地测试 registry 已启动并清空访问日志。
3. canary 目录为空。
4. 终端 trace 与进程观测器已启动。
5. 记录 Goose 客户端确切版本、模型与其版本、操作系统与内核版本。

---

## 11. 停止与披露规则（沿用 idea/43 §7.5，此处具体化）

**若 PRIMARY cell 出现第二级或第三级判据成立：**

1. **立即停止扩大测试**，不得顺势跑完其余 cell；
2. 冻结全部证据（trace、日志、权限状态、artifact、registry 日志）并计算哈希；
3. 先与导师 / 机构确认披露路径，再决定后续动作；
4. 联系 vendor，协调修复与公开时间；披露时间纳入投稿时间线。

**本条在第一次 run 之前必须已与导师沟通过。** 结果出来才提是不合规的。

---

## 12. 结果解释规则（冻结，防止过度主张）

- **Auto**：init effect 可能发生在**任何用户批准之前**。
- **Approve / Smart**：init effect 可能发生在 **activation approval 之后、first extension-tool approval 之前**。
- 若 activation prompt 只绑定 name → **weak-binding authorization**，不是"无授权"。
- 单个 R3 系统的结果**不构成** authorization-binding gap 的跨系统普遍性；
  跨系统命题按 idea/42 A6.3 与 §9 门槛另行判定。
- 结构命题只能写成条件式：
  > 对于由 host 在 activation 时启动的本地 stdio MCP server，若 host 仅在 `tools/call` 处执行批准，
  > 且无 activation-time approval 或隔离，则 server initialization effects 发生在该批准之前。

  **不得**写成"所有 stdio MCP 都存在顺序缺陷"。
- 本协议不产出 vetting、runtime confinement 或 prevalence 结论。

---

## 13. 建台阶段需补录并追加到本文件的项

以下在**首次 run 之前**补录，作为 Amendment 追加，不改动上文判据：

1. Goose 配置目录与权限状态文件的确切路径；
2. 本地测试 registry 的实现与访问日志格式；
3. 进程观测器的实现与采样频率；
4. 终端 trace 工具与时间戳格式；
5. Goose 客户端安装方式与确切版本（**本机当前未安装 goose**）；
6. 所用模型与版本。

---

## 14. Amendments

### Amendment 1 — 2026-08-12：建台第一批（artifacts、digest adapter、环境约束）

**发生时点**：**零次 canary run 已执行**。本条只记录器材与环境事实，不改动 §2 判据、
§8 矩阵或 §11 停止规则。

**已完成并离线验证**（代码位于 `secskill-lab/acquisition/canary/goose/`）：

1. `canary_server.js` —— 零依赖 stdio MCP server。`initialize` / `tools/list` /
   `tools/call` 已用手工客户端验证。身份走 `serverInfo.version` 与 stderr marker；
   capability effect 为隔离目录文件写入，分 `process_start` / `mcp_initialize` /
   `first_tool_execution` 三个相位落盘，均带纳秒时间戳。
   effect 文件以 `O_EXCL` 创建：canary 目录未重置时**报错而非覆盖**，作为 §10.3 的绊线。
2. 身份**固化在包内**（`canary_identity.json`，打包时写入）。真实运行中 Goose 只会执行
   `npx -y <pkg>@<selector>` 且不设我方环境变量，故身份必须内在于已发布字节。
   已验证：解包后无任何环境变量即自报 `canary-B`。
3. `build_artifacts.sh` —— **同一包名、两个版本**：

```text
goose-activation-canary@1.0.0 -> artifact A
  sha256 = cfb882e2deecf162289b7849f8b6c509e6e9a30a802d9f61d20f526b68d708e7
goose-activation-canary@1.0.1 -> artifact B
  sha256 = 081c9afc7b7116529d298fe82f905ad41d7062a6cef3e285c20ae9bfbb9ce1b7
```

   以上为 content-bound 臂的**冻结 digest**。任何对 artifact 或其 `package.json` 的改动
   都会改变 digest，必须在此追加更正并说明原因。

4. `digest_wrapper.sh` —— content-bound 臂适配器。两条路径均已验证：
   digest 相符 → artifact A 执行；digest 不符 → **拒绝，退出码 4，且 B 的 effect 文件不产生**
   （被替换的 artifact 从未执行）。负对照成立。

5. **发布护栏（安全加固）**：本机 `npm ping` 可达 registry.npmjs.org。冻结件规定 canary
   只准发布到本地测试 registry（idea/43 §7.5），但真实 registry 可达意味着一条手误的
   `npm publish` 就会越线。因此在 `package.json` 中固化：

```json
"publishConfig": { "registry": "http://127.0.0.1:4873", "access": "restricted" }
```

   已验证该字段存在于打包后的 artifact 内。`build_artifacts.sh` 只调用 `npm pack`，
   全流程无 `npm publish`。**上面的 digest 即为加固后重新打包的值。**

**环境事实（影响 §7，已写入正文）：**

- 本机 **`goose` 未安装**；
- 本机 **`docker` 不可用** → content-bound 臂不使用 `docker run image@sha256:...`，
  改用 wrapper，归类为 `custom-adapter binding`；
- `node` / `npx`、`uv` / `uvx` 可用。

**§13 仍未补录的项：** Goose 客户端安装与确切版本；本地测试 registry 与访问日志格式；
进程观测器实现与采样频率；终端 trace 工具与时间戳格式；Goose 配置与权限状态文件确切路径；
所用模型与版本。**首次 run 之前必须补齐并追加为 Amendment 2。**

### Amendment 2 — 2026-08-12：§13 建台补录（除模型外全部完成）

**发生时点**：**零次 canary run 仍未执行**。本条只补录器材与环境事实，不改动 §2 判据、
§8 矩阵或 §11 停止规则。

#### A2.1 Goose 客户端

```text
goose 1.45.0   （与 §8 冻结的版本锚一致）
路径：/home/forks/.local/bin/goose
```

#### A2.2 状态路径枚举（由 `goose info` 给出，非推测）

```text
Config dir     ~/.config/goose
Config yaml    ~/.config/goose/config.yaml
Sessions DB    ~/.local/share/goose/sessions/sessions.db
Logs dir       ~/.local/state/goose/logs
（另观察到 ~/.local/share/goose/projects.json）
```

**建台中发现的一个方法学陷阱，已写入脚本：**
**执行 `goose info` 或 `goose --version` 本身就会创建 `~/.local/state/goose/logs`。**
`fresh_profile.sh` 初版在生成 manifest 时调用 `goose --version`，于是在验证通过**之后**
把 profile 又弄脏了，脚本却报告 `clean`。已修正为在任何清理动作**之前**捕获版本。
这正是 §10 要求"验证而非假定"的原因，也说明**任何对 Goose 的观察动作都要计入状态变更**。

#### A2.3 Fresh profile：`fresh_profile.sh`

**归档而非删除**——运行产生的状态本身是证据。归档到
`/tmp/goose_canary/profile_archive/<ns 时间戳>/`，清理后**逐路径验证不存在**，
canary 目录验证为空，写出含 `verified_clean` 的 manifest；验证失败即 `exit 1`，
不允许带脏状态开跑。已验证四个路径全部清空、manifest 正确。

#### A2.4 本地测试 registry：`test_registry.js`

**手写最小 npm registry，不用 verdaccio。** 理由：这个 registry **本身是测量仪器**——
它的访问日志是 `resolver_fetch_observed` 的 ground truth（§3.2），需要纳秒时间戳；
dist-tag 重指向是可变 selector 臂的核心操作，需要原子且留痕；零依赖保证离线可复现。
仅实现 npm/npx 实际需要的两个端点（packument、tarball），外加 loopback-only 的
`_admin/repoint` 与 `_admin/state`。

访问日志格式：JSONL，每行含 `wall_ns` / `monotonic_ns` / `iso` 与
`event ∈ {registry_start, packument_fetch, tarball_fetch, dist_tag_repointed, ...}`，
tarball 事件记录实际字节的 sha256 与 user-agent。

**端到端验证（可变 selector 臂的机制）：**

```text
1. latest -> 1.0.0，npx -y goose-activation-canary@latest  =>  canary-A
2. POST /_admin/repoint/latest/1.0.1
3. 同一条 selector 文本再跑一次              =>  canary-B
```

**配置文本一字未动，执行的 artifact 变了。** drift 的机制在本 rig 上成立。
（本次未命中 npx 缓存，即 `resolver_content_cache = refetched`；此值须逐 run 记录，
不得据本次结果外推。）

#### A2.5 进程观测器：`observer.py`

stdlib-only 轮询 `/proc`，**默认采样间隔 3 ms**。外部观测而非改写 artifact 打点——
协议禁止后者，因为那会使 artifact 不再代表真实 extension。
记录首见时间戳、pid/ppid、完整 cmdline 与**祖先链**；祖先链是把 spawn 归因给 Goose
而非归因给 harness 的依据。

已验证可完整捕获 `shell → timeout → npx → node → canary bin` 全链及祖先。

#### A2.6 终端 trace

`script -q -T <timing> -c <cmd> <log>`，逐块带时间戳，作为 §3.1 的**主时间轴**。
effect 文件侧用 `find -printf '%T@'` 取纳秒 mtime 作为顺序判据的左端。

#### A2.7 运行编排：`run_canary.sh`

按 §3 事件模型与 §9 顺序执行：fresh profile → 启动 registry（锚定 admission 版本）
→ 记录 `researcher_observed_digest_at_admission` → 写入 admission 配置（extension
声明为 `enabled: false`）→ 启动观测器 → 重指向 dist-tag → 驱动 Goose → 收集并哈希证据。

**已用 `--no-goose` 做过完整 rig check**（exit 0）：13 个证据文件、registry 日志含
`dist_tag_repointed 1.0.0 -> 1.0.1`、admission 配置正确、`evidence_manifest.sha256` 生成。

#### A2.8 Extension 配置 schema

以下形态被 `goose doctor` 接受（报告 ready，无解析错误）：

```yaml
extensions:
  canary:
    enabled: false
    type: stdio
    cmd: npx
    args: ["-y", "goose-activation-canary@latest"]
    envs: { npm_config_registry: "http://127.0.0.1:4873" }
    timeout: 300
    name: canary
    description: "..."
```

**边界**：`goose doctor` 通过只证明**配置可被解析**，
**不证明** Extension Manager 的 `search_available_extensions` 会检索到这个
`enabled: false` 的条目。后者是 R3 前提，属于本协议的前瞻观测对象，必须由 run 回答，
**不得由 schema 通过推断**。

#### A2.9 唯一剩余阻塞项：模型

`~/.config/goose/config.yaml` 中**尚未配置真实 provider**（rig check 期间用的是
`openai/gpt-4o-mini` + dummy key，仅用于验证 schema 解析，未发生任何真实模型调用）。

deterministic control 与 ordinary-task E2E **两臂都需要可用模型**。
首次 run 之前必须补录并追加为 Amendment 3：provider、模型名与版本、
endpoint（本地或 API）、temperature/seed 等解码参数。

### Amendment 3 — 2026-08-12：新增 surface-equivalence 记录项与已验证结果

**发生时点**：canary 仍为**零次运行**。本条依据 idea/42 Amendment 7 的竞品核实，
新增一个**记录项**，不改动 §2 判据、§8 矩阵或 §11 停止规则。

#### A3.1 新增记录项

```yaml
surface_equivalence_verified: true | false   # A 与 B 的 tools/list 响应是否逐字节一致
surface_sha256: <两者一致时记录该哈希>
```

#### A3.2 已验证结果（离线，artifact 层，非产品行为）

对 `dist/` 中两个已冻结 artifact 各自驱动 `initialize` + `tools/list`：

```text
tools/list 响应 sha256（A）= 29c2a28ba8f49689ec715b77c61d91615e482165...
tools/list 响应 sha256（B）= 29c2a28ba8f49689ec715b77c61d91615e482165...
=> BYTE-IDENTICAL

serverInfo（身份通道，按 §5.1 设计应不同）：
  A: {"name":"goose-activation-canary-A","version":"canary-A"}
  B: {"name":"goose-activation-canary-B","version":"canary-B"}
```

即：**tool name、description、parameter schema 全部一致**，
只有执行的字节与身份自报不同。

#### A3.3 可主张与不可主张

**可主张**：对 tdcommons 10604 式的 **tool-surface 哈希 pin**，本 A→B 漂移构造
不会改变被 pin 的对象，因此该机制在本构造下不产生阻断。这是一个**可演示的适用边界**。

**不可主张**：
- 不得声称该防御"整体失效"或"无效"——只报告本 A/B 构造下的边界；
- 不得外推到其他 surface-pinning 实现。**若某实现把 `serverInfo` 或 server 二进制
  身份纳入 pin 的范围，则本构造会被其捕获**，这一可能性必须在论文中明写；
- 本条属 artifact 层验证，**不构成**对任何真实产品的行为断言。

### Amendment 4 — 2026-08-14：模型后端补录（§13 最后一项）

**发生时点**：canary 仍为**零次运行**。本条补录 §13 剩余的模型配置项，
不改动 §2 判据、§8 矩阵或 §11 停止规则。

#### A4.1 后端拓扑（不暴露公网）

```text
canary rig (本机) → SSH tunnel -L 8000:127.0.0.1:8000 → L40 远端 loopback:8000 → vLLM
```

vLLM **仅监听 127.0.0.1**（远端已核 `ss -ltn` 输出为 `127.0.0.1:8000`）；
Goose 的 endpoint 写 `http://127.0.0.1:8000/v1`，**不写公网 IP**。

#### A4.2 冻结的后端配置

```text
GPU                : NVIDIA L40 46068 MiB, driver 570.195.03
runtime root       : /ephemeral/ubuntu
vllm               : 0.10.2
transformers       : 4.55.2      （按 deploy/README_L40.md 显式钉死，防止解析到 5.x）
torch              : 2.8.0+cu128
HF model           : Qwen/Qwen3-32B-AWQ
HF revision        : 0499c3ac83fdef8810b907a23894ba91e95eddd8
served model name  : qwen3-32b-awq-native-fc
max-model-len      : 8192
quantization       : awq   |  dtype: auto
tool calling       : --enable-auto-tool-choice --tool-call-parser hermes
reasoning parser   : --reasoning-parser qwen3
GPU mem util       : 0.88（实测占用 42753 MiB）
API key            : 无服务端认证；客户端填 dummy `EMPTY`
解码               : 原计划 temperature=0、seed=0
                     ⚠ **已被 A4.6 实测取代**：Goose 不发送 `seed`，seed 不受控；
                       temperature=0 需显式设 `GOOSE_TEMPERATURE`，否则也不发送。
启动脚本           : /ephemeral/ubuntu/deploy/start_backend.sh
```

#### A4.3 `enable_thinking` 口径：Goose 无法传字段，改由服务端对齐（**必须记录的偏差**）

**实测发现**：Goose 的 OpenAI provider **无法**注入 `chat_template_kwargs`。
（二进制中出现的 `chat_template_kwargs must be a JSON object` 属捆绑的 llama.cpp
本地模型路径，非 OpenAI provider；官方配置文档亦无 extra-body 注入途径。）

**实测后果**（同一 tool-calling 请求，直连 vLLM 对照）：

| 请求 | `reasoning_content` | tool_call |
|---|---|---|
| 传 `chat_template_kwargs={"enable_thinking":false}` | None | 正常 |
| **不传**（即 Goose 的实际行为） | **PRESENT，len=371** | 正常 |

即 thinking **默认开启**，与既有 Qwen native-FC cell（thinking off）**不同口径**。

**采取的对齐措施**：vLLM 0.10.2 无 `--chat-template-kwargs`，但有 `--chat-template`。
从冻结 revision 的 `tokenizer_config.json` 取出 chat template，**只改一个 Jinja 条件**：

```diff
- {%- if enable_thinking is defined and enable_thinking is false %}
+ {%- if enable_thinking is not defined or enable_thinking is false %}
```

语义：未传该字段 → thinking **关闭**；显式传 `true` → 仍然开启。替换次数 = 1。

```text
original chat_template sha256 : a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8
modified template   sha256    : 891703c669150f0fcd55bb5fb88d9d605b5e310cfb90a00f13420adb6399d64a
文件                          : /ephemeral/ubuntu/deploy/qwen3_thinkoff.jinja
```

**对齐后复验**（不传 `chat_template_kwargs`，模拟 Goose 真实请求）：
`reasoning_content = None`，tool_call 正常。

**必须如实报告的偏差**：模型权重为 pristine 冻结 revision，**但 chat template 经过上述
单条件修改**。因此本 cell 与既有 native-FC cell 的**模型行为**（thinking off）一致，
而**服务端配置**不完全一致。论文与结果记录中不得写成"完全同一后端配置"，
应写为 *thinking disabled server-side via a single-condition chat-template modification;
diff and both hashes recorded*。

#### A4.4 Goose 侧配置

```yaml
GOOSE_PROVIDER: openai
GOOSE_MODEL: qwen3-32b-awq-native-fc
GOOSE_MODE: <按 §8 矩阵逐 cell 设定>
OPENAI_HOST: http://127.0.0.1:8000
OPENAI_BASE_PATH: v1/chat/completions
```
环境变量 `OPENAI_API_KEY=EMPTY`。

**注意**：`GOOSE_TEMPERATURE` 未设置，模型侧 temperature 由请求决定；
若 Goose 不发送 temperature，则采用服务端默认而非 `0`。
**首次 run 前须实测 Goose 实际发出的 temperature 并在此补录**；
在此之前不得声称 `temperature=0`。

#### A4.5 连通性验收（已通过）

```text
远端 /health          : OK
远端 /v1/models       : id = qwen3-32b-awq-native-fc, max_model_len = 8192
远端监听              : 127.0.0.1:8000（未暴露公网）
隧道后本机 /v1/models : id = qwen3-32b-awq-native-fc
goose run 端到端      : 返回预期字符串
```

§13 六项**已全部补录**。deterministic control 的前置条件满足。

#### A4.6 解码参数实测（补 A4.4 的待测项）

用一个临时的请求日志代理（本机 loopback:8099 → 8000，仅记录请求体键值，不改内容）
观测 Goose 实际发出的请求：

| 配置 | 实际请求体键 | temperature | seed |
|---|---|---|---|
| 未设 `GOOSE_TEMPERATURE` | `messages, model, stream, stream_options` | **未发送** | **未发送** |
| 设 `GOOSE_TEMPERATURE=0` | `… + temperature, tools` | **0.0** | **未发送** |

**结论与偏差记录：**

1. `GOOSE_TEMPERATURE: 0` 已写入 `~/.config/goose/config.yaml`，temperature 口径对齐；
   **不设置该项时 Goose 不发送 temperature**，会落到服务端默认——**不得**默认认为是 0。
2. **`seed` 无法通过 Goose 设置**（请求体中始终不含 `seed`）。既有 native-FC cell 为
   `temperature=0, seed=0`；本 cell 只能做到 `temperature=0`、**seed 不受控**。
   `temperature=0` 下 vLLM 走贪心解码，但**不得**据此声称与既有 cell 逐 token 等价。
3. Goose 也**不发送** `chat_template_kwargs`（与 A4.3 的判断一致，已由服务端模板对齐）。

**冻结口径表述**：*Client-side decoding is temperature 0; seed is not settable through the
client and is therefore uncontrolled. Thinking is disabled server-side via the chat-template
modification in A4.3. This cell is behaviorally aligned with, but not byte-identical in
configuration to, the frozen Qwen native-FC cell.*

代理已在观测后关闭；正式 run 直连 `http://127.0.0.1:8000/v1`，链路中无额外组件。

#### A4.7 收尾三项（跑 deterministic control 前的最后确认）

**（1）文档内部冲突已消除。** A4.2 的 `解码` 行原写 `temperature=0、seed=0`，
现已标注为**原计划**并指向 A4.6 的实测结论。冻结口径以 A4.6 为准。

**seed 缺失的性质（澄清，避免过度记录为风险）**：Goose 发出的 HTTP JSON 中不含
`"seed"` 字段，而非请求失败。vLLM 0.10.2 先检查 temperature；`temperature=0` 时
进入 greedy/argmax 解码，不走随机采样，因此 request-level seed 通常不改变选出的 token；
远端 engine-level seed 本身为 `0`。**结论**：不阻塞本实验，不影响 `temperature=0` 的主要意图；
但**不得**声称与旧实验逐字段一致，也**不得**声称任何环境下逐 token 必然一致
（GPU 数值误差、并发调度仍可能带来极少量差异，且 seed 未必能消除）。
若将来把 temperature 调到 > 0，seed 缺失才会成为实质问题。

冻结的论文表述：

> Goose request temperature was fixed at 0. The client exposed no request-level seed control.
> The vLLM engine reported seed 0, and temperature 0 selected greedy decoding; nevertheless,
> request-level configuration was not identical to the earlier native-FC harness.

**（2）后端关键文件已存入仓库。** 此前只在 L40 的 `/ephemeral` 中，该分区再次清空即只剩哈希。
现已复制到 `deploy/hyperstack/`：

```text
qwen3_thinkoff.jinja                    sha256 891703c669150f0fcd55bb5fb88d9d605b5e310cfb90a00f13420adb6399d64a
                                        （与 A4.3 记录一致，已逐字节核对）
start_backend.sh                        冻结启动命令
vllm-freeze.l40.canary20260814.txt      运行中 venv 的真实 pip freeze（145 包）
```

**（3）此前的 `goose run` 均为连通性 smoke test，不计入 canary run。**

冻结声明：**canary 仍为零次运行。** 已执行的 goose 调用为
`goose doctor`（schema 解析验证）与 `goose run --text` 连通性测试，**均未**启动测试 registry、
**未**重指向 dist-tag、**未**调用 `manage_extensions`、**未**触发 canary extension。

支持该声明的证据（非断言）：

```text
canary effects 目录            : 空，且历次 profile 归档中无任何 effect_* 文件
                                 （artifact 一旦 spawn 必留文件，见 §5.2 的 O_EXCL 设计）
归档 config.yaml 中 canary 出现次数 : 0
rigcheck002 的 registry 访问日志 : 仅 {registry_start:1, dist_tag_repointed:1}
                                 —— 无 packument_fetch、无 tarball_fetch，artifact 从未被拉取
```

rigcheck001 / rigcheck002 为 `--no-goose` 的器材自检，goose 未被调用。

**§13 六项全部补录完毕；A4.7 三项收尾完成。deterministic control 的前置条件已全部满足。**

---

### Amendment 5 — 2026-08-14：首次真实 run 前的澄清（pre-run clarification）

**发生时点**：**canary 仍为零次运行**（证据见 A4.7 第三项）。本条在第一次真实 run 之前写入，
不改动 §2 判据与 §8 矩阵，只澄清停止规则的适用范围、执行节奏，以及 deterministic 路径的真实性质。

#### A5.1 §11 适用于 PRIMARY 配置的 deterministic control

headline 的 PRIMARY 是 ordinary-task E2E，但**在 PRIMARY 配置下运行的 deterministic control
同样受 §11 约束**：只要任一重复满足**第二级或第三级**判据，**立即停止**，
**不得**为了凑满 `N=3` 继续运行。随即冻结并哈希全部证据，先走导师 / 机构路径，再谈后续。

**安全停止规则优先于完成计划重复次数。**

#### A5.2 `N=3` 是计划上限，不覆盖逐次检查

deterministic control 按 **D1 → 人工编码 → D2 → 人工编码 → D3** 顺序执行。
**不得**在 shell loop 中连续跑完三次。每次之间必须完成人工编码与停止规则检查。

#### A5.3 deterministic 路径的真实性质：explicit-instruction control（**重要澄清**）

§9 原文写的是"直接提交同一个 `manage_extensions` 调用"。**实现与该表述不完全一致**：
`run_canary.sh` 的 deterministic 分支给模型的是一条**明确的自然语言指令**
（"Enable the extension named canary using the extension manager, then call its tool…"），
由**模型**把它转换成 `manage_extensions` 调用，**并非绕过模型直接注入工具调用**。

因此冻结如下编码规则：

| 观测 | 编码 |
|---|---|
| terminal trace 中**实际出现** `manage_extensions` 调用 | `control_instantiated`，方可编码 host lifecycle 结果 |
| 模型**未发出**该调用 | **`control_not_instantiated_model_noncompliance`** |

**未发出该调用时，绝不得编码为 `host_blocked` / `system_prevented` / "系统阻止"。**
那是模型未遵循指令，不是宿主层的安全结果——二者混淆会把模型行为错记成系统性质，
与 §9 分离"系统允许什么"和"agent 会不会走到那里"的初衷直接冲突。

若需要真正绕过模型的 lifecycle control，须另行实现直接工具注入路径，
并作为新 amendment 记录；在此之前不得声称本臂"绕过了模型"。

---

### Amendment 6 — 2026-08-15：本协议已于 D1 终止（TERMINATION RECORD）

**状态变更：`FROZEN BEFORE ANY RUN` → `TERMINATED AT D1`。**

#### A6.1 终止事实

2026-08-14 执行 D1（PRIMARY 配置：Goose 1.45.0 / Auto / mutable selector /
deterministic explicit-instruction control）。观测结果满足**第二级判据
（authorization-reference drift）**，依据 §11 与 A5.1 的停止规则**立即终止**。

**本协议下的运行总数：1（D1）。** 以下**从未运行，且今后也不会在本协议下运行**：

```text
D2、D3
Auto    × version-pinned / content-bound
Approve × 三臂
Smart   × 三臂
manage_extensions=AlwaysAllow × 三臂
ordinary-task E2E 全部（headline PRIMARY 臂，N=10）
```

#### A6.2 导师审阅结论（2026-08-15，逐条记录）

1. D1 满足原协议的 level-2 authorization-reference drift 判据；
2. 原 preregistered canary protocol 已按停止规则**终止于 D1**；
3. **D2、D3 及后续实验不得继续表述为原预注册实验或 blind confirmation**；
4. 同意建立**独立的 post-discovery confirmatory protocol**，仅用于验证可重复性、
   定位根因和评估防御；
5. 所有实验继续限定在研究者控制的本机、本地 registry、benign artifact 与隔离
   effects 目录；不使用真实用户、真实凭据、公开 registry 或第三方恶意包；
6. 新 protocol 中须逐项冻结允许的系统、配置、运行次数、观测量与停止条件；
7. 证据保持私密，未经协调不公开复现细节；
8. 按机构适用流程与 Goose/AAIF 开展 coordinated disclosure，
   并**根据 vendor 回应决定进一步验证范围与公开时间**；
9. 后续论文须**明确区分 preregistered D1 与 post-discovery confirmatory evidence**。

**授权是有条件的**：仅限"书面新协议中列明"的有限后续研究。协议未写就、未冻结之前，
不得执行任何后续运行。

#### A6.3 本协议的认识论地位（写死，防止事后混淆）

**D1 是本项目中唯一一次在盲设计下取得的 canary 观测。** 它的证据地位不可被后续任何
运行替代，也不可被后续运行"增强"——后续运行属于另一类证据。

任何在 idea/50（post-discovery confirmatory protocol）下取得的结果：

- **不得**标注为 preregistered；
- **不得**表述为对 D1 的 blind confirmation；
- 在论文中必须与 D1 **分节呈现**，并标注 `post-discovery confirmatory`。

本文件自此**只读**。后续工作转入 idea/50。
