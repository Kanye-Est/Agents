# 53 — Story Framework + Experiment Slate（方向一 · 供 韩老师 讨论）

> **DRAFT — for discussion, not a result.** 本文件是 罗老师 指定的第一步产出：
> **先想写作框架（story），框架下列出需要哪些实验（1/2/3），再与 韩老师 讨论。**
>
> 日期：2026-09-05 · PRIVATE / PRE-DISCLOSURE
> 依赖：idea/51（三篇拆解 → **降级为「实验方法库」**）、idea/52（红队预注册协议 · **EFFECTIVE 2026-09-12**）、
>   frozen archive `harness-benchmark-archive/synthesis_20260828/*`。
> 更新（2026-09-06）：已折入 **韩老师 2026-09-05 回复**——根因重述 + E1/E2 × P-ctx/P-direct 2×2 + 5 篇防御全景两轴表（§2.5，逐篇核实含 SkillTrustBench）+ Claude Code/Codex 适用性屏读（§2.5 末，DOCS-ONLY 非 run）。
> 更新（2026-09-08）：已折入 **韩老师 2026-09-08 定调**——**E2×P-direct 定为主攻**（攻击由植入代码直执、全程不进 LLM context/thinking、仅用工具既得权限）；新增**第三防御族 (C) 运行时决策/轨迹 IPI 验证**（ARGUS 2605.03378 / AgentDoG 2601.18491 / VIGIL 2601.05755，核实：只 gate 决策/轨迹/内容层、不观测工具代码内部行为）+ **2×2 可防御性梯度表**（§2.5）；自适应攻击者（code-agent 生成规避植入）列为授权待批的防御效能测量。引文 Q26–Q29。
> 更新（2026-09-09）：折入**韩老师会议定调**——砍 E2×P-ctx、只做 **E2×P-direct**；产出 **idea/52 Amendment 1**（UTCS 命名 + 真实功能工具 v1 + 危害菜单 G1–G4[G1/G2/G3=MVP·G4 deferred] + code-agent 生成规格+验证器 V + 五判据 + `trajectory_absent` 缺席证明程序 + 第二步静态扫描器 + EFFECTIVE RECORD 引 Amendment sha256）；**三层防御图修正**（静态扫描/(C)轨迹审计/OS-syscall 引爆 三层分开，更正 SkillDetonate="代码扫描器"误标 + 混淆规避的过度主张）。引文增 Q30–Q35（RedCode/RedCodeAgent/JAWS-Bench/Cloak&Detonate 更正/S&P'26 2509.06572/fang 五混淆法，均 raw-verified）。
> 更新（2026-09-12）：**idea/52 授权已激活**（§14 EFFECTIVE RECORD：H1 纪要 `c5b2ab59…` + H2 快照 `88e8fae5…` + H3 会上口头确认，生效日 2026-09-12）。**CC 范围裁定 = 选项 A**：CC/Codex/OpenCode/Gemini/G4 均 deferred；CC 扩权前置 = Python/Shell 载荷+混淆调研 + 披露评估（A1.5 混淆链仅覆盖 JS，CC 主力 Python 58%/Shell 25%，据齐同学 2026-09-11 调研）。base 授权范围 = Goose×{G1,G2,G3}；当前 run=0（建台中）。
> 纪律红线：drift 结论恒停 **level-2**；impact 是新轴、不回填；forbidden vocab 见 §4；
>   **授权已生效**（idea/52 §14 EFFECTIVE RECORD，2026-09-12；base = Goose×{G1,G2,G3}，run 数自 0 起随实跑递增）；**本文件仍是 story 框架、不触发 run**；CC/Codex/OpenCode/Gemini/G4 仍 deferred。

---

## 0. 三条元原则（先写在最前，免得又跑偏）

**(A) 体裁：这是一篇「漏洞发现」论文，不是 benchmark / measurement 论文。**
罗老师 point 3 的实质——AgentDojo / MCPTox / InjecAgent 这类「prove-something-wrong」论文，*贡献是评测本身*，攻击是随手取用的商品，要的是**面广**；而我们的贡献是**一个具体漏洞**（"版本更新中的代码替换面"），一切叙事必须**围绕这一个 finding 组织成 story**。论文结构因此从 MCPTox 三段式换成漏洞论文的经典弧线：**motivation → finding → scheme → experiments。**

**(B) 叙事策略：罗老师举的 Codex / 防御无效 / open-market 是「什么叫 impressive/interesting」的*示例*，不是任务清单。**
中顶会的打法是**把 story 用一个 interesting / impressive 的方式引入**。判定标准只有两条：

> **① 逻辑正确；② 引入的每一个例子都可被认证为真实（authenticatable-as-real）。**

因此我们**允许扩散思维**——不必只用「我们某次实验的亲历时刻」当开头。可以用**外部的、著名的、可考证的真实事件**做 impressive 的引子（如 xz / event-stream），只要它们被当作 **motivation/类比**引用、而**不冒充成我们的结果**。三档真实性分级贯穿全文（§2 表）：
- **real-ours**：我们的冻结证据（有文件 + sha256）；
- **real-external-cited**：外部真实事件（有 CVE / 公开记录），仅作 motivation 引用；
- **gated-not-yet-real**：尚无 run 支撑（如 Codex / Claude Code）→ 只做「预留槽」，**永不断言**。

**(C) 分量重心：单是「发现漏洞」不够——重量在「证明危害」＋「证明利用路径逃过现有防御」。（韩老师 2026-09-08）**
韩老师定调：大模型时代「发现一个漏洞」本身不是难点、分量不足；难点、也是论文重量所在——**揭示这漏洞到底能造成什么危害**。**E2×P-direct 不是新机制，而是「利用此漏洞的一种攻击方式」**，其价值在于它是把漂移变成*真实危害*、且*逃过现有 agent skill 代码扫描*的那条路径。
- **重心排序**：finding（§1③ 漂移本身）＝ 必要铺垫、非 headline；**承重 ＝ §1⑤/E-②（防御逃逸的*结构性*证明）＋ §1⑥/E-③（危害/影响 ＋ 野外可操作性）**。呼应模板：MCPTox 的分量不在「投毒存在」而在 ASR ＋ 对齐失效；AgentDojo 不在「IPI 存在」而在「最强 agent 也被攻穿、防御只压到 8%」。
- **这同时回答 罗老师「新攻击方案 vs 测试框架」**：该二分略假——既不是为新而新地发明攻击（体裁仍是漏洞发现，见 (A)），也不止于 benchmark 罗列防御；而是**用一条逃过现有防御的真实利用路径，把漏洞的危害坐实**。E2×P-direct ＝ 选定的利用路径（量具）；code-agent 自适应生成 ＝ E-② 的「自适应攻击者」臂（**授权待批**）。
- **精确射程（守 level-2、勿对韩过度承诺）**：「逃过现有代码扫描」限指 —— (i) 静态/首装一次性扫描器（靠 E2 更新缺口：装时干净、毒在更新、不复扫）＋ (ii) 运行时决策验证族 ARGUS / AgentDoG / VIGIL（P-direct 不进决策层，无文本、无异常动作可验，§2.5）；**唯 per-invocation OS 级行为引爆理论可及，而无框架逐次部署**。**不写「绕过一切代码扫描」，不碰 §4 forbidden vocab。**

---

## 1. 故事框架（the spine，按论证驱动、非按时间顺序）

> 读法：这是**论证的顺序**，不是我们做实验的顺序。亲历的坎坷被拆成「证据」，安放在论证需要它的地方。

**① Hook / Motivation（impressive · real-external-cited）——「代码从不自我声明」**
过去十年最著名的供应链灾难有一个被防御方忽略的共同点：**投毒载体是*代码*，随一次*获信后的更新*送达，而代码从不像文本那样自我声明。**
- **xz-utils（CVE-2024-3094，2024）**：后门在**发布 tarball**里，不在仓库显眼源码里——*poison lives in the release artifact, not the repo*。（→ 直接给 方向二 tarball-diff 立命题。）
- **event-stream（2018）**：维护权移交后，恶意依赖随一次**版本更新**混入——*post-approval update*。（→ 我们核心面的现实先例。）
- **ua-parser-js（2021）**：npm 账号被劫，恶意版本被发布——*version-update poisoning at scale*。

> **诚实边界（必须出现在正文）**：机制 = 经典恶意包更新供应链，我们**不假装发明新机制**；这三例是**动机/血统**，**不是**我们的实验结果。新颖性见 finding。

> **hook 体例出处（post-2023 漏洞发现型论文，narrative-scan 2026-09-05 核实）**：本 hook 的「先给受信组件正名、再一句话翻面」写法 = **PoisonedRAG**（USENIX'25, 2402.07867：把 RAG 知识库这一受信组件翻成攻击面）＋ **XZ「Wolves in the Repository」**（2504.17473：**信任逐步累积、然后被兑现**的 5 阶段生命周期，正是「获信后更新」的具体化）的合流。见 §1.6 四个叙事动作。

