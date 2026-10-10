# SOL STEP22 — Native Opacity Read-only Host Inventory (2026-10-10 WIB)

## Locked scope

The approved V3 Premiere Pro 2024/Windows 11 architecture stays CEP + ExtendScript + FFmpeg, **one** GPT-chosen preset per scene+asset, mode BOTH mandatory. This is a safe continuation of STEP21's native FADE Opacity candidate and is not a feature change, a new effect, or an invented host parameter mapping.

## Actual code

- **`host/native_opacity_inspector.jsx`**: ES3-compatible, read-only diagnostic adapter for Premiere 24.x. It first checks project existence, exact Premiere 24.x version shape, managed `AIJSON_MANAGED_` sequence GUID/name, V2/V3 target track, 0-based clip start ticks, exact source `nodeId`, and a unique matching clip. It bounds all collection sizes and label strings, then inventories available component `matchName` and parameter `displayName` (locale-dependent) as percent-escaped metadata. No project write, import, keyframe call, parameter `getValue`, `setValue`, dynamic eval or QE DOM. No hardcoded guess of the actual Opacity ID. The adapter **is not wired into** `CSXS/manifest.xml` / production CEP.
- **`core/fx_native_host_probe.py`**: parses a bounded `S22|1|OBSERVED_UNCERTIFIED` diagnostic record and requires a valid tamper-evident STEP21 FADE candidate. It refuses forged `CERTIFIED` statuses, missing/unsupported host versions, duplicated component names, path delimiters, control characters, ambiguous/double encoding, and oversized records. Result keeps `host_verified=false`, `can_assemble=false`, `readback_verified=false`, `time_coordinate_verified=false`, `opacity_value_units_verified=false`, and null matchName claims.
- Tests use synthetic JS Premiere API objects; **they do not prove real Adobe Premiere API behavior**. The JS tests explicitly ensure parameter methods and clip-editing methods are not invoked. Python tests verify exact parser framing, candidate binding, and failure cases, including Unicode labels.
- **`.github/workflows/step22-native-host-inspection.yml`**: Windows/Linux targeted Node ES3 mock and Python candidate-parser tests, complete Python and JavaScript regressions and an assertion that the host inspector is NOT loaded by the production panel.

## Honest status

G1A specification and G2 owner-approved UI were already PASS. G3 Premiere Pro 2024 real-host proof remains **NOT_VERIFIED**. Exact component IDs, Opacity value units, parameter interpolation, keyframe Time coordinates and host readback are still **not certified**; no Premiere timeline edits or export are authorized. 19 of 21 distinct preset backends remain unimplemented. The one real PNG RGBA strict cache integration may still SKIP without a source with alpha; that is not a PASS and does not block unrelated offline safety work.

No new image, screenshot or visual artifact was generated. No final UI edits, features, silent alternatives, main merge, tag or release were performed.

## Next STEP23 (after STEP22 CI)

Continue isolated native Fade host capability checks and source-to-target binding tests **without guessing actual Premiere Opacity matchNames or mutating user sequences**; then work through the existing 21-preset backlog in its approved order when source parameters and gates allow it. Owner's manual Premiere trial stays at the final stage.

## Verification

Record exact GitHub Actions Windows/Linux CI and SHA at the completion of this STEP; never claim PASS before the latest run finishes.
