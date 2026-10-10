"""STEP28 media snapshot -> track -> cache binding, no image asset generated.

Mocks only filesystem/FFprobe boundary; STEP19 and STEP27 separately test
actual MOV and cache-key arithmetic. These assertions are NOT Adobe host QA.
"""
from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from core.fx_media_cache_track_preflight import (
    MediaCacheTrackError, inspect_media_cache_track)
from core.fx_cache_worker import AlphaCacheError
from tests.test_core_fx_native_fade_binding import setup
from tests.test_core_fx_alpha_parity import candidates


def digest(value):
    return sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
                             separators=(",",":"),allow_nan=False).encode()).hexdigest()


class MediaCacheTrackPreflightTests(unittest.TestCase):
    def setUp(self):
        self.fade,self.plan,self.media_refs=setup()
        # The approved STEP15 B02 item is not a native Fade candidate.
        # Independently derive it from the strict STEP21/native material.
        first=self.fade
        start,end,ins,outs=(first[k] for k in (
            "start_frame","end_frame","in_frames","out_frames"))
        self.fx={
            "instance_key":first["instance_key"],"preset":"FADE",
            "direction":"NONE","mode":"BOTH","speed":"MEDIUM",
            "can_render":False,"effect_backend":"NOT_IMPLEMENTED",
            "keyframes":None,"source_reference":"STEP01_B02_PROPOSED_21",
            "reference_evidence":first["reference_evidence"],
            "start_frame":start,"end_frame":end,
            "in_frames":ins,"out_frames":outs,
            "in_range":[start,start+ins],
            "hold_range":[start+ins,end-outs],
            "out_range":[end-outs,end]
        }
        ids=sorted(set(p["item_id"] for p in self.plan["placements"]))
        self.sources={}
        items=[]
        for idx,item_id in enumerate(["SOURCE_SRT"]+ids):
            asset=item_id.startswith("ASSET_")
            if item_id=="SOURCE_SRT":
                kind,relative,imported="srt","caption.srt",False
            elif asset:
                kind,relative,imported="png",item_id+".png",True
            elif item_id=="SOURCE_AUDIO":
                kind,relative,imported="audio","narration.mp3",True
            else:
                kind,relative,imported="background","background.mp4",True
            rec={"item_id":item_id,"kind":kind,
                 "import_to_premiere":imported,
                 "relative_path":relative,
                 "absolute_path":"/owner/media/"+relative,
                 "sha256":format(idx+1,"064x"),
                 "byte_size":100+idx,"mtime_ns":12345+idx}
            items.append(rec)
            self.sources[item_id]=rec
        media_digest=digest(items)
        self.snapshot={
            "schema_version":"verified-media-snapshot-v1",
            "status":"CANDIDATE_NOT_AUTHORIZED",
            "can_import":False,"can_assemble":False,
            "project_id":self.plan["project_id"],
            "media_root":"/owner/media",
            "item_count":len(items),
            "import_count":len(ids),
            "inventory_sha256":media_digest,"items":items,
        }
        self.plan["media_digest"]=media_digest
        keys=("schema_version","project_id","source_digest",
              "media_digest","ticks_per_frame","total_frames","placements")
        self.plan["operation_sha256"]=digest({k:self.plan[k] for k in keys})
        self.report={"fake-report-for-mocked-cache-audit":True}
        self.audit_response={
            "cache_key_sha256":"a"*64,
            "output_sha256":"b"*64,
            "host_verified":False,"can_assemble":False,
        }
        self.params=dict(
            snapshot=self.snapshot,plan=self.plan,fx_item=self.fx,
            report=self.report,cache_root=Path("/owner/cache"),
            ffprobe_exe=Path("/tools/ffprobe"),max_media_bytes=10000,
            max_pixels=50000,max_cached_bytes=100000,timeout_seconds=10)
        self.patches=[
            patch("core.fx_media_cache_track_preflight.recheck_media_snapshot",
                  return_value=True),
            patch("core.fx_media_cache_track_preflight._source_dimensions",
                  return_value=(64,64)),
            patch("core.fx_media_cache_track_preflight.verify_cache_for_candidate",
                  return_value=self.audit_response),
        ]
        self.mocks=[x.start() for x in self.patches]
        for p in self.patches:self.addCleanup(p.stop)
        self.recheck,self.dimensions,self.audit=self.mocks

    def do(self,**overrides):
        p=dict(self.params)
        p.update(overrides)
        return inspect_media_cache_track(**p)

    def fail(self,code,**overrides):
        with self.assertRaises(MediaCacheTrackError) as error:
            self.do(**overrides)
        self.assertEqual(error.exception.code,code)

    def test_exact_media_snapshot_and_occurrence_reuses_only_pinned_cache(self):
        result=self.do()
        self.assertEqual(result["item_id"],"ASSET_A001")
        self.assertEqual(result["source_sha256"],
                         self.sources["ASSET_A001"]["sha256"])
        self.assertEqual(result["cache_key_sha256"],"a"*64)
        self.assertTrue(result["source_recheck_at_preflight"])
        self.assertFalse(result["source_recheck_at_host_transaction"])
        self.assertFalse(result["host_verified"])
        self.assertFalse(result["can_assemble"])
        self.assertFalse(result["can_import"])
        self.assertFalse(result["real_premiere_readback_verified"])
        self.recheck.assert_called_once_with(
            self.snapshot,max_file_bytes=10000)
        self.dimensions.assert_called_once_with(
            self.snapshot,self.sources["ASSET_A001"],50000)
        self.audit.assert_called_once()
        args=self.audit.call_args.kwargs
        self.assertEqual(args["expected_source_sha256"],
                         self.sources["ASSET_A001"]["sha256"])
        self.assertEqual(args["expected_source_dimensions"],(64,64))
        self.assertIs(args["item"],self.fx)
        self.assertIs(args["report"],self.report)

    def test_changed_media_recheck_rejected_before_opening_mov(self):
        self.recheck.return_value=False
        self.fail("E_FX_MEDIA_SNAPSHOT_STALE")
        self.assertFalse(self.audit.called)
        self.assertFalse(self.dimensions.called)

    def test_valid_snapshot_content_with_wrong_inventory_digest_rejected(self):
        tampered=copy.deepcopy(self.snapshot)
        tampered["items"][1]["sha256"]="c"*64
        self.fail("E_FX_MEDIA_SNAPSHOT_CHANGED",snapshot=tampered)
        self.assertFalse(self.recheck.called)
        self.assertFalse(self.audit.called)

    def test_invalid_track_and_mixed_project_rejected_without_media_access(self):
        bad=copy.deepcopy(self.plan)
        bad["placements"][0]["start_ticks"]="123"
        self.fail("E_FX_PLAN_OR_PRESET_INVALID",plan=bad)
        bad=copy.deepcopy(self.snapshot)
        bad["project_id"]="DifferentProject"
        self.fail("E_FX_MEDIA_SNAPSHOT_INVALID",snapshot=bad)
        bad=copy.deepcopy(self.plan)
        bad["media_digest"]="c"*64
        keys=("schema_version","project_id","source_digest",
              "media_digest","ticks_per_frame","total_frames","placements")
        bad["operation_sha256"]=digest({k:bad[k] for k in keys})
        self.fail("E_FX_MEDIA_TRACK_MISMATCH",plan=bad)
        self.assertFalse(self.recheck.called)
        self.assertFalse(self.audit.called)

    def test_same_asset_but_wrong_scene_and_duration_never_uses_cache(self):
        bad=copy.deepcopy(self.fx)
        bad["instance_key"]="OtherScene/A001"
        self.fail("E_FX_INSTANCE_MISSING",fx_item=bad)
        bad=copy.deepcopy(self.fx)
        bad["end_frame"]+=1
        bad["hold_range"][1]+=1
        bad["out_range"][0]+=1
        bad["out_range"][1]+=1
        self.fail("E_FX_TRACK_OCCURRENCE_MISMATCH",fx_item=bad)
        self.assertFalse(self.audit.called)

    def test_different_preset_or_forged_readiness_never_enters_mov_audit(self):
        bad=copy.deepcopy(self.fx)
        bad["preset"]="POP"
        self.fail("E_FX_PLAN_OR_PRESET_INVALID",fx_item=bad)
        bad=copy.deepcopy(self.plan)
        bad["can_assemble"]=True
        self.fail("E_FX_PLAN_OR_PRESET_INVALID",plan=bad)
        self.assertFalse(self.audit.called)

    def test_wrong_asset_item_linkage_rejected_even_if_plan_rehashed(self):
        bad=copy.deepcopy(self.plan)
        target=next(p for p in bad["placements"]
                    if p["instance_key"]==self.fx["instance_key"])
        target["item_id"]="ASSET_A002"
        keys=("schema_version","project_id","source_digest",
              "media_digest","ticks_per_frame","total_frames","placements")
        bad["operation_sha256"]=digest({k:bad[k] for k in keys})
        self.fail("E_FX_TRACK_OCCURRENCE_MISMATCH",plan=bad)
        self.assertFalse(self.audit.called)

    def test_pinned_source_missing_or_changed_geometry_refused(self):
        self.dimensions.side_effect=MediaCacheTrackError(
            "E_FX_MEDIA_SOURCE_UNREADABLE")
        self.fail("E_FX_MEDIA_SOURCE_UNREADABLE")
        self.assertFalse(self.audit.called)

    def test_corrupt_or_wrong_cache_audit_is_not_upgraded(self):
        self.audit.side_effect=AlphaCacheError(
            "E_FX_CACHE_CANDIDATE_MISMATCH")
        self.fail("E_FX_CACHE_CANDIDATE_MISMATCH")
        self.audit.side_effect=AlphaCacheError(
            "E_FX_CACHE_HASH_MISMATCH")
        self.fail("E_FX_CACHE_HASH_MISMATCH")

    def test_malformed_limits_and_duplicate_media_items_rejected(self):
        self.fail("E_FX_RESOURCE_LIMIT_UNVERIFIED",max_pixels=True)
        self.fail("E_FX_RESOURCE_LIMIT_UNVERIFIED",timeout_seconds=0)
        bad=copy.deepcopy(self.snapshot)
        bad["items"].append(copy.deepcopy(bad["items"][0]))
        bad["item_count"]+=1
        self.fail("E_FX_MEDIA_SNAPSHOT_INVALID",snapshot=bad)
        self.assertFalse(self.audit.called)


if __name__=="__main__":
    unittest.main()
