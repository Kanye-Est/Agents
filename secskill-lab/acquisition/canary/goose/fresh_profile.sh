#!/usr/bin/env bash
# Fresh-profile reset and verification for the Goose activation-binding canary.
#
# Protocol freeze: idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md §10
#
# Why this is not optional: a stale `AlwaysAllow` decision left over from an earlier
# run silently converts an "approval was skipped" observation into an artifact of test
# order.  Every run must start from a state that is verifiably empty.
#
# This script ARCHIVES rather than deletes.  Nothing about a run should be
# unrecoverable, and the archived state is itself evidence about what a run created.
#
# Paths are taken from `goose info` (v1.45.0) plus the XDG state dir that `goose info`
# itself creates on first invocation — note that merely inspecting Goose produces state,
# which is exactly why the reset has to be verified rather than assumed.

set -euo pipefail

MARKER="GOOSE-CANARY-FRESH-PROFILE"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-/tmp/goose_canary/profile_archive}"
CANARY_DIR="${CANARY_DIR:-/tmp/goose_canary/effects}"

STAMP="$(date +%Y%m%dT%H%M%S%N)"
ARCHIVE="${ARCHIVE_ROOT}/${STAMP}"

GOOSE_PATHS=(
  "${HOME}/.config/goose"
  "${HOME}/.local/share/goose"
  "${HOME}/.local/state/goose"
  "${HOME}/.cache/goose"
)

log() { printf '%s %s\n' "${MARKER}" "$*" >&2; }

mkdir -p "${ARCHIVE}"

log "archive=${ARCHIVE}"

# Capture the version BEFORE touching anything.  Invoking goose at all — even
# `--version` — recreates the XDG state dir, so querying it after the reset would
# re-dirty the profile and make the verification below a lie.  This bit us once.
GOOSE_VERSION="$(goose --version 2>/dev/null | tr -d ' \n' || echo unknown)"
log "goose_version=${GOOSE_VERSION} (captured pre-reset)"

# --- 1. archive whatever exists ------------------------------------------------
for p in "${GOOSE_PATHS[@]}"; do
  if [ -e "${p}" ]; then
    dest="${ARCHIVE}/$(echo "${p#"${HOME}"/}" | tr '/' '_')"
    cp -a "${p}" "${dest}"
    rm -rf "${p}"
    log "archived_and_cleared path=${p} -> ${dest}"
  else
    log "already_absent path=${p}"
  fi
done

# --- 2. reset the canary effect directory --------------------------------------
if [ -d "${CANARY_DIR}" ] && [ -n "$(ls -A "${CANARY_DIR}" 2>/dev/null)" ]; then
  cp -a "${CANARY_DIR}" "${ARCHIVE}/canary_effects_previous"
  log "archived_previous_effects -> ${ARCHIVE}/canary_effects_previous"
fi
rm -rf "${CANARY_DIR}"
mkdir -p "${CANARY_DIR}"
log "canary_dir_reset path=${CANARY_DIR}"

# --- 3. verify the reset actually took ------------------------------------------
# A reset that silently failed is worse than no reset, because the run would look
# clean while carrying prior permission state.
FAILED=0
for p in "${GOOSE_PATHS[@]}"; do
  if [ -e "${p}" ]; then
    log "VERIFY_FAILED path_still_exists=${p}"
    FAILED=1
  fi
done
if [ -n "$(ls -A "${CANARY_DIR}" 2>/dev/null)" ]; then
  log "VERIFY_FAILED canary_dir_not_empty=${CANARY_DIR}"
  FAILED=1
fi

# --- 4. emit the manifest -------------------------------------------------------
MANIFEST="${ARCHIVE}/fresh_profile_manifest.json"
{
  printf '{\n'
  printf '  "protocol": "goose_activation_binding_canary_v1",\n'
  printf '  "reset_wall_ns": "%s",\n' "$(date +%s%N)"
  printf '  "reset_iso": "%s",\n' "$(date -Is)"
  printf '  "goose_version": "%s",\n' "${GOOSE_VERSION}"
  printf '  "archive": "%s",\n' "${ARCHIVE}"
  printf '  "canary_dir": "%s",\n' "${CANARY_DIR}"
  printf '  "verified_clean": %s\n' "$([ "${FAILED}" -eq 0 ] && echo true || echo false)"
  printf '}\n'
} > "${MANIFEST}"

log "manifest=${MANIFEST}"

if [ "${FAILED}" -ne 0 ]; then
  log "RESULT=dirty — DO NOT RUN. Resolve the paths above first."
  exit 1
fi

log "RESULT=clean"
