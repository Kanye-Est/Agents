#!/usr/bin/env bash
# Pre-invocation environment snapshot for the post-discovery confirmatory protocol.
#
# Protocol: idea/50 Amendment 7 §A7C.4 as narrowed by §A7C.8 (data minimisation).
# Prospective only: applies to runs executed after A7 takes effect.  NOT part of the
# v3 rig that produced R1-1.
#
# RIG v5 CHANGE — data minimisation.  v4 wrote the WHOLE environment with
# key-name-based masking (113 variables in acceptance).  That is more than the
# evidence needs, and archiving arbitrary ambient values is a liability rather than
# an asset: it can carry unrelated projects' paths, tokens the mask pattern happens
# to miss, and machine identifiers that serve no protocol purpose.
#
# RIG v6 CHANGE — three tightenings on top of v5 (A7C.11):
#   (a) a secret is recorded as `<redacted-present>` and NOTHING else.  v5 wrote
#       `<masked len=N sha256_12=…>`; length plus a truncated digest is a
#       cross-run comparable fingerprint, and for a short or low-entropy value it
#       is guessable offline.  Presence is the only fact the protocol needs.
#   (b) no raw value of the variable under study is ever written — not in
#       `env_value_raw`, not inside a diagnostic message, and no verbatim config
#       line.  An unparseable value is recorded as `invalid_for_bool`, full stop.
#   (c) `umask 077` plus an explicit verification: all three files must be 0600,
#       and the caller refuses a formal run if they are not.
#
# The snapshot exists to answer exactly three questions:
#   1. what was GOOSE_DISABLE_SESSION_NAMING at invocation time?
#   2. was the frozen backend configuration actually in force?
#   3. was any proxy set that could defeat the hosts-level OSV block?
# None of the three requires storing unrelated values.  v5 therefore records
#   - ALLOWLISTED keys with values (secrets still masked), and
#   - every other key by NAME ONLY, plus a digest over that sorted name list.
# Name-only still lets a later reader see which variables existed and detect any
# change between runs; it just does not archive their contents.
#
# Files written:
#   env_snapshot_relevant.txt        allowlisted keys with values
#   env_snapshot_other_keys.txt      remaining key NAMES only + count + digest
#   env_snapshot_classification.txt  derived reading of the naming-relevant keys
# The first two are raw (unprocessed) evidence; the third is a source-level
# derivation and says so.
#
# Usage:  env_snapshot.sh capture <outdir> [label]

set -euo pipefail

MARKER="GOOSE-CANARY-ENV-SNAPSHOT"
RIG_VERSION="v9"
log() { printf '%s %s wall_ns=%s\n' "${MARKER}" "$*" "$(date +%s%N)" >&2; }

capture() {
  local outdir="$1" label="${2:-unlabelled}"
  [ -d "${outdir}" ] || { log "FAIL outdir_missing=${outdir}"; return 2; }

  # Set before the first write: a file created 0644 and chmod'ed afterwards is
  # world-readable for the interval in between, which for a pre-invocation snapshot
  # is exactly the interval that matters.
  umask 077

  OUT_RELEVANT="${outdir}/env_snapshot_relevant.txt" \
  OUT_OTHER="${outdir}/env_snapshot_other_keys.txt" \
  OUT_CLASS="${outdir}/env_snapshot_classification.txt" \
  SNAP_LABEL="${label}" \
  SNAP_RIG="${RIG_VERSION}" \
  GOOSE_CFG_YAML="${GOOSE_CFG_YAML:-${HOME}/.config/goose/config.yaml}" \
  python3 - <<'PY'
import hashlib, os, re, sys

relevant_path = os.environ["OUT_RELEVANT"]
other_path    = os.environ["OUT_OTHER"]
class_path    = os.environ["OUT_CLASS"]
label         = os.environ["SNAP_LABEL"]
rig           = os.environ["SNAP_RIG"]
cfg_yaml      = os.environ["GOOSE_CFG_YAML"]

# --- what is in scope, and why ------------------------------------------------
# Each entry is (matcher, reason).  Anything not matched here is recorded by name
# only.  Keeping the reason next to the matcher is deliberate: an allowlist without
# stated purpose grows until it is a whole-environment dump again.
ALLOW_EXACT = {
    "GOOSE_DISABLE_SESSION_NAMING": "the variable under study (A7C.1)",
    "GOOSE_PROVIDER":               "frozen backend precondition",
    "GOOSE_MODEL":                  "frozen backend precondition",
    "GOOSE_MODE":                   "approval-mode arm",
    "GOOSE_TEMPERATURE":            "frozen decoding precondition",
    "OPENAI_HOST":                  "frozen endpoint precondition",
    "OPENAI_BASE_PATH":             "frozen endpoint precondition",
    "HTTP_PROXY":  "would defeat the hosts-level OSV block",
    "HTTPS_PROXY": "would defeat the hosts-level OSV block",
    "ALL_PROXY":   "would defeat the hosts-level OSV block",
    "NO_PROXY":    "proxy-adjacent; recorded for completeness",
    "http_proxy":  "would defeat the hosts-level OSV block",
    "https_proxy": "would defeat the hosts-level OSV block",
    "all_proxy":   "would defeat the hosts-level OSV block",
    "no_proxy":    "proxy-adjacent; recorded for completeness",
    "TZ":   "timestamp interpretation across runs",
    "LANG": "affects tool output parsing",
}
ALLOW_PREFIX = (
    ("GOOSE_",       "any other product setting could change behaviour under test"),
    ("npm_config_",  "resolver configuration: registry and cache location"),
    ("OPENAI_",       "backend client configuration"),
)

SECRET_RE = re.compile(
    r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|_AUTH|AUTH_|COOKIE|SESSION_ID|SIGNATURE)",
    re.IGNORECASE,
)

