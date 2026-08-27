# 50 — Post-Discovery Confirmatory Protocol

> **CONFIDENTIAL / PRE-DISCLOSURE** — 证据与复现细节未经协调不公开。
>
> 日期：2026-08-15
> 协议 ID：`goose_activation_binding_postdiscovery_v1`
> 前置：idea/48（原预注册协议，**已于 D1 终止**，见其 Amendment 6）
> 依赖：idea/42（主框架与主张边界）、idea/43 v1.2（编码手册）、idea/47（route grades）
> 状态：**FROZEN BEFORE ANY RUN UNDER THIS PROTOCOL.** 本协议下运行次数 = 0。
> 授权：导师书面同意（2026-08-15），条件见 §1。

---

## 0. 认识论地位（最重要，写在最前）

**本协议不是预注册确认实验。** 它在 D1 结果已知之后写成，因此：

- 本协议下的任何结果**不得**标注为 `preregistered`；
- **不得**表述为对 D1 的 `blind confirmation`；
- 论文中必须与 D1 **分节呈现**，统一标注 **`post-discovery confirmatory`**；
- D1 是本项目**唯一**一次盲设计下的 canary 观测，其证据地位**不可被本协议下的任何运行
  替代或增强**——二者是不同类别的证据。

写本协议时已知的全部内容：idea/48 Amendment 6 记录的 D1 完整结果与冻结证据。

---

## 1. 导师授权与约束（逐条转为可执行条款）

| # | 授权原文要点 | 本协议中的落实条款 |
|---|---|---|
| 1 | D1 满足 level-2 判据 | §0、§2 引用，不再重新论证 |
| 2 | 原协议已终止于 D1 | idea/48 Amendment 6 已记录，本文件为独立协议 |
| 3 | 后续不得表述为原预注册或 blind confirmation | §0、§9 强制标注 |
| 4 | 仅用于可重复性、根因定位、防御评估 | §3 三个目的，**其余目的一律不在授权范围内** |
| 5 | 限本机 / 本地 registry / benign artifact / 隔离目录；不用真实用户、真实凭据、公开 registry、第三方恶意包 | §4 安全信封，逐项写死 |
| 6 | 逐项冻结系统、配置、运行次数、观测量、停止条件 | §5 / §6 / §7 / §8 |
| 7 | 证据私密，未经协调不公开复现细节 | §9.3 |
| 8 | 按机构流程协调披露；vendor 回应决定后续范围与公开时间 | §10 |
| 9 | 论文区分 D1 与 post-discovery 证据 | §0、§9.1 |

**授权是有条件的**：仅限本文件列明的运行。本文件之外的任何运行**未获授权**。

---

## 2. D1 已确立与未确立的（本协议的起点）

**已确立（level-2）**：在 Goose 1.45.0 / Auto / mutable selector 的单次运行中，
准入时授权绑定的可变选择器在激活时被重新解析为不同制品并被执行，
其间未出现针对具体制品的新授权。

**未确立**：

- `admission_resolution_status = unobservable`（无法区分"系统未解析"与"不可观测"）；
- 因此 level-3 不成立，**不得**使用 TOCTOU 一词；
- 单次运行，无可重复性证据；
- 未测 version-pinned 与 content-bound 两臂是否阻断；
- 未观测 Approve / Smart 模式下批准界面**展示了什么**；
- D1 中 tarball **命中本地缓存**（`resolver_content_cache: local_cache_hit`），
  未控制 npx 缓存状态。

本协议**只针对上述未确立项**。

---

## 3. 三个授权目的（超出即越权）

**C1 可重复性** —— D1 的观测在相同配置下是否稳定复现。

**C2 根因定位** —— 漂移由哪个环节决定：可变 tag、缓存状态、还是准入时不做解析。
特别是尝试把 `admission_resolution_status` 从 `unobservable` 向
`not_performed` 或 `system_resolved` 收敛。

**C3 防御评估** —— 三级绑定（mutable / version-pinned / content-bound adapter）
在同一漂移构造下分别是否阻断，以及各自的授权决策次数代价。

**明确不在授权范围内**：ordinary-task E2E 臂；任何针对其他产品的运行；
任何 permit 原型的完整实现与评估（另议）；任何扩大攻击面的尝试。

---

## 4. 安全信封（逐项写死，越线即停止）

```text
✔ 仅在研究者控制的本机执行
✔ 仅使用本机 loopback 自建测试 registry（publishConfig 硬钉本地地址）
✔ 仅使用 benign artifact：向隔离目录写固定文件；不联网、不读凭据、不访问第三方服务
✔ 效应仅落在隔离 effects 目录
✔ 模型后端为研究者自有 L40，仅 loopback + SSH 隧道

✘ 不使用真实用户或真实用户数据
✘ 不使用任何真实凭据
✘ 不向任何公开 registry 发布或拉取本研究制品
✘ 不引入任何第三方恶意包
✘ 不扫描、不探测、不攻击任何真实服务
✘ 不在研究者控制之外的任何机器上执行
```

---

## 5. 冻结的系统与配置

### 5.1 允许的系统（仅一个）

```text
Goose 1.45.0, Linux x86_64, CLI
```

**不得**在本协议下测试任何其他产品或版本。idea/45 抽样框中的其余单元与本协议无关。

### 5.2 冻结的后端

沿用 idea/48 Amendment 4 的完整配置（Qwen3-32B-AWQ @ 冻结 revision、vLLM 0.10.2、
native FC、thinking 经单条件模板修改关闭、`GOOSE_TEMPERATURE=0`、seed 不受控）。
后端配置**不得**在本协议进行中变更；若必须变更，须作为 amendment 记录并重新开始计数。

### 5.3 冻结的制品

沿用 idea/48 §6 的 A / B（同包名、两版本、tool surface 逐字节相同）：

```text
A: 1.0.0  sha256 cfb882e2deecf162289b7849f8b6c509e6e9a30a802d9f61d20f526b68d708e7
B: 1.0.1  sha256 081c9afc7b7116529d298fe82f905ad41d7062a6cef3e285c20ae9bfbb9ce1b7
```

### 5.4 触发方式（仅一种）

**explicit-instruction control**（idea/48 A5.3）。指令文本与 D1 逐字节相同。
**ordinary-task 触发不在本协议授权范围内。**

编码规则不变：trace 中实际出现 `manage_extensions` 调用才记 `control_instantiated`；
未出现记 `control_not_instantiated_model_noncompliance`，
**不得**编码为 `host_blocked` / `system_prevented`。

### 5.5 新增受控变量：npx 缓存状态

D1 未控制此项。本协议将其提升为显式变量：

```yaml
npx_cache_state: cleared | warm
```

`cleared` = 运行前删除 `~/.npm/_npx`（归档后删除，与 profile 重置同样处理）。
每次运行必须记录该值。

---

## 6. 冻结的运行清单与次数

| ID | 目的 | 模式 | selector 臂 | npx 缓存 | 次数 |
|---|---|---|---|---|---:|
| **R1** | C1 可重复性 | Auto | mutable | warm（同 D1） | **3** |
| **R2** | C2/C3 阴性对照 | Auto | version-pinned `@1.0.0` | cleared | **2** |
| **R3** | C3 内容绑定 | Auto | content-bound（digest wrapper） | cleared | **2** |
| **R4** | C2 准入解析探针 | Auto | mutable | **cleared** | **2** |
| **R5** | C2/C3 批准内容 | Approve | mutable | cleared | **2** |
| **R6** | C2/C3 批准内容 | Smart | mutable | cleared | **2** |

**总计 13 次。硬上限 15 次**（2 次余量仅用于因器材故障作废的重跑，
作废原因须记录；不得用于"结果不好看"的重跑）。

**执行节奏**：逐次运行、逐次人工编码、逐次检查 §8 停止条件。
**不得**在 shell loop 中连续跑完任何一组。

### 6.1 各运行要回答的具体问题

- **R1**：D1 的 level-2 观测是否复现？三次中 `RuntimeArtifact` 是否均为 B？
- **R2**：selector 钉死到 exact version 后，重指向 `latest` 是否**不再**改变执行制品？
  —— 若仍漂移，说明根因不在 tag 可变性，需重新定位。
- **R3**：digest wrapper 是否在制品被替换时拒绝执行、且**不产生** capability effect？
- **R4**：清空 npx 缓存后，registry 日志中**在 `manage_extensions` 之前**是否出现任何请求？
  这是把 `admission_resolution_status` 从 `unobservable` 向 `not_performed` 收敛的唯一途径。
  **限制**：零 registry 流量**不等于**系统未解析（可能有其他路径），
  只能记为 `no_pre_activation_registry_request_observed`，
  **不得**直接改写为 `not_performed`。
- **R5 / R6**：批准界面 `displayed_fields` 究竟包含哪些字段？
  若仅含 `extension_name`，按 idea/48 §4.1 记 **weak-binding authorization**，
  **不得**记为"无授权"。同时记录 `effective_grant_key` 与 decision options。

---

## 7. 冻结的观测量

完全沿用 idea/48 §3（事件模型、时间基准、三重观测 ground truth）与 §4（记录结构），
外加本协议新增的两项：

```yaml
npx_cache_state: cleared | warm                      # §5.5
pre_activation_registry_requests: <计数与逐条事件>    # R4 用
```

`surface_equivalence_verified` 沿用 idea/48 Amendment 3 的已验证结果，不重复验证。

### 7.1 器材修正（本协议下允许，须记录）

idea/48 A4.7 记录的 manifest 顺序缺陷（`run.log` 在被哈希后又追加 `run_complete` 行）
**在本协议下修复**：把 manifest 计算移到全部日志写完之后。

**该修复使器材与 D1 所用版本不再逐字节一致**，因此：
本协议下的 `evidence_manifest.sha256` 应达成 100% 自洽校验；
D1 的 28 OK / 1 FAILED 状态**保持原样，不得回溯修改**。

---

## 8. 停止条件（任一触发即停止并报告）

1. **越出 §4 安全信封的任何需求**——包括为推进实验而需要真实凭据、公开 registry
   或第三方包的任何情形；
2. **出现支持 level-3 的证据**（即观测到 `SystemCheckedOrBound(A)`）——
   这是比 D1 实质更强的主张，须先经导师复核，**不得**自行继续；
3. **任何提示存在真实用户影响的观测**；
4. **vendor 回应到达**——立即暂停，按 §10 重新界定范围；
5. **达到 15 次硬上限**；
6. **连续 2 次器材故障**——先修器材，不得带病继续。

触发后：冻结并哈希全部证据 → 归档至 `~/goose-canary-archive/` → 书面报告导师。

---

## 9. 主张边界与报告纪律

### 9.1 强制标注

本协议下每一条结果，在任何文档、幻灯片与论文中都必须带标注：

```text
post-discovery confirmatory (protocol: goose_activation_binding_postdiscovery_v1)
```

与 D1 的 `preregistered` 结果**分节呈现**，不得混列于同一表格而不加区分。

### 9.2 禁用表述（沿用并扩展 idea/42 A7.3、idea/48）

```text
✘ TOCTOU / exploitable vulnerability
✘ 任何跨系统或行业普遍性（cross-system prevalence）
✘ "系统没有解析 digest"（未观测 ≠ 未发生）
✘ "绕过了批准"（Auto 模式下不存在批准环节）
✘ 把本协议结果称为对 D1 的独立确认
✘ 首次提出内容绑定 / 首次发现授权绑到名字（prior art 已占，见 idea/42 A7.3）
```

### 9.3 保密

证据与复现细节保持私密。在协调披露完成之前：
**不公开发布、不提交预印本、不在公开场合演示复现步骤。**
本项目的证据归档位于 git 仓库之外，不得纳入任何会被推送的目录。

---

## 10. 与披露流程的耦合

按机构适用流程与 Goose / AAIF 开展 coordinated disclosure。

**vendor 回应到达时**：本协议**立即暂停**（§8 第 4 条）。
后续验证范围与公开时间**由 vendor 回应共同决定**，须以新的 amendment 记录，
不得沿用本协议原范围继续执行。

披露时间窗口与投稿时间线一并排定。

---

## 11. 论文侧的分离要求

最终论文中：

- **D1** 作为唯一的预注册观测单独呈现，保留其 `admission_resolution_status = unobservable`
  与 level-2 上限；
- 本协议结果作为 **post-discovery confirmatory evidence** 另节呈现；
- 两者的**证据强度不得等同陈述**；
- 方法学章节须说明停止规则在 D1 触发、原协议随之终止、后续为独立协议——
  这一过程本身是方法学诚信的组成部分，不应隐去。

---

