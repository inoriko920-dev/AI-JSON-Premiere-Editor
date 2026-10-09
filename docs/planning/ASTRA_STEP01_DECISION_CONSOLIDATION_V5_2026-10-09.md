# ASTRA STEP01 — Decision Consolidation V5

> **9 Oktober 2026 WIB — planning only. B01 SOURCE DISCOVERY CLOSED. G1A BLOCKED. G2 NOT_STARTED. NO CODING.**

## 1. Substantive gate progress

The original B01 exit criterion was **historical source documents readable and their SHA-256 recorded**, OR an approved replacement specification. In STEP01 V2, seven historical sources were located in the user's private Library, their content examined and their SHA-256 recorded. **B01 historical source discovery is therefore CLOSED for STEP01 planning.** This is **not** authorization to copy the private source DOCX/TXT to a public GitHub repository. The complete derived handoff is in STEP01 V1–V4 DOCX/MD in PR #1; raw-source transfer is a separate, non-blocking privacy question.

This closes one blocker without implying G1A PASS. Remaining specification blockers are **B02** (direction coverage and FAST/SLOW scope) and **B06** (nested schema, locked=false, resource limits, SRT evidence policy). B03 host real validation, B04 approved UI and B05 dependency packaging are later-stage prerequisites, not proof of design completeness.

## 2. Decision policy (compact, source first)

| ID | Contract/decision | Status | Source |
| --- | --- | --- | --- |
| N01 | Schemas remain edit-plan-v2 & animation-plan-v1; docs distinct | SOURCE_SUPPORTED | V2 5.1; V3 4.1 |
| N02 | 11 EDIT_PLAN top-level and 9 ANIMATION_PLAN top-level mandatory fields | SOURCE_SUPPORTED | V2 5.2 & 5.6 |
| N03 | BOTH mode; one decision per (scene,asset) and one preset IN+OUT | SOURCE_SUPPORTED | V2 5.1; V3 4.2 |
| N04 | SINGLE one asset; DOUBLE exactly two independent LEFT/RIGHT assets | SOURCE_SUPPORTED | V2 5.3; V3 4.2 |
| N05 | Frames integer, half-open; 30FPS initial; ms→frames round_half_up once | SOURCE_SUPPORTED | V2 4.4 |
| N06 | IN+OUT must fit object duration; no automatic shortening/Enter-only | SOURCE_SUPPORTED | V2 8.4; V3 7.2 |
| N07 | Strict UTF-8, duplicate-key reject, forbidden split effect fields | SOURCE_SUPPORTED | V2 6.1; V3 4.2 |
| N08 | Missing or unreadable required media/registry blocks Premiere mutation | SOURCE_SUPPORTED | V2 6.1; V3 10 |
| N09 | Source validation.status READY is not real runtime PASS | SOURCE_SUPPORTED | V3 4.1; 11 |
| N10 | CREATE_NEW_SEQUENCE default, preserve manual edits/cache; no destructive retry | SOURCE_SUPPORTED | V3 5.5 and 6.3 |
| N11 | V3 standalone renderer superseded by Premiere sequence and final Premiere export | SOURCE_SUPPORTED | V3 4.1 |
| N12 | No silent creative effect fallback, no random stagger, no unapproved speed variation | SOURCE_SUPPORTED | V3 4.2 and 7.4 |

### 10 decisions: 1 source issue closed, 2 key approvals remain

