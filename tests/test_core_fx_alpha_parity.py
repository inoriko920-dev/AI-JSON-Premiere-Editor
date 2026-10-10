"""STEP25 independent Fade alpha parity: offline bytes, no new UI/PNG."""
from __future__ import annotations

import copy
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

from core.animation_phases import build_both_phase_candidate
from core.fx_alpha_backend import compile_filter
from core.fx_native_fade import compile_native_fade
from core.fx_alpha_parity import FadeParityError, verify_native_fade_alpha_parity

ROOT = Path(__file__).resolve().parents[1]
_demo = runpy.run_path(str(ROOT / "tests/test_core_contracts.py"))["demo"]
FFMPEG = shutil.which("ffmpeg")
FRAMES_TO_CHECK = ((0, 22), (90, 150))


def candidates(*, scene_start=0, duration=150):
    edit, animation = _demo()
    animation["decisions"][0]["preset"] = "FADE"
    animation["decisions"][0]["direction"] = "NONE"
    item = build_both_phase_candidate(edit, animation, max_instances=10)["entries"][0]
    item.update(start_frame=scene_start, end_frame=scene_start + duration,
                in_range=[scene_start, scene_start + 15],
                hold_range=[scene_start + 15, scene_start + duration - 7],
                out_range=[scene_start + duration - 7, scene_start + duration])
    return compile_native_fade(item), compile_filter(item)


def opaque_red_alpha_bytes(frames):
    result = bytearray()
    for n in range(frames):
        if n < 15:
            value = round(255 * n / 14)
        elif n < frames - 7:
            value = 255
        else:
            value = round(255 * (frames - n - 1) / 6)
        result.extend((255, 0, 0, value))
    return bytes(result)


class FadeParityOfflineTests(unittest.TestCase):
    def test_full_span_reference_no_hold_and_nonzero_global_offset(self):
        for start, duration in FRAMES_TO_CHECK:
            with self.subTest(start=start, duration=duration):
                native, filt = candidates(scene_start=start, duration=duration)
                result = verify_native_fade_alpha_parity(
                    native, filt, opaque_red_alpha_bytes(duration))
                self.assertEqual(result["checked_frames"], duration)
                self.assertEqual(result["checked_rgba_samples"], duration)
                self.assertFalse(result["host_verified"])
                self.assertFalse(result["full_frame_verified"])
                self.assertFalse(result["can_assemble"])

    def test_rejects_alpha_corruption_at_middle_frame_not_only_boundary(self):
        native, filt = candidates()
        damaged = bytearray(opaque_red_alpha_bytes(150))
        damaged[9 * 4 + 3] = 0
        with self.assertRaises(FadeParityError) as ctx:
            verify_native_fade_alpha_parity(native, filt, bytes(damaged))
        self.assertEqual(ctx.exception.code, "E_FX_PARITY_ALPHA_MISMATCH")

    def test_modified_native_and_filtergraph_never_count_as_certified(self):
        native, filt = candidates()
        altered = copy.deepcopy(native)
        altered["samples"][1]["opacity_percent"] = 99
        with self.assertRaises(FadeParityError) as ctx:
            verify_native_fade_alpha_parity(
                altered, filt, opaque_red_alpha_bytes(150))
        self.assertEqual(ctx.exception.code, "E_FX_PARITY_NATIVE_INVALID")
        altered_filter = copy.deepcopy(filt)
        altered_filter["filtergraph"] += ",negate"
        with self.assertRaises(FadeParityError) as ctx:
            verify_native_fade_alpha_parity(
                native, altered_filter, opaque_red_alpha_bytes(150))
        self.assertEqual(ctx.exception.code, "E_FX_PARITY_FILTER_CHANGED")
        altered_filter = copy.deepcopy(filt)
        altered_filter["can_assemble"] = True
        with self.assertRaises(FadeParityError):
            verify_native_fade_alpha_parity(
                native, altered_filter, opaque_red_alpha_bytes(150))

    def test_rejects_decode_short_extra_or_wrong_source(self):
        native, filt = candidates()
        raw = opaque_red_alpha_bytes(150)
        for corrupted in (raw[:-4], raw+b"\x00", b"", "not bytes"):
            with self.subTest(input_type=type(corrupted).__name__):
                with self.assertRaises(FadeParityError) as ctx:
                    verify_native_fade_alpha_parity(native, filt, corrupted)
                self.assertEqual(ctx.exception.code, "E_FX_PARITY_RAW_INVALID")
        damaged = bytearray(raw)
        damaged[4:7] = b"\x00\x00\x00"
        with self.assertRaises(FadeParityError) as ctx:
            verify_native_fade_alpha_parity(native, filt, bytes(damaged))
        self.assertEqual(ctx.exception.code, "E_FX_PARITY_SOURCE_CHANGED")

    def test_unimplemented_presets_cannot_substitute_fade(self):
        native, filt = candidates()
        for preset in ("WIPE", "BRUSH", "POP", "PAN"):
            changed = copy.deepcopy(filt)
            changed["preset"] = preset
            with self.subTest(preset=preset):
                with self.assertRaises(FadeParityError):
                    verify_native_fade_alpha_parity(
                        native, changed, opaque_red_alpha_bytes(150))


@unittest.skipUnless(FFMPEG, "Real FFmpeg required for native MOV parity")
class FadeParityNativeFFmpegTests(unittest.TestCase):
    def test_real_qtrle_opaque_red_source_all_frames_match_native(self):
        # Color filter generates transient *video frames*, never PNG or UI art.
        for scene_start, frames in FRAMES_TO_CHECK:
            with self.subTest(scene_start=scene_start, frames=frames):
                native, compiled = candidates(
                    scene_start=scene_start, duration=frames)
                with tempfile.TemporaryDirectory(prefix="step25_mov_only_") as d:
                    mov = Path(d) / "internal_test.mov"
                    cmd = [
                        FFMPEG, "-hide_banner", "-nostdin", "-loglevel", "error",
                        "-n", "-f", "lavfi", "-i",
                        "color=c=red:s=16x16:r=30:d=6",
                        "-vf", compiled["filtergraph"],
                        "-frames:v", str(frames), "-an", "-c:v", "qtrle",
                        "-pix_fmt", "argb", "-f", "mov", str(mov),
                    ]
                    created = subprocess.run(
                        cmd, capture_output=True, timeout=100, check=False)
                    self.assertEqual(
                        created.returncode, 0,
                        created.stderr.decode(errors="replace")[:900])
                    self.assertTrue(mov.is_file())
                    decoded = subprocess.run([
                        FFMPEG, "-hide_banner", "-nostdin", "-loglevel", "error",
                        "-i", str(mov),
                        "-vf", "scale=1:1:flags=neighbor,format=rgba",
                        "-frames:v", str(frames),
                        "-pix_fmt", "rgba", "-f", "rawvideo", "-",
                    ], capture_output=True, timeout=100, check=False)
                    self.assertEqual(
                        decoded.returncode, 0,
                        decoded.stderr.decode(errors="replace")[:900])
                    evidence = verify_native_fade_alpha_parity(
                        native, compiled, decoded.stdout)
                    self.assertEqual(evidence["checked_frames"],frames)
                    self.assertLessEqual(
                        evidence["max_absolute_alpha_error"],3)
                    self.assertFalse(evidence["native_premiere_verified"])
                    self.assertFalse(evidence["can_assemble"])

if __name__ == "__main__":
    unittest.main()
