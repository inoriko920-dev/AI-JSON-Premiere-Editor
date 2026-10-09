# STEP13 — Premiere clip source IN/OUT + cross-track readback (mock QA)

## Scope
- `host/track_placement_adapter.jsx`: actual ExtendScript ES3 code now applies source-relative clip trim `TrackItem.inPoint` and `outPoint` and confirms exact ticks before accepting each `Track.overwriteClip` placement, including V1 background loop segments, A1 narration and V2/V3 PNGs.
- The instance source OUT for a 6-second V1 loop at 30fps is frame 180; the next 5-second remainder is source OUT frame 150 (source IN frame 0 in both), not the sequence-relative end frame 330. Both get checked and mock tests prove the distinction.
- Every operation checks visible start/end ticks and A1/V1/V2/V3 counts. Unauthorized linked audio or linked video yields `INCOMPLETE` and no retry/cleanup.
- Input becomes invalid before the first host write when it uses unrepresentable source ticks, nonnumeric source frame, or wrong source_out_frame.

## Test and host limitations
This uses JavaScript mocks for Premiere objects. **No real Adobe Premiere Pro 2024 was executed**, and the host mutation script is still disconnected from `CSXS/manifest.xml`. The corresponding real TrackItem setter/API may behave differently in Adobe and must be tested on the owner's Windows 11 host **only after all coding is finished**.
- [STEP13 CI initial source trim commit — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37991554243) on SHA `42571910`, Windows + Ubuntu.
- [STEP13 CI linked-video protection implementation](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37991745058) on SHA `68d3378f`; check the workflow conclusion before claiming PASS.
- Prior STEP12 journal dispatcher is still simulation-only and explicitly rejects all external host callbacks, so it cannot yet execute a real operation.
- **G3 remains BLOCKED_HOST**, no main merge or release.