| ID | Topic | ASTRA recommendation | Status | Notes |
| --- | --- | --- | --- | --- |
| A01 | MVP speed scope | For first host pilot accept only MEDIUM, emit E_ANIM_PRESET for FAST/SLOW until per-preset profiles validated | REQUIRES_USER_APPROVAL | Do not infer from 'lanjutkan' |
| A02 | Direction registry | Adopt 10 source-supported anchor tokens; review proposed 11 keys + alternate tokens; never rewrite JSON direction without migration | REQUIRES_REVIEW | See 21-presets matrix |
| A03 | Unknown fields | Root EDIT_PLAN/ANIMATION_PLAN require V2 fields; reject forbidden animation fields; allow only documented legacy render/validation/provenance; freeze nested allowlist before schema code | ASTRA_PROPOSAL | Do not use example-only shape to reject valid legacy |
| A04 | locked=false | Keep value unchanged; mark NEEDS_REVIEW if false and require a confirmed lock decision before assembly | ASTRA_PROPOSAL | Do not change false to true |
| A05 | SRT evidence alias | APPROX_REVIEW and ESTIMATED_FROM_AUDIO both require review; do not upgrade to EXACT_WORD | SOURCE_DERIVED | When material, block READY until evidence reviewed |
| A06 | Min HOLD equality | D==IN+OUT meets V2 numeric lower bound; visual QA later may warn; D<minimum hard FAIL | SOURCE_DERIVED | No implicit clip extension |
| A07 | Scene gap | Only explicit CUT, EXIT_TO_BG, CONTINUE_LAST from plan; unknown gap blocks preflight | SOURCE_SUPPORTED | V2 section 5.3 |
| A08 | Resource limits | Do not invent production caps; SOL must draft threat-model ADR with testable budgets before enabling helper/host | ASTRA_TECH_REVIEW | B06 pending limit values |
| A09 | Premiere host | Exact 24.x, CEP runtime, native keyframe timebase/alpha require real host probe | SOURCE_SUPPORTED_HOST_PENDING | Host gating stays open |
| A10 | Historical source transfer | Source requirements for STEP01 met by read+SHA inventory, derived contract. Do not copy seven private originals to public repo absent explicit instruction | CLOSED_FOR_SOURCE_DISCOVERY | Availability to SOL as original files is a separate optional transfer decision |

## 3. Source-audited direction map — 21 presets

**Important distinction**: token anchored in a source or V3 example ≠ permitted in a finished registry ≠ backend certified on Premiere.

- **10/21 preset rows have one directly grounded token:** 3 from Master V3 example (`BRUSH.LEFT_TO_RIGHT`, `PAN.FROM_LEFT`, `WIPE.RIGHT_TO_LEFT`), one `FADE.NONE` explicitly in Master V2, and 6 non-directional GENERAL effects from S03 (`POP`, `BLUR`, `SUCCESSION`, `BREATHE`, `NEON`, `STOMP`) conservatively normalized to `NONE`.
- **11/21 preset rows have source descriptions but no unambiguous canonical JSON token.** Their candidate sets below must be reviewed; no silent aliases/movement re-interpretation.
- General engine S03 was authored for random effects, so its random/reroll, Enter-only and auto stagger are **historical/overridden** by V3 locked BOTH mode.
- No preset has demonstrated native or baked playback on actual Premiere 24.x; 0/21 host VERIFIED.

