# STEP03 — P0 gate remains BLOCKED_HOST

## Current validated pilot

- [Windows/Linux CI SUCCESS on tested source SHA](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37963202254) (source `bb8154bb`): Windows **24 JavaScript + 6 Python PASS**, Linux **23 JavaScript + 6 Python PASS / 1 Windows-only skip**.
- The Windows pilot artifact now contains the unsigned CEP test ZIP and `P0_Windows_Pilot.ps1` together. An optional `-ExpectedZipSha256` provides an **independently anchored ZIP digest check** (see [Windows instructions](../../testing/STEP03_WINDOWS_P0_PILOT.md)).
- [Security regression report](P0_NEGATIVE_ZIP_CI_2026-10-09.md): eight corrupt/malicious ZIP variants were rejected, including from Stage mode, with no stage folder created. This is **not** proof that Premiere loaded the extension.
- Original G2-approved PNG images remain unchanged. No user-facing production installer or portable release has been created.

## Remaining real host G3 evidence
1. Tester with Windows 11 and **genuine Adobe Premiere Pro 2024 v24.x** records exact version and CEP runtime.
2. After the owner deliberately approves staging the unsigned P0 pilot with the supported Adobe process, open the panel in Premiere's Extensions menu, record screenshot, docking/resize, close/reopen/focus, and real JSX host result.
3. If dev Python is intentionally configured, click PERIKSA HELPER and record the real CEP Node and Python handshake; otherwise record the expected blocked status. Do **not** use any existing work project for the test.
4. Check that PRECHECK/ASSEMBLE remain disabled and no timeline/project changes occur. Capture original screenshots/logs, tested commit and errors.
5. Only after genuine Windows host observations and fixes can G3 be audited as PASS; without them, leave G3 BLOCKED_HOST and do not start STEP04.

Do not change Windows registry/Adobe security settings silently. `main` and Draft PR merge state are unchanged.
