#!/usr/bin/env bash
# OSV egress control for the post-discovery confirmatory protocol.
#
# Protocol: idea/50 Amendment 1 §A1.1
#
# Goose 1.45.0 contains a native lookup path (`deny_if_malicious_cmd_args` ->
# https://api.osv.dev/v1/query) that would send our package name to a real
# third-party service.  The protocol freezes this as blocked for every run.
#
# Method: bubblewrap binds a modified /etc/hosts over the real one for the
# sandboxed process only.  Chosen over `unshare -m` because bwrap preserves the
# real uid (unshare needs --map-root-user to gain mount capability, which would
# run Goose as root-in-namespace and perturb the very environment under test).
#
# Properties this satisfies (idea/50 A1.1):
#   - no permanent system change: the real /etc/hosts is never written
#   - loopback untouched: same network namespace, so 127.0.0.1 registry,
#     observer and the L40 SSH tunnel all keep working
#   - verifiable before each run, with the verification output kept as evidence
#   - nothing to clean up on abort: the override dies with the process
#
# Usage:
#   osv_block.sh hostsfile <path>        write the override hosts file
#   osv_block.sh verify <path>           prove blocked + loopback intact (evidence)
#   osv_block.sh exec <path> -- <cmd>    run a command with the override applied

set -euo pipefail

OSV_HOST="api.osv.dev"
MARKER="GOOSE-CANARY-OSV-BLOCK"

log() { printf '%s %s wall_ns=%s\n' "${MARKER}" "$*" "$(date +%s%N)" >&2; }

make_hosts() {
  local out="$1"
  cp /etc/hosts "${out}"
  {
    printf '\n# %s — protocol idea/50 A1.1; sandbox-local override, real /etc/hosts untouched\n' "${MARKER}"
    # Both families are required.  An IPv4-only entry leaves the AAAA record
    # resolvable via DNS, and a client preferring IPv6 would still reach the
    # real service.
    printf '127.0.0.1 %s\n' "${OSV_HOST}"
    printf '::1 %s\n' "${OSV_HOST}"
  } >> "${out}"
  log "hosts_override_written path=${out}"
}

# Run a command with the override bound over /etc/hosts, uid preserved.
in_sandbox() {
  local hosts="$1"; shift
  bwrap --dev-bind / / --bind "${hosts}" /etc/hosts -- "$@"
}

verify() {
  local hosts="$1"
  local rc_v4 rc_v6 rc_any resolved fail=0

  # 1. resolution must point only at loopback, in both families
  resolved="$(in_sandbox "${hosts}" getent ahosts "${OSV_HOST}" 2>/dev/null | awk '{print $1}' | sort -u | tr '\n' ' ')"
  log "resolved=${resolved:-<none>}"
  for addr in ${resolved}; do
    case "${addr}" in
      127.0.0.1|::1) ;;
      *) log "VERIFY_FAIL non_loopback_resolution=${addr}"; fail=1 ;;
    esac
  done
  [ -z "${resolved}" ] && { log "VERIFY_FAIL no_resolution_at_all"; fail=1; }

  # 2. connection must fail, forced over each family
  set +e
  in_sandbox "${hosts}" curl -4 -fsS --max-time 6 -o /dev/null \
    "https://${OSV_HOST}/v1/query" -X POST -d '{}' 2>/dev/null; rc_v4=$?
  in_sandbox "${hosts}" curl -6 -fsS --max-time 6 -o /dev/null \
    "https://${OSV_HOST}/v1/query" -X POST -d '{}' 2>/dev/null; rc_v6=$?
  in_sandbox "${hosts}" curl -fsS --max-time 6 -o /dev/null \
    "https://${OSV_HOST}/v1/query" -X POST -d '{}' 2>/dev/null; rc_any=$?
  set -e
  log "curl_rc ipv4=${rc_v4} ipv6=${rc_v6} default=${rc_any}  (0 would mean REACHABLE)"
  for rc in "${rc_v4}" "${rc_v6}" "${rc_any}"; do
    [ "${rc}" -eq 0 ] && { log "VERIFY_FAIL osv_reachable"; fail=1; }
  done

  # 3. the real hosts file must be untouched
  if grep -q "${OSV_HOST}" /etc/hosts 2>/dev/null; then
    log "VERIFY_FAIL real_etc_hosts_modified"; fail=1
  else
    log "real_etc_hosts_clean"
  fi

  # 4. loopback name resolution must still work inside the sandbox
  if in_sandbox "${hosts}" getent hosts localhost >/dev/null 2>&1; then
    log "loopback_resolution_ok"
  else
    log "VERIFY_FAIL loopback_resolution_broken"; fail=1
  fi

  # 5. loopback SERVICES must still be reachable.  Reported per service; a
  #    service that is simply not running yet is not a failure of the block.
  in_sandbox "${hosts}" python3 - <<'PY'
import socket
for name, port in (("test_registry", 4873), ("model_tunnel", 8000)):
    s = socket.socket(); s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port)); print(f"loopback_service {name}:{port} connect_ok")
    except ConnectionRefusedError:
        print(f"loopback_service {name}:{port} refused_not_running")
    except Exception as e:
        print(f"loopback_service {name}:{port} {type(e).__name__}")
    finally:
        s.close()
PY

  if [ "${fail}" -ne 0 ]; then
    log "RESULT=FAIL"; return 1
  fi
  log "RESULT=PASS"
}

cmd="${1:-}"; shift || true
case "${cmd}" in
  hostsfile) make_hosts "$1" ;;
  verify)    verify "$1" ;;
  exec)
    hosts="$1"; shift
    [ "${1:-}" = "--" ] && shift
    in_sandbox "${hosts}" "$@"
    ;;
  *) echo "usage: $0 {hostsfile|verify|exec} <hosts-path> [-- cmd...]" >&2; exit 2 ;;
esac
