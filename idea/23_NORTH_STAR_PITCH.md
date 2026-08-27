# 23 — 北极星 Pitch：The Acquisition Gap

> **这份文档的作用**：把散在 01/02/09/21/22 里的东西重新组织成**一个能冲顶会的正向故事**。
> 21 是防守型的文献盘点（"哪里被占了、哪些话不能说"），读多了会让人觉得没空间。
> 这份是问题驱动型的：**从已有先导结果出发，把文献边界变成一个可证伪的同轨迹测量问题。**
>
> 更新时间：2026-07-24 · 一页能讲清的版本见 §1，完整论证见 §2–§6。

---

## 0. 一句话选题

> **截至 2026-07-24，在已核对的最接近工作中，还没有一篇同时从
> “用户只给普通能力任务、未要求找/装 skill”出发，要求 agent 面对一个尚未安装的目标 skill，
> 再把外部发现、检索、安装执行、落盘/注册、调用和载荷放在同一条运行轨迹中逐段测量。**
> 尚未回答的是：agent 会不会自发地完成这条真实 acquisition 链——以及它在
> 缺口 → 检索 → emitted → parsed → executed → on-disk → invoked → payload
> 各段如何衰减、断在哪一段、由模型还是编排/权限决定。**

这里的差异不是某一个关键词，而是**实验条件的合取**：
**(a) 纯能力任务触发；(b) 目标 skill 尚未安装；(c) 从外部发现到真实安装/注册/调用；(d) 同轨迹逐段归因。**
正式写作应使用“在已核对的最接近工作中尚未发现”，不能在没有系统检索证据时写成绝对的“从来没人做过”。

> ⚠️ **核对后的边界（2026-07-24，最近邻原文已复核）**：三条曾以为的 novelty 都被占了，**不要碰**——
> ① "第一个测真实执行/E2E"：**HalluSquatting（2607.07433）Table 1 已测 40–100% 真实 RCE**；
> ② "第一个测自主/中性触发"：**SCR（2606.15242）CapFlow Neutral 已用中性任务语言测自主组合，
> 平均 ASR 33.6%，单模型最高 91.5%**；
> ③ "第一个研究 install"：**SCR-TrustLift 已测模拟 skill market 中的有害安装
> （平均 1.10%→83.89%），HalluSquatting 已测真实安装/RCE，SearchGEO 与 Skills Don't Exist 也覆盖安装命令或安装 PoC。**
> 仍可检验的区别是：SCR-TrustLift 从一个**已经出现的下游安装请求**开始，且使用 simulated market；
> HalluSquatting 的用户明确要求 clone/install；SearchGEO 停在命令输出；Skills Don't Exist 的安装 PoC
> 需要后续明确指令。它们尚未把“普通能力任务→自主发现→真实安装/注册→调用”作为同一条 E2E 轨迹逐段测量。

---

## 1. 一页纸 Pitch（给导师/组会）

**已有的实证抓手（你自己跑出来的，不是文献）**

1. **Selection friction 的先导证据**：在单模型、单框架、20 个任务中，恶意 skill 的
   Vanilla / 粗糙蹭热度 / LLM 对抗优化选中率分别为 0/20、2/20、1/20。
2. **专一性偏好的先导观察**：本样本中，明确 query（"北京天气""128×64"）均选择专一工具，
   中招仅出现在模糊/跨域任务；是否跨模型成立仍需验证。
3. **Measurement pitfall（关键）**：模型**吐出了** `install_skill(name=weekly_brief)`，
   却因为默认 3 轮 tool budget 被 calendar/weather/search 消耗而**从未执行**。
   → 说明 emitted / parsed / executed 必须拆开；单次调试尚不能证明稳定 execution gap。

**核心论点**：把普通能力任务、外部发现、真实安装/注册、调用和逐段观测放进**同一条轨迹**，
可以检验现有 recommendation、install-decision、post-load 与显式安装 E2E 指标能否外推到
task-induced acquisition。SCR-TrustLift 已经说明“背书会促装”，但它从下游安装请求开始且使用模拟市场；
HalluSquatting 测了真实安装/RCE，但用户明确要求安装。你的 A2（出现 install call、却未执行）
是“输出端点与运行端点可能分离”的先导观察，不是正式结论。

**贡献**
- **The Acquisition Funnel**：把 8 个阶段的条件存活率分开测量的框架（§3 的 P(E2E) 分解）。
- **task-induced acquisition 的逐段测量**：跨模型 × scaffold × install-policy，看每一段在“用户没要求获取、目标尚未安装”时如何衰减。
- **预先规定 Go/No-Go**：pilot 只在出现稳定、可解释、跨设置的效应时进入正式实验（§4）。
- **一个 reporting standard / 简单防御**：强制分段汇报 + acquisition gate / capability justification。