**② 转折 / Thesis（interesting）——「agent 防御在看错的门」**
与此同时，agent 安全社区把力气几乎都压在**读工具「说了什么」**：prompt-injection 检测、context 消毒、描述 diff、工具定义完整性。这条线**默认威胁是模型会读到的文本**。
但一个 agent 工具是**带 bash / 文件读写授权的代码**；工具一更新，新代码在**工具进程内执行、从不进入模型 context**。于是——**这整条描述侧防御线，结构性地在看错的通道。** 这就是 韩老师 点破的 gap：*agent 只看得到描述，从不验证「描述 ≡ 实现」，因为那需要它去跑工具的代码测试。*

**③ Finding 结晶（impressive · real-ours）——「装的时候检一遍，更新时再不回头看」**
把 thesis 落成一句反直觉、可考证的话：**你信任的那次检查发生在安装时——工具更新后，没有人再看一眼。** 具体到我们的证据：**pinning a version does not pin the code your agent runs.**
- 我们本把精确版本号 `@1.0.0` 当作**无聊的阴性对照**（证明 pinning 能挡漂移）——它**确实挡住了** dist-tag 重指（R2 held）。
- 但**同版本重发**（SV：`@1.0.0` 字节 A→B）下，同一个 pin **执行了不同的字节，3/3**，在**未变的 `@1.0.0` 授权**下。
- 冻结原话：*"a version binding is not a content binding; the string '1.0.0' was rebound to B's bytes and Goose executed B."*（`SV_RESULT_v1`）
> **翻面点（narrative-scan 动作1）**：读者信任「钉住的版本号 / 已审查过的工具」；一句话翻面——**钉住的是标签、审查的是首装那一版；更新缺口（E2, §2.5）让新字节在旧授权下执行，而所有首装式扫描器不会复扫。**
> **措辞纪律**：只说「版本号绑定 ≠ 内容绑定」；**永不**写「content binding」、**永不**写 approval bypass / TOCTOU；停 level-2；不外推公共 npm。

**④ 不是偶然 / Systemic（impressive · real-ours）——「同一现象，两台机器，两个原因」**
跨三个异构系统，这个面**出现与否都有可解释的机制**，不是运气：
- **OpenCode** re-auth = `not_applicable`：cache 以 mutable 文本为 key，更新**从未被重新解析**（missing link）。
- **Gemini CLI** re-auth = `drift_observed`：每次调用是**全新进程、重新解析**，更新随之漂入、无新授权。
- 差别**只在**「是否对同一引用发生第二次解析」。→ 这条把论文从「我们测到一个率」抬到「**我们解释了这个面何时存在、为何存在**」。

**⑤ 严谨主线 / 防御无效（interesting · real-ours → E5）——「会因自身损坏而'成功'的防御」**
我们在设计 digest wrapper 对照时发现一个陷阱：**一个永远失败的 wrapper 会伪装成有效防御**（它总在"拒绝"）。于是把 R3 重构成配对的 **R3a 放行 / R3b 拒绝** 正对照，只有 `R3a pass ∧ R3b reject` 才算真防御。→ 这正是 **E5「防御结构性无效」实验里强制阳性对照**的种子：我们证明描述侧防御拦不住代码载荷时，先证明**它确实拦得住描述侧变体**（阳性对照过），否则记 `positive_control_failed`、不主张。**「无效」是受控结果，不是"没调好"。**
> **claim 形状要往「结构性 / structural」推，不止「经验性 / empirical」**（narrative-scan：PoisonedRAG 的体例）。PoisonedRAG 把攻击拆成**两条件**（retrieval condition ∧ generation condition），并**逐字论证**朴素构造的结构性张力：*"if we craft the malicious text P such that it is extremely semantically similar to the target question Q… then we could achieve the retrieval condition but **may not achieve the generation condition**"*（§Deriving two conditions，核对 2026-09-06）——即用**机制/条件框架**说明何时做不到，而非仅经验统计。我们对应的强主张：**扫描文本的防御 *无文本可扫*、diff 描述的防御 *无描述变化可报*——不是它们没拦住，是它们的作用面与代码载荷不相交**。措辞守 idea/52 §10.3 的条件式：「对*代码承载、进程内执行、从不进 context* 的载荷，描述/输出侧防御线结构性无效」，**不写「所有 agent 防御都无效」**。

**⑥ 影响 / 2×2 利用×载荷（real-ours + 安全替身 · 详见 §2.5）**
影响沿韩老师的两根正交轴铺开，不再用旧的 P0/P1/P2 单调阶梯：
- **利用路径**：**E1 首装即毒**（会被首装扫描器抓）↔ **E2 更新投毒**（承重轴——绕开所有一次性首装扫描器）。
- **载荷形式**：**P-direct 代码直执**（打包 workspace → POST，全程不碰 LLM，= 旧 P1）↔ **P-ctx 指令包装为代码**（base64 藏指令、运行时解码注入 context，绕描述 diff，= 旧 P2 强化版）。
- 核心格是 **E2 × {P-direct, P-ctx}**：更新缺口送达 + 两种载荷都在旧授权下执行。P0 良性金丝雀（`SV_RESULT_v1`）保留作**机制对照**（证明字节确实被换）。
- 所有载荷 = **安全替身**（读 `sk-FAKE-…` → 写标记 → POST 127.0.0.1），代表危害而不产生危害。

**⑦ 可选 capstone（gated-not-yet-real）——「打在大家都在用的产品上」**
*若*获得授权且完成 run，在一个**知名生产级 agent**（Codex / Claude Code 之类）上演示 → 把「very impressive」从**预留槽**变成**结果**。**适用性屏读已完成**（§2.5 末）：两款都只 gate 能力、不做代码验证、更新时不复扫；Codex 更有 CVE-2025-61260 + Mindgard 公开背书。**但屏读 ≠ run**——在 run 存在之前，本节只写「applicability screened, measurement pending authorization」，绝不断言。故事被设计成**能接纳**这一槽，而**不依赖**它。

---

## 1.6 四个叙事动作（漏洞发现型论文 ≠ benchmark 论文 · 起草自检表）

> 来源：narrative-scan（2026-09-05）核实的 6 篇 post-2023 单漏洞论文——PoisonedRAG（USENIX'25, 2402.07867）、Demystifying RCE / LLM4Shell（CCS'24, 2309.02926）、Not What You've Signed Up For / IPI 首篇（AISec@CCS'23, 2302.12173）、Imprompter（2410.14923）、Wolves in the Repository / XZ（2504.17473）、We Have a Package for You! / slopsquatting（USENIX'25, 2406.10279）。这四个动作是它们共有、而 benchmark 论文没有的。起草 idea/53 正文时逐条对照：

1. **翻面开场，不是覆盖缺口开场。** benchmark 论文开「这个空间没被充分测量，所以我们全面测」；漏洞论文**先给一个读者信任的组件正名，再一句话翻面**（PoisonedRAG 翻 RAG 知识库；LLM4Shell 翻框架的 code-exec；IPI 翻检索到的网页内容）。→ **我们翻的是「获批准的工具 / 钉住的版本号」**：你信任它，但它钉住的是标签、不是代码（§1③）。
2. **给漏洞命名 + 配一根机制脊柱。** 不只起名（PoisonedRAG / IPI / LLM4Shell / package hallucination），还附一个紧凑的因果模型——PoisonedRAG 的**两条件**（retrieval condition ∧ generation condition）、IPI 的**指令/数据同通道无边界**、LLM4Shell 的 **prompt→生成代码→`exec`**。机制脊柱是「这是**一件事**」而非「打分 N 项」的根据。→ **我们的脊柱**：*admit mutable ref → 授权钉在标签/名字 → 更新后重解析执行 B → 旧授权下、无重授权、载荷是代码故不进 context*。这根脊柱要在正文早早立起来。
3. **实验是「对抗性证明」，按 探测→利用→排除 编排，不是 leaderboard 扫描。** 每个实验去**堵一个怀疑者用来否定 finding 的逃逸口**：PoisonedRAG 用 baseline **各自卡在某一条件失败**证明两条件框架对；LLM4Shell 用 **hallucination test**（哈希/base85/算术）排除「LLM 只是假装执行了代码」；Imprompter 用 **transfer** 排除「只对单一目标过拟合」；三者都以「现有防御 insufficient / 被绕过」收口。→ **我们每个实验的「排除什么」列**（已在 idea/51 §E 备好）就是这个动作；E-② 尤其要像 PoisonedRAG 那样把无效性推到**结构性**（§1⑤）。
4. **有纪律的新颖性边界：把 delta 单独拎出来。** 每篇都显式分开「机制/效果是旧的」与「我们的新实例是什么」（全部逐字核对 2026-09-06）——Imprompter 把新颖性放在**自动计算的一类混淆对抗样本**（逐字 *"a new class of automatically computed obfuscated adversarial prompt attacks"*；并明说手工 IPI *"a casual inspection of the prompt will reveal its true nature"*、而其混淆样本 *"do not reveal their purpose upon inspection"*）；PoisonedRAG 逐字自陈 *"the first knowledge corruption attack to RAG"*（把知识库标定为新攻击面）；LLM4Shell 逐字把 delta 放在载荷通道——*"unlike traditional app vulnerability exploitation, the payload for such attacks consists solely of natural language expressions"*（贡献 = *"a novel combination of attacking strategies including hallucination test and LLM escaping"*）；slopsquatting 逐字 *"a novel form of package confusion attack"*，并自陈是 *"a variation of the classical package confusion attack that has been enabled by code-generating LLMs"*；XZ 逐字把空白定位在系统视角——*"The OSS community has thoroughly investigated the attack's technical aspects, but a centralized, systematic analysis is still needed"*，其贡献 *"lies in providing a comprehensive perspective of the attack timeline"*。→ **我们的 delta**：不是发明供应链攻击，而是 **agent 场景实例化 + 跨系统实测 + 对描述侧防御结构性免疫**（§0 诚实边界，必须出现在正文）。

