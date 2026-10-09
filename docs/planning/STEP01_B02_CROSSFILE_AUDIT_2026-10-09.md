# ASTRA STEP01 — B02 cross-file consistency audit

**9 Oktober 2026 WIB · ASTRA planning-only audit · verification scope: static GitHub source files, not application/runtime tests**

## Input evidence (Draft PR #1 source at b2eea586)

- `docs/planning/STEP01_B02_PROPOSED_21_DIRECTION_REGISTRY.csv` — V6 candidate enum map (21 rows).
- `docs/planning/PRESET_MATRIX.csv` — baseline preset keys, medium IN/OUT frames, backend candidate and UNVERIFIED statuses (21 rows).
- `docs/source/MASTER_PLAN_V3_TRANSCRIPT.md` — V3's inline sample for BRUSH/PAN/WIPE and required BOTH and host proof.
- `docs/planning/STEP01_SOURCE_CONFLICT_MATRIX.csv` — previously stale B06 statuses corrected below.
- `docs/planning/STEP01_B02_DIRECTION_SCOPE_V6_2026-10-09.md` — definition table now includes MASK_VECTOR_OR_RADIAL and MASK_DIAGONAL.

## Static audit outcome

| Criterion | Result |
| --- | --- |
| V6 direction rows | 21/21 present |
| PRESET_MATRIX baseline rows | 21/21 present |
| Unique catalog IDs / preset keys | PASS, no duplicates |
| ID and preset key match | 21/21 PASS |
| MEDIUM IN frame pairs match source baseline | 21/21 PASS |
| MEDIUM OUT frame pairs match source baseline | 21/21 PASS |
| Proposed allowed direction tokens nonempty | 21/21 PASS |
| Anchors appear inside same preset proposed allowlist | 4/4 PASS |
| Inline Master V3 sample lists BRUSH / PAN / WIPE literal tokens | Source confirmation PASS |
| Direction semantics fully explained in V6 table | 9 classes described after fix |
| Baseline native_status and prerender_status | UNVERIFIED for every preset, 0/21 certified |

## Evidence grading (not approval)

- 3 V3 source-literal pairs: `BRUSH.LEFT_TO_RIGHT`, `PAN.FROM_LEFT`, `WIPE.RIGHT_TO_LEFT`.
- 1 V2 source-literal pair: `FADE.NONE` (V2 §5.6).
- 6 `NONE` tokens inferred from non-directional Engine S03 descriptions and still need user signoff.
- 11 rows with proposed enum names based on effects semantics, **not** exact V2/V3 literals.
- Production enum allowlists in V6 are still **PROPOSED**, including non-anchor tokens for otherwise source-anchored presets; these remain unapproved.

## Reconciled legacy conflicts

- `C07` and `C15` are **OPEN_B02_USER_REVIEW**, not B06; exact direction policy is part of the remaining B02 decision.
- `C10` (SRT confidence alias) and `C13` (nested unknown field policy) are **SPEC_CLOSED_BY_ADR002**, not implemented/tested.
- `C12` (layout reference) is **SOURCE_PROFILE_DOCUMENTED_HOST_PROOF_PENDING**; layout reference exists, but golden visual Premiere check is still due at host gates.
- `C09` references the 21 uncalibrated MEDIUM values; it is **HOST_CALIBRATION_PENDING**, not an outstanding user-level choice to block G1A. Not an assertion that durations match original Canva.

## Gate integrity

Cross-file audit is documentation validation; no executable schema/test code, Premiere host 24.x, alpha, native keyframes or assembled media were tested. **G1A remains BLOCKED by B02 explicit user approval** of MEDIUM-first pilot and V6 candidate 21-direction policy. G1B and G2 NOT_STARTED; no coding or main merge. After user approves planning baseline, host proof still required for all 21 effects.