## 12. Amendments

（暂无。本协议下的任何修改按 idea/42 §10 走 append-only amendment，
记录日期、理由与当时已见证据。）

---

## Amendment 1 — 2026-08-15：pre-run 修订（四项必须修改 + 一项 D1 回溯记录）

**发生时点**：本协议下运行次数仍为 **0**。本条在任何运行、L40 恢复或 Goose 执行之前写入。
既有冻结正文**不被覆盖**，以下条款**取代**正文中相应部分。

---

### A1.1 产品原生 OSV 外呼：冻结为阻断（**新增受控项**）

#### 已验证的事实

对已安装的 `goose 1.45.0` 二进制做符号与字符串核验：

```text
https://api.osv.dev/v1/query        存在
deny_if_malicious_cmd_args          存在
deny_if_malicious_impl              存在
```

本机对 `api.osv.dev` **可达**（POST 空体返回 HTTP 400，即服务端有响应）。

**未由本人验证**：Goose 在该网络失败时是否 fail-open。该判断来自源码阅读（codex），
**本协议中标注为 `source-reported, not independently verified by this author`**，
在获得源码级复核之前**不得**作为论文陈述。

#### 边界问题

§4 安全信封原文规定"不访问第三方服务"。该条**只约束了我们的制品**，
**未约束受测产品自身的外呼**。`deny_if_malicious_cmd_args` 路径可能把
包名（`goose-activation-canary`）发送至真实的 `api.osv.dev`。这是信封中一个
此前未解决的缺口。

#### 冻结决定：默认阻断

本协议下**所有运行**必须阻断该外呼，并记录：

```yaml
product_native_osv_egress: blocked_by_harness
osv_block_method: <实现方式>
osv_block_verified: true | false        # 必须为 true 才允许开始该轮运行
```

**实现要求**（具体方式在建台阶段确定并记录，须满足以下全部）：

1. 不对系统做永久性更改（建议用 mount namespace 内的 `/etc/hosts` 覆盖，
   或运行期临时防火墙规则并在结束后移除并验证已移除）；
2. **不得**破坏本机 loopback——模型端点 `127.0.0.1:8000` 与
   测试 registry `127.0.0.1:4873` 必须仍然可达；
3. 运行前**主动验证**：在实际运行环境内对 `api.osv.dev` 的连接尝试必须失败，
   并把该验证输出存入证据；`osv_block_verified=false` 时**禁止**开始运行。

#### 由此产生的主张限制（写死）

- **不得**据本协议结果评价 OSV 在线检测的效果——该路径被我们阻断了；
- **不得**把阻断后的运行描述为"完整的产品默认联网行为"，
  统一表述为 *default configuration with product-native OSV egress blocked by the harness*；
- 若判断阻断会破坏研究问题：**不得自行改为允许外呼**。须先书面写出
  "仅允许该产品原生 OSV 请求"的替代方案、会泄露的字段清单与记录方法，
  提交研究者与导师确认后方可变更。

无论采用哪种方案，该项**必须冻结且可验证**，不得继续保持未观测状态。

#### D1 的回溯记录（**不修改 D1 证据，仅补记认识状态**）

D1 运行时**未控制**该外呼路径。D1 证据中搜索 `osv` / `malicious` **无任何命中**，
但**日志无记录不等于请求未发生**。因此 D1 就此项记为：

```yaml
product_native_osv_egress_at_D1: unobservable
```

**不得**声称 D1 期间未发生 OSV 外呼，也**不得**声称发生过。
D1 的 level-2 漂移观测不受此影响；受影响的是 D1 报告 §8 中
"不访问第三方服务"一句的覆盖范围——该句**仅对我们的制品成立**，
不覆盖受测产品自身的行为。**此点须向导师明示。**

---

### A1.2 npm / npx 缓存：重写操作定义（**取代 §5.5**）

#### 原定义不充分

§5.5 把 `cleared` 定义为删除 `~/.npm/_npx`。**不充分**：`_npx` 只是 npx 的包目录缓存，
tarball / content 缓存通常位于 npm cache 的 `_cacache`。这恰好可能解释 D1
"有 `packument_fetch`、无 `tarball_fetch`"的现象。

**且不得删除或污染用户的全局 `~/.npm`。**

#### 冻结的新定义

每次运行使用**独立、受控**的 cache 目录，通过 `npm_config_cache` 指定
（经 extension 配置的 `envs` 传入，与 `npm_config_registry` 同法）：

```yaml
npm_cache_dir: <每轮独立路径>
npm_cache_state: cleared | controlled-warm
```

- **`cleared`**：运行前**新建的空目录**。不是"删掉某个子目录"。
- **`controlled-warm`**：由**冻结的预热步骤**构造，必须记录：
  - 预热时预置的是**哪个版本**；
  - 缓存中包含 `_cacache` 还是 `_npx` 还是二者；
  - 预热完成后、正式观测窗口开始**之前**清空 registry 访问日志。

每轮保存 cache 状态清单或哈希，存入证据。

#### R1 更名

**R1 改称 `controlled-warm / D1-like cache-hit condition`。**
**不得**声称与 D1 的缓存字节状态完全相同——D1 的缓存状态是未知的。

#### 冻结的判定规则

```text
local_cache_hit : 观测窗口内 registry 有 packument 请求但无对应 tarball 请求，
                  且运行时制品身份确认已执行
refetched       : 观测窗口内 registry 有对应 tarball 请求
undetermined    : 二者均无法确定（含日志缺失、窗口对齐失败）
```

`undetermined` **不得**被折算为其余任一状态。

---

### A1.3 R3 改为配对的功能 / 拒绝对照（**取代 §6 中 R3 的定义**）

#### 原设计的缺陷

原 R3 两次运行都只问"digest 不匹配时是否拒绝"。这**无法排除** wrapper 在 Goose 集成
路径中**始终失败**（fail-closed-by-breakage）——那样也会"拒绝"，但毫无防御价值。

#### 冻结的配对设计（总数仍为 2，不增加预算）

| 子运行 | selector 解析到 | 期望 digest | 通过判据 |
|---|---|---|---|
| **R3a** digest-match | A | A | wrapper 放行，**A 正常启动**，产生预注册的 **A effect** |
| **R3b** digest-mismatch | B | A | wrapper 在 B 执行前**拒绝**，退出码符合冻结值（`4`），**不产生任何 B effect** |

**只有 `R3a pass ∧ R3b reject` 同时成立**，方可称该 content-bound adapter
在此集成路径中"有效阻断漂移"。**仅 R3b 拒绝不能排除 fail-closed-by-breakage。**

**必须继续明确**：该 adapter 是**外部 custom adapter，不是 Goose 原生防御**；
Goose 的 extension schema 无原生 digest 字段，既不理解也不验证该 digest。

---

### A1.4 Approve / Smart 的人工批准操作（**取代 §6 中 R5 / R6 的定义**）

#### 原设计的缺陷

原 R5/R6 只写"观察弹窗显示什么"，**未规定研究者按哪个按钮**——引入未冻结的人为变量。

#### 冻结的操作

每种模式的两次运行固定为：

| 运行 | 操作 |
|---|---|
| 第 1 次 | 完整归档 prompt、`displayed_fields`、`decision_options` 后，选择 **`Allow Once`** |
| 第 2 次 | 完成同样归档后，选择 **`Always Allow`** |

`Always Allow` **仅在该选项实际存在时**选择；若不存在，按预定义编码记录
`decision_option_absent:<列出实际存在的选项>`，**不得临场换成其他选项**。

**每次均须**：从 fresh profile 开始；归档批准前后的 permission store / config 差异；
结束后验证下一轮 profile 已重置。

**研究者不得**根据弹窗内容或前一轮结果临场改变选择。

#### 分别报告三件事（不得合并）

```text
1. 批准界面显示了什么      （displayed_fields）
2. 实际选择了什么          （selected_decision）
3. 持久化记录绑定到什么    （effective_grant_key / scope / expiry）
```

**不得**仅凭出现弹窗就称 artifact-specific authorization。
**不得**把 `Allow Once` 与 `Always Allow` 合并为同一条件报告。

---

### A1.5 器材作废与重跑纪律（补充 §6、§8）

1. **所有器材作废标准必须在看结果之前判定。** 作废理由须在编码结果前写下。
2. **模型未发出 `manage_extensions` 是一个有效结果**
   （`control_not_instantiated_model_noncompliance`），
   **不得**以"器材故障"为名重跑。
3. 逐次执行、逐次编码、逐次检查停止条件；**禁止 shell loop 连跑**。

---

### A1.6 修订后的运行清单（总数与上限未变）

| ID | 目的 | 模式 | selector 臂 | cache | 次数 |
|---|---|---|---|---|---:|
| R1 | 可重复性 | Auto | mutable | **controlled-warm** | 3 |
| R2 | 阴性对照 | Auto | version-pinned `@1.0.0` | cleared | 2 |
| **R3a** | 功能对照 | Auto | content-bound（解析到 A，期望 A） | cleared | **1** |
| **R3b** | 拒绝对照 | Auto | content-bound（解析到 B，期望 A） | cleared | **1** |
| R4 | 准入解析探针 | Auto | mutable | cleared | 2 |
| R5 | 批准内容 | Approve | mutable（Allow Once / Always Allow 各一） | cleared | 2 |
| R6 | 批准内容 | Smart | mutable（Allow Once / Always Allow 各一） | cleared | 2 |

**总计 13 次；硬上限 15 次**——与正文一致，未增加预算。

所有运行额外强制：`product_native_osv_egress = blocked_by_harness` 且
`osv_block_verified = true`（A1.1），否则不得开始。

---

## Amendment 2 — 2026-08-15：工程勘误（pre-run engineering corrigendum）

**发生时点**：本协议下 canary run 次数仍为 **0**。本条修正 Amendment 1 与首版器材中的四项
工程缺陷，均在任何正式运行之前发现。**旧的 preflight 报告与 rig freeze 保留不删，标记为 superseded。**

### A2.1 R1 预热版本更正（**取代 A1.2 中 R1 的预热定义**）

**缺陷**：A1.2 将 `controlled-warm` 定义为预热 **A/1.0.0**。但 D1 中命中 tarball 缓存、
并且实际执行的制品是 **B/1.0.1**。若预热 A，则 `latest→B` 之后仍需下载 B，
得到的是 `refetched` 条件，**无法复现 D1 已知的 cache-hit 条件**。

**更正**：R1 的 `controlled-warm` 固定预热 **B/1.0.1**。

冻结定义改为：

```text
controlled-warm = B (1.0.1) tarball present in _cacache, _npx empty
```

`_npx` 为空的限制不变（无法在不执行制品的前提下预热），预热后清空 registry 日志不变。
R1 仍称 `controlled-warm / D1-like`，**不得**声称与 D1 的缓存字节状态完全相同。

### A2.2 信号中止语义更正

**缺陷**：首版器材使用 `trap finish EXIT INT TERM`。信号到达时 handler 作为信号处理器
执行一次，随后 shell 退出又作为 EXIT handler 执行一次——**重复清理与重复生成 manifest**，
且 `ABORTED` 中记录的 `exit_code` 为 0，与实际中止原因不符。

**更正**：改为独立信号处理器，记录真实信号并设置非零退出码，随后只触发一次 EXIT 清理：

```text
SIGINT  -> 130
SIGTERM -> 143
finish() 以 FINISH_DONE 守卫，保证只执行一次
```

`run_summary.txt` 新增 `signal` 与 `shell_exit_code` 字段，`ABORTED` 区分
`reason=signal`（含信号名）与 `reason=error`。

**已验证**（四条路径，均在前台交付信号）：

| 路径 | shell_exit_code | signal | ABORTED | manifest | finish 执行次数 |
|---|---|---|---|---|---|
| 正常完成 | 0 | none | — | 100% OK | 1 |
| registry 端口占用 | 5 | none | reason=error | 100% OK | 1 |
| SIGINT | 130 | SIGINT | reason=signal | 100% OK | 1 |
| SIGTERM | 143 | SIGTERM | reason=signal | 100% OK | 1 |

**附带发现（须写入操作规程）**：以 `&` 在非交互 shell 中后台启动时，SIGINT 在进入时即为
`SIG_IGN`，而 bash **无法为进入时已被忽略的信号安装 trap**，因此后台启动的运行**不会**
响应 SIGINT。**正式运行必须在前台执行**，否则 Ctrl-C 的中止语义不成立。

### A2.3 后台写入者必须确实退出后才生成 manifest

**缺陷**：首版仅 `kill` observer / registry 后 `sleep 0.4`，未 `wait`。写入者可能在 manifest
生成之后继续写日志，使 manifest 描述的内容与最终文件不符。

