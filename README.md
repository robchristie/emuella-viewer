# Emuella image viewer

A native and browser viewer for large indexed JPEG 2000 (HTJ2K) images and
NITF scenes, delivered by region through JPIP. It reconstructs only the
regions and detection thumbnails it shows, from one shared compressed cache,
across several image panes and a virtualised gallery of 10,000 logical
detections. It is built on [Stobie](https://github.com/robchristie/stobie)
and the [Emuella JPEG 2000 codec](https://github.com/emuella/emuella-j2k).

The viewer was developed inside the Stobie repository and moved here, with its
tools, qualification thresholds, catalogues, workloads and reports, from Stobie
commit `8bfcdd6d55776365cfcb2e672b76c9548abba792`. Stobie history was not imported; the reports' commit
IDs refer to Stobie's history, and their raw evidence stays in
[stobie-evidence](https://github.com/robchristie/stobie-evidence).

## Layout

| Path | What it is |
| --- | --- |
| [`apps/emuella-viewer`](apps/emuella-viewer/README.md) | The viewer: native and browser entry points, its Web Worker and qualification thresholds |
| [`crates/emuella-viewer-source`](crates/emuella-viewer-source) | The regional source adapter between the codec, the JPP profile and a worker |
| [`apps/emuella-viewer-tools`](apps/emuella-viewer-tools) | Preparation, deterministic public fixtures, the local HTTP/JPIP service and measurement clients |
| [`tools/`](tools) | Build, verification and qualification tooling |
| [`docs/`](docs) | The service guide, calibration and qualification reports |

## Build and run

The [contributor guide](CONTRIBUTING.md) lists the prerequisites. Prepare
public deterministic representations and start the local service as the
[service guide](docs/emuella-viewer-service.md) describes, then:

```sh
cargo run --release -p emuella-viewer -- --server http://127.0.0.1:8088
bash tools/build-web.sh "$CAMPAIGN_SCRATCH/viewer-web"
```

The browser build needs WebGPU.

## Stobie

Stobie is a git dependency pinned to one revision in [`Cargo.toml`](Cargo.toml),
and the `stobie` CLI builds the browser package. The viewer uses Stobie's image
layer directly (`stobie-imaging`, `stobie-runtime`, `stobie-render-wgpu`
with its regional renderer, and `stobie-ui-egui`) rather than Stobie's
application host.

## Later work

1. **Move the viewer onto Stobie's `AppHost`.** That would give it the
   framework's hidden ARIA layer, operation through the `stobie` CLI and the
   WebGL2 fallback; today it owns its frame loop and requires WebGPU in the
   browser.

## Licence

[Apache License 2.0](LICENSE), as Stobie. The Emuella codec dependencies are
Apache-2.0 (`emuella-j2k-codestream` is Apache-2.0 AND BSD-2-Clause).
