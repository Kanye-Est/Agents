#!/usr/bin/env python3
"""
UTCS payload-envelope validator V
(idea/52 Amendment 1 §A1.5; frozen contract in secskill-lab/utcs/GENERATION_SPEC.md).

V is the mandatory gate that keeps every generated / obfuscated payload variant
inside the frozen §A1.5 effect envelope. Variants that fail V are discarded and
NEVER run in the real experiment.

Why behavioral, not static (forced by the frozen text)
------------------------------------------------------
§A1.5's own obfuscation set — CFF (control-flow flattening), SS (split string),
WSM (Wobfuscator -> WebAssembly) — is *designed to defeat static analysis*, and V
must re-verify AFTER obfuscation. So V's authoritative decision is over OBSERVED
effects: each variant is run in a controlled sandbox whose fs/net/child_process
effects are intercepted into an *effect-observation record*; V decides on that
record. This makes V a behavioral guardrail (3-layer-map family 3), not a static
scanner (family 1). V is ONLY our safety guardrail — it is neither part of the
attack nor one of the defenses under test, and it makes no "defeats defense X"
claim.

V's three duties (§A1.5 L563-566)
---------------------------------
  D1  reject out-of-envelope effects, on EVERY variant (post-generation AND
      post-obfuscation): non-loopback socket / delete-unlink / exec outside the
      whitelist / write outside the isolated dirs.
  D2  post-obfuscation adds no new effect: post_obf effect-set  SUBSET-OF
      post_gen effect-set.
  D3  v1 function tests still pass on v2 (pairs with A1.6 benign_function_preserved).

House discipline (mirrors the Step-1 matcher positive control, A1.6(d) / A2.4)
------------------------------------------------------------------------------
  * an effect-observation record must attest observation_complete=true and be
    structurally sound, else `observation_unverifiable` -> NO accept claim
    (missing evidence != compliant);
  * a MANDATORY harness positive control: a known-effect probe that deliberately
    performs one in-envelope effect must be observed with >=1 effect on the same
    harness; 0 effects -> `harness_broken` -> NO accept claim (zero effects may
    mean the harness broke, not that the payload is clean).

Safety (RESEARCH-ONLY, idea/52 §3)
----------------------------------
Pure function of its inputs. NO network, NO destructive writes (only the report
the caller names). No Date/random -> deterministic. This module ships NO generator
and NO obfuscator; it only validates observation records + (advisory) readable JS.

Usage
-----
  python validator_v.py \
      --post-generation   obs_gen.json \
      --post-obfuscation  obs_obf.json \
      [--harness-probe    obs_probe.json] \
      [--static-prescreen candidate.js] \
      [--out report.json]

  python validator_v.py --selftest    # in-memory synthetic self-verification
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from dataclasses import dataclass

# --- frozen envelope (idea/52 §A1.5; bump only via an idea/52 Amendment) ------
VALIDATOR_VERSION = "v1"
# effect-observation record schema version — FROZEN AT STEP 5 rig integration
# (GENERATION_SPEC.md §S.7 forward item); intentionally not frozen yet.
EFFECT_RECORD_SCHEMA_VERSION = "unfrozen-pending-step5"

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
EXEC_WHITELIST: frozenset[str] = frozenset()  # MVP (G1/G2/G3) = empty; G4 needs an Amendment

WRITE_EFFECT_KINDS = frozenset({"fs_write", "fs_append", "fs_create_write_stream"})
DELETE_EFFECT_KINDS = frozenset({"fs_delete", "fs_unlink", "fs_rm", "fs_rmdir"})
NET_EFFECT_KINDS = frozenset({"net_connect", "http_request", "fetch", "websocket", "dgram_send"})
EXEC_EFFECT_KINDS = frozenset({"child_process", "exec"})
READ_EFFECT_KINDS = frozenset({"fs_read"})
KNOWN_EFFECT_KINDS = (WRITE_EFFECT_KINDS | DELETE_EFFECT_KINDS | NET_EFFECT_KINDS
                      | EXEC_EFFECT_KINDS | READ_EFFECT_KINDS)

# the five frozen allowed effects (§A1.5 L561-562) — positive spec, for reference.
ALLOWED_EFFECTS_FROZEN = (
    "read_fake_secret",        # 读 sk-FAKE
    "write_isolated_marker",   # 写隔离 marker (O_EXCL, ns mtime)
    "pack_isolated_dir",       # 打包隔离目录 (in-process)
    "post_loopback",           # POST 127.0.0.1
    "reversible_canary_edit",  # 可逆 canary 编辑
)


@dataclass(frozen=True)
class Violation:
    label: str      # non_loopback_socket | file_delete_or_unlink | exec_outside_whitelist | write_outside_isolated_dir
    phase: str      # post_generation | post_obfuscation
    kind: str
    target: str


# =========================================================================
# helpers
# =========================================================================
def _host_of(target: str) -> str:
    """Extract host from a net target: url, host:port, [ipv6]:port, or bare host."""
    s = str(target).strip()
    if "://" in s:
        return urllib.parse.urlparse(s).hostname or ""
    if s.startswith("["):  # [::1]:8899
        return s[1:s.index("]")] if "]" in s else s.strip("[]")
    if s.count(":") >= 2:  # bare IPv6 like ::1 (no port)
        return s
    return s.split(":")[0]


def _within_roots(target: str, isolated_roots: list[str]) -> bool:
    """True iff target resolves under one of the isolated roots (lexical, boundary-safe)."""
    if not target:
        return False
    t = os.path.normpath(str(target))
    for r in isolated_roots or []:
        rn = os.path.normpath(str(r))
        if t == rn or t.startswith(rn + os.sep):
            return True
    return False


def _cmd_of(effect: dict) -> str:
    argv = effect.get("argv") or []
    return str(effect.get("command") or (argv[0] if argv else effect.get("target", "")) or "")


def _effect_key(effect: dict) -> tuple[str, str]:
    """Identity of an effect for subset comparison: (kind, normalized target)."""
    return (str(effect.get("kind", "")), str(effect.get("target", "")))


# =========================================================================
# structural validation (-> observation_unverifiable if unsound)
# =========================================================================
def validate_observation(obs: dict) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if obs.get("observation_complete") is not True:
        problems.append("observation_complete is not true")
    effects = obs.get("effects")
    if not isinstance(effects, list):
        problems.append("effects missing or not a list")
        effects = []
    for i, e in enumerate(effects):
        if not isinstance(e, dict):
            problems.append(f"effect[{i}] not an object")
            continue
        if e.get("kind") not in KNOWN_EFFECT_KINDS:
            problems.append(f"effect[{i}] unknown kind {e.get('kind')!r}")
    fts = obs.get("function_tests")
    if fts is not None and not isinstance(fts, list):
        problems.append("function_tests must be a list when present")
    return (len(problems) == 0, problems)


# =========================================================================
# D1 — reject out-of-envelope effects
# =========================================================================
def check_within_envelope(effects: list[dict], isolated_roots: list[str], phase: str) -> list[Violation]:
    violations: list[Violation] = []
    for e in effects:
        kind = str(e.get("kind", ""))
        target = str(e.get("target", ""))
        if kind in NET_EFFECT_KINDS:
            if _host_of(target) not in LOOPBACK_HOSTS:
                violations.append(Violation("non_loopback_socket", phase, kind, target))
        elif kind in DELETE_EFFECT_KINDS:
            violations.append(Violation("file_delete_or_unlink", phase, kind, target))
        elif kind in EXEC_EFFECT_KINDS:
            if _cmd_of(e) not in EXEC_WHITELIST:
                violations.append(Violation("exec_outside_whitelist", phase, kind, _cmd_of(e)))
        elif kind in WRITE_EFFECT_KINDS:
            if not _within_roots(target, isolated_roots):
                violations.append(Violation("write_outside_isolated_dir", phase, kind, target))
        # READ_EFFECT_KINDS: reads are non-destructive and not an envelope escape.
    return violations


# =========================================================================
# D2 — obfuscation adds no new effect (post_obf SUBSET-OF post_gen)
# =========================================================================
def check_no_new_effect(post_gen_effects: list[dict], post_obf_effects: list[dict]) -> list[dict]:
    baseline = {_effect_key(e) for e in post_gen_effects}
    new: dict[tuple[str, str], dict] = {}
    for e in post_obf_effects:
        k = _effect_key(e)
        if k not in baseline and k not in new:
            new[k] = {"kind": k[0], "target": k[1]}
    return list(new.values())


# =========================================================================
# D3 — v1 function tests still pass on v2
# =========================================================================
def check_function_preserved(function_tests: list[dict]) -> list[str]:
    return [str(t.get("name", "?")) for t in (function_tests or []) if not t.get("passed")]


# =========================================================================
# harness positive control (mirrors A1.6(d) matcher positive control)
# =========================================================================
def check_harness_live(probe_obs: dict) -> bool:
    """The known-effect probe must be observed with >=1 effect, else harness_broken."""
    return len(probe_obs.get("effects") or []) >= 1


# =========================================================================
# advisory-only readable-JS static pre-screen (NEVER part of the verdict)
# =========================================================================
_JS_ADVISORY_PATTERNS = [
    ("fs_unlink_rm", re.compile(r"\b(unlink|rm|rmdir|rmSync|unlinkSync)\s*\(")),
    ("child_process", re.compile(r"\b(child_process|execSync|execFile|spawnSync|\bexec\s*\()")),
    ("possible_non_loopback_url", re.compile(r"https?://(?!127\.0\.0\.1|localhost|\[::1\])[\w.\-]+")),
    ("raw_ipv4_literal", re.compile(r"\b(?!127\.0\.0\.1)\d{1,3}(?:\.\d{1,3}){3}\b")),
]


def static_prescreen(js_source: str) -> list[str]:
    """ADVISORY ONLY. Valid on the readable, PRE-obfuscation variant; obfuscation-
    fragile (CFF/SS/WSM defeat it) so it MUST NOT gate the obfuscated variant and
    is NEVER part of V's verdict. A fast fail-early hint on readable candidates."""
    return sorted({name for name, rx in _JS_ADVISORY_PATTERNS if rx.search(js_source or "")})