> **给我们最紧的合成模板（narrative-scan 结论）**：**PoisonedRAG 的机制脊柱 + XZ 的信任-生命周期 hook + LLM4Shell 的防御无效证明**。即：翻面开场（获批后更新/漂移）→ 命名漏洞并给 2-要素机制 → 跑一个**专门排除「文本扫描防御能拦住代码载荷」的实验**（结构性、非经验性无效）。全程保留 Imprompter 式诚实句：明说我们是 substitution-after-trust 的**新实例**，不是新机制。

---

## 2. Beat 清单与证据出处（真实性分级 + 守则）

| Beat | 在 story 里的角色 | 真实性 | 证据 / 出处 | 守则 |
|---|---|---|---|---|
| xz / event-stream / ua-parser-js | ① Hook 动机 | real-external-cited | CVE-2024-3094 等公开记录 | 仅作 motivation；不冒充我们的结果；带诚实边界 |
| 描述侧防御在看错通道 | ② Thesis | 论证（韩老师 gap） | idea/52 §10.3；attack-surface-pivot | 写成条件式，不写「所有防御都无效」 |
| 版本号绑定 ≠ 内容绑定 | ③ Finding | real-ours | `SV_RESULT_v1`（rig `e3fb768d…`，A `cfb882e2…` / B `cb6fa778…`），`CROSS_OBJECT_AB_RESULTS_v2 §2` | level-2；version-string binding；无 npm 外推；R3a=answered_on_anchor |
| 跨对象机制分歧 | ④ Systemic | real-ours | `CROSS_OBJECT_AB_RESULTS_v2 §3–5` | 各自计数、不合并；不排名 |
| 防御全景两轴（5 篇核实） | ② Thesis 支撑 | real-external-cited | §2.5 表；ACE/USENIX'26/MalSkills/SkillTrustBench/SkillDetonate | 分轴主张；不硬套一条；不主张击败 runtime-per-invocation |
| fail-closed-by-breakage → 配对正对照 | ⑤ 严谨主线 | real-ours | idea/50 A1.3（R3a/R3b） | 阳性对照失败即不主张 |
| 2×2 利用×载荷（E1/E2 × P-ctx/P-direct）| ⑥ 影响 | real-ours（P0）+ 预注册（E2×P） | §2.5；idea/52 §5–6 | 安全替身；127.0.0.1；授权 EFFECTIVE 2026-09-12 |
| 知名产品演示 | ⑦ capstone | **gated-not-yet-real** | 屏读结论：Codex=公开文档已证「no re-check on change」(CVE-2025-61260/Mindgard)；Claude Code=文档证首装仅信任门、auto-update 无复扫 | **run 前不断言**；只写 screened/pending |

---

## 2.5 根因与 2×2 利用/载荷 taxonomy（韩老师 2026-09-05 定稿的框架）

> **根因重述（比"代码≠描述"更利落）**：漏洞不是"攻击者往描述/skill-prompt/外部资源里插显式指令"（那是 IPI，红海）；而是——**agent 允许用户安装第三方工具，却从不验证工具*内容*的安全性，尤其缺少检查工具*代码*、拦截其中可能恶意功能的能力。** 命名的是**缺失的能力（代码验证）**，不是载体。这是我们与整个 IPI/描述侧文献的分野。

**两根正交的轴（韩老师）：**

**轴 A — 利用路径（恶意代码何时到达）：**
- **E1 首装即毒**：用户第一次装的工具就含恶意代码。
- **E2 更新投毒**：首装干净、通过审查；**后续版本更新**里插入恶意代码。← **承重轴**（见下表：代码扫描器只在首装/registry 扫一次、不复扫更新，唯有 E2 能绕过它们；E1 反而会被 MalSkills / USENIX'26 抓住）。
- 共同点：两条路 agent 都**缺少工具代码检查能力**。

**轴 B — 载荷形式（恶意功能如何在 agent 内执行）：**
- **P-ctx 指令包装为代码**：恶意指令被**包装/加密（如 base64）在代码里**，运行时解码后**注入 LLM context window**。→ 绕过描述 diff / 首装描述扫描（描述没变、指令是密文），但解码文本**最终进 context**。（= 我旧版 P2 的强化版。）
- **P-direct 代码直执**：代码**直接执行**恶意功能（打包 workspace → POST 到指定地址）。**与传统恶意软件无异，全程不碰 LLM。**（= 我旧版 P1 = idea/52 §5.2。）

> 这 2×2 **取代** idea/52 的 P1/P2 命名（P0 良性金丝雀保留作机制对照）。映射：旧 P1→**P-direct**，旧 P2→**P-ctx**（且 P-ctx 现明确含 base64-解码-注入这一更强变体）。

### 防御全景表（5 篇，已逐篇核实 · E-② 的骨架）

> 关键发现：这 5 个防御**分布在两根不同的轴上，"代码≠描述"单独一条并不能全beat**——必须**两轴合起来**（描述侧用代码承载绕过；代码/行为扫描器用更新缺口绕过）。诚实分轴主张，比硬套一条更 impressive。

| 防御（核实日期 2026-09-05） | 实际检查什么 | 被【代码≠描述】绕过？ | 被【首装≠更新 E2】绕过？ |
|---|---|---|---|
| **ACE**（NDSS'26）plan-integrity + capability barrier | 仅用**可信信息**建抽象 plan；静态分析在 **plan** 上、非代码/二进制；运行时能力隔离 | **是**（plan/描述完整性层——我们不靠文本塑造 plan） | N/A（非扫描器）；**注**：其 runtime capability 隔离是另一根「围堵」轴，**我们不主张整体击败** |
| **SkillTrustBench**（Tencent Zhuque + CUHK-SZ，2026-06）**评测*install-time 扫描器*的基准**（非扫描器本身）：5,520 例 / 9 威胁类 T01–T09 / 5 依赖层 A–E，取自 62,652 真实 skill；参考扫描器 SkillSpector = 静态规则 + 可选 LLM 语义 + OSV 查询，读**全 skill 内容**（SKILL.md + scripts + config） | **读代码 + 配置**；范式是**"before installation or use"**（HF 卡原文）的一次性 pre-install 判定 | **否**（它读代码，"代码≠描述"在此失效——与 MalSkills 同族） | **是**（"before installation/use" = 首装门；不复扫更新） |
| **"Do Not Mention This…"**（USENIX'26, 2602.06547）静态模式 + **动态行为验证**，**覆盖代码 AND 描述** | 代码 + 描述都扫；一次性 registry sweep | **否**（它也读代码，"不动描述"骗不过） | **是**（registry 一次性扫、不复扫更新） |
| **MalSkills**（ASE'26, 2603.27204）neuro-symbolic 于**代码+prompt+config** | 分析**代码**制品；一次性 corpus scan | **否**（它读代码，"代码≠描述"在此失效） | **是**（一次性 registry 扫，更新缺口是唯一有效论点） |
| **Cloak & Detonate / SkillDetonate**（arXiv 2607.02357）**沙盒引爆行为审计** | 运行时行为、OS 边界 taint；97% 检出 | **否**（看效应不看外观；我们的 P-direct 正是它 taint 的流） | **是（已核实原文 2026-09-06）**——作者把 SkillDetonate 定位为 *"an offline, once-per-skill install gate"*（成本 153s / 14.1K tokens 每 skill vs Cisco 21s）；其提议的静态硬化「安装时记内容哈希、每次运行前复验」被作者自陈 *"at the cost of breaking self-updating skills"*（VI-C）。即：**引爆是一次性首装门**、复验哈希会**破坏自更新 skill** → 更新缺口 E2 未被闭合。**注**：论文明说 *"dynamic execution auditing is the load-bearing defense"*——他们力挺动态审计，但仍是**首装一次**，非逐次调用 |