**更正**：新增 `stop_writer()`——`kill -TERM` → 有界等待（最长 5 s）→ 必要时升级 `kill -KILL`
→ 再等（最长 3 s）→ `wait`。若仍存活则记 `WRITER_STILL_ALIVE` 并在 run.log 中标明
manifest 可能不可靠。**确认全部写入者退出后**才收集文件与计算 manifest。
每轮 run.log 中应出现 2 条 `writer_stopped`（observer 与 registry）。

### A2.4 正式运行前置条件由脚本硬校验

**缺陷**：首版仅要求 `GOOSE_PROVIDER` / `GOOSE_MODEL` 非空，且允许环境覆盖 temperature 与
host；OSV 验证时 registry 尚未启动，无法证明 loopback 服务在同一沙箱内可用。

**更正**：调用 Goose 之前逐项硬校验，任一不符即中止（不同退出码便于区分）：

| 检查 | 冻结值 | 失败退出码 |
|---|---|---|
| provider | `openai` | 10 |
| model | `qwen3-32b-awq-native-fc` | 10 |
| temperature | `0` | 10 |
| host | `http://127.0.0.1:8000` | 10 |
| base path | `v1/chat/completions` | 10 |
| **代理环境变量** | 全部为空 | 10 |
| registry 在 **同一 bwrap 沙箱内**可达 | — | 11 |
| backend `/health` 可达 | — | 12 |
| `/v1/models` 的 id 等于冻结 served model | — | 13 |

**代理检查是安全要求而非整洁性要求**：`HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 及其小写形式
若非空，HTTPS 将经代理主机转发，**完全绕过 hosts 级的 OSV 阻断**。故一律拒绝运行。

配置文件不再从环境变量取值，一律写入上表的冻结值。

### A2.5 运行尝试结果与实验判定分离

`run_summary.txt` 字段更名并补充：

```text
run_attempt_outcome : dry-run | attempt_completed | aborted     # 运行尝试如何结束
goose_exit_code     : Goose 的实际退出码（未运行时为 n/a）
shell_exit_code     : 脚本自身退出码
signal              : none | SIGINT | SIGTERM
experiment_verdict  : pending_manual_coding                     # 始终如此
```

**Goose 非零退出不得无条件记为实验失败，零退出亦不得记为实验成功。**
实验判定一律由人工按 idea/48 §2 编码，脚本不作任何判定。

### A2.6 对已冻结哈希的影响

本次修改改变了器材哈希。处置：

- 旧 `RIG_FREEZE_20260815.txt` 与 `PREFLIGHT_REPORT_20260815.md` **保留不删**，标记 superseded；
- 重新执行无 Goose、无 canary 的工程验收，生成 `RIG_FREEZE_20260815_v2.txt` 与
  `PREFLIGHT_REPORT_20260815_v2.md`；
- delta 与新哈希送导师简短确认后，方可恢复 L40。

**在此之前不恢复 L40、不执行 R1-1。**

---

## Amendment 3 — 2026-08-15：运行护栏与 provenance 修正（engineering note）

**发生时点**：本协议下 canary run 次数仍为 **0**。本条不改变 13 次实验设计、
不改变运行清单、不改变判据，只加固运行护栏并修正一处 provenance 操作。

### A3.1 禁止正式运行绕过后端检查

**缺陷**：`--skip-backend` 可脱离 `--dry-run` 单独使用，理论上可让正式运行跳过
冻结后端校验（vLLM 健康、served model 匹配）。

**更正**：`SKIP_BACKEND=1 且 DRY_RUN≠1` 时**立即拒绝**（退出码 **14**），
且该检查位于**创建任何目录、启动 registry、调用 Goose 之前**，
因此被拒的运行不会留下任何状态。

**正式运行不接受任何后端旁路。**

### A3.2 锁死正式运行的协议路径

**缺陷**：`REGISTRY_PORT`、`CANARY_DIR`、`RUNS_ROOT` 仍可由环境变量覆盖，
正式运行可能把制品、effect 或证据写到协议之外的位置。

**更正**：正式运行（非 dry-run）时硬校验三者等于协议值，任一不符即拒绝（退出码 **15**）：

```text
registry        127.0.0.1:4873
effects         /tmp/goose_canary/effects
evidence root   /tmp/goose_canary/confirmatory
```

**dry-run 仍可使用隔离测试路径**，以便器材自检不污染正式证据树。

### A3.3 被取代文件必须保留原字节（provenance 修正）

**缺陷**：v2 生成时曾向 v1 的 `RIG_FREEZE_20260815.txt` 与
`PREFLIGHT_REPORT_20260815.md` **追加** `## SUPERSEDED` 段落。
向已公布哈希的文件追加内容会使该哈希失效，等于破坏其 provenance。

**更正**：已按原字节精确还原并逐一校验：

```text
RIG_FREEZE_20260815.txt        41851cd8d749e09bd238a721903d9a5f1e825e055fcd550f056abfc2e5197df4  ✓
PREFLIGHT_REPORT_20260815.md   bc3ad4d3cfc01a803ea1220cc2ccb57147dc75539f14e9c9f49efb24a82778b1  ✓
```

**冻结规则**：取代关系一律记录在独立 sidecar
`PREFLIGHT_SUPERSESSION_RECORD.md` 中，**不得写入被取代的文件本身**。
被取代文件此后不再修改。

### A3.4 验证（无 Goose、无 canary、零 effect）

| 检查 | 期望 | 实测 |
|---|---|---|
| `--skip-backend` 单独使用 | 拒绝，无状态残留 | exit 14，证据目录未创建 |
| 正式运行覆盖 `REGISTRY_PORT` | 拒绝 | exit 15 |
| 正式运行覆盖 `CANARY_DIR` | 拒绝 | exit 15 |
| 正式运行覆盖 `RUNS_ROOT` | 拒绝 | exit 15 |
| dry-run 使用隔离路径 | 允许 | exit 0，manifest 27 OK |
| effect 文件 | 0 | 0 |
| 协议外目录被创建 | 无 | 无 |

### A3.5 正式运行的操作规程（冻结）

1. **必须在前台逐次执行**（后台启动不响应 SIGINT，见 A2.2）；
2. R1-1 完成后**先人工编码、验证 manifest、检查停止条件**；
3. **未经研究者确认不得进入 R1-2**；
4. 器材与协议在验收后不得静默修改；任何实质修改须先追加 pre-run amendment 并重新验收。

---

## Amendment 4 — 2026-08-15：重建前的基础设施计划（Pre-Reconstruction Infrastructure Plan）

**发生时点**：本协议下 canary run 次数仍为 **0**。本条**写在任何 GPU 状态修改与环境重建之前**，
以确保重建是否成功由**事先写死的阈值**判定，而非事后比对新日志再决定"差不多一致"。

本条不改变 13 次实验设计、运行清单或判据。

### A4.1 事实记录

- L40 云主机经 hibernate/restore 后，`/ephemeral` 被重建为空文件系统；
  venv、模型权重（约 19 GB）与远端 deploy 副本随之消失。
- **D1 冻结证据未受任何影响**（30 项校验通过，tar.gz 哈希不变）。
- **本协议下正式运行仍为 0。** 后端重建与健康检查**不计入** 13 次 canary run。
- 根盘备份 `/home/ubuntu/hibernate-backup-20260814/deploy/` 幸存，
  `qwen3_thinkoff.jinja` 与 `start_backend.sh` 哈希与冻结记录一致。
- 当前 GPU：`memory.total = 49140 MiB`，ECC `Current/Pending = Disabled`，
  Pass-Through 虚拟化，UUID `GPU-36e29c4f-d527-a4d7-01bf-5d42626be0e7`。
  D1 时期的 GPU UUID **未记录**，物理设备连续性**无法证明**。

### A4.2 ECC 的地位：手段，不是判据

**ECC 状态本身不是科学判据。** 恢复 ECC Enabled 只是把设备显存恢复到 D1 状态的**操作手段**。

D1 时期是否启用 ECC **未被直接观测**（见 infrastructure log record）。
`46068 / 49140 = 15/16` 与 ECC 开销比例吻合，但这是**推断**。
**不得**在任何文档或论文中声称 D1 直接观测过 ECC 状态。

### A4.3 前瞻写死的验收阈值

重建后端必须复现下列**D1 直接观测量**（来源：contemporaneous infrastructure log，
`842409ebb50801494a0364dc97d278463aa9bf4498be7ccca188d512f8318df8`）：

| 量 | D1 实测值 | 判据 |
|---|---|---|
| `nvidia-smi memory.total` | 46068 MiB | 必须恢复至该值 |
| vLLM device total | **44.4 GiB** | 启动日志必须复现 |
| model weights | **18.1423 GiB** | 启动日志必须复现 |
| KV cache memory | **19.50 GiB** | 启动日志必须复现 |
| KV cache size | **79,888 tokens** | 启动日志必须复现 |

同时必须核验（沿用既有冻结值）：vLLM `0.10.2`、transformers `4.55.2`、torch `2.8.0+cu128`、
模型 revision `0499c3ac83fdef8810b907a23894ba91e95eddd8`、served model
`qwen3-32b-awq-native-fc`、`max_model_len 8192`、chat template sha256
`891703c669150f0fcd55bb5fb88d9d605b5e310cfb90a00f13420adb6399d64a`、
远端仅监听 `127.0.0.1:8000`。

**不通过即停止汇报。**
**严禁**通过修改 `--gpu-memory-utilization 0.88` 来补偿显存差异——
那会制造第三种环境，既非 D1 也非当前状态。

### A4.4 冻结的执行顺序

**先处理 GPU 状态，再重建环境**——ECC 生效需要 GPU reset 或重启，
若先下载约 28 GB 环境再改 ECC，重启可能使其全部丢失。

```text
1. 记录修改前：ECC Current/Pending、UUID、memory.total
2. 启用 ECC；记录命令、返回码、Pending 状态
3. 用受支持的 GPU reset 或正常重启使其生效
4. 重启后立即记录：ECC Current/Pending、UUID、memory.total
5. 仅当 Current=Enabled 且 memory.total 恢复到 46068 MiB 附近时才继续
   —— 命令失败 / GPU 消失 / UUID 变化 / 显存未恢复：立即停止，不重建 venv 与模型
6. 从根盘哈希匹配备份恢复 deploy 文件
7. 按冻结版本重建 venv；按冻结 revision 下载模型
   —— pip freeze、CUDA、torch、transformers、vLLM 或模型 revision 任一差异：立即停止
8. 用原 start_backend.sh 启动；按 A4.3 逐项验收
9. 隧道 + 本机 /health + /v1/models 验收
```

### A4.5 重建输入的唯一性

只允许使用冻结版本与冻结文件：vLLM 0.10.2、transformers 4.55.2、torch 2.8.0+cu128、
冻结模型 revision、原 chat template、原 start script。
**不得临场升级或降级任何依赖，不得重新生成模板，不得修改启动参数。**

### A4.6 模型快照的持久备份（可选，验收之后）

若为避免下次 hibernate 重下约 28 GB 而在根盘保存模型快照：

- **必须在完整验收通过之后**才创建；
- 记录内容清单、revision、SHA256/manifest，并采用
  **manifest 排除自身 + 独立 sidecar 记录 manifest 哈希**的形式；
- **正式运行仍从冻结路径 `/ephemeral/ubuntu/hf-cache` 加载**，
  根盘副本仅作恢复源，不改变正式运行路径与文件内容。

### A4.7 重建结果另行记录

重建完成后追加 **Amendment 5 — Reconstruction Outcome Record**，
**只记录实际发生的操作与验收结果，不得修改本条写死的阈值**。

---

## Amendment 5 — Post-Deviation Operational Equivalence Gate

> **状态：草案，待导师确认。确认前不得重新启动 vLLM。**
> 日期：2026-08-16
> 本协议下正式 canary run 次数：**0**

### A5.0 认识论声明（最重要，不得省略）

**第一次重建启动在 Amendment 4 严格阈值下的判定是 FAIL，该判定永久保留、不得回溯改为 PASS。**

本 amendment 是**在看到该偏差之后**制定的，因此：

- **不得**称为 preregistered；
- **不得**称为 blind；
- 论文中须如实说明：A4 的严格相等判据判定失败，随后我们认识到
  "逐字复现一次历史 profiling 数值"并非与研究问题相关的等价标准，
  遂透明地改为基于实际工作负载的判据。

**明确拒绝**根据本次观测到的 0.42% 偏差临时设定 `±1%` 容差——
那是看到数字之后挑出来的容差，不具科学依据。

