# SOL STEP23 — Fade-to-track source binding and exact clip-end guard

**Date:** 2026-10-10 WIB · **Architecture:** Premiere Pro 2024 CEP + ES3 + FFmpeg, unchanged. **Scope:** offline implementation / security stabilization of the already approved G03 FADE.BOTH, not a feature change.

## Concrete defect fixed

STEP22's read-only host inspector previously matched a clip by video track, start ticks and source nodeId, but **did not compare clip end ticks**. A manually trimmed/extended clip could therefore return a plausible component inventory while no longer matching the STEP21 FADE duration. The host inspector now requires an explicit `endTicks` argument, validates it using decimal-string comparisons (no floating point), and checks `selected.end.ticks` matches before reporting the clip's component inventory. It blocks changed/absent/malformed end ticks. No existing sequence, clip, keyframe, cache or asset is edited.

## New offline binding code

`core/fx_native_fade_binding.py`:
- Validates STEP21 native FADE candidate using the original B02 BOTH policy and SHA.
- Recalculates the existing STEP09 `track-placement-candidate-v1` canonical material hash, requires non-executable/readback-unverified flags, and validates each placement's unique `instance_key`, visual track, source reference and integer frame-to-ticks math.
- Finds **one exact** V2/V3 visual placement for the chosen scene/asset occurrence, requiring the identical `start_frame`, `end_frame`, asset `item_id` and duration; never substitutes another asset/preset or guesses offsets.
- Accepts only uniquely mapped, strictly formatted import `item_id` → `node_id` candidate references; requires an exact match for the planned imported item set, without paths or file contents.
- Assembles a **non-executable selector** containing only managed sequence GUID/name, V2/V3 track, exact start and end tick strings, source nodeId, B02 local Fade samples and their precise local tick offsets. Candidate is canonical-digest-pinned and can be validated by recompilation.
- Explicit limits: **not authenticated** against actual Adobe host source IDs, not actual Premiere tick semantics, no Opacity matchName/units/interpolation confirmation, `host_verified=false`, `can_assemble=false`, `time_coordinate_verified=false`. This is a binding candidate, **not authorization to write**.

## Tests and gate

- `tests/test_core_fx_native_fade_binding.py`: normal scene, later nonzero scene, exact local keyframes, forged Fade, tampered track plan/hash/frame, missing/duplicate/wrong media node, invalid managed sequence, forced readiness and stale media binding.
- `tests/native_opacity_inspector.test.cjs`: incorrect clip end ticks, manual trim and missing `clip.end` fail closed; correct candidate selector remains read-only.
- `.github/workflows/step23-native-fade-binding.yml`: Windows/Linux focused tests, complete Python/Node regressions and a static check ensuring only STEP03 is loaded in production CEP.

**No PNG, screenshot, logo, UI or other image created or modified. No new feature or preset, no Premiere host mutation, main merge or release.**

STEP19 strict real RGBA source-to-cache test may remain skipped without compatible owner asset; do not present that as PASS. The real Premiere G3 host gate remains NOT_VERIFIED; the 19 other animation backends remain unimplemented.

## Next STEP24

Build a non-executable clip-bound host response envelope with exact selector echo and source-ID/tick readback tests, strengthening protection against stale reports and switching targets. Do not invent Premiere capability or execute keyframe operations without an actual host-certified profile.

## CI evidence

STEP23 implementation gate must be assessed at the **exact latest SHA** on Windows and Linux. A simulated host is not actual Premiere; G3 remains blocked until final owner PC acceptance.
