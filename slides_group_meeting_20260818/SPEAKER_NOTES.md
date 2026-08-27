# SPEAKER NOTES — 逐页讲解要点（约 12–15 分钟）

> 汇报对象：导师 + 研究组内部讨论。所有表述遵守 SOURCES_AND_CLAIMS.md 的边界。
> 提醒：本 deck 是 frontend-slides 原生 HTML 项目，**不是 PPTX**（文末有说明）。

## P1 标题页（30 s）
- 一句话定位：Agent 扩展安全探索中发现的**授权对象与执行对象漂移**问题，Goose v1.45.0 作为 case study。
- 强调材料性质：组会内部讨论，coordinated disclosure 未启动，请勿外传。
- 开场即声明结论上限 Level 2，管理听众预期。

## P2 一句话发现与当前阶段（1 min）
- 用陈述句完整念一遍核心发现：admission 绑定可变选择器 → activation 前重指向 → 执行 B，配置未变、无新授权。
- 给出两个术语：authorization-reference drift / deferred-resolution authorization，说明这是本文使用的严谨名称。
- 四个状态卡快速过：Level 2；正式运行 5/15；4 次漂移 + 2 次阴性对照；R3–R6 未执行。

## P3 研究动机（1 min）
- 提问式引入：启用扩展时批准的到底是什么？逐层念 L1–L4。
- 落点在 L4：制品内容只在进程外解析时才确定——这是全篇问题的根源。
- 预告回答：在 Goose 的这条路径上，名称不变时控制链不能察觉制品变化。

## P4 Goose 内部机制（1.5 min）
- 沿 7 步链讲：发现只暴露 name/description → 按名取配置 → 授权（Auto 无条件；批准键=工具名）→ OSV 包名检查 → **原样** spawn。
- 强调边界：`@latest` 的解析在虚线框（Goose 进程之外、activation 阶段）。
- 收尾句：名称是贯穿全程的唯一标识符，所以名称不变时所有环节都看不到身份变化。

## P5 威胁模型与 canary（1 min）
- 威胁模型：攻击者只需控制 dist-tag 指向，无需触碰本地。
- canary 设计要点：A/B 同名、tool surface 逐字节相同（排除工具面差异干扰）、O_EXCL 效应文件。
- 主动强调安全信封：良性、本地 loopback、从未发布真实 registry——回应伦理关切。

## P6 D1 与判据（1.5 min）
- 沿时间线讲 D1：admission 记 A → repoint（配置未动）→ spawn → effect_B 在进程启动瞬间出现 → 首工具晚 9.85 s。
- Level 1 成立但**必须注明**批准缺席（Auto 无批准环节，不得说"绕过"）。
- Level 2 成立：四条件合取。
- Level 3 不成立的原因要讲透：我们**没有证据**系统曾绑定 A 的 digest——unobservable ≠ 未发生，所以不能说 TOCTOU。这是审稿人最可能攻击的点，主动交代。

## P7 源码根因（1.5 min）
- 三个结构并排：ExtensionConfig 无 digest 字段（检索 0 命中）；观测到的 CanonicalGrant 只是 `npx …@latest`；ToolPermissionRecord 键为 tool_name。
- OSV 检查：先肯定它有效（信誉筛查），再说明它与 identity binding 正交；`latest` 被显式归约为 version:None。
- 结论条念一遍：不是"忘了校验"，而是**类型里没有可供校验的字段**——这句是论文的根因表述。

## P8 R1 重复性（1.5 min）
- 表格过一遍四轮：全部 A→B，Level 2 均成立。
- 重点讲证据类别纪律：D1 是 preregistered（不计入）；R1-1 带 A5.6 偏差（永久不计入）；R1-2/R1-3 是两次前瞻符合。
- 明确说：**只能说两次，不能说 N=3**——这是协议纪律，也是可信度来源。
- 披露 controlled-warm 证据完整性的轮次差异，展示我们不回避弱点。

## P9 R2 阴性对照（1.5 min）
- 左右对照：R1 臂执行 B；R2 臂（exact @1.0.0 + cleared）两轮执行 A。
- 讲亮点：解析器**看到了** latest=1.0.1 却仍取回 1.0.0（tarball_fetch 证据）。
- 讲五通道交叉确认，说明"执行 A"的判定是稳健的。
- 严格照念允许的唯一表述；然后念两条禁止：版本号≠digest；因果未隔离（双差异 → 需要 R4）。

## P10 能说 / 不能说（1 min）
- 左列快速过（都有冻结证据）。
- 右列逐条念禁用词——这一页是给导师的"自我审计"，也是论文写作的红线清单。

## P11 R3–R6（1.5 min）
- 矩阵过一遍各臂设计。
- 重点讲 R3 配对逻辑：R3a pass ∧ R3b reject 才能证明 content binding；只有 R3b 拒绝可能是 wrapper 坏了（fail-closed-by-breakage）。
- R4 的认识论边界：零流量≠未解析，保持 unobservable。
- 状态：VM 已 hibernate，R3a readiness 恢复后必须重建，不能直接复用。

## P12 benchmark 方向（1 min）
- 先念定位句；强调 **PROPOSED**：这是设计提案，没有任何已完成的 benchmark 数据。
- 维度表不逐条念，点出方法论迁移：复用的是构造方法与判读纪律，不是结论。
- 引出下一页的决策问题。

## P13 局限与伦理（1 min）
- 左列 limitations 逐条快速过（都是主动交代）。
- 右列伦理：良性 canary、停止规则优先、证据冻结纪律、未联系 vendor。

## P14 讨论问题（收尾）
- 逐条念 6 个问题，每个一句话解释为什么需要导师拍板。
- 特别提示 Q1（贡献定位）和 Q5（披露时间线）最影响后续排期。
- 结束语：在收到指示前，不运行新实验、不联系 vendor、不公开任何内容。

## 计时建议
P1–P5 约 5 min；P6–P9 约 6 min；P10–P14 约 4 min。若超时，优先压缩 P3、P12 的展开，保留 P6/P9 的判据与边界讲解。

## 关于"PPTX"的明确说明
frontend-slides 输出的是**原生 HTML 幻灯片**（浏览器全屏演示）+ **PDF 导出版**。它不支持真正的 .pptx 格式；本项目的 PDF 为逐页 1920×1080 静态快照（动画以最终状态呈现）。
