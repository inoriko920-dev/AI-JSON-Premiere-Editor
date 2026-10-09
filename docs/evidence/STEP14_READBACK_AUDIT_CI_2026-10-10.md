# STEP14 — host readback audit CI & compatibility notes

**Implementation SHA:** `3761b15b2a2584d2b2a0837e9bfc43af25f52088`  
**[Windows+Linux CI #37993572759 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37993572759)**. Tests include cross-language Node/ES3 mock → Python audit.

### Readback contract
Input `track-placement-candidate-v1` or `derived-track-candidate-v1` remains `CANDIDATE_NOT_EXECUTABLE` (`can_import=false`, `can_assemble=false`). Input observation `premiere-track-readback-v1` must be `CAPTURED_UNVERIFIED`, with exactly V1/V2/V3/A1 plus no unknown extra clips; source item node ID mapping comes from imported source readback. The reconciler checks every clip in the requested prefix (including empty tracks), exact integer tick strings, source IN/OUT, item identity, clip IDs and sequence UUID.

Result `READBACK_MATCHED_UNVERIFIED` or `READBACK_MISMATCH` is **never host attestation or write authorization**; it carries no paths, filenames or actual IDs. A fabricated observation could still match. External callback to STEP12 simulation dispatcher remains rejected. Source frames are never inferred from GIF, SRT timing estimates or host seconds.

### Adobe API references
- [TrackItem source in/out, start/end, nodeId, projectItem](https://ppro-scripting.docsforadobe.dev/item/trackitem/)
- [Sequence video/audio tracks](https://ppro-scripting.docsforadobe.dev/sequence/sequence/)

### Scope boundary
`host/readback_observer.jsx` is NOT packaged into the active CEP `CSXS/manifest.xml` ScriptPath. Real Adobe CEP and Premiere are not present in GitHub CI. Existing handoff and approved UI image binaries were not changed, `main` untouched, PR stays Draft.
