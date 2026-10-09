# STEP08 offline preflight testing and gate

The new read-only `core/track_preflight.py` uses actual temporary on-disk sources in Python tests; FFprobe metadata is mocked for unit tests, never misrepresented as Adobe runtime. The input media root is isolated and not modified by the app. Tests check SRT cue references, file SHA snapshots, media altered during probe, audio shorter than 330 frames, unknown animation speed, missing binary/timebase, deterministic V1 background loops and V2/V3 imagery plus A1 narration.

CLI diagnostics preserve only candidate digest/total frames/track counts; `can_import=false`, `can_assemble=false`, candidate not executable. CEP ZIP: 24 files/23 SHA records and no write-capable host adapter. No automatic installer or main merge.

GitHub Actions: [STEP08 workflow](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/workflows/step08-preflight.yml). Cite a **completed SUCCESS run at exact commit** for final pass counts. A GitHub runner does not include Premiere 2024; **G3 is still BLOCKED_HOST** pending final user trial after all feasible coding.
