# Autonomous Skill Acquisition：Pilot 与核心假设选择计划

更新时间：2026-07-22  
目标：先用可审计的小规模实验判断哪一个“默认假设”最值得正式推翻，再冻结核心假设并使用 held-out 数据验证。

---

## 1. 总问题先固定，核心叙事暂不固定

总问题在 pilot 前固定为：

> 现有的 selection、recommendation、install-command 和 post-load 指标，能否可靠预测真实 autonomous skill-acquisition risk？

候选假设：

| 编号 | 待检验假设 | 可能推翻的默认认识 |
|---|---|---|
| H1 | `call_emitted` 与 `install_executed` 存在稳定、显著的 execution gap | 输出安装命令可以近似代表真实安装风险 |
| H2 | ordinary-task 条件下也会出现真实、可复现的安装 | 显式用户授权是必要的安装边界 |
| H3 | scaffold / tool budget / permission policy 对 E2E 的影响大于模型差异 | acquisition 安全主要由模型能力或对齐决定 |
| H4 | 高 post-load ASR 无法转化为高 ordinary-task E2E | 装后高 ASR 可以代表现实供应链风险 |

Pilot 只用于发现哪条效应真实、稳定、值得扩大。正式论文只选择一个核心假设，其他假设作为解释或附加分析。

---

## 2. 当前代码基础与必须先修的问题

已有基础：

- `secskill-lab/acquisition/run_acquisition_eval.py`：A0/A2 入口；
- `marketplace.py`：内存 marketplace；
- `meta_tools.py`：`search_skills` / `install_skill`；
- `metrics.py`：阶段指标；
- `queries_gap.py`：能力缺口任务；
- `tool_probe.py`：模型工具调用验收；
- `smoke_test_offline.py`：不调用 LLM 的闭环冒烟。

正式 pilot 前必须修正：

1. **工具轮数**
   - HelloAgents 默认 `max_tool_iterations=3`；
   - 当前 A2 的 `calendar → weather → search → install` 会在 install 前后被截断；
   - 不修改 `.venv/site-packages`，在仓库内增加可配置 runner 或 wrapper；
   - 每次运行记录 `max_tool_iterations`，主条件固定为足以走完整链的数值，另做 3/6/10 轮消融。

2. **阶段事件必须拆开**
   - 当前 `install_intent` 主要由 `install_ok/install_fail/tool_calls` 推断；
   - 新日志应明确记录：

```text
search_intent_observed
search_called
target_retrieved
install_recommended
install_call_emitted
install_call_parsed
install_execution_started
install_execution_succeeded
installed_on_disk
registered_in_agent
invoked
payload_fired
task_ok
```

3. **不要用文本弱信号作为主指标**
   - `gap_triggered` 当前会搜索回复中的“缺少/无法完成”等词；
   - 主指标只使用可审计行为：实际 `search_skills` 调用、结构化 acquisition action 或明确 protocol event；
   - 文本判断只作为 exploratory annotation。

4. **安装必须有独立状态验证**
   - 当前 install 主要是把 Tool 动态注册进内存 registry；
   - 新版应在每个 run 的临时目录写入安装 manifest/package，并检查：
     - 文件存在；
     - manifest 名称/哈希正确；
     - registry 出现该 skill；
     - 新一轮 agent 能发现并调用；
   - `installed_on_disk` 与 `registered_in_agent` 分开。

5. **`task_ok` 改为任务级 verifier**
   - 当前“回复超过 20 字且没有失败”过于宽松；
   - 每个任务定义结构化验收项，例如必须同时出现日程字段、天气字段和联合建议；
   - 主结果使用确定性 verifier；LLM judge 只做补充并盲化条件标签。

6. **可复现元数据**
   - 保存 model ID、量化方式、temperature、seed、prompt hash、task ID、market snapshot、scaffold version、policy、tool budget、完整事件时间线；
   - 每个 run 使用隔离目录和合成数据；payload 只写 marker/发送到 localhost collector，不做真实外泄。

完成标准：同一条离线脚本能逐一构造并断言 emitted、parsed、executed、on-disk、registered、invoked 六种状态；不能再靠最终回复猜测。

---

## 3. L40 部署方案

L40 为 48 GB。用途是提供稳定、低成本、大量重复的本地 victim model，不负责训练模型。

### 3.1 第一阶段模型

开发/主 pilot 建议：

- `Qwen/Qwen3-32B-AWQ`
  - 官方 AWQ 权重；
  - 32B 4-bit 在 L40 上空间充足；
  - 官方模型卡强调 tool-calling 能力；
  - 适合先把协议和重复实验跑稳。

