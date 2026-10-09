# ADR-002 — B06 Technical Spec Freeze (ASTRA)

Status: SPEC_CLOSED_BY_ASTRA on 9 October 2026; G1A still BLOCKED by B02. Planning only, no code, no main merge.

## Decision scope

ASTRA owns technical parser/preflight safety decisions; the user continues to own creative scope choices. B06 is closed at the SPEC level because its fail-closed semantics are specified. Production limits and actual Premiere APIs remain conditional on host evidence at later gates. SPEC_CLOSED does not mean tested, implemented or product ready.

## Technical decisions

1. EDIT_PLAN edit-plan-v2 has eleven V2 root required fields; ANIMATION_PLAN animation-plan-v1 has nine. Unknown root keys and invalid primitive types fail E_JSON_SCHEMA. Never silently strip keys or accept duplicate JSON object keys.
2. Accept all source-documented legacy V2 fields, including semantic_relation, scene locked, stagger_frames, timing_lock, and audit sections render, validation, provenance. Input validation.READY is never trusted as runtime READY. render.output_path remains deprecated read-only metadata, not an FFmpeg export instruction.
3. Unknown nested fields are preserved as input bytes but prevent host mutations: NEEDS_REVIEW with precise JSON pointer, bounded log display, and no silent edits. Explicitly forbidden animation/split IN-OUT fields fail validation even if nested. New allowed fields require versioned contract ADR and compatibility fixtures.
4. Decision.locked is a required JSON boolean. true may proceed subject to all other checks; false remains false and is NEEDS_REVIEW, never automatically flipped to true or rerolled. String false fails the schema.
5. EXACT_WORD needs verified word timestamps; EXACT_CUE only asserts cue boundaries. V2 APPROX_REVIEW and V3 ESTIMATED_FROM_AUDIO remain separate review-only labels; human confirmation must be bound to file/JSON hashes and occurrence. UNRESOLVED and repeat ambiguity block assembly.
6. Use half-open [start_frame,end_frame) integer frames. For nonnegative SRT millisecond values use rational round_half_up once. D < IN+OUT is E_TIME_006; D == IN+OUT satisfies the numeric preflight bound but animation QA must inspect zero-hold visual quality later.
7. Scene gaps and DOUBLE stagger come only from explicit EDIT_PLAN timing/transition_policy, never auto-random. Source missing/unreadable/decode-failed or SHA mismatch stops before Premiere changes. No dummy or inherited media.
8. A production READY transition requires a versioned resource-limit manifest covering JSON bytes, scene/asset/media counts, worker timeout, disk and memory budgets. Unknown, missing, or unapproved caps produce E_CONFIG_LIMITS_UNVERIFIED and no host mutations. Numeric budgets require actual Windows tests and are deliberately not invented in STEP01.
9. Host capability requires Premiere Pro 2024 exact build 24.x, CEP runtime, measured ticks, property/keyframe support and alpha codec proof; unknown blocks assembly. Do not move host proof requirements into spec signoff nor mark host testing PASS.
10. Error UI uses V3 codes where available, retains distinct V2 E_TIME_006/E_PROFILE_010 when needed and logs legacy crosswalk. Do not downgrade errors to warnings; mark failed partial assembly INCOMPLETE and preserve manual edits.
11. Default assembly is CREATE_NEW_SEQUENCE after completed preflight and explicit target confirmation. Read back every host operation; no destructive partial cleanup, media/cache deletion or re-use of unsafe sequence.
12. Validate proposed behavior later with F069–F083 in STEP04/G3–G4 as appropriate. Fixture plans are not executable tests.

## Closing matrix

| Area | STEP01 specification | Later evidence |
| --- | --- | --- |
| Unknown keys / compatibility | ASTRA_SPEC_DECIDED | F069–F072 |
| Locked false | ASTRA_SPEC_DECIDED | F073–F074 |
| SRT labels | ASTRA_SPEC_DECIDED | F075–F077 |
| Resource caps | ASTRA_SPEC_DECIDED_HOST_CAP_DEFERRED | F078–F079 and host measurements |
| Paths, source status, error mapping | ASTRA_SPEC_DECIDED | F080–F082 |
| Host tick safety | ASTRA_SPEC_DECIDED_HOST_PROOF_DEFERRED | F083 host proof |
| B02 speed/direction | OPEN | Explicit scope decision and direction registry review |

## Gate

Historical sources B01 CLOSED; validator spec B06 SPEC_CLOSED_BY_ASTRA; sole remaining STEP01 SPEC blocker B02. G1A BLOCKED, G1B NOT_STARTED, G2 NOT_STARTED, production AC 0/30 and host preset 0/21. After explicit B02 resolution and G1A signoff, STEP02 UI prompt must STOP for approved images and single UI_REFERENCE_FINAL.docx before SOL coding.
