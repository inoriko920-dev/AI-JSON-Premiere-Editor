# SOL STEP29 — Stable owner-media file identity and post-FFprobe source recheck

Date: 10 October 2026 (WIB). Scope locked to **existing** STEP06 source snapshot + STEP28 source/track/cache read-only preflight. No UI, animation preset, motion parameter, user PNG, Premiere project, merge or release changed.

## Two concrete time-of-check/time-of-use defects

1. STEP06's `prepare_media_snapshot` and `recheck_media_snapshot` formerly did `path.stat()` → `_bounded_hash(path)` on a **separately opened** handle → `path.stat()`. They compared digest, size and mtime, but did not pin the opened file's inode/device and ctime against the resolved file path. An external writer might replace a file during hashing while retaining size/mtime; pathname-level metadata checks alone were insufficient to detect all file substitutions.

   Added `_stable_media_hash` in `core/import_snapshot.py`: read a bounded regular file from **one read-only descriptor**, use `os.O_NOFOLLOW` where supported and `O_BINARY` on Windows where supported, and compare `st_dev`, `st_ino`, size, nanosecond mtime and ctime from the initial pathname, opened FD, FD after read, and final pathname. File or metadata identity changes fail closed. The already agreed `verified-media-snapshot-v1` output schema, existing checksum convention and source read permissions are unchanged. No owner file writes.

2. STEP28's `inspect_media_cache_track` verified the source snapshot **before** a potentially slow FFprobe cache audit but emitted a positive offline diagnostic without rechecking sources when the MOV audit finished. Added **a second full source-inventory rehash** immediately after `verify_cache_for_candidate` and before returning; if any mandatory MP4, SRT, PNG or audio source changes during this interval, result is rejected as `E_FX_MEDIA_SNAPSHOT_STALE`. Result records `source_recheck_after_cache_audit=true`, but crucially still `source_recheck_at_host_transaction=false`, `host_verified=false`, `can_assemble=false`. No future real Premiere authorization is implied.

## Automated regression

- `tests/test_core_import_snapshot.py`: new checks simulate an inode substitution during the first and repeat hashing via patched `fstat`, using existing WAV test source and generating **no new UI/image file**. Initial snapshot must refuse with `E_MEDIA_CHANGED_DURING_SNAPSHOT`; recheck must return false.
- `tests/test_core_fx_media_cache_track_preflight.py`: new tests simulate source changes between first and second recheck (including during the MOV audit) and verify no success report escapes. Existing success test requires two independent source rechecks.
- `.github/workflows/step29-media-toctou.yml`: targeted source-integrity suite, full Python suite and full Node/CEP tests on both Windows and Ubuntu. Real STEP19 FFmpeg native MOV/cache tests remain independent required checks.

## Non-claims / gates

A local writer could modify sources **after** even the second recheck. This is an offline fail-closed preflight only, never Premiere host approval. Explicit real G3 Premiere Pro 2024 host evidence is still **NOT_VERIFIED**; 19 of 21 agreed animation presets remain without their render backends and 0 of 21 host-certified. Source transparent-RGBA original PNG strict input-to-cache coverage remains SKIPPED without a suitable existing owner PNG, not PASS. No image is generated, and no UI changes, manual project writes, main merge, tag or release are authorized.

## Next STEP30

Continue stabilizing existing approved features or real reference-grounded implementation while 19 preset motion formulas and real Adobe APIs remain uncertified; never guess visual parameters, generate owner assets, or claim host G3 PASS. A final-owner Windows test happens only after all feasible automated coding/CI work finishes.

**CI:** gate evidence must use exact final SHA with both Windows/Linux results, and all applicable workflows; report any skips honestly.
