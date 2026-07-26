# 39 — S2 原生 Function-Calling 实现冻结

> 日期：2026-07-26  
> 状态：pre-results；尚未运行 Qwen × S2 在线 probe 或因果 trial。  
> 依赖：idea/31、idea/35、idea/38。

## 1. Cell 与 estimand

- Cell：`M1 × S2 = Qwen3-32B-AWQ × OpenAI-style native function calling`。
- 与 anchor `M1 × S1` 相比，只改变 scaffold：
  - S1：模型输出文本 `[TOOL_CALL:...]`，仓库 parser 解析；
  - S2：请求使用 `tools=[{type:function,...}]`，模型返回结构化 `tool_calls`。
- S2 内的 P0/P1 estimand 不变：`acquisition-encouragement bundle`。
  - P0：中性 system prompt + 中性 `search_skills.description`；
  - P1：P0 + search→install→invoke encouragement + encouraging description；
  - P2：模型可见配置与 P1 相同，只在参数解析后、安装执行前 gate。

## 2. 已冻结的等价性

1. 复用同一 150-trial manifest、30 hard specs、marketplace、benign/malicious
   twins、fresh sandbox、collector 与 deterministic verifier。
2. 原生 runner 复现同一事件：
   `tool_call_emitted → parsed → execution_started → succeeded/failed`，
   以及 acquisition / on-disk / registry / invoke / payload / task_ok 全链事件。
3. P2 gate 的位置不变：JSON arguments 成功解析之后、`InstallSkillTool.run`
   之前。
4. 动态安装完成后，下一轮请求重新生成 function schemas，新 skill 才进入
   可调用集合。
5. 安装回执在 S2 不包含 `[TOOL_CALL:...]` 文本示例，避免把 S1 协议泄漏回
   原生 scaffold；等价信息通过下一轮 function schema 暴露。
6. `metrics.py` 与 `analyze_policy_hardgap.py` 不为 S2 修改。

## 3. 实现件

- `secskill-lab/acquisition/native_fc_agent.py`
  - HelloAgents Tool → strict OpenAI function schema；
  - 原生 `tool_calls` loop；
  - provider call id + repository event id；
  - malformed JSON、unknown tool、budget exhaustion 与 execution gate 审计。
- `run_policy_hardgap_eval.py --scaffold native_fc`
  - output 的 `design.scaffold` 与 `backend.scaffold` 明确标记；
  - resume 时拒绝 scaffold 不匹配，避免混合 checkpoint。
- `tool_probe.py --scaffold native_fc`
  - 使用同一 45-probe suite 和同一冻结门槛。
- `serve_qwen3_32b_awq_native_fc.sh`
  - 同 anchor model revision / 8k context；
  - vLLM `--enable-auto-tool-choice --tool-call-parser hermes
    --reasoning-parser qwen3`。

## 4. 在线运行前的本地验收

- Ruff：通过。
- Unit tests：19/19 通过。
- 新增离线契约测试：
  1. strict schema 的 required 参数正确；
  2. P2 在 parse 后、install 执行前阻断；
  3. search→install→动态注册→invoke 全链可运行；
  4. 安装后的 skill 出现在下一轮 native function schemas。

## 5. 在线执行门

1. 等 M2×S1 完成后停止 Llama server，启动冻结的 Qwen native-FC server。
2. 先跑 5 条 transport smoke，仅检查 API / schema / event plumbing。
3. 再跑完整 45 条 tool-probe。使用 idea/38 的五项门槛：
   `≥90% / ≥80% / ≥70% / ≤10% / ≥95%`。
4. 过门才运行 150 条；不过门先归因为 serving/parser/protocol，不能计为安全。
5. 在线 probe 的任何行为结果出现前，不修改任务、prompt、tool description、
   gate、metric 或阈值。

## 6. 预期输出

- `probe_qwen3-32b-awq-native-fc_full_<date>.json`
- `policy_hardgap_causal_v2_full_qwen3-32b-awq-native-fc_<date>.json`
- 同名 `.analysis.json/.md`
- 独立 manifest / source snapshot / model revision / pre-results commit。

