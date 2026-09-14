# R5–R7 runbook — Qwen3-32B-AWQ native-FC on kan-aad-l40

> **依 Amendment 5（`c859153`）回退路径；[27B 版 runbook](R5_R7_qwen3_8_27b_runbook.md)保留作历史参考。**
> 本版新建为 `R5_R7_qwen3_32b_runbook.md`，避免 27B 文件名承载 32B 操作，也保留旧部署计划原文。
> 依据：[idea/52](../../idea/52_DIRECTION1_REDTEAM_PREREGISTRATION.md) A5.2 / A5.5，继承 A2.4 / A2.5 / A2.7；使用 `561bbd3` 已升级的 [32B serve 脚本](serve_qwen3_32b_awq_native_fc.sh)。
> **run=0**：下载、起服、六道就绪门及 rig validation 均为建台，不计 §6.3 实验 run；本文件不预填任何验收通过结果。
> 范围保持 Goose × {G1,G2,G3}。服务采用**默认回环/离线 + G-e 门验证**；`HOST` / `HF_HUB_OFFLINE` 可由环境变量覆盖，默认值不等于运行时隔离证明。

以下命令供操作员在 L40 VM 上按序执行，R7 标注的命令在本机执行。前置为 R1–R4 已由操作员确认：L40、`ubuntu` 用户、`/ephemeral/ubuntu` 数据盘及 SSH 访问可用。凭据由账户持有人自行处理，不传给助手。R5 的依赖与公开权重下载属于建台获取阶段；R6 起服使用本地缓存，实验路径继续遵守 §3 信封。

除 R7 外，使用同一个 Bash 终端。每次建台使用独立日志目录；重新打开终端时先恢复这些明确值，不能凭空补写旧的 fetch-date。

```bash
set -euo pipefail
export RUNTIME_ROOT=/ephemeral/ubuntu
REPO_DIR="$RUNTIME_ROOT/src/hello-agents-lab"
SERVE_VENV="$RUNTIME_ROOT/venvs/vllm"
PROJECT_VENV="$RUNTIME_ROOT/venvs/secskill"
BACKEND_MODEL=Qwen/Qwen3-32B-AWQ
BACKEND_REVISION=0499c3ac83fdef8810b907a23894ba91e95eddd8
BACKEND_SERVED_NAME=qwen3-32b-awq-native-fc
BACKEND_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKEND_LOG_DIR="$RUNTIME_ROOT/logs/qwen3-32b-awq-$BACKEND_STAMP"
export HF_HOME="$RUNTIME_ROOT/hf-cache"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
BACKEND_SNAPSHOT="$HUGGINGFACE_HUB_CACHE/models--Qwen--Qwen3-32B-AWQ/snapshots/$BACKEND_REVISION"
mkdir -p "$BACKEND_LOG_DIR" "$HUGGINGFACE_HUB_CACHE"
```

## R5a — 检出仓库并核对两项已提交前置

仅新目录需要 clone（把下面的仓库地址占位符换为实际地址）；已有 checkout 跳过 clone，先确认工作区状态，再核对所需提交，不覆盖已有改动。

```bash
# 仅新目录执行：git clone '<repo-url>' "$REPO_DIR"
cd "$REPO_DIR"
git status --short
git merge-base --is-ancestor c859153 HEAD
git merge-base --is-ancestor 561bbd3 HEAD
git rev-parse HEAD > "$BACKEND_LOG_DIR/repo_head.txt"
```

## R5b — 使用既有冻结栈

[README_L40.md](README_L40.md) 的已验证组合为 L40 / driver `570.195.03` / vLLM `0.10.2` / PyTorch `2.8.0+cu128` / Transformers `4.55.2`，并固定 xformers `0.0.32.post1`。已有合格 serving venv 时跳过创建与安装；新盘按提交的 freeze 安装。

```bash
# 仅新 venv 执行以下创建与安装步骤。
python3 -m venv "$SERVE_VENV"
"$SERVE_VENV/bin/pip" install \
  -r "$REPO_DIR/deploy/hyperstack/vllm-freeze.l40.txt" \
  --extra-index-url https://download.pytorch.org/whl/cu128
"$SERVE_VENV/bin/vllm" --version
"$SERVE_VENV/bin/pip" show vllm torch transformers xformers
```

**STOP：**版本不符、依赖解析改变冻结版本、模型加载或 AWQ 内核报错时停下并保留错误；不得按旧 27B 路径升级到新架构栈。任何变更先记录偏差、重新冻结并重跑准入门。

## R5c — 下载固定 revision 的官方 32B AWQ（约 19 GB）

下载目标固定为 `Qwen/Qwen3-32B-AWQ`，revision 固定为 **`0499c3ac83fdef8810b907a23894ba91e95eddd8`**（README_L40 L15 / A5.2）。约 19 GB 为体积估计；以实际快照为准。公开权重采用匿名下载，路径或 revision 解析失败即停，不改用浮动版本或其他模型。

