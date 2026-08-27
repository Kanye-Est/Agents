# L40 acquisition-pilot runtime

The current verified VM layout is rooted at `/ephemeral/ubuntu` so model
weights, environments, logs, and results do not consume the small root disk.

## Verified stack

```text
GPU: NVIDIA L40
Driver: 570.195.03
vLLM: 0.10.2
PyTorch: 2.8.0+cu128
Transformers: 4.55.2
Model: Qwen/Qwen3-32B-AWQ
Model revision: 0499c3ac83fdef8810b907a23894ba91e95eddd8
Served name: qwen3-32b-awq
Endpoint: http://127.0.0.1:8000/v1
```

Do not upgrade these independently during a frozen experiment. vLLM 0.10.2
ships CUDA 12.8 binaries. Its unconstrained `transformers>=4.55.2` dependency
can resolve to an incompatible Transformers 5.x release, so Transformers is
explicitly pinned to 4.55.2.

Exact resolved environments are recorded remotely in:

```text
/ephemeral/ubuntu/logs/vllm-freeze.txt
/ephemeral/ubuntu/logs/secskill-freeze.txt
```

Preserved repository copies:

```text
deploy/hyperstack/vllm-freeze.l40.txt
deploy/hyperstack/secskill-freeze.l40.txt
```

Hugging Face files live in `/ephemeral/ubuntu/hf-cache`, and future vLLM
compile artifacts live in `/ephemeral/ubuntu/vllm-cache`.

## Start

```bash
cd /ephemeral/ubuntu/src/hello-agents-lab
nohup ./deploy/hyperstack/serve_qwen3_32b_awq.sh \
  > /ephemeral/ubuntu/logs/vllm-qwen3-32b-awq.log 2>&1 < /dev/null &
```

The service binds to loopback only. `Qwen3-32B-AWQ` is public, so a Hugging
Face token is not required; anonymous downloads may merely have lower rate
limits.

The project `.env` should be copied from
`deploy/hyperstack/env.qwen3-32b-awq.example`. It disables Qwen3 thinking mode
per request through `chat_template_kwargs`. That setting is part of the
measured scaffold and must remain fixed within an experiment.

## Hard-artifact verifier dependencies

The policy × hard-gap pilot also needs independently frozen PDF/QR packages:

```bash
/ephemeral/ubuntu/venvs/secskill/bin/python -m pip install \
  -r deploy/hyperstack/requirements-artifacts.txt
```

These packages generate QR PNG files and independently parse PDF/QR outputs.
The iCalendar verifier uses the Python standard library. Freeze the resolved
environment again after installation and retain it with the experiment.
