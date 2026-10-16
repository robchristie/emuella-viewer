#!/usr/bin/env bash
# Build the viewer for the browser with `stobie build-web`: a locked release
# WASM build, wasm-bindgen into apps/emuella-viewer/web/pkg and Stobie's
# startup loader. With OUTPUT (or STOBIE_VIEWER_WEB_DIR), copy the complete
# static root there, for example into campaign scratch. Then check the
# worker's response adapter against the built WASM. STOBIE names the CLI;
# VIEWER_LOCKED= (empty) drops --locked when a local Stobie patch is active.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STOBIE="${STOBIE:-stobie}"
WEB="apps/emuella-viewer/web"
OUTPUT="${1:-${STOBIE_VIEWER_WEB_DIR:-}}"
"$STOBIE" build-web --manifest-path apps/emuella-viewer/Cargo.toml ${VIEWER_LOCKED---locked}
if [[ -n "$OUTPUT" ]]; then
  mkdir -p "$OUTPUT"
  for asset in index.html bootstrap.js worker.js response.js browser-startup.js; do
    cp "$WEB/$asset" "$OUTPUT/$asset"
  done
  rm -rf "$OUTPUT/pkg"
  cp -r "$WEB/pkg" "$OUTPUT/pkg"
  WEB="$OUTPUT"
fi
node tools/viewer-response-headers.mjs "$WEB"
echo "Serve the viewer's complete static root: $WEB"
