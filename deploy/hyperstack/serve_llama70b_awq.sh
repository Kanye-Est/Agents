#!/usr/bin/env bash
# Start Llama-3.3-70B-Instruct (AWQ 4-bit) with vLLM.
# Fits a single 48GB GPU (A6000/L40) with max_model_len=8192; 80GB is more comfortable.
# Usage:
#   export MODEL_PATH=~/models/llama-3.3-70b-instruct-awq
#   bash deploy/hyperstack/serve_llama70b_awq.sh
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-$HOME/models/llama-3.3-70b-instruct-awq}"
SERVED_NAME="${SERVED_NAME:-llama-3.3-70b-instruct}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
# 48GB cards: keep 8192. If OOM, export MAX_LEN=4096
MAX_LEN="${MAX_LEN:-8192}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"

if [[ ! -d "$MODEL_PATH" ]]; then
  echo "ERROR: MODEL_PATH does not exist: $MODEL_PATH"
  echo "Download an AWQ build of Llama-3.3-70B-Instruct from HuggingFace first, e.g.:"
  echo "  huggingface-cli download <org>/Llama-3.3-70B-Instruct-AWQ --local-dir $MODEL_PATH"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: python not found (activate your venv first)"
  exit 1
fi

echo "Starting vLLM"
echo "  model:  $MODEL_PATH"
echo "  name:   $SERVED_NAME"
echo "  bind:   $HOST:$PORT"
echo "  max_len:$MAX_LEN"

# shellcheck disable=SC2086
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_PATH" \
  --served-model-name "$SERVED_NAME" \
  --host "$HOST" \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --gpu-memory-utilization "$GPU_MEM_UTIL" \
  --dtype auto \
  --trust-remote-code