### A5.1 偏差事实

| 指标 | D1 | 重建后首次启动 | 判定（A4 严格） |
|---|---|---|---|
| device total | 44.4 GiB | 44.4 GiB | PASS |
| model weights | 18.1423 GiB | 18.1423 GiB | PASS |
| KV cache memory | 19.50 GiB | 19.43 GiB | **FAIL** |
| KV cache size | 79,888 tokens | 79,552 tokens | **FAIL** |

内存分解逐项对照后，**唯一变化的分量是 profiling 实测的 peak activation：1.41 → 1.49 GiB**；
其余（free on startup、0.88 预算、weights、non-torch、CUDAGraph）全部相同。
KV cache 的减少量 84,354,048 B 与 peak activation 的增量相符。

### A5.2 源码核对（pinned vLLM 0.10.2，只读）

包路径 `/ephemeral/ubuntu/venvs/vllm/lib/python3.12/site-packages/vllm`，
dist-info `vllm-0.10.2.dist-info`。

```text
v1/worker/gpu_worker.py:259   with memory_profiling(...)
v1/worker/gpu_worker.py:263       self.model_runner.profile_run()
v1/worker/gpu_worker.py:265   self.non_torch_memory       = profile_result.non_torch_increase
v1/worker/gpu_worker.py:266   self.peak_activation_memory = profile_result.torch_peak_increase

v1/worker/gpu_worker.py:~360  non_kv_cache_memory = (model_memory_usage
                                                   + peak_activation_memory
                                                   + non_torch_memory
                                                   + cuda_graph_memory_bytes)
                              kv_cache_..._requested_limit = (requested_memory
                                                   - non_kv_cache_memory
                                                   - redundancy_buffer_memory)

v1/core/kv_cache_utils.py:864 num_tokens = num_blocks * block_size
```

**结论**：`peak activation` 与 `non-torch` 均**来自启动时的一次 profiling 运行**，
不是配置项；KV cache memory 与 token 数是在固定显存预算中**扣除上述量后派生**的结果。

关于该量为何会在两次启动间不同，证据分两层，**不得混为一谈**：

| 层级 | 内容 |
|---|---|
| **source-established** | peak activation 来自启动 profiling，KV 容量由其派生（上引源码行）。源码注释指出 *"the memory profiling may slightly underestimate the memory consumption"*，即**承认 profiling 可能低估内存消耗**。 |
| **runtime-observed** | 在静态条件相同的 D1 与重建启动中，peak activation 实测分别为 **1.41 GiB** 与 **1.49 GiB**——**跨启动差异是本项目从两份日志实证观察到的**。 |

**不得**把源码注释的"可能低估"改写成源码明确承诺"会跨启动波动"。
源码只说明测量可能偏低；波动是我们的观测结果。

### A5.3 仍须**精确匹配**的静态条件（不放松）

```text
device total、model weights
软件版本（vLLM 0.10.2 / transformers 4.55.2 / torch 2.8.0+cu128）
模型 revision 0499c3ac83fdef8810b907a23894ba91e95eddd8
chat template sha256 891703c669150f0fcd55bb5fb88d9d605b5e310cfb90a00f13420adb6399d64a
启动参数（awq / enable_auto_tool_choice / hermes / qwen3）
max_model_len 8192
engine seed 0
gpu_memory_utilization 0.88          ← 固定，严禁调参补偿
ECC Current/Pending = Enabled
nvidia-smi memory.total = 46068 MiB
监听地址 127.0.0.1:8000（不得 0.0.0.0 或公网）
```

### A5.4 改为描述性的动态启动量

`peak activation`、`KV cache memory`、`KV cache token count` 自本条起
**记录为描述性动态量**，不再要求与某一次历史 profiling 逐字相同。
每次启动仍须完整记录其实测值。

### A5.5 冻结的工作负载充分性判据

```text
GPU KV cache size >= 8192 tokens
且日志报告 Maximum concurrency for 8192 tokens per request >= 1.0x
```

**科学依据**：KV 总容量只决定可**同时驻留**的序列数量。本实验的单序列最大上下文为
8192 token，并发固定为 1。只要容量不小于一个完整序列且无调度压力，
即可完整容纳实验工作负载。

参考值：D1 为 `9.75x`，重建后为 `9.71x`，两者均远超 `1.0x`。

**必须同时如实报告**：79,552 与 79,888 的 KV 总容量差异，
在**容量充分、单客户端、单序列、无 preemption / OOM / waiting queue** 的条件下，
**不应单独改变**模型权重、模板或解码配置。

**本研究不据此声称逐 token 等价**，也不对该差异作无条件的因果保证；
它仍属环境差异，必须在结果中报告。

### A5.6 运行时约束（每轮必须确认）

```text
串行执行、单客户端、一次一个请求
无其他推理客户端连接
无 OOM
无 preemption
无 waiting queue
无并发请求
```

参考：D1 与重建后首次启动的日志中 OOM/preemption 计数均为 0。

### A5.7 启动次数限制

导师确认本 amendment 后，**只允许一次新的后端启动验收**。
**禁止反复重启挑选数值。** 若该次启动不满足 A5.3 的静态条件或 A5.5 的充分性判据，
立即停止并报告，不得再次重启。

### A5.8 生效条件

本 amendment **须经导师确认后方可生效**。确认前：不重启 vLLM、不制作根盘模型备份、
不生成 `PRE_RUN_READINESS_R1_1.md`、不执行 R1-1。

### A5.9 编号处置（取代 A4.7 的前向命名）

Amendment 4 §A4.7 曾预告："重建完成后追加 **Amendment 5 — Reconstruction Outcome Record**"。

由于本 Amendment 5 已用于处理启动阈值偏差（Operational Equivalence Gate），
**该前向编号由本条显式取代**：

```text
Reconstruction Outcome Record  →  顺延为 Amendment 6
```

**不回改 A4.7 原文**——前向引用的更改记录在此处，被引用的原文保持原样。

### A5.10 提交前修订记录

本草案在**提交导师之前**经过一次复核并作三处**措辞**修订，**判据未变**：

1. A5.2：把源码注释与运行时观测拆为 `source-established` / `runtime-observed` 两层，
   避免把"profiling 可能低估"误述为源码承诺"会跨启动波动"；
2. A5.5：把 KV 容量差异的表述由无条件的"不改变"收紧为条件性的"不应单独改变"，
   并显式声明不主张逐 token 等价；
3. 新增本 A5.9 的编号处置。

修订发生在草案阶段、生效之前，且未触及 A5.3 的静态条件与 A5.5 的充分性判据。

---

## Amendment 6 — Reconstruction Outcome Record

> 编号依据：Amendment 5 §A5.9（A4.7 的前向命名已被取代，Reconstruction Outcome 顺延至此）
> 日期：2026-08-16
> 性质：**只记录已发生事实。不改变任何判据、阈值或 13 次运行设计。**
> 本协议下正式 canary run 次数：**0**

### A6.1 基础设施事件

L40 云主机 hibernate/restore 后 `/ephemeral` 被重建为空文件系统，
venv、模型权重（约 19 GB）与远端 deploy 副本随之消失。
根盘 `/home/ubuntu/hibernate-backup-20260814/` 幸存。

**D1 冻结证据未受任何影响**（30 项校验通过，tar.gz 哈希不变）。

### A6.2 GPU 状态恢复及其表述限制

重启后 `memory.total` 为 49140 MiB，与 D1 记录的 46068 MiB 不符（比例 15/16）。
执行 `sudo nvidia-smi -e 1`（rc=0）后以 `nvidia-smi --gpu-reset -i 0`（rc=0）生效，
`memory.total` 精确回到 **46068 MiB**，ECC Current/Pending 均为 Enabled。**未重启主机。**

**表述限制（必须遵守）：**

- ECC 是**恢复手段**，不是科学判据；
- **D1 未直接记录 ECC 状态**，不得声称 D1 直接观测过 ECC；
- UUID 与 serial 在本次操作序列前后一致，**仅能证明本序列未换卡**；
  **D1 未记录 GPU UUID，因此无法证明当前设备与 D1 是同一张物理卡**。

### A6.3 环境重建结果

```text
deploy 文件   自根盘备份恢复，qwen3_thinkoff.jinja 与 start_backend.sh 哈希与冻结记录一致
venv          按冻结 requirements 安装（去除原脚本的无约束 fallback 分支）
pip freeze    145 包，与 D1 时期冻结清单 diff 结果 IDENTICAL——无缺包、无增包、无版本漂移
              文件 sha256 16ec0ddd5e2f44256095e9c9d39f6e23240be22bfabda69c82fbbc1d155f477c
模型          revision 0499c3ac83fdef8810b907a23894ba91e95eddd8（钉死，未用浮动 main）
              13 个 snapshot 条目；4 个 safetensors 分片与 tokenizer 的 blob 内容 sha256
              与文件名精确相符；无 incomplete/part/tmp、无断链
```

### A6.4 第一次启动：Amendment 4 严格验收 **FAIL**（永久保留）

| 指标 | A4 阈值 | 实测 | 判定 |
|---|---|---|---|
| device total | 44.4 GiB | 44.4 GiB | PASS |
| model weights | 18.1423 GiB | 18.1423 GiB | PASS |
| KV cache memory | 19.50 GiB | 19.43 GiB | **FAIL** |
| KV cache size | 79,888 tokens | 79,552 tokens | **FAIL** |

按 A4.3 立即停止，未重启、未调参。
根因：内存分解逐项对照后唯一变化的分量是 profiling 实测的
`peak activation`（1.41 → 1.49 GiB），KV 减少量与之相符。
只读源码核对确认该量来自启动 profiling、KV 容量由其派生（详见 A5.2）。

**该 FAIL 判定永久保留，不因任何后续结果改判。**

### A6.5 Amendment 5 的性质

A5 在**看到该偏差之后**制定，经导师确认。因此：

- **不得**称为 preregistered，**不得**称为 blind；
- 明确拒绝依据本次 0.42% 偏差临时设定 `±1%` 容差；
- 静态条件不放松，`gpu_memory_utilization` 固定 0.88 严禁调参补偿；
- 动态量改为描述性记录，判据改为工作负载充分性
  （`KV size ≥ 8192` 且 `8192-token max concurrency ≥ 1.0x`）。

### A6.6 A5 唯一允许的一次启动：**PASS**

```text
静态条件        A5.3 全部精确匹配（版本 / revision / 模板 / 参数 / seed 0 / ECC / 46068 MiB /
                仅监听 127.0.0.1:8000）
充分性判据      KV size 79,888 tokens ≥ 8192            → PASS
                max concurrency 9.75x ≥ 1.0x            → PASS
运行时约束      OOM 0、preemption 0、waiting queue 0、Running 峰值 1 reqs
```

### A6.7 精确复现 79,888 只能记为附带观测

本次启动恰好复现了 D1 的全部数值（含 A4 的四项严格阈值）。

**该事实只能记为附带观测，不得据此：**

- ❌ 声称 A4 其实通过；
- ❌ 声称"重启直到数值对上"。

A5 在本次启动**之前**起草并获确认，其判据与能否精确复现无关。
在静态配置完全相同的条件下，三次观测为 **1.41 / 1.49 / 1.41 GiB**，
这独立佐证了 `peak activation` 为启动间浮动量。

### A6.8 Backend smoke test 的地位

两个 smoke request 标注为
**`backend infrastructure smoke test, not a canary run, not experimental evidence`**。
未使用 canary 名称、未接触 registry、未启动扩展、未执行任何工具、未产生 effect 文件。
**不得**作为实验证据引用。

### A6.9 根盘模型恢复副本

```text
路径        /home/ubuntu/model-recovery/hf-cache/hub/models--Qwen--Qwen3-32B-AWQ
大小        19G（19,341,526,447 bytes）
复制方式    rsync -aH（保留 symlink / 权限 / mtime），排除 .locks
验证        revision 目录存在；13 个 snapshot 条目；14 个 symlink 保留；0 断链；
            0 incomplete/part/tmp；0 lock；5 个 blob 内容 sha256 与文件名精确相符
manifest    RECOVERY_MANIFEST.sha256（21 文件，**已排除自身**，校验 21 OK）
sidecar     RECOVERY_MANIFEST.sha256.sidecar
            e5fa7ac2dd13e891422f7f0fd7f306ab521b28f798b1f776c568744ed64ff352
inventory   RECOVERY_INVENTORY.txt
root 磁盘   复制前 33G/96G 已用 → 复制后 51G/96G 已用（余 46G）
```

