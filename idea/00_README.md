# 📋 IDEA 文件夹导读（从这里开始读）

> **目的**：本文件夹记录了从阅读 IPI 论文到搭建 skill injection 实验的全部思考过程、
> 实验发现、未解决的难题和下一步方向。一个新的 agent 读完这些文件，
> 就能完全接手这项研究工作。
>
> **最后更新**：2026-07-26
> **研究状态**：L40 acquisition development pilot 已跑通；Qwen3-32B-AWQ 在当前
> auto-acquire policy 的 10 个 soft-gap 普通任务上得到 7/10 完整 E2E，A0 预装单域控制
> 目标调用为 0/5。该数字不是论文 ASR；policy × hard-gap v1 正作为 **150-trial
> 管线压测**运行，因果修正版已冻结为 `policy_hardgap_causal_v2`
> （背景见 29，v1 实现见 30，修正版预注册见 31）。
> 导师汇报首选 **24 PDF**；**组会首选 27**（Do Not Mention 主讲 + SCR/HalluSquatting 补充；配套通俗精读见 **28**）；
> 25 为历史双主讲版（IPI + Do Not Mention）；私聊沟通稿见 **26**；完整文献过程见 **13/21**。

---

## 📁 文件结构（按阅读顺序）

| 序号 | 文件 | 内容 | 优先级 |
|------|------|------|--------|
| 1 | **00_README.md** | 本文件，全局导览 | ⭐ 必读 |
| 2 | **01_ORIGIN.md** | 这项研究怎么来的：从 IPI 论文到 skill injection 的思考链 | ⭐ 必读 |
| 3 | **02_EXPERIMENT_RESULTS.md** | 已完成的三阶段实验结果和核心发现 | ⭐ 必读 |
| 4 | **03_CURRENT_BOTTLENECK.md** | 当前卡在哪：为什么优化不生效 + 已排除的原因 | ⭐ 必读 |
| 5 | **04_NEXT_DIRECTIONS.md** | 下一步可以尝试的方向（含文献线索） | ⭐ 必读 |
| 6 | **09_ACQUISITION_PIPELINE.md** | **四阶段 acquisition 全景图、方案菜单、实验矩阵、选型决策** | ⭐ 规划主文档 |
| 6b | **10_LOCAL_BACKEND_PLAN.md** | **Hyperstack 本地 70B 后端（顶会英文、全量替换 API）** | ⭐ 部署必读 |
| 7 | **05_CODE_MAP.md** | 代码结构和各文件作用，方便接手代码 | 按需读 |
| 8 | **06_KEY_CONCEPTS.md** | 关键概念对照表（IPI 论文术语 → skill injection 对应物） | 按需读 |
| 9 | **07_OPEN_QUESTIONS.md** | 所有未解决的开放问题清单 | 头脑风暴时读 |
| 10 | **08_DATA_SNAPSHOT.md** | 实验数据文本快照 | 按需读 |
| 11 | **10_PAPERS_FOR_FEASIBILITY.md** | acquisition 可行性相关论文清单与阅读顺序 | ⭐ 文献推进时读 |
| 12 | **11_MENTOR_ONEPAGER.md** | 早期导师一页纸（历史快照） | 追溯时用 |
| 13 | **12_PAPER_VALIDATION.md** | 论文逐阶段验证攻击可行性（含 2605.11418） | ⭐ 验证攻击时读 |
| 14 | **13_LIT_READING_JOURNEY.md** | **文献阅读过程：从 IPI 到 Acquisition idea 的演变** | ⭐ 复盘/开题叙事 |
| 15 | **14_LIT_SUMMARY_TABLE.md** | 文献短表（查 arXiv） | 查编号时用 |
| 16 | **15_LIT_ACADEMIC_BRIEF.md** | **学术汇报体文献综述简报（推荐口述/组会）** | ⭐ 汇报首选 |
| 17 | **16_HANDOFF_TO_LIT_AGENT.md** | **移交给文献智能体的任务交接包** | ⭐ 交接时必读 |
| 18 | **17_RELATED_WORK_VISUAL_REVIEW.md** | 导师版可视化综述：生命周期图、威胁模型矩阵、指标漏斗 | 历史综述入口 |
| 19 | **18_RELATED_WORK_MENTOR_REVIEW.pdf** | 完整导师版 related-work PDF | 查完整文献时用 |
| 20 | **19_RELATED_WORK_MENTOR_COMPACT.pdf** | 压缩版文献综述 PDF | 历史汇报稿 |
| 21 | **20_RELATED_WORK_AND_RESEARCH_IDEA.pdf** | 文献与研究想法整合版 | 历史汇报稿 |
| 22 | **21_RELATED_WORK_RESEARCH_POSITIONING.pdf** | 31 篇重点工作的定位审计 | ⭐ 文献附录 |
| 23 | **22_PILOT_AND_HYPOTHESIS_SELECTION_PLAN.md** | Instrumentation、pilot、Go/No-Go 与六周计划 | ⭐ 实验规划 |
| 24 | **23_NORTH_STAR_PITCH.md** | 北极星问题；已按 SCR-TrustLift 原文修正过度主张 | ⭐ 研究定位 |
| 25 | **24_MENTOR_LIT_SUMMARY.pdf** | **4 页可直接发导师的文献与进展汇报** | ⭐ 当前汇报首选 |
| 26 | **25_GROUP_MEETING_PAPER_TALK.md** | IPI + Do Not Mention 组会选篇与逐页提纲 | ⭐ 组会准备 |
| 27 | **26_MENTOR_COMMUNICATION.md** | 私聊消息、90 秒开场、追问备答与口径红线 | ⭐ 私聊准备 |
| 28 | **27_GROUP_MEETING_DO_NOT_MENTION.md** | 组会：Do Not Mention 主讲 + SCR/HalluSquatting 补充；数字已回原文核对 | ⭐ 组会准备 |
| 29 | **28_SCR_HALLU_PRESENTATION_CONTENT.md** | SCR/HalluSquatting 通俗精读讲稿（给外行听懂）；做 slides 前的内容底稿 | ⭐ 组会准备 |
| 30 | **29_L40_DEVELOPMENT_PILOT.md** | **L40 环境、protocol gate、A0/A2 首轮结果、口径红线与 policy × hard-gap 决策实验** | ⭐ 当前实验状态 |
| 31 | **30_POLICY_HARDGAP_IMPLEMENTATION.md** | **P0/P1/P2 执行层策略、PDF/ICS/QR 真硬缺口、验收与 v1 管线压测** | ⭐ 当前实验状态 |
| 32 | **31_CORRECTED_CAUSAL_PREREGISTRATION.md** | **修正版 P0/P1 因果对照、30 个独立 hard specs、三类 E2E 与 P2-approved 预注册** | ⭐ v2 必读 |
| 33 | **32_V1_PIPELINE_STRESS_RESULTS.md** | **v1 150/150 结果、P2 gate 事件级验收、错误包名/重复调用与不可说边界** | ⭐ 最新结果 |
| 34 | **33_CAUSAL_V2_MAIN_RESULTS.md** | **v2 正式 primary：P0 5/30 → P1 24/30；三类 hard family 全部同向；P2 0/30** | ⭐ 正式结果 |
| 35 | **34_PAPER_DRAFT_v0.md** | **论文 v0：scaffold authorization 主线、真实结果、Defense 与待补实验** | ⭐ 论文草稿 |
| 36 | **35_GENERALIZATION_PREREGISTRATION.md** | **跨模型/跨 scaffold 复现判据、tool-probe 验收门与 provenance** | ⭐ 下一阶段预注册 |
| 37 | **36_APPROVAL_GATE_DEFENSE_RESULTS.md** | **P2 denied/approved-benign/approved-malicious 三臂：gating ≠ vetting** | ⭐ 防御结果 |
| 38 | **37_FIGURE_SPECS.md** | **论文三张核心图的 panel、数据、caption 与渲染规格** | ⭐ 作图规格 |
| 39 | **38_TRACK_A_EXECUTION_PLAN.md** | **最小可辩护 generalization：M2×S1、M1×S2、M3×S1 的执行顺序与红线** | ⭐ 当前执行计划 |
| 40 | **slides/** | 组会成品：PPT + 放映用预览 PDF + 逐页演讲稿（≤30min）+ 生成脚本；15 张图（4 截原文 / 11 自绘） | ⭐ 组会直接用 |

---

## 🎯 一句话概括当前状态

> **在单模型、单框架、20 个任务的预装实验中观察到 selection friction：
> 三档结果为 0/20 → 2/20 → 1/20；中招集中在模糊/跨域任务。
> 这是研究演化的先导证据，不是跨模型普适结论。**
>
> **规划升级（见 `09_ACQUISITION_PIPELINE.md`）**：把问题从「预装后抢 selection」
> 扩展为四阶段 acquisition 管线——缺口 → 检索 → 安装 → 调用+旁路载荷；
> 最新原文复核表明 SCR 已覆盖 simulated harmful install、HalluSquatting 已覆盖显式安装下真实 E2E，
> 因此当前重点不是“首次 install”，而是 ordinary-task 同轨迹系统测量。**
>
> **2026-07-26 L40 开发性结果（见 `29_L40_DEVELOPMENT_PILOT.md`）**：
> 当前 auto-acquire policy 下 A2 soft-gap 完整 E2E 为 7/10；进入 search 的 7 条全部走到底，
> 主分叉在 task→search。下一步必须用 P0/P1/P2 policy 和真实 hard-gap artifact verifier
> 判断这是任务诱发风险、scaffold 授权风险，还是 soft-gap 模板效应。
>
> **2026-07-26 最新运行状态（见 `31` / `32`）**：v1 管线压测 150/150、0 运行错误，
> 但因三个设计混淆不作因果解释；修正版 v2 已完成 15/15 模型验收，并已在 L40
> 完成 150-trial main causal run。冻结 primary 为 P0 `5/30` → P1 `24/30`
> （+63.3pp；19 对仅 P1 成功、0 对反向），PDF/ICS/QR 三个 family 全部同向；
> P2 denied 为 0/30。P2-approved benign 已完成：
> `functional_e2e=25/30, payload=0/30`；approved+malicious 也保持
> `functional_e2e=25/30`，但 `payload=25/30`，实证边界为 gating ≠ vetting。

---

## ⚠️ 重要约束（接手前必须知道）

1. **所有实验数据都是合成假数据**，外泄只发往本机 127.0.0.1，纯防御性安全研究
2. **LLM API**：deepseek-chat，通过上海交大模型平台（models.sjtu.edu.cn）
3. **API 偶尔会限流/超时**，run_optimize.py 需要后台运行（可能跑 15-20 分钟）
4. **框架限制**：hello-agents 的 tool calling 用的是自定义 `[TOOL_CALL:name:args]` 格式，
   不是 OpenAI 原生 function calling，LLM 有时不按格式输出
5. **导师要求**：从简到难、逐步推进，先跑实验验证假设，再做 summary 汇报
