"""STEP08 offline preflight with real temporary file bytes and mocked FFprobe.

The FFprobe metadata process is mocked to keep CI independent of binaries;
file SHA, SRT, root confinement and rehash are REAL filesystem operations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

from core.track_preflight import prepare_track_preflight


ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]
PNG=(b"\x89PNG\r\n\x1a\n"+(13).to_bytes(4,"big")+b"IHDR"+
     (960).to_bytes(4,"big")+(540).to_bytes(4,"big")+b"\x08\x06\x00\x00\x00")
WAV=b"RIFF"+b"\x00"*4+b"WAVEfmt "+b"\x00"*16
MP4=b"\x00\x00\x00\x18ftypisom"+b"\x00"*20
SRT=(b"1\n00:00:00,000 --> 00:00:05,000\nFirst\n\n"
     b"2\n00:00:05,000 --> 00:00:06,400\nSecond\n\n"
     b"3\n00:00:06,400 --> 00:00:11,000\nThird\n")


def codes(report):
    return {x["code"] for x in report["issues"]}


class TrackPreflightTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.root=Path(self.dir.name)
        self.ffprobe=self.root/"ffprobe.exe"
        self.ffprobe.write_bytes(b"mock-only executable name")
        self.edit,self.animation=demo()
        def pinned(relative: str, data: bytes) -> str:
            path=self.root/relative
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
            return hashlib.sha256(data).hexdigest()
        for role,data in (("srt",SRT),("audio",WAV),("background",MP4)):
            src=self.edit["sources"][role]
            src["sha256"]=pinned(src["path"],data)
        for ref in self.edit["assets"].values():
            ref["sha256"]=pinned(ref["path"],PNG)
        self.probe_calls=0
        self.mutate_during_probe=None

    def tearDown(self):
        self.dir.cleanup()

    def runner(self, args, **options):
        self.probe_calls+=1
        if self.mutate_during_probe:
            self.mutate_during_probe()
            self.mutate_during_probe=None
        is_audio=Path(args[-1]).suffix.lower()==".wav"
        stream=({"codec_type":"audio","codec_name":"pcm_s16le",
                 "sample_rate":"48000"} if is_audio else
                {"codec_type":"video","codec_name":"h264",
                 "width":1920,"height":1080})
        seconds="11.000" if is_audio else "6.000"
        return subprocess.CompletedProcess(args,0,json.dumps({
            "streams":[stream],"format":{"duration":seconds}
        }).encode("utf-8"),b"")

    def check(self, *, ticks="8467200000", exe="valid", **limits):
        return prepare_track_preflight(
            self.edit,self.animation,self.root,
            ffprobe_exe=self.ffprobe if exe=="valid" else exe,
            ticks_per_frame=ticks,max_media_bytes=limits.get("max_bytes",100000),
            max_srt_cues=limits.get("max_cues",20),
            max_import_items=limits.get("max_import",20),
            ffprobe_runner=self.runner
        )

    def test_valid_actual_files_and_probe_generate_exact_four_track_summary(self):
        report=self.check()
        self.assertEqual(report["status"],"NEEDS_REVIEW")
        self.assertFalse(report["can_import"])
        self.assertFalse(report["can_assemble"])
        self.assertEqual(report["error_count"],0,report["issues"])
        self.assertEqual(self.probe_calls,2)
        candidate=report["track_candidate"]
        self.assertEqual(candidate["status"],"CANDIDATE_NOT_EXECUTABLE")
        self.assertFalse(candidate["can_assemble"])
        self.assertEqual(candidate["total_frames"],330)
        self.assertEqual(candidate["track_counts"],{"V1":2,"V2":2,"V3":1,"A1":1})
        self.assertEqual(len(candidate["operation_sha256"]),64)
        self.assertIn("E_HOST_AND_FX_UNVERIFIED",codes(report))
        self.assertNotIn(str(self.root),json.dumps(report))
        self.assertNotIn("absolute_path",json.dumps(report))

    def test_consistent_digest_is_stable(self):
        a=self.check()["track_candidate"]["operation_sha256"]
        b=self.check()["track_candidate"]["operation_sha256"]
        self.assertEqual(a,b)

    def test_missing_real_file_fails_before_ffprobe(self):
        (self.root/self.edit["sources"]["srt"]["path"]).unlink()
        report=self.check()
        self.assertIn("E_MEDIA_MISSING",codes(report))
        self.assertIsNone(report["track_candidate"])
        self.assertEqual(self.probe_calls,0)

    def test_invalid_contract_never_reads_media(self):
        self.animation["mode"]="IN_ONLY"
        report=self.check()
        self.assertIn("E_ANIM_MODE",codes(report))
        self.assertEqual(self.probe_calls,0)

    def test_unsupported_fast_requires_review_before_draft(self):
        self.animation["decisions"][0]["speed"]="FAST"
        report=self.check()
        self.assertIn("E_FX_SPEED_UNCALIBRATED",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_unpinned_background_hash_fails(self):
        del self.edit["sources"]["background"]["sha256"]
        report=self.check()
        self.assertIn("E_MEDIA_HASH_UNPINNED",codes(report))
        self.assertEqual(self.probe_calls,0)

    def test_no_ffprobe_does_not_infer_media_duration(self):
        report=self.check(exe=None)
        self.assertIn("E_FFPROBE_UNAVAILABLE",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_no_host_ticks_cannot_generate_candidate(self):
        report=self.check(ticks=None)
        self.assertEqual(report["status"],"NEEDS_REVIEW")
        self.assertIn("E_HOST_TIMEBASE_UNVERIFIED",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_wrong_ticks_rejected_no_host_success(self):
        report=self.check(ticks="0")
        self.assertIn("E_TRACK_CANDIDATE_REJECTED",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_snapshot_mutation_during_ffprobe_blocks_candidate(self):
        path=self.root/self.edit["assets"]["A001"]["path"]
        self.mutate_during_probe=lambda:path.write_bytes(b"tampered png")
        report=self.check()
        self.assertIn("E_MEDIA_SNAPSHOT_STALE",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_unresolved_srt_reference_blocks_before_probe(self):
        self.edit["scenes"][0]["assets"][0]["entry_evidence"]["cue_id"]=999
        report=self.check()
        self.assertIn("E_SRT_AMBIGUOUS",codes(report))
        self.assertEqual(self.probe_calls,0)

    def test_zero_development_resource_budget_rejected(self):
        report=self.check(max_bytes=0)
        self.assertIn("E_CONFIG_LIMITS_UNVERIFIED",codes(report))
        self.assertEqual(self.probe_calls,0)

    def test_very_short_narration_rejected(self):
        original=self.runner
        def short(args,**options):
            output=original(args,**options)
            if Path(args[-1]).suffix.lower()==".wav":
                obj=json.loads(output.stdout)
                obj["format"]["duration"]="10.000"
                output=subprocess.CompletedProcess(args,0,json.dumps(obj).encode(),b"")
            return output
        self.runner=short
        report=self.check()
        self.assertIn("E_TRACK_CANDIDATE_REJECTED",codes(report))


if __name__=="__main__":
    unittest.main()
