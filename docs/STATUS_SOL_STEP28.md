# SOL STEP28 — Media Snapshot → Timeline Occurrence → Cache Identity Preflight

Date: 10 October 2026 (WIB). Scope: **existing** FADE/WIPE MOV cache and STEP09 candidate four-track timeline. No new feature, preset, UI, PNG, screenshot, or Premiere action.

## Defect closed

STEP27 checked that a cache report matches a caller-supplied SHA/dimensions and strict preset candidate, but did not independently bind those values to the **latest originally approved media inventory and the selected timeline instance**. An outdated imported PNG, another project, or a wrong scene occurrence could otherwise supply plausible `expected_source_sha256`, `instance_key`, and cache metadata.

New `core/fx_media_cache_track_preflight.py` performs the following in fail-closed order:

1. Verify the existing non-executable STEP09 track-plan canonical digest, video track placement structure, original project and timebase. Validate approved B02 FADE/WIPE candidate.
2. Validate STEP06 media snapshot schema and non-authorization gates, project ID, uniqueness of source IDs, imported source set vs four-track manifest, and the snapshot's canonical `inventory_sha256` matching the plan's `media_digest`.
3. Bind only one exact `scene/asset` occurrence to V2/V3, its approved source `ASSET_<id>`, source policy and exact start/end frame duration.
4. Immediately re-read/re-hash **all owner-existing source files** using STEP06's `recheck_media_snapshot` (including required SRT/audio/background), refusing missing/changed media. Read the selected PNG's existing IHDR **read-only**, validating resolution/alpha profile, path confinement and declared media reference. This creates no new source image.
5. Pass that original source SHA, independently re-read original dimensions and exact B02 FX item to STEP27's source-bound cache reuse audit; only a matching MOV with valid current SHA/inode and native FFprobe metadata may return a **non-executable** preflight result.

No automatic cache deletion, output path assembly, host mutation, or fallback to another animation. The result explicitly states `host_verified=false`, `can_import=false`, `can_assemble=false` and `source_recheck_at_host_transaction=false`: a file could change after this offline preflight, and source recheck remains mandatory at an authorized host operation.

## Tests and evidence

- `tests/test_core_fx_media_cache_track_preflight.py`: ten focused tests with **mocked source-filesystem/FFprobe boundaries** (not fake PNG generation). Covers matched inventory, stale source, mutated inventory digest, cross-project/track plan mismatch, wrong scene/frames, different effect, foreign asset linkage, unreadable source, hash-mismatched cached MOV, malformed limits and duplicate inventory IDs. The STEP19 real FFmpeg + approved unchanged PNG workflow remains an **independent** prerequisite for the complete offline suite.
- `.github/workflows/step28-media-cache-track.yml` runs focused and full Python regression plus Node/CEP ES3 regression on Windows/Linux and confirms the 21 agreed presets and non-certified host boundary.
- A test assertion/fixture mistake discovered by CI on the initial commit was fixed before completion: Python mock call `item`/ `report` are positional, and foreign asset test now uses an unambiguously nonexistent asset ID to check early rejection.

## Remaining gates

The stricter transparent-RGBA original PNG alpha-cache case **SKIPS** if no suitable user-owned file is present; that is not a pass. The real Adobe Premiere Pro 2024 host G3 remains NOT_VERIFIED, 0 of 21 effect instances host certified; 19 of 21 distinct preset render backends remain unimplemented. The two currently implemented offline effect candidates are FADE/WIPE.

This internal QA does not approve source/Canva fidelity, Premiere Opacity matchNames, crop position, image duration, or edit-in-place into a manual sequence. Do not merge main or release while specific project acceptance gates remain blocked.

## NEXT STEP29

Continue approved integration/stabilization. In particular, audit media digest consistency and cache publication/inspection against actual source time-of-check/time-of-use races, without changing approved UI or motion values or requiring owner-generated test art.

CI PASS must be grounded in **all applicable Windows/Linux jobs on exact final commit SHA**.
