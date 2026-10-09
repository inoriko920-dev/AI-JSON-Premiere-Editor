# SOL STEP10 — Derived background video-only overlay (10 October 2026)

**Current owner rule:** Continue coding, integrating and CI testing autonomously. Ask the owner to try Windows 11 + Premiere Pro 2024 only at the end. Host G3 remains **BLOCKED_HOST / UNVERIFIED**; unit tests are not equivalent to an actual Premiere render.

## Real code implemented

- `core/background_overlay.py`: read-only provenance check for `core/background_audio.py`'s separately cached MP4 with audio removed. Rechecks SHA-256 of **all source files** through the existing original media snapshot, verifies the newly generated cached MP4 has its claimed hash, byte count and legal cache path/name, and probes original/derived video using an explicitly supplied absolute FFprobe binary, fixed argv, `shell=False` and bounded output/time.
- The original MP4 must have video+audio; the derived result must have exactly one video stream and no audio, subtitles or other streams. Matching `codec`, width/height, exact `30/1` frame rate, explicit positive `nb_frames`, video start time and video stream duration are required. Source/candidate re-hashed again after probing. Any uncertain or changed property **rejects** binding rather than assuming a safe media source.
- The overlay is a `derived-background-overlay-v1` private candidate with a hash fingerprint binding the original snapshot to the video-only cache. Never rewrites the user's EDIT_PLAN/ANIMATION_PLAN JSON or original media. It is always `CANDIDATE_NOT_AUTHORIZED`, with `can_import=false` and `can_assemble=false`.
- `core/derived_track_binding.py`: performs the media verification AGAIN before binding the source to V1 placements of the offline STEP07 track candidate. V1 source references now point to **DERIVED_SOURCE_BACKGROUND** and preserve requested `source_in/out_frame` ranges. Checks video frame count, source trim, all V1 clip boundaries contiguous without overlap/gaps, snapshot fingerprint and plan shape. Leaves V2/V3/A1 placements unchanged. Public summary exposes only counts and digest; path is confined to the **internal, non-executable** plan object.
- New `tests/test_core_background_overlay.py` and `tests/test_core_derived_track_binding.py`: real hash/filesystem operations with mocked FFprobe responses, including cache tamper, source change, wrong FPS, changed frame count, changed video timestamps, audio remaining in cache, unexpected streams, invalid input, illegal path, wrong worklist digest, and V1 trim overflow. No user images or media are created/modified.
- `.github/workflows/step10-derived-overlay.yml`: Windows + Ubuntu Python and JS regressions. The first workflow YAML parse failure and a Windows temporary-directory path-normalization fixture bug were fixed in subsequent commits. **Final CI run must be examined for source SHA before marking PASS**.

## Safe boundaries & next coding

**Host G3 = BLOCKED_HOST.** No source-import or timeline-changing Premiere adapter has been connected to the P0 CEP extension; there is no permission to assemble. Comparing stream metadata is not the same as full decoder/alpha/PTS or clip playback/readback on actual Premiere. An accepted overlay may be rejected on some remuxed sources whose video start/duration or frame count cannot be independently proved. This is intentional fail-closed behavior, not silent fallback.

Next implementation priorities: verify host-level source trim of partial background V1 loops, prove no linked A-track audio appears after video-only V1 placement, keep a transaction journal for incomplete placements, then approved layout/crop and 21 animation presets with BOTH IN+OUT, native/prerender FFmpeg tests, and final Windows package.

Original STEP01/G1A and G2 approved UI are intact. 0/30 real host acceptance cases and 0/21 animation presets host-certified. No merge to main, no release/installer, no manual PC test required now.
