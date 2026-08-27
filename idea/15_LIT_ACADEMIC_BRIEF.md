# 文献综述简报：Skill Acquisition Barrier

**研究问题（一句话）**  
恶意 skill 在进入 agent 工具列表并被合理调用之前，是否存在可量化的瓶颈？若存在，卡在哪一段？

**本文档用途**  
开题 / 组会 / related work 口述稿。不是文献清单。

**L1 口径更新（2026-07-16）**  
显式 install 请求下的真实安装/调用，以及安装命令输出 ASR，已有直接工作。本文不再声称“无人测 install”，而把空白收窄为：**普通任务触发的 agent-initiated acquisition、实际安装执行及其分段 E2E。**

---

## 1. 问题从哪来

间接攻击往往被拆成两截：

```
① 恶意内容如何进入模型视野
② 进入后是否被执行
```

经典工作大量默认 **① 已经成立**，只评 ②。  
IPI 论文首先系统指出：在检索场景里 **① 才是真瓶颈**——不优化则毒文档几乎检不回；用 CEM 优化 trigger 后检索率接近满分。

我们把同一逻辑迁到 **Agent Skill 供应链**：

```
发布/上架 → 被发现 → 被安装 → 被加载 → 被选中 → 执行恶意规程
              ↑              ↑           ↑
           文献较强      分设定已有覆盖   文献很强
```

**工作假设**  
现有高 ASR 工作多测「已加载 / 已在库」；  
真实端到端风险还取决于 **acquisition（发现→安装）**。

---

## 2. 文献地图（三块）

按 agent 生命周期，而不是按发表年份。

### 块 I — 装载之后：执行已经很危险

**代表工作**  
Skill-Inject · Poise · MCPTox · SkillTrojan · BadSkill · SkillJect

**共同设定**  
skill / tool **已经**出现在 agent 上下文或工具集中。

**共同结论**  
- 恶意指令写在 SKILL.md / 工具描述 / 旁路脚本里，前沿 agent 仍大量执行  
- Skill-Inject：最高约 80% ASR  
- Poise：单行 setup + 旁路脚本，约 89% ASR，且用户任务仍完成  
- 后门类（SkillTrojan / BadSkill）：装入后 ASR 可达 97%+  

**对汇报的含义**  
「装进去之后会不会出事」——**问题已被充分回答：会。**  
我们不应再把主贡献写成「再做一个 80% post-load ASR」。

---

### 块 II — 已经在库/列表里：选择可以被操纵

**代表工作**  
ToolHijacker · ToolTweak · MPMA · Semantic Supply-chain (2605.11418) Selection

**共同设定**  
恶意条目 **已经在** tool library / 候选 skill 列表中。

**共同结论**  
- 工具选择常拆成 **检索 → LLM 选择**  
- 优化 name / description 后，选中率可从很低拉到 80% 量级  
- ToolTweak：同类工具竞争下约 20% → 81%  
- ToolHijacker：库内场景 ASR 常 80%+；不优化则检索都进不去  
- MPMA：MCP 上偏好操纵，直接塞词可达近 100% ASR  
- 2605.11418：功能等价的两 skill 里，改 description 可使对抗版被选中约 77.6%  

**对汇报的含义**  
「列表里抢位」在 **同类 / 候选集内** 已被打穿。  
我们 lab 的 0%–10% 来自 **跨域专一工具竞争 + 全能描述**，是更难设定，**不能**和 80% 横比。

---

### 块 III — 装载之前：发现与供应链入口

**代表工作**  
IPI · 2605.11418 Discovery · HalluSquatting · SearchGEO · Skills That Don't Exist · Do Not Mention · You Told Me · SCR

**已有证据**  
| 现象 | 证据 |
|------|------|
| 不优化则进不了 top-k | IPI Vanilla≈0%；ToolHijacker 手动注入弱 |
| 文本 trigger 可抬 registry 排名 | 2605.11418：胜率 86%，Top-10 约 80% |
| 真实市场存在恶意 skill 且被使用 | Do Not Mention：约 9.8 万 skill 中确认 157 恶意 |
| 文档/信任可诱导敏感动作 | You Told Me：README 诱导外泄约 85% |
| 信任转移可促装 | SCR TrustLift：有害安装相关 >83% |
| 显式安装请求可被劫持并完成真实 E2E | HalluSquatting：多组 fetch / invocation / RCE 为 40%–100% |
| 伪搜索证据可诱导安装命令 | SearchGEO：跨生态 Claude 0/18，GPT-5.4-mini 17/18 |
| 幻觉推荐可转成安装交付 | Skills That Don't Exist：agent 平均幻觉推荐 36.9%；另有 n=1 显式授权安装 PoC |
| skill 有生命周期与 acquisition 概念 | Skills 综述 progressive disclosure |

**L1 后的边界**  
2605.11418 仍支持 registry 生命周期在执行前研究不足；但 install 已不能再作为一个整体说“空白”：

- HalluSquatting 已完成**用户明确要求安装**时的真实 marketplace install 与调用；
- SearchGEO 已量化**安装命令输出**，但没有执行安装；
- Skills That Don't Exist 展示 recommendation 后**再次明确授权**的单例安装。

三者仍未系统报告普通任务下由 agent 自己发起的：

```
能力缺口 → 自主去搜 → 搜到 → 发出安装调用 → 实际安装 → 调用 → 载荷 → task_ok
```

**对汇报的含义**  
可站得住的空白不是泛化的 install，而是 **S0 自主 acquisition + executed install + 全链分段条件概率**。

---

## 3. 一张定位图（组会主图）