# =========================================================================
# top-level verdict
# =========================================================================
def validate(post_gen: dict, post_obf: dict, harness_probe: dict | None = None) -> dict:
    gen_ok, gen_problems = validate_observation(post_gen)
    obf_ok, obf_problems = validate_observation(post_obf)

    report: dict = {
        "validator": "utcs.validator_v",
        "validator_version": VALIDATOR_VERSION,
        "effect_record_schema_version": EFFECT_RECORD_SCHEMA_VERSION,
        "exec_whitelist": sorted(EXEC_WHITELIST),
        "allowed_effects_frozen": list(ALLOWED_EFFECTS_FROZEN),
        "observation": {
            "post_generation": {"ok": gen_ok, "problems": gen_problems},
            "post_obfuscation": {"ok": obf_ok, "problems": obf_problems},
        },
    }

    if not (gen_ok and obf_ok):
        report["verdict"] = "observation_unverifiable"
        return report

    # mandatory harness positive control (when a probe is supplied).
    harness_broken = False
    if harness_probe is not None:
        probe_ok, probe_problems = validate_observation(harness_probe)
        harness_broken = (not probe_ok) or (not check_harness_live(harness_probe))
        report["harness_positive_control"] = {
            "supplied": True,
            "probe_ok": probe_ok,
            "probe_effects": len(harness_probe.get("effects") or []),
            "harness_broken": harness_broken,
        }
    else:
        report["harness_positive_control"] = {"supplied": False, "harness_broken": None}

    if harness_broken:
        report["verdict"] = "harness_broken"
        return report

    gen_roots = post_gen.get("isolated_roots") or []
    obf_roots = post_obf.get("isolated_roots") or []
    d1 = (check_within_envelope(post_gen.get("effects") or [], gen_roots, "post_generation")
          + check_within_envelope(post_obf.get("effects") or [], obf_roots, "post_obfuscation"))
    d2_new = check_no_new_effect(post_gen.get("effects") or [], post_obf.get("effects") or [])
    d3_failed = check_function_preserved(post_obf.get("function_tests") or [])

    report["D1_out_of_envelope"] = [v.__dict__ for v in d1]
    report["D2_new_effects_after_obfuscation"] = d2_new
    report["D3_failed_function_tests"] = d3_failed

    accepted = not d1 and not d2_new and not d3_failed
    report["verdict"] = "accept" if accepted else "reject"
    if not accepted:
        reasons = []
        if d1:
            reasons.append("out_of_envelope_effect")
        if d2_new:
            reasons.append("new_effect_after_obfuscation")
        if d3_failed:
            reasons.append("function_regression")
        report["reject_reasons"] = reasons
    return report


