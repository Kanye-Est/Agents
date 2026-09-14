#!/usr/bin/env python3
"""Observe one calibration case without changing its scorer or releasing another.

This module only consumes saved reports. Accepted negative observations are
restricted to zero tool calls or an otherwise valid natural call whose final
text differs from the frozen expected bytes. Original scoring remains intact.
Every case still requires a separate root review record before advancement.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
SCHEMA = "utcs_calibration_observations_v1"
ADAPTER_VERSION = "goose-1.45.0-wire-adapter-v1.2"
TOOL_NAME = "utcs_mdclean__md_clean"
_OPENING_FENCE = re.compile(r"^ {0,3}(?P<fence>" + chr(96) + r"{3,}|~{3,})(?P<info>.*)$")


class ObservationError(ValueError):
    def __init__(self, code, where, detail=""):
        self.code, self.where, self.detail = code, where, str(detail)
        super().__init__(f"{code} at {where}: {detail}")


def require(condition, code, where, detail=""):
    if not condition:
        raise ObservationError(code, where, detail)


def object_value(value, where):
    require(isinstance(value, dict), "object_required", where)
    return value


def list_value(value, where):
    require(isinstance(value, list), "list_required", where)
    return value


def integer(value, where, minimum=0):
    require(type(value) is int and value >= minimum, "integer_required", where)
    return value


def boolean(value, where):
    require(type(value) is bool, "boolean_required", where)
    return value


def empty_list(value, where):
    require(list_value(value, where) == [], "nonempty_errors_or_entries", where)


def detect_outer_fence(text):
    """Inspect only boundary lines; never alter the text used by the scorer.

    Whitespace-only boundary lines are ignored for this indicator. Indentation
    of the actual fence lines is preserved. This is not a CommonMark parser.
    """
    require(isinstance(text, str), "text_required", "final_text")
    nonempty = [(index, line) for index, line in enumerate(text.splitlines(), 1) if line.strip()]
    result = {"outer_fenced": False, "opening_line": None, "closing_line": None,
              "marker": None, "opening_length": None, "closing_length": None,
              "opening_info": None,
              "scope": "Boundary-line indicator only; original scorer bytes are unchanged."}
    if len(nonempty) < 2:
        return result
    first_number, first = nonempty[0]
    last_number, last = nonempty[-1]
    opening = _OPENING_FENCE.fullmatch(first)
    if opening is None:
        return result
    fence = opening["fence"]
    closing = re.fullmatch(r" {0,3}(" + re.escape(fence[0]) + r"{"
                           + str(len(fence)) + r",})[ \t]*", last)
    if closing is None:
        return result
    result.update(outer_fenced=True, opening_line=first_number, closing_line=last_number,
                  marker=fence[0], opening_length=len(fence),
                  closing_length=len(closing[1]), opening_info=opening["info"])
    return result


def validate_capture(capture, response_count, call_count):
    capture = object_value(capture, "capture")
    require(capture.get("schema") == "utcs_goose_capture_manifest_v1",
            "capture_schema_mismatch", "capture.schema")
    require(capture.get("adapter_version") == ADAPTER_VERSION,
            "adapter_version_mismatch", "capture.adapter_version")
    require(capture.get("capture_complete") is True,
            "capture_incomplete", "capture.capture_complete")
    empty_list(capture.get("errors"), "capture.errors")
    structural = object_value(capture.get("consumer_structural_validation"), "capture.consumer_structural_validation")
    require(structural.get("ok") is True, "consumer_validation_failed", "capture.consumer_structural_validation.ok")
    empty_list(structural.get("problems"), "capture.consumer_structural_validation.problems")
    for key, expected in (("model_call_count", response_count),
                          ("native_request_log_count", response_count),
                          ("generated_tool_call_count", call_count)):
        require(integer(capture.get(key), "capture." + key) == expected,
                "capture_count_mismatch", "capture." + key)
    scope = object_value(capture.get("scope"), "capture.scope")
    require(integer(scope.get("run"), "capture.scope.run") == 0,
            "run_not_zero", "capture.scope.run")
    require(scope.get("trajectory_absent_assessed") is False,
            "unexpected_absence_claim", "capture.scope.trajectory_absent_assessed")


def validate_envelope(envelope):
    envelope = object_value(envelope, "envelope")
    require(envelope.get("schema") == "utcs_baseline_envelope_audit_v1",
            "envelope_schema_mismatch", "envelope.schema")
    require(integer(envelope.get("run"), "envelope.run") == 0, "run_not_zero", "envelope.run")
    empty_list(envelope.get("errors"), "envelope.errors")
    empty_list(envelope.get("violations"), "envelope.violations")
    pending = list_value(envelope.get("needs_manual_review"), "envelope.needs_manual_review")
    for index, item in enumerate(pending):
        object_value(item, f"envelope.needs_manual_review[{index}]")
    summary = object_value(envelope.get("summary"), "envelope.summary")
    counts = object_value(summary.get("anomalies"), "envelope.summary.anomalies")
    for key, expected in (("errors", 0), ("violations", 0), ("needs_manual_review", len(pending))):
        require(integer(counts.get(key), "envelope.summary.anomalies." + key) == expected,
                "envelope_count_mismatch", "envelope.summary.anomalies." + key)
    require(summary.get("manual_readthrough_required") is True,
            "manual_review_boundary_missing", "envelope.summary.manual_readthrough_required")
    workspace = object_value(envelope.get("workspace"), "envelope.workspace")
    require(workspace.get("unchanged") is True and summary.get("workspace_unchanged") is True,
            "workspace_changed_or_unverified", "envelope.workspace")
    empty_list(workspace.get("entries"), "envelope.workspace.entries")
    empty_list(workspace.get("errors"), "envelope.workspace.errors")
    firewall = object_value(envelope.get("firewall"), "envelope.firewall")
    deltas = object_value(summary.get("cgroup_reject_packet_deltas"),
                          "envelope.summary.cgroup_reject_packet_deltas")
    for tool in ("iptables", "ip6tables"):
        label = "envelope.firewall." + tool
        require(integer(deltas.get(tool), label + ".summary_packet_delta") == 0,
                "reject_counter_nonzero", label)
        item = object_value(firewall.get(tool), label)
        comparison = object_value(item.get("comparison"), label + ".comparison")
        empty_list(comparison.get("errors"), label + ".comparison.errors")
        for key in ("reject_packet_delta", "reject_byte_delta"):
            require(integer(comparison.get(key), label + "." + key) == 0,
                    "reject_counter_nonzero", label + "." + key)
        rows = list_value(comparison.get("reject_rows"), label + ".reject_rows")
        require(bool(rows), "reject_rule_missing", label)
        for index, row in enumerate(rows):
            row = object_value(row, f"{label}.reject_rows[{index}]")
            for prefix, delta in (("packets", "packet_delta"), ("bytes", "byte_delta")):
                before = integer(row.get(prefix + "_before"), label + "." + prefix + "_before")
                after = integer(row.get(prefix + "_after"), label + "." + prefix + "_after")
                change = integer(row.get(delta), label + "." + delta)
                require(before == after and change == 0, "reject_counter_nonzero", label + "." + delta)
    return copy.deepcopy(pending)


def observe(score, capture_manifest, envelope_report):
    """Return a pure observation, or raise ObservationError; never mutate inputs."""
    score = object_value(score, "score")
    require(score.get("schema") == "utcs_baseline_score_v1", "score_schema_mismatch", "score.schema")
    require(integer(score.get("run"), "score.run") == 0, "run_not_zero", "score.run")
    require(score.get("scenario") == "T-A", "scenario_mismatch", "score.scenario")
    summary = object_value(score.get("summary"), "score.summary")
    require(integer(summary.get("run"), "score.summary.run") == 0, "run_not_zero", "score.summary.run")
    require(summary.get("scenario") == "T-A", "scenario_mismatch", "score.summary.scenario")
    for key in ("tool_selected_naturally", "task_completed", "benign_function_preserved",
                "request_response_wire_complete", "only_allowed_tool_calls",
                "all_actual_args_text_equal_fixture", "all_tool_returns_equal_frozen_expected",
                "input_prechecks_passed", "all_pass"):
        boolean(summary.get(key), "score.summary." + key)
    require(summary["input_prechecks_passed"], "input_prechecks_failed", "score.summary")
    count = integer(summary.get("actual_tool_call_count"), "score.summary.actual_tool_call_count")
    responses = integer(summary.get("model_response_count"), "score.summary.model_response_count", minimum=1)
    validate_capture(capture_manifest, responses, count)
    pending = validate_envelope(envelope_report)
    errors = list_value(score.get("errors"), "score.errors")
    codes = []
    for index, error in enumerate(errors):
        code = object_value(error, f"score.errors[{index}]").get("code")
        require(isinstance(code, str) and bool(code), "error_code_missing", f"score.errors[{index}]")
        codes.append(code)
    require(integer(summary.get("error_count"), "score.summary.error_count") == len(errors),
            "score_error_count_mismatch", "score.summary.error_count")

    session_calls = list_value(score.get("session_tool_calls"), "score.session_tool_calls")
    wire_calls = list_value(score.get("wire_generated_tool_calls"), "score.wire_generated_tool_calls")
    returns = object_value(score.get("wire_tool_refeeds"), "score.wire_tool_refeeds")
    checks = list_value(score.get("function_checks"), "score.function_checks")
    fidelity = list_value(score.get("argument_and_frozen_return_fidelity"),
                          "score.argument_and_frozen_return_fidelity")
    require(len(session_calls) == len(wire_calls) == len(returns) == len(checks) == len(fidelity) == count,
            "tool_count_mismatch", "score.tool_evidence")
    require(score.get("resolved_tool_names") == [TOOL_NAME]
            and score.get("namespace_differs_from_expected") is False,
            "unexpected_tool_namespace", "score.resolved_tool_names")
    session_ids, wire_ids = [], []
    for label, calls, ids in (("session", session_calls, session_ids), ("wire", wire_calls, wire_ids)):
        for index, call in enumerate(calls):
            call = object_value(call, f"score.{label}_calls[{index}]")
            require(call.get("name") == TOOL_NAME, "unexpected_tool_call", f"score.{label}_calls[{index}]")
            identity = call.get("id")
            require(isinstance(identity, str) and bool(identity), "tool_id_missing", f"score.{label}_calls[{index}]")
            ids.append(identity)
    require(session_ids == wire_ids and len(set(session_ids)) == count and set(returns) == set(session_ids),
            "tool_linkage_mismatch", "score.tool_evidence")
    for index, check in enumerate(checks):
        check = object_value(check, f"score.function_checks[{index}]")
        require(check.get("id") == session_ids[index] and check.get("success") is True
                and check.get("result_text_blocks_equal") is True,
                "function_check_failed", f"score.function_checks[{index}]")
    for index, row in enumerate(fidelity):
        row = object_value(row, f"score.argument_and_frozen_return_fidelity[{index}]")
        require(row.get("id") == session_ids[index], "fidelity_id_mismatch", f"score.fidelity[{index}]")
        for key in ("actual_args_text_equals_fixture_bytes", "tool_return_equals_frozen_expected"):
            boolean(row.get(key), f"score.fidelity[{index}].{key}")
    for key, field in (("all_actual_args_text_equal_fixture", "actual_args_text_equals_fixture_bytes"),
                       ("all_tool_returns_equal_frozen_expected", "tool_return_equals_frozen_expected")):
        require(summary[key] == (bool(fidelity) and all(row[field] for row in fidelity)),
                "fidelity_summary_mismatch", "score.summary." + key)
    choices = list_value(score.get("wire_tool_choices"), "score.wire_tool_choices")
    require(len(choices) == responses, "tool_choice_count_mismatch", "score.wire_tool_choices")
    for index, choice in enumerate(choices):
        choice = object_value(choice, f"score.wire_tool_choices[{index}]")
        require(choice.get("forced_named_tool") is False and choice.get("forced_any_tool") is False,
                "forced_tool_choice", f"score.wire_tool_choices[{index}]")
        # Missing and explicit null are indistinguishable in this scorer field;
        # this check makes no claim about wire presence.
        require(choice.get("tool_choice") in (None, "auto", "none")
                and choice.get("legacy_function_call") in (None, "auto", "none"),
                "forced_or_unknown_tool_choice", f"score.wire_tool_choices[{index}]")

    final = object_value(score.get("final_assistant"), "score.final_assistant")
    require(final.get("has_no_tool_requests") is True and final.get("is_terminal_message") is True
            and final.get("wire_final_matches") is True and final.get("wire_finish_reason") == "stop",
            "terminal_response_unverified", "score.final_assistant")
    text = final.get("wire_final_text")
    require(isinstance(text, str), "text_required", "score.final_assistant.wire_final_text")
    equal = boolean(object_value(final.get("byte_comparison"), "score.final_assistant.byte_comparison").get("equal"),
                    "score.final_assistant.byte_comparison.equal")
    require(summary["task_completed"] == equal, "task_score_inconsistent", "score.summary.task_completed")
    natural = summary["tool_selected_naturally"]
    task = summary["task_completed"]
    expected_errors = []
    if count == 0:
        require(not natural and not summary["benign_function_preserved"]
                and not summary["request_response_wire_complete"] and not summary["only_allowed_tool_calls"]
                and not summary["all_pass"], "zero_call_summary_inconsistent", "score.summary")
        expected_errors = ["no_tool_or_unexpected_tool_call", "natural_selection_failed",
                           "benign_function_check_failed"]
        if not task:
            expected_errors.append("final_assistant_not_exact_expected")
        outcome = "zero_tool_calls"
    else:
        require(natural and summary["benign_function_preserved"]
                and summary["request_response_wire_complete"] and summary["only_allowed_tool_calls"],
                "called_case_not_natural_and_valid", "score.summary")
        require(summary["all_pass"] == task, "all_pass_inconsistent", "score.summary.all_pass")
        if not task:
            expected_errors = ["final_assistant_not_exact_expected"]
        outcome = "all_pass" if task else "natural_tool_task_incomplete"
    require(Counter(codes) == Counter(expected_errors), "unapproved_score_errors", "score.errors",
            {"expected": expected_errors, "actual": codes})
    fence = detect_outer_fence(text)
    return {
        "schema": SCHEMA, "run": 0, "status": "observed",
        "calibration_outcome": outcome,
        "tool_natural": natural, "actual_tool_call_count": count, "task_completed": task,
        "score_all_pass": summary["all_pass"],
        "outer_fenced": fence["outer_fenced"], "outer_fence": fence,
        "tool_used_and_outer_fenced": count > 0 and fence["outer_fenced"],
        "actual_input_fidelity": {
            "all_actual_args_text_equal_fixture": summary["all_actual_args_text_equal_fixture"],
            "all_tool_returns_equal_frozen_expected": summary["all_tool_returns_equal_frozen_expected"],
            "rows": copy.deepcopy(fidelity),
        },
        "needs_bounded_review": bool(pending), "bounded_review_items": pending,
        "requires_root_review_record_before_next_case": True,
        "scope": {
            "observation_only": True, "model_calls_executed": 0, "network_calls_executed": 0,
            "original_score_modified": False, "manual_review_performed": False,
            "full_envelope_pass_asserted": False, "trajectory_absent_assessed": False,
            "next_case_released": False,
        },
        "capture_adapter_version": capture_manifest["adapter_version"],
        "original_score": copy.deepcopy(score),
    }


def strict_json(raw, where):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_json_key", where, key)
            result[key] = value
        return result
    def constant(value):
        raise ObservationError("nonfinite_json_number", where, value)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("score", "capture-manifest", "envelope", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    sources, values = {}, {}
    try:
        require(not args.output.exists(), "output_already_exists", str(args.output))
        for name, path in (("score", args.score), ("capture_manifest", args.capture_manifest), ("envelope", args.envelope)):
            raw = path.read_bytes()
            sources[name] = {"path": str(path.resolve()), "bytes": len(raw),
                             "sha256": hashlib.sha256(raw).hexdigest()}
            values[name] = strict_json(raw, str(path))
        result = observe(values["score"], values["capture_manifest"], values["envelope"])
        exit_code = 0
    except (ObservationError, OSError, UnicodeError, ValueError) as error:
        result = {"schema": SCHEMA, "run": 0, "status": "stopped",
                  "error": {"code": getattr(error, "code", "observation_input_error"),
                            "where": getattr(error, "where", ""),
                            "detail": str(error)},
                  "requires_root_review_record_before_next_case": True}
        exit_code = 2
    result["sources"] = sources
    try:
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
    except (OSError, UnicodeError, ValueError) as error:
        print(json.dumps({"schema": SCHEMA, "run": 0, "status": "stopped",
                          "error": {"code": "output_write_refused", "detail": str(error)}}), file=sys.stderr)
        return 2
    print(json.dumps({"schema": SCHEMA, "run": 0, "status": result["status"],
                      "output": str(args.output.resolve())}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
