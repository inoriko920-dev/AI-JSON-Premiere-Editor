# STEP12 simulated dispatcher — tested implementation / evidence

**New source:** `core/transaction_dispatcher.py` and `tests/test_core_transaction_dispatcher.py`; [CI source SHA 87bae6b7](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/commit/87bae6b79b69c286f9834a7ccf48e0c2dbb0cc88).
[Windows and Ubuntu GitHub Actions #37990675282 SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37990675282).

### Coverage
- Caller must present exactly original candidate and next journal index; stale/altered plan rejected pre-action.
- Journal INTENT written and fsynced before any simulation. A simulated crash leaves status UNKNOWN_AFTER_INTENT and blocks auto-retry.
- Mismatch writes INCOMPLETE; subsequent operations blocked pending operator review. Recorded matching results are labeled SIMULATED, not Premieres's actual readback.
- External host callbacks refused: the test-only dispatcher only accepts `SimulatedReadback` exact class. No shell, file/video modifications, interactive CEP actions or Adobe instance.
- Dedicated 12/12 test PASS on both platforms; full Python 204 tests with 2 optional skips, and JavaScript Windows 90 PASS / Ubuntu 88 PASS + 2 Windows-only skips.
- P0 CEP live host still `host/step03.jsx` only. No real host write route.

### Safety boundary
This is an intermediate piece, **not** a production dispatcher. Hash-chain integrity is not host authorization. An external process could mutate files after Python verification; real Premiere trim and readback still require separate proof. G3 BLOCKED_HOST and no effect or acceptance evidence.
