# SOL STEP05 — Premiere sequence adapter candidate, 10 Oct 2026

**Owner rule:** finish coding, integration, automated tests and bugfixes before final Windows 11/Premiere Pro 2024 manual test. **G3 real host is still NOT VERIFIED**; don't confuse mock checks with Adobe runtime success. No image generation/edits, no main merge or release.

## Implemented
- `host/sequence_adapter.jsx`: ECMAScript 3 implementation of read-only `inspect()` for Premiere 24.x host/version, active sequence tracks, dimensions and exact `timebase` decimal string. Uses documented `Sequence.timebase` property, not rounded seconds.
- Guarded `createNewEmpty(name, requestedGUID, requirements, authorization)` calls documented `app.project.createNewSequence(name,id)` only after explicit verified preflight/owner confirmation/capability/layout/FX flags (integration still blocked). Refuses existing sequence names/IDs, invalid new IDs, wrong profile/host, missing API. After create, checks one new sequence appeared and readback width=1920/height=1080, V1/V2/V3 and A1 counts, matching host timebase. Reports actual created ID on success.
- On inconsistent or exception-after-mutation: **INCOMPLETE**; preserve the new partially created sequence, never overwrite old sequence or auto-delete/retry.
- `core/host_ticks.py`: pure Python lossless frame*host timebase integer arithmetic; gives V2/V3 exact decimal-string target ticks (start/end/duration) for scene instances, rejects overlaps, malformed timing/track, and never marks plan executable.
- `panel/sequence_probe.js`: read-only fixed-expression bridge and strict response parser; values remain string ticks, sanitized host dimensions/track counts; timeout/cancel ignore old host replies.
- Mocked-host JavaScript and Python regression suites; all old JSON/media/SRT/FFprobe tests remain in CI.

**Important operational limitation:** The STEP05 JSX creation function is **NOT imported into the live CEP ScriptPath or panel action**. Tests only invoke it against mock app objects. A production assembly route must be enabled only after source preflight, host capability evidence, layout/FX backend proof and final Windows host test. There is no user action needed now.

## Remaining coding
1. Versioned approval/capability/crop/registry manifests with hash-bound immutable snapshots, real import of required PNG/background/audio into a safe new project bin, no retry to partial sequence.
2. Timeline V1 background loops, V2/V3 image placement and A1 narration with exact ticks and host track readback, failure journal and media recheck.
3. Animation 21 preset BOTH curves/native or FFmpeg alpha prerender, locking/phase time, track readback; tests and Windows distribution.
4. Full host validation deferred until final user test; existing CI cannot prove Premiere behavior.

**G1A SPEC PASS · G2 UI PASS · G3 BLOCKED_HOST** (untested). New STEP05 adapter mocked tests do not certify Premiere, media import, effects, or complete app. PR #5 Draft, `main` unchanged.
