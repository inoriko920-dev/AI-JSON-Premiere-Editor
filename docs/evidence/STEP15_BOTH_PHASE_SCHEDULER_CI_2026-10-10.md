# STEP15 BOTH MEDIUM scheduler — CI proof and limits

**Code SHA:** `69049289b4b04e4763eae44287135536e8e96851`.  
[Actions Windows + Ubuntu #37994743727 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37994743727).

The scheduler is implemented in `core/animation_phases.py`; reference frame durations/evidence were copied from `docs/planning/STEP01_B02_PROPOSED_21_DIRECTION_REGISTRY.csv` into `core/animation_timings_b02.json`. A regression test reads the actual ASTRA CSV and compares all **21** preset entries including IN, OUT and evidence level. No source visual imagery was generated or modified.

For each occurrence `(scene_id, asset_id)`: keep the single locked preset, direction and MEDIUM speed; generate disjoint half-open intervals `[start,start+IN)`, `[start+IN,end-OUT)`, `[end-OUT,end)`. Reject durations below `IN+OUT` as `E_TIME_006` with no truncation. Equality yields zero HOLD requiring later visual QA. Outputs deterministic SHA; `can_render/can_assemble/host_verified` always false.

`core/validate_cli.py` exposes only count/digest when `--include-animation-phases --max-animation-instances` is explicitly used. CEP requests this read-only check, sanitizes response and shows a non-renderable summary. It never changes Premiere. The CEP Windows pilot package now contains 26 allowlisted files and 25 SHA entries.

CI confirms **Windows 99/99 JS pass, 234 Python tests completed with no failures; Ubuntu 97 JS pass, 2 Windows skips, 234 Python tests with no failures**, dedicated 11/11 STEP15 Python passes per OS. Optional FFprobe-related Python tests can skip if binaries are absent. Genuine Premiere Pro 2024 host, 21 visual effect implementations, native keyframe curves, RGBA alpha and output MP4 were not evaluated: **G3 NOT VERIFIED**.
