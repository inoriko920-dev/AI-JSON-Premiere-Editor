# SOL STEP30 — Pin alpha MOV bytes across native FFprobe and pixel readback

Date: 10 October 2026 (WIB). Scope: **existing** B02 FADE/WIPE MOV render/cache hardening only. No preset, UI, asset, source image, CEP, project, merge or release change.

## Defect corrected

STEP19 rendered and checked a private QTRLE MOV through FFprobe and sampled-alpha FFmpeg readback. STEP26 added source/private cache SHA + inode validation immediately **before** no-overwrite cache publication and immediately **after**. However, before STEP30, the MOV was *not SHA-pinned before FFprobe and alpha validation*. A concurrent writer could swap or modify the staged MOV during those long-running validations and leave a new file that was never proven equivalent to the MOV whose metadata/pixels were checked; STEP26 would then compute the hash of that already-changed file and report success.

STEP30 adds `_hash_stable_mov(output)` **immediately after render**, ahead of FFprobe and sample-alpha decoding. On successful readback, it computes a second stable SHA + device/inode identity and requires exact equivalence **before the existing atomic hard-link publish**. It then retains STEP26's final published-path SHA/inode recheck. A change or same-byte inode replacement between validation stages fails `E_FX_CACHE_CHANGED`, with no cache publish. The user's original PNG remains read-only and the only cleanup is the uniquely owned private work directory.

## Regression

- Added 3 focused tests in `tests/test_core_fx_cache_worker.py` exercising a mocked writer immediately after FFprobe, alpha validation mutating the same staged inode, and replacement of the staged file with identical bytes but a different inode while an alpha checker runs. All must fail without publishing or changing the original PNG. No new PNG, screenshots, UI assets, logo or diagram is generated; these use existing mock MOV bytes.
- `.github/workflows/step30-pinned-alpha-qtrle.yml` checks Windows and Ubuntu with focused cache tests plus complete Python and CEP/ES3 regressions. Native FFmpeg checks in the existing STEP19 and STEP25 workflows are additional required checks and must PASS on the final SHA.

## Boundary and honest gate

These hashes detect file changes during the validation window, not an arbitrarily malicious writer after the final audit; STEP20 read-only SHA check remains required when reusing a cache. Only isolated offline candidate status is possible: `can_assemble=false`, `host_verified=false`, original 21 preset registry unchanged, 19 distinct backends unimplemented, actual Premiere Pro 2024 G3 still NOT_VERIFIED. Owner-created genuine RGBA PNG input-to-cache integration case may remain an explicit SKIP without compatible file, not a PASS.

No source asset was created or edited, no Premiere host mutation, and no main merge/tag/release. User performs Windows acceptance only after all autonomous implementation work.

## STEP31

Continue safe internal stability of approved JSON→media→scene→FFmpeg/host candidate boundaries. Do not invent uncalibrated preset movement/duration or add features. A missing optional alpha-validation image must not block independent source-code work.

**CI requirement:** full exact final commit SHA, Windows and Linux, all applicable workflows must complete SUCCESS before declaring STEP30 offline gate PASS.
