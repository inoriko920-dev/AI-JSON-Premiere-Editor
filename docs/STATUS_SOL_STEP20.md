# SOL STEP20 — Cache Integrity on Restart and Full-Stream Validation

Date: 2026-10-10. Scope: **internal resilience/security only**; no new menu, panel, feature, UI image, animation preset, or change to JSON/project export behavior.

## Existing defect and security improvement

STEP19's FFprobe command used `-select_streams v:0`, which silently hid additional audio, data and video streams. A MOV file can contain unexpected secondary streams even while the selected QTRLE/ARGB video looks valid. The cache worker now probes **all** streams and requires **exactly one** valid QTRLE/ARGB 30-fps video stream of the expected source dimensions and frame count.

## Offline restart proof

- New `verify_cached_report` in `core/fx_cache_worker.py` re-opens an **existing** SHA-addressed cached MOV in read-only mode from its expected key and a trusted prior render report. It rejects missing entries, symlinks, malformed reports, wrong SHA-256, wrong size/metadata, unexpectedly large files, and file mutation while reading/probing.
- Uses stat identity checks before/after the file digest and metadata probe; retains `no-overwrite` and never deletes or repairs a potentially valuable cached file automatically.
- IMPORTANT: this audit does NOT re-certify source-relative alpha pixels, entire frames, Canva motion fidelity or Premiere Pro 2024. Its return claims only `SHA256_AND_METADATA_CHECKED` with `host_verified=false` and `can_assemble=false`.
- Existing `render_candidate` sampled-alpha QA and cache key remain unchanged, other than strict refusal of additional MOV streams.

## Regression proof

- Unit tests: valid cache reopen, cryptographic tampering, forged report including path traversal, missing cache, oversize, changed content during FFprobe, hidden audio, symbolic link, and read-only user PNG.
- Native Windows and Linux test extends existing owner-approved RGB PNG **read-only** codec transport: creates only private temporary MOV(s) from the existing file and tests that FFprobe accepts a pure QTRLE MOV but rejects a MOV containing an injected **PCM audio track**. No new PNG, image, UI asset or owner artwork generated.
- Full Python / JS regression workflows on the changed branch are required before STEP20 gate is passed. Review exact head SHA and all applicable CI checks; do not declare PASS on an in-progress run.

## Boundaries

No new owner image is needed for this reliability work. The strict transparent RGBA input→cache test still transparently **SKIPS** if no owner RGBA PNG exists; skip is not PASS. That is a separate evidence gap, not justification to stop unrelated internal bug fixes.

21 preset registry remains fixed; 2 candidate backends FADE and WIPE, 19 not yet implemented. G3 Premiere host **UNVERIFIED**, 0/21 host certified, no release/merge permitted before the project's mandatory gates. This is not a final Windows acceptance test.
