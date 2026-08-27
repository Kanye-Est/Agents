# 10 — 本地 / Hyperstack 后端方案（顶会向，已锁定）

> 根据 2026-07 讨论锁定。目标：摆脱卡慢 API，用可复现的开源 70B 级模型做英文主实验，冲顶会。

---

## 0. 已锁定决策

| 项 | 决定 |
|----|------|
| 论文语言 / 实验语言 | **全英文**（query、skill 描述、system prompt、论文） |
| 部署位置 | **Hyperstack SSH 远程 GPU**（**开发默认 A6000 48G**；定稿/吃紧再 A100/H100 80G） |
| Q1 实际属于 | **方案 A**：实验在远程 GPU 机上跑（本机只写代码、scp/rsync 同步） |
| 主模型 | **Llama-3.3-70B-Instruct**（英文 agent+tool 顶会最常见档） |
| 第二模型（论文表） | **Qwen2.5-72B-Instruct**（跨模型一行，可选） |
| 切换力度 | **主路径全部替换为本地**；旧 deepseek 中文结果仅作探索性附录/不进主表 |
| 量化 | **开发用 4bit（AWQ）；定稿可再跑 BF16/更高配对照**（见下文解释） |
| 上下文 | **max_model_len=8192 起步**；不够再 16384 |
| 并发 | **先 1**；探针通过后再 2–4 |
| 验收 | 接受 10 条 tool probe 门槛后再跑 A0/A2 |
| API | 保留 `.env.api` 备份，**默认不使用** |

---

## 1. 你标「不懂」的三项，用人话说明

### Q1：A 还是 C？

| | 含义 | 你的情况 |
|--|------|----------|
| **A** | SSH 登录有 GPU 的机器，模型和服务都在那跑实验 | ✅ Hyperstack 就是这个 |
| **C** | 本机也跑一部分重实验 + 远程也跑 | 你本机是 4060，**不必**当实验机 |

工作流建议：

```text
笔记本：改代码、git commit
    ↓ rsync / git pull
Hyperstack：vLLM 起模型 + 跑 run_acquisition_eval
    ↓ 结果 json scp 回来
笔记本：写论文 / 画图
```

### Q4：量化是什么？

模型权重可以用「完整精度」或「压缩精度」放进显存：

| 说法 | 类比 | 显存 | 速度 | 质量 |
|------|------|------|------|------|
| **BF16 / FP16** | 原画 | 最吃 | 中 | 最好 |
| **4bit（AWQ/GPTQ）** | 高清压缩 | 省很多 | 更快 | 通常接近，agent 任务往往够用 |

**70B + 80G 单卡：**

- BF16 70B 权重大约 140GB 量级 → **单卡塞不下**，要多卡或量化  
- **4bit 70B** 大约 35–40GB 级 → **单卡 80G 很舒服**，还能留 KV cache 给多轮对话  

所以：**不是「质量差的山寨」，而是顶会论文里也常见的部署方式。**  
推荐：

1. **日常实验 / 矩阵：Llama-3.3-70B AWQ 4bit**  
2. 若审稿质疑：加一句用相同设定的更高精度或第二模型复现关键数字  

H100 若支持 FP8，也可作为质量–速度折中（部署稍复杂，第二步再做）。

### Q5：上下文长度 & 并发是什么？

**上下文（context / max_model_len）**  
= 一次对话里模型能「记住」的 token 上限（系统提示 + 工具描述 + 历史 + 回复）。

- 你的 agent：system + 8 个工具描述 + 多轮 TOOL_CALL ≈ 通常 **2k–6k tokens**  
- **8192 一般够**；只有历史特别长再开 16384  
- 上下文开越大，同样显存下 **越慢、越容易 OOM**

**并发（并发请求数）**  
= 同时跑几条 `agent.run(query)`。

- 先 **1**：稳定测延迟与正确性  
- 矩阵扫参时再 **2–4**（看显存与 vLLM 配置）  
- 并发太高会变慢或爆显存，不是越大越好  

---

## 2. 顶会向模型选择理由

| 模型 | 角色 | 原因 |
|------|------|------|
| **Llama-3.3-70B-Instruct** | **主 victim** | 英文、工具调用生态熟、安全/agent 论文引用多 |
| **Qwen2.5-72B-Instruct** | 论文第二列 | 证明不是单模型伪影 |
| deepseek-chat（交大） | **不进主路径** | 卡慢；且中文探索与英文主文不一致 |

主表至少报告：**Llama-3.3-70B**；有算力再加 Qwen 一行。

---

## 3. 「全部替换」对实验意味着什么

不只是换 URL，还包括：

| 模块 | 动作 |
|------|------|
| `.env` | 默认指向 Hyperstack 上 vLLM |
| system prompt | 英文 |
| `queries_natural` / `queries_gap` | **英文版** |
| skill `SKILL.md` description | **英文**（攻击面本身就是自然语言） |
| marketplace blurb / install_note | 英文 |
| 旧 0%/10%/5% | 标注为 preliminary (zh/deepseek)，**主文重跑** |

