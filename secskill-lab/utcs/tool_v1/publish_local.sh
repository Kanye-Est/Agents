#!/usr/bin/env bash
# UTCS tool v1 — publish utcs-mdclean to the LOCAL Verdaccio (127.0.0.1:4873) ONLY.
#
# Spec: idea/52 §A1.1 (A/v1 must be installable so Goose can `npx -y utcs-mdclean@<ver>`
# it from the local registry) + goose/config.template.yaml (npm_config_registry =
# http://127.0.0.1:4873) + goose/README forward item.
#
# SAFETY (idea/52 §3 envelope — NON-NEGOTIABLE):
#   * Publishes to the LOOPBACK Verdaccio only. Hardcoded 127.0.0.1:4873; the script
#     REFUSES any non-loopback registry. NEVER public npm on the experiment path.
#   * The committed package.json stays "private": true (npm blocks publishing it). This
#     script publishes from an EPHEMERAL staging copy with `private` removed and
#     publishConfig.registry pinned to the loopback registry — so the only path to a
#     registry is this script, and it can only reach loopback. The repo package itself
#     remains unpublishable by default.
#   * No global npm config is mutated (no `npm config set`). Registry is passed per-invocation
#     via --registry and a staging-local .npmrc.
#   * Fixed version: publishes the exact `version` in package.json (no floating tag).
#
# Usage:  ./publish_local.sh            # publish pinned version to local Verdaccio
#         NPM_TOKEN=... ./publish_local.sh   # non-interactive auth (else: npm adduser once)
set -euo pipefail

REGISTRY="${REGISTRY:-http://127.0.0.1:4873}"
PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- loopback guard: refuse to publish anywhere that is not 127.0.0.1 / localhost ----
host="$(printf '%s' "$REGISTRY" | sed -E 's#^https?://([^:/]+).*#\1#')"
case "$host" in
  127.0.0.1|localhost|::1) : ;;
  *) echo "ERROR: registry '$REGISTRY' is not loopback (host='$host'). Refusing." >&2
     echo "       This tool publishes to the LOCAL Verdaccio only (idea/52 §3)." >&2
     exit 2 ;;
esac

NAME="$(node -p "require('$PKG_DIR/package.json').name")"
VERSION="$(node -p "require('$PKG_DIR/package.json').version")"
echo "package: $NAME@$VERSION  ->  $REGISTRY"

# ---- check Verdaccio is up (do NOT auto-start a service; prompt instead) ----
if ! curl -sS -m 3 -o /dev/null "$REGISTRY/-/ping"; then
  cat >&2 <<EOF
ERROR: local Verdaccio is not reachable at $REGISTRY

Start it locally, bound to loopback, then re-run this script, e.g.:

    # if verdaccio is installed:
    verdaccio --listen 127.0.0.1:4873
    # (ensure its config 'listen' is 127.0.0.1 only — never 0.0.0.0)

First-time publish auth (once per machine), if the registry requires a user:
    npm adduser --registry $REGISTRY
    #   ...or run this script with NPM_TOKEN=<token> for non-interactive auth.
EOF
  exit 1
fi

# ---- stage an ephemeral, publishable copy (keeps the committed package.json private) ----
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
# copy only what package.json 'files' ships, plus package.json itself.
cp "$PKG_DIR/package.json" "$STAGE/package.json"
cp -R "$PKG_DIR/src" "$STAGE/src"
cp -R "$PKG_DIR/test" "$STAGE/test"

# rewrite the STAGING package.json: drop `private`, pin publishConfig.registry to loopback.
node -e '
  const fs = require("fs");
  const p = process.argv[1], reg = process.argv[2];
  const j = JSON.parse(fs.readFileSync(p, "utf8"));
  delete j.private;
  j.publishConfig = Object.assign({}, j.publishConfig, { registry: reg });
  fs.writeFileSync(p, JSON.stringify(j, null, 2) + "\n");
' "$STAGE/package.json" "$REGISTRY"

# optional non-interactive auth token, scoped to the loopback registry only.
if [[ -n "${NPM_TOKEN:-}" ]]; then
  printf '//127.0.0.1:4873/:_authToken=%s\n' "$NPM_TOKEN" > "$STAGE/.npmrc"
fi

# ---- publish (fixed version) ----
echo "publishing $NAME@$VERSION to $REGISTRY ..."
if ! ( cd "$STAGE" && npm publish --registry "$REGISTRY" ); then
  cat >&2 <<EOF

publish failed. Common causes on a local Verdaccio:
  * version already exists ($NAME@$VERSION): bump the version, or (LOCAL dev registry only)
        npm unpublish "$NAME@$VERSION" --registry $REGISTRY --force
  * not authenticated: npm adduser --registry $REGISTRY   (or set NPM_TOKEN=...)
EOF
  exit 1
fi

echo "OK: published $NAME@$VERSION to $REGISTRY"
echo "verify: npm view $NAME versions --registry $REGISTRY"
echo "Goose then pulls it via: npx -y $NAME@$VERSION   (config.template.yaml @<SELECTOR>)"
