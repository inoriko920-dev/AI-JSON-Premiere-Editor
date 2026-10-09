# STEP11 audit journal evidence — developer/offline tests

Implementation files:
- `core/transaction_journal.py`: create-new, fsync append-only transaction intent/result, hash-chain replay, strict event grammar, write lease and no-automatic-retry recovery.
- `tests/test_core_transaction_journal.py`: real temporary-folder unit tests on both Windows and Linux.
- `.github/workflows/step11-transaction-journal.yml`: test journal and full existing JavaScript/CEP and Python core regressions on both OS.

**CI:** [Initial Windows/Linux run 37989577771 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37989577771) at commit `b7fd725a98fc0e61872d769533b10a5305250ba1`: 17 STEP11 journal unit tests passed on both; Windows 190 Python tests + 90 Node tests, Linux 190 Python tests + 88 Node passed and 2 skipped. Follow-up `ec5c779b` adds recovery fingerprint verification and two more tests; its CI must be independently checked before calling final SHA PASS.

This is strictly offline code evidence: GitHub CI cannot inspect native Premiere Pro 2024 after timeline mutation. The journal does not yet wrap STEP07 ExtendScript host invocations, does not create a Premiere project, and cannot certify actual readback or a final MP4.

State meanings:
- `OPEN_NOT_AUTHORIZED`: journal exists, may have recorded matching results; still no Adobe edit permission.
- `UNKNOWN_AFTER_INTENT`: last action may or may not have been performed; **never retry automatically**.
- `INCOMPLETE_MANUAL_REVIEW`: failed/partial operation; preserve all existing and partial managed media/sequence.
- `CLOSED_RECORDED_UNVERIFIED`: external caller recorded all results; still not host-certified.
- `NEXT_STEP_AWAITING_HOST_APPROVAL`: candidate matches original job; never an executable token.

Security limits: JSONL SHA is unkeyed (not authentication), file lock is a cooperative lease (not a distributed transaction), host/process crash across I/O and calls still needs final dispatcher integration and runtime evidence. G3 remains unverified.
