# STEP06 media import candidate / CI evidence

## Source and Adobe API basis
- `core/import_snapshot.py`: hash-pinned read-only snapshot and freshness recheck; *not* an executable/import authorization token.
- `host/media_import_adapter.jsx`: candidate ECMAScript 3 adapter, NOT currently loaded by CEP. Uses APIs documented at https://ppro-scripting.docsforadobe.dev/general/project/ (importFiles), https://ppro-scripting.docsforadobe.dev/item/projectitem/ (createBin, getMediaPath, findItemsMatchingMediaPath).
- `core/validate_cli.py` + CEP bridge: expose only sanitized counts and digest. Real media paths stay local to Python/host and never forwarded as UI report.
- `tests/media_import_adapter.test.cjs`: rejects unsupported host, invalid auth, duplicate bin/paths and prior project media, missing/stale files, failed imports, partial post-import readback. Preserves existing user's bin/items on failure.
- `tests/test_core_import_snapshot.py`: hashes bytes, forbids missing hashes, symlink escapes and traversal, requires all sources, rejects changed files, aliases and missing media.

## CI evidence
[Run #37978073723 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37978073723):
- Windows: **77/77 Node JS PASS**, **105/105 Python PASS**; dedicated **13/13** JSX importer and **14/14** snapshot tests PASS at that source revision.
- Ubuntu: **75 Node PASS + 2 Windows-only SKIP**, **105 Python tests** without FAIL, optional FFprobe real-binary smoke may SKIP.
- Windows PowerShell pack inspection, staging only after explicit consent, 21 allowed files/20 hashes, eight deliberately malicious archive cases REJECTED. Host mutator script excluded from runtime ZIP and CSXS manifest.

## Limitations
- This is **no host certification**. A forged authorization object on an exposed host method would be unsafe, so the method must remain disconnected until a separate reviewed dispatcher binds immutable hash/owner/host capability proofs. Existing CEP runtime only performs read-only validation.
- Size/mtime rechecks in ES3 cannot replace Python SHA verification; source changes between hash check and host import are a TOCTOU risk requiring final same-source proof and host validation.
- No bin/project import was performed in Adobe Premiere Pro. No final sequence, 21 FX or MP4 exists. G3 remains unverified and the owner should not test now, per coding-first instruction.
