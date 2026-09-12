#!/usr/bin/env bash
# Pinned Qwen3.8-27B-AWQ backend — native function calling, thinking OFF.
#
# Spec: idea/52 Amendment 2 §A2.2 (agent-side primary backend for Goose × {G1,G2,G3}).
# Fuses: serve_qwen3_32b_awq_native_fc.sh (Qwen3 native-FC scaffold)
#      + serve_llama3_3_70b_awq_pinned.sh (determinism guards, fail-loud)
#      + A2.2 additions (--chat-template thinkoff, --seed 0, --max-num-seqs 1).
# Frozen stack (README_L40): vLLM 0.10.2 / torch 2.8.0+cu128 / transformers 4.55.2.
#
# SAFETY / DISCIPLINE (inherited):
#   * binds 127.0.0.1 ONLY (idea/52 §3 "no public egress on the experiment path").
#   * serves OFFLINE by default (HF_HUB_OFFLINE=1) so a pinned, already-downloaded
#     revision is used and no live @latest resolution / network fetch happens at serve.
#   * REVISION MUST BE PINNED. This script refuses to start on an unpinned revision —
#     it will NOT silently resolve a mutable tag. Pin MODEL_REVISION from the R5
#     download (record it in the G-d weights manifest).
#   * think-off is part of the measured scaffold and is fixed within the experiment.
#   * If vLLM 0.10.2 cannot load this model: STOP per A2.2 (bring a bump plan; bump
#     then re-run tool-probe + re-freeze). Do NOT upgrade silently mid-experiment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RUNTIME_ROOT="${RUNTIME_ROOT:-/ephemeral/ubuntu}"
VLLM_BIN="${VLLM_BIN:-$RUNTIME_ROOT/venvs/vllm/bin/vllm}"

# Model identity. A2.3/R5 downloads Qwen/Qwen3.8-27B-AWQ. VERIFY the exact repo at
# deploy (A2.2: "以 HF 上实际存在为准"; do NOT confuse with Qwen3.5/3.6-27B siblings).
MODEL_ID="${MODEL_ID:-Qwen/Qwen3.8-27B-AWQ}"
# REQUIRED unless MODEL_PATH is given. Fill from the downloaded snapshot (R5) — this
# is the commit hash under .../snapshots/<rev>/ ; it also goes in the G-d manifest.
MODEL_REVISION="${MODEL_REVISION:-}"
# Optional: serve an explicit local snapshot dir (most deterministic; mirrors the
# pinned-llama script). If set, --revision is not passed and MODEL_ID is ignored.
MODEL_PATH="${MODEL_PATH:-}"

# served-model-name MUST equal .env LLM_MODEL_ID (env.qwen3-8-27b.example) so G-a
# (/v1/models returns the pinned name) passes. A2.2 line 670/675.
SERVED_NAME="${SERVED_NAME:-qwen3-8-27b-awq}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
MAX_LEN="${MAX_LEN:-8192}"            # A2.2: 8192 start; raise to 16384 only if insufficient.
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"  # A2.2 range 0.88–0.96 (48G L40 has ample headroom at ~14–16GB AWQ).

# Chat template = the frozen think-off scaffold living beside this script (robust to
# clone location). A2.2 caveat: if Qwen3.8 ships a divergent chat_template, update
# this .jinja and RE-FREEZE it with the experiment.
CHAT_TEMPLATE="${CHAT_TEMPLATE:-$SCRIPT_DIR/qwen3_thinkoff.jinja}"

export HF_HOME="${HF_HOME:-$RUNTIME_ROOT/hf-cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$RUNTIME_ROOT/vllm-cache}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"   # serve from cache; no serve-time network.

mkdir -p "$HF_HOME" "$HUGGINGFACE_HUB_CACHE" "$VLLM_CACHE_ROOT"

if [[ ! -x "$VLLM_BIN" ]]; then
  echo "ERROR: vLLM executable not found: $VLLM_BIN (build the venv per the R5-R7 runbook)" >&2
  exit 1
fi
if [[ ! -f "$CHAT_TEMPLATE" ]]; then
  echo "ERROR: chat template not found: $CHAT_TEMPLATE" >&2
  exit 1
fi

# Resolve target: explicit local snapshot (preferred) or pinned repo@revision.
TARGET_ARGS=()
if [[ -n "$MODEL_PATH" ]]; then
  if [[ ! -f "$MODEL_PATH/config.json" ]]; then
    echo "ERROR: MODEL_PATH snapshot incomplete (no config.json): $MODEL_PATH" >&2
    exit 1
  fi
  TARGET_ARGS=( "$MODEL_PATH" )
  echo "serving local snapshot: $MODEL_PATH" >&2
else
  if [[ -z "$MODEL_REVISION" ]]; then
    echo "ERROR: MODEL_REVISION is not pinned. Refusing to serve a mutable/unpinned" >&2
    echo "       revision. Set MODEL_REVISION=<commit hash from the R5 download>," >&2
    echo "       or set MODEL_PATH=<.../snapshots/<rev>>. (A2.2 pinned-revision rule.)" >&2
    exit 2
  fi
  TARGET_ARGS=( "$MODEL_ID" --revision "$MODEL_REVISION" )
  echo "serving $MODEL_ID @ $MODEL_REVISION (offline=$HF_HUB_OFFLINE)" >&2
fi

exec "$VLLM_BIN" serve "${TARGET_ARGS[@]}" \
  --served-model-name "$SERVED_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --max-num-seqs 1 \
  --seed 0 \
  --dtype auto \
  --quantization awq \
  --enforce-eager \
  --disable-log-requests \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --reasoning-parser qwen3 \
  --chat-template "$CHAT_TEMPLATE"