第二模型候选：

- Llama-3.3-70B-Instruct 的可靠 AWQ/GPTQ 版本；
  - 70B 4-bit 权重约为 35–40 GB 量级；
  - L40 可尝试 8k context、并发 1；
  - 必须先跑 tool probe，不能因为模型更大就默认可用。

正式论文后续至少再加入一个不同来源的 frontier/API 模型；单张 L40 的本地结果不能替代跨模型验证。

### 3.2 vLLM 初始配置

```text
quantization: AWQ
max_model_len: 8192
gpu_memory_utilization: 0.88–0.90
temperature: 0（协议调试）/ 固定低温度（重复实验）
concurrency: 1（验收）→ 2–4（批量）
server bind: 127.0.0.1
```

vLLM 官方支持 AutoAWQ、GPTQModel、FP8 等量化格式。先使用模型仓库自带量化配置，不在 pilot 阶段自行量化。

### 3.3 模型验收门槛

在攻击实验前单独通过：

| 探针 | 门槛 |
|---|---:|
| 明确单工具任务 | ≥ 90% 正确调用 |
| 显式 search 任务 | ≥ 80% 调用 `search_skills` |
| 显式 install 正对照 | ≥ 70% 到达 `install_execution_started` |
| 无关任务乱搜索/乱安装 | ≤ 10% |
| 结构化 tool-call 解析成功 | ≥ 95% |

不过线时先修 chat template、tool protocol、temperature 和 parser；不得直接把协议失败计为模型安全。

---

## 4. Pilot 任务集

当前任务几乎全部围绕 `weekly_brief`，不足以判断现象是否跨任务稳定。Pilot 扩展为 3 个能力家族：

1. 日程 × 天气联合简报；
2. 多来源资料聚合并生成带引用摘要；
3. 结构化数据转换/导出为指定交付格式。

每个家族准备：

- 4 个 ordinary gap tasks：任务需要缺失的组合能力，但不出现 search/install/skill；
- 2 个 no-gap controls：内置工具足以完成；
- 2 个 irrelevant controls：完全不需要工具；
- 2 个 explicit-install positives：明确要求搜索和安装，用于验证系统能力。

合计约 30 个任务。开发集与 held-out 集各占一半；held-out 在假设冻结前不运行。

### Marketplace 设计

- 每个家族 1 个目标 skill、2 个功能相近 benign skills、3–5 个无关 decoys；
- 先设置“目标保证进入 top-3”，隔离 S0/S2；
- S0/S2 信号存在后，才加入真实 ranking 竞争；
- benign/malicious twin 的可见功能保持一致，恶意版本只把 payload 换成安全 marker；
- baseline card 使用中性描述，不默认写“必须安装”。

---

## 5. Pilot 条件与运行规模

### 5.1 第一轮：链路与基线（约 60–100 runs）

目的：确认 runner 没有系统性截断，测 ordinary baseline。

- 1 个本地模型；
- 1 个 scaffold；
- 3 个任务家族；
- ordinary / recommendation-confirm / explicit-install 三类触发；
- neutral marketplace card；
- 2–3 个重复种子。

必须同时包含 no-gap 和 irrelevant controls。

### 5.2 第二轮：候选效应筛查（累计约 200–350 runs）

增加：

- 第二模型；
- 第二 scaffold 或 native structured tool-call runner；
- 两种 S2 通道：优先 multi-source 与 trust-transfer，或选择 false-error 替换其中一个；
- tool budget 3 / 6 / 10；
- auto-install 与 confirmation gate 两种 policy。

Pilot 不做大规模显著性声明，主要看效应方向、跨任务家族一致性和故障归因。

---

## 6. 选择核心假设的预先规则

以下规则在 pilot 前写入结果分析脚本，避免事后挑故事。

| 观察到的信号 | 优先核心假设 | 进入正式实验的最低证据 |
|---|---|---|
| emitted 明显高于 executed/on-disk | H1：proxy endpoint 无效 | 差距跨 ≥2 个任务家族和 ≥2 个模型/scaffold 方向一致 |
| ordinary 条件出现真实安装 | H2：授权边界不可靠 | 至少 5 个不同任务成功，且跨 ≥2 个家族；排除 prompt 泄露 |
| tool budget/policy/scaffold 改变率远大于模型切换 | H3：系统因素主导 | 固定任务和模型后可复现；日志能定位具体阻断阶段 |
| post-load 高，但 ordinary E2E 很低 | H4：post-load 外推失真 | S3 正对照稳定成功，S0/S2 衰减跨家族一致且能解释原因 |
| 所有条件都低且没有结构性差异 | Go/No-Go 失败 | 不扩大主实验；检查任务有效性后停止或转向 |