# Presence, and nothing else.  No length, no digest, no HMAC, no truncated
# fingerprint: any of those is comparable across runs, and a short value is
# recoverable from a digest by brute force.  The protocol only ever needs to know
# whether a credential-shaped variable was set.
REDACTED = "<redacted-present>"

env = dict(os.environ)
for k in ("OUT_RELEVANT", "OUT_OTHER", "OUT_CLASS", "SNAP_LABEL", "SNAP_RIG", "GOOSE_CFG_YAML"):
    env.pop(k, None)          # snapshot plumbing is not part of the run environment

STUDY_KEY = "GOOSE_DISABLE_SESSION_NAMING"


def classify_bool_env(raw):
    """Mirror goose config/base.rs parse_env_value + serde_json::from_value::<bool>.

    Env values go through JSON parse first, then a lowercase true/false match, then
    integer/float, then string.  Only a real JSON/keyword boolean deserialises into
    `bool`; everything else errors, and agent.rs:400 turns that error into
    `unwrap_or(false)` — i.e. naming stays ENABLED.  `1` therefore does NOT disable
    naming via the environment at this commit, although the docs list it.

    The offending value is deliberately never returned or echoed: an "invalid" value
    can itself be sensitive, and the classification is complete without it.
    """
    if raw is None:
        return "unset", "enabled", "key absent from environment"
    low = raw.strip().lower()
    if low == "true":
        return "true", "disabled", "parses to JSON/keyword boolean true"
    if low == "false":
        return "false", "enabled", "parses to boolean false"
    return ("invalid_for_bool", "enabled",
            "value does not deserialise into bool -> getter Err -> unwrap_or(false)")


# Computed up front so the allowlist file can record the STATE instead of the value.
state, effective, why = classify_bool_env(env.get(STUDY_KEY))

def classify_key(k):
    if k in ALLOW_EXACT:
        return ALLOW_EXACT[k]
    for pre, why in ALLOW_PREFIX:
        if k.startswith(pre):
            return why
    return None

relevant, other = [], []
n_redacted = 0
# `reason`, not `why`: `why` holds the basis string returned by classify_bool_env and
# must not be overwritten by the allowlist loop (v8 did, and R1-2's classification
# file recorded a proxy-allowlist reason in the `basis=` field).
# Absence has to be stated, not implied.  "No HTTP_PROXY line in the file" is weak
# evidence that no proxy was set — it is indistinguishable from "we never looked".
# Every exactly-named allowlist key therefore gets a line, `<unset>` included.
for k in sorted(ALLOW_EXACT):
    if k not in env:
        relevant.append((k, "<unset>", ALLOW_EXACT[k] + " [absent — recorded explicitly]"))
for k in sorted(env):
    reason = classify_key(k)
    if reason is None:
        other.append(k)
        continue
    if k == STUDY_KEY:
        # four states only, never the value (A7C.11b)
        v = f"<state:{state}>"
    elif SECRET_RE.search(k):
        v = REDACTED; n_redacted += 1
    else:
        v = env[k].replace("\n", "\\n")
    relevant.append((k, v, reason))