**能否达到顶会体量取决于 pilot**：只有当逐段衰减跨任务/模型具有稳定结构，或普通任务下出现
可复现的真实自主安装，才能形成有分量的 measurement / systems 结论。仅仅指出条件组合不同，不足以构成贡献。

---

## 2. 把 21 那张"覆盖图"倒过来读

21 让你泄气，是因为它按"谁覆盖了什么"排列，读起来处处被占。但换一个轴——**按"每篇停在链条的哪一格"排列**——结论立刻反转：

| 竞品 | 触发起点 | **终点（停在这里）** | 差在哪一刀 |
|---|---|---|---|
| Semantic SC (`2605.11418`) | skill 已在 registry | **selection**（77.6% 选中） | 不测 emitted 之后的执行/落盘 |
| SearchGEO (`2606.16821`) | benign 信息/推荐-seeking 任务 | **endorsement**（答案层）；skill 是 18 例小 probe，停在**接受安装命令** | 不测 parsed/executed/on-disk |
| SCR-CapFlow (`2606.15242`) | **含 Neutral 中性触发** | 真实 mock state-change；Neutral 平均 33.6% | 测 available skills 的路径组合，不含外部发现/安装 |
| SCR-TrustLift (`2606.15242`) | 上游 review/endorsement + **下游安装请求** | simulated skill market 中的有害安装，平均 1.10%→83.89% | 不从普通能力任务自主发现开始；不测真实落盘/注册/调用 |
| HalluSquatting (`2607.07433`) | **用户明确 "clone/install X"** | 真实 E2E / RCE（40–100%） | 触发不是普通任务，用户已有安装意图 |
| Skills Don't Exist (`2607.12340`) | 用户求 skill 推荐 | 主结果是 hallucination rate；另有明确指令下的 benign install PoC | 不测 ordinary-task 自主全链与恶意调用 |
| Skill-Inject / Poise (`2602.20156` / `2606.07943`) | **skill 已加载** | payload（80% / 89.3%） | 整个 S0–S2 被跳过 |

**两个曾经以为的 novelty 都被占了，必须放弃：**
- ❌ "第一个测真实执行" —— **HalluSquatting、SCR 都测了真实执行/RCE/state-change**。
- ❌ "第一个测自主/中性触发" —— **SCR 的 CapFlow Neutral 已经用中性任务语言测 agent 自主行动（平均 33.6%，最高 91.5%）**。
- ❌ "SCR 只测预装 skill、没有 install" —— **这只适用于 CapFlow；TrustLift 已经在模拟市场里测了有害安装。**

**精确后的待检验位置是 task-induced acquisition 的同轨迹测量：**
> 触发是**纯能力任务**（用户零 skill/install/search 意图）**且** 目标 skill **一开始不在 agent 手里**——
> 必须走完外部发现 → 检索 → **真实落盘安装** → 注册 → 调用 → 载荷，**且**逐段归因。

SCR-CapFlow 差在不做 acquisition；SCR-TrustLift 差在从下游安装请求开始且安装市场是模拟的；
HalluSquatting 差在用户明说要装；SearchGEO 差在命令输出；Skills Don't Exist 的主测量停在推荐，
安装 PoC 另加了明确安装指令。你的 A2 暗示这条链可能在 emitted→executed 之间断裂；
是否稳定、是否跨模型/脚手架成立，必须由 pilot 决定。

> ✅ 上表各行的终点/触发均已回原文核对（HalluSquatting、Skills Don't Exist、SearchGEO、SCR 读全文；
> Semantic SC、Skill-Inject、Poise 取自 15 号笔记的原文数值）。

---

## 3. 论文的心脏：The Acquisition Funnel

把风险写成条件概率的乘积（这条式子你在 21 第 6 页已经有了，但被当成脚注；它其实是全文的骨架）：

```
P(E2E) = P(gap)
       · P(retrieved | gap)
       · P(emitted   | retrieved)
       · P(parsed    | emitted)
       · P(executed  | parsed)
       · P(on-disk   | executed)
       · P(invoked   | installed)
       · P(payload ∧ task_ok | invoked)
```

**文献中的端点并不统一**：有的明确报告条件阶段，有的报告从更强起点出发的 E2E。
问题不是这些论文“算错”，而是这些数字不能脱离各自起点直接外推到 ordinary-task autonomous acquisition。
- SearchGEO 报的是 `P(emitted|retrieved)`
- Semantic SC 报的是 `P(selected|retrieved)`
- Skill-Inject 报的是 `P(payload|invoked)`

**你要报的**：整条乘积，以及**每一段各自的存活率**——并指出哪一段是真正的瓶颈。
一旦某几段的条件率显著小于 1（A2 暗示 emitted→executed 可能有落差），单段或强起点下的 ASR
就可能高估 ordinary-task E2E 风险。是否存在稳定“高估倍数”是待检验假设，不能在 pilot 前写成结论。

