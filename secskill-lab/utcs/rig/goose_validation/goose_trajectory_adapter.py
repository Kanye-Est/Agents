#!/usr/bin/env python3
"""Strict, offline Goose 1.45.0 -> frozen trajectory input schema v1 adapter.

Wire evidence is authoritative; native request JSONL and the full session export
must independently reconcile. Unsupported/error/truncated/ambiguous evidence
fails closed. This is capture validation only: no matcher positive control and
no trajectory_absent claim. No network, subprocess, or model calls.

Pinned shape references (v1.45.0):
  crates/goose-provider-types/src/conversation.rs (Conversation newtype array)
  crates/goose-provider-types/src/conversation/message.rs
  crates/goose-provider-types/src/conversation/tool_result_serde.rs
  crates/goose-provider-types/src/request_log.rs
  crates/goose-provider-types/src/formats/openai.rs
  crates/goose-providers/src/openai.rs
  crates/goose-providers/src/openai_compatible.rs
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
VERSION = "goose-1.45.0-wire-adapter-v1.1"
SOURCES = (
    "system_prompt", "developer_prompt", "user_turn", "model_output",
    "tool_call_request", "tool_return", "thinking",
)
REQUEST_KEYS = {
    "model", "messages", "tools", "tool_choice", "stream", "stream_options",
    "temperature", "top_p", "max_tokens", "max_completion_tokens", "stop",
    "seed", "frequency_penalty", "presence_penalty", "parallel_tool_calls",
    "response_format", "logprobs", "top_logprobs", "n", "user", "service_tier",
    "store", "metadata", "reasoning_effort", "chat_template_kwargs",
}
CHUNK_KEYS = {
    "id", "object", "created", "model", "choices", "usage",
    "system_fingerprint", "service_tier", "prompt_logprobs",
}
DELTA_KEYS = {
    "role", "content", "tool_calls", "reasoning", "reasoning_content",
    "reasoning_details", "refusal", "audio", "annotations",
}

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def _unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result

def strict_json(text):
    return json.loads(text, object_pairs_hook=_unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("non-finite JSON number: " + value)))

class Audit:
    def __init__(self):
        self.errors = []
        self.sources = []

    def check(self, condition, code, where="", detail=""):
        if not condition:
            self.errors.append({"code": code, "where": str(where), "detail": str(detail)})
        return bool(condition)

    def obj(self, value, where):
        if not self.check(isinstance(value, dict), "object_required", where):
            return {}
        return value

    def keys(self, obj, allowed, where):
        if isinstance(obj, dict):
            self.check(not (set(obj) - set(allowed)), "unknown_fields", where,
                       ",".join(sorted(set(obj) - set(allowed))))

    def decode(self, text, where, default=None):
        try:
            return strict_json(text)
        except (ValueError, TypeError, UnicodeError) as error:
            self.check(False, "invalid_json", where, error)
            return default

    def read(self, path, expected=None, label=""):
        try:
            p = Path(path)
            data = p.read_bytes()
            row = {"path": str(p.resolve()), "bytes": len(data), "sha256": sha(data),
                   "label": label}
            self.sources.append(row)
            if expected is not None:
                self.check(expected == row["sha256"], "source_sha256_mismatch", p)
            return data
        except (OSError, TypeError, ValueError) as error:
            self.check(False, "source_unreadable", str(path), error)
            return b""

    def load(self, path, label=""):
        return self.obj(self.decode(self.read(path, label=label), path, {}), path)

def text_content(value, audit, where, allow_null=False):
    if value is None and allow_null:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for index, raw in enumerate(value):
            block = audit.obj(raw, f"{where}[{index}]")
            audit.keys(block, {"type", "text", "annotations", "_meta"}, where)
            if not audit.check(block.get("type") == "text", "unknown_content_block", where,
                               block.get("type")):
                continue
            text = block.get("text")
            if audit.check(isinstance(text, str), "text_required", where):
                parts.append(text)
        return "\n".join(parts)
    audit.check(False, "unsupported_text_content", where, type(value).__name__)
    return ""

def parse_arguments(value, audit, where):
    if not audit.check(isinstance(value, str), "raw_arguments_not_string", where):
        return {}
    parsed = audit.decode(value, where, {})
    audit.check(isinstance(parsed, dict), "arguments_not_object", where)
    return parsed if isinstance(parsed, dict) else {}

def parse_wire_call(raw, audit, where):
    call = audit.obj(raw, where)
    audit.keys(call, {"id", "type", "function"}, where)
    audit.check(call.get("type") == "function", "unsupported_tool_call_type", where)
    function = audit.obj(call.get("function"), where + ".function")
    audit.keys(function, {"name", "arguments"}, where + ".function")
    call_id, name, arguments = call.get("id"), function.get("name"), function.get("arguments")
    audit.check(isinstance(call_id, str) and bool(call_id), "tool_call_id_missing", where)
    audit.check(isinstance(name, str) and bool(name), "tool_name_missing", where)
    parsed = parse_arguments(arguments, audit, where + ".arguments")
    return {"id": call_id, "name": name, "arguments": parsed,
            "raw_arguments": arguments if isinstance(arguments, str) else canonical(arguments)}

def core_call(call):
    return {key: call.get(key) for key in ("id", "name", "arguments")}

def empty_projection():
    return {"text": "", "thinking": "", "calls": [], "returns": [], "users": []}

def native_projection(message, audit, where):
    result = empty_projection()
    message = audit.obj(message, where)
    audit.keys(message, {"id", "role", "created", "content", "metadata"}, where)
    role = message.get("role")
    audit.check(role in ("assistant", "user"), "unknown_native_role", where, role)
    blocks = message.get("content")
    if not audit.check(isinstance(blocks, list), "native_content_not_list", where):
        return result
    text_parts = []
    for index, value in enumerate(blocks):
        label = f"{where}.content[{index}]"
        block = audit.obj(value, label)
        kind = block.get("type")
        if kind == "text":
            audit.keys(block, {"type", "text", "annotations", "_meta"}, label)
            text = block.get("text")
            if audit.check(isinstance(text, str), "native_text_not_string", label):
                text_parts.append(text)
        elif kind == "thinking":
            audit.keys(block, {"type", "thinking", "signature"}, label)
            audit.check(role == "assistant", "thinking_wrong_role", label)
            text = block.get("thinking")
            if audit.check(isinstance(text, str), "native_thinking_not_string", label):
                result["thinking"] += text
        elif kind in ("toolRequest", "toolResponse"):
            field = "toolCall" if kind == "toolRequest" else "toolResult"
            audit.keys(block, {"type", "id", field, "metadata", "_meta"}, label)
            call_id = block.get("id")
            audit.check(isinstance(call_id, str) and bool(call_id), "native_tool_id_missing", label)
            wrapped = audit.obj(block.get(field), label + "." + field)
            audit.keys(wrapped, {"status", "value", "error"}, label)
            if not audit.check(wrapped.get("status") == "success", "native_tool_error", label,
                               wrapped.get("error", wrapped.get("status"))):
                continue
            body = audit.obj(wrapped.get("value"), label + ".value")
            if kind == "toolRequest":
                audit.check(role == "assistant", "tool_request_wrong_role", label)
                audit.keys(body, {"name", "arguments", "_meta"}, label)
                arguments = body.get("arguments", {})
                if arguments is None:
                    arguments = {}
                audit.check(isinstance(arguments, dict), "native_arguments_not_object", label)
                name = body.get("name")
                audit.check(isinstance(name, str) and bool(name), "native_tool_name_missing", label)
                result["calls"].append({"id": call_id, "name": name, "arguments": arguments})
            else:
                audit.check(role == "user", "tool_response_wrong_role", label)
                audit.keys(body, {"content", "isError", "structuredContent", "_meta"}, label)
                audit.check(body.get("isError") in (None, False), "native_tool_execution_error", label)
                audit.check(body.get("structuredContent") is None, "unsupported_structured_result", label)
                content = body.get("content")
                if audit.check(isinstance(content, list), "native_tool_content_not_list", label):
                    parts = []
                    for part_index, part in enumerate(content):
                        sub = audit.obj(part, f"{label}.result[{part_index}]")
                        audit.keys(sub, {"type", "text", "annotations", "_meta"}, label)
                        if audit.check(sub.get("type") == "text", "unknown_tool_result_block", label,
                                       sub.get("type")):
                            text = sub.get("text")
                            if audit.check(isinstance(text, str), "tool_result_text_required", label):
                                parts.append(text)
                    # Pinned Goose formats/openai.rs:356-363 joins text blocks with SPACE.
                    result["returns"].append({"id": call_id, "content": " ".join(parts)})
        else:
            audit.check(False, "unknown_native_content_block", label, kind)
    joined = "\n".join(text_parts)
    if role == "assistant":
        result["text"] = joined
    elif text_parts:
        result["users"].append(joined)
    return result

def merge_projection(target, part):
    for key in ("text", "thinking"):
        target[key] += part[key]
    for key in ("calls", "returns", "users"):
        target[key].extend(part[key])

def parse_sse(body, audit, where):
    parsed = []
    data_lines, event_name, event_id = [], None, None
    def flush():
        nonlocal data_lines, event_name, event_id
        if data_lines:
            data = "\n".join(data_lines)
            is_done = data.strip() == "[DONE]"
            value = None if is_done else audit.decode(data, where)
            parsed.append({"data": data, "json": value, "is_done": is_done,
                           "event": event_name, "id": event_id})
        data_lines, event_name, event_id = [], None, None
    for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not line:
            flush()
        elif line.startswith(":"):
            continue
        elif line.startswith("data:"):
            value = line[5:]
            data_lines.append(value[1:] if value.startswith(" ") else value)
        elif line.startswith("event:"):
            event_name = line[6:].lstrip(" ")
            audit.check(event_name in ("message", ""), "unsupported_sse_event", where, event_name)
        elif line.startswith("id:"):
            event_id = line[3:].lstrip(" ")
        else:
            audit.check(False, "unknown_sse_field", where, line[:80])
    flush()
    audit.check(bool(parsed), "sse_empty", where)
    audit.check(sum(p["is_done"] for p in parsed) == 1, "sse_done_count", where)
    audit.check(bool(parsed) and parsed[-1]["is_done"], "sse_done_not_last", where)
    return parsed

def verify_http_part(part, audit, where, request=False):
    part = audit.obj(part, where)
    decoded = {}
    for key in ("body", "raw"):
        try:
            raw = base64.b64decode(part[key + "_base64"], validate=True)
            audit.check(sha(raw) == part.get(key + "_sha256"), "http_sha256_mismatch", where, key)
            decoded[key] = raw
        except (KeyError, ValueError, TypeError) as error:
            audit.check(False, "http_base64_invalid", where, error)
            decoded[key] = b""
    try:
        body = decoded["body"].decode("utf-8", errors="strict")
    except UnicodeError as error:
        audit.check(False, "http_utf8_invalid", where, error)
        body = ""
    audit.check(body == part.get("body_text"), "http_body_text_mismatch", where)
    if request:
        value = audit.decode(body, where, {})
        audit.check(value == part.get("json"), "http_request_json_mismatch", where)
        return body, audit.obj(value, where)
    return body, part.get("json")

def parse_response(response, request, audit, where):
    body, recorded_json = verify_http_part(response, audit, where)
    response = audit.obj(response, where)
    audit.check(response.get("status") == 200, "http_model_status_not_200", where,
                response.get("status"))
    streaming = request.get("stream") is True
    if streaming:
        chunks = parse_sse(body, audit, where)
        stored = response.get("sse_events")
        if audit.check(isinstance(stored, list), "sse_events_missing", where):
            audit.check(len(stored) == len(chunks), "sse_event_count_mismatch", where)
            for index, (raw, parsed) in enumerate(zip(stored, chunks)):
                raw = audit.obj(raw, where)
                audit.check(raw.get("index") == index, "sse_index_mismatch", where)
                for key in ("data", "json", "is_done"):
                    audit.check(raw.get(key) == parsed[key], "sse_projection_mismatch",
                                f"{where}[{index}].{key}")
        audit.check(response.get("done") is True, "wire_sse_not_done", where)
        values = [c["json"] for c in chunks if not c["is_done"]]
    else:
        parsed = audit.decode(body, where, {})
        audit.check(parsed == recorded_json, "http_response_json_mismatch", where)
        values = [parsed]

    result = {"text": "", "reasoning": "", "reasoning_content": "",
              "native_thinking": "", "calls": [], "id": None,
              "finish_reason": None, "usage": None, "raw_reasoning_fields": [], "raw_chunks": values}
    tool_parts = {}
    finish_count = 0
    seen_ids = set()
    for index, raw in enumerate(values):
        label = f"{where}.chunk[{index}]"
        value = audit.obj(raw, label)
        audit.keys(value, CHUNK_KEYS, label)
        if "error" in value:
            audit.check(False, "model_error", label, value["error"])
        identity = value.get("id")
        if isinstance(identity, str) and identity:
            seen_ids.add(identity)
        else:
            audit.check(False, "completion_id_missing", label)
        if value.get("model") is not None:
            audit.check(value["model"] == request.get("model"), "response_model_mismatch", label)
        if value.get("usage") is not None:
            audit.check(isinstance(value["usage"], dict), "usage_not_object", label)
            result["usage"] = value["usage"]
        for opaque in ("prompt_logprobs",):
            audit.check(value.get(opaque) in (None, []), "unsupported_response_field", label, opaque)
        choices = value.get("choices")
        if not audit.check(isinstance(choices, list), "choices_not_list", label):
            continue
        audit.check(len(choices) <= 1, "multiple_model_choices", label)
        for raw_choice in choices:
            choice = audit.obj(raw_choice, label)
            audit.keys(choice, {"index", "delta" if streaming else "message", "finish_reason", "logprobs"}, label)
            audit.check(choice.get("index") == 0, "choice_index_not_zero", label)
            audit.check(choice.get("logprobs") in (None, []), "unsupported_logprobs", label)
            finish = choice.get("finish_reason")
            if finish not in (None, ""):
                finish_count += 1
                result["finish_reason"] = finish
                audit.check(finish in ("stop", "tool_calls"), "truncated_or_unknown_finish", label, finish)
            delta = audit.obj(choice.get("delta" if streaming else "message"), label)
            audit.keys(delta, DELTA_KEYS, label)
            audit.check(delta.get("role") in (None, "assistant"), "model_role_not_assistant", label)
            if delta.get("content") is not None:
                result["text"] += text_content(delta["content"], audit, label + ".content")
            for field in ("reasoning", "reasoning_content"):
                if delta.get(field) is not None:
                    text = delta[field]
                    if audit.check(isinstance(text, str), "reasoning_not_text", label, field):
                        result[field] += text
                        result["raw_reasoning_fields"].append({"chunk": index, "field": field, "text": text})
            preferred = delta.get("reasoning_content") or delta.get("reasoning") or ""
            if isinstance(preferred, str):
                result["native_thinking"] += preferred
            for field in ("reasoning_details", "refusal", "audio", "annotations"):
                audit.check(delta.get(field) in (None, [], ""), "unsupported_model_content", label, field)
            calls = delta.get("tool_calls") or []
            if not audit.check(isinstance(calls, list), "tool_calls_not_list", label):
                continue
            for position, raw_call in enumerate(calls):
                call = audit.obj(raw_call, label)
                if not streaming:
                    result["calls"].append(parse_wire_call(call, audit, label))
                    continue
                audit.keys(call, {"index", "id", "type", "function"}, label)
                call_index = call.get("index")
                if not audit.check(isinstance(call_index, int) and not isinstance(call_index, bool)
                                   and call_index >= 0, "tool_chunk_index_missing", label):
                    continue
                item = tool_parts.setdefault(call_index, {"id": None, "name": "", "raw_arguments": "", "type": None})
                if call.get("id") is not None:
                    audit.check(item["id"] in (None, call["id"]), "tool_chunk_id_changed", label)
                    item["id"] = call["id"]
                if call.get("type") is not None:
                    audit.check(call["type"] == "function", "tool_chunk_type_unknown", label)
                    item["type"] = call["type"]
                function = audit.obj(call.get("function"), label + ".function")
                audit.keys(function, {"name", "arguments"}, label)
                for field, target in (("name", "name"), ("arguments", "raw_arguments")):
                    if function.get(field) is not None:
                        if audit.check(isinstance(function[field], str), "tool_fragment_not_string", label, field):
                            item[target] += function[field]
    audit.check(len(seen_ids) == 1, "completion_id_inconsistent", where, sorted(seen_ids))
    result["id"] = next(iter(seen_ids)) if len(seen_ids) == 1 else None
    audit.check(finish_count == 1, "finish_marker_count", where, finish_count)
    for index in sorted(tool_parts):
        item = tool_parts[index]
        result["calls"].append(parse_wire_call(
            {"id": item["id"], "type": item["type"],
             "function": {"name": item["name"], "arguments": item["raw_arguments"]}}, audit, where))
    ids = [c["id"] for c in result["calls"]]
    audit.check(len(ids) == len(set(ids)), "duplicate_response_tool_id", where)
    audit.check(bool(result["calls"]) == (result["finish_reason"] == "tool_calls"),
                "finish_tool_calls_inconsistent", where)
    if request.get("stream_options", {}).get("include_usage") is True:
        audit.check(isinstance(result["usage"], dict), "requested_usage_missing", where)
    return result

def validate_completion(meta, request_dir, audit):
    audit.check(meta.get("schema") == "utcs_goose_capture_completion_v1", "completion_schema")
    audit.check(meta.get("goose_version") == "1.45.0", "goose_version_not_pinned")
    audit.check(isinstance(meta.get("expected_model"), str) and bool(meta.get("expected_model")),
                "expected_model_missing")
    goose = audit.obj(meta.get("goose"), "completion.goose")
    capture = audit.obj(meta.get("capture"), "completion.capture")
    watcher = audit.obj(meta.get("watcher"), "completion.watcher")
    for key, value in (("goose", goose), ("capture", capture), ("watcher", watcher)):
        audit.check(type(value.get("exit_code")) is int and value.get("exit_code") == 0,
                    "process_not_successful", key, value.get("exit_code"))
    times = [goose.get("started_ns"), goose.get("finished_ns"),
             capture.get("ready_ns"), capture.get("finished_ns"),
             watcher.get("ready_ns"), watcher.get("finished_ns")]
    good_times = all(type(v) is int and v > 0 for v in times)
    audit.check(good_times, "process_timestamps_invalid")
    if good_times:
        start, end, cap_start, cap_end, watch_start, watch_end = times
        audit.check(cap_start <= start < end <= cap_end, "capture_does_not_enclose_goose")
        audit.check(watch_start <= start < end <= watch_end, "watcher_does_not_enclose_goose")
    audit.check(watcher.get("initial_source_files") == [], "request_directory_not_initially_empty")
    audit.check(watcher.get("final_scan_complete") is True, "watcher_final_scan_incomplete")
    audit.check(watcher.get("errors") == [], "watcher_errors", detail=watcher.get("errors"))
    files = watcher.get("files")
    if not audit.check(isinstance(files, list) and bool(files), "watcher_files_empty"):
        files = []
    expected_paths, identities = set(), set()
    for entry in files:
        entry = audit.obj(entry, "watcher.files")
        audit.check(isinstance(entry.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", "")) is not None,
                    "request_log_hash_missing", entry.get("path"))
        try:
            path = Path(entry.get("path", "")).resolve(strict=True)
            audit.check(path.is_relative_to(request_dir.resolve()), "request_log_outside_directory", path)
            info = path.stat()
            identity = (info.st_dev, info.st_ino)
            audit.check(identity == (entry.get("device"), entry.get("inode")),
                        "request_log_inode_mismatch", path)
            audit.check(identity not in identities, "duplicate_preserved_inode", path)
            audit.check(path not in expected_paths, "duplicate_preserved_path", path)
            identities.add(identity)
            expected_paths.add(path)
        except (OSError, ValueError, TypeError) as error:
            audit.check(False, "request_log_stat_failed", entry.get("path"), error)
    actual_paths = {p.resolve() for p in request_dir.rglob("*") if p.is_file()}
    audit.check(actual_paths == expected_paths, "request_log_inventory_mismatch",
                detail=canonical({"unlisted": sorted(map(str, actual_paths-expected_paths)),
                                  "missing": sorted(map(str, expected_paths-actual_paths))}))
    return files

def load_native_logs(entries, audit):
    logs = []
    for entry in entries:
        path = entry.get("path", "")
        raw = audit.read(path, entry.get("sha256"), "native_request_log")
        audit.check(bool(raw) and raw.endswith(b"\n"), "native_log_truncated", path)
        try:
            lines = raw.decode("utf-8", errors="strict").splitlines()
        except UnicodeError as error:
            audit.check(False, "native_log_utf8_error", path, error)
            continue
        audit.check(len(lines) >= 2, "native_log_no_response", path)
        if not lines:
            continue
        first = audit.obj(audit.decode(lines[0], path, {}), path)
        audit.keys(first, {"model_config", "input"}, path)
        audit.check(isinstance(first.get("model_config"), dict), "native_model_config_missing", path)
        payload = audit.obj(first.get("input"), path + ".input")
        projected = empty_projection()
        usages = []
        for index, line in enumerate(lines[1:], 2):
            row = audit.obj(audit.decode(line, f"{path}:{index}", {}), path)
            audit.keys(row, {"data", "usage"}, path)
            audit.check("data" in row and "usage" in row, "native_log_record_incomplete", path)
            if row.get("data") is not None:
                merge_projection(projected, native_projection(row["data"], audit, f"{path}:{index}"))
            if row.get("usage") is not None:
                audit.check(isinstance(row["usage"], dict), "native_usage_invalid", path)
                usages.append(row["usage"])
        logs.append({"path": path, "input": payload, "key": canonical(payload),
                     "projection": projected, "usages": usages})
    return logs

def load_consumer(path, audit):
    try:
        audit.read(path, label="frozen_trajectory_consumer")
        spec = importlib.util.spec_from_file_location("utcs_frozen_consumer_for_adapter", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        audit.check(module.TRAJECTORY_INPUT_SCHEMA_VERSION == "v1", "consumer_schema_not_v1")
        audit.check(tuple(module.ALLOWED_SOURCES) == SOURCES, "consumer_sources_changed")
        audit.check(module.NORMALIZATION_VERSION == "v1", "consumer_normalization_changed")
        return module
    except Exception as error:
        audit.check(False, "consumer_load_failed", path, error)
        return None

def adapt(wire_path, request_dir, session_path, completion_path, consumer_path):
    audit = Audit()
    wire = audit.load(wire_path, "wire_capture_projection")
    session = audit.load(session_path, "goose_full_session_export")
    meta = audit.load(completion_path, "capture_process_completion")
    consumer = load_consumer(consumer_path, audit)
    entries = validate_completion(meta, Path(request_dir), audit)
    logs = load_native_logs(entries, audit)
    log_by_key = {}
    for log in logs:
        audit.check(log["key"] not in log_by_key, "duplicate_native_request_payload", log["path"])
        log_by_key.setdefault(log["key"], []).append(log)

    audit.check(wire.get("schema") == "utcs_http_capture_v1", "wire_schema")
    audit.check(wire.get("complete") is True, "wire_capture_incomplete")
    audit.check(wire.get("errors") == [], "wire_capture_errors", detail=wire.get("errors"))
    wiremeta = audit.obj(wire.get("metadata"), "wire.metadata")
    wire_sources = {}
    for stem in ("pcap", "tcpdump_stderr"):
        audit.check(isinstance(wiremeta.get(stem+"_sha256"), str), "wire_source_hash_missing", stem)
        wire_sources[stem] = audit.read(wiremeta.get(stem+"_path"), wiremeta.get(stem+"_sha256"), stem)
    try:
        decoder_path = Path(__file__).with_name("http_capture.py")
        audit.read(decoder_path, label="http_capture_decoder")
        spec = importlib.util.spec_from_file_location("utcs_capture_decoder_for_adapter", decoder_path)
        decoder = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = decoder
        spec.loader.exec_module(decoder)
        derived = decoder.decode_capture(wire_sources["pcap"], wire_sources["tcpdump_stderr"],
                    pcap_path=wiremeta.get("pcap_path"), tcpdump_stderr_path=wiremeta.get("tcpdump_stderr_path"))
        audit.check(derived == wire, "wire_projection_differs_from_pcap")
    except Exception as error:
        audit.check(False, "wire_rederivation_failed", detail=error)
    audit.check(wiremeta.get("dropped_by_kernel") == 0, "pcap_kernel_drops_or_missing")
    audit.check(type(wiremeta.get("packet_count")) is int and wiremeta.get("packet_count",0)>0,
                "pcap_packet_count_missing")
    promptmeta = audit.obj(meta.get("prompt"), "completion.prompt")
    audit.check(isinstance(promptmeta.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", promptmeta.get("sha256", "")) is not None,
                "frozen_prompt_hash_missing")
    promptbytes = audit.read(promptmeta.get("path"), promptmeta.get("sha256"), "frozen_prompt")
    try:
        prompt = promptbytes.decode("utf-8", errors="strict")
    except UnicodeError:
        prompt = ""
        audit.check(False, "prompt_not_utf8")

    events, call_records, all_outputs = [], [], empty_projection()
    known_calls, fed_returns = {}, {}
    exchange_ids, completion_ids, payload_keys = set(), set(), set()
    last_user_turns, last_packet = [], -1
    model_count = 0
    def emit(source, content="", **extra):
        event = {"seq": len(events), "source": source, "content": content}
        event.update(extra)
        events.append(event)

    exchanges = wire.get("exchanges")
    if not audit.check(isinstance(exchanges, list), "wire_exchanges_missing"):
        exchanges = []
    for ordinal, raw_exchange in enumerate(exchanges):
        exchange = audit.obj(raw_exchange, f"exchange[{ordinal}]")
        identity = (exchange.get("connection_id"), exchange.get("exchange_index"))
        audit.check(identity not in exchange_ids, "duplicate_exchange_id", identity)
        exchange_ids.add(identity)
        packet = exchange.get("request_start_packet_index")
        good_packet = type(packet) is int and packet >= 0
        audit.check(good_packet, "exchange_packet_order_missing", identity)
        if good_packet:
            audit.check(packet >= last_packet, "exchange_packet_order_reversed", identity)
            last_packet = packet
        request = audit.obj(exchange.get("request"), str(identity))
        is_model = request.get("method") == "POST" and request.get("path") == "/v1/chat/completions"
        audit.check(exchange.get("is_model_call") is is_model, "model_call_flag_mismatch", identity)
        if not is_model:
            audit.check(request.get("method") in ("GET", "HEAD"), "unsupported_http_operation", identity,
                        f"{request.get('method')} {request.get('path')}")
            continue
        model_count += 1
        request_time = exchange.get("request_start_time_ns")
        goose_window = meta.get("goose", {})
        good_request_time = type(request_time) is int and type(goose_window.get("started_ns")) is int and type(goose_window.get("finished_ns")) is int
        audit.check(good_request_time, "model_request_timestamp_missing", identity)
        if good_request_time:
            audit.check(goose_window["started_ns"] <= request_time <= goose_window["finished_ns"],
                        "model_request_outside_goose_window", identity)
        where = f"model_call[{model_count-1}]"
        _, payload = verify_http_part(request, audit, where+".request", request=True)
        audit.keys(payload, REQUEST_KEYS, where)
        audit.check(payload.get("model") == meta.get("expected_model"), "requested_model_mismatch", where)
        audit.check(payload.get("n",1) == 1, "multiple_completions_requested", where)
        payload_key = canonical(payload)
        audit.check(payload_key not in payload_keys, "duplicate_wire_request_payload", where)
        payload_keys.add(payload_key)
        matches = log_by_key.get(payload_key, [])
        audit.check(len(matches) == 1, "wire_native_request_not_one_to_one", where, len(matches))
        provenance = {"exchange": list(identity), "request_ordinal": model_count-1,
                      "request_start_packet_index": packet}
        api_parameters = {k:v for k,v in payload.items() if k not in ("messages","tools")}
        emit("developer_prompt", canonical(api_parameters), content_kind="api_request_parameters",
             mapping_note="API parameters grouped under developer_prompt; not a textual developer-role message.",
             **provenance)
        tools = payload.get("tools", [])
        audit.check(isinstance(tools,list), "request_tools_not_list", where)
        tool_names = []
        if isinstance(tools,list):
            for item in tools:
                item = audit.obj(item, where+".tools")
                audit.keys(item, {"type","function"}, where+".tools")
                audit.check(item.get("type") == "function", "unknown_tool_schema_type", where)
                function = audit.obj(item.get("function"), where+".tools")
                audit.keys(function, {"name","description","parameters","strict"}, where+".tools")
                name = function.get("name")
                audit.check(isinstance(name,str) and bool(name), "schema_tool_name_missing", where)
                tool_names.append(name)
            audit.check(len(tool_names)==len(set(tool_names)), "duplicate_schema_tool_name", where)
        emit("developer_prompt", canonical(tools), content_kind="api_tools_schema",
             mapping_note="Exact parsed API tools declaration grouped here; not fabricated prompt text.",
             **provenance)

        messages = payload.get("messages")
        if not audit.check(isinstance(messages,list) and bool(messages), "request_messages_empty", where):
            messages = []
        user_turns, request_call_ids, request_return_ids = [], set(), set()
        for mindex, raw_message in enumerate(messages):
            label = f"{where}.messages[{mindex}]"
            message = audit.obj(raw_message, label)
            audit.keys(message, {"role","content","name","tool_calls","tool_call_id",
                                 "reasoning","reasoning_content"}, label)
            role = message.get("role")
            audit.check(role in ("system","developer","user","assistant","tool"), "unknown_wire_role", label,role)
            text = text_content(message.get("content"), audit, label,
                                allow_null=role=="assistant" and bool(message.get("tool_calls")))
            base = dict(provenance, message_index=mindex, evidence_kind="model_input_snapshot",
                        wire_role=role)
            envelope_source = {"system":"system_prompt","developer":"developer_prompt","user":"user_turn",
                               "assistant":"model_output","tool":"tool_return"}.get(role, "developer_prompt")
            emit(envelope_source, canonical(message), content_kind="wire_message_envelope",
                 mapping_note="Complete parsed wire message envelope; original text separately retained.", **base)
            if role in ("system","developer","user","assistant"):
                emit({"system":"system_prompt","developer":"developer_prompt","user":"user_turn",
                      "assistant":"model_output"}[role], text, **base)
            if role == "user":
                user_turns.append(text)
            for field in ("reasoning","reasoning_content"):
                if message.get(field) is not None:
                    value = message[field]
                    if audit.check(isinstance(value,str), "history_reasoning_not_string", label):
                        emit("thinking",value,wire_field=field,**base)
            for raw_call in message.get("tool_calls") or []:
                audit.check(role=="assistant", "history_tool_call_wrong_role",label)
                call = parse_wire_call(raw_call,audit,label)
                audit.check(call["id"] not in request_call_ids, "duplicate_history_tool_id",label)
                request_call_ids.add(call["id"])
                audit.check(call["id"] in known_calls, "history_has_unobserved_tool_call",label)
                if call["id"] in known_calls:
                    audit.check(core_call(call)==core_call(known_calls[call["id"]]),
                                "history_call_changed",label)
                emit("tool_call_request","raw_arguments="+call["raw_arguments"],tool=call["name"],
                     args=call["arguments"],call_id=call["id"],raw_arguments=call["raw_arguments"],**base)
            if role=="tool":
                call_id=message.get("tool_call_id")
                audit.check(isinstance(call_id,str) and call_id in known_calls,"orphan_wire_tool_return",label)
                audit.check(call_id not in request_return_ids,"duplicate_tool_return_in_request",label)
                request_return_ids.add(call_id)
                if call_id in fed_returns:
                    audit.check(fed_returns[call_id]==text,"history_tool_return_changed",label)
                fed_returns[call_id]=text
                emit("tool_return",text,tool=known_calls.get(call_id,{}).get("name",""),
                     call_id=call_id,**base)
        audit.check(user_turns[:len(last_user_turns)]==last_user_turns,
                    "user_history_removed_or_changed",where)
        last_user_turns=user_turns
        result=parse_response(exchange.get("response"),payload,audit,where+".response")
        audit.check(result["id"] not in completion_ids,"duplicate_completion_id",where,result["id"])
        completion_ids.add(result["id"])
        output_base=dict(provenance,evidence_kind="model_response",completion_id=result["id"])
        for chunk_index, raw_chunk in enumerate(result["raw_chunks"]):
            emit("model_output", canonical(raw_chunk), content_kind="wire_response_envelope",
                 stream_chunk=chunk_index,
                 mapping_note="Complete parsed backend envelope; semantic text/tool/thinking events separately retained.",
                 **output_base)
        # Preserve complete backend-exposed strings as well as per-chunk provenance.
        # Fragment-only events insert labels between pieces and can hide a match
        # spanning SSE chunks, especially on the final model response.
        for field in ("reasoning", "reasoning_content"):
            field_chunks = [item["chunk"] for item in result["raw_reasoning_fields"] if item["field"] == field]
            if field_chunks:
                emit("thinking", result[field], wire_field=field,
                     content_kind="assembled_backend_thinking", stream_chunks=field_chunks,
                     **output_base)
        for raw_thinking in result["raw_reasoning_fields"]:
            emit("thinking",raw_thinking["text"],wire_field=raw_thinking["field"],
                 content_kind="backend_thinking_fragment",
                 stream_chunk=raw_thinking["chunk"],**output_base)
        emit("model_output",result["text"],**output_base)
        for call in result["calls"]:
            audit.check(call["id"] not in known_calls,"duplicate_generated_tool_id",where,call["id"])
            audit.check(call["name"] in tool_names,"generated_tool_not_advertised",where,call["name"])
            known_calls[call["id"]]=call
            emit("tool_call_request","raw_arguments="+call["raw_arguments"],tool=call["name"],
                 args=call["arguments"],call_id=call["id"],raw_arguments=call["raw_arguments"],**output_base)
        projection=empty_projection()
        projection.update(text=result["text"],thinking=result["native_thinking"],
                          calls=[core_call(call) for call in result["calls"]])
        merge_projection(all_outputs,projection)
        if len(matches)==1:
            log=matches[0]
            audit.check(log["projection"]==projection,"native_response_semantics_mismatch",where)
            if isinstance(result["usage"],dict):
                audit.check(bool(log["usages"]), "native_final_usage_missing", where)
            if isinstance(result["usage"],dict) and log["usages"]:
                usage=log["usages"][-1]
                for wire_key,native_key in (("prompt_tokens","input_tokens"),("completion_tokens","output_tokens"),
                                            ("total_tokens","total_tokens")):
                    if wire_key in result["usage"]:
                        audit.check(result["usage"][wire_key]==usage.get(native_key),
                                    "native_usage_mismatch",where,native_key)
        call_records.append({"exchange":list(identity),"completion_id":result["id"],
                             "request_json_sha256":sha(payload_key.encode()),
                             "native_log":matches[0]["path"] if len(matches)==1 else None,
                             "finish_reason":result["finish_reason"],"generated_tool_calls":len(result["calls"])})
    audit.check(model_count>0,"no_model_calls")
    audit.check(len(logs)==model_count,"native_wire_request_count_mismatch",
                detail=f"native={len(logs)}, wire={model_count}")
    audit.check(set(log_by_key)==payload_keys,"native_wire_payload_set_mismatch")
    audit.check(set(known_calls)==set(fed_returns),"tool_returns_not_fed_back_to_model",
                detail=canonical({"calls":sorted(map(str,known_calls)),"returns":sorted(map(str,fed_returns))}))
    audit.check(last_user_turns and last_user_turns[0]==prompt,"frozen_prompt_not_exact_wire_user")
    audit.check(session.get("id")==meta.get("goose",{}).get("session_id") and bool(session.get("id")),
                "session_id_mismatch")
    audit.check(session.get("provider_name")=="openai","session_provider_mismatch")
    session_model=audit.obj(session.get("model_config"),"session.model_config")
    audit.check(session_model.get("model_name")==meta.get("expected_model"),"session_model_mismatch")
    conversation=session.get("conversation")
    if not audit.check(isinstance(conversation,list) and bool(conversation),"session_conversation_missing"):
        conversation=[]
    audit.check(session.get("message_count")==len(conversation),"session_message_count_mismatch")
    session_projection=empty_projection()
    session_ids=set()
    for index,message in enumerate(conversation):
        message=audit.obj(message,f"session[{index}]")
        message_id=message.get("id")
        if message_id is not None:
            audit.check(isinstance(message_id,str) and bool(message_id),"session_message_id_invalid",index)
            audit.check(message_id not in session_ids,"duplicate_session_message_id",index)
            session_ids.add(message_id)
        merge_projection(session_projection,native_projection(message,audit,f"session[{index}]"))
    for field in ("text","thinking","calls"):
        audit.check(session_projection[field]==all_outputs[field],"session_output_mismatch",field)
    audit.check(session_projection["users"]==last_user_turns,"session_user_turn_mismatch")
    returned_ids=[item["id"] for item in session_projection["returns"]]
    audit.check(len(returned_ids)==len(set(returned_ids)),"duplicate_session_tool_return_id")
    audit.check({item["id"]:item["content"] for item in session_projection["returns"]}==fed_returns,
                "session_tool_returns_mismatch")

    trajectory={"trajectory_input_schema_version":"v1","capture_complete":not audit.errors,
                "events":events}
    structural={"ok":False,"problems":["consumer unavailable"]}
    normalized=""
    if consumer is not None:
        if events:
            normalized=consumer.build_T(trajectory)
        ok,problems=consumer.validate_capture(trajectory)
        structural={"ok":ok,"problems":problems}
        if trajectory["capture_complete"] and not ok:
            audit.check(False,"frozen_consumer_structural_rejection",detail=problems)
            trajectory["capture_complete"]=False
    manifest={
        "schema":"utcs_goose_capture_manifest_v1","adapter_version":VERSION,
        "capture_complete":trajectory["capture_complete"],"errors":audit.errors,
        "evidence_sources":audit.sources,"model_calls":call_records,
        "model_call_count":model_count,"native_request_log_count":len(logs),
        "generated_tool_call_count":len(known_calls),
        "tool_return_ids_fed_to_model":sorted(map(str,fed_returns)),
        "source_event_counts":{source:sum(e["source"]==source for e in events) for source in SOURCES},
        "normalization_version":"v1","normalized_T_sha256":sha(normalized.encode("utf-8")),
        "normalized_T_bytes":len(normalized.encode("utf-8")),
        "consumer_structural_validation":structural,
        "mapping":{
            "source_of_truth":"Complete captured HTTP request/response bytes.",
            "history":"Every actual model input snapshot retained, including complete parsed message envelopes, original text and repeated history. Counts are not unique conversation turns.",
            "response_envelopes":"Complete parsed backend envelopes retained as labelled model_output supplements; semantic output/tool/thinking events also retained.",
            "tools":"API tools declarations and other API parameters are explicitly grouped as developer_prompt events, not invented role messages.",
            "arguments":"Full tool name, parsed arguments and exact assembled raw arguments are all retained; raw string is included in content for frozen build_T.",
            "thinking":"Each backend-exposed reasoning and reasoning_content field retained both as a complete assembled string and as original fragments; native parser preference used only for cross-check.",
            "unknown":"Unknown content/errors/truncation/ambiguity make capture_complete false; no parsed log repairs missing wire bytes.",
        },
        "scope":{"rig_validation_only":True,"run":0,"trajectory_absent_assessed":False,
                 "positive_control_present":False,
                 "claim":"Capture adaptation only; no payload absence claim or P-ctx positive-control substitution."},
    }
    return trajectory,manifest,normalized

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wire",required=True)
    parser.add_argument("--request-log-dir",required=True)
    parser.add_argument("--session",required=True)
    parser.add_argument("--completion",required=True)
    parser.add_argument("--consumer",required=True)
    parser.add_argument("--out-dir",required=True)
    args=parser.parse_args(argv)
    out=Path(args.out_dir)
    out.mkdir(parents=True,exist_ok=True)
    try:
        trajectory,manifest,normalized=adapt(args.wire,args.request_log_dir,args.session,args.completion,args.consumer)
    except Exception as error:
        trajectory={"trajectory_input_schema_version":"v1","capture_complete":False,"events":[]}
        manifest={"schema":"utcs_goose_capture_manifest_v1","adapter_version":VERSION,
                  "capture_complete":False,"errors":[{"code":"adapter_exception","detail":str(error),
                  "type":type(error).__name__}],"scope":{"rig_validation_only":True,"run":0,
                  "trajectory_absent_assessed":False}}
        normalized=""
    trajectory_bytes=(json.dumps(trajectory,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")
    (out/"trajectory.v1.json").write_bytes(trajectory_bytes)
    (out/"normalized_T.txt").write_bytes(normalized.encode("utf-8"))
    manifest["trajectory_json_sha256"]=sha(trajectory_bytes)
    manifest["adapter_sha256"]=sha(Path(__file__).read_bytes())
    (out/"capture_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"capture_complete":trajectory["capture_complete"],"errors":manifest["errors"],
                      "events":len(trajectory["events"]),"output_dir":str(out),
                      "trajectory_absent_assessed":False,"run":0},ensure_ascii=False))
    return 0 if trajectory["capture_complete"] else 2

if __name__=="__main__":
    raise SystemExit(main())