> **两轴结论**：我们用**两条不同的轴击败两个不同的防御族**——(A) **描述侧 / plan 侧防御**（ACE-plan / USENIX 的描述半边）靠**代码承载**（代码≠描述）；(B) **首装式内容/代码/行为扫描器**（读代码的 MalSkills、SkillTrustBench-评测的 SkillSpector、USENIX 静态半边，及行为引爆 SkillDetonate）——它们**读得到代码**，"代码≠描述"对它们**失效**，唯一有效论点是**更新缺口 E2**（一次性首装扫、不复扫更新）。
> **诚实分轴**：不硬把 5 个防御塞进"代码≠描述"一条——那对 (B) 族是站不住的（它们确实读代码）。分轴主张（描述侧→代码承载；扫描器→更新缺口）既准确又更 impressive。
> **诚实边界（Imprompter 式，写进正文）**：若存在**逐次调用（per-invocation）的运行时行为引爎**，我们的 P-direct **会被检出**——我们**不声称**击败它。但据 SkillDetonate 原文（2607.02357, VI-C，已核实）：（i）他们把该防御定位为 *"an offline, once-per-skill install gate"*（成本 153s/14.1K-tokens/skill），即**首装一次**、非逐次调用；（ii）他们提议的复验硬化（安装时记哈希、每次运行前复验）被自陈会 *"break self-updating skills"*，故更新缺口未闭合。**注意准确性**：论文本身主张 *"dynamic execution auditing is the load-bearing defense"*（力挺动态审计），我们**不得**把它描述成"作者承认防御无效"——我们只主张：**在其被部署的首装门形态下**，E2 更新缺口未被覆盖。故结论是「**对已部署防御 + 首装门形态的动态审计无效**」，**逐次调用引爆列为正交、未来防御方向**（与 idea/52 §7.4 对 OSV 的处理同构）。
> **引用红线（2026-09-06 教训）**：正文所有带引号的句子必须逐字回到原文核对；机制性断言若无原文支撑，写成我们的分析、**不加引号冒充作者原话**。曾误造 "there is no second pass" 一句（原文无此语），已删除。

### 2×2 可防御性梯度（韩老师 2026-09-08 定：E2×P-direct 为主攻）

> 2026 年又出现**第三防御族**——**运行时决策/轨迹 IPI 验证**，不同于上表的「描述侧 (A)」与「首装扫描器 (B)」。核实三篇后确认一条对我们至关重要的性质：**它们全部只在 agent 的「决策 / 轨迹 / 所感知内容」层拦截，无一观测工具代码的内部执行行为**——这正是 P-direct 从缝里漏过之处。

**第三族 (C)：运行时 IPI / 决策验证（2026）**
- **ARGUS**（2605.03378，*Context-Aware Prompt Injection*，**tavily 原文核实**）：*"a runtime decision auditor that makes the evidence behind each state-changing action explicit before execution"*——*"ARGUS mediates every tool call proposed by the agent"*，只对状态改变动作触发审计（*"State-changing calls trigger an audit"*），并把每个 tool-call **参数**溯回其 context span（Influence-Provenance Graph；*"it traces each tool-call argument back to the span from which the value was copied, normalized, derived, or resolved"*）。即它校验的是 **agent 提出的动作 + 其参数在 context 中的出处**，非工具进程内部行为。对「合法调用的良性工具、其代码用既得权限自行外传」——无异常参数、无新的状态改变动作 → **检不出**。（机制为逐字引语；「作者把被攻陷工具代码列为 scope 外」一句我方未取到该逐字句，作无引号归纳。）
- **AgentDoG**（2601.18491，*Diagnostic Guardrail*，**tavily 原文核实**）：*"provides fine-grained and contextual monitoring across agent trajectories"*，且 §8.2 自陈 *"the input of AgentDoG is confined to text-based trajectories"*；三维 taxonomy 按 *"source (where), failure mode (how), and consequence (what)"* 分类，确列 *"malicious tool execution"* 一类——但既然输入仅限文本轨迹，**轨迹里不显形的 covert side channel（P-direct 的效应）便无从推断** → **检不出**。（「评测用模拟工具输出、无 side-effect 遥测」为我方对其设定的归纳，非逐字。）
- **VIGIL**（2601.05755，*Verify-Before-Commit*，摘要+框架 raw-verified）：verify-before-commit——*"a runtime verifier strictly validates these tentative trajectories before commitment"*、*"rectifies deviations induced by malicious tool feedback"*，以锚定 **user intent** 的约束校验 agent 的**候选轨迹/动作**，针对恶意工具**反馈（内容）**。术语为 *"tool stream injection"*。（§4.5 verifier 内部未逐行读，但框架层已明确是轨迹/内容验证、非工具内部。）
- **共同点**：三者都在**决策/轨迹/内容**层拦截 → **P-ctx**（解码文本进 context、改变下一步动作）落其射程；**P-direct**（不碰决策层）天然在其视野外。**只有 OS 级逐次行为引爆（SkillDetonate 一族）能看见 P-direct 的效应，而那只在首装门部署（成本）。**

**2×2 可防御性梯度：**

| 单元 | 谁能防住 | 为什么 | 我们的定位 |
|---|---|---|---|
| **E1×P-dir**（最易防） | 首装**静态代码扫描器**（MalSkills / USENIX 静态）+ 首装**行为引爆**（SkillDetonate，syscall 非代码扫描） | 首装即读到恶意代码（静态）/ 观测到恶意 syscall（引爆） | 机制对照，非主攻 |
| **E1×P-ctx** | 首装扫描器 ∪ 运行时 IPI 验证 (C) | 编码载荷首装可疑；一旦解码注入即被 (C) 抓 deviation | 双重覆盖，非主攻 |
| **E2×P-ctx** | 运行时 IPI 验证 (C) | 逃过首装复扫（更新缺口），但解码文本进 context、改变动作 → 落 (C) 射程；本质是 VIGIL 所述 tool stream injection 的**一种投递** | **次要 / 进阶臂**：新颖在投递，坐落已被 (C) 防的空间 |
| **E2×P-direct**（最难防·**主攻**） | **唯有逐次调用的 OS 级行为引爆** | 逃过首装复扫（更新缺口）**且**不碰 context / 决策层——(A)(C) 无文本 / 无动作可验，(B) 首装一次不复扫；malice 在合法工具进程内、决策层之下 | **韩老师定为主攻**：植入代码直执，全程不进 LLM context/thinking，仅用工具既得权限 = 传统 malware，但因不复扫更新、且非已知恶意样本，连每次扫描的 AV 引擎（VirusTotal / Cisco / Trend）也检不出 |

