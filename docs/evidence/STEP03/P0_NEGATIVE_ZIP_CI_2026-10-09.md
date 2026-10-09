# STEP03 SOL — Adversarial Windows ZIP inspector evidence (2026-10-09)

**Tested code commit:** `bb8154bbd1d90ffb376217c061d59971afff9c4d`  
**CI Windows + Linux:** [Push run 37963202254 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37963202254) and [Draft PR run 37963209555 — SUCCESS](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37963209555).

## Verified source tests and negative archive tests

- Windows: 24/24 Node tests PASS, 6/6 Python tests PASS; PowerShell read-only Inspect, explicit Stage guard, no-overwrite and evidence-template checks PASS.
- Ubuntu: 23 Node tests PASS + 1 Windows-only skip, 6/6 Python tests PASS.
- **Eight deliberately corrupted ZIP variants** were generated under a temporary Windows CI directory. All were rejected, both for Inspect and Stage, before any stage directory appeared:
  1. Modified runtime JavaScript with unchanged digest: `P0_SHA_MISMATCH`
  2. Duplicated checksum record: `P0_SHA_MANIFEST_INVALID`
  3. Missing checksum record: `P0_SHA_MANIFEST_INVALID`
  4. Path traversal archive member: `P0_UNSAFE_ENTRY`
  5. Unexpected archive member: `P0_UNSAFE_ENTRY`
  6. Oversized archive member: `P0_UNSAFE_ENTRY`
  7. Missing archive entry: `P0_UNEXPECTED_ENTRIES`
  8. Duplicate archive entry: `P0_UNEXPECTED_ENTRIES`
- An independently supplied **ZIP** SHA-256 is now optionally enforced by `-ExpectedZipSha256`; a wrong or malformed expected value fails closed. Without this option, the inspector explicitly reports `P0_PROVENANCE=SELF_INTEGRITY_ONLY`. **An internal SHA manifest alone cannot prove download provenance.**
- Negative suite source: `tools/windows/Test_P0_Negative.ps1`; inspector: `tools/windows/P0_Windows_Pilot.ps1`.

## Downloaded artifact integrity cross-check

GitHub artifact id **11631822664**, name `AI_JSON_Premiere_STEP03_P0_TEST_ONLY_Windows`, associated with source SHA `bb8154bb`, expires after 7 days.

Independently downloaded/extracted in the working container:
- Outer artifact ZIP: **13,282 bytes**, **CRC PASS**, two root members: `AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip` and `P0_Windows_Pilot.ps1`.
- Inner unsigned CEP test ZIP: **10,956 bytes**, SHA-256 `655838bfb8d1e3a1766c7052f53f4a246b8167e126ad8f0b4f4730a9e3a00f95`, **CRC PASS**, **10 allowlisted entries**, nine checksum manifest records, **9/9 sha256 content matches**.
- Outer artifact's ZIP SHA-256 is separately recorded by GitHub as `bfdf370260471f0da22e91a53f3e302f1bfab8da35c4cb85620097da35a72408`. This is *not* the inner CEP ZIP hash; when using `-ExpectedZipSha256`, use the **inner** ZIP digest above if the code matches the tested source.
- The PowerShell inspector is read-only by default. Staging requires explicit `-Mode Stage -ConfirmStage`, cannot overwrite an existing pilot directory, does not alter Windows registry/trust, does not launch Premiere or modify user projects.

## Gate limitations

**G3 remains `BLOCKED_HOST`**. No actual installed/licensed Adobe Premiere Pro 2024 (v24.x) on Windows 11 was used. The test asserts only ZIP handling and local helper behavior. We cannot claim panel menu visibility, CEP runtime compatibility, docking, host JSX callback, actual Premiere version, or real edit safety. AC01–AC30 host verification remains 0/30; 21 animation effects remain 0/21 host certified. G1B executable schema and STEP04 remain NOT_STARTED.

**No main merge, no Production ZIP/installer or release, no image generation/edit.**
