# SOURCES AND CLAIMS — slide claim → evidence 对应表

> 组会用 slides（2026-08-18）的每一项主张与其冻结证据来源。
> 所有证据以只读方式从 `~/goose-canary-archive/` 与 `hello-agents-lab/idea/` 核实。
> 哈希一律只显示前 8–12 位；完整值见对应文件。

## 证据文件缩写

| 缩写 | 文件 | sha256（前 12 位） |
|---|---|---|
| [D1] | `goose-canary-archive/D1_PRIVATE_MENTOR_REPORT.md` | 0d545410… |
| [SRC] | `D1_SOURCE_ROOTCAUSE_AUDIT.md` | c2075d53… |
| [SRC-ADD] | `D1_SOURCE_ROOTCAUSE_AUDIT_ADDENDUM.md` | —（原件 sha 0d545410 见其自述） |
| [R1组] | `R1_GROUP_AGGREGATE_RECORD.md` | d7aadba6… |
| [R1-1] | `R1-1_MANUAL_CODING_RECORD.md` | a10182e9… |
| [R2-1] | `R2-1_MANUAL_CODING_RECORD.md` | 9f62201d… |
| [R2-2] | `R2-2_MANUAL_CODING_RECORD.md` | 0e909dbf… |
| [R2组] | `R2_GROUP_AGGREGATE_RECORD.md` | —（见 canonical index） |
| [P48] | `idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md` | 见 idea/48 |
| [P50] | `idea/50_POST_DISCOVERY_CONFIRMATORY_PROTOCOL.md` | effective 216a615e3e35… |
| [R3a-H] | `PRE_RUN_READINESS_R3a_v1.HIBERNATION_NOTICE.md` | sidecar bb9433f5… |
| [IDX] | `ARCHIVE_CANONICAL_INDEX.md` + Addendum 1–11 | 8e24f27f… |

## 逐页 claim → evidence

### Slide 1 — 标题页
| claim | evidence |
|---|---|
| Goose v1.45.0；研究阶段（Level 2；5 次正式运行；协调披露待定） | [D1] §2.1；[R2组] §6 |

### Slide 2 — 一句话发现与当前阶段
| claim | evidence |
|---|---|
| admission 时授权绑定可变选择器 `npx -y goose-activation-canary@latest`；activation 前同一引用被重指向 B 并执行；配置逐字节未变；无针对制品的新授权 | [D1] §1、§4.3、§5.2；[R1组] §2 |
| 结论名称 authorization-reference drift / deferred-resolution authorization；上限 Level 2 | [D1] §0、§6 |
| 正式运行数 5 / 硬上限 15（R1-1/R1-2/R1-3/R2-1/R2-2） | [R2组] §6；[IDX] A11.2 |
| R3–R6 未执行；VM 已 hibernate | [P50] §6/A1.6；[R3a-H] |

### Slide 3 — 研究动机
| claim | evidence |
|---|---|
| 发现与选择只暴露 name + description；名字贯穿发现/查找/检查/授权 | [SRC] §6 |
| OSV 检查输入为名称（`latest` → version: None） | [SRC] §4 |
| 最终制品内容仅在进程外解析时确定 | [SRC] §2、§3 |

### Slide 4 — Goose 内部机制链
| claim | evidence |
|---|---|
| 7 步调用链（inspect → get_extension_by_name → add_extension → deny_if_malicious_cmd_args → Command::new 原样 spawn → npx 解析 @latest → 执行解析 artifact）；`@latest` 解析不在 Goose 链路任何一步 | [SRC] §2（含行号） |

### Slide 5 — 威胁模型与 canary
| claim | evidence |
|---|---|
| A=1.0.0 sha256 cfb882e2deec…；B=1.0.1 sha256 081c9afc7b71… | [D1] §2.3 |
| tool surface 逐字节相同（tools/list sha256 29c2a28b…） | [D1] §2.3 |
| 效应文件 O_EXCL；loopback:4873 自建 registry；从未发布到真实 registry；不联网、不读凭据 | [D1] §2.3、§3.2、§8 |

### Slide 6 — D1 与 Level 判据
| claim | evidence |
|---|---|
| D1 时间线（registry_start … effect_B_first_tool_execution，间隔约 9.85 s） | [D1] §4.1 |
| Level 1 成立（附条件 no_first_tool_approval_in_profile） | [D1] §6；[P48] §2.2 |
| Level 2 成立（四条件合取） | [D1] §6 |
| Level 3 不成立：SystemCheckedOrBound(A) 无证据；admission_resolution_status=unobservable；system_bound_digest=absent | [D1] §5.3、§6；[P48] §2.3 |

### Slide 7 — 源码根因
| claim | evidence |
|---|---|
| ExtensionConfig::Stdio 无 digest/hash/signature/publisher/version-lock 字段（extension.rs:176；四文件检索 0 命中） | [SRC] §3 |
| 观测到的 CanonicalGrant 仅为配置条目 cmd+args（@latest，无 digest、无版本钉死） | [D1] §5.2；[R1-1] §2.5 |
| ToolPermissionRecord 以 tool_name 为键；AlwaysAllow 覆盖未来所有 extension 启用 | [SRC] §5 |
| OSV pre-spawn 检查：对名称/版本信誉（MAL- 通告）有效；`latest` 显式归约 version:None；网络/HTTP/JSON 失败 fail-open；与 artifact identity binding 正交 | [SRC] §4；[SRC-ADD] A2 |
| 配置与权限记录合起来仍缺少能指称已解析制品的字段 | [SRC-ADD] A3 |
| npx 解析发生在 Goose 进程之外、activation 阶段 | [SRC] §2 |

