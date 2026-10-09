# STEP03 — Pilot P0: HOST BLOCKED

## Implemented on SOL branch
- CEP 24.x-only candidate extension manifest and Indonesian white/blue dockable UI skeleton, based on G2-approved designs.
- ExtendScript ES3 read-only host version probe via one **fixed**, non-interpolated evalScript call.
- Panel bridge with strict response grammar, unsupported host rejection, 8-second timeout, stale callback cancellation.
- Python helper --probe JSON handshake (manual CLI only; actual CEP helper launch NOT wired).
- Assembly/preflight/file import buttons **disabled**. No JSON parser, FFmpeg worker, timeline operations or effect code yet.
- Unit/static tests are non-Premiere checks, NOT host evidence. Upstream Adobe samples consulted for protocol shape; **no Adobe-licensed source code vendored**.

## Mandatory real host evidence for G3
1. Windows 11 + Adobe Premiere Pro 2024 **exact build 24.x**, record version/OS/locale/CEP runtime.
2. Install unpacked extension in the supported user/system CEP extensions folder via an owner-approved method (no silent registry changes/PlayerDebugMode toggle).
3. Open Premiere > Window > Extensions > AI JSON Premiere Editor (P0), inspect docking at narrow/wide sizes and layout against approved PNGs.
4. Check host detection supported PPRO 24.x; record real screenshot/video and logs. Observe unsupported host guard without entering timeline.
5. Close/reopen Premiere and panel; test timeouts/callbacks, unicode source root paths (STEP04 implementation may be required to test them) and no unintended mutation.
6. Test Python helper --probe manually; CEP-to-helper launch remains not integrated, so **P0 full requirements incomplete**.
7. Record exact tested commit, commands, EXIT codes, screenshots and logs in this directory. Only then evaluate G3 PASS.

## Blocker
No Windows 11 Premiere Pro 2024 host is available in this execution session, hence **G3 BLOCKED_HOST**. Do not progress as if AC01 or AC02 passed and do not start STEP04.