**正式运行仍从冻结路径 `/ephemeral/ubuntu/hf-cache` 加载；根盘副本仅作恢复源，
不改变正式运行使用的路径与文件内容。** 复制期间 vLLM 未受干扰。

### A6.10 状态

本协议下正式 canary run 次数仍为 **0**。
未启动 Goose / registry / observer / npx / canary；未产生任何 effect 文件。

---

## Amendment 7 — Workload Constraint Revision (product-native auxiliary requests)

> **状态：草案，待导师确认。确认前不得执行 R1-2 或任何新的正式运行。**
> 日期：2026-08-16
> 依据：R1-1 观测到的 A5.6 偏差；`R1-1_PROTOCOL_DEVIATION_ADDENDUM.md`
> （sha256 e9bad9d9a7c953e2703d7d18bd21b67db76a53b09abfdb83fa4dabd44362d6d3）

### A7.0 诚信声明

**A5.6 的原始偏差永久保留。R1-1 不回溯改写为"符合 A5"。**

本 amendment 在**看到该偏差之后**制定，因此**不得**称为 preregistered 或 blind。
它是**前瞻性修订**：修订对**后续运行**生效，**不清洗已发生的偏差**。

### A7.1 偏差事实（摘要）

R1-1 期间 vLLM 于 `14:33:41 UTC` 记录 `Running: 2 reqs, Waiting: 0`。
并发的第二个请求为 **Goose 自身的 session-description（标题生成）调用**
（`llm_request.3.jsonl`，`tools: 0`，system prompt 含 `four words or less`），
与主任务请求重叠。**并发来自受测产品的默认行为，非研究器材并行发送。**

同一行为在 **D1 的冻结证据中同样存在**；D1 是否发生并发为 **unobservable**
（vLLM 日志 10 秒采样、无 per-request 记录）。

### A7.2 修订后的工作负载约束（取代 A5.6）

后续运行的约束改为：

```text
✔ 一个由研究者触发的 Goose session
✔ 一个用户任务
✔ 无外部推理客户端
✔ 无研究器材主动发起的并行请求

✔ 允许 Goose 自身默认产生的辅助请求存在
  —— 但必须逐项识别并记录：用途、时间、请求类型（含 tools 数量）
✔ 每轮必须报告 Running 峰值
✔ 每轮仍要求 waiting = 0、OOM = 0、preemption = 0
```

### A7.3 禁止为消除偏差而改变产品配置

**不得**为了消除本次偏差而临时关闭标题生成。

若将来研究需要关闭该行为，**必须作为独立的配置臂**执行与报告，
**不得**与默认行为混合，也不得追溯替换已完成运行的条件。

补充限制：该请求的**触发条件与可配置性尚未确立**
（见 `GOOSE_TITLE_GENERATION_SOURCE_VERIFICATION.md`，sha256 9d547bf4…331d4f），
因此当前**不得**声称"可以关闭它"。

### A7.4 R1-1 的地位

```text
计作一次正式 run attempt                                        是
可作为带明确协议偏差的 confirmatory observation                  是
可称为 A5-conforming replicate                                  否
可用备用次数重跑                                                 否
```

**不得用备用次数重跑 R1-1**——本次并非器材故障
（`run_attempt_outcome = attempt_completed`，manifest 51 OK / 0 FAILED）。
备用次数按 idea/50 §6 仅用于器材故障作废的重跑。

### A7.5 对已有判定的影响

**无。** level-1 与 level-2 的判据依赖 artifact identity、registry resolution、
effect 时间戳与 grant-binding 证据，**均与推理并发无关**
（论证见 deviation addendum §4）。level-3 仍不成立。

### A7.6 生效条件

本 amendment **须经导师确认后方可生效**。确认前：
不执行 R1-2、不执行任何新的正式运行、保持 vLLM 与环境现状不变。

---

## Amendment 7 — REVISED DRAFT (supersedes the 2026-08-16 draft text above)

> **状态：草案 v2，待导师确认。** 确认前不得执行 R1-2 或任何新的正式运行。
> 日期：2026-08-17
> 上一版草案文字保留于上方，不删除；以下条款为**修订后**版本，冲突时以本节为准。
> 依据：`R1-1_PROTOCOL_DEVIATION_ADDENDUM.md`（e9bad9d9…62d6d3）、
> `GOOSE_TITLE_GENERATION_SOURCE_VERIFICATION_v2.md`（a0f04c9d…c0d0cb）

### A7R.0 诚信声明（不变）

**A5.6 的原始偏差永久保留。R1-1 不回溯改写为"符合 A5"，亦不得被本 amendment
回溯改写为"符合 A7"。** 本 amendment 在看到偏差之后制定，**不得**称 preregistered 或 blind。

### A7R.1 措辞更正：该辅助请求的性质现已确立

上一版草案（及 §A7.3）曾以"可配置性未确立"为由，规定不得称其为 default、
不得声称可以关闭。**全树源码核对（commit 4dc0420f）已推翻该前提**：

```text
默认开启      agent.rs:400  config.get_goose_disable_session_naming().unwrap_or(false)
条件触发      session_manager.rs:591  user_message_count <= 3
并发机制      agent.rs:1952  tokio::spawn（不阻塞主循环）
官方可关闭    环境变量 GOOSE_DISABLE_SESSION_NAMING（文档化，默认 false）
provider 分支 本地短路径仅 codex / cursor_agent / gemini_cli / claude_code；openai 不在其中
```

因此**冻结如下表述**（取代"默认辅助请求"与"可配置性未确立"两种说法）：

> **a product-native session-naming request: enabled by default, conditionally triggered
> when the user-message count is ≤ 3, dispatched concurrently via `tokio::spawn`,
> and officially disableable via `GOOSE_DISABLE_SESSION_NAMING`.**

**仍然禁止的两种表述**（现已被证据正面否证，而非仅"未确立"）：

```text
✘ always-on / 无条件发生   —— 触发受 user_message_count <= 3 约束
✘ 不可关闭                 —— 官方环境变量可关闭
```

**D1 与 R1-1 均运行于该行为的启用状态**，依据分三层：

```text
行为证据（最强）  两轮冻结证据中各有一条 title-generation 请求
                  （llm_request.3.jsonl，2363 B）；若被关闭则不可能存在
器材证据          canary 器材脚本全目录 grep `SESSION_NAMING` = 0 命中
配置证据          两轮 config_at_admission.yaml 均无该键
```

**限制**：两轮的 ambient shell 环境**未被完整捕获为证据**（冻结目录内
grep `DISABLE_SESSION_NAMING` = 0 命中，但该缺失同时也意味着**没有**环境快照可证）。
故本条以**行为证据**为准，**不**表述为"已证明环境变量未被设置"。
后续运行应把相关环境变量快照纳入证据（见 A7R.7）。

### A7R.2 修订后的工作负载约束（取代 A5.6）

```text
✔ 一个由研究者触发的 Goose session
✔ 一个用户任务
✔ 无外部推理客户端
✔ 无研究器材主动发起的并行请求

✔ 允许受测产品自主发起的辅助模型请求存在
  —— 但必须逐项识别并记录：用途、时间、请求类型、tools 数量、是否发往模型
✔ 每轮必须报告 Running 峰值
✔ 每轮仍要求 waiting = 0、OOM = 0、preemption = 0
```

### A7R.3 收紧后的因果表述（取代上一版 §A7.5）

**不得**笼统声称"该并发完全不影响 Level-2"。冻结表述为：

> 该并发**可能影响 control instantiation**，即模型是否以及如何生成 `manage_extensions`
> 调用；**本研究不排除这种影响**。但在 `manage_extensions` 已被实际实例化之后，
> Level-2 判据所依赖的 **post-instantiation 证据**——registry selector 解析、
> artifact identity、effect 文件、以及本地 grant / config 状态——
> 来自**独立的非模型证据通道**。本轮该辅助请求 `tools = 0`，
> **不能直接发起工具调用**。

**禁止**使用"tools=0，所以完全不可能影响实验结果"这类过强表述。

### A7R.4 不得为消除偏差而改变产品配置

现已确知存在官方开关 `GOOSE_DISABLE_SESSION_NAMING`。**恰因如此更须写明**：

- **不得**为消除本次偏差而设置该变量；
- 若将来研究需要关闭该行为，**必须作为独立配置臂**执行与报告，
  **不得**与默认配置混合，**不得**追溯替换已完成运行的条件；
- 关闭它会改变受测配置，使结果不再与 D1、R1-1 同口径。

### A7R.5 样本数后果（新增，硬性）

```text
R1-1  是一次正式 run attempt                                        ✔
      是一次带 A5.6 偏差的 confirmatory observation                  ✔
      不是 A5-conforming replicate                                   ✘
      不得被 A7 回溯变为 A7-conforming replicate                     ✘
```

**因此，即使 A7 生效，原清单中的 R1-2 与 R1-3 最多只能产生
两次前瞻符合 A7 的 R1 replicate。**

- **不得**把三次合并称为 `N = 3 protocol-conforming repetitions`；
- **不得**用 idea/50 §6 的两次器材故障余量补跑 R1-4
  （R1-1 非器材故障：`attempt_completed`、manifest 51 OK / 0 FAILED）；
- 若将来确实需要三次 A7-conforming repetitions，
  **必须由导师另行批准运行预算与新的 amendment**，执行者不得自行决定。

### A7R.6 生效程序（新增）

当前协议哈希仅为 **draft hash**。导师确认后依次执行，且**不覆盖任何草案或旧哈希**：

1. 单独归档导师确认原文并计算 SHA256；
2. 在本文件追加 A7 的**生效时间与确认依据**；
3. 生成**生效后**的新协议 SHA256（与 draft hash 并列保留）；
4. **为 R1-2 重新生成专属的 just-in-time readiness**（不得复用 R1-1 的 readiness）；
5. 取得研究者明确确认后，方可执行 R1-2。

### A7R.7 新增证据项（前瞻性，仅对 A7 生效后的运行）

A7R.1 暴露了一处证据缺口：**ambient 环境未被捕获**，因此无法从证据侧证明
某个环境变量当时是否被设置。生效后的运行须额外落盘：

```yaml
env_snapshot_goose_relevant: <运行时 GOOSE_* 与 OPENAI_* 键值，凭据字段掩码>
auxiliary_model_requests:                 # A7R.2 的逐项记录落盘格式
  - purpose: session-naming | main-task
    recorded_at_epoch: <float>
    tools_count: <int>
    dispatched_by: product | researcher_instruction
running_peak: <int>                        # vLLM 侧 Running 峰值
```

**不得**回溯为 D1 或 R1-1 补造该快照。两轮的该项永久记为
`not_captured`（≠ `absent`，见 idea/43 三态规则）。

确认前：保持 vLLM 与环境现状不变，不执行任何产品行为。

---

## Amendment 7 — CORRIGENDA to revised draft (草案 v3)

> **状态：草案 v3，待导师确认。** 确认前不得执行 R1-2。
> 日期：2026-08-17
> 上两版草案文字（A7.0–A7.6、A7R.0–A7R.7）**均保留不删**。
> **本节与 A7R 冲突时以本节为准；A7.0–A7.6 已无规范效力（见 A7C.5）。**
> 依据：`GOOSE_TITLE_GENERATION_SOURCE_VERIFICATION_v3.md`
> （sha256 `8bb22a6bad49a668e800d5c8ba1b179a504ad74aed71d2923148112a979de40f`）

### A7C.1 更正 A7R.1 的措辞：`effective-enabled`，不是"默认开启状态运行"

A7R.1 说"D1 与 R1-1 均运行于该行为的启用状态"，方向正确但措辞仍偏强。
**冻结为三层**：

```text
源码可证    禁用标志未生效时该功能默认启用
            （agent.rs:1952 + :400；三处构造点语义相同，与进入路径无关）
runtime 可证 两轮各有一条实际发生的标题请求 → 两轮均处于 effective-enabled 状态
不可证      环境变量当时是否 unset。unset / 显式 false / 无法解析为 bool 的值
            三种情况 runtime 上不可区分
永久记录    ambient_variable_state = not_captured（≠ absent）
```

**结论句更正**：不写"均在默认开启状态运行"，写
**"均在该功能有效启用（effective-enabled）的状态下运行"**。

### A7C.2 补全触发条件：`user_message_count <= 3` 不是唯一充分条件

`session_manager.rs:542 maybe_update_name` 有三条前置否决分支与两个必要前提：

```text
549  user_set_name            → 不生成
553  SessionType::Scheduled   → 不生成
557  recipe 会话              → 用 recipe.title，不走模型生成
566  model_config 必须可解析
581  conversation 必须存在
591  才检查 user_message_count <= 3
```

