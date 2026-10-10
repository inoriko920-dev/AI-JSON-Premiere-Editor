# SOL STEP24 — Nonce-bound FADE host readback envelope

**Date:** 2026-10-10 WIB. **Fixed scope:** G03 Fade/BOTH source and target validation for Adobe Premiere Pro 2024 CEP + ExtendScript. No new preset, UI, behavior or asset. This step is an isolated offline diagnostic, **not production execution**.

## Issue

STEP23 binds source node ID, sequence, track, start/end ticks and FADE candidate digest. STEP22's host component inspection returns only component metadata; the reply itself does not carry the target or request identity. A stale/unrelated (including different-clip) component report could be mistaken for the latest response if the caller fails to associate its request with the response.

## Changes

- `host/native_fade_readback_envelope.jsx` is an ES3 read-only adapter that wraps the existing `$._AIJSON_NATIVE_OPACITY_INSPECT_V1.inspect` and demands explicit managed sequence name/ID, V2/V3 track, start/end ticks, source node ID, previously bound candidate SHA and an exact lowercase 128-bit challenge string. It returns an encoded, bounded `S24|1|OBSERVED_UNCERTIFIED` report including all selector fields and the nested S22 report. A mismatch, missing inspector, unexpected Premiere version, changed clip length, missing component or inspection exception results in `BLOCKED`. Neither ES3 module is wired into the production CEP ScriptPath; neither edits timeline/media/parameters.
- `core/fx_native_readback_session.py` constructs a new nonce using `secrets.token_hex(16)` after validating the STEP23 canonical binding against its Fade, track plan and imported media map; a session accepts **at most one response** and burns the challenge before validating untrusted bytes. Checks every echoed selector, bound digest, strict encoding, freshness relative to challenge, and the STEP22 defensive S22 parser. Rejects a swapped source node, altered end/start, different sequence, outdated nonce, replay, forged certification, malformed Unicode/percent encoding, and changed current binding.
- **Security boundary:** a nonce and echoed digest correlate reports; **they do not authenticate Adobe Premiere or prevent a malicious caller forging a complete response with a known nonce**. No user-visible host trust is granted. Response remains `SOURCE_AND_SELECTOR_ECHOED_NOT_HOST_CERTIFIED`, `host_verified=false`, `can_assemble=false`, `time_coordinate_verified=false`. Real Premiere host identification, parameter IDs, real timing interpolation and actual write/readback are outstanding.
- `tests/native_fade_readback_envelope.test.cjs` and `tests/test_core_fx_native_readback_session.py`: mocked host and Python tests for stable binding, stale/replayed challenge, exact selector mismatch, source node substitution, altered end, blocked host inspector, oversized/malformed report, fake approval and nonzero instance-local keyframe semantics.
- `.github/workflows/step24-native-fade-readback.yml`: Windows/Linux full Python and JS regression plus static safeguard that neither diagnostic script is included in the production CEP panel. Additional real FFmpeg alpha-cache regression remains an independent workflow.

## Evidence and remaining blockers

STEP24 gate requires **all relevant checks on the exact commit** to PASS. Skipped native binaries/tests are not equivalent to actual Premiere host proof. True transparent owner-PNG-to-cache integration remains SKIPPED without a suitable existing file, but this does not block offline code improvements.

**G3 Premiere host** is NOT_VERIFIED: 0 of 21 effects host-certified; 19 of 21 distinct FFmpeg backends unimplemented. G03 native Fade keyframes remain a candidate, while FADE and WIPE have uncalibrated FFmpeg render candidates. Do not merge, release, rewrite user PNG, generate visuals or request final Windows acceptance until remaining autonomous coding/tests complete.

## Next STEP25

Continue unimplemented, already-agreed animation subset only when its motion parameters are supported by frozen reference contracts; otherwise prioritize independent fixture/QC stability, avoid guessing native `matchName` / new image prerequisites. No new features without user instruction.
