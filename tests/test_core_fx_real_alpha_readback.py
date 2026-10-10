"""STEP18 real FFmpeg qtrle/argb alpha roundtrip using lavfi input only.

This deliberately generates NO PNG, UI image, user asset, or project file.
The temporary synthetic MOV is deleted as soon as each test completes.
Live Premiere import and Canva animation fidelity remain UNVERIFIED.
"""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

from core.animation_phases import build_both_phase_candidate
from core.fx_alpha_backend import compile_filter

_ROOT = Path(__file__).resolve().parents[1]
_demo = runpy.run_path(str(_ROOT / "tests/test_core_contracts.py"))["demo"]
_WIDTH = 16
_HEIGHT = 16
_FRAMES = 150
_FRAME_BYTES = _WIDTH * _HEIGHT * 4
_FFMPEG = shutil.which("ffmpeg")
_FFPROBE = shutil.which("ffprobe")


def _candidate(preset: str, direction: str) -> dict:
    edit, animation = _demo()
    animation["decisions"][0]["preset"] = preset
    animation["decisions"][0]["direction"] = direction
    return compile_filter(build_both_phase_candidate(
        edit, animation, max_instances=10)["entries"][0])


def _run(argv: list[str], timeout: int = 55) -> bytes:
    result = subprocess.run(
        argv, capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise AssertionError(
            "FFmpeg/FFprobe real subprocess failed (exit {}): {}".format(
                result.returncode,
                result.stderr.decode("utf-8", errors="replace")[:1200]))
    return result.stdout


def _pixel(raw: bytes, n: int, x: int, y: int) -> tuple[int, int, int, int]:
    pos = n * _FRAME_BYTES + (y * _WIDTH + x) * 4
    return tuple(raw[pos:pos + 4])


@unittest.skipUnless(_FFMPEG and _FFPROBE,
                     "real FFmpeg and FFprobe required; enforced by STEP18 CI")
class RealFFmpegAlphaRoundtripTests(unittest.TestCase):
    def _render_decode(self, preset: str, direction: str) -> tuple[dict, bytes]:
        candidate = _candidate(preset, direction)
        self.assertNotIn("D-N-1", candidate["filtergraph"])
        self.assertIn("({}-N-1)".format(_FRAMES), candidate["filtergraph"])
        self.assertEqual(candidate["frames"], _FRAMES)

        with tempfile.TemporaryDirectory(prefix="step18_ffmpeg_") as folder:
            mov = Path(folder) / "isolated_alpha_candidate.mov"
            # ffmpeg generates a 16x16 lavfi color stream in memory, NEVER
            # an image asset. Only an ephemeral test MOV is written.
            _run([
                _FFMPEG, "-hide_banner", "-nostdin", "-loglevel", "error",
                "-n", "-f", "lavfi", "-i",
                "color=c=red:s=16x16:r=30:d=5,format=gbrap",
                "-vf", candidate["filtergraph"],
                "-frames:v", str(_FRAMES), "-an", "-c:v", "qtrle",
                "-pix_fmt", "argb", "-f", "mov", str(mov)
            ])
            self.assertTrue(mov.is_file())
            metadata = json.loads(_run([
                _FFPROBE, "-v", "error", "-select_streams", "v:0",
                "-count_frames", "-show_entries",
                "stream=codec_name,pix_fmt,width,height,nb_read_frames,r_frame_rate",
                "-of", "json", str(mov)
            ]))
            streams = metadata["streams"]
            self.assertEqual(len(streams), 1)
            stream = streams[0]
            self.assertEqual(stream["codec_name"], "qtrle")
            self.assertEqual(stream["pix_fmt"], "argb")
            self.assertEqual((stream["width"], stream["height"]),
                             (_WIDTH, _HEIGHT))
            self.assertEqual(stream["r_frame_rate"], "30/1")
            self.assertEqual(stream["nb_read_frames"], str(_FRAMES))
            raw = _run([
                _FFMPEG, "-hide_banner", "-nostdin", "-loglevel", "error",
                "-i", str(mov), "-frames:v", str(_FRAMES),
                "-pix_fmt", "rgba", "-f", "rawvideo", "-"
            ])
        self.assertEqual(len(raw), _FRAMES * _FRAME_BYTES)
        return candidate, raw

    def test_fade_real_mov_has_zero_full_and_gradual_alpha(self):
        item, raw = self._render_decode("FADE", "NONE")
        self.assertEqual((item["in_frames"], item["out_frames"]), (15, 7))
        for x, y in ((0, 0), (3, 12), (15, 15)):
            self.assertEqual(_pixel(raw, 0, x, y)[3], 0)
            self.assertEqual(_pixel(raw, 14, x, y)[3], 255)
            self.assertEqual(_pixel(raw, 142, x, y)[3], 255)
            self.assertEqual(_pixel(raw, 149, x, y)[3], 0)
            self.assertAlmostEqual(_pixel(raw, 7, x, y)[3], 127, delta=3)
            self.assertAlmostEqual(_pixel(raw, 146, x, y)[3], 127, delta=3)
        # Full RGB is preserved under transparency; the alpha channel is
        # changing, not the original RGB source.
        for n in (0, 7, 14, 146, 149):
            r, g, b, _ = _pixel(raw, n, 3, 3)
            self.assertGreaterEqual(r, 245)
            self.assertLessEqual(g, 10)
            self.assertLessEqual(b, 10)

    def test_wipe_four_directions_have_distinct_real_pixel_masks(self):
        directions = {
            "LEFT_TO_RIGHT": (255, 0),
            "RIGHT_TO_LEFT": (0, 255),
            "TOP_TO_BOTTOM": (255, 0),
            "BOTTOM_TO_TOP": (0, 255),
        }
        for direction, expected in directions.items():
            with self.subTest(direction=direction):
                item, raw = self._render_decode("WIPE", direction)
                self.assertEqual((item["in_frames"], item["out_frames"]),
                                 (21, 8))
                self.assertEqual(_pixel(raw, 0, 3, 3)[3], 0)
                self.assertEqual(_pixel(raw, 20, 12, 12)[3], 255)
                self.assertEqual(_pixel(raw, 142, 12, 12)[3], 255)
                self.assertEqual(_pixel(raw, 149, 12, 12)[3], 0)
                # Halfway through IN (10/20), the wipe covers half width
                # or height. Sample opposite quadrants to verify direction.
                self.assertEqual(
                    (_pixel(raw, 10, 3, 3)[3],
                     _pixel(raw, 10, 12, 12)[3]), expected)

if __name__ == "__main__":
    unittest.main()
