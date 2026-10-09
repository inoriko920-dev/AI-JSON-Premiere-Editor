"""OPTIONAL integration using real local ffmpeg/ffprobe binaries and tiny synthetic MP4.

No user media or network access. Tests the exact production fixed-argv copy
pipeline; does not certify Premiere 2024, FX or source-trim semantics.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from core.background_audio import prepare_video_only_background


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


@unittest.skipUnless(FFMPEG and FFPROBE, "optional FFmpeg binaries unavailable")
class BackgroundAudioRealIntegration(unittest.TestCase):
    def test_real_audio_bearing_mp4_becomes_verified_silent_copy(self):
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as cache_dir:
            root, cache = Path(root_dir), Path(cache_dir)
            src = root / "background.mp4"
            make = [str(FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30",
                    "-f", "lavfi", "-i", "sine=frequency=600:sample_rate=48000",
                    "-t", "1", "-c:v", "mpeg4", "-q:v", "5",
                    "-c:a", "aac", "-shortest", "-y", str(src)]
            try:
                result = subprocess.run(make, capture_output=True, timeout=30,
                                        check=False)
            except (OSError, subprocess.TimeoutExpired):
                self.skipTest("runner cannot create synthetic MP4")
            if result.returncode != 0 or not src.exists():
                self.skipTest("runner missing mpeg4/aac encoder")
            original = src.read_bytes()
            sha = hashlib.sha256(original).hexdigest()
            report = prepare_video_only_background(
                root, src.name, sha, cache,
                ffmpeg_exe=Path(FFMPEG).resolve(),
                ffprobe_exe=Path(FFPROBE).resolve(),
                max_input_bytes=3*1024*1024,
                max_output_bytes=3*1024*1024)
            self.assertEqual(report["status"], "VIDEO_ONLY_CANDIDATE_UNVERIFIED")
            self.assertFalse(report["can_import"])
            self.assertFalse(report["can_assemble"])
            self.assertEqual(report["audio_streams"], 0)
            self.assertEqual(src.read_bytes(), original)
            target = Path(report["candidate_path"])
            self.assertTrue(target.is_file())
            self.assertNotEqual(target, src)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),
                             report["sha256"])
            verify = subprocess.run(
                [str(FFPROBE), "-v", "error", "-select_streams", "a",
                 "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                 str(target)],
                capture_output=True, timeout=20, check=False)
            self.assertEqual(verify.returncode, 0)
            self.assertEqual(verify.stdout.strip(), b"")
            with self.assertRaises(Exception):
                # No accidental overwrite on retry: pre-existing cache retained.
                prepare_video_only_background(
                    root, src.name, sha, cache,
                    ffmpeg_exe=Path(FFMPEG).resolve(),
                    ffprobe_exe=Path(FFPROBE).resolve(),
                    max_input_bytes=3*1024*1024,
                    max_output_bytes=3*1024*1024)


if __name__ == "__main__":
    unittest.main()
