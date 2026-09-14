# Goose 1.45.0 rig validation instruments

本目录冻结 Goose 建台验证所用的采集、控制和评分代码。所有建台与探针记录均为
`run=0`；T-A 是一次独立的 rig validation，不执行实验矩阵。

首次 VM 预检在解析 `iptables -S OUTPUT` 时停止：原输出对 cgroup 路径加了引号，
旧核验却按未加引号的子串比较。`tests/fixtures/iptables-output-before.txt` 是那次
命令保存的完整 stdout，逐字节导入；旁边的 provenance JSON 保存原命令和时间。
`output_rules.py` 通过 shell token 解析核验第一条 OUTPUT 规则，回放与实际控制器
调用同一函数。它仍要求确切的 cgroup、目标链及无额外协议限制，不能把不同规则
当作等价规则。

## 冻结与来源

- `import-provenance.json` 记录从 VM 导入的原始文件及其当时的 SHA256；它是来源记录。
- `SHA256SUMS` 记录本批最终文件的 SHA256，路径相对本目录。控制器在执行前核验源码。
- Git commit 固定这份清单及源码；VM 必须核对该 commit 和工作树字节后才能放行 T-A。
- `baseline/` 保存已经冻结的 T-A 提示、输入、预期输出和原冻结记录。
  `.gitattributes` 禁止 Git 改写这些字节及原始 stdout fixture 的换行。
- 这份清单固定的是研究仪表；工具 A 的启动选择器仍为 `utcs-mdclean@latest`。
  本批不改变工具选择器、Goose 版本、模型或后端冻结栈。

## 组件

| 文件 | 作用 |
| --- | --- |
| `output_rules.py` | 同时供原始输出回放和实际 OUTPUT 首规则核验使用 |
| `prepare_controls.py` | 新建独立 gate cgroup，复用本地 OSV 辅助服务，逐项验证规则计数 |
| `rig_gate.py` | 四次本机控制、显式放行及唯一一次 strace/Goose 启动 |
| `launch_baseline.py` | 采集就绪、授权配置变更、单次基线、进程树结束与会话导出 |
| `capture_watch.py` | 在 Goose 日志轮转前保全请求文件的 inode |
| `http_capture.py` | 离线重组 PCAP 中的 TCP、HTTP 与 SSE |
| `goose_trajectory_adapter.py` | 交叉核对 wire、native 请求日志与会话，输出输入 schema v1 |
| `score_baseline.py` | 自然选用、逐字节任务完成及发布工具正常功能的独立评分 |
| `audit_baseline_envelope.py` | 工作区、拒绝规则计数及 strace 网络事件的保守提取与审计 |
| `freeze_baseline.py` | 原 T-A 冻结程序；已冻结的提示词不因重试而重新生成 |
| `rig_helpers.sh` | 当前 L40 建台窗口的监听、防火墙及既有进程快照核对 |
| `archive_phase.py` | 将指定阶段复制成稳定快照，生成文件清单与证据 tar |

`osv_unavailable.py` 是仅回环的 HTTP 503 辅助服务。其状态只能记作
“扫描不可用”；不构成扫描通过或任何防御效果证据。重试复用已记录的实例。

原始输出回放的 `--expected-cgroup` 取 iptables 使用的根相对路径，不带开头的
`/`。本批成功报告是 `validation/original-output-replay.corrected-call.json`；
首次 CLI 调用误传绝对期望路径的拒绝记录也保留，详见对应 receipt。

```bash
python3 -B output_rules.py \
  --rules-file tests/fixtures/iptables-output-before.txt \
  --expected-cgroup system.slice/utcs-rig-ta-20260914-103238.service \
  --expected-chain UTCS_RIG4_103238 \
  --output /absolute/new-evidence-path/replay.json
```

## 执行约束

运行入口的参数以各脚本 `--help` 为准。源码从本目录读取，运行产物写入新的阶段
目录；失败阶段、原始 stdout 和原配置快照保留。已有 OSV、vLLM、collector 与
Verdaccio 服务不因重试而重启。

在新的 gate cgroup 内依次验证：允许的 IPv4 回环 TCP、被拒绝的 IPv4 TCP、
被拒绝的 IPv6 TCP、被拒绝的本机 UDP 53。最后一项只发送一个无 DNS 报文语义
的字节。每项既要满足连接结果，也要看到对应专用规则的计数增长。没有公网探测。
规则只约束该 Goose cgroup 的直接 IP 出站；本地后端和 registry 的离线配置另有
已接受的建台证据。

全部控制通过后，先启动原始 HTTP 捕获与日志 watcher；二者真实就绪后才将
extension 从 `enabled:false` 改为 `true`，记录授权事件并放行一次 T-A。
评分不修剪最终文本、不移除围栏、不补换行，不通过时不重跑或调整门限。

采集结束要求整棵 cgroup 已空、wrapper 成功结束、无异常清理或遗留子进程。
tcpdump 或 watcher 提前结束均不能视为完整捕获。适配器保留原始参数、消息
envelope、工具 schema、分片及完整拼接的 thinking；未知或不完整材料不作完整性主张。
合成自验与真实会话验证分别记录，本目录不据此生成 `trajectory_absent` 的结论，
也不把合成自验当作协议要求的 P-ctx 阳性对照。

`validation/` 中的报告说明执行它们的实际 Python/Node 版本；本机自验不替代 VM
冻结运行时。真实执行的证据必须另存于 VM 阶段目录，记录源码 commit、清单哈希、
环境、进程和捕获时间。
