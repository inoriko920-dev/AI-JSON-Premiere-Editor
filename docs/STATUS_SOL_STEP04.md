# SOL — STEP04 ongoing implementation, 10 October 2026

**Working rule:** Continue all safe coding, integration, CI and bugfix work first; owner's Windows 11 / Premiere 2024 hands-on test is deferred until coding is done. G3 remains **BLOCKED_HOST / NOT_VERIFIED**, never PASS on unit/CI alone.

## Completed code in Draft PR #4
- Native CEP file selection for both distinct JSONs and required media root, secure isolated Python helper process (no shell), hard-coded read-only CLI arguments, cancellation and sanitized status report.
- Strict contracts, pair/scene/BOTH/track timing rules, SHA-256/path/SRT checks and deterministic non-executable timeline draft (demo 330 frames).
- **NEW: `core/ffprobe.py`** — optional explicit absolute local `ffprobe(.exe)`, fixed `subprocess.run([...],shell=False)` without any JSON-derived executable/flags, 12-second timeout, bounded response and safe error codes. Probes actual narration audio + background video stream types, codec, sample rate, resolution and duration. Unknown codecs/duration are review, missing streams/read errors fail closed. It **cannot** certify decode, alpha, 21 effects or Premiere host.
- `core/validate_cli.py` now runs FFprobe metadata after JSON and media hash checks, if configured. If no FFprobe, status `E_FFPROBE_UNAVAILABLE` / REVIEW; if media invalid, FFprobe SKIPPED. Bridge only reads optional trusted environment variable `AIJSON_P0_FFPROBE_EXE`, never from user JSON. No app READY status.
- Unsigned development CEP bundle updated: 18 runtime files + README + checksum manifest, **19 SHA-256 entries**. Windows tester/stager remains explicit consent, no registry changes/overwrite.
- [Detailed FFprobe/CI report](evidence/STEP04_FFPROBE_PREFLIGHT_CI_2026-10-10.md).

## CI proof
- [Windows + Ubuntu Actions #37974300753 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37974300753) on implementation SHA `d0d0724a`: Windows **45/45 JS + 77/77 Python PASS**, Ubuntu **43 JS PASS, 2 Windows-only skips + 77 Python PASS**, Windows malicious ZIP suite PASS.
- [After optional real FFprobe smoke test added: #37974518967 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37974518967): Windows 45 JS + 78 Python tests (one Python **SKIP** because real ffprobe/ffmpeg binaries absent on runner), Ubuntu 43 JS PASS (2 skip) + 78 Python tests (one Python **SKIP** for same reason). This means **real FFprobe smoke was not performed on GitHub CI**.
- Separately, inside the available isolated Linux environment with actual FFmpeg 7.1.5, a generated one-second 48kHz mono WAV + one-second 64x64 MPEG-4 MP4 were probed with the exact fixed FFprobe arguments: return code 0, codec `pcm_s16le` / `mpeg4`, 1.000 seconds each. This checks real FFprobe command/metadata but **not Adobe Premiere or the full application UI**.

## Remaining actual features
Resource/codec production policy and full decode gate; original profile/crop hashes; safe native Premiere sequence creation/import/move/readback + rollback; native and FFmpeg prerender EACH of 21 BOTH animations; deterministic phase curves, cache/journal, crash recovery; Windows bundle signing/integration; automated stress tests. No Adobe Premiere host tests yet.

G1A SPEC PASS; G2 approved UI PASS; **G3 BLOCKED_HOST** deferred to final manual test; no 21 effects certified and no host AC verified. No merge to main, no release, no claim of finished app.