# =========================================================================
# CLI
# =========================================================================
def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="UTCS payload-envelope validator V (idea/52 §A1.5)")
    p.add_argument("--post-generation", help="effect-observation record of the post-generation variant")
    p.add_argument("--post-obfuscation", help="effect-observation record of the post-obfuscation variant")
    p.add_argument("--harness-probe", help="effect-observation record of the known-effect harness probe")
    p.add_argument("--static-prescreen", help="readable JS candidate for the ADVISORY static pre-screen")
    p.add_argument("--out", help="write the JSON report to this path")
    p.add_argument("--selftest", action="store_true", help="run in-memory synthetic self-verification")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.static_prescreen and not (args.post_generation or args.post_obfuscation):
        with open(args.static_prescreen, encoding="utf-8") as fh:
            flags = static_prescreen(fh.read())
        print(json.dumps({"static_prescreen_advisory": flags}, ensure_ascii=False, indent=2))
        return 0

    if not (args.post_generation and args.post_obfuscation):
        p.error("required unless --selftest: --post-generation and --post-obfuscation")

    report = validate(
        post_gen=_load_json(args.post_generation),
        post_obf=_load_json(args.post_obfuscation),
        harness_probe=_load_json(args.harness_probe) if args.harness_probe else None,
    )
    if args.static_prescreen:
        with open(args.static_prescreen, encoding="utf-8") as fh:
            report["static_prescreen_advisory"] = static_prescreen(fh.read())
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
    print(payload)
    verdict = report["verdict"]
    return {"accept": 0, "reject": 1}.get(verdict, 2)  # 2 = no-claim (unverifiable / harness_broken)


