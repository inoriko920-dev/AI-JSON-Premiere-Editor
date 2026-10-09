"""STEP10 original/cached MP4 overlay: actual file hash + mock FFprobe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.import_snapshot import prepare_media_snapshot
from core.background_overlay import prepare_background_overlay, OverlayError

PNG = (b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4,"big") + b"IHDR" +
       (640).to_bytes(4,"big") + (360).to_bytes(4,"big") + b"\x08\x06\x00\x00\x00")
MP4 = b"\x00\x00\x00\x18ftypisom" + b"video user bytes"
WAV = b"RIFF" + b"\x00"*4 + b"WAVEfmt " + b"\x00"*16
SRT = b"1\n00:00:00,000 --> 00:00:02,000\nDemo\n"


def metadata(audio, *, frames="60", fps="30/1", start="0.000000",
             duration="2.000000", codec="h264", extra_kind=None):
    streams=[{"codec_type":"video","codec_name":codec,
              "width":640,"height":360,"avg_frame_rate":fps,
              "nb_frames":frames,"start_time":start,"duration":duration}]
    if audio:
        streams.append({"codec_type":"audio","codec_name":"aac"})
    if extra_kind:
        streams.append({"codec_type":extra_kind,"codec_name":"weird"})
    return json.dumps({"streams":streams}).encode()


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.input_temp=tempfile.TemporaryDirectory()
        self.cache_temp=tempfile.TemporaryDirectory()
        self.root=Path(self.input_temp.name)
        self.cache=Path(self.cache_temp.name)
        self.original=self.root/"background.mp4"
        self.derived=None
        self.edit={"project_id":"EXAMPLE","sources":{},"assets":{}}
        for key,payload,filename in [
            ("background",MP4,"background.mp4"),
            ("audio",WAV,"narasi.wav"),
            ("srt",SRT,"narasi.srt"),
        ]:
            path=self.root/filename
            path.write_bytes(payload)
            self.edit["sources"][key]={"path":filename,
                 "sha256":hashlib.sha256(payload).hexdigest()}
        (self.root/"assets").mkdir()
        asset=self.root/"assets/A001.png"
        asset.write_bytes(PNG)
        self.edit["assets"]={"A001":{"path":"assets/A001.png",
                                    "sha256":hashlib.sha256(PNG).hexdigest()}}
        self.snapshot=prepare_media_snapshot(
            self.edit,self.root,max_file_bytes=100000,max_import_items=8)
        self.derived=self.cache/(
           "BG_NO_AUDIO_"+self.edit["sources"]["background"]["sha256"][:24]+".mp4")
        self.derived.write_bytes(b"\x00\x00\x00\x18ftypisom"+"cached video".encode())
        self.report={
            "status":"VIDEO_ONLY_CANDIDATE_UNVERIFIED",
            "output_created":True,"can_import":False,"can_assemble":False,
            "audio_streams":0,
            "source_sha256":self.edit["sources"]["background"]["sha256"],
            "sha256":hashlib.sha256(self.derived.read_bytes()).hexdigest(),
            "byte_size":self.derived.stat().st_size,
            "candidate_path":str(self.derived),
        }
        self.ffprobe=self.cache/"ffprobe.exe"
        self.ffprobe.write_bytes(b"MOCK TOOL - NOT EXECUTED")
        self.original_metadata=metadata(True)
        self.derived_metadata=metadata(False)
        self.calls=[]
        self.mutate_on_derived=False

    def tearDown(self):
        self.input_temp.cleanup()
        self.cache_temp.cleanup()

    def runner(self,args,**kwargs):
        self.calls.append((args,kwargs))
        self.assertEqual(args[0],str(self.ffprobe))
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"],20)
        is_derived = Path(args[-1]).resolve() == self.derived.resolve()
        if is_derived and self.mutate_on_derived:
            self.derived.write_bytes(b"CHANGED AFTER PROBE")
        output=(self.derived_metadata if is_derived
                else self.original_metadata)
        return subprocess.CompletedProcess(args,0,output,b"")

    def verify(self,**kwargs):
        return prepare_background_overlay(
            self.edit,self.snapshot,self.report,self.root,self.cache,
            ffprobe_exe=self.ffprobe,max_media_bytes=100000,
            runner=self.runner,**kwargs)

    def test_valid_mp4_video_only_candidate_keeps_original_and_no_host_permission(self):
        before=self.original.read_bytes()
        result=self.verify()
        self.assertEqual(result["status"],"CANDIDATE_NOT_AUTHORIZED")
        self.assertFalse(result["can_assemble"])
        self.assertFalse(result["can_import"])
        self.assertEqual(result["video_frame_count"],60)
        self.assertEqual(len(result["overlay_sha256"]),64)
        self.assertEqual(result["public_summary"]["video_fps"],"30/1")
        self.assertNotIn(str(self.cache),json.dumps(result["public_summary"]))
        self.assertEqual(self.original.read_bytes(),before)
        self.assertEqual(len(self.calls),2)

    def test_overlay_digest_is_stable_and_source_bound(self):
        a,b=self.verify(),self.verify()
        self.assertEqual(a["overlay_sha256"],b["overlay_sha256"])
        self.assertEqual(a["original_inventory_sha256"],
                         self.snapshot["inventory_sha256"])

    def test_malformed_untrusted_snapshot_is_structured_error(self):
        self.snapshot=None
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_REQUEST_INVALID")

    def test_unreadable_ffprobe_utf8_is_structured_error(self):
        self.derived_metadata=b"\xff\xfe"
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_FFPROBE_FAILED")

    def test_wrong_derived_sha_must_fail_before_probing(self):
        self.report["sha256"]="f"*64
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_DERIVED_FILE_INVALID")
        self.assertEqual(self.calls,[])

    def test_original_snapshot_stale_blocks_before_probe(self):
        (self.root/"assets/A001.png").write_bytes(b"CHANGED")
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_ORIGINAL_SNAPSHOT_STALE")
        self.assertEqual(self.calls,[])

    def test_existing_cached_source_claim_cannot_be_import_authorization(self):
        self.report["can_import"]=True
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_ISOLATION_REPORT_INVALID")

    def test_cached_audio_stream_rejected(self):
        self.derived_metadata=metadata(True)
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_AUDIO_TOPOLOGY_INVALID")

    def test_extra_subtitle_stream_rejected(self):
        self.derived_metadata=metadata(False,extra_kind="subtitle")
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_STREAMS_INVALID")

    def test_fps_mismatch_unverified(self):
        self.derived_metadata=metadata(False,fps="30000/1001")
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_FRAME_RATE_UNVERIFIED")

    def test_missing_frame_count_cannot_guess_duration(self):
        self.derived_metadata=metadata(False,frames="N/A")
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_FRAME_COUNT_UNVERIFIED")

    def test_remux_frame_loss_fails_closed(self):
        self.derived_metadata=metadata(False,frames="59")
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_VIDEO_IDENTITY_CHANGED")

    def test_remux_start_and_duration_changes_fail(self):
        for changed in (metadata(False,start="0.040000"),
                        metadata(False,duration="1.960000")):
            self.derived_metadata=changed
            with self.assertRaises(OverlayError) as ex:self.verify()
            self.assertEqual(ex.exception.code,"E_OVERLAY_VIDEO_TIMING_CHANGED")

    def test_mutation_during_probe_fails_even_if_metadata_same(self):
        self.mutate_on_derived=True
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_FILE_CHANGED_DURING_PROBE")

    def test_unsafe_cache_path_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            outside_file=Path(outside)/self.derived.name
            outside_file.write_bytes(self.derived.read_bytes())
            self.report["candidate_path"]=str(outside_file)
            with self.assertRaises(OverlayError) as ex:self.verify()
            self.assertEqual(ex.exception.code,"E_OVERLAY_DERIVED_FILE_INVALID")

    def test_missing_ffprobe_is_error_not_implicit_pass(self):
        with self.assertRaises(OverlayError) as ex:
            prepare_background_overlay(
                self.edit,self.snapshot,self.report,self.root,self.cache,
                ffprobe_exe=None,max_media_bytes=100000,runner=self.runner)
        self.assertEqual(ex.exception.code,"E_OVERLAY_PATH_OR_TOOL_INVALID")

    def test_original_stream_must_have_audio_for_derived_mode(self):
        self.original_metadata=metadata(False)
        with self.assertRaises(OverlayError) as ex:self.verify()
        self.assertEqual(ex.exception.code,"E_OVERLAY_AUDIO_TOPOLOGY_INVALID")


if __name__=="__main__":
    unittest.main()
