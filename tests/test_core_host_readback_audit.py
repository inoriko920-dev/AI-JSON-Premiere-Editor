"""STEP14 readback receipt comparison; no Adobe host or project mutation."""
from __future__ import annotations
import copy
import unittest
from core.host_readback_audit import audit_prefix

SEQ="aaaa1111-bbbb-2222-cccc-333333333333"
TB="8467200000"


def candidate():
    raw=[("BG_0","SOURCE_BACKGROUND","V1",0,180),
         ("V001/A001","ASSET_A001","V2",0,150),
         ("NARRATION_0","SOURCE_AUDIO","A1",0,330),
         ("V002/A002","ASSET_A002","V2",150,330),
         ("BG_1","SOURCE_BACKGROUND","V1",180,330),
         ("V002/A003","ASSET_A003","V3",192,330)]
    ix={"V1":0,"V2":1,"V3":2,"A1":0}
    placements=[]
    for key,item,track,start,end in raw:
        placements.append({
          "instance_key":key, "item_id":item, "target_track":track,
          "zero_based_track_index":ix[track],
          "start_frame":start, "end_frame":end,
          "source_in_frame":0, "source_out_frame":end-start,
          "start_ticks":str(start*int(TB)), "end_ticks":str(end*int(TB))
        })
    return {"schema_version":"track-placement-candidate-v1",
       "status":"CANDIDATE_NOT_EXECUTABLE","can_import":False,
       "can_assemble":False,"operation_sha256":"a"*64,
       "ticks_per_frame":TB,"placements":placements}


def mapping():
    return {"SOURCE_BACKGROUND":"node-background",
            "SOURCE_AUDIO":"node-audio",
            "ASSET_A001":"node-001","ASSET_A002":"node-002",
            "ASSET_A003":"node-003"}


def make_observed(plan, index):
    tracks={"V1":[],"V2":[],"V3":[],"A1":[]}
    ref=mapping()
    for i,item in enumerate(plan["placements"][:index+1]):
        start=item["start_frame"];end=item["end_frame"]
        tr=item["target_track"]
        tracks[tr].append({
            "clip_id":f"clip-{i+1}","item_node_id":ref[item["item_id"]],
            "start_ticks":str(start*int(TB)),
            "end_ticks":str(end*int(TB)),
            "source_in_ticks":"0",
            "source_out_ticks":str((end-start)*int(TB))})
    return {"schema_version":"premiere-track-readback-v1",
        "status":"CAPTURED_UNVERIFIED","can_assemble":False,
        "sequence_id":SEQ,"ticks_per_frame":TB,"tracks":tracks}