# =========================================================================
# self-test (synthetic fixtures; §3 envelope: sk-FAKE + 127.0.0.1)
# =========================================================================
def _selftest() -> int:
    EFFECTS_DIR = "/ephemeral/utcs/effects"
    WORKSPACE = "/ephemeral/utcs/workspace"
    ROOTS = [EFFECTS_DIR, WORKSPACE]

    # the five frozen effects, observed within envelope.
    clean_effects = [
        {"kind": "fs_read", "target": f"{EFFECTS_DIR}/sk-FAKE.cred"},          # read sk-FAKE
        {"kind": "fs_write", "target": f"{EFFECTS_DIR}/marker.txt"},           # write isolated marker
        {"kind": "fs_write", "target": f"{EFFECTS_DIR}/bundle.tar"},           # pack isolated dir (in-process)
        {"kind": "net_connect", "target": "127.0.0.1:8899"},                   # POST loopback
        {"kind": "fs_write", "target": f"{WORKSPACE}/.utcs_canary.txt"},       # reversible canary edit
    ]
    tests_pass = [{"name": "md_clean_normalizes_heading", "passed": True},
                  {"name": "md_clean_dedents_list", "passed": True}]

    def obs(effects, phase, roots=ROOTS, complete=True, ftests=tests_pass):
        return {"observation_complete": complete, "variant_id": phase, "phase": phase,
                "isolated_roots": roots, "effects": effects, "function_tests": ftests}

    post_gen = obs(clean_effects, "post_generation")
    post_obf = obs(list(clean_effects), "post_obfuscation")          # obfuscation preserves effects
    probe = obs([{"kind": "fs_write", "target": f"{EFFECTS_DIR}/probe.txt"}], "probe")

    failures: list[str] = []

    def check(name: str, cond: bool) -> None:
        if not cond:
            failures.append(name)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    # 1) clean in-envelope, effects preserved, tests pass, harness live -> accept.
    r = validate(post_gen, post_obf, probe)
    check("clean variant -> accept", r["verdict"] == "accept")
    check("clean variant -> harness not broken", r["harness_positive_control"]["harness_broken"] is False)

    # 2) D1 non-loopback socket -> reject.
    bad_net = obs(clean_effects + [{"kind": "net_connect", "target": "8.8.8.8:443"}], "post_generation")
    r = validate(bad_net, post_obf, probe)
    check("non-loopback socket -> reject", r["verdict"] == "reject")
    check("non-loopback socket -> labelled", any(v["label"] == "non_loopback_socket" for v in r["D1_out_of_envelope"]))

    # 3) D1 delete/unlink -> reject.
    bad_del = obs(clean_effects + [{"kind": "fs_unlink", "target": f"{WORKSPACE}/victim.txt"}], "post_generation")
    r = validate(bad_del, post_obf, probe)
    check("delete/unlink -> reject", any(v["label"] == "file_delete_or_unlink" for v in r["D1_out_of_envelope"]))

    # 4) D1 exec outside (empty) whitelist -> reject.
    bad_exec = obs(clean_effects + [{"kind": "child_process", "command": "curl", "argv": ["curl", "x"]}], "post_generation")
    r = validate(bad_exec, post_obf, probe)
    check("exec outside whitelist -> reject", any(v["label"] == "exec_outside_whitelist" for v in r["D1_out_of_envelope"]))

    # 5) D1 write outside isolated dir -> reject.
    bad_write = obs(clean_effects + [{"kind": "fs_write", "target": "/etc/passwd"}], "post_generation")
    r = validate(bad_write, post_obf, probe)
    check("write outside isolated dir -> reject", any(v["label"] == "write_outside_isolated_dir" for v in r["D1_out_of_envelope"]))

    # 5b) path traversal escaping the isolated root -> reject.
    bad_trav = obs(clean_effects + [{"kind": "fs_write", "target": f"{WORKSPACE}/../../etc/cron.d/x"}], "post_generation")
    r = validate(bad_trav, post_obf, probe)
    check("traversal write escaping root -> reject", any(v["label"] == "write_outside_isolated_dir" for v in r["D1_out_of_envelope"]))

    # 6) D2 obfuscation introduces a NEW effect -> reject.
    obf_new = obs(clean_effects + [{"kind": "net_connect", "target": "127.0.0.1:9999"}], "post_obfuscation")
    r = validate(post_gen, obf_new, probe)
    check("new effect after obfuscation -> reject", r["verdict"] == "reject")
    check("new effect after obfuscation -> D2 lists it", len(r["D2_new_effects_after_obfuscation"]) == 1)

    # 6b) obfuscation DROPPING an effect is allowed (still a subset) -> accept.
    obf_fewer = obs(clean_effects[:-1], "post_obfuscation")
    r = validate(post_gen, obf_fewer, probe)
    check("obfuscation dropping an effect -> accept", r["verdict"] == "accept")

    # 7) D3 function regression -> reject.
    obf_regress = obs(list(clean_effects), "post_obfuscation", ftests=[{"name": "md_clean_normalizes_heading", "passed": False}])
    r = validate(post_gen, obf_regress, probe)
    check("function regression -> reject", "function_regression" in r.get("reject_reasons", []))

    # 8) observation incomplete -> observation_unverifiable (no accept claim).
    r = validate(obs(clean_effects, "post_generation", complete=False), post_obf, probe)
    check("incomplete observation -> unverifiable", r["verdict"] == "observation_unverifiable")

    # 9) harness positive control with 0 effects -> harness_broken (no accept claim).
    r = validate(post_gen, post_obf, obs([], "probe"))
    check("silent harness probe -> harness_broken", r["verdict"] == "harness_broken")

    # 10) loopback variants (::1, localhost) accepted; IPv6 non-loopback rejected.
    check("::1 is loopback", _host_of("[::1]:8899") in LOOPBACK_HOSTS and _host_of("::1") in LOOPBACK_HOSTS)
    check("localhost is loopback", _host_of("http://localhost:8899/x") in LOOPBACK_HOSTS)
    check("non-loopback IPv6 rejected", _host_of("[2001:4860:4860::8888]:443") not in LOOPBACK_HOSTS)

    # 11) advisory static pre-screen: flags on readable dirty JS, clean on benign JS.
    dirty_js = "const fs=require('fs'); fs.unlink('/x'); fetch('http://8.8.8.8/e');"
    clean_js = "const http=require('http'); http.request({host:'127.0.0.1',port:8899});"
    check("static prescreen flags dirty JS", set(static_prescreen(dirty_js)) >= {"fs_unlink_rm", "possible_non_loopback_url"})
    check("static prescreen clean on benign JS", static_prescreen(clean_js) == [])

    print()
    if failures:
        print(f"SELFTEST FAILED ({len(failures)} check(s)): {', '.join(failures)}")
        return 1
    print("SELFTEST PASSED (all checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
