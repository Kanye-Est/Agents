#!/usr/bin/env bash
# Pinned single-L40 server for the Track-A M2 × S1 cell.
set -euo pipefail

RUNTIME_ROOT="${RUNTIME_ROOT:-/ephemeral/ubuntu}"
VLLM_BIN="${VLLM_BIN:-$RUNTIME_ROOT/venvs/vllm/bin/vllm}"
MODEL_REVISION="${MODEL_REVISION:-64d255621f40b42adaf6d1f32a47e1d4534c0f14}"
MODEL_PATH="${MODEL_PATH:-$RUNTIME_ROOT/hf-cache/models--casperhansen--llama-3.3-70b-instruct-awq/snapshots/$MODEL_REVISION}"
SERVED_NAME="${SERVED_NAME:-llama-3.3-70b-instruct-awq}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
MAX_LEN="${MAX_LEN:-8192}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.96}"

export HF_HOME="${HF_HOME:-$RUNTIME_ROOT/hf-cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$HF_HOME/hub}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$RUNTIME_ROOT/vllm-cache}"

if [[ ! -x "$VLLM_BIN" ]]; then
  echo "ERROR: vLLM executable not found: $VLLM_BIN" >&2
  exit 1
fi
if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  echo "ERROR: pinned model snapshot is incomplete: $MODEL_PATH" >&2
  exit 1
fi

exec "$VLLM_BIN" serve "$MODEL_PATH" \
  --served-model-name "$SERVED_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --max-num-seqs 1 \
  --dtype auto \
  --quantization awq \
  --enforce-eager \
  --disable-log-requests
