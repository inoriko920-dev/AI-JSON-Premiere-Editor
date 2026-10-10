# SOL STEP21 — Native FADE keyframe planner (2026-10-10 WIB)

## Baseline alignment

Master V3 prioritizes editable Premiere-native Motion/Opacity wherever feasible. B02 G03 FADE is the only approved opacity-only preset with literal `NONE` direction and 15-frame IN / 7-frame OUT MEDIUM reference. Exactly one preset per scene+asset, BOTH mandatory. The native path supplements (does not replace or weaken) the STEP16–20 source-alpha prerender candidate.

## Implemented

- `core/fx_native_fade.py`: deterministic, tamper-evident native Fade **keyframe candidate** for 0-based instance-local 30-fps indices:
  - first frame 0% opacity;
  - end of 15-frame IN (frame 14) 100%;
  - first frame of 7-frame OUT (index D-7) 100%;
  - last frame (D-1) 0%.
- Nonzero sequence/global start offsets do NOT shift the instance-local keyframes. Zero-HOLD D=22 yields indices 0,14,15,21 with no hidden retiming or frame omission.
- The compiler reuses the existing STEP16 strict reference and phase-range validator. FAST/SLOW, IN-only, different directions, forged backend flags, changed reference timings, other presets and short clips fail. A validator recomputes a SHA-256 candidate digest and exact compiler output before any use.
- Real Premiere Opacity component `matchName`, effect param id, Time object coordinate space, host-build version, sample interpolation and keyframe readback **remain unverified**. The payload deliberately has `host_component_match_name=null`, `host_verified=false`, `readback_verified=false`, `can_assemble=false`. It is NOT an executable host editing operation.
- `tests/test_core_fx_native_fade.py`: positive 150- and 22-frame cases, nonzero start, explicit FADE.BOTH endpoints, preset non-substitution, tampered flags, short scene fail-closed, rehashed payload checks.
- `.github/workflows/step21-native-fade.yml`: Windows/Linux exact tests plus full existing Python and JS regressions, host gate remains blocked.

## Important nonclaims and limitations

- This step does **not** change any approved feature, UI, layout or scope. No PNG was created, modified or substituted. No host mutation, import, timeline rendering, destructive media changes, main merge, tag or release.
- Even if all tests PASS, native FADE remains **not host-certified** until a later Premiere Pro 2024 run. This is a coding progress milestone, not end-to-end application completion.
- Other 19 FFmpeg animation presets still unimplemented. 2/21 FADE + WIPE prerender-alpha candidates remain; FADE now additionally has a native *keyframe planning* candidate. Exact visual match to Canva is not claimed.
- Separate RGBA PNG full-cache integration test is still SKIPPED when no compatible owner PNG exists; do not reinterpret the skip as PASS or treat unrelated coding as blocked.
- Keep PR Draft, do not merge into `main` or release while G3 host approval and real preset gallery are still pending.

## STEP22 suggestion after STEP21 gate

Add a guarded and separately testable Premiere Pro 2024 native Opacity parameter readback/preflight adapter, mapping only certified host ids and exact instance-relative 30-fps keyframe coordinates. Do not guess parameter matchName or Time semantics; no real host write until capability and authorization gates PASS.
