# STEP07 automated coding evidence and host limits

**Branch:** `sol/step07-timeline-track-placement-20261010`. Based on step06, not `main`.

- `core/track_worklist.py` — V1 MP4 background loop *worklist*, V2/V3 PNG placement *worklist*, A1 narration *worklist*, deterministic hash, source frame ranges and decimal-string destination ticks. A worklist is **not** a Premiere sequence.
- `host/track_placement_adapter.jsx` — guarded V2/V3 still-host placement *candidate*, disconnected from live CEP. A true host must measure actual default still duration and trim, support V1 background and A1 audio separately, and confirm no accidental linked audio. No code here can claim it already does.
- Adobe scripting guide **Track.overwriteClip()** expects a tick-string argument on `Track`: https://ppro-scripting.docsforadobe.dev/sequence/track/ ; **TrackItem.start/end** return Time objects: https://ppro-scripting.docsforadobe.dev/item/trackitem/ . Real 2024 host still needs verification because docs/mocks are not runtime proof.
- Fixed mock regression on V2 by using an independent simulated destination, avoiding a V3 closure capture.
- CI [#37981535195 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37981535195): Windows **91 JS PASS / 116 Python PASS / 1 optional FFprobe SKIP**; Linux **89 JS PASS / 2 Windows skips / 116 Python PASS / 1 FFprobe skip**. No actual Premiere host job.
- NO active CEP ScriptPath for any Premiere mutation candidates. No source media, UI images or existing sequences were altered. All host counts still 0/30 AC and 0/21 animations verified.
