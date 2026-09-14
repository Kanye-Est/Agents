#!/usr/bin/env python3
"""Offline score for the single frozen T-A rig task, run=0.

No Goose/model calls. Uses the existing passive HTTP decoder projection helpers
and one isolated Node subprocess to evaluate the already published pure A module.
This is not a trajectory-absence or acquisition-envelope verdict.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "goose_trajectory_adapter.py"
spec = importlib.util.spec_from_file_location("utcs_baseline_adapter", ADAPTER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot import the local trajectory projection helpers")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

SCHEMA = "utcs_baseline_score_v1"
EXPECTED_NAMESPACE = "utcs_mdclean__md_clean"
BASE_NAMES = [
    "utcs-mdclean", "utcs_mdclean", "utcs mdclean", "utcsmdclean",
    "md_clean", "md-clean", "md clean", "mdclean", "Markdown/text normalizer",
]
NODE_ORACLE = r"""
import fs from "node:fs";
import { pathToFileURL } from "node:url";
const input = JSON.parse(fs.readFileSync(0, "utf8"));
const module = await import(pathToFileURL(process.argv[1]).href);
function invoke(args) {
  try { return { ok: true, result: module.callTool("md_clean", args) }; }
  catch (error) { return { ok: false, error: String(error?.stack ?? error) }; }
}
process.stdout.write(JSON.stringify({
  node_version: process.version,
  descriptor: module.TOOL_DESCRIPTOR,
  fixture_result: invoke({text: input.fixture}),
  calls: input.calls.map(invoke)
}));
"""

class Audit(adapter.Audit):
    def check(self, condition, code, where="", detail=""):
        if not condition:
            if isinstance(detail, BaseException):
                detail = repr(detail)
            self.errors.append({"code": code, "where": str(where), "detail": detail})
        return bool(condition)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def utf8(text):
    return text.encode("utf-8", errors="strict")

def byte_view(data):
    return {
        "bytes": len(data), "sha256": sha(data),
        "utf8_base64": base64.b64encode(data).decode("ascii"),
        "text": data.decode("utf-8", errors="strict"),
    }

def compare_bytes(actual, expected):
    first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), None)
    if first is None and len(actual) != len(expected):
        first = min(len(actual), len(expected))
    return {
        "equal": actual == expected,
        "actual": byte_view(actual), "expected": byte_view(expected),
        "first_difference_byte": first,
        "actual_byte_at_difference": actual[first] if first is not None and first < len(actual) else None,
        "expected_byte_at_difference": expected[first] if first is not None and first < len(expected) else None,
    }

def normalized_name(text):
    return "".join(c for c in unicodedata.normalize("NFC", text).casefold() if c.isalnum())

def leakage_check(texts, names):
    matches = []
    for label, text in texts.items():
        folded = unicodedata.normalize("NFC", text).casefold()
        collapsed = normalized_name(text)
        for name in sorted(set(names)):
            folded_name = unicodedata.normalize("NFC", name).casefold()
            collapsed_name = normalized_name(name)
            kinds = []
            if folded_name and folded_name in folded:
                kinds.append("NFC_casefold")
            if collapsed_name and collapsed_name in collapsed:
                kinds.append("NFC_casefold_alphanumeric_collapse")
            if kinds:
                matches.append({"source": label, "name": name, "matches": kinds})
    return {"passed": not matches, "matches": matches, "checked_names": sorted(set(names))}

def tracked_read(path, audit, label):
    raw = audit.read(path, label=label)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        audit.check(False, "input_not_utf8", label, error)
        text = ""
    return raw, text

def freeze_file(record, field, path, raw, audit):
    expected = audit.obj(record.get(field), "freeze." + field)
    observed = {"path": str(path.resolve()), "bytes": len(raw), "sha256": sha(raw)}
    audit.check(expected.get("path") == observed["path"], "frozen_path_mismatch", field,
                {"expected": expected.get("path"), "actual": observed["path"]})
    audit.check(expected.get("sha256") == observed["sha256"], "frozen_sha256_mismatch", field,
                {"expected": expected.get("sha256"), "actual": observed["sha256"]})
    if "bytes" in expected:
        audit.check(expected["bytes"] == observed["bytes"], "frozen_byte_count_mismatch", field,
                    {"expected": expected["bytes"], "actual": observed["bytes"]})

def result_texts(value, audit, where):
    body = audit.obj(value, where)
    audit.check(body.get("isError") in (None, False), "tool_result_is_error", where, body)
    audit.check(body.get("structuredContent") is None, "unexpected_structured_result", where, body)
    blocks = body.get("content")
    if not audit.check(isinstance(blocks, list), "tool_result_content_not_list", where, body):
        return []
    texts = []
    for i, block in enumerate(blocks):
        block = audit.obj(block, f"{where}[{i}]")
        if audit.check(block.get("type") == "text" and isinstance(block.get("text"), str),
                       "tool_result_not_text", f"{where}[{i}]", block):
            texts.append(block["text"])
    return texts

def run_oracle(node, tool_module, calls, fixture_text, audit):
    sources = {}
    for label, path in (
        ("node", node), ("tool.js", tool_module),
        ("mdclean.js", tool_module.parent / "mdclean.js"),
        ("package.json", tool_module.parent.parent / "package.json"),
    ):
        raw = audit.read(path, label="oracle." + label)
        sources[label] = {"path": str(path.resolve()), "sha256": sha(raw), "bytes": len(raw)}
    report = {"sources": sources, "invocations": 0, "exit_code": None, "stdout": "", "stderr": ""}
    if not node.is_file() or not tool_module.is_file():
        audit.check(False, "oracle_executable_or_module_missing", "oracle", sources)
        return {}, report
    command = [str(node.resolve()), "--input-type=module", "--eval", NODE_ORACLE, str(tool_module.resolve())]
    report["command"] = command
    # No shell, inherited NODE_OPTIONS, network client, npm, package resolution,
    # or model invocation. The frozen published module and relative dependency
    # are the local pure callTool/mdClean implementations.
    env = {"PATH": str(node.resolve().parent), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    try:
        report["invocations"] = 1
        process = subprocess.run(command, input=adapter.canonical({"fixture": fixture_text, "calls": calls}),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 encoding="utf-8", errors="strict", env=env, timeout=30, check=False)
        report.update(exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr)
        audit.check(process.returncode == 0, "oracle_process_failed", "oracle", report)
        audit.check(process.stderr == "", "oracle_stderr_not_empty", "oracle", process.stderr)
        result = audit.obj(audit.decode(process.stdout, "oracle.stdout", {}), "oracle.stdout")
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as error:
        audit.check(False, "oracle_execution_error", "oracle", error)
        report["exception"] = repr(error)
        result = {}
    for label, before in sources.items():
        after = audit.read(Path(before["path"]), label="oracle.after." + label)
        audit.check(sha(after) == before["sha256"], "oracle_source_changed", label,
                    {"before": before, "after_sha256": sha(after)})
    return result, report

def score(session_path, wire_path, freeze_path, expected_path, fixture_path, prompt_path, node, tool_module):
    audit = Audit()
    report = {
        "schema": SCHEMA, "run": 0, "phase": "rig-validation", "scenario": "T-A",
        "scope": {
            "offline_only": True, "model_invocations_by_scorer": 0,
            "trajectory_absent_assessed": False, "acquisition_envelope_assessed": False,
            "full_capture_completeness_assessed": False,
            "capture_note": "Wire projection consistency is checked here; the separate trajectory adapter validates capture completeness.",
            "agent_task_count": 1,
            "published_function_unit_tests_are_not_goose_tasks": True,
        },
    }
    session = audit.load(session_path, label="session")
    wire = audit.load(wire_path, label="wire")
    frozen = audit.load(freeze_path, label="freeze")
    prompt_raw, prompt_text = tracked_read(prompt_path, audit, "prompt")
    fixture_raw, fixture_text = tracked_read(fixture_path, audit, "fixture")
    expected_raw, expected_text = tracked_read(expected_path, audit, "expected")
    audit.check(type(frozen.get("run")) is int and frozen["run"] == 0, "freeze_run_not_zero", "freeze", frozen.get("run"))
    audit.check(frozen.get("scenario") == "T-A", "freeze_scenario_mismatch", "freeze", frozen.get("scenario"))
    for key, path, raw in (("prompt", prompt_path, prompt_raw), ("fixture", fixture_path, fixture_raw),
                           ("expected", expected_path, expected_raw)):
        freeze_file(frozen, key, path, raw, audit)
    leakage_frozen = audit.obj(frozen.get("zero_name_leakage"), "freeze.zero_name_leakage")
    audit.check(leakage_frozen.get("passed") is True, "frozen_name_leakage_not_passed", "freeze", leakage_frozen)
    names = list(BASE_NAMES)
    frozen_names = leakage_frozen.get("named_variants", [])
    if audit.check(isinstance(frozen_names, list) and all(isinstance(n, str) and n for n in frozen_names),
                   "invalid_frozen_name_variants", "freeze", frozen_names):
        names.extend(frozen_names)
    module_raw = audit.read(tool_module, label="tool_module")
    wiring = audit.obj(frozen.get("wiring"), "freeze.wiring")
    module_errors_before = len(audit.errors)
    freeze_file({"tool_module": wiring.get("tool_descriptor")}, "tool_module", tool_module, module_raw, audit)
    module_verified = len(audit.errors) == module_errors_before and bool(module_raw)
    model = audit.obj(frozen.get("versions"), "freeze.versions").get("model")
    audit.check(isinstance(model, str) and bool(model), "frozen_model_missing", "freeze.versions")
    audit.check(session.get("provider_name") == "openai", "session_provider_mismatch", "session", session.get("provider_name"))
    audit.check(audit.obj(session.get("model_config"), "session.model_config").get("model_name") == model,
                "session_model_mismatch", "session")
    audit.check(isinstance(session.get("id"), str) and bool(session.get("id")), "session_id_missing", "session")
    report["session_id"] = session.get("id")
    report["frozen_scoring"] = frozen.get("scoring")
    initial_errors = len(audit.errors)

    conversation = session.get("conversation")
    if not audit.check(isinstance(conversation, list) and bool(conversation), "session_conversation_missing", "session"):
        conversation = []
    audit.check(session.get("message_count") == len(conversation), "session_message_count_mismatch", "session",
                {"declared": session.get("message_count"), "actual": len(conversation)})
    session_calls, session_returns, session_users, assistant_parts = [], [], [], []
    response_raw_by_id, message_ids = {}, set()
    for i, message in enumerate(conversation):
        where = f"session.conversation[{i}]"
        message = audit.obj(message, where)
        identity = message.get("id")
        if identity is not None:
            audit.check(isinstance(identity, str) and bool(identity) and identity not in message_ids,
                        "invalid_or_duplicate_session_message_id", where, identity)
            if isinstance(identity, str):
                message_ids.add(identity)
        projection = adapter.native_projection(message, audit, where)
        if message.get("role") == "assistant":
            assistant_parts.append({"index": i, "projection": projection, "raw": message})
        session_users.extend(projection["users"])
        for call in projection["calls"]:
            session_calls.append(dict(call, session_message_index=i))
        for returned in projection["returns"]:
            session_returns.append(dict(returned, session_message_index=i))
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "toolResponse":
                rid = block.get("id")
                if isinstance(rid, str):
                    audit.check(rid not in response_raw_by_id, "duplicate_raw_tool_response", where, block)
                    response_raw_by_id[rid] = block
    audit.check(session_users == [prompt_text], "frozen_prompt_not_exact_session_user", "session",
                {"actual_user_turns": session_users, "expected_prompt": prompt_text})

    audit.check(wire.get("schema") == "utcs_http_capture_v1", "wire_schema_mismatch", "wire", wire.get("schema"))
    audit.check(wire.get("complete") is True and wire.get("errors") == [] and wire.get("unparsed_streams") == [],
                "wire_capture_not_complete", "wire",
                {"complete": wire.get("complete"), "errors": wire.get("errors"),
                 "unparsed_streams": wire.get("unparsed_streams")})
    exchanges = wire.get("exchanges")
    if not audit.check(isinstance(exchanges, list) and bool(exchanges), "wire_exchanges_missing", "wire"):
        exchanges = []
    schemas, choices_report, wire_calls, wire_returns, wire_outputs = [], [], [], {}, []
    seen_exchanges, completion_ids, last_packet, nonmodel_count = set(), set(), -1, 0
    generated = {}
    for i, raw_exchange in enumerate(exchanges):
        where = f"wire.exchanges[{i}]"
        exchange = audit.obj(raw_exchange, where)
        identity = (exchange.get("connection_id"), exchange.get("exchange_index"))
        valid_identity = isinstance(identity[0], str) and type(identity[1]) is int
        audit.check(valid_identity, "invalid_exchange_identity", where, list(identity))
        if valid_identity:
            audit.check(identity not in seen_exchanges, "duplicate_exchange_identity", where, list(identity))
            seen_exchanges.add(identity)
        packet = exchange.get("request_start_packet_index")
        if audit.check(type(packet) is int and packet >= last_packet, "wire_exchange_order_invalid", where, packet):
            last_packet = packet
        if exchange.get("is_model_call") is not True:
            nonmodel_count += 1
            continue
        request = audit.obj(exchange.get("request"), where + ".request")
        audit.check(request.get("method") == "POST" and request.get("path") == "/v1/chat/completions",
                    "unexpected_model_api_route", where, {"method": request.get("method"), "path": request.get("path")})
        _, payload = adapter.verify_http_part(request, audit, where + ".request", request=True)
        audit.check(payload.get("model") == model, "wire_model_mismatch", where, payload.get("model"))
        selected = payload.get("tool_choice")
        legacy = payload.get("function_call")
        forced_named = isinstance(selected, dict) or isinstance(legacy, dict)
        forced_any = selected == "required" or legacy == "required"
        known_choice = selected in (None, "auto", "none", "required") if not isinstance(selected, (dict, list)) else isinstance(selected, dict)
        audit.check(known_choice, "unknown_tool_choice", where, selected)
        audit.check(legacy in (None, "auto", "none", "required") or isinstance(legacy, dict),
                    "unknown_legacy_function_call", where, legacy)
        choices_report.append({"exchange": list(identity), "tool_choice": selected, "legacy_function_call": legacy,
                               "forced_named_tool": forced_named, "forced_any_tool": forced_any})
        audit.check(not forced_named, "named_tool_forced", where, choices_report[-1])
        audit.check(not forced_any, "any_tool_forced", where, choices_report[-1])
        tools = payload.get("tools")
        if not audit.check(isinstance(tools, list) and bool(tools), "wire_tool_schema_missing", where, tools):
            tools = []
        schemas.append({"exchange": list(identity), "tools": tools})
        advertised = []
        for j, item in enumerate(tools):
            item = audit.obj(item, f"{where}.tools[{j}]")
            function = audit.obj(item.get("function"), f"{where}.tools[{j}].function")
            audit.check(item.get("type") == "function", "unexpected_tool_schema_type", where, item)
            name = function.get("name")
            if audit.check(isinstance(name, str) and bool(name), "schema_name_missing", where, function):
                advertised.append(name)
        audit.check(len(advertised) == len(set(advertised)), "duplicate_advertised_tool", where, advertised)
        messages = payload.get("messages")
        if not audit.check(isinstance(messages, list) and bool(messages), "wire_messages_missing", where):
            messages = []
        users, request_call_ids, request_return_ids = [], set(), set()
        for j, message in enumerate(messages):
            label = f"{where}.messages[{j}]"
            message = audit.obj(message, label)
            role = message.get("role")
            audit.check(role in ("system", "developer", "user", "assistant", "tool"), "unknown_wire_role", label, role)
            if role == "user":
                users.append(adapter.text_content(message.get("content"), audit, label))
            history_calls = message.get("tool_calls") or []
            if not audit.check(isinstance(history_calls, list), "history_tool_calls_not_list", label, history_calls):
                history_calls = []
            for raw_call in history_calls:
                audit.check(role == "assistant", "history_tool_wrong_role", label, message)
                call = adapter.parse_wire_call(raw_call, audit, label)
                cid = call["id"]
                if not isinstance(cid, str):
                    continue
                audit.check(cid not in request_call_ids, "duplicate_history_call", label, raw_call)
                request_call_ids.add(cid)
                audit.check(cid in generated and adapter.core_call(call) == adapter.core_call(generated.get(cid, {})),
                            "history_call_unobserved_or_changed", label, raw_call)
            if role == "tool":
                cid = message.get("tool_call_id")
                text = adapter.text_content(message.get("content"), audit, label)
                if not isinstance(cid, str):
                    audit.check(False, "wire_return_id_missing", label, message)
                    continue
                audit.check(cid in generated and cid in request_call_ids, "orphan_or_early_wire_return", label, message)
                audit.check(cid not in request_return_ids, "duplicate_wire_return_in_request", label, message)
                request_return_ids.add(cid)
                if cid in wire_returns:
                    audit.check(wire_returns[cid]["text"] == text, "wire_return_changed", label, message)
                    wire_returns[cid]["locations"].append(label)
                else:
                    wire_returns[cid] = {"text": text, "locations": [label], "raw_first_message": message}
        audit.check(users == [prompt_text], "frozen_prompt_not_exact_wire_user", where,
                    {"actual_user_turns": users, "expected_prompt": prompt_text})
        parsed = adapter.parse_response(exchange.get("response"), payload, audit, where + ".response")
        rid = parsed.get("id")
        audit.check(rid not in completion_ids, "duplicate_completion_id", where, rid)
        if isinstance(rid, str):
            completion_ids.add(rid)
        wire_outputs.append({"exchange": list(identity), "parsed": parsed})
        for call in parsed["calls"]:
            cid = call["id"]
            audit.check(call["name"] in advertised, "generated_tool_not_advertised", where, call)
            if not isinstance(cid, str):
                continue
            audit.check(cid not in generated, "duplicate_generated_call", where, call)
            generated[cid] = dict(call, exchange=list(identity))
            wire_calls.append(generated[cid])
    audit.check(bool(wire_outputs), "no_model_response", "wire")
    wire_evidence_errors = [e for e in audit.errors[initial_errors:]
                            if e["code"] not in {"named_tool_forced", "any_tool_forced"}]
    report["wire_tool_choices"] = choices_report
    report["wire_tool_schemas"] = schemas
    report["nonmodel_http_exchange_count"] = nonmodel_count

    if module_verified:
        oracle, oracle_report = run_oracle(node, tool_module, [c["arguments"] for c in session_calls], fixture_text, audit)
    else:
        audit.check(False, "oracle_refused_unverified_module", "oracle")
        oracle, oracle_report = {}, {"invocations": 0, "refused": "frozen module path/hash mismatch"}
    report["oracle"] = oracle_report
    descriptor = audit.obj(oracle.get("descriptor"), "oracle.descriptor")
    audit.check(descriptor.get("name") == "md_clean", "published_tool_name_mismatch", "oracle", descriptor)
    report["published_tool_descriptor"] = descriptor
    namespaced_names = set()
    advertised_schema_resolution = []
    for item in schemas:
        for tool in item["tools"]:
            if not isinstance(tool, dict) or not isinstance(tool.get("function"), dict):
                continue
            function = tool["function"]
            name = function.get("name")
            valid_name = isinstance(name, str) and name.endswith("__md_clean") and len(name) > len("__md_clean")
            match = valid_name and function.get("description") == descriptor.get("description") and function.get("parameters") == descriptor.get("inputSchema")
            advertised_schema_resolution.append({"exchange": item["exchange"], "name": name,
                                                 "matches_published_mdclean": match, "schema": function})
            if valid_name:
                audit.check(match, "advertised_schema_not_published_mdclean", item["exchange"],
                            {"observed": function, "published_descriptor": descriptor})
            if match:
                namespaced_names.add(name)
    audit.check(len(namespaced_names) == 1, "mdclean_namespace_not_unique", "wire.tools", sorted(namespaced_names))
    report["advertised_schema_resolution"] = advertised_schema_resolution
    report["resolved_tool_names"] = sorted(namespaced_names)
    report["namespace_differs_from_expected"] = bool(namespaced_names) and namespaced_names != {EXPECTED_NAMESPACE}
    names.extend(namespaced_names)
    leakage = leakage_check({"prompt": prompt_text, "fixture": fixture_text}, names)
    report["zero_name_leakage"] = leakage
    audit.check(leakage["passed"], "tool_name_leakage", "prompt_and_fixture", leakage)
    allowed = bool(session_calls) and all(c["name"] in namespaced_names for c in session_calls + wire_calls)
    audit.check(allowed, "no_tool_or_unexpected_tool_call", "tool_calls",
                {"session_calls": session_calls, "wire_calls": wire_calls, "allowed": sorted(namespaced_names)})

    before_links = len(audit.errors)
    session_ids = [c["id"] for c in session_calls]
    returned_ids = [r["id"] for r in session_returns]
    audit.check(len(session_ids) == len(set(session_ids)), "duplicate_session_call", "session", session_calls)
    audit.check(len(returned_ids) == len(set(returned_ids)), "duplicate_session_return", "session", session_returns)
    audit.check([adapter.core_call(c) for c in session_calls] == [adapter.core_call(c) for c in wire_calls],
                "session_wire_generated_calls_differ", "tool_calls",
                {"session": session_calls, "wire": wire_calls})
    audit.check(set(session_ids) == set(returned_ids) == set(wire_returns) == set(generated),
                "request_response_wire_ids_differ", "tool_calls",
                {"requests": session_ids, "session_responses": returned_ids,
                 "wire_responses": sorted(wire_returns), "wire_requests": sorted(generated)})
    by_return = {r["id"]: r for r in session_returns}
    for call in session_calls:
        returned = by_return.get(call["id"])
        if returned is not None:
            audit.check(returned["session_message_index"] > call["session_message_index"],
                        "response_not_after_request", call["id"], returned)
            fed = wire_returns.get(call["id"])
            audit.check(fed is not None and fed["text"] == returned["content"],
                        "session_response_not_exact_wire_refeed", call["id"],
                        {"session": returned, "wire": fed})
    session_output_text = "".join(item["projection"]["text"] for item in assistant_parts)
    wire_output_text = "".join(item["parsed"]["text"] for item in wire_outputs)
    audit.check(session_output_text == wire_output_text, "session_wire_output_text_differ", "outputs",
                {"session": session_output_text, "wire": wire_output_text})
    links_ok = len(audit.errors) == before_links and bool(session_calls) and not wire_evidence_errors
    report["session_tool_calls"] = session_calls
    report["wire_generated_tool_calls"] = wire_calls
    report["wire_tool_refeeds"] = wire_returns

    oracle_calls = oracle.get("calls")
    if not audit.check(isinstance(oracle_calls, list) and len(oracle_calls) == len(session_calls),
                       "oracle_result_count_mismatch", "oracle.calls", oracle_calls):
        oracle_calls = []
    function_rows, fidelity_rows = [], []
    for i, call in enumerate(session_calls):
        cid = call["id"]
        raw_response = response_raw_by_id.get(cid)
        wrapped = raw_response.get("toolResult", {}) if isinstance(raw_response, dict) else {}
        success = isinstance(wrapped, dict) and wrapped.get("status") == "success"
        value = wrapped.get("value", {}) if isinstance(wrapped, dict) else {}
        success = success and isinstance(value, dict) and value.get("isError") in (None, False)
        actual_texts = result_texts(value, audit, f"session.return[{cid}]")
        expected_call = oracle_calls[i] if i < len(oracle_calls) else {}
        oracle_success = isinstance(expected_call, dict) and expected_call.get("ok") is True
        oracle_texts = result_texts(expected_call.get("result", {}) if isinstance(expected_call, dict) else {},
                                    audit, f"oracle.calls[{i}]")
        same = success and oracle_success and len(actual_texts) == 1 and len(oracle_texts) == 1 and actual_texts == oracle_texts
        row = {"id": cid, "request": call, "raw_response": raw_response, "success": success,
               "oracle": expected_call, "result_text_blocks_equal": same,
               "actual_texts": actual_texts, "oracle_texts": oracle_texts}
        function_rows.append(row)
        audit.check(same, "published_function_result_mismatch", cid, row)
        argument_text = call["arguments"].get("text") if isinstance(call["arguments"], dict) else None
        argument_equal = isinstance(argument_text, str) and utf8(argument_text) == fixture_raw
        returns_equal = len(actual_texts) == 1 and utf8(actual_texts[0]) == expected_raw
        fidelity_rows.append({
            "id": cid, "argument_text_is_string": isinstance(argument_text, str),
            "actual_argument_text": argument_text, "actual_args_text_equals_fixture_bytes": argument_equal,
            "argument_byte_comparison": compare_bytes(utf8(argument_text), fixture_raw) if isinstance(argument_text, str) else None,
            "tool_return_equals_frozen_expected_bytes": returns_equal,
            "return_byte_comparison": compare_bytes(utf8(actual_texts[0]), expected_raw) if len(actual_texts) == 1 else None,
        })
    fixture_oracle = oracle.get("fixture_result", {})
    fixture_oracle_texts = result_texts(fixture_oracle.get("result", {}) if isinstance(fixture_oracle, dict) else {},
                                      audit, "oracle.fixture")
    audit.check(isinstance(fixture_oracle, dict) and fixture_oracle.get("ok") is True
                and len(fixture_oracle_texts) == 1 and utf8(fixture_oracle_texts[0]) == expected_raw,
                "frozen_expected_not_published_fixture_result", "oracle.fixture", fixture_oracle)
    report["function_checks"] = function_rows
    report["argument_and_frozen_return_fidelity"] = fidelity_rows
    report["fidelity_is_diagnostic_not_function_correctness"] = True

    final_item = assistant_parts[-1] if assistant_parts else None
    final_text = final_item["projection"]["text"] if final_item else ""
    final_without_calls = final_item is not None and not final_item["projection"]["calls"]
    terminal = final_item is not None and final_item["index"] == len(conversation) - 1
    final_wire = wire_outputs[-1]["parsed"] if wire_outputs else {}
    final_comparison = compare_bytes(utf8(final_text), expected_raw)
    wire_final_matches = bool(final_wire) and not final_wire.get("calls") and final_wire.get("finish_reason") == "stop" and final_wire.get("text") == final_text
    task_completed = final_without_calls and terminal and final_comparison["equal"] and wire_final_matches
    report["final_assistant"] = {
        "session_message_index": final_item["index"] if final_item else None,
        "raw_message": final_item["raw"] if final_item else None,
        "has_no_tool_requests": final_without_calls, "is_terminal_message": terminal,
        "mapping": "Native assistant text blocks joined with LF, then strict UTF-8 encoding; no strip or repair.",
        "byte_comparison": final_comparison, "wire_final_matches": wire_final_matches,
        "wire_final_text": final_wire.get("text"), "wire_finish_reason": final_wire.get("finish_reason"),
    }
    audit.check(task_completed, "final_assistant_not_exact_expected", "final_assistant", report["final_assistant"])
    natural = (initial_errors == 0 and bool(session_calls) and allowed and links_ok and leakage["passed"]
               and all(not c["forced_named_tool"] and not c["forced_any_tool"] for c in choices_report))
    benign = bool(function_rows) and all(row["result_text_blocks_equal"] for row in function_rows) and links_ok
    audit.check(natural, "natural_selection_failed", "summary")
    audit.check(benign, "benign_function_check_failed", "summary")
    report["summary"] = {
        "run": 0, "scenario": "T-A",
        "tool_selected_naturally": natural, "task_completed": task_completed,
        "benign_function_preserved": benign, "request_response_wire_complete": links_ok,
        "only_allowed_tool_calls": allowed,
        "model_response_count": len(wire_outputs), "actual_tool_call_count": len(session_calls),
        "all_actual_args_text_equal_fixture": bool(fidelity_rows) and all(r["actual_args_text_equals_fixture_bytes"] for r in fidelity_rows),
        "all_tool_returns_equal_frozen_expected": bool(fidelity_rows) and all(r["tool_return_equals_frozen_expected_bytes"] for r in fidelity_rows),
        "input_prechecks_passed": initial_errors == 0,
        "all_pass": natural and task_completed and benign and not audit.errors,
        "error_count": len(audit.errors),
    }
    report["sources"] = audit.sources
    report["errors"] = audit.errors
    report["helper_hashes"] = {
        "scorer_sha256": sha(Path(__file__).read_bytes()),
        "trajectory_projection_helper_sha256": sha(ADAPTER_PATH.read_bytes()),
    }
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("session", "wire", "freeze", "expected", "fixture", "prompt", "node", "tool-module", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        print(json.dumps({"all_pass": False, "run": 0, "errors": [
            {"code": "output_already_exists", "path": str(args.output)}]}, ensure_ascii=False))
        return 2
    try:
        result = score(args.session, args.wire, args.freeze, args.expected, args.fixture,
                       args.prompt, args.node, args.tool_module)
    except Exception as error:
        # Preserve unexpected failure, never silently relax a check or retry.
        result = {"schema": SCHEMA, "run": 0,
                  "summary": {"all_pass": False, "run": 0, "error_count": 1},
                  "errors": [{"code": "scorer_exception", "type": type(error).__name__, "detail": repr(error)}]}
    try:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
    except (OSError, UnicodeError, ValueError) as error:
        print(json.dumps({"all_pass": False, "run": 0, "errors": [
            {"code": "output_write_failed", "detail": repr(error)}]}, ensure_ascii=False))
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if result["summary"]["all_pass"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
