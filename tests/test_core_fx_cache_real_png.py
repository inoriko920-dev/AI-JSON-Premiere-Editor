"""Read-only STEP19 integration: use existing approved UI PNG as codec transport input.

Tests PNG -> pinned private copy -> FFmpeg MOV -> sampled alpha -> private
cache publication. It does NOT repurpose the UI image in the application
or claim it matches Canva. No new PNG, screenshot, or source asset created.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import runpy
import shutil
import struct
import tempfile
import unittest

from core.animation_phases import build_both_phase_candidate
from core.fx_cache_worker import render_candidate

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "docs" / "ui" / "final"
_demo = runpy.run_path(str(ROOT / "tests/test_core_contracts.py"))["demo"]
FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def approved_existing_alpha_png():
    """Choose already-approved repository artwork, without creating any."""
    for path in sorted(UI.glob("UI*.png")):
        with path.open("rb") as f:
            head = f.read(33)
        if len(head) != 33 or head[:8] != b"\x89PNG\r\n\x1a\n":
            continue
        width, height = struct.unpack(">II", head[16:24])
        if (head[24] in (8, 16) and head[25] in (4, 6)
                and width >= 8 and height >= 8):
            return path, width, height
    return None


def item(preset="FADE", direction="NONE"):
    edit, animation = _demo()
    animation["decisions"][0]["preset"] = preset
    animation["decisions"][0]["direction"] = direction
    entry = build_both_phase_candidate(edit, animation, max_instances=10)["entries"][0]
    # Exact B02 IN/OUT reference retained, minimum lawful duration keeps
    # genuine full-resolution CI FFmpeg runtime modest.
    length = entry["in_frames"] + entry["out_frames"]
    entry.update(start_frame=0, end_frame=length,
                 in_range=[0, entry["in_frames"]],
                 hold_range=[entry["in_frames"], entry["in_frames"]],
                 out_range=[entry["in_frames"], length])
    return entry


@unittest.skipUnless(FFMPEG and FFPROBE, "real FFmpeg and FFprobe missing")
class ApprovedPNGReadonlyIntegrationTests(unittest.TestCase):
    def test_existing_approved_source_is_unchanged_and_cache_pixel_verified(self):
        source_info = approved_existing_alpha_png()
        if source_info is None:
            self.skipTest("No existing approved RGBA or grayscale-alpha PNG in repository")
        source, width, height = source_info
        self.assertTrue(source.is_file())
        before = source.stat()
        original_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="step19_cache_") as cache:
            report = render_candidate(
                item(), source_png=Path(source.name),
                media_root=UI.resolve(), cache_root=Path(cache).resolve(),
                expected_sha256=original_sha, ffmpeg_exe=Path(FFMPEG).resolve(),
                ffprobe_exe=Path(FFPROBE).resolve(),
                max_source_bytes=10_000_000, max_pixels=10_000_000,
                max_frames=40, timeout_seconds=240)
            self.assertTrue(report["alpha_pixels_verified"])
            self.assertFalse(report["host_verified"])
            self.assertFalse(report["whole_frame_verified"])
            self.assertFalse(report["can_assemble"])
            self.assertFalse(report["canva_fidelity_verified"])
            self.assertEqual(report["size"], [width,height])
            self.assertGreater(report["alpha_checked_samples"],0)
            self.assertEqual(len(list(Path(cache).glob("fx_*.mov"))),1)
            self.assertFalse(list(Path(cache).glob(".fx_work_*")))
        after = source.stat()
        self.assertEqual((before.st_size,before.st_mtime_ns),
                         (after.st_size,after.st_mtime_ns))
        self.assertEqual(original_sha,hashlib.sha256(source.read_bytes()).hexdigest())

if __name__ == "__main__":
    unittest.main()