否则审稿人会问：中文 API 结果和英文本地结果是不是两套系统。

---

## 4. GPU 选型（资源不浪费）

| 卡 | 显存 | 建议用途 |
|----|------|----------|
| **A6000** | **48G** | ✅ **当前默认**：70B AWQ + 8k 上下文；日常 acquisition / 矩阵 |
| L40 | 48G | 同 A6000 档，可互换 |
| A100/H100 | 80G | 定稿主表、更长上下文、更高并发、BF16/更宽松 KV |
| A4000 | 16G | ❌ 不够 70B；最多 7B–14B 玩具，不进论文主路径 |

**A6000 跑 70B AWQ 要点（48G 偏紧但常用）：**

- 必须用 **4bit AWQ/GPTQ**，不要 BF16 70B 单卡  
- `max_model_len=8192`（先别 32k）  
- `gpu_memory_utilization≈0.90`  
- 并发 **先 1**  
- 若 OOM：降到 4096 上下文，或临时换 **32B** 做开发，主表再换 70B@A100  

### 4.1 机器就绪

```bash
# 登录后
nvidia-smi          # 确认 A6000 48G（或你选的卡）
df -h               # 模型盘至少 100G+ 空闲
python3 --version   # 建议 3.10+
```

### 4.2 装 vLLM（示例）

```bash
# 建议独立环境
python3 -m venv ~/venv-vllm
source ~/venv-vllm/bin/activate
pip install -U pip
pip install vllm transformers accelerate
# 按 CUDA 版本以 vLLM 官方文档为准
```

### 4.3 拉模型（二选一）

```bash
# 需要 HuggingFace token 时：
# huggingface-cli login

# 主模型：70B AWQ（单卡友好，具体 repo 名以 HF 上可用 AWQ 为准）
# 示例（请以当前 HF 上实际存在的 AWQ 仓库为准）：
# huggingface-cli download casperhansen/llama-3.3-70b-instruct-awq --local-dir ~/models/llama-3.3-70b-awq
```

仓库名会变动；部署时在 HF 搜 `Llama-3.3-70B-Instruct AWQ` 选下载量高的。

### 4.4 启动服务

见仓库脚本：`deploy/hyperstack/serve_llama70b_awq.sh`

```bash
# 默认端口 8000，仅监听本机（SSH 隧道访问更安全）
bash deploy/hyperstack/serve_llama70b_awq.sh
```

本机访问远程（可选）：

```bash
ssh -L 8000:127.0.0.1:8000 user@hyperstack-host
```

### 4.5 实验环境 `.env`

复制 `deploy/hyperstack/env.local.example` → 实验目录 `.env`：

```bash
LLM_API_KEY=EMPTY
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_MODEL_ID=llama-3.3-70b-instruct   # 与 vLLM --served-model-name 一致
```

### 4.6 验收顺序

```bash
# 1) 原始 OpenAI 兼容连通
curl http://127.0.0.1:8000/v1/models

# 2) 工具格式探针（10 条）
python secskill-lab/acquisition/tool_probe.py

# 3) 通过后再
python secskill-lab/acquisition/run_acquisition_eval.py --condition A0,A2 --num-queries 5
```

---

## 5. 验收门槛（Q7，已接受）

| 探针 | 通过线 |
|------|--------|
| 明确单工具 | ≥9/10 正确 TOOL_CALL |
| 缺口任务出现 search 意图 | ≥6/10 |
| 强制「请 search 并 install」 | ≥5/10 走到 install |
| 无关任务乱装 | ≤2/10 |

不过线：降温度 `temperature=0`、加强 system prompt、换 AWQ 源或试 Qwen2.5-72B-AWQ，**不要直接报攻击失败**。

---

## 6. 安全

- vLLM **只绑 127.0.0.1**，不要 `0.0.0.0` 裸奔公网  
- 外泄 collector 仍是 127.0.0.1  
- Hyperstack 防火墙默认拒绝外网访问 8000  

---

## 7. 里程碑（建议两周内）

| Day | 事 |
|-----|-----|
| 1 | Hyperstack 起 vLLM + curl models 通 |
| 1–2 | tool_probe 通过 |
| 2–3 | 英文 query + 英文 skill 描述迁移 |
| 3–4 | A0/A2 英文全量，定位 Stage2 |
| 5+ | 安装诱导矩阵 B；论文主表数字 |

---

## 8. 当前仓库已提供

- `deploy/hyperstack/serve_llama70b_awq.sh` — 启动模板  
- `deploy/hyperstack/env.local.example` — 环境变量模板  
- `secskill-lab/acquisition/tool_probe.py` — 英文工具探针  
- 本文 — 决策与解释  

下一步（需你在 Hyperstack 上执行）：装 vLLM → 下模型 → 起服务 → 跑 probe。  
代码侧英文 query/skill 迁移可在本机继续改，再 sync 上去。
