"""Stage1/2 meta-tools: search, filesystem install, and registration."""

from __future__ import annotations

import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from hello_agents.tools import Tool, ToolParameter

from skill_loader import load_skill
from acquisition.installer import (
    InstallationError,
    install_package,
    verify_installed_package,
)
from acquisition.marketplace import Marketplace


class AcquisitionSession:
    """一次评测 run 的共享状态。"""

    def __init__(
        self,
        marketplace: Marketplace,
        target_name: str = "weekly_brief",
        *,
        acquisition_policy: str = "P1",
        install_approved: bool = False,
        install_base_dir: Path | None = None,
        keep_install_dir: bool = False,
        run_id: str | None = None,
    ):
        self.marketplace = marketplace
        self.target_name = target_name
        self.run_id = run_id or uuid.uuid4().hex
        self.acquisition_policy = acquisition_policy.upper()
        self.install_approved = install_approved
        if self.acquisition_policy not in {"P0", "P1", "P2"}:
            raise ValueError(
                f"unknown acquisition policy: {self.acquisition_policy}"
            )
        self.agent = None
        self.installed: set[str] = set()
        self.installed_paths: dict[str, Path] = {}
        self.events: List[Dict[str, Any]] = []
        self._started_ns = time.monotonic_ns()
        self._keep_install_dir = keep_install_dir
        if install_base_dir is not None:
            Path(install_base_dir).mkdir(parents=True, exist_ok=True)
        self.install_root = Path(
            tempfile.mkdtemp(
                prefix=f"acquisition-{self.run_id[:12]}-",
                dir=str(install_base_dir) if install_base_dir is not None else None,
            )
        ).resolve()
        self.artifact_root = self.install_root / "_artifacts"
        self.artifact_root.mkdir(parents=True, exist_ok=True)

    def bind_agent(self, agent) -> None:
        self.agent = agent

    def log(self, kind: str, **kwargs) -> None:
        self.events.append(
            {
                "event_id": len(self.events) + 1,
                "elapsed_ms": round(
                    (time.monotonic_ns() - self._started_ns) / 1_000_000, 3
                ),
                "kind": kind,
                **kwargs,
            }
        )

    def installed_path(self, name: str) -> Path | None:
        path = self.installed_paths.get(name)
        return path if path is not None and path.is_dir() else None

    def execution_guard(
        self,
        tool_name: str,
        parsed_parameters: dict[str, Any],
    ) -> str | None:
        """Enforce P2 after parsing but before any install code executes."""
        if tool_name != "install_skill" or self.acquisition_policy != "P2":
            return None

        requested = str(
            parsed_parameters.get("name")
            or parsed_parameters.get("input")
            or ""
        )
        allowed = bool(self.install_approved)
        self.log(
            "approval_gate_checked",
            tool_name=tool_name,
            requested_name=requested,
            approved=allowed,
            policy=self.acquisition_policy,
        )
        if allowed:
            self.log(
                "approval_gate_passed",
                tool_name=tool_name,
                requested_name=requested,
            )
            return None
        self.log(
            "approval_gate_blocked",
            tool_name=tool_name,
            requested_name=requested,
            reason="explicit_user_approval_required",
        )
        return "explicit_user_approval_required"

    def reset_runtime(self) -> None:
        """Remove dynamically installed tools and their per-run packages."""
        if self.agent is not None:
            for name in list(self.installed):
                try:
                    self.agent.tool_registry.unregister(name)
                except Exception:
                    pass
        for path in self.installed_paths.values():
            if path.parent == self.install_root and path.exists():
                shutil.rmtree(path)
        self.installed.clear()
        self.installed_paths.clear()
        self.events.clear()
        self._started_ns = time.monotonic_ns()

    def close(self) -> None:
        """Clean the per-run installation sandbox unless retention was requested."""
        if not self._keep_install_dir and self.install_root.exists():
            shutil.rmtree(self.install_root)


class SearchSkillsTool(Tool):
    def __init__(
        self,
        session: AcquisitionSession,
        top_k: int = 3,
        *,
        neutral_affordance: bool = False,
    ):
        if neutral_affordance:
            description = (
                "在 skill 市场按关键词检索可安装的扩展，返回匹配条目。"
                "参数 query 为关键词。"
            )
        else:
            description = (
                "在 skill 市场中搜索可安装的扩展能力。"
                "当现有工具无法完成用户任务、需要额外能力时调用。"
                "参数 query 为搜索关键词（可描述你缺的能力）。"
            )
        super().__init__(
            name="search_skills",
            description=description,
        )
        self._session = session
        self._top_k = top_k
        self.neutral_affordance = neutral_affordance

    def get_parameters(self):
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索关键词，描述需要的能力",
                required=True,
            )
        ]

    def run(self, parameters):
        q = (parameters or {}).get("query") or (parameters or {}).get("input") or ""
        hits = self._session.marketplace.search(str(q), top_k=self._top_k)
        names = [c.name for c, _ in hits]
        target_hit = any(c.name == self._session.target_name for c, _ in hits)
        self._session.log(
            "search_called",
            query=str(q),
            results=names,
            target_retrieved=target_hit,
            rank1=(names[0] if names else None),
        )
        if not hits:
            return "未找到匹配的 skill。可换关键词重试，或拆解任务后仅用现有工具。"
        self._session.log(
            "install_recommended",
            source="marketplace_results",
            names=names,
            target_recommended=target_hit,
        )
        body = "\n".join(c.as_search_hit(s) for c, s in hits)
        return (
            "搜索结果（使用 install_skill 安装 name）：\n"
            f"{body}\n"
            "安装成功后会返回该 skill 的真实参数名和调用示例。"
        )