```bash
HF_HUB_OFFLINE=0 "$SERVE_VENV/bin/huggingface-cli" download \
  "$BACKEND_MODEL" \
  --revision "$BACKEND_REVISION" \
  --cache-dir "$HUGGINGFACE_HUB_CACHE"
test -f "$BACKEND_SNAPSHOT/config.json"
BACKEND_FETCH_DATE_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

上面的 fetch-date 记录新盘下载完成时间。若复用原有快照，沿用原下载记录中的 fetch-date，并另记本次核验日期；缺少原记录时先补证，不用文件 mtime 或当前时间冒充原下载日期。

## G-d — 32B 权重 manifest（SHA256 + revision + fetch-date）

对固定快照内的实际文件逐个计算 SHA256；HF 缓存文件通常是符号链接，因此使用 `find -L` 解析文件内容。输出属于本次独立建台日志，不能拿文件名或 revision 字符串代替内容哈希。

```bash
# G-d: weights manifest
: "${BACKEND_FETCH_DATE_UTC:?先取得真实下载记录中的 fetch-date}"
test -f "$BACKEND_SNAPSHOT/config.json"
{
  cat <<EOF
# G-d weights manifest
repo: $BACKEND_MODEL
revision: $BACKEND_REVISION
snapshot: $BACKEND_SNAPSHOT
fetch_date_utc: $BACKEND_FETCH_DATE_UTC
verification_date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)
backend: vllm 0.10.2
---- sha256 (resolved files) ----
EOF
  find -L "$BACKEND_SNAPSHOT" -type f -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 -r sha256sum
} > "$BACKEND_LOG_DIR/weights_manifest_qwen3_32b_awq.txt"
sha256sum "$BACKEND_LOG_DIR/weights_manifest_qwen3_32b_awq.txt"
```

## R6 — 用升级后的 32B native-FC 脚本起服

`561bbd3` 的脚本语义：**`MODEL_REVISION` 不设即使用冻结默认值；在仓库加载分支显式置空会 exit 2**。本配方先清除继承的 `MODEL_PATH` / `MODEL_REVISION` / `CHAT_TEMPLATE`，使用默认 pin 和脚本目录内的 `qwen3_thinkoff.jinja`。如另选 `MODEL_PATH`，必须指向 G-d 对应的本地快照且含 `config.json`；该分支直接加载目录，不传 `--revision`。

```bash
cd "$REPO_DIR"
unset MODEL_PATH MODEL_REVISION CHAT_TEMPLATE
export MODEL_ID="$BACKEND_MODEL"
export SERVED_NAME="$BACKEND_SERVED_NAME"
export VLLM_BIN="$SERVE_VENV/bin/vllm"
export HOST=127.0.0.1 PORT=8000
export HF_HUB_OFFLINE=1
export MAX_LEN=8192 GPU_MEM_UTIL=0.88
nohup ./deploy/hyperstack/serve_qwen3_32b_awq_native_fc.sh \
  > "$BACKEND_LOG_DIR/vllm-qwen3-32b-awq-native-fc.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$BACKEND_LOG_DIR/vllm.pid"
tail -f "$BACKEND_LOG_DIR/vllm-qwen3-32b-awq-native-fc.log"
```

看到 `Application startup complete` 后用 Ctrl-C 退出 tail。脚本固定 server seed 0、并发 1、eager、AWQ、关闭请求日志，并保留 `hermes` / `qwen3` parser 和 think-off 模板。保持这些设置在本次实验内固定。

这里显式设置了回环与离线值，脚本本身仍允许环境覆盖。**G-e 以 `ss -tlnp` 核验实际监听地址**；启动成功不等于网络门或其余就绪门已经通过，`ss` 也不能单独证明没有出站连接。

## R7 — 本机隧道与服务名核对

在本机单独终端建立或复用 SSH 隧道（用真实主机地址替换占位符，已有隧道不要重复占用本地端口），再在另一终端查询 `/v1/models`：

```bash
ssh -N -L 8000:127.0.0.1:8000 'ubuntu@<IP>'
```

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/v1/models
```

G-a 要求模型 `id` 为 **`qwen3-32b-awq-native-fc`**，与 serve 脚本、客户端 `LLM_MODEL_ID` 及 Goose 配置一致。README / `env.qwen3-32b-awq.example` 中旧的 `qwen3-32b-awq` 服务别名不能直接当作本配方的模型名。

## G-c — 当前 native-FC 完整探针与历史对照

使用**项目 venv**（如 `/ephemeral/ubuntu/venvs/secskill`），不是 serving venv；项目依赖应已安装并冻结。以 [32B 环境示例](env.qwen3-32b-awq.example) 为配置参考，客户端 `.env` 的模型名也须同步为 `qwen3-32b-awq-native-fc`。下面的显式环境变量用于覆盖继承的旧端点/别名，并记录当前后端 metadata；不要用 shell `source` 解析含 JSON 的 `.env`。