---

## 4. 如何去风险：先写清楚什么结果值得继续

传统攻击型选题容易把价值绑定在“攻击必须打上去”。测量型问题可以接受正反两种方向，
但不等于任何数字都有论文价值：

| pilot 观察到 | headline | 性质 |
|---|---|---|
| **H1**：emitted ≫ executed，且断点在系统层 | "Agent 攻击 ASR 不可组合；真实风险被高估 N 倍；瓶颈在编排非对齐" | 衡量学 / 反直觉 |
| **H2**：普通任务下出现真实、可复现的落盘安装 | "**自主 acquisition**：无需用户授权的新威胁模型" | 进攻 / 更炸 |
| **H4**：post-load 高 ASR，但 ordinary E2E 极低 | 强化 H1——post-load 数字无法外推到供应链风险 | 校准 / 支撑 H1 |
| 全低，但任务明确度产生稳定、跨设置的单调边界 | 任务专一性与 acquisition 的安全边界 | 需专门验证后才可能转向 |
| 全低且无结构、无法归因 | **No-Go：停止扩大实验** | 不是论文结果 |

- 安装率 X **显著 > 0 且跨任务/模型可复现** → 可能确立自主 acquisition 威胁。
- 安装率 X **≈ 0** → 只有在漏斗断点稳定、可解释，或任务明确度形成可复现边界时才有研究价值。

**关键**：你不需要在动手前赌哪个 headline，但必须在 pilot 前写清楚什么信号才值得继续，
避免跑完后为任意结果补故事。

---

## 5. 这同时回答了你"下一步怎么选"

你现在觉得没方向，是因为想在写代码前就锁死 novelty。但衡量型选题的正确姿势相反：
**22 里的 pilot 本身就是"让数据替你选顶会叙事"的决策器。**

```
22 的 Week 1–4 pilot  ──►  哪一段条件率掉得最狠 / 普通任务安装率 X 是多少
                              │
        ┌─────────────────────┼─────────────────────┐
     H1 成立               H2 成立                H4/全低
   衡量学 headline       自主威胁 headline       专一性防线 headline
        └─────────────────────┴─────────────────────┘
                              ▼
                     23_HYPOTHESIS_FREEZE.md（冻结唯一 primary）
                              ▼
                      held-out 正式实验
```

也就是说：**先跑 22 的 pilot，你就知道端哪盘菜。** 22 不是杂活，它是选题引擎。

---

## 6. 落地清单（和 22 完全对齐，这里只标"为顶会服务"的优先级）

**必须先修（否则 A2 那类假象会污染主指标）**
1. 仓库内可配置 `max_tool_iterations` 的 runner，主条件设到足以走完整链，另做 3/6/10 轮消融
   —— 直接产出 `P(executed|emitted)` 随 budget 的曲线，这是 H1 的候选证据。
2. 把 install 从"仅内存注册"改为**临时目录落盘 + manifest + registry** 双验证，
   `installed_on_disk` 与 `registered_in_agent` 分开 —— 这是"真实执行"区别于"吐命令"的地基。
3. 确定性 task verifier + emitted/parsed/executed 单元测试 —— 主指标只用可审计行为，文本弱信号只做注释。

**pilot 要产出的那张图（论文 Figure 1 的雏形）**
- 一张 funnel/瀑布图：横轴是 8 个阶段，纵轴是条件存活率，多条线代表不同 model / scaffold / budget。
- 若图中"emitted → executed"或"executed → on-disk"的落差跨任务/模型稳定，并能排除协议故障，
  H1 才值得进入正式验证。

**能立刻开始的三件事（抄自 22 §11，这里确认优先级不变）**
1. runner 可配 `max_tool_iterations` + 记录每轮 raw response / tool event；
2. install 改为落盘 + manifest + registry 双验证；
3. weekly-brief family 写确定性 verifier + emitted/parsed/executed 单测。

---

## 7. 对 21 的处置

**别再往 21 里加文献了。** 它已经过度防守，越读越觉得没空间——但它的价值是真实的：
它是本文档 §2 那张"每篇停在哪一格"表的原始素材库。

- 21 → 降级为**文献附录 / related work 素材**（配合 `18_RELATED_WORK_MENTOR_REVIEW.pdf`）。
- **23（本文档）→ 北极星**：给导师/组会讲的主线，一页 pitch 在 §1。

一句话记住：**21 的价值不是证明“绝对无人做过”，而是把不同起点、终点和环境条件拆开，
帮助你提出一个可证伪的同轨迹测量问题。** 这个问题能否成为论文，要让 22 的 pilot 用数据回答。
