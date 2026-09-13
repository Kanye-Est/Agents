#!/usr/bin/env bash
# Pinned Qwen3-32B-AWQ backend: native function calling, thinking OFF.
# Spec: idea/52 Amendment 5; build-out only (run=0).
# Guard scaffold: serve_qwen3_8_27b_awq_native_fc.sh at 3ef65bb.
# Frozen stack: vLLM 0.10.2 / torch 2.8.0+cu128 / transformers 4.55.2.
#
# An unset MODEL_REVISION keeps the README_L40 pin. An explicitly empty value
# fails with exit 2 for repo loading; MODEL_PATH selects a local snapshot instead.
# HOST=127.0.0.1 and HF_HUB_OFFLINE=1 are overridable defaults. G-e must verify
# loopback-only listeners with ss -tlnp; these defaults do not enforce isolation.
# Download the pinned snapshot before serving offline. Keep think-off fixed and
# do not silently upgrade the frozen stack within an experiment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RUNTIME_ROOT="${RUNTIME_ROOT:-/ephemeral/ubuntu}"
VLLM_BIN="${VLLM_BIN:-$RUNTIME_ROOT/venvs/vllm/bin/vllm}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-32B-AWQ}"
# Use '-' rather than ':-' so an explicit empty value reaches the guard below.
MODEL_REVISION="${MODEL_REVISION-0499c3ac83fdef8810b907a23894ba91e95eddd8}"
# A local snapshot is used directly, without MODEL_ID or --revision.
MODEL_PATH="${MODEL_PATH:-}"
# Must match client LLM_MODEL_ID and the G-a /v1/models result.
SERVED_NAME="${SERVED_NAME:-qwen3-32b-awq-native-fc}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
MAX_LEN="${MAX_LEN:-8192}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.88}"
CHAT_TEMPLATE="${CHAT_TEMPLATE:-$SCRIPT_DIR/qwen3_thinkoff.jinja}"

export HF_HOME="${HF_HOME:-$RUNTIME_ROOT/hf-cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$RUNTIME_ROOT/vllm-cache}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"

if [[ ! -x "$VLLM_BIN" ]]; then
  echo "ERROR: vLLM executable not found: $VLLM_BIN" >&2
  exit 1
fi
if [[ ! -f "$CHAT_TEMPLATE" ]]; then
  echo "ERROR: chat template not found: $CHAT_TEMPLATE" >&2
  exit 1
fi

TARGET_ARGS=()
if [[ -n "$MODEL_PATH" ]]; then
  if [[ ! -f "$MODEL_PATH/config.json" ]]; then
    echo "ERROR: MODEL_PATH snapshot incomplete (no config.json): $MODEL_PATH" >&2
    exit 1
  fi
  TARGET_ARGS=( "$MODEL_PATH" )
  echo "serving local snapshot: $MODEL_PATH (offline=$HF_HUB_OFFLINE)" >&2
else
  if [[ -z "$MODEL_REVISION" ]]; then
    echo "ERROR: MODEL_REVISION is explicitly empty. Refusing repo loading without a pin." >&2
    echo "       Unset it to use the frozen README_L40 revision, set a commit hash," >&2
    echo "       or set MODEL_PATH to a downloaded local snapshot." >&2
    exit 2
  fi
  TARGET_ARGS=( "$MODEL_ID" --revision "$MODEL_REVISION" )
  echo "serving $MODEL_ID @ $MODEL_REVISION (offline=$HF_HUB_OFFLINE)" >&2
fi

mkdir -p "$HF_HOME" "$HUGGINGFACE_HUB_CACHE" "$VLLM_CACHE_ROOT"

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
