# SOL STEP04 — CEP picker → Python validation → draft compiler (automated CI)

**Source revision tested:** `948b22c8697fedc14f6003be996e891d9f0f93d5`  
**GitHub Actions:** [#37973410632](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37973410632), SUCCESS for Windows and Ubuntu. No Adobe Premiere runtime is available in the CI runner.

## Verified scope

- **Panel CEP:** 3 native Adobe picker buttons for EDIT_PLAN.json, ANIMATION_PLAN.json and media root. The P0 version-check UI remains. Offline validation is a separate action; `btn-preflight` and `btn-assemble` remain disabled.
- **Local Node → Python bridge:** explicit Python interpreter path via AIJSON_P0_PYTHON_EXE, fixed script `helper/validate_request.py`, `-I -B` isolation, `execFile` with shell:false, fixed flags and bounded timeout/stdout. Host callbacks don't authorize assembly.
- **Validation:** requires both JSON and selected media root; parses with duplicate-key rejection; checks matching pairs/BOTH/slots/half-open frames; audits media SHA/root paths/SRT; strict non-READY protocol. When JSON contract is invalid, media audit is skipped.
- **Deterministic draft:** scene/asset frame and V2/V3 track placement reference, stable operation digest. The example has 2 scenes, 3 image instances and 330 frames: A001 V2 [0,150), A002 V2 [150,330), A003 V3 [192,330). No invented layout transform, host tick, alpha phase or backend. **DRAFT_NOT_EXECUTABLE**, not a Premiere timeline operation.
- **Safety:** no import, editing, media writes, MP4 render, registry, automatic download or main merge. Native dialogs are user-triggered and file paths remain hidden from UI summaries.
- **Unsigned test ZIP:** 17 runtime files + readme + SHA manifest = 19 files, 18 content hashes; Windows ZIP inspector, staging consent and 8 malicious archive test variants PASS in temp runner dir.

| Runner | JavaScript | Python | Archive tests |
|---|---|---|---|
| Windows | **44/44 PASS**, including one real Node → Python process test | **65/65 PASS** | staging/18 checksums/8 negative cases PASS |
| Ubuntu | **42 PASS**, 2 Windows-only SKIPPED | **65/65 PASS** | deterministic bundle PASS |

Tested source has actual code in `panel/validation_ui.js`, `panel/validation_bridge.js`, `helper/validate_request.py`, `core/validate_cli.py`, `core/media.py`, `core/draft_compiler.py`; CI result is **not** a plugin-in-Premiere success certificate.

## Deferred final tests and remaining coding

- Adobe Premiere Pro 2024 24.x on Windows 11 must eventually verify CEP picker behavior, Node runtime, docking, true host version/bridge, import, sequence creation, clip readback, native/prerender animation, linked media and exported MP4. **G3 BLOCKED_HOST / UNVERIFIED** until then.
- Still not implemented: final host mutation adapter, approved layout/crop transforms, full SRT review automation, native/pre-render FX registry implementation (21/21), actual FFprobe and media decoder validation, end-user bundled interpreter and signing/packaging, edit-safe sequence assembly. No AC host verified.
- G1A SPEC PASS and G2 approved final UI PASS; G1B structural validator unit tests PASS for covered fixtures, but entire production preflight/G1B+host certification incomplete. Do not mark application finished.

Owner explicitly requested completing all feasible coding and CI before owner's manual Premiere trial at the very end. PR #4 remains Draft and `main` untouched.
