# Speaker Notes — mentor_authorization_drift_progress_20260818

> PRIVATE — Research Discussion / Coordinated Disclosure Pending
> 讲稿对应 16 页（正文 12 + 附录 4）。每页 1–3 句要点 + 提醒。
> 所有数字均出自 goose-canary-archive 真实记录（见 SOURCES.md）。

---

## P1 标题

开场一句话：同一条 `package@latest` 配置，检查时指向 A，真正启动时却运行了 B。
这次汇报先讲 Goose 的证据，再讨论要不要扩展到其他框架。提醒听众：材料暂不外传。

## P2 一句话结果与当前状态

- 先用页面上的一句话讲清现象：同一条 `package@latest`，检查时指向 A，启动时实际跑成了 B；配置没有改。
- Auto 模式本来就没有批准界面，所以这里只说「全程没有批准界面」，不要说成「绕过批准」。
- 证据构成必须说准：**D1 首次按协议运行 + 两次按协议复现（R1-2/R1-3）+ 一次过程有偏差的补充观测（R1-1）**。不要顺口说成「重复了三次/四次」。
- 当前进度：R1/R2 完成，R3 未执行；VM 已 hibernate，恢复后须重新检查实验环境。

## P3 研究问题

- 用「正版 ≠ 被授权的那一版」定调。
- 身份阶梯：extension name → mutable selector → exact version → content digest → RuntimeArtifact。
  指出 Goose 当前只在前三层活动，digest 层缺失。
- 落到核心问题：授权对象与最终执行字节是否同一个对象。

## P4 Goose 内部机制

- 左列是 Goose 进程内七个已审计控制点；右列是进程外的 npx 解析与 RuntimeArtifact。
- 强调三件事：配置保存的是**启动配方**；ExtensionConfig **没有 digest 字段**
  （extension.rs:176，全文检索 0 命中）；npx 解析发生在 **Goose 所有控制点之后**。
- 漂移发生在"授权引用 ↔ RuntimeArtifact"之间——名字不变，字节已换。

## P5 受控实验设计

- registry 时间线：admission 时 latest→A，activation 前重指向 B；配置文本始终 package@latest。
- 执行确认靠多通道交叉：artifact 自报、effect 文件、registry 日志、进程祖先链。
- 安全信封四件套：本地 loopback registry、良性 A/B、隔离 effects 目录、无真实用户/凭据/公开恶意包。

## P6 D1 结果

- D1 是首次按预先写好的协议运行，原协议（idea/48）在这一轮后停止。
- 三个事实：admission 观察到 A、activation 执行 B、全程 0 次批准提示（Auto）。
- 判据阶梯：L1 顺序现象成立；L2 drift 成立；L3 需要 SystemCheckedOrBound(A)，system_bound_digest = absent，
  四轮一致——**不是 TOCTOU、不是任意代码执行**。

## P7 源码根因

- 中心句：多个安全环节共用同一个弱身份（名字）。
- 六条源码事实各带 file:line；如果被追问，D1_SOURCE_ROOTCAUSE_AUDIT.md 有完整调用链。
- 关键表述：**Goose 确实有安全检查**。OSV 会检查已知恶意包，但系统没有继续确认
  「被检查的代码」和「最后运行的代码」是不是同一份。不要说「Goose 没有安全检查」。

## P8 R1 可重复性

- 表格逐列讲：D1（盲）/ R1-1（A5.6 并发偏差，不计入）/ R1-2、R1-3（两次前瞻符合协议的重复）。
- 四轮全部：admission A → RuntimeArtifact canary-B，L2 成立。
- 汇报时说「D1 首次结果，R1-2 和 R1-3 两次复现」。**不要称 N=3**，也不要把四轮合并计数。

## P9 R2 阴性对照

- R1 组 @latest 四轮漂移（执行 B）；R2 组 @1.0.0 两轮未漂移（执行 A），
  且解析器**看到了**新 tag（packument latest=1.0.1）仍取回 1.0.0。
- 每轮五条独立证据确认执行 A：effect 文件 / 安装树 / registry tarball / 终端自报 / per-run 缓存。
- 允许的唯一总结："在该受控 registry 环境中，精确版本阻止了 dist-tag 漂移，支持 R1 根因定位。"
- 两个必须说的限制：① R1 与 R2 之间**缓存条件也不同**（controlled-warm vs cleared），因果分离需 R4；
  ② **版本号不是 digest**——同一版本号重发为不同字节的情形未测，这正是 R3 要回答的问题。

## P10 当前证据能说什么

- 左列四条"可以说"；右列六条"不能说"。被质疑时优先引用右列自约束（TOCTOU / 批准绕过 / ACE /
  跨系统普遍性 / exact-version=content binding / benchmark 已完成——全部禁止）。

## P11 R3–R6 与 benchmark 路线

- 页面带 PROPOSED — NOT YET EXECUTED 徽标，口头也要说。
- R3a/R3b：content-bound 臂 digest 匹配放行 / 不匹配在执行前拒绝；R4：mutable + 清空缓存补因果分离；
  R5/R6：Approve / Smart 批准界面显示与授权绑定。
- 恢复门槛：VM 已 hibernate，恢复后按 hibernation notice 逐项重建 readiness，研究者确认后才执行。
- benchmark 方向：统一 benign A/B workload → 多个开源框架 → 六个比较维度。
- 计数现状：正式运行 5 / 硬上限 15。

## P12 组会决定

四个问题逐个过：主贡献形态 / 推进顺序 / 首批框架 / 披露与投稿时间线。
收尾定位句："核心发现已经形成，科学闭环仍在构建；目前是 benchmark 的种子，不是已经完成的 benchmark 论文。"

## 附录 A（D1 终端回放）

被问"当时终端到底什么样"时翻到。强调：模型只发过名字、配置没改、执行的是 B、无批准界面。

## 附录 B（证据完整性）

六轮 manifest 全表。要点：D1 外层 30/0、内层 28/1（历史顺序缺陷，已确定性证明，不回溯修改）；
后五轮全部 0 FAILED。协议谱系：preregistered（idea/48，已终止）与 post-discovery（idea/50，effective 216a615e…）严格分开。

## 附录 C（四轮 R1 对照）

轮次间差异必须并列：器材（D1 器材/v3/v8/v9）、硬件身份层（unobserved/recorded_A/recorded_B/recorded_B）、
缓存证据完整性、辅助请求 overlap（unobservable/observed/observed/not_observed）。
提醒：not_observed ≠ 未发生；不得写"同一环境连续未变"。

## 附录 D（benchmark 测量维度）

九个设计维度，来自本 case study 编码手册；框架选型确定后逐项冻结。

---

## 全程口径红线（备查）

1. 不得称 TOCTOU；2. 不得称绕过批准 / ACE；3. R1 不得称 N=3；4. R2 不得称 content binding 或因果证明；
5. 不得作跨系统普遍性主张；6. D1（preregistered）与 idea/50 下运行严格分列；7. 未运行项一律标 PROPOSED。
