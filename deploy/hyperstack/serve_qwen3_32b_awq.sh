#!/usr/bin/env bash
# Single-L40 vLLM server for the acquisition pilot.
set -euo pipefail

RUNTIME_ROOT="${RUNTIME_ROOT:-/ephemeral/ubuntu}"
VLLM_BIN="${VLLM_BIN:-$RUNTIME_ROOT/venvs/vllm/bin/vllm}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-32B-AWQ}"
MODEL_REVISION="${MODEL_REVISION:-0499c3ac83fdef8810b907a23894ba91e95eddd8}"
SERVED_NAME="${SERVED_NAME:-qwen3-32b-awq}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
MAX_LEN="${MAX_LEN:-8192}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.88}"

export HF_HOME="${HF_HOME:-$RUNTIME_ROOT/hf-cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$RUNTIME_ROOT/vllm-cache}"

mkdir -p "$HF_HOME" "$HUGGINGFACE_HUB_CACHE" "$VLLM_CACHE_ROOT"

if [[ ! -x "$VLLM_BIN" ]]; then
  echo "ERROR: vLLM executable not found: $VLLM_BIN" >&2
  exit 1
fi

exec "$VLLM_BIN" serve "$MODEL_ID" \
  --revision "$MODEL_REVISION" \
  --served-model-name "$SERVED_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --dtype auto \
  --quantization awq
