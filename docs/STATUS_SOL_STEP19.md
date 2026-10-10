# SOL STEP19 — Fail-closed PNG-to-MOV alpha readback (2026-10-10)

## Scope and implementation

Branch based on STEP18 PR #21 exact head `a04c00788e6bfbb6991ff7dd34b327511df16dc8`. Do not merge into `main` or release. Continue offline implementation, defer owner Premiere Pro 2024 trial to the very end.

- Added `core/fx_alpha_verify.py`: independently decodes original private PNG snapshot and MOV output with native FFmpeg, using bounded **8×8 nearest-neighbor RGBA samples**, frame selection for first/IN/HOLD/OUT/last, and source-relative alpha comparisons. Supports FADE, plus direction-aware WIPE boundaries. Does not create PNG or screenshot assets. Fails closed for invalid timing/preset, missing/transparent-unobservable alpha, mismatching pixels, broken decoder or truncated output. Tolerance only allows small codec rounding; sampling does **not** establish whole-frame, Canva fidelity, or Premiere compatibility.
- Updated `core/fx_cache_worker.py`: **real alpha readback required before cache publication**. Metadata-only is not enough. The SHA-addressed cache identity version is bumped to `fx-alpha-cache-v2-alpha-sampled` to segregate earlier unverified MOVs. SHA-256 of MOV computed **before** atomic no-overwrite hard-link publication. Report can now say `alpha_pixels_verified=true` **only after** the verifier actually succeeds, while `whole_frame_verified=false`, `canva_fidelity_verified=false`, `host_verified=false`, `can_assemble=false` remain enforced.
- Extended mocked cache tests to assert verifier is invoked, mismatch aborts cleanly, and a rejected verifier result cannot authorize the cache. Fake mocked bytes are **not** counted as independent alpha proof.
- Added separate alpha policy/mismatch/opaque/decode-failure unit tests.
- Added `tests/test_core_fx_cache_real_png.py`: reads an **already existing owner-approved UI PNG from the repository as a codec transport smoke input only**; checks source SHA/mtime unchanged; renders a candidate MOV only in a private temporary cache directory, then decodes actual pixels. This is **not** user artwork generation, UI editing, final animation asset use, nor an endorsement that animating a UI screenshot is an end-user feature. This test will explicitly skip when no approved repository PNG has an alpha channel; such a skip must be declared and must **not** be misrepresented as real-PNG verification.
- Workflow `.github/workflows/step19-cache-pixels.yml` verifies native binaries, focused unit tests, real existing approved PNG path when compatible, complete Python regressions and JS CEP regressions on Windows and Ubuntu.

## Safety

Sources are hashed and copied to a unique private directory; user files are read-only. Real cache output is only a MOV, not a new image. No uploaded image generated or modified by the assistant. All 19 remaining presets still blocked (2/21 candidate backends). No Canva visual match or whole-frame claims. G3 Premiere host **BLOCKED_HOST / UNVERIFIED**, 0/21 certified on real Premiere. No merge, tag, release or owner manual testing.

## Gate checklist

- Repository code, unit tests, native FFmpeg integration and CI: require actual GitHub run results.
- If existing PNG type lacks alpha, CI may show a skip; this is a **source-compatibility blocker for real approved PNG evidence**, not a PASS.
- Runtime test only covers sampling. Full-frame quality, crash recovery, persistent cache, all effects, host binding and final MP4 remain undone.

## Next STEP20

Secure cache recovery and collision proof (broken/partial/stale entries, cache integrity on restart), then expand 19 distinct animation backend families without silent approximation or image-generation by the assistant.
