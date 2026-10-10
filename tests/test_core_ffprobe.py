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

    def inspect(self, *, payload=None, code=0, execute=None, exe="default",
                include_linked=False):
        def runner(argv, **kwargs):
            self.calls.append((argv, kwargs))
            if execute:
                raise execute
            raw = payload if payload is not None else fixture()
            # Real FFprobe returns one file's streams per invocation, not
            # the combined streams from both narration and background.
            if not include_linked:
                try:
                    decoded = json.loads(raw)
                    if type(decoded) is dict and isinstance(decoded.get("streams"),list):
                        role = "audio" if str(argv[-1]).endswith(".wav") else "video"
                        decoded["streams"] = [
                            s for s in decoded["streams"]
                            if type(s) is dict and s.get("codec_type") == role
                        ]
                        raw = json.dumps(decoded).encode("utf-8")
                except (ValueError, TypeError):
                    pass
            return subprocess.CompletedProcess(argv, code, raw, b"")
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

    def test_background_linked_audio_is_a_hard_error(self):
        mixed = fixture()
        report = self.inspect(payload=mixed, include_linked=True)
        self.assertEqual(report["status"], "PREFLIGHT_FAIL")
        self.assertIn("E_BACKGROUND_AUDIO_NOT_ISOLATED", codes(report))
        self.assertFalse(report["can_assemble"])
        self.assertEqual(len(report["streams"]), 1)  # narration inspected

    def test_background_unknown_side_stream_is_blocking(self):
        mixed = json.loads(fixture())
        mixed["streams"] = [
            {"codec_type":"video","codec_name":"h264","width":1920,"height":1080},
            {"codec_type":"subtitle","codec_name":"mov_text"}
        ]
        report = self.inspect(payload=json.dumps(mixed).encode(), include_linked=True)
        self.assertIn("E_BACKGROUND_STREAM_TOPOLOGY_UNKNOWN",codes(report))
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")

    def test_background_multiple_video_tracks_is_blocking(self):
        v = {"codec_type":"video","codec_name":"h264",
             "width":1920,"height":1080}
        mixed = json.dumps({"streams":[v,v],"format":{"duration":"11.5"}}).encode()
        report = self.inspect(payload=mixed)
        self.assertIn("E_BACKGROUND_VIDEO_STREAM_AMBIGUOUS",codes(report))
        self.assertFalse(report["can_assemble"])

    def test_narration_multiple_audio_streams_never_silently_pick_first(self):
        def runner(argv, **_kwargs):
            audio = str(argv[-1]).endswith(".wav")
            record = ({"codec_type":"audio","codec_name":"pcm_s16le",
                       "sample_rate":"48000"} if audio else
                      {"codec_type":"video","codec_name":"h264",
                       "width":1920,"height":1080})
            payload = {"streams":[record,dict(record)] if audio else [record],
                       "format":{"duration":"11.500"}}
            return subprocess.CompletedProcess(argv,0,json.dumps(payload).encode(),b"")
        report=inspect_ffprobe(self.edit,self.root,ffprobe_exe=self.ffprobe,runner=runner)
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_AUDIO_STREAM_AMBIGUOUS",codes(report))
        self.assertEqual(len(report["streams"]),1)
        self.assertFalse(report["can_assemble"])

    def test_fractional_millisecond_narration_never_truncated_to_valid_timeline(self):
        # STEP33 media metadata must not defeat FIX01's strict audio-tail gate.
        for value in ("11.500001","11.499999"):
            with self.subTest(audio_duration=value):
                def runner(argv, **_kwargs):
                    audio = str(argv[-1]).endswith(".wav")
                    record = ({"codec_type":"audio","codec_name":"pcm_s16le",
                               "sample_rate":"48000"} if audio else
                              {"codec_type":"video","codec_name":"h264",
                               "width":1920,"height":1080})
                    payload = {"streams":[record],
                               "format":{"duration":value if audio else "11.500"}}
                    return subprocess.CompletedProcess(argv,0,json.dumps(payload).encode(),b"")
                report=inspect_ffprobe(self.edit,self.root,
                                       ffprobe_exe=self.ffprobe,runner=runner)
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_DURATION_PRECISION_UNVERIFIED",codes(report))
                self.assertFalse(any(x["pointer"]=="/sources/audio"
                                     for x in report["streams"]))
                self.assertFalse(report["can_assemble"])

    def test_excessively_nested_ffprobe_output_returns_structured_failure(self):
        nested = (b"[" * 6000) + b"0" + (b"]" * 6000)
        self.assertLess(len(nested), 128*1024)
        def runner(argv, **_kwargs):
            raw = nested if str(argv[-1]).endswith(".wav") else fixture()
            return subprocess.CompletedProcess(argv,0,raw,b"")
        report=inspect_ffprobe(self.edit,self.root,ffprobe_exe=self.ffprobe,runner=runner)
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_FFPROBE_BAD_RESPONSE",codes(report))
        self.assertFalse(report["can_assemble"])

    def test_background_video_only_remains_review_not_certified(self):
        # Runner fixture responses for both files are video-only: audio probe
        # correctly rejects missing narration, so test a video-only background
        # with a callable that returns actual source-specific stream records.
        def runner(argv, **_kwargs):
            video = argv[-1].endswith(".mp4")
            payload = ({"streams":[{"codec_type":"video","codec_name":"h264",
                                    "width":1920,"height":1080}],
                        "format":{"duration":"11.5"}} if video else
                       {"streams":[{"codec_type":"audio","codec_name":"pcm_s16le",
                                    "sample_rate":"48000"}],
                        "format":{"duration":"11.5"}})
            return subprocess.CompletedProcess(argv,0,json.dumps(payload).encode(),b"")
        report=inspect_ffprobe(self.edit,self.root,ffprobe_exe=self.ffprobe,runner=runner)
        self.assertEqual(report["status"],"NEEDS_REVIEW",report["issues"])
        self.assertFalse(report["can_assemble"])
        self.assertEqual(len(report["streams"]),2)

    def test_missing_duration_requires_review(self):
        body = fixture().decode().replace('"11.500"', '"N/A"')
        r = self.inspect(payload=body.encode())
        self.assertIn("E_FFPROBE_DURATION_UNVERIFIED", codes(r))
        self.assertTrue(all(x["duration_ms"] is None for x in r["streams"]))

    def test_nonfinite_duration_review(self):
        body = fixture().decode().replace('"11.500"', '"NaN"')
        r = self.inspect(payload=body.encode())
        self.assertIn("E_FFPROBE_DURATION_UNVERIFIED", codes(r))

    def test_narration_precision_beyond_decimal_context_is_not_rounded_off(self):
        # Decimal's default 28 digits would turn this into exactly 11000 ms.
        for value in ("11.00000000000000000000000000001",
                      "10.9999999999999999999999999999",
                      "0.00000000000000000000000000001"):
            with self.subTest(duration=value):
                def runner(argv, **_kwargs):
                    audio = str(argv[-1]).endswith(".wav")
                    record = ({"codec_type":"audio","codec_name":"pcm_s16le",
                               "sample_rate":"48000"} if audio else
                              {"codec_type":"video","codec_name":"h264",
                               "width":1920,"height":1080})
                    data = {"streams":[record],
                            "format":{"duration":value if audio else "11.500"}}
                    return subprocess.CompletedProcess(argv,0,json.dumps(data).encode(),b"")
                report=inspect_ffprobe(self.edit,self.root,
                                       ffprobe_exe=self.ffprobe,runner=runner)
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_DURATION_PRECISION_UNVERIFIED",codes(report))
                self.assertFalse(any(x["pointer"]=="/sources/audio"
                                     for x in report["streams"]))
                self.assertFalse(report["can_assemble"])

    def test_background_fraction_beyond_decimal_context_never_rounds_up(self):
        # Background policy is floor-to-available milliseconds. Near a
        # frame edge, Decimal * 1000 previously rounded 10999.999... to 11000.
        def runner(argv, **_kwargs):
            audio = str(argv[-1]).endswith(".wav")
            record = ({"codec_type":"audio","codec_name":"pcm_s16le",
                       "sample_rate":"48000"} if audio else
                      {"codec_type":"video","codec_name":"h264",
                       "width":1920,"height":1080})
            value = "11.000" if audio else "10.9999999999999999999999999999"
            data={"streams":[record],"format":{"duration":value}}
            return subprocess.CompletedProcess(argv,0,json.dumps(data).encode(),b"")
        report=inspect_ffprobe(self.edit,self.root,ffprobe_exe=self.ffprobe,runner=runner)
        self.assertEqual(report["status"],"NEEDS_REVIEW",report["issues"])
        self.assertEqual([x["duration_ms"] for x in report["streams"]],[11000,10999])
        self.assertFalse(report["can_assemble"])

    def test_millisecond_trailing_zeros_remain_valid_and_unchanged(self):
        value="11.00000000000000000000000000000"
        report=self.inspect(payload=fixture().decode().replace(
            '"11.500"','"'+value+'"').encode())
        self.assertNotIn("E_FFPROBE_DURATION_PRECISION_UNVERIFIED",codes(report))
        self.assertEqual([x["duration_ms"] for x in report["streams"]],[11000,11000])

    def test_extremely_long_sample_rate_returns_error_without_int_crash(self):
        # Python 3.11 rejects int() of thousands of digits; never let
        # malicious metadata escape the structured FFprobe issue protocol.
        raw = fixture().decode().replace('"48000"', '"' + '9'*10000 + '"')
        self.assertLess(len(raw), 128*1024)
        report = self.inspect(payload=raw.encode())
        self.assertEqual(report["status"], "PREFLIGHT_FAIL")
        self.assertIn("E_FFPROBE_SAMPLE_RATE", codes(report))
        self.assertFalse(report["can_assemble"])

    def test_extreme_decimal_exponent_duration_fails_closed(self):
        # Decimal('1e999999999') is finite but converting it to integer
        # milliseconds is not safe. Do not advertise a usable duration.
        for value in ("1e999999999", "1e308"):
            with self.subTest(value=value):
                raw = fixture().decode().replace('"11.500"', '"'+value+'"')
                report = self.inspect(payload=raw.encode())
                self.assertIn("E_FFPROBE_DURATION_UNVERIFIED", codes(report))
                self.assertTrue(all(x["duration_ms"] is None
                                    for x in report["streams"]))
                self.assertFalse(report["can_assemble"])

    def test_supported_sample_rate_and_duration_unchanged(self):
        report = self.inspect()
        self.assertNotIn("E_FFPROBE_SAMPLE_RATE", codes(report))
        self.assertNotIn("E_FFPROBE_DURATION_UNVERIFIED", codes(report))
        self.assertEqual(report["streams"][0]["sample_rate"], 48000)
        self.assertEqual(report["streams"][0]["duration_ms"], 11500)

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
