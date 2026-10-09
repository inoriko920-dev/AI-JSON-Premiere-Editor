# SOL STEP03 — CEP panel lifecycle cleanup and P0 artifact proof

**Source commit tested:** `79c53ef904c2a6f1320546dbff97352b21179273`.  
**Run:** [GitHub Actions #37963971626](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37963971626) — **SUCCESS**, Windows latest and Ubuntu latest.  
**Windows artifact:** `AI_JSON_Premiere_STEP03_P0_TEST_ONLY_Windows`, artifact ID `11632757967`, expires 2026-10-16 (GitHub Actions test artifact only, not a release).

## Actual code repair
- Panel P0 now registers idempotent `pagehide` and `unload` cleanup.
- In-flight fixed JSX host-version requests are cancelled and their callbacks are invalidated when the panel closes.
- In-flight Python subprocess helper probe is cancelled/killed during panel shutdown; stale helper callbacks cannot report success after close.
- Disabled import/preflight/assembly buttons stay disabled. No Premiere project mutation, no new UI mockup images.
- Two new mock-browser lifecycle tests verify delayed host callback suppression and one-time helper subprocess kill even when `pagehide` and `unload` both fire.

## Cross-platform unit tests
| Runner | JavaScript Node tests | Python unittest | Other safeguards |
|---|---|---|---|
| Windows | 26 PASS / 0 FAIL | 6 PASS | safe staging and eight adversarial ZIP cases PASS |
| Ubuntu | 25 PASS / 1 Windows-only SKIP | 6 PASS | P0 deterministic package PASS |

## Artifact integrity re-verified
Downloaded actual GitHub Actions Windows artifact into isolated working environment:
- Outer GitHub artifact ZIP: **13,367 bytes**, CRC PASS; contains `AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip` and `P0_Windows_Pilot.ps1`.
- Inner CEP pilot ZIP: **11,042 bytes**, SHA-256 `e4e5a034e6fbdb010cd06b44815036f1450df9cc623e636420a3b124bcaf3efd`, ZIP CRC PASS, 10 allowlisted entries and **9/9 internal content SHA-256 valid**.
- Verified the inner `panel/app.js` actually includes the lifecycle `unload` teardown code (not merely a PR code diff).
- **External hash parameter uses the INNER CEP ZIP digest**, never the outer GitHub artifact digest. Both checks are for integrity; they are not Premiere host proof.

## Mandatory G3 status
**G3 = BLOCKED_HOST.** Adobe Premiere Pro 2024 major 24.x on real Windows 11 has **not** run this code in a CEP window. Closing CEP may emit lifecycle events differently from mock-browser simulations; genuine panel menu, docking, process termination, host/probe and safe timeline state require real host logs/screenshots and exact version. G1B/STEP04 NOT_STARTED; animation presets 0/21 host verified, AC 0/30 host verified. PR remains Draft and `main` unchanged; no installer/production release.
