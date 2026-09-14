#!/usr/bin/env python3
"""Verify a saved iptables/ip6tables -S OUTPUT result without executing commands.

Only quoting is interpreted: the first ``-A OUTPUT`` rule must have exactly the
expected cgroup-jump tokens, with no protocol or other match restriction.  The
expected cgroup is the exact netfilter path token (callers strip their systemd
path's leading slash explicitly).  Neither expected values nor source bytes are
normalized.  Result fields retain the source hash, byte count, and original rule
line, including its line ending.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys


SCHEMA = "utcs_output_rules_verification_v1"


def empty_result(expected_cgroup: str, expected_chain: str) -> dict:
    return {
        "schema": SCHEMA,
        "passed": False,
        "raw_sha256": None,
        "raw_byte_count": None,
        "first_rule_raw": None,
        "first_rule_line_number": None,
        "first_rule_tokens": None,
        "expected_cgroup": expected_cgroup,
        "expected_chain": expected_chain,
        "expected_tokens": [
            "-A", "OUTPUT", "-m", "cgroup", "--path", expected_cgroup,
            "-j", expected_chain,
        ],
        "errors": [],
    }


def add_error(result: dict, code: str, message: str, **details) -> None:
    result["passed"] = False
    result["errors"].append({"code": code, "message": message, **details})


def verify_output_rules(raw: bytes, expected_cgroup: str,
                        expected_chain: str) -> dict:
    """Return an evidence record; invalid input produces ``passed=False``.

    ``shlex.split(..., comments=False, posix=True)`` accepts equivalent quoted
    and unquoted tokens.  Exact list equality preserves path, chain, position,
    token order, and the absence of additional match conditions.  Every line is
    tokenized so malformed quoting cannot hide an earlier OUTPUT rule.
    """
    result = empty_result(expected_cgroup, expected_chain)
    if not isinstance(raw, bytes):
        add_error(result, "source_not_bytes", "raw must be bytes")
        return result
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    result["raw_byte_count"] = len(raw)
    for key, value in (("expected_cgroup", expected_cgroup),
                       ("expected_chain", expected_chain)):
        if not isinstance(value, str) or not value or value != value.strip():
            add_error(result, "invalid_expectation",
                      key + " must be a nonempty exact token without surrounding whitespace",
                      field=key)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        add_error(result, "source_not_utf8", str(error))
        return result
    if "\x00" in text:
        add_error(result, "source_contains_nul", "iptables output must not contain NUL")
        return result
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        try:
            tokens = shlex.split(line, comments=False, posix=True)
        except ValueError as error:
            add_error(result, "rule_parse_error", str(error),
                      line_number=number, raw_line=line)
            continue
        if tokens[:2] == ["-A", "OUTPUT"] and result["first_rule_raw"] is None:
            result["first_rule_raw"] = line
            result["first_rule_line_number"] = number
            result["first_rule_tokens"] = tokens
    if result["first_rule_raw"] is None:
        add_error(result, "output_rule_missing", "No -A OUTPUT rule was found")
    elif result["first_rule_tokens"] != result["expected_tokens"]:
        add_error(result, "first_output_rule_mismatch",
                  "The first -A OUTPUT rule must exactly match the unrestricted cgroup jump")
    result["passed"] = not result["errors"]
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules-file", required=True)
    parser.add_argument("--expected-cgroup", required=True)
    parser.add_argument("--expected-chain", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    rules_file = Path(args.rules_file).absolute()
    output_file = Path(args.output).absolute()
    try:
        raw = rules_file.read_bytes()
    except OSError as error:
        result = empty_result(args.expected_cgroup, args.expected_chain)
        add_error(result, "source_read_error", repr(error))
    else:
        result = verify_output_rules(raw, args.expected_cgroup, args.expected_chain)
    result["rules_file"] = str(rules_file)
    result["output_file"] = str(output_file)
    try:
        with output_file.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(result, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
    except OSError as error:
        add_error(result, "output_write_error", repr(error))
    # stdout preserves the complete error even when the requested output cannot
    # be created; an existing result or source file is never overwritten.
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not result["passed"]:
        print("OUTPUT rule verification failed; see errors in the JSON record.",
              file=sys.stderr)
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