```
                    恶意内容如何进入系统？
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
     文档检索(IPI)      Skill/MCP 库内选择      Skill 市场/安装
     ─────────────      ─────────────────      ───────────────
     IPI CEM            ToolHijacker           2605.11418 Discovery
     KidnapRAG          ToolTweak              Do Not Mention(生态)
                        MPMA                   You Told Me / SCR(旁证)
                        2605.11418 Selection
                                               HalluSquatting(显式安装 E2E)
                                               SearchGEO(安装命令)
                              │
                              ▼
                    进入后是否执行恶意行为？
                    ─────────────────────
                    Skill-Inject · Poise
                    MCPTox · SkillTrojan …
                              │
                              ▼
              ┌───────────────────────────────┐
              │  本工作聚焦                     │
              │  Acquisition Barrier            │
              │  普通任务 → 自主检索 → 实装 → 调用│
              │  逐段区分 emitted / executed    │
              └───────────────────────────────┘
```

**一句话定位**  
> 我们不与 Skill-Inject 比「装完后有多危险」，  
> 也不重复 HalluSquatting 的「用户明确要求安装」。  
> 我们量化的是：用户只给普通任务时，agent 会不会因能力缺口**自行发起并执行 acquisition**，以及失败发生在哪一段。

---

## 4. 与本 lab 证据如何咬合

| 我们的结果 | 文献怎么读 |
|------------|------------|
| 预装 + 跨域：0% / 10% / 5% | 支持 **selection barrier 在难设定下成立**；不等于「description 永远无效」 |
| 明确 query 从不中招 | 专一性偏好；与 ToolTweak「同类可操纵」可并存 |
| A2：检索后生成 install tool call，但未执行 | 当前是**编排截断**：三轮工具预算已耗尽；只能证明检索与 emitted intent，不能证明模型拒绝安装 |
| 下一步打 FE / 文档 / TrustLift | 分别对应 MSB、You Told Me、SCR |

**A2 方法学勘误**  
现有 raw reply 末尾已出现 `install_skill` 调用；框架未进入下一轮解析/执行。重跑前必须把 `install_call_emitted`、`install_call_parsed`、`install_executed` 与 `installed_on_disk` 分开。否则会把 orchestration failure 错判成 behavioral barrier。

---

## 5. Related Work 口述结构（约 2 分钟）

**第一段 — 装载后已充分危险**  
Skill 与 MCP 投毒在 post-load 设定下 ASR 很高（Skill-Inject、Poise、MCPTox）。说明第三方 skill 是真实供应链面。

**第二段 — 进入上下文之前存在 barrier**  
IPI 证明检索是 IPI 的真瓶颈。Tool 选择工作进一步表明：库内文档可被优化到近满分检索与高选中率。2605.11418 把 SKILL.md 本身变成 registry 攻击面。

**第三段 — 空白与贡献**  
已有近邻工作分别覆盖显式安装请求的真实 E2E（HalluSquatting）和安装命令背书（SearchGEO），但尚未把普通任务触发的 agent 自主 acquisition 做成完整基准。  
我们在具备 search/install 的 agent 上，用分指标量化 **缺口—检索—安装调用—实际安装—调用—载荷—任务完成**，并区分模型决策与编排器执行。  
Skill Acquisition Barrier 的贡献应落在 **S0 自主性、executed install 与逐段归因**，而不是笼统宣称第一次研究安装。

---

## 6. 审稿人可能问什么（预备答案）

| 问题 | 答法 |
|------|------|
| 和 Skill-Inject 有何不同？ | 他们默认已加载；我们测进入加载之前。 |
| description 优化不是已经有了吗？ | 有，但是 **库内/同类**。我们还包含 **install 决策** 与 **跨域竞争**。 |
| 2605.11418 是否已做完？ | 他们做 registry 排名与二选一偏好；我们做 **agent 运行时 acquisition 全链轨迹与条件指标**。 |
| HalluSquatting 不是已完整安装并调用了吗？ | 是，但用户明确要求 `install X`；我们的主条件是用户只给普通任务，agent 自行识别能力缺口并发起 acquisition。显式安装应作为上界对照。 |
| SearchGEO 不是已有 install ASR 吗？ | 它的终点是精确安装命令输出，未执行工具调用。我们把 emitted、parsed、executed、落盘和后续调用分别计量。 |
| 为什么早期只有 5%？ | 那是预装跨域 selection 下界，用来证明 barrier，不是最终 E2E ASR。 |

---

## 7. 结论（汇报收尾）

1. **Post-load 执行**：文献充分 → 引用即可。  
2. **库内/同类选择**：文献充分 → 引用即可。  
3. **显式 install / 命令输出**：已有直接结果 → 必须作为强邻居与对照。  
4. **普通任务触发的自主 acquisition**：尚缺 executed、分段 E2E → **本工作切口**。  
5. 方法菜单已齐：假错误、文档权威、信任转移、多源伪证据、检索 trigger、装后专一伪装、旁路载荷。  
6. 当前实验状态：selection barrier 已见；A2 是 **检索通、install call 已发出、执行被编排器截断**，尚不能证明行为上的安装门。

---

## 附录：最少引用集（写进 PPT 右下角）

```
叙事    IPI (2601.07072)
装后    Skill-Inject (2602.20156) · Poise (2606.07943)
库内选  ToolHijacker (2504.19793) · ToolTweak (2510.02554)
市场    2605.11418 · Do Not Mention (2602.06547)
安装直接 HalluSquatting (2607.07433) · SearchGEO (2606.16821)
推荐交付 Skills That Don't Exist (2607.12340)
安装旁证 You Told Me (2603.11862) · SCR (2606.15242)
术语    Skills Survey (2602.12430)
菜单    MSB (2510.15994) · MPMA (2505.11154)
```

详细条目表见 `14_LIT_SUMMARY_TABLE.md`（查 arXiv 用）。  
阅读过程见 `13_LIT_READING_JOURNEY.md`。
