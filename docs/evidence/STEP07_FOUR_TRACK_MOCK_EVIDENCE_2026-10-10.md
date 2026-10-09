# STEP07 four-track placement — implementation notes

**Primary implementation:** `core/track_plan.py`, `host/track_placement_adapter.jsx`.  
**Mock tests:** `tests/test_core_track_plan.py`, `tests/track_placement_adapter.test.cjs`.  
**CI:** `.github/workflows/step07-track-mock.yml` builds/test Windows and Ubuntu and verifies no live mutator leaked into CEP.

Documented public ExtendScript API references:  
- https://ppro-scripting.docsforadobe.dev/sequence/track/ — Track.overwriteClip(projectItem,time) using tick string; Track.insertClip can ripple, therefore not used.
- https://ppro-scripting.docsforadobe.dev/item/trackitem/ — start/end and duration Time objects, linked source project item; actual PPro runtime still unverified.
- https://ppro-scripting.docsforadobe.dev/sequence/sequence/ — Sequence.timebase decimal string; 0-based track collections.

No real Adobe installation, real audio isolation certification, imported footage, editable FX animation, or final MP4 was used or verified in CI. Test-only fixture durations/background loops are synthetic. **G3 BLOCKED_HOST**, all host AC pending. Do not merge main or release.
