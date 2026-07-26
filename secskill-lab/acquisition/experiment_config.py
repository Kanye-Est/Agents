"""Serializable configuration for acquisition evaluation runs."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExperimentConfig:
    max_tool_iterations: int = 10
    temperature: float = 0.0
    seed: int | None = None
    install_framing: str = "neutral"
    target_variant: str = "malicious"
    acquisition_policy: str = "P1"
    install_approved: bool = False
    keep_install_dirs: bool = False
    install_base_dir: Path | None = None

    def __post_init__(self) -> None:
        if self.max_tool_iterations < 0:
            raise ValueError("max_tool_iterations must be non-negative")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if self.install_framing not in {"neutral", "necessity", "ad"}:
            raise ValueError(f"invalid install_framing: {self.install_framing}")
        if self.target_variant not in {"malicious", "benign"}:
            raise ValueError(f"invalid target_variant: {self.target_variant}")
        if self.acquisition_policy not in {"P0", "P1", "P2"}:
            raise ValueError(
                f"invalid acquisition_policy: {self.acquisition_policy}"
            )

    def metadata(
        self, *, system_prompt: str, market_snapshot: dict | None = None
    ) -> dict:
        raw = asdict(self)
        raw["install_base_dir"] = (
            str(self.install_base_dir.resolve())
            if self.install_base_dir is not None
            else None
        )
        raw.update(
            {
                "model_id": os.getenv("LLM_MODEL_ID", "unknown"),
                "model_revision": os.getenv("LLM_MODEL_REVISION", "unknown"),
                "llm_backend": os.getenv("LLM_BACKEND", "unknown"),
                "llm_backend_version": os.getenv(
                    "LLM_BACKEND_VERSION", "unknown"
                ),
                "llm_quantization": os.getenv("LLM_QUANTIZATION", "unknown"),
                "llm_dtype": os.getenv("LLM_DTYPE", "unknown"),
                "llm_base_url_kind": _base_url_kind(os.getenv("LLM_BASE_URL", "")),
                "prompt_sha256": hashlib.sha256(
                    system_prompt.encode("utf-8")
                ).hexdigest(),
                "runner_schema_version": 2,
                "scaffold": "hello_agents_audited_text_protocol",
                "hello_agents_version": _package_version("hello-agents"),
                "python_version": platform.python_version(),
                "chat_template_kwargs": _chat_template_kwargs(),
            }
        )
        if market_snapshot is not None:
            raw["market_snapshot_sha256"] = market_snapshot.get("sha256")
            raw["market_visible_sha256"] = market_snapshot.get("visible_sha256")
        return raw

    def llm_kwargs(self) -> dict:
        kwargs = {"temperature": self.temperature}
        if self.seed is not None:
            kwargs["seed"] = self.seed
        return kwargs


def _base_url_kind(base_url: str) -> str:
    """Record backend class without leaking a full private endpoint."""
    lowered = (base_url or "").lower()
    if "127.0.0.1" in lowered or "localhost" in lowered:
        return "local"
    if not lowered:
        return "unknown"
    if "deepseek" in lowered:
        return "deepseek"
    if "dashscope" in lowered:
        return "dashscope"
    if "openai" in lowered:
        return "openai"
    return "remote_custom"


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _chat_template_kwargs() -> dict | None:
    raw = os.getenv("LLM_CHAT_TEMPLATE_KWARGS", "").strip()
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"configuration_error": "invalid JSON"}
    return value if isinstance(value, dict) else {"configuration_error": "not an object"}
