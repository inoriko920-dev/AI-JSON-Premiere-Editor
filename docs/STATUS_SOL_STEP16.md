# SOL STEP16 — FFmpeg alpha renderer subset (2026-10-10)

**Owner rule:** code and test everything feasible first, final user Premiere 2024 / Windows 11 trial only at the end. `LANJUTKAN` requires actual coding, no repeat-only plans. G3 **BLOCKED_HOST** (still no real Premiere runtime), no UI PNG generation/modification and no auto-merge or release.

## Implemented in Draft PR #19
- Branch `sol/step16-ffmpeg-alpha-backend-20261010` continues the **most advanced coherent STEP15 PR #17** chain (STEP07 through STEP15), avoiding duplicated STEP07 efforts on older parallel branches.
- `core/fx_alpha_backend.py` builds real FFmpeg planar GBR+alpha `geq` expressions for **FADE** and **WIPE** (four precisely enumerated cardinal directions). RGB channels are copied unchanged, source size stays unchanged, only alpha changes. IN/HOLD/OUT uses **original MEDIUM B02 frame budgets**, without phase shortening/re-randomization, same preset on BOTH transitions. Alpha starts at zero on the first IN frame, reaches full alpha on the last IN frame, holds, and ends at zero on the last OUT frame.
- `build_ffmpeg_command()` returns a fixed **argument array only** for PNG `-loop 1` 30 fps → QTRLE/ARGB MOV, `-n` no overwrite and no shell. It validates absolute source/output paths, expected binary name and regenerated filtergraph against versioned B02 reference. Does NOT execute FFmpeg, write any source/media, create an output video on the user's PC, or import to Premiere by itself.
- **All other 19 presets still reject with `E_FX_BACKEND_NOT_IMPLEMENTED`**. In particular BRUSH/INK/DIGITAL/SPRAY_PAINT/SKETCH and transform presets must not be approximated with FADE/WIPE. No claim of 21 certified effects, visual equivalence to Canva, approved image crop, alpha quality in Premiere or working MP4 final.
- `tests/test_core_fx_alpha_backend.py`: 11 focused cases including unsupported presets, exact phase timing and reference tampering, arbitrary FFmpeg graph injection refusal, Windows/Linux absolute paths, `-n` no overwrite, and optional FFmpeg lavfi synthetic in-memory syntax smoke.
- `.github/workflows/step16-fx-alpha.yml`: Windows + Ubuntu unit and regression automation. CEP ScriptPath stays read-only `host/step03.jsx`; no mutation or renderer is accessible from panel.

## Evidence boundary
- Windows and Ubuntu success at prior code SHA `6215bd4c`: [Actions #37997018885](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37997018885), Windows 99/99 JS PASS, Ubuntu 97 PASS/2 Windows-only skipped, **245 Python tests** with 3 environment-only skips, 0 failures. Both GitHub runners lack FFmpeg for the optional live lavfi test (one focused skip).
- A separate isolated Linux FFmpeg executable ran FADE/WIPE left-right/top-bottom `geq` expressions against color-generated in-memory lavfi frames with `-f null -`, all exit code 0 and **no created PNG or MOV assets**. This confirms filter syntax only—not rendered quality, correct alpha values after encoding or Premiere compatibility.
- Latest additional commit improves exact alpha endpoints; require the latest CI result before stating final PASS.
- [Technical evidence](evidence/STEP16_FFMPEG_ALPHA_SUBSET_CI_2026-10-10.md).

## Next actual coding
1. Sandboxed/cache-scoped FFmpeg execution worker with SHA-pinned source and PNG→MOV alpha decode/readback, no overwrite and crash-safe output cleanup.
2. Distinct mask/transform implementations for remaining 19 presets using approved B02 semantics, no silent substitutions; pinned B02 reference calibration; then layout/crop and Premiere native/baked adapter.
3. Final host G3, 21 visual/live effect QA, real project imports/timeline/audio and MP4 export and Windows packaging at the **end**, per owner.

**App NOT finished. G1A/G2 PASS; G3 host unverified; 0/21 real host effects certified; no merge main or release.**
