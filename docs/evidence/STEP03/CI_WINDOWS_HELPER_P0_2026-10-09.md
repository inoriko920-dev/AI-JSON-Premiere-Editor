# SOL STEP03 — P0 static CI / Windows subprocess proof

**Tested code SHA:** `e9ad7d3d227c7e37d09cca3184a324d2eac4b8c7`
**CI push run:** [#37959967055](https://github.com/inoriko920-dev/AI-JSON-Premiere-Editor/actions/runs/37959967055) — SUCCESS.

| Runner | Node tests | Python tests | Result |
|---|---|---|---|
| Windows latest, setup-node 20 / Python 3.11 | **23 PASS, 0 FAIL, 0 skipped** | **3 PASS** | **SUCCESS** |
| Ubuntu latest, setup-node 20 / Python 3.11 | **22 PASS, 0 FAIL, 1 Windows-only skipped** | **3 PASS** | **SUCCESS** |

## What runs on Windows
- Real Node `child_process.execFile` starts installed Python 3.11 interpreter via absolute path inherited from `setup-python`, with `-I -B helper/handshake.py --probe`; no shell.
- Parses JSON handshake with protocol `AIJSON_STEP03_P0`, version `0.0.3`, and all 4 capabilities false.
- Validates supported Premiere major 24.x (simulated JSX), rejects 25.x, malformed responses and version tampering; fixed JSX command, timeouts, stale callbacks, missing helper, path traversal and extraneous capabilities.
- Checks manifest CEF Node flags under `Resources` and validates disabled preflight and assembly buttons.
- This does **not** exercise Adobe Premiere, CSXS plugin installation, real Chromium context, real JSX `app.version`, or actual docking.

## Production claims NOT made
- Not a Premiere CI workflow, cannot verify AC01/AC02.
- No Windows 11 exact Premiere version or license in this test environment; G3 still BLOCKED_HOST.
- No JSON validator, media importer, timeline assembly, effects, MP4 exporter, installer or portable build. 0/30 AC host verified, 0/21 animations host verified.
- Helper uses a *developer-only explicit Python path*; end-user helper packaging is later scope.