> **韩老师 2026-09-08 定调**：**首先定位 E2×P-direct**——它逃的不只是文本检测，是**整族运行时决策验证 (C)**，因为恶意根本不经过 agent 的决策。**E2×P-ctx 作进阶/次要臂**：攻击指令一旦进 LLM backbone 的 context，就与 VIGIL 描述的 tool stream injection 同过程、可能被 (C) 拦——**是我们所利用漏洞的一种投递方式，不是主攻**。
> **诚实边界**（延续上文）：per-invocation 的 OS 级引爆**理论上**能检出 P-direct，我们**不声称**击败它；但（i）无已部署框架逐次部署（成本），（ii）连提出者 SkillDetonate 也只在首装引爆。主张仅限「对**已部署防御 + 首装门形态**无效」。
> **★ 三层防御图（2026-09-09 修正 · 防 SkillDetonate 措辞陷阱）**：`代码扫描`不是一族而是**三层**，三者观测面不同、被击败方式不同——
> - **(1) 静态代码扫描器**（读代码文本/结构：MalSkills / USENIX 静态半边 / SkillSpector）——被**混淆**击败（= SkillCloak 已发表：`static scanner collapses from 99% to 10% under Structural Obfuscation`，Q33），且首装一次 → 也被 **E2 更新缺口**击败。
> - **(2) 运行时决策/轨迹审计 (C)**（读 LLM 工作轨迹文本：ARGUS / AgentDoG / VIGIL；`the input of AgentDoG is confined to text-based trajectories`，Q29）——被 **P-direct**（不进决策层、返回值不含恶意结果）击败。
> - **(3) OS-syscall 行为引爆**（SkillDetonate：`observes only the OS level syscalls`，Q33，**非代码扫描**）——**混淆对它无效**（`sustains 87% detection and stays stable under SkillCloak`，Q33）；唯一诚实的击败论点是**部署形态 = 首装一次门**（更新不复扫，E2 缺口）+ **成本**（153s + 14.1K token/skill）。
>
> **自适应攻击者（韩老师 2026-09-08 新问 · 授权待批 · 措辞已按 Q33 收紧）**：
> - **对 (1) 静态扫描器**：code agent 生成 + 混淆（fang 五法 DE/DCI/CFF/SS/WSM，Q35）压低检出率——**但这大体是 SkillCloak 已发表结论（引用、非我方主张）**；我方差异化 = **投递路径（E2 更新）+ 工具/npm 生态 + code-agent 生成**，不是"我们发现混淆能逃扫描器"。
> - **对 (3) 行为引爆**：**混淆不管用**（Q33）；要击败它需**行为/沙盒规避**（环境键控激活、沙盒检测、逻辑炸弹）——**另一类更敏感技术**，论文显示引爆对混淆稳健，故这是**开放测量问题**、非既成胜利，且很可能**不必要**（主论点靠更新缺口即可）。
> - **禁写"混淆击败一切代码扫描 / 击败逐次引爆"。** 定性为**授权的防御效能测量**（对**自适应攻击者**的检出率），合成 payload / 127.0.0.1 信封内。**授权分层（2026-09-12 生效）**：对 (1) 静态扫描器的规避测量（A1.5 JS 混淆 + A1.7 扫描器集，跑在 **Goose×{G1,G2,G3}** 主台）已在 idea/52 §14 EFFECTIVE 范围内，可按 §6.3 建台后开跑；对 (3) **行为/沙盒规避仍 gated**（超出本期范围、design-only、须二期单独扩权）。**跨对象（OpenCode/Gemini）/ G4 / Claude Code 亦 deferred。**

### 韩老师收尾问：Claude Code / Codex 有这个漏洞吗？（DOCS/SOURCE 屏读结论 · 非 run · 2026-09-06）

> **口径**：这是**文档/公开来源的适用性屏读**（applicability screening），**不是**已确证的 exploit，**也不是** idea/52 下的 run——即便 idea/52 授权已于 2026-09-12 生效，其对象范围为 **Goose 主台**，**Claude Code/Codex 本期 deferred（选项 A，见 §5 / idea/52 §14 CC 裁定）**，故此处仍只作屏读、不跑。区分**权限/信任提示**（问用户是否放行能力）与**代码验证**（检查工具真实代码里的恶意行为）——两款产品都有前者、都**没有**后者。

**Codex CLI —— 面存在且已被公开文献记录（最强档）。**
- 第三方工具装载：`~/.codex/config.toml` 或项目内 `.codex/config.toml` 的 MCP server（stdio `command`+`args`，如 `npx -y @brightdata/mcp`），作为子进程运行。
- 首装：无代码扫描/签名/审查；信任绑在**项目目录**（`trust_level`），配 per-tool approval——**能力门，非代码检查**。
- 更新：**Check Point CVE-2025-61260（≤v0.23.0）逐字**："There is no interactive approval, no secondary validation of the command or arguments, and **no re-check when those values change**"（Our Research Findings §，核对 2026-09-06）。其机制逐字：**"the behavior binds trust to the presence of the MCP entry under the resolved CODEX_HOME rather than to the contents of the entry"**——故良性 config 可 post-approval/post-merge 被换成恶意（Technical Deep Dive §）。Mindgard 将其一般化为 **"Approve Once, Exploit Forever"** 的信任持久化问题（标题逐字；Claude Code/Codex/Gemini CLI 共有），提议修复「信任应绑到被执行的内容、可执行 config 变更时重新批准」**正是当前缺失的**。（Mindgard 用 TOCTOU 一词描述——**该词是 Mindgard 的、非我们的**；我方记录仍守 level-2、不使用 TOCTOU。）
- Caveat：CVE 已在 >v0.23.0 修复「无提示自动执行」——但补的是**信任/批准门，非代码验证**；Mindgard（~2026）指信任持久化缺口仍在。

**Claude Code —— 面很可能存在（文档口径）。**
- 装载两条：`claude mcp add` 的 MCP server（stdio = 本地命令行进程，用户权限）；marketplace 的 plugins（打包 skills/agents/hooks/MCP/`bin/` 可执行文件）。
- 首装：MCP 文档**通篇只有信任门/执行语言，没有任何「扫描 / 沙箱 / 签名 / 代码审查 server 代码」的表述**——即"代码验证"这一能力在文档中缺席（这是我们的分析，非引语）。文档逐字警告 **"Verify you trust each server before connecting it"**（MCP 页 Find-and-build-MCP-servers §，Warning 块，逐字核对 2026-09-06）。Plugins 页逐字：**"Anthropic doesn't control what MCP servers, files, or other software are included in plugins and can't verify that they work as intended"**（discover-plugins §Manage），且 plugins/marketplaces **"can execute arbitrary code on your machine with your user privileges"**（discover-plugins §Security，逐字核对 2026-09-06）。唯一部分例外：社区 marketplace 提交时过 Anthropic 自动校验（`claude plugin validate` + automated safety screening）并钉 commit SHA——**作者侧提交门**，不适用于官方 curation / 任意 Git·URL·local marketplace / `--plugin-dir`。
- 更新：官方 marketplace **默认 auto-update**——后台刷新并把 plugin 更新到磁盘最新版，只提示 `/reload-plugins`，**无文档化的复验/复扫**；`npx -y …@latest` 的 MCP 每次启动拉新上游代码、无复检。**先前信任静默延续。**

**结论（供 §5 问1）**：两款都**只 gate 能力、不做代码验证**，更新时不复扫——**正是我们描述的面**。Codex 有 CVE + 独立研究背书（最适合 capstone 引用为 real-external-cited motivation）；Claude Code 为文档级路径。**但**：把任一款做成 **⑦ capstone 的 real-ours 演示**，仍需**对象范围扩权**——idea/52 已于 2026-09-12 生效，但本期对象锁定 **Goose**，**Claude Code/Codex 属 deferred**（CC 扩权前置 = Python/Shell 载荷与混淆方案调研完成 + 披露评估，见 idea/52 §14 CC 裁定）——**在该扩权 run 存在之前只写 "applicability screened, measurement pending scope-expansion"，绝不断言**。
> 屏读来源核对提醒：两条 vendor 文档 URL（code.claude.com / learn.chatgpt.com）与 Check Point / Mindgard 帖，引用前正文里再核一遍。

---

## 3. 实验 1/2/3（服务于 story，非覆盖矩阵 · 供 韩老师 挑）

> 罗老师 的实验方法透镜：每个实验问「**它证明什么 / 排除什么 / 目的是什么**」，方法从 idea/51-方法库借。实验是主要工作量，但由 story 决定选哪些、不做大杂烩。

- **E-② 防御结构性无效（interesting · 最成熟）**
  证明：描述侧防御线（IPI 检测 / 消毒 / 描述 diff / surface pin）对代码载荷检不出、拦不下。
  排除：`fail-silent-by-breakage`（强制阳性对照——同一危害的描述侧变体它拦得住）。
  资产：idea/52 §7，已冻结。方法借：MCPTox §4.3（re-host 同一危害于另一载体）。
- **E-③ 可实操性 / 野外暴露（impressive）**
  证明：这个面在真实生态**可操作**（P1 演示）＋**普遍存在且供应商不复审**（方向二 tarball-diff：xz 教训——毒在发布物不在仓库）。
  排除：主指标是**暴露度 / 缺乏复审**，*不是*"抓到多少恶意样本"（不可证伪、方差大、披露风险）。
  资产：idea/52 §5.2（P1）+ 方向二协议（**待写**）。方法借：MalOSS / Backstabber's taxonomy。
- **E-① 知名产品演示（very impressive · gated）**
  证明：大家在用的 agent 也中招 → 重要性不言而喻。
  现状：**主台授权已生效（2026-09-12）但本实验对象（Codex/Claude Code）属 deferred + 未 run（run=0）**；纳入与否属 §5 待决、须二期对象扩权（CC 前置 = Python/Shell 混淆方案）。**预留槽，不列为已有结果。**

> 三者与 story 的对应：② 支撑 thesis ②/⑤；③ 支撑 ①（现实血统）+ ⑥（影响）；① 是可选 capstone ⑦。

---

## 4. 每个实验刻意**不主张**什么（前置堵审稿）

