"""STEP08 offline preflight with real temporary file bytes and mocked FFprobe.

The FFprobe metadata process is mocked to keep CI independent of binaries;
file SHA, SRT, root confinement and rehash are REAL filesystem operations.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from core.import_snapshot import prepare_media_snapshot
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

    def test_snapshot_authority_tampering_blocks_before_ffprobe(self):
        original=prepare_media_snapshot(
            self.edit,self.root,max_file_bytes=100000,
            max_import_items=20)
        for key,value in (("status","READY"),
                          ("can_assemble",True),
                          ("can_import",True),
                          ("import_count",0)):
            with self.subTest(field=key):
                forged=dict(original)
                forged[key]=value
                with patch("core.track_preflight.prepare_media_snapshot",
                           return_value=forged):
                    report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_MEDIA_SNAPSHOT_STALE",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_assemble"])
                self.assertEqual(self.probe_calls,0)

    def test_snapshot_mutation_during_ffprobe_blocks_candidate(self):
        path=self.root/self.edit["assets"]["A001"]["path"]
        self.mutate_during_probe=lambda:path.write_bytes(b"tampered png")
        report=self.check()
        self.assertIn("E_MEDIA_SNAPSHOT_STALE",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_same_bytes_same_mtime_audio_swap_during_ffprobe_blocks_candidate(self):
        # Rechecking only SHA/size/mtime cannot detect an identical file
        # replacement while FFprobe is running. It must bind the original
        # source identity from STEP06's non-authorizing snapshot.
        audio=self.root/self.edit["sources"]["audio"]["path"]
        before=audio.stat()
        payload=audio.read_bytes()
        def replace_identical_audio():
            replacement=self.root/"snapshot-swap-audio.wav"
            replacement.write_bytes(payload)
            os.utime(replacement,ns=(before.st_atime_ns,before.st_mtime_ns))
            os.replace(replacement,audio)
        self.mutate_during_probe=replace_identical_audio
        report=self.check()
        after=audio.stat()
        self.assertEqual(audio.read_bytes(),payload)
        self.assertEqual(before.st_size,after.st_size)
        self.assertEqual(before.st_mtime_ns,after.st_mtime_ns)
        self.assertNotEqual((before.st_dev,before.st_ino,before.st_ctime_ns),
                            (after.st_dev,after.st_ino,after.st_ctime_ns))
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_MEDIA_SNAPSHOT_STALE",codes(report))
        self.assertIsNone(report["track_candidate"])
        self.assertFalse(report["can_assemble"])

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



    def test_invalid_narration_channels_block_four_track_candidate(self):
        original=self.runner
        for channels in (0, -1, False, "2"):
            with self.subTest(channels=channels):
                def with_invalid_channels(args,**kwargs):
                    response=original(args,**kwargs)
                    if Path(args[-1]).suffix.lower()==".wav":
                        payload=json.loads(response.stdout)
                        payload["streams"][0]["channels"]=channels
                        return subprocess.CompletedProcess(
                            args,0,json.dumps(payload).encode("utf-8"),b"")
                    return response
                self.runner=with_invalid_channels
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_CHANNELS",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_import"])
                self.assertFalse(report["can_assemble"])

    def test_multiple_narration_streams_block_track_before_timeline_candidate(self):
        original=self.runner
        def ambiguous(args,**options):
            output=original(args,**options)
            if Path(args[-1]).suffix.lower()==".wav":
                body=json.loads(output.stdout)
                body["streams"].append(dict(body["streams"][0]))
                output=subprocess.CompletedProcess(args,0,json.dumps(body).encode(),b"")
            return output
        self.runner=ambiguous
        report=self.check()
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_AUDIO_STREAM_AMBIGUOUS",codes(report))
        self.assertIsNone(report["track_candidate"])
        self.assertFalse(report["can_assemble"])

    def test_fractional_millisecond_narration_blocks_track_candidate(self):
        original=self.runner
        for value in ("11.000001","10.999999"):
            with self.subTest(duration_seconds=value):
                def fractional(args,**options):
                    output=original(args,**options)
                    if Path(args[-1]).suffix.lower()==".wav":
                        body=json.loads(output.stdout)
                        body["format"]["duration"]=value
                        output=subprocess.CompletedProcess(args,0,json.dumps(body).encode(),b"")
                    return output
                self.runner=fractional
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_DURATION_PRECISION_UNVERIFIED",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_assemble"])

    def test_invalid_large_ffprobe_numbers_cannot_create_track_candidate(self):
        original=self.runner
        for kind in ("sample_rate", "duration"):
            with self.subTest(kind=kind):
                def hostile(args,**options):
                    output=original(args,**options)
                    if Path(args[-1]).suffix.lower()==".wav":
                        payload=json.loads(output.stdout)
                        if kind=="sample_rate":
                            payload["streams"][0]["sample_rate"]="9"*10000
                        else:
                            payload["format"]["duration"]="1e999999999"
                        return subprocess.CompletedProcess(
                            args,0,json.dumps(payload).encode("utf-8"),b"")
                    return output
                self.runner=hostile
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_assemble"])
                expected=("E_FFPROBE_SAMPLE_RATE" if kind=="sample_rate" else
                          "E_FFPROBE_DURATION_UNVERIFIED")
                self.assertIn(expected,codes(report))

    def test_background_just_short_of_11_seconds_requires_two_real_source_loops(self):
        # 10.999999999... seconds cannot supply 330 whole frames at 30fps;
        # rounding to 11000 ms would silently request a nonexistent frame.
        original=self.runner
        def near_boundary(args,**kwargs):
            output=original(args,**kwargs)
            if Path(args[-1]).suffix.lower()==".mp4":
                data=json.loads(output.stdout)
                data["format"]["duration"]="10.9999999999999999999999999999"
                return subprocess.CompletedProcess(
                    args,0,json.dumps(data).encode("utf-8"),b"")
            return output
        self.runner=near_boundary
        report=self.check()
        self.assertEqual(report["status"],"NEEDS_REVIEW",report["issues"])
        self.assertEqual(report["error_count"],0)
        self.assertEqual(report["track_candidate"]["track_counts"]["V1"],2)
        self.assertFalse(report["can_assemble"])

    def test_audio_microtail_never_reaches_four_track_candidate(self):
        original=self.runner
        def microtail(args,**kwargs):
            output=original(args,**kwargs)
            if Path(args[-1]).suffix.lower()==".wav":
                data=json.loads(output.stdout)
                data["format"]["duration"]="11.00000000000000000000000000001"
                return subprocess.CompletedProcess(
                    args,0,json.dumps(data).encode("utf-8"),b"")
            return output
        self.runner=microtail
        report=self.check()
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_FFPROBE_DURATION_PRECISION_UNVERIFIED",codes(report))
        self.assertIsNone(report["track_candidate"])
        self.assertFalse(report["can_assemble"])

    def test_numeric_json_microtail_blocks_four_track_preflight(self):
        original=self.runner
        def numeric_microtail(args, **kwargs):
            response=original(args,**kwargs)
            if Path(args[-1]).suffix.lower()==".wav":
                payload=response.stdout.replace(
                    b'"duration": "11.000"',
                    b'"duration": 11.00000000000000000000000000001')
                self.assertNotEqual(payload,response.stdout)
                return subprocess.CompletedProcess(args,0,payload,b"")
            return response
        self.runner=numeric_microtail
        report=self.check()
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_FFPROBE_DURATION_PRECISION_UNVERIFIED",codes(report))
        self.assertIsNone(report["track_candidate"])
        self.assertFalse(report["can_assemble"])

    def test_duplicate_ffprobe_duration_member_blocks_four_track(self):
        original=self.runner
        for suffix in (".wav", ".mp4"):
            with self.subTest(source_suffix=suffix):
                def ambiguous(args,**kwargs):
                    response=original(args,**kwargs)
                    if Path(args[-1]).suffix.lower()==suffix:
                        value=(b'"duration": "11.000"' if suffix==".wav"
                               else b'"duration": "6.000"')
                        changed=response.stdout.replace(
                            value,value[:-1]+b', "duration": "1.000"')
                        self.assertNotEqual(changed,response.stdout)
                        return subprocess.CompletedProcess(args,0,changed,b"")
                    return response
                self.runner=ambiguous
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_BAD_RESPONSE",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_import"])
                self.assertFalse(report["can_assemble"])
                self.runner=original

    def test_container_stream_duration_conflict_blocks_track_candidate(self):
        original=self.runner
        for extension in (".wav", ".mp4"):
            with self.subTest(extension=extension):
                def mismatched(args, **kwargs):
                    response=original(args,**kwargs)
                    if Path(args[-1]).suffix.lower()==extension:
                        payload=json.loads(response.stdout)
                        # The container claims a full source while its only
                        # selected stream is materially shorter.
                        payload["streams"][0]["duration"]="1.000"
                        return subprocess.CompletedProcess(
                            args,0,json.dumps(payload).encode("utf-8"),b"")
                    return response
                self.runner=mismatched
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_DURATION_CONFLICT",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_import"])
                self.assertFalse(report["can_assemble"])

    def test_narration_with_cover_art_or_data_stream_blocks_four_tracks(self):
        original=self.runner
        for added in ({"codec_type":"video","codec_name":"mjpeg"},
                      {"codec_type":"data","codec_name":"bin_data"}):
            with self.subTest(extra_stream=added["codec_type"]):
                def with_side_stream(args,**options):
                    output=original(args,**options)
                    if Path(args[-1]).suffix.lower()==".wav":
                        data=json.loads(output.stdout)
                        data["streams"].append(added)
                        return subprocess.CompletedProcess(
                            args,0,json.dumps(data).encode("utf-8"),b"")
                    return output
                self.runner=with_side_stream
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_NARRATION_STREAM_TOPOLOGY_UNKNOWN",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_import"])
                self.assertFalse(report["can_assemble"])

    def test_unrepresentable_ffprobe_json_exponent_blocks_four_track(self):
        original=self.runner
        for suffix in (".wav", ".mp4"):
            with self.subTest(source_suffix=suffix):
                def broken_probe(args, **kwargs):
                    response=original(args,**kwargs)
                    if Path(args[-1]).suffix.lower()==suffix:
                        payload=response.stdout.replace(
                            b'"duration": "11.000"' if suffix==".wav"
                            else b'"duration": "6.000"',
                            b'"duration": 1e99999999999999999999999999999')
                        self.assertNotEqual(payload,response.stdout)
                        return subprocess.CompletedProcess(args,0,payload,b"")
                    return response
                self.runner=broken_probe
                report=self.check()
                self.assertEqual(report["status"],"PREFLIGHT_FAIL")
                self.assertIn("E_FFPROBE_BAD_RESPONSE",codes(report))
                self.assertIsNone(report["track_candidate"])
                self.assertFalse(report["can_import"])
                self.assertFalse(report["can_assemble"])
                # A malformed number may not authorize any host action.
                self.runner=original

    def test_audio_bearing_background_never_yields_timeline_candidate(self):
        original=self.runner
        def with_linked_audio(argv,**kwargs):
            output=original(argv,**kwargs)
            if Path(argv[-1]).suffix.lower()==".mp4":
                payload=json.loads(output.stdout)
                payload["streams"].append({"codec_type":"audio","codec_name":"aac",
                                           "sample_rate":"48000"})
                return subprocess.CompletedProcess(argv,0,json.dumps(payload).encode(),b"")
            return output
        self.runner=with_linked_audio
        report=self.check()
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_BACKGROUND_AUDIO_NOT_ISOLATED",codes(report))
        self.assertIsNone(report["track_candidate"])

    def test_unknown_background_auxiliary_stream_blocks_candidate(self):
        original=self.runner
        def with_data(argv,**kwargs):
            output=original(argv,**kwargs)
            if Path(argv[-1]).suffix.lower()==".mp4":
                payload=json.loads(output.stdout)
                payload["streams"].append({"codec_type":"data","codec_name":"bin_data"})
                return subprocess.CompletedProcess(argv,0,json.dumps(payload).encode(),b"")
            return output
        self.runner=with_data
        report=self.check()
        self.assertIn("E_BACKGROUND_STREAM_TOPOLOGY_UNKNOWN",codes(report))
        self.assertIsNone(report["track_candidate"])

if __name__=="__main__":
    unittest.main()
