"""ASTRA FIX01 regression: narration tail and EXACT_CUE timing (offline only)."""
import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest
from core.media import inspect_media
from tests.test_core_media import PNG_HEADER, WAV_HEADER, MP4_HEADER
from core.track_plan import TrackPlanError, compile_four_track_candidate

demo = runpy.run_path(str(Path(__file__).with_name("test_core_contracts.py")))["demo"]


def snapshot(edit):
    return {"schema_version": "verified-media-snapshot-v1",
            "status": "CANDIDATE_NOT_AUTHORIZED", "can_import": False,
            "can_assemble": False, "inventory_sha256": "a"*64,
            "import_count": len(edit["assets"])+2}


class AstraFix01Tests(unittest.TestCase):
    def test_exact_narration_duration_is_a_nonexecutable_candidate(self):
        edit, animation = demo()
        candidate = compile_four_track_candidate(
            edit, animation, ticks_per_frame="8467200000",
            audio_duration_ms=11000, background_duration_ms=6000,
            media_snapshot=snapshot(edit))
        self.assertEqual(candidate["total_frames"], 330)
        self.assertEqual(candidate["status"], "CANDIDATE_NOT_EXECUTABLE")
        self.assertFalse(candidate["can_assemble"])

    def test_audio_tail_cannot_be_silently_discarded(self):
        edit, animation = demo()
        for duration, expected in ((12000, "E_TRACK_NARRATION_TOO_LONG"),
                                   (11001, "E_TRACK_NARRATION_TOO_LONG"),
                                   (10999, "E_TRACK_NARRATION_TOO_SHORT")):
            with self.subTest(duration=duration):
                with self.assertRaises(TrackPlanError) as ctx:
                    compile_four_track_candidate(
                        edit, animation, ticks_per_frame="8467200000",
                        audio_duration_ms=duration, background_duration_ms=6000,
                        media_snapshot=snapshot(edit))
                self.assertEqual(ctx.exception.code, expected)

    def inspect_with_cue(self, cue_start_ms, instance_start_frame):
        edit, _ = demo()
        edit["scenes"] = edit["scenes"][:1]
        edit["scenes"][0]["assets"][0]["start_frame"] = instance_start_frame
        raw = ("1\\n00:00:{:02d},{:03d} --> 00:00:10,000\\nExisting cue\\n".format(
            cue_start_ms // 1000, cue_start_ms % 1000)).encode().replace(b"\\n", b"\n")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            edit["sources"]["srt"]["path"] = "sub.srt"
            source_data = {"srt": raw, "audio": WAV_HEADER,
                           "background": MP4_HEADER}
            for kind, blob in source_data.items():
                record = edit["sources"][kind]
                target = root / record["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(blob)
                record["sha256"] = hashlib.sha256(blob).hexdigest()
            for record in edit["assets"].values():
                target = root / record["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(PNG_HEADER)
                record["sha256"] = hashlib.sha256(PNG_HEADER).hexdigest()
            return inspect_media(edit, root, max_file_bytes=4096,
                                 max_srt_cues=10)

    def test_exact_cue_must_match_instance_entry(self):
        report = self.inspect_with_cue(9000, 0)
        self.assertEqual(report["status"], "PREFLIGHT_FAIL")
        self.assertIn("E_SRT_CUE_FRAME_MISMATCH",
                      [x["code"] for x in report["issues"]])

    def test_exact_cue_correct_and_round_half_up_50ms(self):
        for ms, frame in ((0, 0), (50, 2)):
            with self.subTest(ms=ms):
                report = self.inspect_with_cue(ms, frame)
                self.assertNotIn("E_SRT_CUE_FRAME_MISMATCH",
                                 [x["code"] for x in report["issues"]
                                  if x["severity"] == "ERROR"])
                self.assertEqual(report["status"], "NEEDS_REVIEW")
                self.assertFalse(report["can_assemble"])


if __name__ == "__main__":
    unittest.main()
