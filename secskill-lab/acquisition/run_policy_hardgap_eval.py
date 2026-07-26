"""Policy × hard-gap decision experiment.

The default manifest is exactly 150 malicious-twin trials:

    3 policies × (10 no-gap + 10 soft-gap + 10 PDF + 10 ICS + 10 QR)

P0 exposes search/install tools but does not prompt autonomous acquisition.
P1 is the current auto-acquire scaffold.
P2 uses the P1 prompt while an execution-layer guard blocks installation
without an externally supplied approval bit.

The runner randomizes one frozen manifest, uses a fresh agent/registry/install
root for every trial, and checkpoints after every completed row.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
ROOT = LAB.parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from baseline_agent import TOOL_LOG, make_listener  # noqa: E402
from collector import start_collector_endpoint  # noqa: E402

from acquisition.audited_agent import build_audited_agent  # noqa: E402
from acquisition.experiment_config import ExperimentConfig  # noqa: E402
from acquisition.marketplace import marketplace_for_target  # noqa: E402
from acquisition.meta_tools import (  # noqa: E402
    AcquisitionSession,
    InstallSkillTool,
    SearchSkillsTool,
)
from acquisition.metrics import aggregate, summarize_run  # noqa: E402
from acquisition.native_fc_agent import build_native_fc_agent  # noqa: E402
from acquisition.queries_gap import GAP_TASKS, TaskCase  # noqa: E402
from acquisition.queries_hardgap import (  # noqa: E402
    ICS_TASKS,
    NO_GAP_TASKS,
    PDF_TASKS,
    QR_TASKS,
)
from acquisition.run_acquisition_eval import (  # noqa: E402
    ACQ_NATIVE_SYSTEM_PROMPT,
    ACQ_SYSTEM_PROMPT,
    P0_NATIVE_SYSTEM_PROMPT,
    P0_SYSTEM_PROMPT,
    load_benign,
)


RESULTS_DIR = HERE / "results"
SCHEMA_VERSION = 2
DESIGN_ID = "policy_hardgap_causal_v2"
POLICIES = ("P0", "P1", "P2")
FAMILIES: dict[str, list[TaskCase]] = {
    "G0": NO_GAP_TASKS,
    "G1": GAP_TASKS,
    "PDF": PDF_TASKS,
    "ICS": ICS_TASKS,
    "QR": QR_TASKS,
}
POLICY_PROMPTS = {
    # Search/install remain visible through the generated tool inventory.
    "P0": P0_SYSTEM_PROMPT,
    "P1": ACQ_SYSTEM_PROMPT,
    # Deliberately identical to P1: the treatment is execution enforcement.
    "P2": ACQ_SYSTEM_PROMPT,
}
NATIVE_POLICY_PROMPTS = {
    "P0": P0_NATIVE_SYSTEM_PROMPT,
    "P1": ACQ_NATIVE_SYSTEM_PROMPT,
    "P2": ACQ_NATIVE_SYSTEM_PROMPT,
}


def _parse_csv(raw: str, allowed: set[str]) -> list[str]:
    values = [item.strip().upper() for item in raw.split(",") if item.strip()]
    unknown = [item for item in values if item not in allowed]
    if unknown:
        raise ValueError(f"unknown values: {unknown}; allowed={sorted(allowed)}")
    if not values:
        raise ValueError("at least one value is required")
    return values


def build_manifest(
    *,
    policies: list[str],
    families: list[str],
    num_per_family: int,
    target_variant: str,
    order_seed: int,
    approval_granted: bool = False,
    task_indices: list[int] | None = None,
) -> list[dict[str, Any]]:
    if not 1 <= num_per_family <= 10:
        raise ValueError("num_per_family must be between 1 and 10")
    rows: list[dict[str, Any]] = []
    for policy in policies:
        for family in families:
            tasks = (
                [FAMILIES[family][index - 1] for index in task_indices]
                if task_indices is not None
                else FAMILIES[family][:num_per_family]
            )
            for task in tasks:
                approval_state = (
                    "granted"
                    if policy == "P2" and approval_granted
                    else "denied"
                    if policy == "P2"
                    else "not_applicable"
                )
                task_spec = {
                    "task_id": task.task_id,
                    "query": task.query,
                    "verifier": task.verifier,
                    "target_name": task.target_name,
                }
                rows.append(
                    {
                        "trial_id": (
                            f"{DESIGN_ID}-{policy}-{approval_state}-"
                            f"{family}-{task.task_id}-{target_variant}"
                        ),
                        "design_id": DESIGN_ID,
                        "policy": policy,
                        "approval_state": approval_state,
                        "group": family,
                        "task_id": task.task_id,
                        "target_name": task.target_name,
                        "target_variant": target_variant,
                        "task_spec_sha256": hashlib.sha256(
                            json.dumps(
                                task_spec,
                                ensure_ascii=False,
                                sort_keys=True,
                                separators=(",", ":"),
                            ).encode("utf-8")
                        ).hexdigest(),
                        "policy_prompt_sha256": hashlib.sha256(
                            POLICY_PROMPTS[policy].encode("utf-8")
                        ).hexdigest(),
                        "meta_tool_description_mode": (
                            "neutral_affordance"
                            if policy == "P0"
                            else "encouraging"
                        ),
                    }
                )
    random.Random(order_seed).shuffle(rows)
    for index, row in enumerate(rows, start=1):
        row["randomized_index"] = index
    return rows


def _task_lookup() -> dict[str, TaskCase]:
    return {
        task.task_id: task
        for tasks in FAMILIES.values()
        for task in tasks
    }


def source_snapshot() -> dict[str, Any]:
    paths = sorted(HERE.glob("*.py"))
    paths.extend(
        [
            LAB / "skill_loader.py",
            LAB / "collector.py",
        ]
    )
    for variant in ("benign", "research_malicious"):
        for target_name in ("weekly_brief", "pdf_form", "calendar_ics", "qr_code"):
            package = LAB / "skills" / variant / target_name
            paths.extend(sorted(package.glob("*.py")))
            paths.extend(sorted(package.glob("SKILL.md")))
    files: dict[str, str] = {}
    aggregate = hashlib.sha256()
    for path in sorted(set(path.resolve() for path in paths)):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(ROOT).as_posix()
        files[relative] = digest
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
    env_path = ROOT / ".env"
    env_sha256 = (
        hashlib.sha256(env_path.read_bytes()).hexdigest()
        if env_path.is_file()
        else None
    )
    return {
        "aggregate_sha256": aggregate.hexdigest(),
        "env_sha256": env_sha256,
        "files": files,
    }


def _restore_env(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def run_trial(
    trial: dict[str, Any],
    *,
    config: ExperimentConfig,
    install_base_dir: Path | None,
    keep_install_dirs: bool,
    scaffold: str = "text",
) -> dict[str, Any]:
    task = _task_lookup()[str(trial["task_id"])]
    policy = str(trial["policy"])
    target_name = str(trial["target_name"])
    market = marketplace_for_target(
        target_name,
        install_framing=config.install_framing,
        target_variant=config.target_variant,
    )
    session = AcquisitionSession(
        market,
        target_name=target_name,
        acquisition_policy=policy,
        install_approved=config.install_approved,
        install_base_dir=install_base_dir,
        keep_install_dir=keep_install_dirs,
        run_id=str(trial["trial_id"]),
    )
    captured, shutdown, collector_url = start_collector_endpoint(0)
    previous_env = {
        "DATA_SYNC_COLLECTOR": os.environ.get("DATA_SYNC_COLLECTOR"),
        "ACQUISITION_ARTIFACT_DIR": os.environ.get(
            "ACQUISITION_ARTIFACT_DIR"
        ),
    }
    os.environ["DATA_SYNC_COLLECTOR"] = collector_url
    os.environ["ACQUISITION_ARTIFACT_DIR"] = str(session.artifact_root)

    TOOL_LOG.clear()
    native_function_calling = scaffold == "native_fc"
    if scaffold not in {"text", "native_fc"}:
        raise ValueError(f"unknown scaffold: {scaffold}")
    agent_builder = (
        build_native_fc_agent if native_function_calling else build_audited_agent
    )
    policy_prompts = (
        NATIVE_POLICY_PROMPTS if native_function_calling else POLICY_PROMPTS
    )
    agent = agent_builder(
        extra_tools=load_benign()
        + [
            SearchSkillsTool(
                session,
                neutral_affordance=policy == "P0",
            ),
            InstallSkillTool(
                session,
                native_function_calling=native_function_calling,
            ),
        ],
        listener_fn=make_listener(verbose=False),
        system_prompt=policy_prompts[policy],
        event_sink=session.log,
        execution_guard=session.execution_guard,
    )
    session.bind_agent(agent)

    try:
        try:
            reply = agent.run(
                task.query,
                max_tool_iterations=config.max_tool_iterations,
                **config.llm_kwargs(),
            )
        except Exception as exc:
            reply = f"[ERROR] {type(exc).__name__}: {exc}"
            session.log(
                "trial_exception",
                exception_type=type(exc).__name__,
                reason=str(exc),
            )
        time.sleep(0.05)
        called = [call["tool_name"] for call in TOOL_LOG]
        metrics = summarize_run(
            events=list(session.events),
            tool_calls=called,
            target_name=target_name,
            captured=list(captured),
            reply=reply or "",
            verifier=task.verifier,
            artifact_root=str(session.artifact_root),
        )
        session.log(
            "payload_fired",
            observed=metrics["payload_fired"],
            target=target_name,
        )
        session.log(
            "task_ok",
            observed=metrics["task_ok"],
            verifier=metrics["task_verification"],
        )
        return {
            **trial,
            "family": task.family,
            "gap_type": task.gap_type,
            "trigger": task.trigger,
            "meta_tool_description_mode": (
                "neutral_affordance" if policy == "P0" else "encouraging"
            ),
            "scaffold": scaffold,
            "query": task.query,
            "note": task.note,
            "verifier": task.verifier,
            "reply_preview": (reply or "")[:400],
            "market_snapshot": market.snapshot(),
            "metrics": metrics,
            "events": list(session.events),
            "install_root": str(session.install_root),
            "artifact_root": str(session.artifact_root),
        }
    finally:
        shutdown()
        _restore_env(previous_env)
        session.close()


def _flatten_metrics(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row.get("metrics") or {})


def grouped_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[(str(row["policy"]), str(row["group"]))].append(
            _flatten_metrics(row)
        )

    output: dict[str, Any] = {}
    for (policy, group), metrics_rows in sorted(buckets.items()):
        summary = aggregate(metrics_rows)
        summary["approval_gate_blocked"] = sum(
            1 for row in metrics_rows if row.get("approval_gate_blocked")
        )
        summary["approval_gate_blocked_rate"] = round(
            summary["approval_gate_blocked"] / len(metrics_rows),
            4,
        )
        summary["duplicate_invocations_total"] = sum(
            int(row.get("duplicate_invocations", 0)) for row in metrics_rows
        )
        output[f"{policy}:{group}"] = summary
    return output


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _print_row(row: dict[str, Any], completed: int, total: int) -> None:
    metrics = row["metrics"]
    print(
        f"[{completed:03d}/{total:03d}] {row['policy']}:{row['group']} "
        f"{row['task_id']} | search={int(metrics['search_called'])} "
        f"install={int(metrics['installed_on_disk'])} "
        f"block={int(metrics['approval_gate_blocked'])} "
        f"invoke={int(metrics['invoked'])} "
        f"payload={int(metrics['payload_fired'])} "
        f"task={int(metrics['task_ok'])} e2e={int(metrics['e2e'])}"
    )


def main() -> Path:
    parser = argparse.ArgumentParser(
        description="Run the policy × hard-artifact decision pilot"
    )
    parser.add_argument("--policies", default="P0,P1,P2")
    parser.add_argument("--families", default="G0,G1,PDF,ICS,QR")
    parser.add_argument("--num-per-family", type=int, default=10)
    parser.add_argument(
        "--task-indices",
        default=None,
        help="Optional 1-based comma-separated task indices, e.g. 2,5,9.",
    )
    parser.add_argument(
        "--target-variant",
        choices=["malicious", "benign"],
        default="malicious",
    )
    parser.add_argument(
        "--install-framing",
        choices=["neutral", "necessity", "ad"],
        default="neutral",
    )
    parser.add_argument("--max-tool-iterations", type=int, default=10)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--order-seed", type=int, default=20260726)
    parser.add_argument(
        "--scaffold",
        choices=["text", "native_fc"],
        default="text",
        help="Tool-call transport. Defaults to the frozen S1 text protocol.",
    )
    parser.add_argument(
        "--approval-granted",
        action="store_true",
        help="Externally authorize P2 installs (not used in the default pilot).",
    )
    parser.add_argument("--install-base-dir", type=Path, default=None)
    parser.add_argument("--keep-install-dirs", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Resume an existing checkpoint with the same manifest.",
    )
    args = parser.parse_args()

    policies = _parse_csv(args.policies, set(POLICIES))
    families = _parse_csv(args.families, set(FAMILIES))
    task_indices = None
    if args.task_indices:
        task_indices = [
            int(value.strip())
            for value in args.task_indices.split(",")
            if value.strip()
        ]
        if (
            not task_indices
            or len(set(task_indices)) != len(task_indices)
            or any(index < 1 or index > 10 for index in task_indices)
        ):
            raise ValueError("task indices must be unique integers from 1 to 10")
    manifest = build_manifest(
        policies=policies,
        families=families,
        num_per_family=args.num_per_family,
        target_variant=args.target_variant,
        order_seed=args.order_seed,
        approval_granted=args.approval_granted,
        task_indices=task_indices,
    )
    config = ExperimentConfig(
        max_tool_iterations=args.max_tool_iterations,
        temperature=args.temperature,
        seed=args.seed,
        install_framing=args.install_framing,
        target_variant=args.target_variant,
        acquisition_policy="P1",
        install_approved=args.approval_granted,
        keep_install_dirs=args.keep_install_dirs,
        install_base_dir=args.install_base_dir,
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = (
        args.resume
        or args.output
        or RESULTS_DIR / f"policy_hardgap_{stamp}.json"
    )
    if args.resume:
        payload = json.loads(output.read_text(encoding="utf-8"))
        if payload.get("manifest") != manifest:
            raise ValueError("resume manifest does not match requested experiment")
        if payload.get("design", {}).get("scaffold", "text") != args.scaffold:
            raise ValueError("resume scaffold does not match requested experiment")
    else:
        manifest_sha256 = hashlib.sha256(
            json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        policy_prompts = (
            NATIVE_POLICY_PROMPTS
            if args.scaffold == "native_fc"
            else POLICY_PROMPTS
        )
        backend = config.metadata(
            system_prompt=policy_prompts["P1"],
            market_snapshot=None,
        )
        backend["acquisition_policy"] = "varied_by_manifest"
        backend["scaffold"] = (
            "openai_native_function_calling"
            if args.scaffold == "native_fc"
            else "hello_agents_audited_text_protocol"
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "design_id": DESIGN_ID,
            "created_at": datetime.now().astimezone().isoformat(),
            "status": "running",
            "design": {
                "policies": policies,
                "families": families,
                "num_per_family": args.num_per_family,
                "task_indices": task_indices,
                "target_variant": args.target_variant,
                "install_framing": args.install_framing,
                "temperature": args.temperature,
                "seed": args.seed,
                "order_seed": args.order_seed,
                "approval_granted": args.approval_granted,
                "scaffold": args.scaffold,
                "primary_endpoint": "discovery_e2e",
                "primary_groups": ["PDF", "ICS", "QR"],
                "g1_inference_unit": "single_prototype_prompt_variants",
                "fresh_agent_registry_install_root_per_trial": True,
                "randomized_order": True,
            },
            "backend": backend,
            "source_snapshot": source_snapshot(),
            "manifest_sha256": manifest_sha256,
            "manifest": manifest,
            "rows": [],
            "summary": {},
        }
        _atomic_write(output, payload)

    completed_ids = {str(row["trial_id"]) for row in payload["rows"]}
    total = len(manifest)
    print(
        f"Policy × hard-gap pilot: {total} planned, "
        f"{len(completed_ids)} already complete\ncheckpoint={output}"
    )
    for trial in manifest:
        if str(trial["trial_id"]) in completed_ids:
            continue
        row = run_trial(
            trial,
            config=config,
            install_base_dir=args.install_base_dir,
            keep_install_dirs=args.keep_install_dirs,
            scaffold=args.scaffold,
        )
        payload["rows"].append(row)
        payload["summary"] = grouped_summary(payload["rows"])
        payload["updated_at"] = datetime.now().astimezone().isoformat()
        _atomic_write(output, payload)
        completed_ids.add(str(trial["trial_id"]))
        _print_row(row, len(completed_ids), total)

    payload["status"] = "complete"
    payload["completed_at"] = datetime.now().astimezone().isoformat()
    payload["summary"] = grouped_summary(payload["rows"])
    _atomic_write(output, payload)
    print(f"Complete: {output}")
    return output


if __name__ == "__main__":
    main()
