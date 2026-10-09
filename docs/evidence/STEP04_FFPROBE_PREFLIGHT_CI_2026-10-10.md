# STEP04 FFprobe metadata preflight — code/CI proof (2026-10-10)

**Repo:** `inoriko920-dev/AI-JSON-Premiere-Editor`  
**Implementation SHA:** `d0d0724ac749edd694181dcb84ee6638303a21ef`  
**Real-smoke-test commit:** `6d454ab941f776f39f9e44bd6c4c22bcefe8a837`

## What was implemented
`core/ffprobe.py`: explicit executable path, no shell, static argument vector, 12-second timeout, 128-KB response check. Verifies actual FFprobe result structure, audio/video stream presence, codec names, sample rate, dimensions and positive duration. Fails closed on missing media, invalid binary, timeout and malformed/missing stream; unknown codec and absent duration are REVIEW. Reports **never** set `can_assemble=true`.

`core/validate_cli.py`: optional `--ffprobe-exe`, run only after valid JSON and media hash/header checks. `panel/validation_bridge.js` receives optional `AIJSON_P0_FFPROBE_EXE` from trusted process environment; no project JSON may set command path. `helper/validate_request.py` executes via fixed isolated interpreter. ZIP includes all 18 runtime modules with 19 SHA hashes, still TEST ONLY.

## Verified GitHub CI
- [Actions #37974300753](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37974300753): Windows 45/45 JS + 77/77 Python PASS; Linux 43 JS PASS, 2 Windows-only SKIP, 77/77 Python PASS. PowerShell archive contents/hash + malicious ZIP tests PASS.
- [Actions #37974518967](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37974518967): both OS SUCCESS. Additional opt-in **real FFprobe** regression was **SKIPPED on both** because neither CI image supplied FFmpeg/FFprobe executables by default; mocking tests and package checks passed.
- No dependencies were silently downloaded or installed during CI.

## Real FFprobe command verification in isolated developer environment
A Linux environment containing FFmpeg/FFprobe 7.1.5 ran the exact FFprobe `-v error -show_entries format=duration:stream=index,codec_type,codec_name,width,height,sample_rate,channels,duration -of json` command against a newly generated one-second WAV (mono, 48000Hz, PCM16) and one-second MPEG4 MP4 (64x64, 30fps); both returned code **0**, decoded metadata: `pcm_s16le`, sample rate `48000`, `mpeg4`, 64x64 and duration `1.000000`. This is **not** a test of the packaged CEP/Python module executing FFprobe and not a Premiere host test.

## Limits/next
Still no actual Premiere 2024 24.x CEP panel tests, alpha stream decode quality, approved codec policy, effect timing/crop or media write. **G3 BLOCKED_HOST**, G1B full preflight in progress, STEP04 implementation partial, no merge/release. User trial scheduled last after all feasible coding and automated tests.
