# SOL STEP04 — Offline two-JSON contract validator (working code)

**Owner update 10 Oct 2026:** continue implementation/UI/integration/automated bugfixes without asking for real Windows/Premiere manual testing at each stage. Perform owner's manual test at end. This overrides the *schedule* of G3 gate testing; it **does not** imply G3 PASS, authorize merge, or relax safety/certification requirements.

STEP04 branch `sol/step04-json-validator-20261010` continues from STEP03 current code, avoiding redesigning the previously approved 12 UI images.

## Added
- `core/contracts.py`: strict duplicate-key and nonfinite-value JSON parser; two plan roots, project/revision, one decision per scene/asset pair, BOTH, SINGLE/DOUBLE, integer frame constraints, known 21-preset direction/speed checks; unknown nested/locked=false require review.
- `core/direction_registry.json`: candidate 21 preset direction enums, **not** host-verified FX backends.
- `core/validate_cli.py`: read-only local diagnostics with explicit developer input-byte cap and no host mutations. Status is NEVER READY: exit 2 invalid or 3 needs review.
- `tests/test_core_contracts.py`: synthetic positive/negative demo contract tests.
- `.github/workflows/step04-core.yml`: Windows and Linux unit CI.

## Still required before runtime READY
Actual input media reads/hash and SRT checks; resource caps based on Windows evidence; approved layout profile and exact animation registry hash/duration/calibration; Premiere 24.x tested host capabilities/alpha; deterministic compiler, media import, timeline create and readback; all 21 effects. These will be coded and tested as far as possible before user host trial.

**G3 BLOCKED_HOST** pending final manual Premiere phase. G1B executable tests in progress; no Premiere host AC or effects certified. No main merge/release, no false app completion claims.