### Slide 8 — R1 重复性
| claim | evidence |
|---|---|
| 三类证据：D1（preregistered，不计入）；R1-1（A5.6 并发偏差，永久不计入）；R1-2/R1-3（两次前瞻符合，上限） | [R1组] §0；[IDX] A11.2 |
| 四轮观测：admission A(1.0.0)；dist-tag 1.0.0→1.0.1；RuntimeArtifact=canary-B；L1 间隔 ~9.85 / ~9.99 / 9.9237 / 6.6169 s | [R1组] §2 |
| ✘ 不得声称 N=3；不得合并计数 | [R1组] §0 |
| controlled-warm 证据完整性：D1/R1-1 未捕获；R1-2/R1-3 完整捕获 | [R1组] §5；CONTROLLED_WARM_EVIDENCE_GAP_RECORD |
| 四轮共同：批准提示 0；local_cache_hit；session_scoped | [R1组] §2 |
| R1-1 偏差性质：产品自主 session-naming 并发请求（Running: 2） | [R1-1] §4；R1-1_PROTOCOL_DEVIATION_ADDENDUM(+ERRATUM) |

### Slide 9 — R2 阴性对照
| claim | evidence |
|---|---|
| R2-1/R2-2：args=["-y","goose-activation-canary@1.0.0"]；cleared cache；repoint 1.0.0→1.0.1 已执行 | [R2-1] §1；[R2-2] §1 |
| 两轮 RuntimeArtifact=A(1.0.0)；五通道交叉确认（效应文件/安装树/registry 日志 tarball_fetch 1.0.0 cfb882e2deec…/终端 canary-B 0 次/_cacache 仅 A） | [R2-1] §2；[R2-2] §2 |
| 解析器看到 latest=1.0.1 仍取回 1.0.0 | [R2组] §2 |
| 唯一允许表述：在该受控 registry 环境中，精确版本阻止了 dist-tag 漂移（重复两次） | [R2组] §0 |
| ✘ 内容绑定/一般完整性/因果证明；R1↔R2 存在双差异（selector 形式 + 缓存条件），需 R4 分离 | [R2组] §0、§4 |

### Slide 10 — 能说 / 不能说
| claim | evidence |
|---|---|
| 禁用词表：TOCTOU、arbitrary code execution、绕过 artifact-specific 批准、跨框架普遍性、已确认高危漏洞、N=3、内容完整性、因果证明 | [D1] §0；[R1组] §0；[R2组] §0；[SRC] §9 |
| 证据完整性：D1 外层 30 OK/0 FAILED、内层 28 OK/1 FAILED（已证顺序缺陷）；R1-1 frozen 52 OK；R1-2/R1-3 frozen 63 OK；R2-1/R2-2 frozen 52 OK（均 0 FAILED） | [D1] §7；[R1组] §3；[R2组] §3 |

### Slide 11 — R3–R6 计划
| claim | evidence |
|---|---|
| 运行清单：R3a/R3b（content-bound，各 1）、R4×2（mutable+cleared）、R5×2（Approve，Allow Once/Always Allow 各一）、R6×2（Smart） | [P50] §6 + A1.3/A1.4/A1.6 |
| R3 判读：仅 R3a pass ∧ R3b reject ⇒ content binding 有效；仅 R3b 拒绝不能排除 fail-closed-by-breakage；adapter 为外部 custom adapter，非 Goose 原生 | [P50] A1.3 |
| R4 认识论边界：零 registry 流量 ≠ 未解析；保持 unobservable，仅记 no_pre_activation_registry_request_observed | [P50] §6.1；[R2组] §4 |
| R3a 未执行；VM hibernate；readiness v1 标记 superseded-on-resume / not directly reusable | [R3a-H] |

### Slide 12 — 多框架 benchmark（proposed）
| claim | evidence |
|---|---|
| 方向：统一受控 attack/workload，测量多框架对 artifact identity drift 的抵抗能力 | 导师建议（组会讨论项，非实验结果） |
| 11 个维度（mutable selector、解析阶段、admission 解析、DisplayedGrant、CanonicalGrant、重授权、验证机制、模式差异、RuntimeArtifact 可观测、防御有效性、fail-open/closed） | 讨论提案（基于 [SRC] 的 Goose 观测维度泛化） |
| 状态：PROPOSED — 未开始，无任何已完成的 benchmark 数据 | 本 slides 明确标注 |

### Slide 13 — 局限与伦理
| claim | evidence |
|---|---|
| 单产品单版本；源码↔二进制仅版本号对应未做构建复现验证；仅 stdio 路径；LLM 步骤确定性未证明 | [SRC] §11；[SRC-ADD] A6 |
| 模型后端两处偏差（chat template 单条件修改；seed 无法设置） | [D1] §2.2 |
| 安全信封与停止规则；证据冻结+双哈希+只读归档；未联系 vendor | [D1] §3.3、§7、§8；[P50] §8 |

### Slide 14 — 讨论问题
6 个问题来自本汇报要求（研究决策，供组会讨论；无实验主张）。

## 与本 deck 相关的禁用表述清单（自查已通过）

- ✘ TOCTOU / arbitrary code execution / 可利用漏洞 / 高危定级
- ✘ "绕过了（artifact-specific）用户批准"（Auto 模式无批准环节）
- ✘ 跨系统/跨框架普遍性
- ✘ N = 3 protocol-conforming repetitions
- ✘ exact-version = 内容绑定 / 内容完整性保证
- ✘ R1→R2 因果证明
- ✘ "Goose 没有安全检查"（明确错误）
- ✘ "系统绝对没有解析过 digest"
- ✘ 把 proposed benchmark 写成已完成结果
