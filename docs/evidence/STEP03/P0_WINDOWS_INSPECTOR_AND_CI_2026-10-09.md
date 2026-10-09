# STEP03 P0 — Safe Windows inspector and pilot artifact verification

**Date:** 2026-10-09 WIB  
**Code revision tested:** `7345bc1dfe1b92c0b9629a7e586b67f310063665`  
**GitHub Actions:** [Push #37962129971](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37962129971) — Windows+Ubuntu SUCCESS; associated PR run #37962135985 also successful.  
**Artifact id:** `11631521486` / `AI_JSON_Premiere_STEP03_P0_TEST_ONLY_Windows` (time-limited GitHub Actions artifact; **not a Release**).

## What was actually tested

| Check | Outcome |
|---|---|
| Windows GitHub runner Node tests | 24/24 PASS |
| Windows Python tests | 6/6 PASS |
| Ubuntu Node tests | 23 PASS; 1 Windows-only SKIP |
| Ubuntu Python tests | 6/6 PASS |
| `P0_Windows_Pilot.ps1 -Mode Inspect` checks allowlisted ZIP contents and 9 SHA-256 hashes | PASS on Windows CI |
| Calling `-Mode Stage` without `-ConfirmStage` | Correctly REFUSED; no target folder created |
| Staging with `-ConfirmStage` into a **temporary CI directory**, not a user's CEP folder | PASS |
| Second staging attempt with an existing target | Correctly REFUSED; no overwrite |
| Evidence-template generation | PASS; expressly NOT_VERIFIED |
| Any Adobe Premiere 2024 runtime installed/tested in CI | **NO** |

## Artifact round-trip outside GitHub Actions

The newly downloaded outer artifact was inspected in the execution container.

- Outer ZIP: 12,978 bytes; **CRC PASS**.
- Two files, now **side by side at archive root**: `AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip` (10,956 bytes) and `P0_Windows_Pilot.ps1` (6,686 bytes).
- Inspector script SHA-256: `2f909ba6aa38f51a72e2c66f9425f64053c431177d176e59657e37a4ec5a480e`.
- Inner CEP runtime ZIP SHA-256: `655838bfb8d1e3a1766c7052f53f4a246b8167e126ad8f0b4f4730a9e3a00f95` (unchanged from previous test pack).
- Inner ZIP **CRC PASS** with 10 allowed files (eight runtime files, readme, checksum manifest) and **9/9 SHA-256 content hashes match**.
- The previous packaging bug (PowerShell script and ZIP in separate directories) is now closed.

## Host gate not inferred

CI proves only source and Windows test-helper behavior, not PPRO v24/CEP load, real dock/resizing, actual ExtendScript evaluation, helper callback from a real CEP process, or unchanged project. **G3 BLOCKED_HOST**, G1B NOT_STARTED, AC01–AC30 host verification 0/30, effects 0/21.

### User-visible test workflow, only when explicitly ready
- Extract the outer artifact; inspect `P0_Windows_Pilot.ps1` before any execution.
- Run `.\P0_Windows_Pilot.ps1 -Mode Inspect` in PowerShell. This is **read-only**.
- **Only if the owner intentionally chooses to stage the test extension**, run `.\P0_Windows_Pilot.ps1 -Mode Stage -ConfirmStage`; it stages to the per-user CEP extensions directory, does not overwrite, modify registry, enable developer mode, start Premiere or install Python. A blocked unsigned panel must remain blocked pending a separately approved legitimate test configuration.
- To create **an empty form**, use `.\P0_Windows_Pilot.ps1 -Mode Evidence`. Completing this form does not itself certify G3. Send actual Premiere version, screenshots, logs (with personal paths redacted), tester observation.
- Documentation: [STEP03 Windows pilot walkthrough](../../testing/STEP03_WINDOWS_P0_PILOT.md).  
No `main` merge and no STEP04 code.
