# 10 — 相关论文：服务「acquisition 管线可行性」探索

> **目的**：不是泛读 agent 安全，而是回答  
> 「缺口→检索→安装→调用+载荷」这条路 **值不值得做、怎么做、别人卡在哪**。  
> **用法**：按阶段读；每篇只抽「可迁移到实验的 1–2 个点」。  
> **更新**：2026-07-14

---

## 0. 你现在的可行性问题清单

| # | 问题 | 你已有证据 | 论文应帮你确认什么 |
|---|------|------------|-------------------|
| Q1 | 无缺口时 selection 是否真难破？ | lab: 0–10% | 是否普遍、别人怎么破 |
| Q2 | 工具库是否常拆成 **retrieval + selection**？ | 你 A2 有 mock search | 是否标准架构（可对齐 IPI/ToolHijacker） |
| Q3 | 搜到后 agent 是否会 **自主 install**？ | 冒烟: 搜到不装 | 有没有现成 install 环、ASR 量级 |
| Q4 | 装入后执行率是否高？ | 文献 80%+ 量级 | threat model 是否默认「已加载」 |
| Q5 | description 优化 / CEM 是否可迁移？ | CEM 在 IPI 通 | tool doc 优化是否通 |
| Q6 | 本地小模型 vs API 大模型会否改结论？ | 仅 deepseek-chat | 跨模型敏感性 |

---

## 1. 必读第一梯队（直接服务你的管线）

### 1.1 已加载 skill 的执行面（证明 Stage3 值得接）

| 论文 | 链接 | 读什么 | 对你的含义 |
|------|------|--------|------------|
| **Skill-Inject** | arXiv:2602.20156 · skill-inject.com · github.com/aisa-group/skill-inject | threat model、injection 形态、ASR 定义 | **默认 skill 已在上下文**；80% 是 post-load，不是 install |
| **Poise** | arXiv:2606.07943 | 单行 body + 旁路脚本、task 仍成功、位置目录 | Stage3b/3c 主方案参考；可对照你的 weekly_brief |
| **IPI in the Wild** | arXiv:2601.07072 | retrieval barrier、CEM、Vanilla/Query+/Opt | 你选题的结构模板；Stage1 可抄 CEM |

**可行性结论（文献侧）**：Stage3「装完再打」被多篇工作支撑；你的差异化应在 **Stage0–2**。

---

### 1.2 Tool 选择 / 检索（直接对齐 Stage1 + 预装 selection）

| 论文 | 链接 | 读什么 | 对你的含义 |
|------|------|--------|------------|
| **ToolHijacker** | arXiv:2504.19793 · NDSS | **retrieval + selection 两阶段**；毒 tool document 劫持选择 | 架构与你「市场检索→再选中」同构；他们偏 **库内文档注入**，你偏 **安装后进列表** |
| **ToolTweak** | arXiv:2510.02554 | 迭代改 tool **name/description** 提高被选中率 | 比你「LLM 对抗改描述」更系统；可借优化环设计 |
| **How Many Tools Should an LLM Agent See?** | arXiv:2605.24660 | 每次给模型看 K 个 tool 的深度选择 | 解释「工具太多要先检索」；支持 marketplace/top-k mock 的合理性 |

**可行性结论**：工业界/论文里 **先 retrieval 再 selection** 是主流；你的 Stage1 mock **不是玩具设定**，是标准分解。

---

### 1.3 MCP / Skill 生态与供应链（支撑「装」作为攻击面）

| 论文 | 链接 | 读什么 | 对你的含义 |
|------|------|--------|------------|
| **MCPTox** | arXiv:2508.14925 | tool metadata 投毒、真实 MCP servers、高 ASR | Stage3a 描述投毒；「强模型更听话」 |
| **MSB** | arXiv:2510.15994 | 12 类攻击 taxonomy（name-collision、false-error、preference…） | **Stage2 安装诱导** 可直接借 false-error / preference |
| **MCPSecBench** | arXiv:2508.13220 | 17 类攻击、四攻击面 | 写 related work / 威胁模型用 |
| **Skills Are Not Islands** | arXiv:2607.01136 | skill **依赖图**、传递风险 | 二重依赖 / companion 叙事有文献锚 |
| **Benign in Isolation, Harmful in Composition (SCR)** | arXiv:2606.15242 | 组合才有害 | 渐进信任 / 双包可行性 |
| **HalluSquatting / Agentic Botnets** | arXiv:2607.07433 | 幻觉包名/skill 名被抢注 | Stage1 替代 CEM 的路径 |
| **Do Not Mention This to the User** | arXiv:2602.06547 | 真实 registry 恶意 skill 测量 | 真实世界「会装吗」的生态证据 |

