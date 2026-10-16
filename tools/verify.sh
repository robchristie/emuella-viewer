#!/usr/bin/env bash
# The viewer's complete verification: bash tools/verify.sh [STAGE...]
# Stages are checks, native and browser; with none, all three run in order.
# CI runs each stage as its own job. The browser stage needs the `stobie` CLI
# from the pinned Stobie revision (or STOBIE naming it), the wasm-bindgen CLI
# at the locked version, Node and Playwright's Chromium.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export STOBIE="${STOBIE:-stobie}"
stages=("$@")
(( ${#stages[@]} )) || stages=(checks native browser)
run() { echo "+ $*"; "$@"; }
# A local Stobie patch (.cargo/config.toml) changes the lockfile's sources, so
# --locked holds only without one.
LOCKED=(--locked)
if [[ -f .cargo/config.toml ]] && grep -q '^\[patch' .cargo/config.toml; then
  echo "note: .cargo/config.toml patches Stobie; building without --locked" >&2
  LOCKED=()
fi

for stage in "${stages[@]}"; do
  case "$stage" in
    checks)
      run cargo fmt --all --check
      run cargo clippy "${LOCKED[@]}" --workspace --all-targets --all-features -- -D warnings
      run cargo clippy "${LOCKED[@]}" --target wasm32-unknown-unknown -p emuella-viewer -- -D warnings
      run cargo test "${LOCKED[@]}" --workspace
      run python3 -m unittest discover -s tools/tests
      run npm ci
      run node --test tools/tests/*.test.mjs apps/emuella-viewer/web/tests/worker.test.mjs
      ;;
    native)
      run cargo build "${LOCKED[@]}" --workspace --release
      ;;
    browser)
      run python3 tools/check-stobie-cli.py
      run bash tools/bootstrap-linux-ui.sh
      run npm ci
      run npx playwright install chromium
      run env VIEWER_LOCKED="${LOCKED[*]}" bash tools/build-web.sh
      run "$STOBIE" build-web --manifest-path apps/emuella-viewer/Cargo.toml "${LOCKED[@]}" \
        --production --output target/web-production
      # Validation targets the packaged artefact, never the development build.
      packaged="$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(next(a["assetDirectory"] for a in m["apps"] if a["name"] == "emuella-viewer"))' target/web-production/manifest.json)"
      run node tools/viewer-response-headers.mjs "target/web-production/$packaged"
      run node tools/viewer-startup-smoke.mjs target/web-production
      ;;
    *)
      echo "unknown stage $stage; expected checks, native or browser" >&2
      exit 2
      ;;
  esac
  echo "Verification stage $stage passed"
done
