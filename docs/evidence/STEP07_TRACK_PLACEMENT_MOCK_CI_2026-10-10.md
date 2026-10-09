# STEP07 — test evidence and exact host API boundary

## Source-code paths
`host/timeline_placement_adapter.jsx`, `tests/timeline_placement_adapter.test.cjs`, `core/timeline_lanes.py`, `tests/test_core_timeline_lanes.py`, `.github/workflows/step07-placement-mock.yml`.

API reference for Premiere's `Track.overwriteClip(ProjectItem, time)`, `Track.insertClip()` and `Track.clips`: https://ppro-scripting.docsforadobe.dev/sequence/track/ . Clip item `start.ticks`, `end.ticks` and `projectItem`: https://ppro-scripting.docsforadobe.dev/item/trackitem/ .

`Track.insertClip` is deliberately NOT used because it can ripple clips; `overwriteClip` is attempted only if the managed sequence destination track is empty, and every track is read back after placement. Even so a host-side effect may occur before a failure. Never call this on a user-edited sequence or blindly retry after INCOMPLETE.

## CI
- Initial run [#37984590942](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37984590942) failed due to test treating a source comment containing `setInPoint(` as a real execution call. **Not counted as successful QA**.
- Fixed run [#37984840574](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37984840574) SUCCESS Windows/Linux; adds exact decimal string subtraction and drops ES3 unsupported `Array.indexOf`.
- Final implementation run [#37985006310](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37985006310) SUCCESS Windows + Linux at code SHA `1b8ca49643724c5ae613eb5909fe0176badb25c5`.
  - Windows **14/14 focused JS PASS, 92/92 overall Node PASS, 113 Python PASS + 1 optional genuine FFprobe SKIP**.
  - Linux **14/14 focused JS PASS, 90 overall JS PASS + 2 Windows skips, 113 Python PASS + 1 FFprobe SKIP**.
  - Live CEP guard `NO_LIVE_HOST_MUTATION_ROUTE=PASS`.
- These are mocks + pure functions, **not** real Premiere Pro 2024 effects/track behavior. The host may differ from mocks; G3 explicitly remains UNVERIFIED.

## Next real coding
Implement host-verified source trims and safe per-track append contract, media authorization freshness, transform/crop per approved UI layout, linked audio side-effect handling, transaction journal and 21 BOTH FX engines. Owner manual test happens after all coding possible.
