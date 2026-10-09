# STEP07 Track placement adapter — mock CI evidence

Implementation commit: `0eda45af17bbd65f8beae8e5b25c384c6b87769b`.

[Windows + Linux CI run 37995908038 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37995908038).

| Layer | Windows | Ubuntu |
|---|---|---|
| Explicit ES3 Track adapter cases | 13 PASS | 13 PASS |
| Python timeline compiler cases | 11 PASS | 11 PASS |
| Complete Node regressions | 91 PASS | 89 PASS, 2 Windows-only skipped |
| Complete Python regressions | 116 PASS, 1 optional FFprobe skipped | 116 PASS, 1 optional FFprobe skipped |
| Live mutation-route guard | PASS | PASS |

The pure candidate generates V1 looping background, V2/V3 distinct instance placements, and A1 narration without truncating audio. Tick arithmetic is decimal-string exact (including host-side simulated ES3). Mock adapter applies `Track.overwriteClip`, then modifies only a new TrackItem in/out/end and validates exact TrackItem.start/end ticks/identity/track counts. Post-mutation failures are **INCOMPLETE** and never call deletion/retry.

**Source API:** Premiere Pro ExtendScript `Track.overwriteClip(projectItem, ticksString)` at https://ppro-scripting.docsforadobe.dev/sequence/track/ ; `TrackItem.start/end/inPoint/outPoint` are `Time` objects at https://ppro-scripting.docsforadobe.dev/item/trackitem/ . Actual clipping, image hold duration and linked-audio behavior are untested in real Premiere 2024.

This code deliberately remains **outside live CEP ScriptPath and signed release** because direct caller-supplied authorizations are not secure permission proofs and codec/render readiness is unfinished. G3 still BLOCKED_HOST. Application not complete.
