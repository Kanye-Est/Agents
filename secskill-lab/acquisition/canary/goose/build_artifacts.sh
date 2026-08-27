#!/usr/bin/env bash
# Build the two canary artifacts as npm tarballs for the local test registry.
#
# Protocol freeze: idea/48_GOOSE_CANARY_PROTOCOL_FREEZE.md
#
# One package NAME, two VERSIONS.  This is the whole point of the mutable-selector
# arm: `pkg@latest` must be able to resolve to A at admission time and to B at
# activation time without the selector text changing.
#
#   1.0.0 -> artifact A   (dist-tag `latest` initially)
#   1.0.1 -> artifact B   (dist-tag `latest` after the repoint)
#
# Both artifacts are benign: they write one fixed file into an isolated directory
# and echo text.  They never touch real credentials and never egress anywhere.
# They are published ONLY to a local test registry (idea/43 §7.5).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-${HERE}/dist}"
CANARY_DIR="${CANARY_DIR:-/tmp/goose_canary/effects}"
PKG_NAME="${PKG_NAME:-goose-activation-canary}"
# Hard publish guard.  npmjs.org is reachable from this host, so a mistyped
# `npm publish` would otherwise reach the real registry — a direct violation of
# idea/43 §7.5.  publishConfig pins the destination to the local test registry;
# npm refuses to publish anywhere else without an explicit --registry override.
LOCAL_REGISTRY="${LOCAL_REGISTRY:-http://127.0.0.1:4873}"

mkdir -p "${OUT}"

build_one() {
  local id="$1" version="$2"
  local stage="${OUT}/pkg_${id}"

  rm -rf "${stage}"
  mkdir -p "${stage}"

  cp "${HERE}/canary_server.js" "${stage}/canary_server.js"
  chmod +x "${stage}/canary_server.js"

  cat > "${stage}/canary_identity.json" <<EOF
{
  "canary_id": "${id}",
  "canary_dir": "${CANARY_DIR}",
  "built_for": "goose_activation_binding_canary_v1"
}
EOF

  cat > "${stage}/package.json" <<EOF
{
  "name": "${PKG_NAME}",
  "version": "${version}",
  "description": "Benign research canary: stdio MCP server that reports its own artifact identity. Local test registry only.",
  "private": false,
  "publishConfig": { "registry": "${LOCAL_REGISTRY}", "access": "restricted" },
  "bin": { "${PKG_NAME}": "canary_server.js" },
  "files": ["canary_server.js", "canary_identity.json"],
  "license": "UNLICENSED"
}
EOF

  ( cd "${stage}" && npm pack --pack-destination "${OUT}" >/dev/null )

  local tarball="${OUT}/${PKG_NAME}-${version}.tgz"
  local digest
  digest="$(sha256sum "${tarball}" | awk '{print $1}')"
  printf '%s  %s  artifact_%s\n' "${digest}" "$(basename "${tarball}")" "${id}"
  printf '%s\n' "${digest}" > "${tarball}.sha256"
}

echo "package name : ${PKG_NAME}"
echo "canary dir   : ${CANARY_DIR}"
echo "output       : ${OUT}"
echo
echo "sha256                                                            tarball                              artifact"
build_one A 1.0.0
build_one B 1.0.1

cat <<'EOF'

Next (rig build, see idea/48 §13):
  1. start the local test registry and publish both versions
  2. point dist-tag `latest` at 1.0.0 (artifact A)
  3. record the researcher-observed digest at admission time
  4. between admission and activation, repoint `latest` to 1.0.1 (artifact B)

The .sha256 files are the frozen digests for the content-bound arm (idea/48 §7).
EOF
