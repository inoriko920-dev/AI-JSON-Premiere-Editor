# SOL STEP08 — 4-track offline preflight (10 October 2026)

Owner instruction: finish coding and all feasible automated tests first; user Windows 11 / Premiere Pro 2024 hands-on test only at the end. **G3 stays BLOCKED_HOST / NOT VERIFIED.**

Real code:
- `core/track_preflight.py` combines strict dual JSON contracts, actual media/SRT scan and SHA-256 inventory, real-media snapshot recheck, FFprobe stream/duration metadata, and deterministic V1/V2/V3/A1 track compiler.
- If FFprobe is not configured, outcome NEEDS_REVIEW with NO candidate; invalid JSON/media/SRT or changed source fails closed. Optional timebase is for an UNVERIFIED offline draft only.
- `core/validate_cli.py` adds `--include-track-preflight` and optional `--candidate-timebase-ticks`, without READY. CEP panel uses the new read-only option; `panel/validation_bridge.js` strips untrusted data and forwards only track counts, total frames and digest.
- CEP test-only package includes all transitive Python modules (`host_ticks.py`, `track_plan.py`, `track_preflight.py`), with **24 allowlisted entries, 23 SHA-256 hashes**. Project-modifying host adapters remain excluded.
- Automated tests cover actual temporary local media bytes and SRT, mocked FFprobe records, changed/missing source, hash mismatch, invalid track timing, private path redaction and safe bridge parsing. Earlier Windows Node-to-Python integration remains in CI.

Unfinished: full Premiere 24.x host readback, immutable proof-bound dispatcher, project import/placement authorization, crop/layout final, 21/21 BOTH animations, native vs prerender backend, journal/recovery, Windows final installer, MP4 and actual host acceptance. **No claim app is finished**. PR remains Draft, main untouched.
