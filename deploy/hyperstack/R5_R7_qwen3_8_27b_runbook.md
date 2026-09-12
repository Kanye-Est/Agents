# R5–R7 runbook — Qwen3.8-27B-AWQ backend on kan-aad-l40 (new-disk path)

> Spec: `idea/52` **Amendment 2** §A2.2 (serve spec) · §A2.3 (S1 recovery, new-disk R5) ·
> §A2.4 (ready gate G-a…G-f) · §A2.5 (G-c tool-probe gate) · §A2.7 (rig validation ≠ run).
> **`run = 0`** throughout — backend build-out + ready-gate are **not** §6.3 attack runs (A2.7).
> **Safety:** vLLM binds `127.0.0.1` only; **no credentials pass through the assistant**
> (public AWQ weights need no token; if gated, the account holder runs `huggingface-cli
> login` themselves); **no silent stack upgrade** (see the STOP checkpoint).
>
> These steps run **on the VM** (operator/account-holder at the `kan-aad-l40` console).
> The assistant authored the pinned artifacts; it does not (and cannot) execute here.

Preconditions (R1–R4, done): fresh L40 48G, `/ephemeral/ubuntu/{hf-cache,vllm-cache,logs,venvs,src}`
owned by `ubuntu`, tunnel `ssh -L 8000:127.0.0.1:8000 ubuntu@<IP>`.

Paths: `RUNTIME_ROOT=/ephemeral/ubuntu` · repo `→ $RUNTIME_ROOT/src/hello-agents-lab`
· serving venv `→ $RUNTIME_ROOT/venvs/vllm` · logs `→ $RUNTIME_ROOT/logs`.

---

## R5a — clone repo (main, incl. c1c8dc6 / 5835ecd + this backend commit)

```bash
mkdir -p /ephemeral/ubuntu/src && cd /ephemeral/ubuntu/src
git clone <repo-url> hello-agents-lab
cd hello-agents-lab && git checkout main && git log --oneline -3   # confirm HEAD
```

## R5b — build serving venv + install the FROZEN stack (vLLM 0.10.2)

Reproduce the exact `README_L40` stack from the committed freeze (torch cu128 needs the
PyTorch cu128 index):

```bash
python3 -m venv /ephemeral/ubuntu/venvs/vllm
/ephemeral/ubuntu/venvs/vllm/bin/pip install --upgrade pip
/ephemeral/ubuntu/venvs/vllm/bin/pip install \
  -r /ephemeral/ubuntu/src/hello-agents-lab/deploy/hyperstack/vllm-freeze.l40.txt \
  --extra-index-url https://download.pytorch.org/whl/cu128
# verify the pins
/ephemeral/ubuntu/venvs/vllm/bin/vllm --version                        # expect 0.10.2
/ephemeral/ubuntu/venvs/vllm/bin/pip show vllm torch transformers xformers \
  | grep -E '^(Name|Version)'   # vllm 0.10.2 / torch 2.8.0+cu128 / transformers 4.55.2 / xformers 0.0.32.post1
```

### ⚠ A2.2 STOP CHECKPOINT (do NOT skip)

`Qwen3.8-27B` is a new model. If it **cannot load** on the frozen 0.10.2 stack —
`vllm serve` erroring on unknown architecture, an AWQ-kernel/quantization mismatch,
or transformers-too-old — **STOP.** Do **not** `pip install -U` / bump anything silently.
Capture the exact error and hand it back; the plan is then: bump vLLM/transformers to
the **minimum** version that loads Qwen3.8-27B-AWQ → **re-run the G-c tool-probe** →
**re-freeze** (a new `vllm-freeze.*.txt`) → record it as an **Amendment** — *before* any run.
(A2.2: "不在冻结实验中途悄升级"; the chat-template may likewise need a 3.8-specific update
and re-freeze.)

## R5c — download weights (public AWQ repo, no token) + capture the pinned revision

```bash
export HF_HOME=/ephemeral/ubuntu/hf-cache
/ephemeral/ubuntu/venvs/vllm/bin/huggingface-cli download Qwen/Qwen3.8-27B-AWQ
```

- **Verify the exact repo at download (A2.2):** if `Qwen/Qwen3.8-27B-AWQ` 404s, confirm the
  correct id on HF — do **not** confuse with `Qwen3.5/3.6-27B` siblings; report back the
  resolved id. Public repo → anonymous download works (lower rate limits only).
- **Capture the revision** (the snapshot commit hash = the dir name under `snapshots/`):

```bash
ls -1 /ephemeral/ubuntu/hf-cache/hub/models--Qwen--Qwen3.8-27B-AWQ/snapshots/
```