- drift 恒停 **level-2**；impact 结果不回填、不给冻结记录重新定级。
- forbidden vocab：**TOCTOU / exploitable vulnerability / exploitability / approval bypass**；精确版本臂永远叫**版本号绑定**，不叫「内容绑定」。
- **不池化**三对象；**3/3 = 确定性、非发生率**；OpenCode/Gemini 同版本 = `not_tested`、不外推。
- 著名事件（xz 等）是**动机引用**，**不是**我们的结果；我们**不声称**发明供应链攻击。
- OSV / reputation 恶意包检测**正交**，**不主张**击败它（我方是本地良性替身、天然不在恶意库）。
- capstone（⑦）在 run 存在前**不断言**。

---

## 5. 留给 韩老师 的待决问题

1. ~~**对象集**：capstone 是否纳入 Codex / Claude Code？~~ **【已决 2026-09-09】对象仅 Goose 锚点**；G4 与跨对象（OpenCode / Gemini CLI）deferred；**Codex / Claude Code 维持筛查/文档层**（Codex-CVE 仅作 real-external-cited motivation 引用），红队 run 须单独扩权。范围锁定见 idea/52 §14 EFFECTIVE RECORD（生效 2026-09-12）「授权运行范围锁定」。
2. ~~**一篇还是两篇**~~ **【已决 2026-09-09】一篇**：方向一（controlled attack + 最小可行性）+ 方向二（ecosystem measurement）**合写一篇**，S&P'26 式「攻击先行 → 测量随后」；**方向二以「有界暴露抽样」进入**（非全量普查，规模视抽样产出再扩），信封条款（被动 tarball 分析 / 无主动探测 / 不断言恶意 / 不对重发布政策做主张）见 idea/52 §14 EFFECTIVE RECORD（生效 2026-09-12）。
3. **头条**：E-② / E-③ / E-① 哪个当 headline？（②最成熟、③最 impressive-且-可做、①最重但 gated。）
4. **motivation 开头**：外部 hook（xz 三例）+ 我们的 finding（版本号≠内容）这套引入方式，是否够 interesting、逻辑是否站得住？

---

## 6. 真实性与引用守则（扩散思维的护栏）

- **允许**用外部真实事件做 impressive 引子；**前提**是 ① 逻辑正确 ② 可考证为真实，且**明确标注为 motivation、非本文结果**。
- 我方每个 beat 必须能落到**冻结文件 + sha256**（§2 表）；落不到的，不进正文当结果。
- **gated beat 永不断言**：没有 run 就只写 screened/pending。
- 著名 CVE / 事件引用**核对准确**（编号、年份、载体），错引比不引更糟。

---

## 7. 下一步与依赖

1. **本文件（idea/53）→ 与 韩老师 过 §5 四问**（罗老师 指定的讨论前提）。
2. 文献线（纯文献、零授权，可并行）：
   - ✅ idea/51 **已重标为实验方法库**（§E：逐条「证明什么 / 排除什么 / 目的」+ 映射，2026-09-05）；
   - ✅ **post-2023「漏洞发现型」论文补扫已完成**（narrative-scan 2026-09-05，6 篇核实）→ 四个叙事动作已落到 §1.6，hook/E-② claim 形状已据此加强；
   - ⏳ novelty 矩阵**人工核对**：日期剪枝 → 轴相关性 triage → 只粗读「可比」桶 → 窄表重建（缩小 related-work 覆盖、放大我方，视觉拉开差距）——**在本文件（§1.6 动作2）定下机制脊柱的轴之后做**；~35 篇独立扫查，宜开子代理并行。
3. **方向二协议**（E-③ 的 tarball-diff 台子）：**一篇已定** → 方向二作为「**有界暴露抽样**」子台起草（信封：被动 tarball 分析 / 无主动探测 / 不断言恶意 / 不对重发布政策做主张，见 idea/52 §14）；只测能力面 + 更新暴露的**普遍性**，不测恶意普遍率（level-2 + 无外推）。
4. **授权**：idea/52 **已于 2026-09-12 生效**（H1 归档纪要 + H2 填哈希前快照 + H3 会上口头确认，三哈希锚定；见 idea/52 §14 EFFECTIVE RECORD）——**本期范围 = Goose×{G1,G2,G3}**，可按 §6.3 建台后逐次开跑；**capstone / 跨对象（OpenCode/Gemini/Codex/Claude Code）/ G4 / 行为规避仍需二期书面扩权**（归档+哈希）方可 run。

---

## 8. 外部引文台账（citation ledger · 像内部证据的 sha256 一样，每条带 provenance）

> 制度化（用户 2026-09-06 建议）：**正文每一处带引号的外部引语，在此登记「逐字原文 · 出处+节号 · 核对日期 · 状态」。** 状态 = ✅verbatim-verified / 🟡paraphrase-not-quoted / 🔴removed / ⏳unverified。**未达 ✅ 的引语不得以引号形式进正文**；机制断言无原文支撑者写成分析句、不加引号。发老师前 `grep '"'` 逐条对齐本台账。

