# SOL STEP13 — source trim and linked-track readback (2026-10-10)

**Owner instruction:** finish feature/UI/integration coding and automated QA before requesting final Windows 11 + Premiere Pro 2024 hands-on testing. **G3 remains BLOCKED_HOST/UNVERIFIED.** No image assets generated or edited; no `main` merge or release.

## Actual changes
1. Fixed `host/track_placement_adapter.jsx` to use documented per-instance Premiere TrackItem **`inPoint`/`outPoint`** as Time objects (separate from sequence-relative `start`/`end`). Previously source IN/OUT frame values were validated but never applied during `Track.overwriteClip`.
2. Calculate source tick values from the approved host tick-string timebase by ES3 safe decimal-string multiplication without JavaScript 53-bit rounding. Reject impossible source frame lengths **before the first placement**, and reject missing source trim properties **after placement** with `INCOMPLETE`.
3. After each newly inserted clip, set `clip.inPoint.ticks` and `clip.outPoint.ticks` through `Time` object assignments; read both back, set/verify `clip.end`, recheck `clip.start`, IN and OUT. Never auto-retry or delete a partially changed sequence.
4. Extend anti-spill protection: after every clip, count expected clips on V1, V2, V3 and A1. Previously only unexpected linked audio was checked. Unexpected automatically linked VIDEO now stops `INCOMPLETE|UNEXPECTED_LINKED_VIDEO`.
5. Add source-trim, two-background-loop, narration, bad source frame and linked-video failure regression tests to `tests/track_placement_adapter.test.cjs`. CI workflow `.github/workflows/step13-source-trim.yml` checks Windows and Linux (mock only), plus all existing JS/Python regression suites.
6. All production CEP manifest/ScriptPath remains **P0 read-only**. This writing adapter and STEP12 simulated journal are NOT wired into live user interface and are not a released plugin.

## Adobe API basis
- `TrackItem.inPoint` / `TrackItem.outPoint` read/write source-relative `Time` properties, while `TrackItem.start` / `TrackItem.end` are sequence-relative: https://ppro-scripting.docsforadobe.dev/item/trackitem/
- `Track.overwriteClip(projectItem,time)` documented behavior, but actual Premiere Pro 2024 24.x host behavior **requires final host proof**: https://ppro-scripting.docsforadobe.dev/sequence/track/

## Still missing — continue coding on next LANJUTKAN
A real journal-to-host operation dispatcher with independent non-forgeable owner/capability evidence, post-import fresh SHA binding, operation receipts and safe crash/no-replay handling. Approved layout and image crop, 21 individual BOTH native/FFmpeg alpha animations, full integration/build/packaging and final host tests. Do not activate host mutation from CEP before independent guard checks are implemented.

**G1A SPEC PASS, G2 UI PASS, G3 HOST NOT VERIFIED.** 0/30 live acceptance cases and 0/21 effects certified; no finished MP4, production installer or release.
