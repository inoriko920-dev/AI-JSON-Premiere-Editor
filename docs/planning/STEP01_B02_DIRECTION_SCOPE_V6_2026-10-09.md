# ASTRA STEP01 — B02 Final Technical Direction Proposal V6

> **9 Oktober 2026 WIB · review required · planning only**
> **G1A BLOCKED — B02 awaiting explicit scope approval and 21-direction registry sign-off · G2 NOT_STARTED · NO CODING**

## 1. What this resolves without guessing

ASTRA proposes a complete, explicit, stable JSON direction-policy table for 21 BOTH animation presets, with source provenance and failure rules. It does **not** assert Canva-original timing, Premiere 24.x support, native/alpha backend certification, or user approval.

Master V2 §5.5–5.6 explicitly prioritizes calibrated `speed=MEDIUM` for MVP; FAST/SLOW only become usable when their **per-preset** IN/OUT frame pairs have been calibrated and tested. Master V3 §7.2 and §7.3 keep the 21-preset long-term scope and strict `allowed_directions` per registry. The proposed first milestone does not delete FAST/SLOW from schema; it blocks their **execution** until certified without guessing a speed multiplier.

**Evidence precision correction:** of the 21 rows, only **4 exact (preset, direction) tokens** are literally in V2/V3: `BRUSH.LEFT_TO_RIGHT`, `PAN.FROM_LEFT`, `WIPE.RIGHT_TO_LEFT` (V3 DEMO_001), and `FADE.NONE` (Master V2 §5.6). For another **6 non-spatial effects**, `NONE` is a conservative normalization derived from Engine S03 descriptions, **not** a literal approved JSON example. The last **11 rows** have source-supported movement types but candidate enum names need review. This replaces the misleading shorthand '10 source-verified tokens' in prior notes.

## 2. Semantics must not collapse

| Field classification | Meaning of `direction` | Examples | Preflight rule |
| --- | --- | --- | --- |
| MASK_VECTOR | Direction in which visible mask coverage progresses, image stays fixed | BRUSH, WIPE, GRADIENT | `LEFT_TO_RIGHT` differs from `FROM_LEFT` |
| MASK_ORIGIN | Where organic reveal begins, e.g. center or edge | INK | `CENTER` is origin, not movement |
| MASK_PATTERN_MODE | Spray pattern (uniform/sweep/burst), not an independent travel vector | SPRAY_PAINT | enum exact, no blanket aliases |
| TRANSFORM_ORIGIN | Side from which the entire asset approaches base position | PAN, RISE, DRIFT, BASELINE | `FROM_LEFT` is origin; image moves right |
| OSCILLATION_AXIS | Main shake axis (horizontal or vertical), not origin | TECTONIC | no rotation/translation direction alias |
| ROTATION_SIGN | Clockwise vs counterclockwise tilt/rotation | TUMBLE, SCRAPBOOK | entry offset fixed by registry; never random new creative decision |
| NONE | Effect has no directional degree of freedom | FADE, POP, BLUR etc. | only exact `NONE`, no random direction |

## 3. Proposed exact allowed_directions for review

**These are candidate serialized strings, not certified implementation values.** Source-defined semantic motion applies; no random direction substitution when token is absent or disallowed.

