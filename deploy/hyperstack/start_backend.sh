#!/usr/bin/env bash
# Canary backend: Qwen3-32B-AWQ, native function calling, thinking disabled by default.
# Protocol: idea/48 Amendment 4
set -euo pipefail
R=/ephemeral/ubuntu
export HF_HOME=$R/hf-cache
export HUGGINGFACE_HUB_CACHE=$R/hf-cache/hub
export VLLM_CACHE_ROOT=$R/vllm-cache
exec "$R/venvs/vllm/bin/vllm" serve Qwen/Qwen3-32B-AWQ \
  --revision 0499c3ac83fdef8810b907a23894ba91e95eddd8 \
  --served-model-name qwen3-32b-awq-native-fc \
  --host 127.0.0.1 --port 8000 --max-model-len 8192 \
  --gpu-memory-utilization 0.88 --dtype auto --quantization awq \
  --enable-auto-tool-choice --tool-call-parser hermes --reasoning-parser qwen3 \
  --chat-template "$R/deploy/qwen3_thinkoff.jinja"
