# STEP03 — P0 pilot: tests green, G3 real host verification still blocked

**Source and test packaging:** SOL branch `sol/step03-cep-p0-20261009`.  
**CI evidence:** [Windows + Linux SUCCESS #37962129971](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37962129971).  
**Current downloadable test artifact:** GitHub Actions named `AI_JSON_Premiere_STEP03_P0_TEST_ONLY_Windows`, containing CEP ZIP and PowerShell inspector side-by-side. Unpacked, unsigned development pilot; not installer or release.

### Before use on a real Windows host
Read [short Windows procedure](../../testing/STEP03_WINDOWS_P0_PILOT.md) and [exact checksum/CI evidence](P0_WINDOWS_INSPECTOR_AND_CI_2026-10-09.md). Run the inspector first; staging is a separately explicit step. It cannot change Adobe/Windows trust settings. If CEP refuses unsigned extension, stop and report; no auto-registry/debug changes.

### Mandatory G3 requirements
1. Confirm exact Windows 11 and **Adobe Premiere Pro 2024 24.x** installed under license, record version/build and CEP runtime.
2. User-authorized staging under per-user CEP path, if supported by the actual Adobe setup; open `Window > Extensions` and locate P0 panel. Do not assert any Premiere host check has occurred in CI.
3. Test docking, resize/narrow panel, close/reopen, focus/keyboard, and disabled preflight/import/assembly controls.
4. Click PERIKSA HOST; capture actual version probe and CEP logs. If explicitly configured, click PERIKSA HELPER and capture real Python response (or report fail code), without changing any project.
5. Record real screenshots/logs, exact commit SHA, expected/observed behaviour and errors. Only after these observations and any fixes can G3 be audited.

**G3 BLOCKED_HOST; G1B/STEP04 NOT_STARTED.** No user image generation or alteration, no merge, installer or MP4 claims.