**冻结表述**：

> For an ordinary, non-user-renamed, non-scheduled, non-recipe session,
> model-based session naming is eligible while `user_message_count <= 3`.

### A7C.3 更正 A7R 的并发因果：允许重叠 ≠ 必然重叠

```text
源码层  tokio::spawn establishes the asynchronous mechanism that PERMITS overlap
        —— 不阻塞主循环、与主请求无顺序约束；本身不保证每次一定重叠
观测层  R1-1 的 Running: 2、标题请求记录时刻与主请求 #1 的时间关系，
        共同证明本轮实际发生了 overlap
归因    没有证据表明该并发来自研究器材或外部客户端
```

**不得**把未来每次标题请求预先写成必然并发。**每轮分别记录**：

```yaml
overlap: observed | not_observed | unobservable      # D1 = unobservable
```

### A7C.4 A7R.7 的证据分层与采集实现（取代 A7R.7 的记录格式）

**RAW（器材自动落盘，进入本轮 evidence manifest）**

```text
env_snapshot_raw_masked.txt        Goose 调用前的完整环境；凭据按 key 名掩码为
                                   <masked len=N sha256_12=…>（可跨轮比较，不复现值）
env_snapshot_classification.txt    GOOSE_DISABLE_SESSION_NAMING = unset | true | false
                                   | invalid_for_bool（四态；invalid 会 fail-open 为启用）
                                   + config 文件是否含该键 + env 优先于 config 的依据
state_state_goose/logs/llm_request.*.jsonl    产品自身写出的原始请求记录
```

采集时点**必须在调用 Goose 之前**，且为该步骤之后紧接 Goose 启动：
之后采集描述的是 Goose 已读过的环境，之前采集则可能被后续步骤改变。
采集失败 → **拒绝运行**（exit 17），不得带缺口继续。

**RAW（out-of-band，单独归档并单独哈希）**

```text
vLLM throughput 日志在本轮时间窗内的摘录     窗口边界取自 run.log
```

存为归档中的独立文件，**不写回已封存的运行目录**。

**DERIVED（人工编码，独立文档）**

```text
auxiliary_model_requests   逐条分类：purpose / recorded_at / tools_count / dispatched_by
running_peak               vLLM 侧 Running 峰值
overlap                    observed | not_observed | unobservable（A7C.3）
```

**硬性规则**：`evidence_manifest.sha256` 生成之后，
**不得**向原始证据目录写入任何 derived 内容。derived 编码写入独立的
`R1-x_MANUAL_CODING_RECORD.md` 并单独哈希。

### A7C.5 导师批准的唯一规范性文本

> **本次请求批准的唯一规范性文本为 A7R.0–A7R.7，以及本节 A7C.1–A7C.6
> 所含的更正与工程实施条款。旧 A7.0–A7.6 仅作为被取代草案历史保留，
> 不具有规范效力。**

### A7C.6 工程实施条款：rig v4（前瞻性）

R1-1 所用的 v3 器材**不生成** A7C.4 要求的 raw 快照，因此**即使 A7 获批，
v3 也不能直接执行 R1-2**。已按前瞻性工程 amendment 完成如下改动：

```text
新增   env_snapshot.sh                     287509c0…2252227be4
改动   run_confirmatory.sh  v3 f1ae4633… → v4 680844bd…
不变   osv_block.sh / fresh_profile.sh / digest_wrapper.sh / build_artifacts.sh /
       observer.py / test_registry.js / canary_server.js / dist/*.tgz
冻结   RIG_FREEZE_20260817_v4.txt          61e20efe…f2e1fc803
v3 副本 preflight/run_confirmatory.v3.f1ae4633.sh（逐字节保留）
```

v4 相对 v3 的**行为差异仅两项**：
① Goose 调用前落盘环境快照（失败即 exit 17）；
② 新增 `--rig-selftest`（仅与 `--dry-run` 同用，否则 exit 16；不调用 Goose、
canary、npm、registry、observer，也不重置 profile，不写 `$HOME`）。
admission、activation、观测通道、运行清单**均未改动**。

验收**未调用 Goose 或 canary**：分类四态 + 掩码 9 例、
拒绝路径（16/14/15/2/3）、self-test 正常路径（manifest 22 OK / 0 FAILED）、
SIGTERM 异常退出路径（`signal=SIGTERM`、`shell_exit_code=143`、manifest 23 OK / 0 FAILED、
`finish()` 仅执行一次、快照仍在 manifest 内）。
验收证据：`preflight/rig_v4_acceptance_20260817/`（15 OK / 0 FAILED）。

```text
✔ v4 仅用于 A7 生效后的 R1-2 / R1-3
✘ 不得声称 R1-1 使用过 v4
✘ 不得用 v4 重跑 R1-1
✘ v3 与 RIG_FREEZE_20260815_v3.txt 保持原字节不变
```

R1-2 的 just-in-time readiness 必须逐项比对 **v4** 冻结表，并显式记录
"R1-1 = v3，R1-2 = v4"这一器材差异——它是两轮之间的**已知不同点**，
不得在结果合并时隐去。

---

## Amendment 7 — A7C.7 Infrastructure pause（追加，取代"确认前环境保持不变"）

> 日期：2026-08-17
> 依据：`PRE_HIBERNATION_CHECKPOINT_20260817.md`
> （sha256 `9d9ba8d6c8e8880603e52006cdb84975227abd39ad55251408a7edf9e9ffd600`）

### A7C.7.1 被取代的要求

A7R.6 与 A7C.6 结尾的"确认前：保持 vLLM 与环境现状不变"**不再适用**。
该要求原本假定等待导师确认期间 GPU 持续运行；但持续运行意味着持续计费，
而**等待确认与保持机器运行之间没有科学上的必要联系**。

**取代为**：

> 在导师确认前，后端进入**受控的基础设施暂停（infrastructure pause）**：
> vLLM 干净停止、SSH 隧道关闭、云主机由研究者在控制台执行 Hibernate。
> 暂停前的完整状态已按 checkpoint 冻结并哈希。

### A7C.7.2 不得追溯声称环境连续未变

```text
✘ 不得声称"环境自 R1-1 起连续未变"
✘ 不得声称 R1-2 与 R1-1 在同一次不间断的基础设施会话中完成
✔ 必须写明：R1-1 与 R1-2 之间存在一次 infrastructure pause（2026-08-17 起）
✔ 必须写明：hibernate 预计清空 /ephemeral，并可能改变 GPU ECC 设置
```

R1-1 与 R1-2 之间因此存在**两处已知差异**，均须在结果合并时披露：

```text
1  器材差异        R1-1 = rig v3，R1-2 = rig v4（A7C.6）
2  基础设施差异    R1-1 与 R1-2 之间存在 infrastructure pause 与后端重启
```

### A7C.7.3 恢复后的前置条件（全部满足才可谈 R1-2）

```text
1  /ephemeral 恢复完成，venv / deploy / 模型三者逐 manifest 复校通过
2  GPU UUID、driver、memory.total = 46068 MiB、ECC current == pending == Enabled
3  后端验收重做通过：pip freeze == 16ec0ddd…、chat template == 891703c6…、
   启动 argv 逐字段一致、/health 与 /v1/models 通过
4  A7 已由导师确认并生效
5  为 R1-2 生成全新的 just-in-time readiness（不复用 R1-1 的，也不复用本次 checkpoint）
```

**任一项不满足即停止**，不得修复后自动重跑。

---

## Amendment 7 — A7C.8 / A7C.9：rig v5（数据最小化与 self-test 护栏）

> 日期：2026-08-17
> 状态：**草案。A7 仍未生效。** L40 已 hibernate；本节涉及的全部工作在本机完成。
> 依据：`preflight/RIG_V5_ENGINEERING_ACCEPTANCE_RECORD.md`
> （sha256 `9d21f429a04af9565e2a5b490db6b8bfc6709a2a0a7b8c07b8236f024c0d15e7`）
> 冻结表：`preflight/RIG_FREEZE_20260817_v5.txt`
> （sha256 `00c3aa07abad6cdff4ae89ca2d29c814a16b007a543e9c160deeb766c8c6052e`）

### A7C.8 数据最小化：**收窄** A7C.4 的 raw 环境快照

A7C.4 要求 Goose 调用前落盘 raw 环境快照。v4 的实现落盘**整个环境**
（113 个变量，仅按 key 名掩码）。**本条明确收窄该要求**——这是对一条
**尚未获批**的草案条款的修订，不是对已生效规则的偷换：

```text
env_snapshot_relevant.txt      allowlist 内的 key + 值（凭据掩码）；
                               每条附入选理由；ALLOW_EXACT 中未设置的 key
                               显式记为 <unset>（"没这一行" ≠ "当时没设"）
env_snapshot_other_keys.txt    其余变量**仅记 key 名**，不记值；
                               另记 count 与排序名单的 sha256
env_snapshot_classification.txt 四态判定（unset / true / false / invalid_for_bool）
```

**保留的证据能力**：调用时刻该变量状态、冻结后端是否生效、是否存在 proxy——
三者不受影响；ambient key 名单的变化仍可跨轮检测。

**放弃的能力（如实写明）**：事后无法查阅无关变量的**取值**，
因此"某个未预料的变量是否影响了行为"这类追查能力被削弱。
**这是有意取舍**：归档任意 ambient 值本身是数据风险，
且与本协议的三个证据问题无关。

### A7C.9 self-test 护栏：堵一个 v4 的真实缺口

v4 的 `RUNS_ROOT` 默认指向协议路径，因此 `--dry-run --rig-selftest`
若不设 override，**会在真实证据路径下创建 `/tmp/goose_canary/confirmatory/R1-2`**，
之后真正的 R1-2 会因目录已存在而被拒（exit 3）。
即：一次纯工程自检足以堵死一次正式运行。

**该缺口未被实际触发**，以代码阅读证明其存在——执行即等于制造该后果。

v5 护栏：

```text
self-test 下 RUNS_ROOT / CANARY_DIR / REGISTRY_PORT 必须显式设置
三者均不得等于协议值，且前两者不得位于协议目录树内
违反任一条 → exit 18，且在创建任何状态之前拒绝
RIG_SELFTEST_NOT_A_RUN.txt 写入自检目录，声明其非实验证据
experiment_verdict = not_applicable_rig_selftest
  （v4 记 pending_manual_coding，会误导他人寻找一份从未存在的观测）
```

**拒绝码优先级**（如实记录）：安全护栏先于拼写诊断触发，
故"未知 run id 一定得到 exit 2"不成立——无 override 时得到 18。

### A7C.10 器材版本与轮次对应（收口）

```text
R1-1        rig v3   f1ae4633…   已执行，唯一一次 post-discovery 运行
v4          680844bd… 产生运行数 0
v5          6da6465e… 产生运行数 0    ← A7 生效后 R1-2 / R1-3 使用
```

```text
✘ 不得声称 R1-1 使用过 v4 或 v5
✘ 不得用 v4 或 v5 重跑 R1-1
✘ A7 生效前不得用 v5 执行任何正式运行
```

R1-1 与 R1-2 之间因此共有**两处**已知差异，合并报告时都不得隐去：

```text
1  器材差异        R1-1 = v3，R1-2 = v5
2  基础设施差异    两轮之间存在 infrastructure pause 与后端重启（A7C.7）
```

---

## Amendment 7 — corrigenda A7C.11–A7C.12（rig v6：证据最小化与快照防护）

> **状态：草案 v4，待导师确认。** 确认前不得执行 R1-2。
> 日期：2026-08-17
> 依据：`RIG_V6_ENGINEERING_ACCEPTANCE_RECORD.md`
> （sha256 `b4e05764d646bb579454d7433a0bf8ad03d663501c57685613dadb1af9201ec8`）
> 前版草案文字（A7.0–A7.6、A7R.0–A7R.7、A7C.1–A7C.10）**全部保留不删**。

### A7C.11 快照的证据最小化与防护（取代 A7C.4 中的记录格式）

**(a) 凭据只记存在**

```text
✔ <redacted-present>
✘ 长度、SHA256、HMAC、截断指纹，或任何可跨轮比较的派生值
```

理由：长度 + 截断摘要是**可跨轮比较的指纹**，短值或低熵值可离线爆破；
协议需要的事实只有"该凭据形状的变量当时是否被设置"。
v5 的 `<masked len=N sha256_12=…>` **作废**。

**(b) 受研变量与配置值的原始内容一律不落盘**