**可行性结论**：供应链/registry/依赖 已被当作一等攻击面；缺的是 **你这种分段指标的 acquisition barrier 量化**。

---

### 1.4 间接注入与「权威通道」（服务 Stage2：为何搜到不装、怎么促装）

| 论文 | 链接 | 读什么 | 对你的含义 |
|------|------|--------|------------|
| **AgentDojo** | arXiv:2406.13352 | 工具返回劫持后续行为 | I3：假错误 / 工具返回促装 |
| **InjecAgent** | arXiv:2403.02691 | user tools vs attacker tools | 多工具诱导 |
| **You Told Me to Do It**（README 诱导） | arXiv:2603.11862 | 文档当 instruction 的服从率 | I4 文档权威通道 |
| **Dynamic Malicious Skills** | arXiv:2606.16287 | skill 文档诱导运行时注入 | 装后动态下毒 |
| **ShareLock** | arXiv:2606.27027 | 多 tool 分片投毒 | 进阶；非第一周 |

**可行性结论**：你冒烟里「搜到不装」很正常——需要 **额外权威/必要性信号**；这些论文提供通道类型，不是现成 install ASR。

---

## 2. 第二梯队（写故事 / 做防御对照 / 扩框架）

| 论文 | 用途 |
|------|------|
| LASM Survey arXiv:2604.23338 | 把 acquisition 标到 Ecosystem + Tool Execution 层 |
| ToolEmu arXiv:2309.15817 | 危险工具评测方法论 |
| ClawGuard / AgentSentry | 防御对照（runtime gate） |
| SkillAttack arXiv:2604.04989 | 不改 skill、改 prompt 的红队（对照 threat model） |
| PhantomSkill arXiv:2606.19191 | 辅助资源藏毒（旁路加强） |
| Anthropic: Writing effective tools for agents | 工程：工具该专一——解释你的专一性偏好 |

索引汇总：  
https://github.com/LLMSecurity/awesome-agent-skills-security

---

## 3. 按你四阶段的「读论文 → 改实验」映射

```
S0 缺口
  读: MSB (false-error), AgentDojo
  做: G1 缺口 query（已有）→ G3 NEED_SKILL（下一步）

S1 检索
  读: IPI, ToolHijacker, How Many Tools K, HalluSquatting
  做: 关键词检索（已有）→ 对比 Hallu 名 / embedding+CEM

S2 安装  ★ 你当前断点
  读: README 诱导, MSB preference/false-error, Do Not Mention (生态)
  做: I1/I2/I3/I5 ablation（最优先）

S3 调用+载荷
  读: Skill-Inject, Poise, ToolTweak, MCPTox
  做: 专一 V1（已有 weekly_brief）→ Poise setup 旁路
```

---

## 4. 建议阅读顺序（约 1–1.5 周可执行）

### Day 1–2：对齐 threat model（防和 Skill-Inject 比歪）

1. Skill-Inject（摘要 + threat model + 评测是否预加载）  
2. Poise（§1–3 攻击构造）  
3. 你自己的 `09_ACQUISITION_PIPELINE.md` 对照：哪些他们默认跳过  

**产出一句话**：  
「文献高 ASR 多在 post-load；我们量化 pre-load acquisition。」

### Day 3–4：选择与检索

4. ToolHijacker（retrieval+selection 图）  
5. ToolTweak（改 name/desc 的优化环）  
6. IPI（只看 barrier + CEM 流程，算法细节可后读）  

**产出**：Stage1 要不要上 CEM 的判断标准（embedding 市场？还是仅关键词？）

