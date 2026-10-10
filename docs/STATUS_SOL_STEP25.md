# SOL STEP25 — Full timeline native FADE ↔ actual FFmpeg alpha parity (10 Oct 2026 WIB)

## Why this STEP (no scope expansion)

The frozen B02 policy already approves G03 FADE, `direction=NONE`, `speed=MEDIUM`, mode BOTH, reference **15 IN / 7 OUT frames**. STEP16/18 compiled and genuinely decoded an isolated FFmpeg QTRLE/ARGB render; STEP21 compiled candidate editable Premiere Opacity keyframes; STEP23/24 bound exact clips and protected read-only diagnostic reports. **No preceding STEP directly proved those two independent reference curves agree on every frame.**

The other 19 presets lack calibrated motion/visual curves and cannot be silently approximated or replaced with Fade. STEP25 validates the one already implemented effect instead of inventing parameters.

## Implementation

- `core/fx_alpha_parity.py`: accepts only a validated, SHA-pinned STEP21 native FADE plan, recompiles the original reference with `core.fx_alpha_backend.compile_filter`, and rejects altered graphs/preset IDs or fraudulent `can_assemble` flags. Consumes only raw, decoded **1×1 RGBA bytes** from a **known opaque red FFmpeg lavfi video source**; checks **every** 30-fps frame's decoded alpha against native linear keyframe interpolation (0 → 100 → hold → 0). It also checks the expected opaque-red RGB source and rejects wrong length, unexpected RGB, or even one interior alpha mismatch. No PNG or image asset is generated/read/written by the module.
- `tests/test_core_fx_alpha_parity.py`: pure-byte correctness and tampering unit tests, plus **real** temporary 16×16 lavfi → FFmpeg GEQ → QTRLE/ARGB MOV → 1×1 RGBA decoded comparison. Test scenarios: 150-frame normal scene starting at global frame 90; 22-frame zero-hold minimum scene starting at zero. Ephemeral MOV stays inside a temporary directory and is deleted; there is NO UI artwork, screenshot or input source PNG.
- `.github/workflows/step25-fade-real-parity.yml`: Windows and Linux ensure real FFmpeg installation, forbid skipping binary test, run focused tests plus full Python and JavaScript/CEP regressions, and assert the 21-preset registry and Premiere host gate have not changed.

## Boundaries

Result code `OFFLINE_FULL_TIMELINE_ALPHA_PARITY_ONLY` explicitly marks `source_png_verified=false`, `full_frame_verified=false`, `native_premiere_verified=false`, `canva_fidelity_verified=false`, `host_verified=false`, `can_assemble=false`. 1×1 sampling verifies a known reference **alpha timing curve**, not image masking throughout the frame or faithful motion inside Adobe. STEP19's missing true-RGBA owner-PNG integration remains transparently SKIPPED where no suitable existing source is available; not a PASS.

Existing G1A/G2 approval and UI stay untouched. Real Premiere 24.x G3 unverified, 0/21 real host effects certified; FADE and WIPE FFmpeg render candidates, 19 backends unimplemented, no change in fixed user requirements. No main merge, tag, release, or Premiere project modification.

## Next STEP26

Stabilize already-approved effect/crop host preflight or continue evidence-backed implementation of another previously agreed preset without inventing motion speed/distance. Avoid generating images or stopping autonomous coding merely because optional extra QA artwork is missing.

## CI

Record exact SHA and both Windows/Linux run outcomes. Do not count skipped tests as success or declare production parity/visual approval.
