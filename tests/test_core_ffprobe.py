"""Mocked FFprobe metadata tests. No network, no real Premiere, no images."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.ffprobe import inspect_ffprobe


def fixture(audio=True, background=True, codec="h264"):
    streams = ([{"codec_type": "audio", "codec_name": "pcm_s16le",
                 "sample_rate": "48000", "channels": 2}] if audio else [])
    streams += ([{"codec_type": "video", "codec_name": codec, "width": 1920,
                  "height": 1080}] if background else [])
    return json.dumps({"streams": streams, "format": {"duration": "11.500"}}).encode()


def codes(report):
    return [x["code"] for x in report["issues"]]


class FFProbeTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.root = Path(self.work.name)
        self.ffprobe = self.root / "ffprobe.exe"
        self.ffprobe.write_bytes(b"no executable launched in unit tests")
        (self.root / "audio.wav").write_bytes(b"test")
        (self.root / "background.mp4").write_bytes(b"test")
        self.edit = {"sources": {
            "audio": {"path": "audio.wav"},
            "background": {"path": "background.mp4"}}}
        self.calls = []

    def tearDown(self):
        self.work.cleanup()

    def inspect(self, *, payload=None, code=0, execute=None, exe="default"):
        def runner(argv, **kwargs):
            self.calls.append((argv, kwargs))
            if execute:
                raise execute
            return subprocess.CompletedProcess(argv, code,
                payload if payload is not None else fixture(), b"")
        return inspect_ffprobe(self.edit, self.root,
            ffprobe_exe=self.ffprobe if exe == "default" else exe,
            runner=runner)

    def test_valid_audio_and_video_metadata_not_host_ready(self):
        r = self.inspect()
        self.assertEqual(r["status"], "NEEDS_REVIEW")
        self.assertFalse(r["can_assemble"])
        self.assertEqual(len(r["streams"]), 2)
        self.assertEqual(r["streams"][0]["codec"], "pcm_s16le")
        self.assertEqual(r["streams"][1]["duration_ms"], 11500)
        self.assertIn("E_DECODE_PREMIERE_UNVERIFIED", codes(r))
        self.assertEqual(len(self.calls), 2)
        for args, kwargs in self.calls:
            self.assertFalse(kwargs["shell"])
            self.assertEqual(kwargs["timeout"], 12)
            self.assertEqual(args[0], str(self.ffprobe))
            self.assertEqual(args[1:3], ["-v", "error"])

    def test_no_executable_is_review_not_fake_verified(self):
        r = self.inspect(exe=None)
        self.assertIn("E_FFPROBE_UNAVAILABLE", codes(r))
        self.assertEqual(self.calls, [])

    def test_untrusted_binary_path_fails_before_exec(self):
        for val in (Path("ffprobe.exe"), self.root / "other.exe"):
            r = self.inspect(exe=val)
            self.assertIn("E_FFPROBE_PATH", codes(r))
        self.assertFalse(self.calls)

    def test_process_timeout_and_errors_fail(self):
        self.assertIn("E_FFPROBE_TIMEOUT", codes(
            self.inspect(execute=subprocess.TimeoutExpired(["ffprobe"], 12))))
        self.assertIn("E_FFPROBE_EXEC_FAILED", codes(
            self.inspect(execute=OSError("not present"))))

    def test_malformed_oversized_or_nonzero_ffprobe_refused(self):
        for data, rc in ((b"{bad", 0), (b"x" * 140000, 0),
                         (fixture(), 1), (b"[]", 0)):
            r = self.inspect(payload=data, code=rc)
            self.assertIn("E_FFPROBE_BAD_RESPONSE", codes(r))

    def test_missing_audio_or_video_stream_fails(self):
        r = self.inspect(payload=fixture(audio=False))
        self.assertIn("E_FFPROBE_STREAM_MISSING", codes(r))
        r = self.inspect(payload=fixture(background=False))
        self.assertIn("E_FFPROBE_STREAM_MISSING", codes(r))

    def test_codec_unknown_needs_review_not_override(self):
        r = self.inspect(payload=fixture(codec="unknown_new_video"))
        self.assertIn("E_VIDEO_CODEC_REVIEW", codes(r))
        self.assertEqual(r["status"], "NEEDS_REVIEW")

    def test_missing_duration_requires_review(self):
        body = fixture().decode().replace('"11.500"', '"N/A"')
        r = self.inspect(payload=body.encode())
        self.assertIn("E_FFPROBE_DURATION_UNVERIFIED", codes(r))
        self.assertTrue(all(x["duration_ms"] is None for x in r["streams"]))

    def test_nonfinite_duration_review(self):
        body = fixture().decode().replace('"11.500"', '"NaN"')
        r = self.inspect(payload=body.encode())
        self.assertIn("E_FFPROBE_DURATION_UNVERIFIED", codes(r))

    def test_absent_media_raises_structured_not_host_status(self):
        (self.root / "background.mp4").unlink()
        r = self.inspect()
        self.assertIn("E_MEDIA_MISSING", codes(r))
        self.assertEqual(r["status"], "PREFLIGHT_FAIL")

    def test_dimensions_or_sample_rate_invalid(self):
        bad = fixture().decode().replace('"width": 1920', '"width": 0')
        self.assertIn("E_FFPROBE_DIMENSIONS",
                      codes(self.inspect(payload=bad.encode())))
        bad = fixture().decode().replace('"48000"', '"NaN"')
        self.assertIn("E_FFPROBE_SAMPLE_RATE",
                      codes(self.inspect(payload=bad.encode())))

if __name__ == "__main__":
    unittest.main()
