# SOL STEP03 P0 — CI and unsigned pilot package proof (2026-10-09)

**Verified product-code SHA:** `88010b4002bd38a68179a89b3e6623de5e0243d2`  
**CI push run:** [37960954035](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37960954035), **SUCCESS**.  
**CI PR run:** [37960959003](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37960959003), **SUCCESS**.  
**Windows artifact name:** `AI_JSON_Premiere_STEP03_P0_TEST_ONLY_Windows`  
**Artifact id:** `11630259667`. GitHub artifact is retained for 7 days and is **not a GitHub Release**.

## Test results actually observed

| Runner | Node tests | Python unittest | Build and publication |
|---|---|---|---|
| Windows latest | **24/24 PASS; 0 fail** | **6/6 PASS** | deterministic test ZIP generated, artifact uploaded successfully |
| Ubuntu latest | **23 PASS, 1 Windows-only SKIP; 0 fail** | **6/6 PASS** | identical packaging procedure ran; no duplicate artifact |

The Windows test suite includes an actual Node `execFile` launch of Python 3.11 with fixed arguments, in addition to simulated CEP browser/JSX tests. **Neither runner has Adobe Premiere Pro installed**, and none of these checks is runtime G3 proof.

## ZIP verified out of GitHub Actions

The workflow artifact was downloaded and inspected independently in the working container.

- Outer GitHub artifact ZIP CRC PASS (10,080 bytes).
- Inner `AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip` CRC PASS (10,956 bytes).
- Inner SHA-256: `655838bfb8d1e3a1766c7052f53f4a246b8167e126ad8f0b4f4730a9e3a00f95`.
- Included only 8 allowlisted CEP/runtime files, `P0_TEST_ONLY_README.txt`, and `P0_SHA256SUMS.txt`.
- **9/9 SHA-256 entries verified byte-for-byte** against inner ZIP; no `node_modules`, planning source, user UI PNG/DOCX, registry modifications, installer or final MP4.
- Source packaging script: [build_p0_pilot.py](../../../tools/build_p0_pilot.py). Test: [test_p0_package.py](../../../tests/test_p0_package.py).

## Explicit boundary: P0 test pack, not release

The pilot ZIP is an **unsigned, unpacked CEP development extension**. It does not self-install, enable developer mode, change security settings, or certify compatibility with any specific Premiere build. Loading an unsigned panel can require an owner-authorized Adobe CEP developer setup; do not silently perform registry changes.

Required subsequent real-host evidence before **G3 PASS**:
1. Windows 11 with Premiere Pro **2024 24.x** exact build and CEP runtime.
2. User/tester opens P0 from Premiere Extensions menu (if supported) and verifies docking, resize, close/reopen, UTF-8 display and absence of user project mutations.
3. Host version probe and optional developer-configured local Python helper probe are **actually run inside CEP**, capture real screenshots, logs, version and tested SHA.
4. If host fails or panel fails to open, mark G3 FAIL/BLOCKED, fix on SOL branch and repeat; do not invent a success.
5. G1B/STEP04 remain not started. Premiere effects host certification 0/21, host acceptance criteria 0/30.

**Gate: G3 BLOCKED_HOST.** `main` stays unchanged, PR remains Draft; no merge, installer, portable production build or release.