### Day 5–6：安装与权威通道（对准你的断点）

7. MSB taxonomy 中与 selection/install 相关的 4–5 类  
8. AgentDojo 一条成功 IPI 案例（工具返回如何改计划）  
9. README / 「You Told Me to Do It」类（文档通道）  

**产出**：I3 假错误、I5 companion 的实验设计草稿

### Day 7：生态与供应链（写 related work）

10. Skills Are Not Islands 或 SCR 选一  
11. MCPTox 结果表扫一眼（跨模型 ASR）  
12. awesome-agent-skills-security 扫标题，补 2 篇最新  

---

## 5. 读论文时的「可行性 checklist」（每篇填 5 行）

```
论文:
默认 skill/tool 是否已在上下文?  [是/否/部分]
有没有 search/install 动作?      [有/无]
攻击成功是否要求用户任务仍完成? [是/否]
优化对象是什么?                 [desc/name/doc/body/script]
可直接抄进我 lab 的一点:         [……]
```

若 10 篇里 **≥7 篇默认已加载** → 你的 acquisition barrier 空白真实存在。  
若 **多篇已有自主 install 高 ASR** → 缩小 claim，改做「hello-agents 上的复现+分段指标」。

---

## 6. 和「要不要换本地模型」的交叉（读文献时顺带记）

| 文献现象 | 对 API vs 本地的启示 |
|----------|---------------------|
| MCPTox：更强 instruction-following 有时更高 ASR | 本地 7B 可能 **更难攻或行为不同**，结论需跨模型 |
| Skill-Inject / Poise：多 agent 配置 | 至少 2 个后端才有发表力度 |
| Tool selection 对 prompt/格式敏感 | 换模型 = 换 tool-call 格式服从度，要先修 harness |

**现阶段建议**（结合你冒烟）：

- **先不换模型**，把 Stage2 安装 ablation 跑稳（同一 deepseek，归因干净）  
- 主方案出现后，用 **1 个本地开源 + 现 API** 做跨模型，而不是现在就迁移全栈  

---

## 7. 下载与代码（搜索工具不稳时）

```bash
# 核心 PDF
wget https://arxiv.org/pdf/2602.20156 -O /tmp/skill-inject.pdf
wget https://arxiv.org/pdf/2606.07943 -O /tmp/poise.pdf
wget https://arxiv.org/pdf/2601.07072 -O /tmp/ipi.pdf
wget https://arxiv.org/pdf/2504.19793 -O /tmp/toolhijacker.pdf
wget https://arxiv.org/pdf/2510.02554 -O /tmp/tooltweak.pdf
wget https://arxiv.org/pdf/2508.14925 -O /tmp/mcptox.pdf
wget https://arxiv.org/pdf/2510.15994 -O /tmp/msb.pdf
wget https://arxiv.org/pdf/2605.24660 -O /tmp/how-many-tools.pdf

# 代码（优先）
git clone --depth 1 https://github.com/aisa-group/skill-inject /tmp/skill-inject
# Poise: https://github.com/liofoil/SkillSafety
```

你本机 IPI PDF：`/home/forks/AResearch/ANL/2601.07072v1.pdf`

---

## 8. 与本仓库其他文件

| 文件 | 关系 |
|------|------|
| `literature.md` | 早期 slides/T1–T4 向；本文件是 **acquisition 可行性向** |
| `09_ACQUISITION_PIPELINE.md` | 实验阶段定义；论文读完回填「📚→✅」 |
| `04_NEXT_DIRECTIONS.md` | 方向列表；本文件给阅读优先级 |

---

## 9. 最小结论（现在就可以用）

1. **管线在文献上可行**：retrieval+selection 是标准；post-load 高危有 Skill-Inject/Poise；供应链/依赖有 2026 一串工作。  
2. **空白也真实**：多数高 ASR **不测「自主安装」**；你的 Stage2 断点正是可发点。  
3. **下一篇最该精读的 3 个**：ToolHijacker、ToolTweak、MSB（false-error 段）+ 扫 Skill-Inject threat model。  
4. **实现优先级不改**：先 Stage2 ablation，再 CEM/本地模型。