| # | 引语（逐字） | 出处 · 节号 | 核对日期 | 状态 |
|---|---|---|---|---|
| Q1 | `a version binding is not a content binding; the string '1.0.0' was rebound to B's bytes and Goose executed B.` | 内部冻结 `SV_RESULT_v1`（CROSS_OBJECT_AB_RESULTS_v2 §2） | 2026-08-28 | ✅（real-ours，非外部） |
| Q2 | `an offline, once-per-skill install gate` | SkillDetonate 2607.02357 · VI（cost 段） | 2026-09-06 | ✅ |
| Q3 | `at the cost of breaking self-updating skills` | 同上 · VI-C | 2026-09-06 | ✅ |
| Q4 | `dynamic execution auditing is the load-bearing defense` | 同上 · VI-C | 2026-09-06 | ✅ |
| Q5 | `Verify you trust each server before connecting it.` | Claude Code MCP 文档 · Find-and-build-MCP-servers §（Warning 块） | 2026-09-06 | ✅ |
| Q6 | `Anthropic doesn't control what MCP servers, files, or other software are included in plugins and can't verify that they work as intended` | Claude Code discover-plugins · Manage installed plugins § | 2026-09-06 | ✅ |
| Q7 | `can execute arbitrary code on your machine with your user privileges` | Claude Code discover-plugins · Security § | 2026-09-06 | ✅ |
| Q8 | `no re-check when those values change` | Check Point CVE-2025-61260 · Our Research Findings § | 2026-09-06 | ✅ |
| Q9 | `binds trust to the presence of the MCP entry under the resolved CODEX_HOME rather than to the contents of the entry` | 同上 · Technical Deep Dive § | 2026-09-06 | ✅ |
| Q10 | `Approve Once, Exploit Forever`（Mindgard 帖标题；TOCTOU 一词属 Mindgard、非我方） | Mindgard blog（trust-persistence） · 标题 | 2026-09-06 | ✅ |
| Q11 | `before installation or use` | SkillTrustBench HuggingFace dataset card | 2026-09-06 | ✅ |
| Q12 | `the first knowledge corruption attack to RAG` | PoisonedRAG 2402.07867 · abstract/intro | 2026-09-06 | ✅ |
| Q13 | `may not achieve the generation condition`（语境：其自证朴素构造的两条件张力） | PoisonedRAG 2402.07867 · §Deriving two conditions | 2026-09-06 | ✅ |
| Q14 | `a new class of automatically computed obfuscated adversarial prompt attacks` | Imprompter 2410.14923 · intro | 2026-09-06 | ✅ |
| Q15 | `do not reveal their purpose upon inspection` | Imprompter 2410.14923 · related work | 2026-09-06 | ✅ |
| — | ~~`there is no second pass`~~（SkillDetonate）| — | 2026-09-05 | 🔴 removed（原文无此句，误造） |
| — | ~~`cannot achieve the generation condition`~~（PoisonedRAG）| — | 2026-09-06 | 🔴 removed（曲解为 baseline 结构性失败） |
| — | ~~`the novel part is the way they obfuscate`~~（Imprompter）| — | 2026-09-06 | 🔴 removed（原文无此句） |
| — | ~~`first on this surface`~~（PoisonedRAG）| — | 2026-09-06 | 🔴 removed（非逐字，改用 Q12） |
| — | ~~`only checked whether the MCP entry was present…not what was in it`~~（Check Point）| — | 2026-09-06 | 🔴 removed（paraphrase，改用 Q9） |
| — | ~~`no scanning, sandboxing, signature checking, or code review of server code`~~（Claude Code）| — | 2026-09-06 | 🔴 removed（不在 MCP 文档；改写为无引号分析句） |
| Q16 | `unlike traditional app vulnerability exploitation, the payload for such attacks consists solely of natural language expressions` | LLM4Shell 2309.02926 · body | 2026-09-06 | ✅ |
| Q17 | `a novel combination of attacking strategies including hallucination test and LLM escaping` | LLM4Shell 2309.02926 · contribution | 2026-09-06 | ✅ |
| Q18 | `a novel form of package confusion attack` | slopsquatting 2406.10279 · abstract | 2026-09-06 | ✅ |
| Q19 | `a variation of the classical package confusion attack that has been enabled by code-generating LLMs` | slopsquatting 2406.10279 · body | 2026-09-06 | ✅ |
| Q20 | `The OSS community has thoroughly investigated the attack's technical aspects, but a centralized, systematic analysis is still needed` | XZ 2504.17473 · §I | 2026-09-06 | ✅ |
| Q21 | `lies in providing a comprehensive perspective of the attack timeline` | XZ 2504.17473 · §I | 2026-09-06 | ✅ |
| Q22 | `a dynamic benchmarking framework which we populate–as a first version–with 97 realistic tasks and 629 security test cases` | AgentDojo 2406.13352 · §1 | 2026-09-06 | ✅（idea/51 用） |
| Q23 | `an injection might fool the LLM simulator too` | AgentDojo 2406.13352 · §2（ToolEmu 批评） | 2026-09-06 | ✅（idea/51 用） |
| Q24 | `the first large-scale empirical evidence of Tool Poisoning's effectiveness on real-world MCP servers` | MCPTox 2508.14925 · §1 contributions | 2026-09-06 | ✅（idea/51 用） |
| Q25 | `the first public benchmark designed specifically for MCP Tool Poisoning` | MCPTox 2508.14925 · §1 | 2026-09-06 | ✅（idea/51 用） |
| Q26 | `VIGIL: Defending LLM Agents Against Tool Stream Injection via Verify-Before-Commit`（术语 "tool stream injection"） | VIGIL 2601.05755 · 标题 | 2026-09-08 | ✅（arxiv 元数据 + tavily 原文） |
| Q27 | `a runtime verifier strictly validates these tentative trajectories before commitment` / `rectifies deviations induced by malicious tool feedback` | VIGIL 2601.05755 · 摘要 + §4 框架 | 2026-09-08 | ✅（tavily 原文；§4.5 内部未逐行） |
| Q28 | `ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection`（标题）；机制 `ARGUS mediates every tool call proposed by the agent` / `State-changing calls trigger an audit` / `a runtime decision auditor that makes the evidence behind each state-changing action explicit before execution` / `it traces each tool-call argument back to the span from which the value was copied, normalized, derived, or resolved` | ARGUS 2605.03378 · 标题 + §方法（tavily 原文） | 2026-09-08 | ✅ raw-verified |
| Q29 | `AgentDoG: A Diagnostic Guardrail Framework for AI Agent Safety and Security`（标题）；`provides fine-grained and contextual monitoring across agent trajectories` / `the input of AgentDoG is confined to text-based trajectories`（§8.2）/ taxonomy `source (where), failure mode (how), and consequence (what)` 含 `malicious tool execution` 一类 | AgentDoG 2601.18491 · 标题 + §8.2/摘要（tavily 原文） | 2026-09-08 | ✅ raw-verified |
| Q30 | `The overall rejection rate is low, and the attack success rate is high for all code agents` | RedCode 2411.07781（NeurIPS'24 D&B）· 结论 | 2026-09-09 | ✅ raw-verified（tavily） |
| Q31 | `the first automated red-teaming agent designed to systematically uncover vulnerabilities in diverse code agents` / `avoid biases introduced by LLM-based evaluators` | RedCodeAgent 2510.02609 · 摘要/方法 | 2026-09-09 | ✅ raw-verified（tavily） |
| Q32 | `Breaking the Code: Security Assessment of AI Code Agents Through Systematic Jailbreaking Attacks`（标题）；`largely stop at textual refusal or harmful-content detection; they do not assess whether agents can write runnable malicious code`；agent-agnostic 覆盖 OpenHands/SWE-Agent/Codex-Agent | JAWS-Bench 2510.01359 · 标题+§1 | 2026-09-09 | ✅ raw-verified（tavily） |
| Q33 | 完整标题 `Cloak and Detonate: Scanner Evasion and Dynamic Detection of Agent Skill Malware`；机制 `SkillDetonate runs the skill in a single sandboxed agent session and observes only the OS level syscalls`（∴ 是 **syscall 行为审计非代码扫描**）；`a behavior-centric runtime auditor that … detects malicious effects through OS-boundary information-flow evidence rather than install-time appearance`；对混淆 `sustains 87% detection and stays stable under SkillCloak`，而 `the best static scanner collapses from 99% to 10% under Structural Obfuscation`；`with SFS Packing, over 90% of evasion skills bypass all scanners` | Cloak & Detonate 2607.02357 · 标题+摘要+§IV（arxiv-html raw） | 2026-09-09 | ✅ raw-verified（tavily · **更正**早前"代码扫描器"误标） |
| Q34 | `MCP Unintended Privacy Disclosure (MCP-UPD)`；三阶段 `Parasitic Ingestion, Privacy Collection, and Privacy Disclosure`；`8.7% of all tools and 27.2% of all servers expose exploitable capabilities`（1,062/12,230 · 370/1,360）；§II-B1 目标 `unauthorized data exfiltration … sensitive local files (e.g., configuration files containing API keys)`；§VI-D2 `Arbitrary File Write` / §VI-D1 `Remote Command Execution`（future work）；根因 `MCP lacks both context–tool isolation and least-privilege enforcement` | Parasites in the Toolchain 2509.06572（IEEE S&P'26）· 摘要+§I+§II-B+§VI-D（arxiv-html v5 raw） | 2026-09-09 | ✅ raw-verified（tavily · G1/G2←II-B1、G3←VI-D2、G4←VI-D1 映射据此） |
| Q35 | fang 五混淆法 "tested obfuscation methods"：`Default obfuscation (DE), which replaces identifier names with meaningless randomly generated strings, simplifies source code to reduce readability, placing strings in separate arrays, etc.` / `Dead code injection (DCI), which inserts random unrelated code blocks` / `Control flow flattening (CFF), which transforms the structure of a program and hides control flow information` / `Split string (SS), which splits long strings into shorter chunks` / `Wobfuscator (WSM) … performs cross-language obfuscation`；工具 = open-source JavaScript Obfuscator + Wobfuscator | USENIX Sec'24 "LLMs for Code Analysis: Do LLMs Really Do Their Job?"（Fang）· §2.4 methods list（usenix PDF raw） | 2026-09-09 | ✅ raw-verified（tavily·JS↔npm 生态） |

> **U1–U3 已于 2026-09-06 逐字核实并升级为 Q16–Q21；§1.6 动作4 已替换为逐字引语。idea/51 亦已过台账**（Q22–Q25；改正 MCPTox "widespread vulnerability" 非 "systemically vulnerable"、"10 categories" 非 "8 域"）。台账制度覆盖所有要给导师看的文档（idea/51/52/53、slides）。**唯一有意留在台账外的是 novelty 矩阵的 AI 概括**——那是「关系声称」非「引语」，按 罗老师 要求等本人粗读，不作已核事实。
> **2026-09-08 增补 Q26–Q29**：VIGIL 标题/术语/机制为 tavily **原文** raw-verified；ARGUS/AgentDoG **亦已于 2026-09-08 经 tavily 原文 raw-verified**（标题 + 机制逐字，见 Q28/Q29）——初次 WebFetch 摘要的措辞经原文核对后**已用真正逐字句替换**（印证「子代理/抓取转述不得直接升为引语」纪律：WebFetch 转述与原文并不逐字一致，如 ARGUS「audit layer…intercepts tool calls」在原文实为「mediates every tool call proposed by the agent」）。SkillDetonate 两句 = **既有 Q2/Q3**（2026-09-06 已 ✅），2026-09-08 复核再确认：完整 cost 句 *"…is acceptable for an offline, once-per-skill install gate"* 在 **§V-A**、hash-recheck 片段 *"record a content hash at scan time, re-verify before each run"* 在 **§VI-C**（正文以无引号转述用之）。

---

## 9. Amendments

