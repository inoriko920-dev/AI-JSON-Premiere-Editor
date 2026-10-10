# SOL STEP18 — Real FFmpeg Alpha MOV Roundtrip (2026-10-10)

## Scope and discovered blocking defect

Previous STEP16/STEP17 mocked tests were green but did **not** decode genuine MOV pixels. Independent native FFmpeg 7.1.5 execution exposed a real bug: the generated `geq` progress equation referenced `D` (duration), which is **not** a valid `geq` expression variable. Real FFmpeg exited with `Undefined constant or missing '('`. Therefore STEP17's successful mock-based metadata run **did not imply render correctness**.

## Code changes

- `core/fx_alpha_backend.py`: embeds the compiler-verified exact integer total frame count instead of a symbolic `D` in the frame-based progress expression. Still validates B02 BOTH / MEDIUM frames and rejects arbitrary user-supplied graphs.
- `tests/test_core_fx_real_alpha_readback.py`: runs native FFmpeg with a synthetic, in-memory `lavfi` solid-color stream, creates **only a private temporary MOV** (never a PNG, owner UI asset or project file), probes codec `qtrle`, pixel format `argb`, dimensions `16x16`, 30 fps and 150 decoded frames, then decodes raw RGBA through a pipe. Examines alpha at actual IN/HOLD/OUT boundaries, interior fade progress, and the four directional WIPE masks. Temporary MOV is deleted automatically.
- `.github/workflows/step18-real-alpha.yml`: Windows/Linux job asserts genuine `ffmpeg` and `ffprobe` are installed, runs real alpha roundtrip plus previous Python and JS regressions. Real codec validation tests cannot silently fall back to mocked subprocess calls on CI.
- No user-provided images generated, modified or used as substitutes. No CEP host mutation, no rollout or `main` merge.

## Local independent native diagnosis (Linux, FFmpeg 7.1.5)

- Pre-fix: FFmpeg error `Undefined constant or missing '('` for `D-N-1`.
- After replacing `D` with the exact total of 150 frames: native FFmpeg accepted the filtergraph; decoded 150 raw RGBA frames.
- Independently generated small test MOVs for FADE and each of four WIPE directions were decoded with FFmpeg and reported as QTRLE/ARGB by FFprobe; alpha masks changed correctly at the sampled pixels.

These are developer-environment checks and must **not** be conflated with GitHub Windows and Linux CI results, whose exact run IDs must be recorded after completion.

## Gate

- STEP18 implementation: delivered to isolated Draft PR (CI verdict pending until GitHub runs finish).
- Real synthetic FFmpeg MOV pixel readback: covered. **Real user PNG-to-cache worker alpha verification remains pending**; STEP17 `alpha_pixels_verified=false` correctly stays false.
- Full 21-preset implementation: 2 candidate backends / 19 unimplemented.
- Canva fidelity: NOT VERIFIED.
- Premiere Pro 2024 live import and full timeline: **G3 BLOCKED_HOST / UNVERIFIED**.
- Owner image-generation work: not requested or performed.
- Final owner manual acceptance, packaging, release: not started.

## Next STEP19

Implement fail-closed cache-worker alpha validation against **existing owner-approved PNG inputs** (read-only source and private snapshot only) and sampled real MOV frames, with resource caps and race-safe cache publication. Do not make alpha certification or host import claims from metadata alone.
