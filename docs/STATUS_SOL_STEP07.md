# SOL STEP07 — V1/V2/V3/A1 timeline operations and guarded still placement

**Owner instruction (10 Oct 2026):** finish UI/coding/integration and all feasible automated tests before the owner tests on Windows 11/Adobe Premiere Pro 2024 at the end. Real Premiere G3 remains **BLOCKED_HOST/UNVERIFIED**, no fake host PASS. No modifications to approved PNG UI assets, no main merge/release.

## Implemented in this development branch

- `core/track_worklist.py`: deterministic, read-only operation manifest of all four intended tracks. V1 loops the background and produces a shortened final segment; V2/V3 follow each asset's exact half-open integer frame positions; A1 narration spans the sequence and refuses too-short recorded audio. Every operation carries decimal-string Premiere tick targets, expected source trim and media item identity without calculating time from JS floating-point. Overlap, missing ID/hash reference, unreviewed source duration, resource limits and missing source are rejected.
- The worklist **never grants READY**, never imports media, never writes, is **DRAFT_NOT_EXECUTABLE**. Frame-accurate media durations are explicit external inputs **not yet independently host certified**. Full source trim/alpha/creative presets are blockers.
- `host/track_placement_adapter.jsx`: candidate ExtendScript ES3 `Track.overwriteClip(projectItem, startTicks)` for V2/V3 imported PNGs ONLY. Requires an explicitly reviewed owner/host/layout/effects/trim authorization object, managed sequence ID, approved managed bin and source nodeID, and an exact **whole timeline readback snapshot** before any mutation. Rejects overlap with any clip on the destination track. Post-insert checks newly created clip nodeId/source, exact `start.ticks`/`end.ticks` and all OTHER tracks unchanged; returns `INCOMPLETE` if any mismatch. **No automatic deletion/retry or editing existing sequence.**
- The JSX candidate is **NOT loaded by `CSXS/manifest.xml` or bundled in the active P0 ZIP**, so no live Premiere mutation route exists. V1/A1 placement is deliberately NOT claimed implemented in Premiere because source splitting, linking, source duration and trim have not been host validated.
- `tests/test_core_track_worklist.py` (11 pure Python tests) and `tests/track_placement_adapter.test.cjs` (13 mock-host JS tests) cover four-track operation mapping, background repeat, exact ticks, overlaps, missing media and zero duration; early rejects, partial host failures, linked-audio surprises and no overwrite of existing clips.
- A failing first CI run was caused by a V2 *test fixture* overwriting mock V3 via a captured closure. Corrected the fixture and retested; **not** marked green until actual CI reran.

## Latest CI evidence
[GitHub Actions #37981535195 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37981535195) at SHA `5102d2fe95a6f51ffd58810a035c24f5a56f57bb`.

| Runner | Dedicated mock JS | Entire JS | Entire Python |
| --- | --- | --- | --- |
| Windows | **13/13 PASS** | **91/91 PASS** | **117 total: 116 PASS, 1 optional FFprobe SKIP** |
| Ubuntu | **13/13 PASS** | **91 total: 89 PASS, 2 Windows-only SKIP** | **117 total: 116 PASS, 1 optional FFprobe SKIP** |

CI also asserts live CEP ScriptPath still contains only `host/step03.jsx`; neither sequence, media-import nor still-placement host mutation is exposed to users. Developer ZIP remains read-only.

## Continue next — actual coding, no manual owner test yet
1. Extend deterministic source trim and exact media duration proofs, with FFprobe approved source-frame counts (not rounded guesses). Host adapter candidate for **V1 repeated MP4 / A1 narration** with audio-link suppression and per-operation readback; no mutation without verified isolated clips.
2. Integrate approved layout/crop/alpha and native/FFmpeg backends for the **21 individual BOTH animations** (no guessed curves, frame phases or fallback).
3. Hash-bound host operations journal, failure isolation and partial state recovery, safe Windows package and final end-to-end tests.
4. Last step: actual Premiere 2024 v24.x Windows 11 host test to close G3 and acceptance cases. Until then **0/30 real host cases verified**, **0/21 animated effects host verified**.

G1A/G2 PASS; G3 BLOCKED_HOST, STEP07 unit/CI PASS, production assembly NOT READY. Draft PR, `main` unchanged.