- **2026-09-06 · 折入 韩老师 2026-09-05 回复。** 理由：韩老师率先回复罗老师与我的讨论，给出更利落的根因表述与 2×2 框架，并点名 5 篇防御 + 收尾问「CC/Codex 有无此漏洞」。改动：
  1. 新增 **§2.5**：根因重述（缺失的能力 = 代码验证，非载体）+ **E1/E2 × P-ctx/P-direct 2×2**（取代旧 P0/P1/P2 单调阶梯，P0 留作机制对照）+ **5 篇防御全景两轴表**（逐篇核实：ACE / SkillTrustBench〔Tencent+CUHK-SZ，评测 install-time 扫描器的基准，读全 skill 内容〕 / USENIX'26 2602.06547 / MalSkills ASE'26 2603.27204 / Cloak&Detonate 2607.02357）。
  2. **两轴结论**：描述侧防御靠「代码≠描述」绕过；首装式内容/代码/行为扫描器（它们**读得到代码**，"代码≠描述"失效）靠**更新缺口 E2**绕过。诚实分轴，不硬套一条。诚实边界：per-invocation 运行时引爆会检出 P-direct，我们不主张击败它（未部署 + 成本 153s/14K-tokens/skill）。
  3. §1③ 翻面点改为「装时检一遍、更新不回头」；§1⑥ 影响改为 2×2；§2 Beat 表加防御两轴行、impact 行换 2×2、capstone 行填屏读结论。
  4. §2.5 末新增 **Claude Code / Codex 适用性屏读**（DOCS/SOURCE-ONLY，非 run）：两款都只 gate 能力、不做代码验证、更新不复扫；Codex 有 CVE-2025-61260（Check Point）+ Mindgard「Approve Once, Exploit Forever」背书；Claude Code 为文档级路径。屏读 ≠ run，capstone 仍 gated。
  > 纪律未变：level-2 天花板、forbidden vocab、no-pooling、127.0.0.1/合成密钥安全信封、idea/52 授权 PENDING 全部延续。

- **2026-09-06 · 引文清扫（citation sweep）。** 用户指出正文带引号的外部引文未逐字核实——这与前一日误造 SkillDetonate 引语同类、高危。逐条抓原文核对后：**改正 4 处**——(i) 删去 PoisonedRAG 误引 `"cannot achieve the generation condition"`（原文是"朴素构造 *may not* achieve"、语境是其自证两条件张力，非 baseline 结构性失败）；(ii) PoisonedRAG 新颖性引语更正为逐字 `"the first knowledge corruption attack to RAG"`；(iii) 删去 Imprompter 伪引 `"the novel part is the way they obfuscate"`（原文无此句），改为逐字 `"a new class of automatically computed obfuscated adversarial prompt attacks"`；(iv) 删去 Check Point 伪引 `"only checked whether the MCP entry was present…"`，改为逐字 `"binds trust to the presence of the MCP entry… rather than to the contents"`。**删去伪引 1 处**——Claude Code `"no scanning, sandboxing, signature checking, or code review of server code"` 不在 MCP 文档，改写为无引号分析句（文档中「代码验证能力缺席」）+ 保留真实逐字警告。**LLM4Shell / slopsquatting / XZ 三条引语标 UNVERIFIED，待核。** 全部已核引文的 provenance 收入 §9 台账。

- **2026-09-08 · 折入 韩老师 2026-09-08 定调 + 锁三防御机制。** 韩老师定 **E2×P-direct 为主攻**（植入代码直执、不进 context/thinking、仅用既得权限）。核实 ARGUS(2605.03378)/AgentDoG(2601.18491)/VIGIL(2601.05755) 三篇**运行时 IPI 防御**，确认其**只 gate 决策/轨迹/内容层、不观测工具代码内部行为**——故 P-direct 逃逸整族 (C)，仅逐次 OS 级引爆可及（无人部署、成本高）。改动：§2.5 新增**第三防御族 (C)** + **2×2 可防御性梯度表**；doc-header 加 2026-09-08 note；台账加 Q26–Q29。**自适应攻击者（code-agent 生成规避植入）**列为**授权待批**的防御效能测量，只写设计不跑。VIGIL 术语为 *"tool stream injection"*（非 "tool stream prompt injection"）。**ARGUS/AgentDoG/VIGIL 机制均已 tavily 原文 raw-verified（Q26–Q29）；初次 WebFetch 摘要措辞与原文不逐字一致，正文已替换为真正逐字句。** 纪律未变（level-2 / forbidden vocab / 127.0.0.1 / idea/52 PENDING）。

- **2026-09-09 · 折入 韩老师会议定调（UTCS 最小攻击实验）＋ 三层防御图修正 ＋ 清两笔核实债。** 会议定：承认 SkillDetonate 类 runtime auditor 理论可防，但论文口径用**成本**（153s+14.1K token/skill）+ **沙盒不可靠**回应（引用、不做真沙盒规避实验）；**E2×P-ctx 彻底砍**（进 context 即被 runtime 看见）；只做 **E2×P-direct**（完全工具主导、绕过 LLM 防御）；下一步 = 设计攻击场景 + 定目标 + 做**最小攻击实验验证可行性**。产出 **idea/52 Amendment 1**（UTCS 命名+三阶段、真实功能工具 v1、危害菜单 G1–G4[G1/G2/G3=MVP · G4 deferred]、code-agent 生成规格+双重验证器 V、五判据[四元组+`benign_function_preserved`+`task_completed`]、`trajectory_absent` 缺席证明程序[含 P-ctx 匹配器阳性对照]、第二步静态扫描器集、EFFECTIVE RECORD 须引本 Amendment sha256）。**清核实债**：Q34（S&P'26 2509.06572 三阶段/8.7%/§II-B1/§VI-D 映射）、Q35（fang 五混淆法 §2.4 逐字）均 **tavily 原文 raw-verified**，五混淆法为 A1.5 冻结内容故不带 ⏳ 落盘。**三层防御图修正（关键·防 SkillDetonate 措辞陷阱）**：`代码扫描`拆成 (1) 静态扫描（混淆击败=SkillCloak 已发表 + E2 缺口）/(2) 运行时轨迹审计 (C)（P-direct 击败）/(3) OS-syscall 引爆（混淆**无效**、唯部署形态+成本可论）——更正早前把 SkillDetonate 误标"代码扫描器"、及 §2.5 line 170 "混淆规避 SkillDetonate"的过度主张。台账加 Q30–Q35。**未新增任何危害量化主张**（idea/52 仍 PENDING）；level-2 / forbidden vocab / 127.0.0.1 / 授权门 纪律未变。
- **2026-09-08(b) · 折入 韩老师「分量论点」＋ 收敛 罗/韩 框定。** 韩老师澄清（回 罗老师「是否设计新攻击」）：**单发掘漏洞分量不够，重量在「揭示危害」＋「利用路径逃过现有代码扫描」**；E2×P-direct 是「利用此漏洞的一种攻击方式」、非新机制。改动：**§0 增第三条元原则 (C)**——重心从 finding 移到 E-②（防御逃逸结构性证明）＋ E-③（危害/影响）；明确回答 罗老师的「新攻击 vs 测试框架」二分（皆不精确：体裁仍是漏洞发现，工具是逃过防御的真实利用路径）；把「逃过代码扫描」精确到射程（静态首装扫描器 ＋ 运行时决策验证族，唯逐次行为引爆理论可及、无人部署）。**未新增任何危害量化主张**（E4/impact 仍待测、idea/52 PENDING）；纪律未变。

- **2026-09-12 · 授权激活（idea/52 §14 翻 EFFECTIVE）＋ Claude Code 范围裁定（选项 A）。** 三项授权门全部满足：**(H1)** 归档纪要 sha256 `c5b2ab59a240ab8549655ea272d6529fa8a6ffb189d1b53f56e51d6cf39d0311`（2026-09-09 会议纪要逐字落盘 `idea/archive/2026-09-09_han_meeting_minutes.md`）· **(H2)** 填哈希前的 idea/52 快照 sha256 `88e8fae51882d550c3521c3a8002f39089816cadc0deb8ba4f6a19d9e9114f43`（`idea/archive/2026-09-09_idea52_amendment1_snapshot.md`）· **(H3)** 导师确认出处（确认日 2026-09-12 · 渠道 会上口头确认 · 逐字摘录「可以按照这个做」〔即按 2026-09-09 纪要执行〕；诚实备注：口头确认无书面原文，以 H1 纪要为授权内容依据）。idea/52 §14 状态 **PENDING → EFFECTIVE，生效日 2026-09-12**，run 数自 0 起随实跑递增（本记录生效时 run=0，尚无 run）。**本期范围锁 = Goose×{G1,G2,G3}**；建台顺序：轨迹捕获仪表（A1.4 前提）→ 冻结生成规格+验证器 V → 真实功能工具 v1 → MVP（每格 3 次、五判据）。**Claude Code 裁定（选项 A · 已定）**：G4 / 跨对象（OpenCode/Gemini）/ Claude Code 均 deferred；CC 附注 = 扩权前置条件为 **Python/Shell 载荷与混淆方案调研完成 + 披露评估**（理由：A1.5 冻结混淆链 JS-only，而 CC 插件主力语言 Python 58% / Shell 25%，齐同学 2026-09-11 调研，载荷语言与混淆方案未备，CC 红队须与「Python/Shell 混淆扩展」捆绑为二期单独扩权）。据此把 §1/§2/§3/§7 及本节多处「PENDING 授权」现状句更新为 EFFECTIVE + 对象范围声明。纪律未变（level-2 / forbidden vocab / no-pooling / 127.0.0.1 合成密钥信封 / 三层防御图 / S1 平台停机）。
