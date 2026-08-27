# SOURCES — mentor_authorization_drift_progress_20260818

> 每条主张 → 证据文件 → 使用的字段/章节。所有文件位于 `/home/forks/goose-canary-archive/`
> （记为 ARCH）或 `/home/forks/AResearch/Agent/hello-agents-lab/idea/`（记为 IDEA）。
> 本文件只索引已核对的记录；未列出的主张不得上 slides。

---

## P1 标题

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| Goose v1.45.0 case study | ARCH/D1_SOURCE_ROOTCAUSE_AUDIT.md | 头部：对象 tag v1.45.0，commit 4dc0420f… |
| Coordinated Disclosure Pending | IDEA/50 §10（披露协调条款） | §10 披露流程 |

## P2 一句话结果与当前状态

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 发现：引用文本不变、artifact A→B | ARCH/R1_GROUP_AGGREGATE_RECORD.md | §2 判据与观测（admission A；RuntimeArtifact canary-B；grant 仅可变 selector） |
| 一次盲发现 + 两次 conforming + 一次带偏差观测 | 同上 §0 三类证据；§8 R1 组结束状态 | 类别 A/B/C 定义；R1-4 不执行 |
| R3 未执行、VM 已 hibernate | ARCH/infrastructure/INFRASTRUCTURE_PAUSE_RECORD_20260818.md | §1 暂停前状态（未执行 R3a/R3b/R4×2/R5×2/R6×2）；§3 后端停止 |
| 恢复后须重建 readiness | ARCH/PRE_RUN_READINESS_R3a_v1.HIBERNATION_NOTICE.md | "恢复后必须重做"清单 1–9 |

## P3 研究问题

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 身份阶梯五层 | IDEA/42 A1.4 identity 等级（I0–I4 概念来源）；IDEA/48 §2.3 关键区分 | A1.4 表；§2.3 research_observed vs system_bound |
| digest 层缺失（Goose 侧） | ARCH/D1_SOURCE_ROOTCAUSE_AUDIT.md | §3 ExtensionConfig 字段集；sha256/digest 检索 0 命中 |

## P4 Goose 内部机制

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 九步机制链 | ARCH/D1_SOURCE_ROOTCAUSE_AUDIT.md | §2 完整调用链 [1]–[7]（含行号） |
| search 只暴露 name/description | 同上 §6 | extension_manager.rs:1998 摘录 |
| Auto 无条件 Allow | 同上 §5 | permission_inspector.rs:161 起 |
| OSV 检查、latest→version None | 同上 §4 | extension_malware_check.rs:99 / :154 |
| Command::new 原样传参、解析在进程外 | 同上 §2 结论段 | "`@latest` 的解析不在这条链上的任何一步" |
| 漂移位于授权引用与 RuntimeArtifact 之间 | ARCH/D1_SOURCE_ROOTCAUSE_AUDIT_ADDENDUM.md | A7 仍然成立的结论 1–2 |

## P5 受控实验设计

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| registry A/B 时间线 | ARCH/R1_GROUP_AGGREGATE_RECORD.md | §2（dist-tag admission→act 1.0.0→1.0.1，四轮一致） |
| 配置文本全程不变 | ARCH/R1_GROUP_AGGREGATE_RECORD.md | §2（grant 绑定：args 仅 …@latest）；R2-1 记录 §5（运行后配置与 admission 逐字节相同） |
| 多通道交叉确认 | ARCH/R2-1_MANUAL_CODING_RECORD.md §2；R2-2 同节 | 五条独立证据通道 1–5 |
| 安全信封四件套 | IDEA/50 §4 安全信封 | 逐项写死的限制 |

## P6 D1 盲发现

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| D1 唯一盲观测、协议终止于 D1 | IDEA/50 §0 认识论地位；头部"前置" | 原预注册协议 idea/48 已于 D1 终止 |
| admission A / activation B / 0 批准 | ARCH/R1_GROUP_AGGREGATE_RECORD.md §2；ARCH/D1_PRIVATE_MENTOR_REPORT.md | 批准提示 0；no_first_tool_approval_in_profile |
| L1/L2/L3 判据与四轮 level 分布 | ARCH/R1_GROUP_AGGREGATE_RECORD.md §2 | level-1 成立(附条件)；level-2 成立；level-3 不成立 |
| system_bound_digest absent（L3 无证据） | 同上 §2 | system_bound_digest absent，四轮一致 |
| D1 间隔约 9.85 s | /tmp/goose_canary/FROZEN_D1_20260814T230717/effect_timestamps.txt | mcp_initialize→first_tool_execution 差值 |

## P7 源码根因

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 中心句与六条事实 | ARCH/D1_SOURCE_ROOTCAUSE_AUDIT.md §3–§6 | extension.rs:176；permission_store.rs:12；:1998；:154；:99 |
| "确有安全检查、OSV 有效但正交" | ARCH/D1_SOURCE_ROOTCAUSE_AUDIT_ADDENDUM.md | A2（OSV 双目标对照表） |
| 配置+权限记录合并仍无 artifact 字段 | 同上 A3 | joint lack 表述 |
| 不写"所有防御同时失效" | 同上 A1 | 收紧后的冻结表述 |

