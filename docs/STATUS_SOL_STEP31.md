# SOL STEP31 — Pin Owner PNG Descriptor and Private Staged Source During FFmpeg Validation

Date: 10 October 2026 WIB. Scope: **existing** FADE/WIPE alpha MOV render cache input integrity. Approved 21-animation preset registry, UI, animation timings, JSON contracts and Premiere Pro 2024 hybrid architecture are unchanged. No new visual asset or PNG is generated.

## Two real input integrity gaps

1. The existing `_copy_pinned` source copy used `source.stat()`, then `source.open("rb")`, and compared final size/mtime/inode, but did not verify the identity of the **opened FD** at both ends or the source ctime. A same-size, same-mtime file replacement or rename/substitute during the copy could potentially bypass filename-only checks even when its bytes were identical. The function now opens the source with a read-only descriptor (`O_NOFOLLOW` where supported) and compares device/inode, file size, nanosecond mtime and ctime for initial source path, opened FD, FD after reading, and final source path. Only regular files are permitted. The exclusive `O_EXCL` private target copy and source SHA-256 check are preserved; original owner files are never written.

2. Even with a correct initial owner PNG snapshot, the private staged `input.png` could be modified or replaced while FFmpeg renders and verifies the derived MOV. The render worker now hashes the private staged source with the existing stable-file SHA/inode helper **before starting FFmpeg** and checks the same SHA + inode again after FFprobe and the sampled alpha-pixel checker, before caching the result. If staged bytes differ or the inode is substituted, it fails closed with `E_FX_SOURCE_CHANGED`; the MOV is **not published**. STEP30's staged MOV and STEP26's published MOV identity checks remain active.

## Regression tests

Three focused cases added to `tests/test_core_fx_cache_worker.py`, using the **pre-existing short byte-header mock**, no new PNG image:
- fstat reports a swapped original source inode mid-copy while byte size/content/mtime remain unchanged → source copy rejected and no FFmpeg command issued;
- alpha checker changes the private staged PNG during validation → no cache publication;
- alpha checker swaps the private staged PNG for a same-byte replacement with a different inode → no cache publication.

All cases must preserve the original input fixture and remove only the unique private workdir. Tests do not certify actual Adobe host import, entire image alpha or Canva motion. `.github/workflows/step31-source-copy-integrity.yml` runs focused and complete Python + JS regressions on Windows/Linux. Existing STEP19 live FFmpeg/QTRLE checks are required separately on final SHA.

## Gate limits and known blockers

This is a **bounded offline integrity check**, not a guarantee against arbitrary writers after the final check, or an Adobe G3 approval. Existing source snapshot rehash and cache restart verification are still required at their respective steps. `can_assemble=false`, `host_verified=false`, 0/21 Premiere host-certified, and 19/21 agreed motion preset render backends remain unimplemented.

Strict owner-original transparent RGBA PNG-to-cache integration test may still SKIP when owner file is absent; SKIP is not PASS. Never generate owner images; never edit user media; never merge to main, tag or release without mandatory project gates and authorization.

## Next STEP32

Continue closed-scope input/cache/scene integrity stabilization or implement remaining animation behavior **only** with locked calibrated preset parameters. Do not invent motion distances/speeds or add UI.

**Final STEP31 offline gate requires all applicable CI on one latest SHA, both Windows and Linux.**