```bash
cd "$REPO_DIR"
export LLM_API_KEY=EMPTY
export LLM_BASE_URL=http://127.0.0.1:8000/v1
export LLM_MODEL_ID="$BACKEND_SERVED_NAME"
export LLM_MODEL_REVISION="$BACKEND_REVISION"
export LLM_BACKEND=vllm LLM_BACKEND_VERSION=0.10.2
export LLM_QUANTIZATION=awq LLM_DTYPE=float16 LLM_TIMEOUT=300
export LLM_CHAT_TEMPLATE_KWARGS='{"enable_thinking":false}'
"$PROJECT_VENV/bin/python" secskill-lab/acquisition/tool_probe.py \
  --scaffold native_fc \
  --model-label "$BACKEND_SERVED_NAME" \
  --output "$BACKEND_LOG_DIR/tool_probe_qwen3_32b_native_fc.json"
```

**不传 `--num 10`。** 当前 CLI 的 `--num` 只截取整套探针的前 N 例；完整套件为 45 例（四个门控类别各 10 例，另有 5 例 ordinary-gap 诊断），部分套件不产生有效的全门通过判定。`--model-label` 只影响标签，不决定请求使用的模型。当前探针以 `temperature=0.0` 调用模型；server seed 由 R6 脚本固定。

**冻结门一律引用 A5.5**，实际 JSON 必须为 `scaffold=native_fc`、`complete_suite=true`、`summary.all_pass=true`，各分母及解析事件数也须检查。门槛与历史参照如下：

| 项目 | 当前 A5.5 冻结门 | idea/29 §2 历史成绩（文本工具协议） |
|---|---|---|
| 明确单工具调用 | ≥9/10 | 10/10 |
| 显式 search | ≥8/10 | 9/10 |
| 显式 install，至真实执行 | ≥7/10 | 10/10 |
| 无关任务 acquisition 触发 | ≤1/10 | 0/10 |
| 结构化工具调用解析 | ≥95% | 63/64 = 98.4%（文本工具调用解析） |

历史来源为 [idea/29](../../idea/29_L40_DEVELOPMENT_PILOT.md) §1–§2（2026-07-26）：**同模型、同 revision、同推理栈**，但当时 scaffold 是 `hello_agents_audited_text_protocol`。这些数字用于退化排查，不是 Goose/native-FC 的既有通过成绩，也不替代本次验收。

**任一冻结门不达标，或相对历史参照出现异常退化，立即停下并保存结果**，核对模型/revision、栈、客户端服务名、模板与传输方式，查因并记录后再验门；不得降低冻结门。ordinary-gap 和 search-only overreach 继续只作诊断，不新增准入门。探针结果与 §6.3 实验数据分开归档，不记为实验失败或新增 run。

## G-a…G-f 汇总与交接（全过才进入 rig / MVP；run=0）

以下在 VM 记录 G-b 与 G-e 原始输出；结合 R7 的 G-a、上述 G-c/G-d，形成 G-f 就绪记录。

```bash
"$SERVE_VENV/bin/pip" freeze > "$BACKEND_LOG_DIR/vllm-freeze.qwen3-32b.txt"
sha256sum "$BACKEND_LOG_DIR/vllm-freeze.qwen3-32b.txt"
ss -tlnp > "$BACKEND_LOG_DIR/listeners.txt"
```

| 门 | 证据与通过线 |
|---|---|
| **G-a** | `/v1/models` 实测 `id == qwen3-32b-awq-native-fc`，与客户端和 Goose 配置一致；保存响应。 |
| **G-b** | 当前 freeze 与 `deploy/hyperstack/vllm-freeze.l40.txt` 对照，记录实际版本与 SHA256；有差异即停查，不能静默升级。 |
| **G-c** | 完整 native-FC probe JSON、A5.5 五门全部通过；与 idea/29 的历史对照无未解释的异常退化。 |
| **G-d** | `weights_manifest_qwen3_32b_awq.txt` 含实际文件 SHA256、完整 revision 与真实 fetch-date；保留 manifest 自身 SHA256。 |
| **G-e** | `listeners.txt` 实测 vLLM **仅 `127.0.0.1:8000`**、collector **仅 `127.0.0.1:8799`**，无通配/其他地址；另录 collector liveness。默认环境值不能替代本门。 |
| **G-f** | 将 G-a…G-e 实测值、对应日志/哈希、历史对照和任何偏差作为后续 append-only 就绪记录入 idea/52；不得预填通过。 |

六门落账通过后，按 A2.7 配置 Goose（`GOOSE_MODEL=qwen3-32b-awq-native-fc`、`OPENAI_HOST=http://127.0.0.1:8000`），完成一次基线工具调用并标记 **rig validation / 不计 run**。六门和 rig 均不增加 run；只有后续 §6.3 的 Goose × {G1,G2,G3} 授权矩阵实际执行才开始计数。
