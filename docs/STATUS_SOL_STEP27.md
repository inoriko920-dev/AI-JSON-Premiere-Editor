# SOL STEP27 — Strict source/preset binding before reusing a cached MOV

**Date:** 10 October 2026, WIB. **Scope:** existing FADE/WIPE QTRLE cache validation ONLY. No added presets, UI changes, host mutation, PNGs or new owner assets.

## Defect and remediation

STEP20's `verify_cached_report` validates that the MOV bytes, SHA-256, codec and frame metadata match a *previous report*. However, a correctly formed report can be associated with the **wrong source asset or different animation** on subsequent attempts. Its SHA/metadata audit does not bind the report to the **current requested** PNG hash, FADE/WIPE preset, direction and frame timing.

New `verify_cache_for_candidate` in `core/fx_cache_worker.py` takes the trusted independent **expected source SHA256** and **expected source geometry** along with the existing STEP15/B02 candidate. It recompiles using the existing strict STEP16 `compile_filter` (BOTH, MEDIUM, immutable reference); reconstructs the original cache key via a common `_cache_key` helper; compares key, preset, frame count, width and height to the report **before** any subprocess operation. Only then calls STEP20's existing read-only SHA/inode and FFprobe auditor. Missing/bad caller source hash, invalid type geometry, wrong asset, wrong direction, wrong preset, altered timing or falsified size **fail closed**. No cache image/video is opened for the early rejected cases.

The shared `_cache_key` avoids drift between the render path and reuse path, preserving the existing cache key format `fx-alpha-cache-v2-alpha-sampled`—existing valid caches do **not** get renamed/invalidated by this change.

## Verification / privacy

Added six tests to `tests/test_core_fx_cache_worker.py`:
- Valid cache reopens with exact identity and explicitly non-authorizing audit.
- Different source SHA: no probe or deletion.
- Wrong Fade/Wipe preset or WIPE direction: no probe.
- Wrong asset dimensions or altered report frames/preset: no probe.
- Unpinned/malformed source hash, bool/non-integer dimensions: reject before probe.
- Correct identity but corrupt cache content: STEP20 integrity check rejects; file preserved.

`.github/workflows/step27-cache-reuse-binding.yml` tests Windows and Linux with full Python and CEP/ES3 regressions. Existing STEP19 live FFmpeg workflow independently verifies QTRLE actual MOV from a read-only approved PNG and remains separately required.

**Security boundary:** The expected source hash and dimensions must come from earlier independently authenticated source-media preflight, not from untrusted reused reports. This offline association **does not itself re-read the source PNG**, re-check alpha pixels or authorize Premiere import/assembly. Returns `source_bytes_reverified=false`, `alpha_pixels_reverified=false`, `host_verified=false`, `can_assemble=false`. This is cache integrity work only.

Real Premiere Pro 2024 G3 NOT VERIFIED; original 21-preset contract remains frozen, with FADE/WIPE QTRLE offline candidates, 19 backends still unimplemented. Transparent RGBA owner-PNG strict integration can still SKIP when compatible owner asset absent (not a PASS). No image created/generated/modified, no main merge/tag/release.

## Next STEP28

Continue already-agreed offline effect/asset preflight stabilization without inventing visual parameters; prioritize validated cross-stage media ownership and guaranteed rejection of stale cache references before future assembly.

**Gate:** exact final commit must pass all applicable Windows/Linux workflows, including existing FFmpeg checks.