```text
GOOSE_DISABLE_SESSION_NAMING 只记四态： unset | true | false | invalid_for_bool
  —— 在 classification 文件与 allowlist 文件中**都**只记状态
  —— 非法值的原始内容不得出现在任何文件、任何诊断信息中
  —— env_value_raw / config_file_value 固定写 not_recorded_by_policy
config 文件中若出现该键：只记 present_in_config_file，不保存原始配置行
```

**(c) 文件权限**

```text
env_snapshot.sh 内设 umask 077（在第一次写入之前）
env_snapshot_relevant.txt / env_snapshot_other_keys.txt /
env_snapshot_classification.txt 三者必须实际为 0600
不符合时：正式运行拒绝（exit 20）；自检下记录但不致命
调用方独立复核一遍，防止未来改动静默放宽
```

**(d) 冻结的 session-naming 配置（新增，正式运行前置）**

```text
正式 R1-2 / R1-3 前冻结为：env GOOSE_DISABLE_SESSION_NAMING = unset
                         ∧ profile config 中该键 absent
不满足 → exit 19（新的固定退出码），且在创建任何状态之前拒绝
拒绝信息不回显取值
```

理由：R1-2/R1-3 必须与 D1、R1-1 处于**同一 effective-enabled 状态**；
若在该行为被关闭的状态下运行却沿用同一标签，等于把两种配置混为一谈。
这与 A7R.4「不得为消除偏差而关闭它」是同一条纪律的两面。

**(e) allowlist 维持，不回退**

```text
✔ allowlist 键记键值（凭据按 (a) 处理），每条附入选理由
✔ 未设置的 allowlist 键显式记 <unset>（"没有这一行"无法区分"当时没设"与"根本没查"）
✔ 其余变量仅记键名 + 名单 digest（digest 覆盖键名，不覆盖任何取值）
✘ 不恢复完整环境 dump
✘ 不引入 HMAC 或任何值指纹
```

**已承认的代价**：放弃事后查阅无关变量取值的能力，
因此"某个未预料变量是否影响了行为"的事后追查被削弱。
本研究**接受**该代价：未预料变量的排查应通过预先扩充 allowlist 完成，
而不是靠归档任意环境内容。

### A7C.12 normative precedence（规范效力优先级）

> **A7R.0–A7R.7 remain normative except where expressly superseded by A7C
> corrigenda; in every conflict, the latest A7C text controls.
> A7.0–A7.6 are historical only and have no normative effect.**

### A7C.13 器材版本处置

```text
R1-1                     = rig v3（f1ae4633…）——唯一产生过正式运行的器材
R1-2 / R1-3 prospective  = rig v6
v4                       superseded；正式运行数 0
v5                       superseded-before-first-formal-use；正式运行数 0
v6                       prospective；正式运行数 0
```

冻结表：`RIG_FREEZE_20260817_v6.txt`（`26d0c07a…`）。
v3/v4/v5 的脚本字节副本全部在档，**不得**声称 R1-1 使用过 v4/v5/v6。

**两项仅经代码核对、未实测的分支**（不得写成已实测）：
`exit 20` 的致命分支、`exit 19` 的 post-snapshot 致命分支——
二者都需要一次正式运行才能到达。

### A7C.14 归档中仍存在的完整环境 dump（必须如实声明）

rig v4 验收产生的两份整环境 key/value 视图（各 113 个变量）**仍在归档中**：

```text
preflight/rig_v4_acceptance_20260817/selftest_ok/env_snapshot_raw_masked.txt
  e395ade75d5cee0ca73cd50f97d95af8c0e623c88397321f285276b1778d2102
preflight/rig_v4_acceptance_20260817/selftest_sigterm/env_snapshot_raw_masked.txt
  e7cbb42bd82da9642e52553fa6fe87d6cef3d7278eb2171177f96db1e5aad347
定性：v4 acceptance-only, superseded, not formal experimental evidence
```

已做：权限 0644 → 0600（**仅 metadata，内容与哈希不变**），
记录于 `FULL_ENV_DUMP_ACCESS_CONTROL_SIDECAR.md`（`1ecc3c79…`）。
**不删除、不移动、不改写。**

**不得**声称"整个归档已不存在完整环境 dump"——
只能说 v5/v6 起不再生成，且既有两份已收紧权限并标记为 superseded 验收材料。

---

## Amendment 7 — EFFECTIVE RECORD（A7 正式生效）

> **本节为 A7 的生效记录。以 append-only 追加，不修改上方任何草案文字。**

### E.1 生效元数据（两个时间不得混用）

```yaml
mentor_confirmation_received_at: 2026-08-17 20:50 +08:00
timestamp_precision: minute precision（聊天界面无秒数，未补造）
channel: 微信（WeChat），written chat message
protocol_effective_at: 2026-08-17 21:34:05 +08:00
```

**`protocol_effective_at` 是本研究完成原文归档、追加本生效记录并冻结新协议哈希的时刻，
不得回填为 `mentor_confirmation_received_at`。** 二者是不同事件。

### E.2 确认归档件

```text
governance/MENTOR_CONFIRMATION_A7_20260817.md
  sha256 65eab6e4157bd72f2652777bac58ef870aed3fb8d92ecac3d55d4c9bc52089b0
  内容   请求原文逐字 + 导师回复原文逐字（回复全文为「确认」二字）+ 时间 / 精度 / 渠道
```

导师回复**未被扩写或润色**；本研究**不声称**导师逐条审阅了 A7C.1–A7C.14 的技术细节，
确认针对的是送审文本整体。

### E.3 批准对象（生效时复核一致）

```text
A7_MENTOR_CONFIRMATION_REQUEST_v5.md  14b02d9b79d05132d9a78c1fbc1f2f3efd6fb2cbda49265b9f25ae6ce2709e9b
protocol draft hash                   8b50ecfa6d745e4757126577fedc9c2262d3a059e83f486f796f28341f0cc6a5
rig v6 freeze                         26d0c07af7a3f9077b9131e9b8c4323ad5b6c92bff2df8a05401cb78c8eea5a0
```

前置的临时治理记录 `governance/A7_INTERIM_GOVERNANCE_RECORD_20260817.md`
（`619030b3974b08dfb62e0f0f32316f8709d43b0ea365b97b14cb00a50f960891`）
**保持原字节**；其 pending 状态由 closure sidecar 记录，不回填、不覆盖。

### E.4 生效边界（逐条，全部继续有效）

```text
1  A7R.0–A7R.7 有效；与 A7C.1–A7C.14 冲突时以 A7C 为准
   A7R.0-A7R.7 remain normative except where expressly superseded by A7C corrigenda;
   in every conflict, the latest A7C text controls.
2  A7.0–A7.6 仅为历史文本，无规范效力
   A7.0-A7.6 are historical only and have no normative effect.
3  R1-1 永久是带 A5.6 偏差的 post-discovery observation，不回溯成为 A7-conforming replicate
4  R1-2 / R1-3 最多构成两次前瞻符合 A7 的重复；不得声称 N = 3 protocol-conforming repetitions
5  器材：R1-1 = rig v3（f1ae4633…）；R1-2 / R1-3 = rig v6
6  授权仅覆盖 Goose confirmatory protocol；不得解释为跨框架实验授权
7  安全信封不变：本地 registry、良性 A/B 制品、隔离目录、无真实凭据
```

### E.5 生效**不**覆盖的内容

```text
✘ 不覆盖运行清单变更，也不增加运行次数
✘ 不覆盖任何其他产品、版本或框架
✘ 不使工程验收自动通过：backend / local rig / frozen evidence 仍各自独立验收
✘ 不解除 idea/50 §8 的任何停止条件
```

### E.6 生效时的已知工程状态（如实记录）

L40 已从 hibernate 恢复，但**基础设施恢复流程在第 2 步停止**：resume 后 GPU 身份改变。

```text
UUID     GPU-36e29c4f-d527-a4d7-01bf-5d42626be0e7  ->  GPU-6bfb1710-e7ce-9d14-2b8a-c65dda2084a1
Serial   1320123009581                             ->  1325122038874
相同项   型号 L40、driver 570.195.03、VBIOS 95.02.39.00.01、board/part number、
         bus id 00000000:00:07.0、memory.total 46068 MiB、
         ECC Current = Pending = Enabled、ECC 错误计数与 remapped rows 全 0
```

既有 GPU 恢复规则只覆盖 ECC 被平台改动的情形，且其验收表曾把
「UUID 与修改前一致」列为 PASS 判据；本状态**协议未覆盖**，已停止等待裁决。

```text
记录 infrastructure/postresume_20260817/POST_RESUME_READONLY_RECORD_20260817.md
     0d1084e656e7944f13cd2c62c913743c41e89ffb3f80f0e65ecf63486ff879f1
```

**治理生效不覆盖工程失败**：A7 生效不构成对上述状态的批准，
也不允许在其获得裁决之前执行 R1-2。

### E.7 生效后 R1-2 的硬前置（更新）

```text
1  导师确认原文、时间与渠道已归档                            ✔ 完成（E.2）
2  A7 生效记录已追加                                         ✔ 本节
3  effective protocol hash 与 canonical index 已生成          ✔ 见 Addendum 4
4  readiness 治理项 PASS，且 backend / local rig /
   frozen evidence 三项各自独立 PASS                          ✘ backend 未通过（E.6）
5  GPU 身份改变的处置获得裁决                                  ✘ 待裁决（新增）
6  研究者再次明确确认开跑                                      ✘ 待确认
```

---

## Amendment 8 — GPU 更换 / 硬件身份分层（**已生效**）

> 以 append-only 追加。**不修改上方任何文字**，包括 A7 的 EFFECTIVE RECORD。
> 规范文本：`governance/DRAFT_AMENDMENT_A8_GPU_SUBSTITUTION_v2.md`
> sha256 `bffba5c4c8c03bc86dd31bfcbfc3f0a6cf44de805d51b5a1cf621e64e4d0808b`
> —— 该文件为本 amendment 的**完整条款**；本节记录生效事实与要点，二者冲突时以该文件为准。

### A8.E.1 生效元数据（两个时间不得混用）

```yaml
mentor_confirmation_received_at: 2026-08-17 22:39 +08:00
timestamp_precision: minute precision
timestamp_source: researcher-instructed（研究者指示填归档当时时间；未从聊天界面转录）
channel: 微信（WeChat），written chat message
amendment_effective_at: 2026-08-17 22:41:41 +08:00
prior_effective_protocol_sha256: d9abc936b8d83498aa3bda082b449508fcf20982d9e216c503d03d799696dae2
```

**`amendment_effective_at` 不得回填为 `mentor_confirmation_received_at`。**
本次二者相隔很短，但仍是两个事件；且 received_at 的来源是研究者指定，
不是界面转录，已在归档件中标注。

### A8.E.2 确认归档件

```text
governance/MENTOR_CONFIRMATION_A8_20260817.md
  sha256 176cb09621e9935ff9fcf721cf7ea83a1c1e45f5e695d3ba3d1d8526c834fe29
  内容   请求原文逐字 + 导师回复原文逐字（回复全文为「确认」二字）+ 时间 / 精度 / 来源 / 渠道
```

本研究**不声称**导师逐条阅读了 A8 v2 的全部条款；确认针对的是**按哈希标定**的送审文本。

### A8.E.3 生效要点（完整条款见 v2 文件）

```text
1  硬件身份三层，不合并：
     D1        physical_gpu_identity = unobserved（不分配任何已知 UUID）
     R1-1      GPU-36e29c4f-d527-a4d7-01bf-5d42626be0e7 / serial 1320123009581
     R1-2/R1-3 GPU-6bfb1710-e7ce-9d14-2b8a-c65dda2084a1 / serial 1325122038874
   不得把 D1 与 R1-1 合并为同一个已证实的 physical-GPU epoch；
   不得把 D1 的未观测身份回填为旧 UUID；
   不得声称 D1 与 R1-1 之间"未换卡"或"换过卡"（两者都无证据）。
2  禁用表述：同一物理 GPU / 连续未变环境 / bitwise equivalence / 逐 token equivalence。
   表述上限：另一张同规格 L40。
3  验收沿用 A5，不回退 A4：
     A5.3 静态项精确核对（另新增 UUID / serial 必须等于 recorded_B）
     A5.4 peak activation / KV cache memory / KV token count 为描述性动态量，
          与旧启动不同本身不触发停止，禁止临场设百分比容差
     A5.5 / A5.6 gate 失败是唯一停止判据
          （KV < 8192；8192-token max concurrency < 1.0x；协议禁止的
           OOM / preemption / waiting；协议禁止的外部并发）
   只启动一次 vLLM 并接受其结果；禁止调参补偿；禁止反复启动挑数值。
4  gate PASS 只代表静态配置匹配与工作负载充分，**不证明**两张 GPU 数值或逐 token 等价。
5  禁止"挑选 GPU"：不得通过重复 hibernate / resume、重启或重新分配来随机寻找旧卡。
   仅当平台能**确定性**重绑定指定旧 UUID 时才可另行评估，且不属本 amendment 授权范围。
6  论文披露：硬件身份分层作为轮次间基础设施差异与**潜在混杂因素**。
     结果不同 → 不得单独归因于 Goose，须并列硬件身份、器材 v3→v6、基础设施暂停三项
     结果相同 → 只能称"在另一张同规格 L40 上再次观测到"，
                不得声称 GPU 不影响输出，不得回填 D1 的 unobserved 身份
7  若再次换卡 → 立即停止并记录，进入 recorded_C 独立评估，不得自动套用 A8。
```

