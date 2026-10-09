"""STEP10 derived V1 worklist binding: no Premiere writes or user files modified."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.import_snapshot import prepare_media_snapshot
from core.background_overlay import prepare_background_overlay
from core.derived_track_binding import bind_derived_v1_candidate,DerivedTrackError

PNG=(b"\x89PNG\r\n\x1a\n"+(13).to_bytes(4,"big")+b"IHDR"+
     (640).to_bytes(4,"big")+(360).to_bytes(4,"big")+b"\x08\x06\x00\x00\x00")
MP4=b"\x00\x00\x00\x18ftypisom"+b"test video original"
WAV=b"RIFF"+b"\x00"*4+b"WAVEfmt "+b"\x00"*16
SRT=b"1\n00:00:00,000 --> 00:00:02,000\nDemo\n"


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.cache_tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.cache=Path(self.cache_tmp.name)
        self.edit={"sources":{},"assets":{}}
        for kind,relative,data in [
            ("srt","narasi.srt",SRT),("audio","narasi.wav",WAV),
            ("background","bg.mp4",MP4),
        ]:
            path=self.root/relative
            path.write_bytes(data)
            self.edit["sources"][kind]={
                "path":relative,"sha256":hashlib.sha256(data).hexdigest()}
        a=self.root/"A001.png";a.write_bytes(PNG)
        self.edit["assets"]["A001"]={
            "path":"A001.png","sha256":hashlib.sha256(PNG).hexdigest()}
        self.snapshot=prepare_media_snapshot(
            self.edit,self.root,max_file_bytes=100000,max_import_items=10)
        bg_hash=self.edit["sources"]["background"]["sha256"]
        self.original=self.root/"bg.mp4"
        self.derived=self.cache/("BG_NO_AUDIO_"+bg_hash[:24]+".mp4")
        self.derived.write_bytes(b"\x00\x00\x00\x18ftypisom"+b"derived video")
        self.report={
            "status":"VIDEO_ONLY_CANDIDATE_UNVERIFIED",
            "output_created":True,"audio_streams":0,
            "can_import":False,"can_assemble":False,
            "source_sha256":bg_hash,
            "sha256":hashlib.sha256(self.derived.read_bytes()).hexdigest(),
            "byte_size":self.derived.stat().st_size,
            "candidate_path":str(self.derived),
        }
        self.exe=self.cache/"ffprobe.exe"
        self.exe.write_bytes(b"fixture binary no execution")
        self.calls=0
        self.overlay=self.revalidate()
        self.plan={"schema_version":"track-placement-candidate-v1",
                   "status":"CANDIDATE_NOT_EXECUTABLE",
                   "can_import":False,"can_assemble":False,
                   "operation_sha256":"a"*64,
                   "media_digest":self.snapshot["inventory_sha256"],
                   "total_frames":130,
                   "track_counts":{"V1":3,"V2":1,"V3":0,"A1":1},
                   "placements":[]}
        for n,(a,b) in enumerate([(0,60),(60,120),(120,130)]):
            self.plan["placements"].append({
                "instance_key":"BG_"+str(n),"item_id":"SOURCE_BACKGROUND",
                "target_track":"V1","source_policy":"BACKGROUND_VIDEO_ONLY_UNVERIFIED",
                "start_frame":a,"end_frame":b,"source_in_frame":0,
                "source_out_frame":b-a,
            })
        self.plan["placements"].append({
            "instance_key":"NARRATION_0","item_id":"SOURCE_AUDIO",
            "target_track":"A1","start_frame":0,"end_frame":130
        })

    def tearDown(self):
        self.tmp.cleanup();self.cache_tmp.cleanup()

    def runner(self,args,**kw):
        self.calls+=1
        original=Path(args[-1]).resolve()==self.original.resolve()
        streams=[{"codec_type":"video","codec_name":"h264","width":640,
                  "height":360,"avg_frame_rate":"30/1",
                  "nb_frames":"60","start_time":"0.000000","duration":"2.000000"}]
        if original:streams.append({"codec_type":"audio","codec_name":"aac"})
        return subprocess.CompletedProcess(args,0,json.dumps({"streams":streams}).encode(),b"")

    def revalidate(self):
        return prepare_background_overlay(
            self.edit,self.snapshot,self.report,self.root,self.cache,
            ffprobe_exe=self.exe,max_media_bytes=100000,runner=self.runner)

    def bind(self):
        return bind_derived_v1_candidate(
            self.plan,self.overlay,self.edit,self.snapshot,self.report,
            self.root,self.cache,ffprobe_exe=self.exe,
            max_media_bytes=100000,runner=self.runner)

    def test_all_v1_segments_use_derived_source_with_exact_requested_trim(self):
        original=copy.deepcopy(self.plan)
        work=self.bind()
        self.assertEqual(work["status"],"CANDIDATE_NOT_EXECUTABLE")
        self.assertFalse(work["can_import"])
        self.assertFalse(work["can_assemble"])
        self.assertEqual(work["v1_clip_count"],3)
        v1=[x for x in work["placements"] if x["target_track"]=="V1"]
        self.assertEqual([x["source_out_frame"] for x in v1],[60,60,10])
        self.assertEqual([x["trim_required"] for x in v1],[False,False,True])
        self.assertTrue(all(x["item_id"]=="DERIVED_SOURCE_BACKGROUND" for x in v1))
        self.assertEqual(self.plan,original,"Never overwrite original worklist")
        self.assertNotIn(str(self.cache),json.dumps(work["public_summary"]))
        self.assertEqual(work["placements"][-1]["item_id"],"SOURCE_AUDIO")

    def test_deterministic_plan_digest(self):
        self.assertEqual(self.bind()["operation_sha256"],self.bind()["operation_sha256"])

    def test_forged_host_ready_plan_rejected(self):
        self.plan["can_assemble"]=True
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_DERIVED_BINDING_INPUT_INVALID")

    def test_stale_overlay_manifest_rejected_after_real_check(self):
        self.overlay["derived_sha256"]="0"*64
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_DERIVED_BINDING_STALE")

    def test_cache_file_changed_rejected(self):
        self.derived.write_bytes(b"altered video")
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_OVERLAY_DERIVED_FILE_INVALID")

    def test_partial_last_bg_loop_cannot_exceed_verified_video_frame_count(self):
        self.plan["placements"][2]["source_out_frame"]=61
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_DERIVED_V1_RANGE_INVALID")

    def test_v1_gap_and_overlap_never_auto_ripple(self):
        self.plan["placements"][1]["start_frame"]=61
        self.plan["placements"][1]["source_out_frame"]=59
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_DERIVED_V1_COVERAGE_INVALID")

    def test_wrong_media_snapshot_digest_rejected(self):
        self.plan["media_digest"]="b"*64
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_DERIVED_BINDING_INPUT_INVALID")

    def test_wrong_track_counts_rejected(self):
        self.plan["track_counts"]["V1"]=2
        with self.assertRaises(DerivedTrackError) as ex:self.bind()
        self.assertEqual(ex.exception.code,"E_DERIVED_TRACK_COUNT_INVALID")

    def test_original_user_audio_and_bg_untouched(self):
        before=self.original.read_bytes()
        work=self.bind()
        self.assertEqual(self.original.read_bytes(),before)
        self.assertEqual((self.root/"narasi.wav").read_bytes(),WAV)
        self.assertNotEqual(work["placements"][0]["item_id"],"SOURCE_BACKGROUND")


if __name__=="__main__":
    unittest.main()