| ID | Preset | Direction type | Proposed allowed JSON values | Evidence | MEDIUM IN/OUT reference (frames) |
| --- | --- | --- | --- | --- | --- |
| R01 | BRUSH | MASK_VECTOR | `LEFT_TO_RIGHT;RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP;DIAGONAL_TL_BR;DIAGONAL_BR_TL` | V3_EXACT_LITERAL | 39/9 |
| R02 | INK | MASK_ORIGIN | `CENTER;FROM_LEFT;FROM_RIGHT;FROM_TOP;FROM_BOTTOM` | PROPOSAL_SOURCE_SEMANTICS | 40/9 |
| R03 | DIGITAL | MASK_VECTOR_OR_RADIAL | `LEFT_TO_RIGHT;RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP;RADIAL` | PROPOSAL_SOURCE_SEMANTICS | 24/7 |
| R04 | SPRAY_PAINT | MASK_PATTERN_MODE | `UNIFORM;SWEEP_LEFT_TO_RIGHT;SWEEP_RIGHT_TO_LEFT;ORIGIN_BURST` | PROPOSAL_SOURCE_SEMANTICS | 42/9 |
| R05 | SKETCH | MASK_DIAGONAL | `DIAGONAL_TL_BR;DIAGONAL_BR_TL` | PROPOSAL_SOURCE_SEMANTICS | 42/10 |
| R06 | GRADIENT | MASK_VECTOR_OR_RADIAL | `LEFT_TO_RIGHT;RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP;RADIAL` | PROPOSAL_SOURCE_SEMANTICS | 33/8 |
| G01 | RISE | TRANSFORM_ORIGIN | `FROM_BOTTOM;FROM_TOP` | PROPOSAL_SOURCE_SEMANTICS | 21/8 |
| G02 | PAN | TRANSFORM_ORIGIN | `FROM_LEFT;FROM_RIGHT;FROM_TOP;FROM_BOTTOM` | V3_EXACT_LITERAL | 21/8 |
| G03 | FADE | NONE | `NONE` | V2_EXACT_LITERAL | 15/7 |
| G04 | POP | NONE | `NONE` | INFERRED_NONE_FROM_ENGINE | 16/7 |
| G05 | WIPE | MASK_VECTOR | `LEFT_TO_RIGHT;RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP` | V3_EXACT_LITERAL | 21/8 |
| G06 | BLUR | NONE | `NONE` | INFERRED_NONE_FROM_ENGINE | 21/8 |
| G07 | SUCCESSION | NONE | `NONE` | INFERRED_NONE_FROM_ENGINE | 25/9 |
| G08 | BREATHE | NONE | `NONE` | INFERRED_NONE_FROM_ENGINE | 30/9 |
| G09 | BASELINE | TRANSFORM_ORIGIN | `FROM_BOTTOM;FROM_TOP` | PROPOSAL_SOURCE_SEMANTICS | 14/7 |
| G10 | DRIFT | TRANSFORM_ORIGIN | `FROM_LEFT;FROM_RIGHT;FROM_TOP;FROM_BOTTOM;DIAGONAL_TL_BR;DIAGONAL_BR_TL` | PROPOSAL_SOURCE_SEMANTICS | 33/9 |
| G11 | TECTONIC | OSCILLATION_AXIS | `HORIZONTAL;VERTICAL` | PROPOSAL_SOURCE_SEMANTICS | 22/8 |
| G12 | TUMBLE | ROTATION_SIGN | `CLOCKWISE;COUNTERCLOCKWISE` | PROPOSAL_SOURCE_SEMANTICS | 24/9 |
| G13 | NEON | NONE | `NONE` | INFERRED_NONE_FROM_ENGINE | 20/7 |
| G14 | SCRAPBOOK | ROTATION_SIGN | `CLOCKWISE;COUNTERCLOCKWISE` | PROPOSAL_SOURCE_SEMANTICS | 22/9 |
| G15 | STOMP | NONE | `NONE` | INFERRED_NONE_FROM_ENGINE | 17/7 |

## 4. Policy on unresolved edge types

1. BRUSH, INK, SKETCH, SPRAY_PAINT and other reveal effects need real alpha mask tests. They cannot be marked backend `VERIFIED` merely from direction enums.
2. TECTONIC `HORIZONTAL` and `VERTICAL` encode **axis**. TUMBLE and SCRAPBOOK encode **rotation sign**. For the source's optional entry side, the preset registry must freeze a single deterministic motion mapping per token (not choose a random second direction); if that representation is insufficient, raise a separate versioned schema ADR rather than invent a second GPT direction field.
3. Source S03 has legacy random-mode, Enter-only/Exit-only and 80–220 ms auto-stagger instructions. These are explicitly overridden by Master V3's one GPT preset, global `BOTH`, and start frames from EDIT_PLAN. Do not re-introduce randomization.
4. For direction unsupported by registry or an uncalibrated speed, respond `E_ANIM_PRESET`; never fall back to FADE, change direction, silently scale duration, alter scene cut, or rewrite JSON. For preset without verified native/prerender backend, respond `E_FX_BACKEND` even if direction itself parses correctly.
5. Registry must separate `json_preset_key`, `direction_semantics`, `direction_allowed`, `medium_in_frames_ref`, `medium_out_frames_ref`, `fast/slow status`, `native_status`, `prerender_status`, and `tested_both`. Until host proof, backend fields remain `UNVERIFIED`.

## 5. A single approval to close STEP01, not 21 user-level choices

Recommended scope: **initial implementation and host pilot with `MEDIUM` only, without removing FAST/SLOW from product requirements; keep them disabled until the per-preset duration matrix is approved/tested.** Accept this **21-row proposed direction policy as the planning baseline for SOL**, with per-effect rendering/behavior still subject to actual 24.x host validation. SOL must not replace these literal tokens silently.

**Request user explicit approval of BOTH pieces in one sentence:** `Setuju pilot MEDIUM dulu dan matriks arah 21 preset V6 sebagai baseline perencanaan; FAST/SLOW menyusul setelah kalibrasi.`

Do **not** treat a generic `lanjutkan` as that approval. Pending approval, **B02 remains BLOCKED** and so does G1A. After approval, ASTRA may record decision in a separate gate closure report, then STEP02 UI prompt and **STOP** until images and 1 DOCX UI final approved and committed. Coding SOL only after G2.

## 6. Verification plan (future, not executed)

Tests: exact direction enum per preset; wrong origin/vector alias; NONE-only effect with movement direction; unsupported FAST/SLOW; min clip duration; correct different direction on two assets; frontend inspector displays typed direction; host native keyframe/prerender alpha and later 21/21 BOTH gallery. Existing 83 fixtures remain plans; add F084–F091 for directional semantics.

**Source priority:** user instructions > Master V3 architecture and locked BOTH > Master V2 two-JSON/duration spec > S03 engine visual semantics > proposed registry names. All 21 MEDIUM frame-pairs are source *reference*, not Canva-original measured values or Premiere pass.