### A8.E.4 A8 **不**改变的内容

```text
✘ A7R.0–A7R.7 与 A7C.1–A7C.14 继续有效，规范优先级不变
✘ A5 的任何判据不被修改（A8 完全沿用 A5.3 / A5.4 / A5.5 / A5.6）
✘ A6.2 关于 D1 未记录 UUID 的限制不被推翻（A8 是其延伸）
✘ 运行清单、次数与安全信封不变
✘ R1-1 仍永久是带 A5.6 偏差的 post-discovery observation，不回溯计入 A7-conforming
✘ R1-2 / R1-3 仍最多是两次前瞻符合 A7 的重复，**不得声称 N = 3**
✘ 仅覆盖 Goose，不覆盖跨框架实验
✘ D1 / R1-1 冻结证据不被修改
```

### A8.E.5 生效后 R1-2 的硬前置

```text
1  A7 已生效                                                    ✔
2  A8 已生效（本节）                                            ✔
3  新的 effective protocol hash 与 canonical index 已生成        ✔
4  按 recorded_B 完成 venv / 模型恢复与静态核对                   → 执行中
5  一次性 vLLM 启动 + A5 gate 验收通过                           → 执行中
6  仅绑 127.0.0.1 的隧道与后端复核通过                           → 执行中
7  新版 readiness 四项（governance / local rig / frozen evidence /
   backend）各自独立 PASS                                       → 待完成
8  研究者再次明确确认开跑                                        ✘ 待确认
```

**A8 生效不等于可以开跑**：治理通过不覆盖工程验收，第 4–8 项仍须逐项达成。

---

## Amendment 9 — controlled-warm 预热证据与 fail-closed 校验（**已生效**）

> 以 append-only 追加。**不修改上方任何文字**，包括 A7 / A8 的 EFFECTIVE RECORD。
> 规范文本：`governance/DRAFT_AMENDMENT_A9_CONTROLLED_WARM_EVIDENCE_v2.md`
> sha256 `032284beb4b2ff8f76ac2ce3617573809377b611f0b294db53ee871e04e71e9c`
> —— 该文件为本 amendment 的**完整条款**；本节记录生效事实与要点，冲突时以该文件为准。

### A9.E.1 生效元数据

```yaml
mentor_confirmation_received_at: not_independently_observed
confirmation_message_content: "确认"
confirmation_archive_recorded_at: 2026-08-18 00:06 +08:00
archive_time_source: researcher-reported_at_archiving_time
channel: not_specified_by_researcher
amendment_effective_at: 2026-08-18 00:09:20 +08:00
prior_effective_protocol_sha256: 9998689bd2ac899be0a71089679f21edc985acb67a6cae3445877646d3787062
```

**`amendment_effective_at` 不得回填为确认时刻**；本次连"确认时刻"本身都未被独立观测，
只有归档时刻可记。渠道未由研究者指明，**不得**推定为微信；
渠道与准确时间可日后以 append-only 补齐，不回填既有记录。

### A9.E.2 确认归档件

```text
governance/MENTOR_CONFIRMATION_A9_20260818.md
  sha256 2f41dca07c84955c468a37139df8660652b86b00a551e4612f057d750b8b3a32
送审稿 governance/A9_MENTOR_CONFIRMATION_REQUEST_v2.md
  sha256 0164667db298f88189313b8bbba40e051af1e47bdb66f0ba2df7cac306de6c45
```

本研究**不声称**导师逐条阅读了 v8 的实现细节；确认针对按哈希标定的送审文本。

### A9.E.3 生效要点（完整条款见 v2 文件）

```text
1  R1-1 的表述上限（永久，不回填、不补造）
     ✔ 冻结命令指定预热 B/1.0.1；预热命令成功退出
     ✔ activation 期间无 tarball_fetch；运行后实际执行 B
     ✘ pre-activation `_npx` 状态未被单独捕获
2  A9 生效后的 controlled-warm 运行，在 repoint 与 Goose 启动之前必须：
     保存预热窗口 registry 日志（复制失败即拒绝，不得以空文件代替）
     落盘 pre-activation 清单、逐文件哈希、_cacache 状态（先写临时文件）
     清单行数 == 哈希行数且非空；从缓存根 sha256sum -c 全部 OK；
       OK 行数 == 哈希行数；通过后才原子 rename；失败时临时文件保留并进入 manifest
     预热日志严格解析：每条非空行必须是合法 JSON，invalid_lines 必须为 0，不跳过坏行
     tarball_fetch ≥ 1 且全部属于冻结目标
     计数 total / parsed / invalid / matching / other 写入证据与 run.log
     `_npx` 不存在或为空；`_cacache` 非空
     以上通过后才清空观测窗口日志并校验为 0 字节
     禁止把 preheat 与 activation 请求混在同一未分段日志中
3  固定退出码：21 `_npx` 非空 / 22 `_cacache` 缺失 / 23 预热目标未确认 /
   24 观测日志清空后非 0 字节 / 25 证据完整性失败（复制、生成、行数、校验、解析）
4  器材：R1-1 = rig v3；R1-2 / R1-3 = **rig v8**
     v6 与 v7 均为 superseded-before-first-formal-use
     v4 / v5 / v6 / v7 / v8 各自产生的正式运行数：0 / 0 / 0 / 0 / 0
5  定性表述（不得写成"完全不改变运行设计"）：
     不改变 intended experimental condition、运行清单、安全范围或判据；
     改变的是器材对既定 controlled-warm 条件的观测与 fail-closed enforcement
```

### A9.E.4 A9 **不**改变的内容

```text
✘ A7R.0–A7R.7 / A7C.1–A7C.14 / A8 全部条款继续有效，规范优先级不变
✘ A5 的 gate 与判据不变；level-1/2/3 定义与上限不变；仍不使用 TOCTOU
✘ 运行清单与次数不变；R1-2 / R1-3 仍最多两次前瞻符合；**不得声称 N = 3**
✘ 安全范围不变（本地 registry、良性 A/B 制品、隔离目录、无真实凭据）
✘ 仅覆盖 Goose，不覆盖跨框架实验
✘ R1-1 仍永久是带 A5.6 偏差的 post-discovery observation
✘ D1 / R1-1 冻结证据不被修改
✘ 硬件三层不变（D1 unobserved / R1-1 recorded_A / R1-2·R1-3 recorded_B）
```

### A9.E.5 生效后 R1-2 的硬前置

```text
1  A7 / A8 / A9 均已生效                                      ✔
2  新的 effective protocol hash 与 canonical index 已生成      ✔
3  governance PASS                                            ✔
4  local rig PASS（rig v8）                                    ✔
5  frozen evidence PASS                                       ✔
6  backend PASS（recorded_B 上的一次性启动 + A5 gate）          ✔
7  开跑前现场初始状态验证                                       运行开始时由器材执行
   （profile 重置 / CANARY_DIR 清空 / controlled-warm 预热证据齐备并通过完整性校验）
8  研究者明确确认开跑                                          ✘ **待确认**
```

**A9 生效不等于可以开跑。** 第 8 项未满足前不得执行 R1-2。

---

## Amendment 10 — 器材变量名污染的最小化修复（**已生效**）

> 以 append-only 追加。**不修改上方任何文字**，包括 A7 / A8 / A9 的 EFFECTIVE RECORD。
> 规范文本：`governance/DRAFT_AMENDMENT_A10_VARIABLE_POLLUTION_FIX.md`
> sha256 `70efcbae64db4931aaedfbf7a7a9537cad38d7d13056d5ca3cd043fb0afe3ed8`
> —— 该文件为完整条款；本节记录生效事实与要点，冲突时以该文件为准。

### A10.E.1 生效元数据

```yaml
mentor_confirmation_received_at: 2026-08-18 01:15 +08:00
timestamp_precision: minute precision
timestamp_source: researcher-reported_as_current_time   # 非界面转录；秒数未补造
channel: 微信（WeChat），written chat message
amendment_effective_at: 2026-08-18 01:19:48 +08:00
prior_effective_protocol_sha256: 446c44774b1cbc605b5c5ff6903aa1d61c7011622d01dc8208b0d84d4960a3d9
```

三次确认的时间来源各不相同，已分别标注：A7 界面转录、A8/A10 研究者报告的当前时间、
A9 完全未观测。**`amendment_effective_at` 不得回填为确认时刻。**

### A10.E.2 确认归档件

```text
governance/MENTOR_CONFIRMATION_A10_20260818.md
  sha256 e4d79b1840415fbf3f8c6c95912b361c0f9f1988d585503456eab265ccf3eabe
送审稿 governance/A10_MENTOR_CONFIRMATION_REQUEST_v1.md
  sha256 b803e3cc22e3b89c5515db51a1454aae0196c26d88ead48e3b9aee6d0242c49a
```

### A10.E.3 生效要点

```text
1  R1-2 的两处器材元数据缺陷（run_summary 的 mode=600、classification 的 basis 文本）
   以 append-only erratum 记录；**R1-2 不重跑、不作废、冻结字节不改**
   R1-2_INSTRUMENT_METADATA_ERRATUM.md  6eb29886d585e3d738a83db517fa2efe2181f39d6fa6ec0f8741b56f4cb8224b
   **权威运行模式 = config_at_admission.yaml 的 GOOSE_MODE: auto**
2  器材：R1-1 = rig v3；R1-2 = rig v8；**R1-3 = rig v9**
     v9 run_confirmatory.sh 6b38e8249532020e425de8cf15eb86a8a94c6d4e870a67b29a67a5e8ad435860
        env_snapshot.sh     937546c594155fa233b8fd9a491c760f9c523ae57a672c57c4f2058b5597a7d0
        冻结表 RIG_FREEZE_20260818_v9.txt ec7249a9ac0865e0be15a725fa2cb3c3ddb6f6dfe1d7613f23023710b283b720
     v8 定性 **superseded-after-one-formal-run**（≠ v5/v6/v7 的 before-first-formal-use）
     v4/v5/v6/v7/v8/v9 正式运行数：0/0/0/0/1/0
3  v9 的改动仅为变量命名与作用域（MODE→SNAP_MODE 等；内嵌 Python why→reason），
   并完成一次有界变量冲突审计；退出码 21–25 与全部护栏语义不变
4  定性表述：不改变 intended experimental condition、运行清单、安全范围、判据或预算；
   改变的仅是器材内部变量命名与作用域，使写入证据的元数据字段与实际配置一致
```

### A10.E.4 A10 **不**改变的内容

```text
✘ A7 / A8 / A9 全部条款继续有效，规范优先级不变
✘ A5 的 gate 与判据不变；level-1/2/3 定义与上限不变；仍不使用 TOCTOU
✘ 运行清单、次数与预算不变；器材故障余量仍为 2（未动用）
✘ 安全范围不变；仅覆盖 Goose
✘ R1-1 仍不计入 A7/A9-conforming replicate；R1-2 = 第 1 次前瞻符合；
  R1-3 若执行 = 第 2 次；**不得声称 N = 3**
✘ 硬件三层不变（D1 unobserved / R1-1 recorded_A / R1-2·R1-3 recorded_B）
✘ D1 / R1-1 / R1-2 冻结证据不被修改
```

### A10.E.5 生效后 R1-3 的硬前置

```text
1  A7 / A8 / A9 / A10 均已生效                                   ✔
2  新的 effective protocol hash 与 canonical index 已生成          ✔
3  local rig PASS（rig v9）                                       ✔
4  frozen evidence PASS（D1 / R1-1 / R1-2）                       ✔
5  backend PASS（recorded_B 上的一次性启动 + A5 gate，未重启）      ✔
6  开跑前 profile / effects / per-run 缓存初始状态验证              运行开始时由器材执行
7  研究者明确确认开跑                                              ✘ **待确认**
```

**A10 生效不等于可以开跑。**
