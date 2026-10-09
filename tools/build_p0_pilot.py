#!/usr/bin/env python3
"""Build a deterministic, unsigned CEP P0 TEST-ONLY archive. Not an installer/release."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PILOT = "AI_JSON_Premiere_P0_Pilot"
REQUIRED = (
    "CSXS/manifest.xml",
    "panel/index.html",
    "panel/styles.css",
    "panel/bridge.js",
    "panel/helper_bridge.js",
    "panel/validation_bridge.js",
    "panel/validation_ui.js",
    "panel/app.js",
    "host/step03.jsx",
    "helper/handshake.py",
    "helper/validate_request.py",
    "core/__init__.py",
    "core/contracts.py",
    "core/draft_compiler.py",
    "core/ffprobe.py",
    "core/import_snapshot.py",
    "core/media.py",
    "core/host_ticks.py",
    "core/track_plan.py",
    "core/track_preflight.py",
    "core/validate_cli.py",
    "core/direction_registry.json",
)
GUIDE = """STEP03 P0 - UNSIGNED CEP DEVELOPMENT PILOT (NOT AN INSTALLER)
Target: Adobe Premiere Pro 2024 (24.x), Windows 11.
Status: GitHub static CI only; G3 BLOCKED_HOST until genuine Premiere evidence.
Unzip and inspect files before any test. Folder AI_JSON_Premiere_P0_Pilot
contains CEP manifest, read-only JSX probe, native file pickers, and offline JSON validator.
Unpacked unsigned CEP may require approved local developer/trust configuration.
DO NOT change registry, security settings, or install helpers automatically.
Only follow Adobe-supported CEP test setup with explicit owner approval.
Python developer-only: environment AIJSON_P0_PYTHON_EXE pointing to a trusted
absolute python.exe must be inherited by Premiere, or helper stays blocked.
Includes safe offline data checks only: no Premiere import, sequence assembly, effects, media writes or MP4 generation.
Keep existing user projects intact. Do not claim G3 from this ZIP/CI.
For pilot log and exact real host evidence see docs/evidence/STEP03/README.md.
"""
ARCHIVE_DATE = (2020, 1, 1, 0, 0, 0)
MAX_PILOT_BYTES = 512 * 1024


def source_bytes(relative: str) -> bytes:
    p = ROOT / relative
    if p.is_symlink() or not p.is_file():
        raise ValueError(f"Missing, symlink, or non-file: {relative}")
    if p.resolve().is_relative_to(ROOT.resolve()) is False:
        raise ValueError(f"Outside source root: {relative}")
    data = p.read_bytes()
    if len(data) > MAX_PILOT_BYTES:
        raise ValueError(f"Oversized pilot source: {relative}")
    return data


def zip_member(z: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=ARCHIVE_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    z.writestr(info, data, compresslevel=9)


def build(output: Path) -> dict[str, str]:
    if output.is_symlink():
        raise ValueError("Output cannot be a symlink")
    entries: dict[str, bytes] = {}
    for relative in REQUIRED:
        entries[f"{PILOT}/{relative}"] = source_bytes(relative)
    entries[f"{PILOT}/P0_TEST_ONLY_README.txt"] = GUIDE.encode("utf-8")
    manifest_lines = [f"{hashlib.sha256(data).hexdigest()}  {key[len(PILOT)+1:]}"
                      for key, data in sorted(entries.items())]
    entries[f"{PILOT}/P0_SHA256SUMS.txt"] = ("\n".join(manifest_lines) + "\n").encode("ascii")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", allowZip64=False) as z:
        for key, data in sorted(entries.items()):
            zip_member(z, key, data)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(entries)
    return {k: hashlib.sha256(v).hexdigest() for k,v in entries.items()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist/AI_JSON_Premiere_P0_Pilot_TEST_ONLY.zip")
    args = parser.parse_args(argv)
    outfile = Path(args.output).resolve()
    build(outfile)
    digest = hashlib.sha256(outfile.read_bytes()).hexdigest()
    print(f"P0_TEST_ZIP={outfile}")
    print(f"P0_TEST_ZIP_SHA256={digest}")
    print(f"NOTICE=UNSIGNED_TEST_ONLY_NOT_PREMIERE_VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
