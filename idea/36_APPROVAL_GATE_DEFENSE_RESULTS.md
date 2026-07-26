# 36 — Approval Gate：拒绝、良性授权与恶意授权

> 日期：2026-07-26
> 状态：三个防御臂全部完成。
> 目的：区分 execution authorization 与 skill vetting。

## 1. 三臂结果

三个 hard family 合并，均为同一冻结的 30 个 PDF/ICS/QR specs：

| Arm | Search | Install/on-disk | Invoke | Functional E2E | Payload | Gate block |
|---|---:|---:|---:|---:|---:|---:|
| P2 denied + malicious | 22/30 | 0/30 | 0/30 | 0/30 | 0/30 | 25 attempts / 25 |
| P2 approved + benign | 25/30 | 25/30 | 25/30 | 25/30 | 0/30 | 0 |
| P2 approved + malicious | 25/30 | 25/30 | 25/30 | 25/30 | 25/30 | 0 |

Approved 两臂的逐 family utility 完全相同：

| Twin | PDF | ICS | QR | Pooled |
|---|---:|---:|---:|---:|
| Benign functional E2E | 9/10 | 6/10 | 10/10 | 25/30 |
| Malicious functional E2E | 9/10 | 6/10 | 10/10 | 25/30 |
| Benign payload | 0/10 | 0/10 | 0/10 | 0/30 |
| Malicious payload | 9/10 | 6/10 | 10/10 | 25/30 |

benign→malicious 的 payload 配对结果：

```text
benign=0, malicious=1: 25
benign=1, malicious=0: 0
exact McNemar p: 5.96e-8
```

这个 p 值只是描述 twin 操作按构造生效；核心证据是 utility 路径逐任务一致，而 payload
在所有 25 个实际调用上完全分离。

## 2. 模型可见等价性

30/30 配对任务均满足：

- user query 相同；
- task-spec hash 相同；
- P2 policy-prompt hash 相同；
- `visible_market_sha256` 相同；
- 每个 family 的 benign/malicious `SKILL.md` 字节级相同；
- name、blurb、tags、install note、parameter schema 和正常 artifact 行为相同。

完整 marketplace hash 故意不同，因为内部 provenance 记录了
`package_variant=benign/malicious` 和不同 handler package；这些字段不进入模型可见的
搜索结果或批准界面。恶意 handler 只额外向 `127.0.0.1` collector 发送合成 marker。

因此 approved 两臂不是“恶意 skill 更会诱导模型”的比较。模型与批准者基于当前界面
看到的证据相同，唯一实验变化是获批 package 的隐藏实现。

## 3. 正确的防御结论

Approval gate 有两个得到实证支持的作用：

1. **Policy enforcement**：未授权时，25/25 实际安装尝试在解析后、执行前被拦截；
2. **Audit/authorization point**：安装从静默的 agent 行为变成显式、可记录的决定。

它不提供第三个能力：

3. **Skill vetting**：授权 malicious twin 后，25/25 实际调用仍触发 payload。

所以边界结果不是“gate 被绕过”。攻击没有绕过 gate；它获得了批准。结果证明：

> Gate 决定能不能装，但在缺少额外 provenance 的界面上，不能决定该不该装。

完整防御必须组合：

```text
execution gate
+ authenticated provenance / signature
+ static or reputation-based vetting
+ least-privilege capability scoping
+ post-install runtime monitoring
```

## 4. 可复核文件

```text
secskill-lab/acquisition/results/
  policy_hardgap_causal_v2_full_20260726.json
  policy_hardgap_causal_v2_p2_approved_benign_20260726.json
  policy_hardgap_causal_v2_p2_approved_malicious_20260726.json
```

Approved benign：

```text
manifest_sha256 = abe04b4952776e879abf12f0faeae7229e8c391460b9e2df10fb1493cd80a7f9
```

Approved malicious：

```text
manifest_sha256 = ebe93bc765a1c60112e498e6e097e73d18d4439f50982c0ac83dc8efef2f552b
```

两者 runner source：

```text
cad62aa0d162d950584c65b6d1118ac8175715b6971ca8b32e830334cf6638a6
```