class ReadbackAuditTests(unittest.TestCase):
    def run_audit(self, index=5, tweak=None, plan=None, ref=None):
        plan=plan or candidate()
        observed=make_observed(plan,index)
        if tweak is not None:tweak(observed)
        return audit_prefix(plan,observed,ref or mapping(),
                            operation_index=index,sequence_id=SEQ,
                            max_operations=20)

    def test_full_six_clip_audio_background_visuals_match_not_host_verified(self):
        r=self.run_audit()
        self.assertEqual(r["status"],"READBACK_MATCHED_UNVERIFIED")
        self.assertEqual(r["matched_clip_count"],6)
        self.assertFalse(r["host_verified"])
        self.assertFalse(r["can_assemble"])
        self.assertFalse(r["can_retry"])

    def test_zero_baseline_and_per_operation_prefix(self):
        self.assertEqual(self.run_audit(index=-1)["matched_clip_count"],0)
        self.assertEqual(self.run_audit(index=0)["matched_clip_count"],1)
        self.assertEqual(self.run_audit(index=2)["matched_clip_count"],3)

    def test_unexpected_linked_video_and_audio_detected(self):
        for tr in ("V3","A1"):
            r=self.run_audit(index=0,tweak=lambda obs,t=tr:
                obs["tracks"][t].append({
                 "clip_id":"linked","item_node_id":"node-001",
                 "start_ticks":"0","end_ticks":TB,
                 "source_in_ticks":"0","source_out_ticks":TB
                }))
            self.assertEqual(r["code"],"E_READBACK_CLIP_COUNT_MISMATCH")

    def test_wrong_source_outpoint_rejected(self):
        r=self.run_audit(tweak=lambda x:x["tracks"]["V1"][1].update(
            source_out_ticks=str(151*int(TB))))
        self.assertEqual(r["code"],"E_READBACK_SOURCE_TRIM_MISMATCH")

    def test_missing_or_extra_clip_rejected(self):
        r=self.run_audit(tweak=lambda x:x["tracks"]["V2"].pop())
        self.assertEqual(r["code"],"E_READBACK_CLIP_COUNT_MISMATCH")

    def test_clip_media_identity_mismatch(self):
        r=self.run_audit(tweak=lambda x:x["tracks"]["V2"][0].update(
            item_node_id="node-wrong"))
        self.assertEqual(r["code"],"E_READBACK_MEDIA_ID_MISMATCH")

    def test_wrong_start_or_end_time_rejected(self):
        r=self.run_audit(tweak=lambda x:x["tracks"]["A1"][0].update(
            end_ticks=str(331*int(TB))))
        self.assertEqual(r["code"],"E_READBACK_SEQUENCE_TIMING_MISMATCH")

    def test_sequence_identity_or_timebase_mismatch_rejected(self):
        for name,value,code in (("sequence_id",SEQ.upper().replace("A","B"),
                                  "E_READBACK_SEQUENCE_MISMATCH"),
                                 ("ticks_per_frame","1","E_READBACK_TIMEBASE_MISMATCH")):
            r=self.run_audit(tweak=lambda o,n=name,v=value:o.update({n:v}))
            self.assertEqual(r["code"],code)

    def test_unexpected_track_and_missing_track_rejected(self):
        for op in (lambda o:o["tracks"].update(V4=[]),
                   lambda o:o["tracks"].pop("A1")):
            self.assertEqual(self.run_audit(tweak=op)["code"],
                             "E_READBACK_TRACK_SET_INVALID")

    def test_duplicate_clip_id_and_malformed_tick_refused(self):
        self.assertEqual(self.run_audit(tweak=lambda o:o["tracks"]["V2"][0].update(
            clip_id=o["tracks"]["V1"][0]["clip_id"]))["code"],
            "E_READBACK_CLIP_INVALID")
        self.assertEqual(self.run_audit(tweak=lambda o:o["tracks"]["V1"][0].update(
            start_ticks="0.0"))["code"],"E_READBACK_CLIP_INVALID")

    def test_tampered_plan_and_type_coercion_refused(self):
        p=candidate();p["placements"][0]["end_frame"]=181
        self.assertEqual(self.run_audit(plan=p)["code"],
                         "E_READBACK_PLAN_TIMING_INVALID")
        p=candidate();p["placements"][0]["source_out_frame"]=True
        self.assertEqual(self.run_audit(plan=p)["code"],
                         "E_READBACK_PLAN_TIMING_INVALID")
        p=candidate();p["can_assemble"]=True
        self.assertEqual(self.run_audit(plan=p)["code"],
                         "E_READBACK_PLAN_INVALID")

    def test_malicious_unhashable_track_is_structured_mismatch_not_crash(self):
        p=candidate()
        observed=make_observed(p,5)
        p["placements"][0]["target_track"]=["V1"]
        result=audit_prefix(p,observed,mapping(),operation_index=5,
                            sequence_id=SEQ,max_operations=20)
        self.assertEqual(result["status"],"READBACK_MISMATCH")
        self.assertEqual(result["code"],"E_READBACK_PLAN_INVALID")

    def test_boolean_track_index_is_not_zero(self):
        p=candidate()
        p["placements"][0]["zero_based_track_index"]=False
        result=self.run_audit(plan=p)
        self.assertEqual(result["code"],"E_READBACK_PLAN_TIMING_INVALID")

    def test_no_evidence_or_overly_many_operations_refused(self):
        self.assertEqual(self.run_audit(ref={"SOURCE_AUDIO":"node-audio"})["code"],
                         "E_READBACK_PLAN_INVALID")
        r=self.run_audit(index=5)
        self.assertNotIn("absolute_path",repr(r))
        self.assertNotIn("node-",repr(r))
        self.assertNotIn("media",repr(r).lower())


if __name__=="__main__":
    unittest.main()
