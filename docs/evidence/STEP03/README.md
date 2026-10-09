# STEP03 — P0 pilot host gate (BLOCKED_HOST)

The STEP03 P0 **code exists and passes CI**, but its real Adobe Premiere 2024 behavior is not yet proven.

### CI evidence
- [Latest verified source CI](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37960954035): **Windows 24 JS + 6 Python PASS**, Ubuntu **23 JS + 6 Python PASS / 1 Windows-only skipped**.
- A time-limited GitHub Actions artifact `AI_JSON_Premiere_STEP03_P0_TEST_ONLY_Windows` contains one unsigned inner CEP test ZIP.
- Independent artifact inspection verifies inner SHA-256 `655838bfb8d1e3a1766c7052f53f4a246b8167e126ad8f0b4f4730a9e3a00f95` and all 9 internal hashes. See [full audit](P0_PILOT_PACKAGE_AND_CI_2026-10-09.md).

### Safe real Windows/Premiere pilot
1. Use actual Premiere Pro **2024 v24.x** on Windows 11. Record exact build/locale/CSXS runtime. Unpack the TEST ONLY pilot into a temporary directory and inspect contents. Loading it may require Adobe-approved developer/trust setup; **do not change registry or weaken security settings without explicit owner approval**.
2. If local CEP extension testing is authorized and configured, place unpacked `AI_JSON_Premiere_P0_Pilot` in the supported user CEP extensions directory for the test and open the panel using the Premiere Window > Extensions menu (wording varies by version). If not visible, capture a bug report with version/extension logs and stop.
3. Click PERIKSA HOST. Verify host 24.x displayed from *actual ExtendScript*; ensure unsupported hosts cannot assemble. Record original screenshot and raw logs. Try docking, narrow/wide width, close/reopen and keyboard.
4. Optional Python helper pilot: explicitly set the environment variable `AIJSON_P0_PYTHON_EXE` to a trusted absolute Python executable, inherited by Premiere when it launches. Then click PERIKSA HELPER; record actual real CEP Node + Python response. If missing, expect a diagnostic rather than automatic install.
5. Verify project/timeline stays untouched, screenshot the disabled import/preflight/assembly controls. Do not use real work projects for this experiment.
6. Record Windows version, Premiere exact build, tested commit, extension path, expected/actual screenshots/logs and failure codes before requesting G3 evaluation.

**G3 BLOCKED_HOST**, not PASS. `main` is not merged; G1B/STEP04 haven't begun. No image generation/edits to final UI allowed.