## P8 R1 可重复性

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 表格四行全部字段 | ARCH/R1_GROUP_AGGREGATE_RECORD.md | §0 类别；§1 逐轮基本信息；§2 观测 |
| R1-1 偏差性质 | ARCH/R1-1_PROTOCOL_DEVIATION_ADDENDUM.md | §0 三层定性（A5.6 并发）；§1–2 请求身份 |
| 不得称 N=3 | ARCH/R1_GROUP_AGGREGATE_RECORD.md §0 硬性；§8 | 禁用表述清单 |
| rig 谱系（v3/v8/v9） | ARCH/ARCHIVE_CANONICAL_INDEX_ADDENDUM_11.md | A11.3 器材使用记账 |

## P9 R2 阴性对照

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| R2-1 执行 A、五通道证据 | ARCH/R2-1_MANUAL_CODING_RECORD.md | §2 通道 1–5；§0 三层定性 |
| R2-2 执行 A、参数逐字段相同 | ARCH/R2-2_MANUAL_CODING_RECORD.md | §1 冻结参数；§2 通道 1–5 |
| 两轮一致观测 | ARCH/R2_GROUP_AGGREGATE_RECORD.md | §2 两轮观测（RuntimeArtifact A；未发生漂移） |
| 允许的唯一总结句 | ARCH/R2-1 §3；R2-2 §3；R2_GROUP §0 | "把 selector 钉死为 exact version 阻止了本次 dist-tag 漂移" |
| 缓存条件差异 + R4 需要 | ARCH/R2_GROUP_AGGREGATE_RECORD.md §4 | 两个差异不可分离；R4 定义 |
| 版本号不是 digest | 同上 §0 禁止的表述；§6 剩余清单 | content binding 禁止；R3a/R3b 待跑 |
| R2 间隔 6.6671 / 6.6291 s | R2-1 §5；R2_GROUP §2 | effect 时间戳 |

## P10 当前证据能说什么

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 可说四条 | R1_GROUP §2/§5；R2_GROUP §2/§5 | 可重复观测；与 mutable selector 一致；阴性对照相容；多通道确认 |
| 不可说六条 | R1_GROUP §2 结论上限；R2_GROUP §0；IDEA/50 §0 | TOCTOU/批准/ACE/普遍性/content binding/benchmark |

## P11 R3–R6 与 benchmark

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| R3a/R3b 设计 | IDEA/50 A1.3 表 | digest-match 放行 / digest-mismatch 拒绝（退出码 4，无 B effect） |
| R4/R5/R6 次数与模式 | IDEA/50 §5 运行清单 + A1.4 | R4×2、R5×2、R6×2 |
| 恢复门槛 | ARCH/PRE_RUN_READINESS_R3a_v1.HIBERNATION_NOTICE.md | 恢复后必须重做 1–9 |
| 正式运行 5 / 上限 15 | ARCH/infrastructure/INFRASTRUCTURE_PAUSE_RECORD_20260818.md §1 | 计数 |
| benchmark 维度 | 本 deck 附录 D（源自 IDEA/43 编码手册 + IDEA/42 A7.2 三列） | 设计维度，未执行 |

## P12 组会决定

四个问题与定位句来自研究者本次汇报要求；定位句与 R2_GROUP §6、INFRASTRUCTURE_PAUSE §1 的状态一致。

## 附录 A（终端回放）

| 内容 | 证据文件 | 字段/章节 |
|---|---|---|
| 终端六行 | /tmp/goose_canary/FROZEN_D1_20260814T230717/terminal_trace.log | 全文（manage_extensions / canary_echo / canary-B 回显） |
| registry 两行 | 同目录 registry_access.jsonl | registry_start / dist_tag_repointed / packument_fetch |

## 附录 B（证据完整性）

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 六轮 manifest 数字 | ARCH/infrastructure/INFRASTRUCTURE_PAUSE_RECORD_20260818.md §2 冻结证据复核 | D1 外 30/0 内 28/1；R1-1 52/51；R1-2、R1-3 63/62；R2-1、R2-2 52/51（均 0 FAILED 除 D1 内层） |
| D1 内层 1 FAILED 成因 | ARCH/R1_GROUP_AGGREGATE_RECORD.md §3 | manifest 后追加 run_complete 一行；确定性证明；不回溯修改 |
| 协议谱系与 effective 哈希 | ARCH/ARCHIVE_CANONICAL_INDEX_ADDENDUM_10.md | A10.2 effective 216a615e…（A10，当前） |

## 附录 C（四轮 R1 对照）

| 主张 | 证据文件 | 字段/章节 |
|---|---|---|
| 器材/硬件身份层/缓存完整性/overlap | R1_GROUP §1、§5、§6 | 五项轮次间差异必须并列 |
| level-1 间隔四轮数值 | R1_GROUP §2 | ~9.85 / ~9.99 / 9.9237 / 6.6169 s |
| not_observed ≠ 未发生 | ARCH/R1-3_WORDING_ERRATUM.md | 采样粒度限制 |

## 附录 D（benchmark 维度）

九个维度对应 IDEA/43 binding vector 与 IDEA/42 A7.2"绑定对象/复核时刻/隐含假设"三列的并集；
fail-open/fail-closed 来自 ARCH/D1_SOURCE_ROOTCAUSE_AUDIT.md §4（OSV 失败模式）。
