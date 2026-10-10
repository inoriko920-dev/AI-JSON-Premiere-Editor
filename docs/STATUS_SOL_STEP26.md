# SOL STEP26 — Atomic cache publication and post-link verification

**10 October 2026 (WIB).** This is a stabilizing fix for the approved FADE/WIPE offline alpha MOV cache; the 21-effect registry, frozen UI, two-JSON structure, original user media and Premiere 2024 CEP architecture remain unchanged.

## Concrete race fixed

Previously, `render_candidate` verified decoded alpha and hashed its private temporary QTRLE MOV, then published it atomically via `os.link`, but did not re-check the **published** inode or SHA afterwards. An external writer could modify/replace the staged or published file in that gap, leaving a stale `output_sha256` and an apparently successful render report.

The fix adds `_hash_stable_mov` for both private candidate and final published path. This uses `lstat`, `O_NOFOLLOW` when provided by the OS, read-only fd with `fstat`, regular-file requirements, SHA-256 and before/after inode+size+mtime+ctime consistency. The final hash **must equal** the verified private candidate's SHA and hard-link device+inode identity **must match**, or `E_FX_CACHE_CHANGED` is raised. No false successful render report is emitted. It does NOT overclaim protection from an actor who tampers after the final audit; normal cache reuse still runs the STEP20 re-open SHA audit.

Safety rule: **never auto-remove the published MOV** on integrity failure. The file remains for user reconciliation; future attempts for the same key must reject no-overwrite collisions. No owner media, UI or PNG modified.

## Regression

- `tests/test_core_fx_cache_worker.py`: mock tamper immediately after atomic link and replacement by a different inode with identical bytes; both must fail closed. Original media stays byte-identical, only unique workdir is cleaned; the questionable final MOV remains and cannot be overwritten. Separate success test verifies final SHA matches report and read-only restart auditor.
- `.github/workflows/step26-cache-publication.yml`: Windows/Linux regression with full Python + JS/ES3 test suites. Existing STEP19 workflow independently checks native FFmpeg QTRLE and alpha pixels on owner-approved unmodified PNG; a strict true-RGBA owner source may still legitimately **SKIP** and is not counted as PASS.

## Gates

This step does **not** certify real Premiere/Canva rendering. G3 native Adobe host remains NOT_VERIFIED, 19 of 21 preset backends not implemented. No generated PNG/screenshot/visual asset or feature/UI change. Do not merge to main or release while project gates remain unmet.

## STEP27 candidate

Continue closed-scope stability and fail-closed checks for existing render/import path (e.g. cache readback pre-assembly) without adding new effects or guessing unavailable Canva motion parameters. Do not demand owner PC testing before all safe automated implementation is complete.

**CI:** Use exact final commit and both OS runs for PASS. Do not treat skipped tests as PASS.