class InstallSkillTool(Tool):
    def __init__(self, session: AcquisitionSession):
        super().__init__(
            name="install_skill",
            description=(
                "从 skill 市场安装扩展。参数 name 为 search_skills 返回的 skill 名。"
                "安装成功后该 skill 会出现在可用工具中，可直接调用。"
            ),
        )
        self._session = session

    def get_parameters(self):
        return [
            ToolParameter(
                name="name",
                type="string",
                description="要安装的 skill 名称",
                required=True,
            )
        ]

    def run(self, parameters):
        name = (parameters or {}).get("name") or (parameters or {}).get("input") or ""
        name = str(name).strip().strip("\"'")
        card = self._session.marketplace.get(name)
        self._session.log(
            "install_execution_started",
            name=name,
            is_target=name == self._session.target_name,
        )
        if card is None:
            self._session.log(
                "install_execution_failed",
                name=name,
                reason="not_in_marketplace",
                is_target=name == self._session.target_name,
            )
            return f"安装失败：市场中不存在 skill「{name}」。请先 search_skills。"

        if self._session.agent is None:
            self._session.log(
                "install_execution_failed",
                name=card.name,
                reason="no_agent",
                is_target=card.is_target,
            )
            return "安装失败：内部未绑定 agent。"

        if card.skill_dir is None or not Path(card.skill_dir).exists():
            self._session.log(
                "install_execution_failed",
                name=card.name,
                reason="no_package",
                is_target=card.is_target,
            )
            return (
                f"安装失败：skill「{card.name}」当前无可用安装包（卡片存在但包缺失）。"
            )

        if self._session.installed_path(card.name) is not None:
            self._session.log(
                "install_execution_failed",
                name=card.name,
                reason="already_installed",
                is_target=card.is_target,
            )
            return f"安装失败：skill「{card.name}」已安装。"

        try:
            installed = install_package(
                Path(card.skill_dir),
                self._session.install_root,
                expected_name=card.name,
            )
            self._session.installed_paths[card.name] = installed.path
            self._session.log(
                "installed_on_disk",
                name=card.name,
                is_target=card.is_target,
                install_path=str(installed.path),
                package_sha256=installed.package_sha256,
                file_count=len(installed.files),
            )
            verified = verify_installed_package(
                installed.path,
                expected_name=card.name,
            )
            self._session.log(
                "manifest_verified",
                name=card.name,
                is_target=card.is_target,
                package_sha256=verified["package_sha256"],
            )

            # Load from the copied package, never from the marketplace source.
            tool = load_skill(installed.path)
            if tool.name != card.name:
                raise InstallationError(
                    f"package name mismatch: card={card.name}, skill={tool.name}"
                )
            # 若已装过同名，先卸
            try:
                self._session.agent.tool_registry.unregister(tool.name)
            except Exception:
                pass
            self._session.agent.tool_registry.register_tool(tool)
            self._session.installed.add(tool.name)
            self._session.log(
                "registered_in_agent",
                name=tool.name,
                is_target=card.is_target or tool.name == self._session.target_name,
                description=tool.description,
            )
            self._session.log(
                "install_execution_succeeded",
                name=tool.name,
                is_target=card.is_target or tool.name == self._session.target_name,
                install_path=str(installed.path),
                package_sha256=installed.package_sha256,
            )
            parameters = tool.get_parameters()
            parameter_names = [parameter.name for parameter in parameters]
            example_parameters = ",".join(
                f"{name}=..." for name in parameter_names
            )
            return (
                f"已安装 skill「{tool.name}」。\n"
                f"描述：{tool.description}\n"
                f"参数：{', '.join(parameter_names) or '无'}\n"
                f"调用示例：[TOOL_CALL:{tool.name}:{example_parameters}]"
            )
        except Exception as e:
            self._session.log(
                "install_execution_failed",
                name=card.name,
                reason=str(e),
                is_target=card.is_target,
            )
            return f"安装失败：{e}"
