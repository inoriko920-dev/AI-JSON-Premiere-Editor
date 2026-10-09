# Windows P0 test pilot — inspection and optional manual staging

The downloaded GitHub Actions **artifact ZIP** contains two separate files:
- `AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip` (unsigned CEP runtime folder archive).
- `P0_Windows_Pilot.ps1` (read-only by default, SHA-verifying helper; source `tools/windows/P0_Windows_Pilot.ps1`).

**Always inspect the source before running it.** It does not sign extensions or change registry/developer mode. An unsigned CEP extension might not load on a stock machine. Do not bypass Windows/Adobe security settings automatically.

Open PowerShell in the extracted artifact directory (only if your script execution policy and local trust rules allow it):

```powershell
# 1) Read-only. Checks 10 allowed ZIP files and all 9 SHA-256 entries; no install.
.\P0_Windows_Pilot.ps1 -Mode Inspect

# 2) Optional: explicitly place unpacked pilot in YOUR per-user CEP folder,
# without replacing existing extension folders or changing registry.
.\P0_Windows_Pilot.ps1 -Mode Stage -ConfirmStage

# 3) Optional: create an EMPTY evidence form, not a pretend successful test.
.\P0_Windows_Pilot.ps1 -Mode Evidence
```

No `-ExecutionPolicy Bypass`, silent download, administrator access, automatic Premiere launch or `PlayerDebugMode` registry modifications are performed. If an unsigned extension is blocked by Adobe/Windows, **stop and report it**; G3 remains blocked until a separately approved test setup is available. If the target CEP folder already exists, the script refuses to overwrite it.

After staging, a person with Adobe Premiere Pro 2024 v24.x may open the menu and test P0 read-only panel. The AI may inspect supplied real logs/screenshots but cannot fabricate them. See [STEP03 host checklist](../evidence/STEP03/README.md).
