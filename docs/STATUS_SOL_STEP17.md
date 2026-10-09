# SOL STEP17 — Isolated FFmpeg Alpha Cache Worker (2026-10-10)

**Owner instruction remains active:** complete all feasible coding/integrations and automated regressions before the owner tests Premiere Pro 2024 on Windows 11. G3 remains **BLOCKED_HOST**, no 21 presets host certified, no manual host test requested at this stage. No image/asset generation or editing of owner's approved PNG UI, no main merge or release.

## Why this is the correct continuation

The repository had already advanced through a coherent STEP07–STEP16 PR chain since the prior STEP06 user-facing report. STEP16 PR #19 implemented candidate FADE/WIPE filtergraphs but no cache render worker. This branch `sol/step17-alpha-cache-worker-20261010` is based directly on STEP16, **not** on the older parallel STEP07 branch.

## Code completed

- `core/fx_cache_worker.py`: candidate local FFmpeg RGBA rendering worker, only the distinct FADE and WIPE presets implemented by STEP16. Reuses the exact B02 MEDIUM BOTH phase schedule; no substitute for any of the other 19 presets.
- Requires an existing PNG inside a chosen media root and a pinned lowercase SHA-256. Copies bytes into a unique private cache work directory while computing the hash, rejecting changed source, file outside approved root, unexpected PNG header/bit-depth/alpha, and explicit resource limits.
- Runs fixed `ffmpeg` argv with `shell=False`, `-n` and timeout on the **private source copy**, not on the owner's PNG directly. Checks rendered MOV through `ffprobe` for codec `qtrle`, pixel format `argb`, 30/1 FPS, exact width/height and total frame count.
- Publishes a new SHA-addressed MOV into cache with an atomic hard link (no overwrite even if the destination appears concurrently); cleans only the private work directory on success or failure. No existing source/media/cache deletion.
- Report remains **RENDERED_METADATA_CHECKED_NOT_HOST_OR_ALPHA_CERTIFIED**, `can_assemble=false`, `host_verified=false`, `alpha_pixels_verified=false`, `canva_fidelity_verified=false`. It does **not** expose local input or cache output paths in the returned summary.
- `tests/test_core_fx_cache_worker.py`: 11 mocked-subprocess tests, not a true FFmpeg MOV codec test, using only an incomplete PNG IHDR byte header fixture (not a generated UI/art asset). Cross-platform Windows path mock mismatch found and fixed via `Path.samefile()`.
- `.github/workflows/step17-alpha-cache.yml`: focused tests plus all existing Python and CEP/ES3 JavaScript regressions on Windows and Ubuntu; live CEP stays on read-only `host/step03.jsx`.

## Verified CI on implementation SHA `c1e51a07a0ab28480aa804dddc5415c62cce818c`

[STEP17 Actions #37998026165 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37998026165):
- Windows: focused **11/11 PASS**, entire **99/99 JavaScript PASS**, full **256 Python tests, 253 PASS / 3 SKIP**, zero failures.
- Ubuntu: focused **11/11 PASS**, entire **97 JavaScript PASS / 2 Windows-only SKIP**, full **256 Python tests, 253 PASS / 3 SKIP**, zero failures.
- Real FFmpeg executable/alpha-pixel rendering on an actual PNG and Premiere host still **NOT** tested by this run. Mocked FFprobe readback cannot certify real QTRLE codec fidelity.

## Remaining developer work

Actual FFmpeg 30fps RGBA cache rendering/decoded first/hold/last frame alpha readback under independently provided trusted test assets; cache crash safety/recovery and Windows bundling; 19 unique remaining animation backends (no silent approximations); final approved crop/layout calibration; native/rendered MOV import to Premiere track with actual host readback, narration/background and MP4 output; eventual owner Windows 11 + Premiere 24.x final acceptance test.

**G1A/G2 PASS; G3 BLOCKED_HOST/UNVERIFIED. 0/21 host-certified animations. App incomplete. PR #20 Draft, main untouched.**