with open(relevant_path, "w", encoding="utf-8") as fh:
    fh.write(f"# {label}\n")
    fh.write(f"# rig={rig} data-minimised snapshot: ALLOWLISTED keys only (A7C.8)\n")
    n_absent = sum(1 for _, v, _ in relevant if v == "<unset>")
    fh.write(f"# allowlisted_lines={len(relevant)} present={len(relevant)-n_absent} "
             f"explicitly_absent={n_absent} redacted_values={n_redacted} other_keys={len(other)}\n")
    fh.write("# a redacted value is recorded as <redacted-present> only: no length,\n")
    fh.write("# no digest, no fingerprint, nothing comparable across runs (A7C.11)\n")
    fh.write("# every other variable is recorded by NAME ONLY in env_snapshot_other_keys.txt\n")
    for k, v, reason in sorted(relevant):
        fh.write(f"{k}={v}\t# {reason}\n")

# Name-only inventory.  The digest makes "did the ambient key set change between
# runs?" answerable without archiving any of the values.
other_blob = "\n".join(other) + ("\n" if other else "")
with open(other_path, "w", encoding="utf-8") as fh:
    fh.write(f"# {label}\n")
    fh.write(f"# rig={rig} NAMES ONLY — no values recorded (A7C.8 data minimisation)\n")
    fh.write(f"# count={len(other)}\n")
    fh.write(f"# sha256_of_sorted_name_list={hashlib.sha256(other_blob.encode()).hexdigest()}\n")
    fh.write(other_blob)

# ---- naming-relevant classification -----------------------------------------
KEY = STUDY_KEY          # state/effective/why were computed above

# Presence of the key is recorded; the configured value is NOT.  A verbatim config
# line would reintroduce exactly the raw-value leak this rig version removes.
cfg_present = "no_config_file"
if os.path.exists(cfg_yaml):
    cfg_present = "absent_from_config_file"
    with open(cfg_yaml, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if ln.strip().startswith(KEY):
                cfg_present = "present_in_config_file"
                break

# Env wins over the config file (get_param checks env first).  Only when the env is
# unset can the config file decide, and this snapshot does not re-implement YAML
# coercion — so the result is marked indeterminate rather than guessed.
if state == "unset" and cfg_present == "present_in_config_file":
    effective = "indeterminate_config_file_value_not_interpreted"

with open(class_path, "w", encoding="utf-8") as fh:
    fh.write(f"# {label}\n")
    fh.write(f"# rig={rig}\n")
    fh.write("# DERIVED, source-level reading of goose commit 4dc0420f5704a92806c6628c8f0a3497d7a88759\n")
    fh.write("# not empirically tested against a running binary\n")
    fh.write(f"key={KEY}\n")
    fh.write(f"env_state={state}\n")
    fh.write("env_value_raw=not_recorded_by_policy\n")   # A7C.11(b)
    fh.write(f"config_file={cfg_yaml}\n")
    fh.write(f"config_file_key={cfg_present}\n")
    fh.write("config_file_value=not_recorded_by_policy\n")
    fh.write("precedence=env_over_config_file (config/base.rs:735)\n")
    fh.write(f"effective_session_naming={effective}\n")
    fh.write(f"basis={why}\n")
    fh.write("note=an effective_session_naming value of `enabled` means the product MAY\n")
    fh.write("note=issue a session-naming request; whether one actually occurred, and\n")
    fh.write("note=whether it overlapped the main request, is decided by manual coding\n")
    fh.write("note=against the run's llm_request logs and vLLM throughput log.\n")

print(f"env_snapshot rig={rig} env_state={state} effective_session_naming={effective} "
      f"allowlisted={len(relevant)} redacted={n_redacted} other_keys_by_name={len(other)}",
      file=sys.stderr)
PY
  # umask should already have produced 0600.  Verify rather than assume: an inherited
  # ACL, a mounted filesystem or a future edit could defeat it silently.
  local perm_fail=0 f mode
  for f in env_snapshot_relevant.txt env_snapshot_other_keys.txt env_snapshot_classification.txt; do
    chmod 600 "${outdir}/${f}" 2>/dev/null || true
    mode="$(stat -c '%a' "${outdir}/${f}" 2>/dev/null || echo missing)"
    if [ "${mode}" != "600" ]; then
      log "PERM_FAIL file=${f} mode=${mode} expected=600"; perm_fail=1
    else
      log "perm_ok file=${f} mode=${mode}"
    fi
  done
  [ "${perm_fail}" -eq 0 ] || { log "FAIL snapshot_permissions_not_0600"; return 3; }

  log "captured rig=${RIG_VERSION} label=${label} outdir=${outdir}"
}

cmd="${1:-}"; shift || true
case "${cmd}" in
  capture) capture "$@" ;;
  *) echo "usage: $0 capture <outdir> [label]" >&2; exit 2 ;;
esac
