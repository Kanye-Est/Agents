#!/usr/bin/env bash
# Optional 2nd model for multi-model paper table.
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-$HOME/models/qwen2.5-72b-instruct-awq}"
SERVED_NAME="${SERVED_NAME:-qwen2.5-72b-instruct}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8001}"
MAX_LEN="${MAX_LEN:-8192}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"

if [[ ! -d "$MODEL_PATH" ]]; then
  echo "ERROR: MODEL_PATH does not exist: $MODEL_PATH"
  exit 1
fi

python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_PATH" \
  --served-model-name "$SERVED_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --dtype auto \
  --trust-remote-code