| ID | Preset | Source-grounded token | Basis | Other candidate tokens (NOT approved) |
| --- | --- | --- | --- | --- |
| R01 | BRUSH | LEFT_TO_RIGHT | SAMPLE_V3 | RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP;DIAGONAL |
| R02 | INK | — | PROPOSED_ONLY | CENTER;FROM_LEFT;FROM_RIGHT;FROM_TOP;FROM_BOTTOM |
| R03 | DIGITAL | — | PROPOSED_ONLY | LEFT_TO_RIGHT;RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP;RADIAL |
| R04 | SPRAY_PAINT | — | PROPOSED_ONLY | UNIFORM;LEFT_TO_RIGHT;RIGHT_TO_LEFT;ORIGIN_BURST |
| R05 | SKETCH | — | PROPOSED_ONLY | DIAGONAL_TL_BR;DIAGONAL_BR_TL |
| R06 | GRADIENT | — | PROPOSED_ONLY | LEFT_TO_RIGHT;RIGHT_TO_LEFT;TOP_TO_BOTTOM;BOTTOM_TO_TOP |
| G01 | RISE | — | PROPOSED_ONLY | FROM_BOTTOM;FROM_TOP |
| G02 | PAN | FROM_LEFT | SAMPLE_V3 | FROM_RIGHT;FROM_TOP;FROM_BOTTOM |
| G03 | FADE | NONE | V2_LITERAL | NONE |
| G04 | POP | NONE | ENGINE_NO_DIRECTION | NONE |
| G05 | WIPE | RIGHT_TO_LEFT | SAMPLE_V3 | LEFT_TO_RIGHT;TOP_TO_BOTTOM;BOTTOM_TO_TOP |
| G06 | BLUR | NONE | ENGINE_NO_DIRECTION | NONE |
| G07 | SUCCESSION | NONE | ENGINE_NO_DIRECTION | NONE |
| G08 | BREATHE | NONE | ENGINE_NO_DIRECTION | NONE |
| G09 | BASELINE | — | PROPOSED_ONLY | FROM_BOTTOM;FROM_TOP |
| G10 | DRIFT | — | PROPOSED_ONLY | FROM_LEFT;FROM_RIGHT;FROM_TOP;FROM_BOTTOM;DIAGONAL |
| G11 | TECTONIC | — | PROPOSED_ONLY | HORIZONTAL;VERTICAL |
| G12 | TUMBLE | — | PROPOSED_ONLY | CLOCKWISE;COUNTERCLOCKWISE |
| G13 | NEON | NONE | ENGINE_NO_DIRECTION | NONE |
| G14 | SCRAPBOOK | — | PROPOSED_ONLY | CLOCKWISE;COUNTERCLOCKWISE;FROM_LEFT;FROM_RIGHT |
| G15 | STOMP | NONE | ENGINE_NO_DIRECTION | NONE |

### Direction semantic risks

1. `FROM_LEFT` is an origin for PAN; `LEFT_TO_RIGHT` is a reveal-progress vector for BRUSH/WIPE. Both move visually toward the right in these examples but are **not interchangeable enums**.
2. TECTONIC uses motion axis; TUMBLE and SCRAPBOOK have rotation sign and potentially separate entry side; do not force an unrepresentable two-parameter behavior into one JSON field by guessing.
3. IN and OUT use the **same preset**; OUT's visual behavior is defined by that preset, not a separate GPT direction or effect. For NONE effects, no spatial motion is created.
4. `animation_profile.sha256` placeholders, legacy sheet layouts and demo source hashes are never acceptable for runtime READY. Registry schema describes desired behavior; its implementation/QA is separate.

## 4. Recommended single sign-off to stop the planning loop

**Proposed scope** (not yet approved by user):
- First usable MVP accepts only `speed="MEDIUM"` and the registry's **specifically approved tokens**. FAST/SLOW yield a clear input validation error until their 21-preset durations are calibrated; unsupported directions also fail without silent rewriting.
- Approve this V5 21-row direction matrix as **a review baseline**, not as permission to invent missing canonical names.
- ASTRA may freeze strict root-field and forbidden-field policy but must preserve documented legacy metadata (`render`, `validation`, `provenance`); unknown nested fields policy is an ADR reviewed before schema implementation.
- Scope of finished product remains all 21 presets BOTH, and final confidence only after host-specific evidence—not a declaration that 21/21 already work.

**Only after approval + B02/B06 closure:** mark G1A SPEC PASS, proceed to STEP02 UI prompt, then **STOP** for all final images + explicit approval + single UI_REFERENCE_FINAL.docx stored in GitHub. SOL cannot code before that. No merge main / build / release in STEP01.

## 5. Evidence and handoff

- Historical source audit and SHA in `ASTRA_STEP01_SOURCE_RECOVERY_AND_CONTRACT_V2_2026-10-09.md`; all seven raw sources remain private.
- V3 DEMO_001 static audit: 18/18 **example-only** checks, 68 planned fixtures; no executable production tests.
- This V5 is a **decision proposal**, not a software implementation, QA/P0 proof or gate PASS. For further work read AGENTS.md and Master V3 first.
