"""Optional REAL local FFmpeg/FFprobe smoke, only using generated temporary media.

No Premiere host; no user media, downloads, external networks or GPU needed.
Skipped explicitly if official runner image lacks the binaries/encoder.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

from core.ffprobe import inspect_ffprobe


FFPROBE = shutil.which("ffprobe")
FFMPEG = shutil.which("ffmpeg")


@unittest.skipUnless(FFPROBE and FFMPEG, "real ffprobe/ffmpeg unavailable in runner")
class RealFFProbeSmokeTests(unittest.TestCase):
    def test_real_wav_mp4_metadata_from_temporary_generated_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wav_file = root / "narration.wav"
            with wave.open(str(wav_file), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(48000)
                f.writeframes(b"\0\0" * 48000)
            mp4_file = root / "background.mp4"
            command = [
                str(FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=black:s=64x64:r=30",
                "-t", "1", "-an", "-c:v", "mpeg4", "-pix_fmt", "yuv420p",
                "-y", str(mp4_file)
            ]
            try:
                created = subprocess.run(
                    command, capture_output=True, timeout=20, check=False)
            except (OSError, subprocess.TimeoutExpired):
                self.skipTest("media encoder unavailable")
            if created.returncode != 0 or not mp4_file.exists():
                self.skipTest("bundled runner ffmpeg lacks mpeg4 encoder")
            edit = {"sources": {
                "audio": {"path": wav_file.name},
                "background": {"path": mp4_file.name}
            }}
            report = inspect_ffprobe(edit, root, ffprobe_exe=Path(FFPROBE).resolve())
            self.assertEqual(report["status"], "NEEDS_REVIEW", report["issues"])
            self.assertEqual(len(report["streams"]), 2)
            by_type = {record["stream_kind"]: record for record in report["streams"]}
            self.assertTrue(by_type["audio"]["codec"].startswith("pcm_"))
            self.assertEqual(by_type["audio"]["sample_rate"], 48000)
            self.assertEqual(by_type["video"]["width"], 64)
            self.assertEqual(by_type["video"]["height"], 64)
            self.assertEqual(by_type["video"]["codec"], "mpeg4")
            self.assertGreaterEqual(by_type["audio"]["duration_ms"], 990)
            self.assertTrue(all(not str(root) in str(i) for i in report["issues"]))
            self.assertFalse(report["can_assemble"])


if __name__ == "__main__":
    unittest.main()