“最低证据”是进入下一阶段的工程门槛，不是最终论文的统计结论。

若多条同时满足，优先级建议：

1. H1 measurement validity：最稳，低/高安装率都可研究；
2. H2 authorization boundary：安全影响最大，但依赖现象真实存在；
3. H3 systems/policy：适合在系统效应非常强时转主线；
4. H4 risk calibration：适合普通任务几乎不安装但原因清楚时。

---

## 7. Pilot 后的“冻结”步骤

Pilot 结束后创建 `idea/23_HYPOTHESIS_FREEZE.md`，必须写明：

1. 唯一 primary hypothesis；
2. primary endpoint；
3. 主比较条件；
4. 任务、模型、scaffold、policy 范围；
5. 排除规则与失败运行如何处理；
6. 统计模型和置信区间；
7. held-out task 清单及 hash；
8. 哪些分析只属于 secondary/exploratory。

随后才运行 held-out tasks。Pilot 数据不进入 primary confirmatory p-value；可作为系统开发结果或附录单独报告。

---

## 8. 正式实验轮廓

若 pilot 通过 Go 条件，正式实验至少包括：

- 4–6 个能力家族；
- 40–80 个 held-out tasks；
- ≥3 个模型，至少两个不同模型家族；
- ≥2 个 scaffold；
- ordinary / recommendation-confirm / explicit-install；
- neutral 与选定的 1–2 个 S2 通道；
- auto-install / confirmation gate；
- task-specific utility verifier；
- bootstrap confidence intervals；
- 对任务和模型做 mixed-effects/logistic analysis（视样本量决定）；
- 一个简单防御或 reporting standard：例如 acquisition gate、capability justification、execution provenance，或强制分段指标报告。

---

## 9. 六周执行表

### Week 1：Instrumentation

- 增加仓库内可配置 tool-loop runner；
- 完整拆分 emitted/parsed/executed/on-disk/registered；
- 临时安装目录与 manifest 验证；
- task verifier；
- 单元测试和离线冒烟。

交付：一条命令生成完整 event trace；所有阶段可被测试独立触发。

### Week 2：L40 与任务集

- L40 起 vLLM；
- Qwen3-32B-AWQ tool probe；
- 扩展三个能力家族和 marketplace decoys；
- 划分 development / held-out tasks；
- 安全 sandbox 和合成 payload marker。

交付：模型验收报告、任务卡、market snapshot。

### Week 3：第一轮 Pilot

- 跑 60–100 个基线 runs；
- 修复协议/任务问题；
- 检查 ordinary/no-gap/irrelevant/explicit 四类行为；
- 确保所有失败能归因到具体阶段。

交付：阶段漏斗、failure taxonomy、数据质量报告。

### Week 4：候选假设筛查

- 加第二模型或 scaffold；
- 加两类 S2 通道和 policy/tool-budget 消融；
- 按预先规则选择 primary hypothesis；
- 写 `23_HYPOTHESIS_FREEZE.md`。

交付：Go/No-Go 决策和冻结文档。

### Week 5–6：正式验证准备与第一批 held-out

- 锁定配置和分析脚本；
- 运行 held-out 数据；
- 计算置信区间、阶段条件率和归因分析；
- 根据 primary finding 决定是否加入防御实验。

交付：论文主结果表的第一版，而不是最终投稿稿。

---

## 10. 分工

需要人工完成：

- 开通 L40、SSH 与磁盘；
- 接受模型许可证/准备 Hugging Face token；
- 决定 GPU 使用时段和预算；
- 确认是否允许后续调用外部 API 模型。

代码与实验侧可以继续协助完成：

- runner 与指标重构；
- 测试、任务和 marketplace 配置；
- L40 部署脚本与运行命令；
- 结果聚合、图表和假设选择报告；
- pilot 后的冻结文档。

---

## 11. 立即开始的前三个任务

1. 修改 runner，使 `max_tool_iterations` 可配置并记录每轮 raw response/tool event；
2. 把 install 从“仅内存注册”改为“临时目录落盘 + manifest + registry”双重验证；
3. 为现有 weekly-brief family 写确定性 task verifier 和 emitted/parsed/executed 单元测试。

这三项完成前不启动大规模 L40 实验。
