# SOL STEP32 — Original owner PNG freshness through FFmpeg alpha-cache publication

Date: 10 October 2026 WIB. Scope remains the agreed FADE/WIPE alpha MOV render cache, without modifying the approved UI, behavior, JSON contract, 21 animation presets, PNGs, or Premiere Pro 2024 project. No visual image was generated.

## Proven gap

STEP31 verifies the owner PNG identity during the initial copy and rehashes the **private staged PNG** before/after FFmpeg render + pixel checks. However, the owner's **original** file could change after that copy while the private image stayed intact, leaving a successful MOV cache report for a source which no longer matches the current original on disk. In particular, a concurrent overwrite or same-byte different-inode replacement of the owner path after staging would not be detected by the staged-only checks.

## Code changes

`core/fx_cache_worker.py` now reads the owner source again using the existing stable regular-file `_hash_stable_mov` check after the private copy and before FFmpeg starts. It requires source SHA to still equal the independently pinned expected original SHA. It then compares original source SHA plus device/inode **again after** FFprobe and sampled alpha-pixel verification, before cache publication. Finally, after the no-overwrite MOV hard link and published MOV SHA/inode verification, it compares the original file a third time before returning a success report. Source changes raise `E_FX_SOURCE_CHANGED`. The code only reads original owner media; it never modifies it.

The publication window remains fundamentally non-atomic across distinct user-media and cache directories, so this is a **bounded freshness check**, not a guarantee against concurrent change after the final read. If the original changes after the cache MOV has been published but before the report can succeed, the new MOV remains for reconciliation. On subsequent same-key attempts the existing no-overwrite rule raises `E_FX_CACHE_EXISTS_NO_OVERWRITE`, rather than silently deleting/replacing potentially valuable evidence.

STEP31's staged-source and STEP30/26's private/published MOV consistency checks remain mandatory and unchanged. A different source SHA still cannot be treated as the same render candidate.

## Regression tests / CI

Three tests added in `tests/test_core_fx_cache_worker.py`, using only previously existing tiny mock bytes and temporary paths (no new PNG graphic, logo or source artwork):
1. Another process modifies original owner PNG after FFprobe has read the private MOV → no MOV published and no success report.
2. Another process replaces owner PNG with a same-byte new-inode file during alpha readback → invalidates candidate despite unchanged SHA.
3. Original PNG changes at the final MOV publication step → no successful report; published MOV is **preserved** and next same-key render refuses overwrite.

`.github/workflows/step32-source-freshness.yml`: focused cache tests, full Python security tests and complete CEP ES3/JS regression on Windows and Ubuntu. STEP19 actual FFmpeg cache and STEP25 real opacity parity checks remain independent exact-head prerequisites.

## Limits and next phase

Actual Adobe Premiere Pro 2024 host G3 remains NOT_VERIFIED, 0 of 21 animation presets host-certified; only FADE/WIPE have FFmpeg offline candidate backends; 19 distinct preset backends remain unimplemented because source-calibrated motion data is unavailable. Genuine owner alpha PNG-to-cache end-to-end integration can still SKIP without a suitable existing user-owned transparent source; SKIP is not PASS.

No main merge/tag/release, UI redesign, approved feature modification, user image generation or premature manual PC test.

## STEP33

Continue implementing and stabilizing approved JSON→source→timeline→FX boundaries with precise reference-derived behavior. Do not invent missing motion distances, timings, host matchNames or artwork. Do not grant real-host authorization based on mock tests.

**Gate requirement:** final commit and every applicable Windows/Linux CI workflow must finish SUCCESS before STEP32 can be marked offline PASS.
