# SOL STEP11 — Durable transaction journal and crash recovery (10 October 2026)

**Current rule:** User wants all available coding, integration, bugfix and automated testing completed before the final hands-on Premiere Pro 2024 test on Windows 11. Do not request a manual Premiere trial yet. **G3 BLOCKED_HOST / NOT_VERIFIED** remains truthful; it does not stop offline development.

## Code delivered

- `core/transaction_journal.py`: an append-only UTF-8 JSONL journal under an explicitly existing output folder. A new job uses exclusive creation, no replacing old journal. Each record has an unkeyed SHA-256 integrity chain and sequence number; `fsync()` is used on every append. Records carry only job ID, operation hash, plan digest, sanitized result code and state, never user-media paths, filenames, credential or full source JSON.
- `TransactionJournal.start()`: checks that the input is a **non-executable** STEP07 or STEP10 candidate; hashes every operation to bind intent to the original plan but **does not** elevate candidate to READY.
- `record_intent(index)`: persists an intent BEFORE a later host dispatcher is permitted to call Premiere; no state transition permits missing-operation skip or implicit retry.
- `record_result(index, READBACK_MATCHED/INCOMPLETE, code)`: records an externally reported readback result. It is not host proof by itself. If incomplete, job remains manual-review only.
- `read_journal()`: fully replays and verifies the chain; rejects truncated/tampered JSONL, duplicate JSON object keys and invalid event transitions, no automatic repair.
- `inspect_resume()`: compares the resumed candidate and every operation hash against the original journal, refuses changed sources/plan, unresolved pending intent, incomplete job and completed job. Returned `next_index` is **not** authorization to execute.
- An exclusive `.lock` prevents two compliant writers from appending simultaneously; orphaned lock after crash requires deliberate review rather than auto-removal. Journal is never deleted after partial host operations.
- `tests/test_core_transaction_journal.py`: tests real disk writes, replay after restart, crash-intent UNKNOWN, incomplete job, invalid candidate, corrupt hash, truncated journal, duplicate keys, stale lock and plan fingerprint changes.
- `.github/workflows/step11-transaction-journal.yml`: Windows and Linux tests of STEP11 plus full prior JS/Python regression suite.

## Security & correctness boundary

This is an **offline audit foundation only**. The existing panel still loads **read-only** `host/step03.jsx`; the STEP07 host mutator and STEP11 journal are **not yet connected by an authenticated, safely authorized dispatcher**. A forged status string or SHA chain is not enough to allow a host write. SHA chain only detects corruption and is not a cryptographic signature. The future dispatcher must fsync INTENT prior to Adobe invocation, verify actual host readback before logging RESULT, and never resume UNKNOWN or INCOMPLETE without owner review. This is a developer module, **not** a completed editing transaction.

## Next work

Implement a safe dispatcher/protocol linking actual imported source IDs, approved STEP10 derived-background cache, managed sequence identity, per-clip host readback and transaction events; prohibit double execution after a browser reload/crash. Then layout/crop and 21 BOTH preset animation backend, FFmpeg alpha and final packaging/CI. Do not generate or modify approved UI PNGs.

**G1A/G2 PASS, G3 BLOCKED_HOST, 0/30 host cases and 0/21 effects host-certified.** No main merge, no release, no installer; user does not need to test on PC yet.
