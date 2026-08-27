#!/usr/bin/env bash
# Content-bound arm adapter (idea/48 §7).
#
# Goose's extension schema has NO native digest field:  native content binding = absent.
# This wrapper supplies the binding from outside, as a `custom-adapter binding` in the
# three-level scheme of idea/47 (native / resolver-enforced / custom-adapter).
#
# It must be reported honestly in results:  Goose neither understands nor verifies this
# digest.  The wrapper is what makes the arm constructible at all, and that gap is
# precisely the first-class binding capability the acquisition permit is meant to add.
#
# Usage, as it would appear in a Goose stdio extension command:
#   digest_wrapper.sh <expected_sha256> <npm-spec> [server args...]
#
# Behaviour:
#   fetch tarball -> sha256 -> compare -> REFUSE on mismatch -> extract -> exec on match
#
# Every decision is written to stderr with a nanosecond timestamp so it can be aligned
# to the terminal trace that is the run's primary time axis (idea/48 §3.1).

set -euo pipefail

MARKER="GOOSE-CANARY-DIGEST-WRAPPER"

log() {
  printf '%s phase=%s wall_ns=%s iso=%s %s\n' \
    "${MARKER}" "$1" "$(date +%s%N)" "$(date -Is)" "${2:-}" >&2
}

if [ "$#" -lt 2 ]; then
  log usage_error "expected: <expected_sha256> <npm-spec> [args...]"
  exit 2
fi

EXPECTED="$1"; shift
SPEC="$1"; shift

WORK="$(mktemp -d -t goose-canary-digest-XXXXXX)"
cleanup() { rm -rf "${WORK}"; }
trap cleanup EXIT

log fetch_start "spec=${SPEC}"

# npm pack resolves the spec against the configured registry and writes a tarball.
# Resolution happens HERE, at activation time — which is exactly the window the
# mutable-selector arm exercises.
if ! TARBALL_NAME="$(cd "${WORK}" && npm pack "${SPEC}" --silent 2>/dev/null | tail -1)"; then
  log fetch_failed "spec=${SPEC}"
  exit 3
fi

TARBALL="${WORK}/${TARBALL_NAME}"
if [ ! -f "${TARBALL}" ]; then
  log fetch_failed "tarball_missing=${TARBALL_NAME}"
  exit 3
fi

ACTUAL="$(sha256sum "${TARBALL}" | awk '{print $1}')"
log digest_resolved "actual=${ACTUAL} expected=${EXPECTED}"

if [ "${ACTUAL}" != "${EXPECTED}" ]; then
  # This is the whole point of the arm: an immutable content binding must REFUSE the
  # substituted artifact, where the mutable and version-pinned arms accept it.
  log digest_mismatch_refused "actual=${ACTUAL} expected=${EXPECTED}"
  exit 4
fi

log digest_match "digest=${ACTUAL}"

tar xzf "${TARBALL}" -C "${WORK}"
ENTRY="${WORK}/package/canary_server.js"
if [ ! -f "${ENTRY}" ]; then
  log entry_missing "entry=${ENTRY}"
  exit 5
fi

log exec_start "entry=${ENTRY}"
# Keep the wrapper in the process tree so the observer can attribute the spawn.
exec node "${ENTRY}" "$@"
