# STEP05 sequence/timebase implementation evidence

## Coding files
- `host/sequence_adapter.jsx`: Premiere ExtendScript ES3 candidate (not loaded by P0 CEP). Read-only host/sequence inspector and guarded create-new-only sequence method.
- `panel/sequence_probe.js`: strict CEP parser for `S5|1|OBSERVED` protocol; decimal `timebase` remains string even above JS safe integer.
- `core/host_ticks.py`: arbitrary-precision Python ticks planner from integer frame.
- `tests/sequence_adapter.test.cjs`, `tests/sequence_probe.test.cjs`, `tests/test_core_host_ticks.py`: mocked host, response parsing, failure preservation, exact timestamps and collision/duplicate protection.

## API basis
- Adobe community-supported Premiere ExtendScript scripting guide: https://ppro-scripting.docsforadobe.dev/general/project/ (`Project.createNewSequence(name, id)`), https://ppro-scripting.docsforadobe.dev/sequence/sequence/ (`Sequence.timebase` and track collections).
- UXP APIs from Premiere 25.6+ do not replace the specifically requested CEP/ExtendScript 2024 v24.x target.

## Gate limitations
The host-creation method remains disconnected from CEP main panel, and the CI mocks are not real Premiere interactions. Host G3, 21 animation backend certifications and native media import/readback remain PENDING/UNVERIFIED. No production installer/MP4 or change to `main`.