## G-d — weights manifest (sha256 + revision + fetch-date)

```bash
REV=<paste the revision from above>
SNAP=/ephemeral/ubuntu/hf-cache/hub/models--Qwen--Qwen3.8-27B-AWQ/snapshots/$REV
{ echo "# G-d weights manifest"; echo "repo: Qwen/Qwen3.8-27B-AWQ"; echo "revision: $REV";
  echo "fetch_date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "backend: vllm 0.10.2";
  echo "---- sha256 (resolved files) ----"; find -L "$SNAP" -type f | sort | xargs sha256sum; } \
  | tee /ephemeral/ubuntu/logs/weights_manifest_qwen3_8_27b_awq.txt
```

## R6 — start vLLM (loopback, pinned revision)

```bash
cd /ephemeral/ubuntu/src/hello-agents-lab
export MODEL_REVISION=$REV          # or: export MODEL_PATH=$SNAP  (serve local snapshot)
nohup ./deploy/hyperstack/serve_qwen3_8_27b_awq_native_fc.sh \
  > /ephemeral/ubuntu/logs/vllm-qwen3-8-27b-awq.log 2>&1 < /dev/null &
tail -f /ephemeral/ubuntu/logs/vllm-qwen3-8-27b-awq.log   # wait: "Application startup complete"
```

The script **refuses to start on an unpinned revision** and serves **offline**
(`HF_HUB_OFFLINE=1`) from the cached snapshot — no serve-time network.

## R7 — tunnel verify (from the laptop)

```bash
ssh -L 8000:127.0.0.1:8000 ubuntu@<IP>
curl -s http://127.0.0.1:8000/v1/models      # should list qwen3-8-27b-awq
```

---

## Readiness gate G-a…G-f (§A2.4 — all must pass before MVP; still `run = 0`)

| Gate | Command | Pass line |
|---|---|---|
| **G-a** `/v1/models` | `curl -s http://127.0.0.1:8000/v1/models \| python3 -m json.tool` | `id == qwen3-8-27b-awq` (matches SERVED_NAME & `.env` LLM_MODEL_ID) |
| **G-b** env freeze | `/ephemeral/ubuntu/venvs/vllm/bin/pip freeze \| tee /ephemeral/ubuntu/logs/vllm-freeze.qwen3-8-27b.txt; sha256sum /ephemeral/ubuntu/logs/vllm-freeze.qwen3-8-27b.txt` | matches `deploy/hyperstack/vllm-freeze.l40.txt` (if a bump was forced at R5b, THIS file is the **re-freeze** — record its sha256 + the Amendment) |
| **G-c** tool-probe | `cp deploy/hyperstack/env.qwen3-8-27b.example .env` (set `LLM_MODEL_REVISION=$REV`), then `<project-venv>/bin/python secskill-lab/acquisition/tool_probe.py --num 10 --model-label qwen3-8-27b-awq` | **idea/38 §4 frozen gate**: single-tool ≥9/10 · explicit-search ≥8/10 · explicit-install ≥7/10 · irrelevant ≤1/10 · structured-parse ≥95%. Below line → "该模型撑不住协议", archive separately, **not** "attack failed" (A2.5). |
| **G-d** weights manifest | (produced above) `cat /ephemeral/ubuntu/logs/weights_manifest_qwen3_8_27b_awq.txt` | sha256 + revision + fetch-date recorded |
| **G-e** network surface | `ss -tlnp \| grep -E ':8000\|:8799'` | vLLM on **`127.0.0.1:8000` only** (NO `0.0.0.0`); the collector already hardcodes `127.0.0.1` bind (`secskill-lab/collector.py`) |
| **G-f** ledger | assemble G-a…G-e **measured** values | lands as the next `idea/52` Amendment (idea/40-style ready record) |

> **G-c prerequisite:** the tool-probe runs on the **project** venv (hello-agents client),
> not the serving venv — build it first if absent (project README: Python 3.12 +
> `hello-agents[all]==0.2.8`), e.g. `/ephemeral/ubuntu/venvs/secskill`.

## After the gate passes (forward — A2.7, still `run = 0`)

1. Set `LLM_MODEL_REVISION=$REV` in the project `.env`.
2. A2.7 Goose rig validation: fill `secskill-lab/utcs/goose/config.template.yaml`
   backend (`GOOSE_MODEL: qwen3-8-27b-awq`, `OPENAI_HOST: http://127.0.0.1:8000`),
   one baseline tool call → labelled **rig validation / 不计 run**.
3. Return the G-a…G-e measured values; the assistant drafts the **G-f ready-record Amendment**.
