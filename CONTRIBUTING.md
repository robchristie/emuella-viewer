# Contributing to the Emuella viewer

These rules apply to every change.

## Prerequisites

- Rust **1.99.0** with the `wasm32-unknown-unknown` target, clippy and rustfmt
  ([`rust-toolchain.toml`](rust-toolchain.toml) selects them).
- The `stobie` CLI built from the pinned Stobie revision, and the
  `wasm-bindgen` CLI **0.2.127**, the version the lockfile resolves:

  ```sh
  REV=$(python3 -c 'import tomllib; print(tomllib.load(open("Cargo.toml","rb"))["workspace"]["dependencies"]["stobie-core"]["rev"])')
  cargo install --locked --git https://github.com/robchristie/stobie --rev "$REV" stobie-cli
  cargo install --locked wasm-bindgen-cli --version 0.2.127
  ```

- Node.js **25.8.2** and npm; Playwright is pinned in `package-lock.json`.
- Python 3 with GDAL's and NumPy's Python bindings for the tool tests.
- For browser checks on Linux, Chromium's libraries. `tools/bootstrap-linux-ui.sh`
  unpacks pinned x86_64 packages into ignored `.tools/` (it needs `curl` and
  `bsdtar`); set `STOBIE_USE_SYSTEM_UI_LIBS=1` to use the host's instead, as CI
  does.
- Preparation of real inputs needs a maintained GDAL shared library and the
  JP2Emuella plugin; see the [service guide](docs/emuella-viewer-service.md).

## Verification

Full verification is:

```sh
bash tools/verify.sh
```

It runs three stages, which CI runs as separate jobs; `bash tools/verify.sh
STAGE` runs one:

- `checks`: formatting, native and WASM Clippy, the Rust tests, the Python and
  Node tool tests and the worker tests.
- `native`: the release build of the whole workspace.
- `browser`: checks that `stobie` matches the pinned revision, builds the
  viewer with `stobie build-web` and checks the worker's response adapter
  against the built WASM; then packages it with `stobie build-web --production`,
  checks the packaged adapter, and runs the startup smoke, which proves the
  WebGPU requirement and worker-failure cleanup in Chromium.

Focused checks: `cargo test -p emuella-viewer --lib`, `cargo clippy --target
wasm32-unknown-unknown -p emuella-viewer` and `bash tools/build-web.sh`.

The fixture journeys (`node tools/viewer-browser-smoke.mjs` against a running
`emuella-viewer-tools serve`) and the qualification campaigns in
[`docs/`](docs) are run by hand; they are not part of `tools/verify.sh`.
Deterministic public fixture journeys do not establish protected real-image
qualification, codec quality, every browser and GPU, or large-image
performance.

## Stobie

Every Stobie crate in [`Cargo.toml`](Cargo.toml)'s `[workspace.dependencies]`
names one exact revision; `tools/check-stobie-cli.py` enforces that and checks
the CLI against it.

- **Upgrade:** change the revision in all five lines, run `cargo update -p
  stobie-core` (Cargo updates the others with it), reinstall the `stobie` CLI
  from the same revision, and run full verification.
- **Unmerged Stobie changes:** create `.cargo/config.toml` (it is ignored)
  patching each Stobie crate to a local checkout:

  ```toml
  [patch."https://github.com/robchristie/stobie"]
  stobie-core = { path = "/path/to/stobie/crates/stobie-core" }
  stobie-imaging = { path = "/path/to/stobie/crates/stobie-imaging" }
  stobie-runtime = { path = "/path/to/stobie/crates/stobie-runtime" }
  stobie-render-wgpu = { path = "/path/to/stobie/crates/stobie-render-wgpu" }
  stobie-ui-egui = { path = "/path/to/stobie/crates/stobie-ui-egui" }
  ```

  Cargo still fetches the pinned revision to resolve the patch. Use that
  checkout's `stobie` (`STOBIE=/path/to/stobie/target/release/stobie`).

Framework contracts the viewer relies on are owned by Stobie: the
[regional adapter contract](https://github.com/robchristie/stobie/blob/main/docs/regional-adapter-contract.md),
the [browser startup guide](https://github.com/robchristie/stobie/blob/main/docs/browser-startup.md)
and the image layer's crate boundaries. Change them there first.

## Evidence

Never commit raw captures such as screenshots, logs or runtime observation
dumps, local imagery or prepared scenes. Write them under ignored `.tools/` or
registered campaign scratch. Durable raw evidence goes to a new commit in the
append-only [stobie-evidence](https://github.com/robchristie/stobie-evidence)
archive (never rewrite its history), and reports link to it by permalink.
Only small qualification protocols, build receipts and result summaries stay
tracked, such as `docs/viewer-acceptance-*.json`.

## Reports written before the move

Reports and receipts in `docs/` written in the Stobie repository keep their
original commands, paths and commit IDs, which refer to Stobie's history. The
commands map to this repository as follows:

| In Stobie | Here |
| --- | --- |
| `STOBIE_VIEWER_WEB_DIR=DIR cargo xtask build-viewer-web` | `bash tools/build-web.sh DIR` |
| `cargo xtask viewer-smoke` | `node tools/viewer-browser-smoke.mjs` |
| `cargo xtask verify` | `bash tools/verify.sh` |
| `cargo xtask build-browser-production` | `stobie build-web --manifest-path apps/emuella-viewer/Cargo.toml --production` |
