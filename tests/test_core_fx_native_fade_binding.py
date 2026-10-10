"""STEP23 Fade-to-track binding tests (Python only; no images/host edits)."""
from __future__ import annotations

import copy
from pathlib import Path
import runpy
import unittest

from core.animation_phases import build_both_phase_candidate
from core.fx_native_fade import compile_native_fade
from core.fx_native_fade_binding import (
    FadeBindingError, bind_native_fade_candidate, validate_native_fade_binding
)
from core.track_plan import compile_four_track_candidate

ROOT = Path(__file__).resolve().parents[1]
demo = runpy.run_path(str(ROOT / "tests/test_core_contracts.py"))["demo"]
SEQUENCE = "12345678-abcd-49ef-88ab-123456789abc"
NAME = "AIJSON_MANAGED_FadeCandidate"


def setup(index=0):
    edit, animation=demo()
    animation["decisions"][index]["preset"]="FADE"
    animation["decisions"][index]["direction"]="NONE"
    phases=build_both_phase_candidate(edit,animation,max_instances=12)["entries"]
    fade=compile_native_fade(phases[index])
    media={"schema_version":"verified-media-snapshot-v1",
           "status":"CANDIDATE_NOT_AUTHORIZED",
           "can_import":False,"can_assemble":False,
           "inventory_sha256":"a"*64,"import_count":len(edit["assets"])+2}
    track=compile_four_track_candidate(
        edit,animation,ticks_per_frame="8467200000",
        audio_duration_ms=11000,background_duration_ms=6000,
        media_snapshot=media)
    ids=sorted(set(p["item_id"] for p in track["placements"]))
    refs=[{"item_id":value, "node_id":"Node"+str(i+1)}
          for i,value in enumerate(ids)]
    return fade,track,refs


class FadePlacementBindingTests(unittest.TestCase):
    def setUp(self):
        self.fade,self.track,self.refs=setup()

    def bind(self,**options):
        payload=dict(fade=self.fade,track_plan=self.track,
                     media_refs=self.refs,managed_sequence_id=SEQUENCE,
                     managed_sequence_name=NAME)
        payload.update(options)
        return bind_native_fade_candidate(**payload)

    def reject(self,code,**options):
        with self.assertRaises(FadeBindingError) as caught:
            self.bind(**options)
        self.assertEqual(caught.exception.code,code)

    def test_binds_to_unique_visual_clip_and_four_opacity_keys(self):
        output=self.bind()
        self.assertEqual(output["status"],"SELECTOR_BOUND_NOT_HOST_AUTHORIZED")
        self.assertEqual(output["selector"]["track"],"V2")
        self.assertEqual(output["selector"]["start_ticks"],"0")
        self.assertEqual(output["selector"]["end_ticks"],str(150*8467200000))
        self.assertEqual(output["item_id"],"ASSET_A001")
        self.assertEqual(output["instance_key"],self.fade["instance_key"])
        self.assertEqual([x["instance_frame"] for x in
                          output["local_keyframe_samples"]],[0,14,143,149])
        self.assertEqual([x["instance_ticks"] for x in
                          output["local_keyframe_samples"]],
                         [str(x*8467200000) for x in [0,14,143,149]])
        self.assertEqual([x["opacity_percent"] for x in
                          output["local_keyframe_samples"]],[0,100,100,0])
        self.assertFalse(output["node_id_host_verified"])
        self.assertFalse(output["clip_end_host_verified"])
        self.assertFalse(output["time_coordinate_verified"])
        self.assertFalse(output["can_assemble"])
        self.assertFalse(output["host_verified"])
        self.assertNotIn("png",str(output).lower())
        validate_native_fade_binding(
            output,self.fade,self.track,self.refs,
            managed_sequence_id=SEQUENCE,managed_sequence_name=NAME)

    def test_later_scene_uses_global_selector_but_local_animation_frames(self):
        fade,plan,refs=setup(index=1)
        result=self.bind(fade=fade,track_plan=plan,media_refs=refs)
        target=next(p for p in plan["placements"]
                    if p["instance_key"]==fade["instance_key"])
        self.assertGreater(fade["start_frame"],0)
        self.assertEqual(result["selector"]["start_ticks"],
                         str(fade["start_frame"]*8467200000))
        self.assertEqual(result["selector"]["end_ticks"],
                         str(fade["end_frame"]*8467200000))
        self.assertEqual(result["selector"]["track"],target["target_track"])
        self.assertEqual(result["local_keyframe_samples"][0]["instance_ticks"],"0")
        self.assertFalse(result["host_verified"])

    def test_modified_phase_duration_or_fake_host_ready_never_binds(self):
        for patch in ({"end_frame":149},{"host_verified":True},
                      {"can_assemble":True},{"preset":"PAN"}):
            fade=dict(self.fade,**patch)
            with self.subTest(patch=patch):
                self.reject("E_FX_NATIVE_CANDIDATE_INVALID",fade=fade)

    def test_wrong_item_node_or_missing_import_ref_rejected(self):
        self.reject("E_FX_MEDIA_REFS_MISMATCH",
                    media_refs=self.refs[:-1])
        dup=copy.deepcopy(self.refs)
        dup[0]["node_id"]=dup[1]["node_id"]
        self.reject("E_FX_MEDIA_REFS_INVALID",media_refs=dup)
        modified=copy.deepcopy(self.refs)
        modified[0]["node_id"]="../../unsafe"
        self.reject("E_FX_MEDIA_REFS_INVALID",media_refs=modified)
        modified=copy.deepcopy(self.refs)
        modified.append(dict(modified[0]))
        self.reject("E_FX_MEDIA_REFS_INVALID",media_refs=modified)
        self.reject("E_FX_MEDIA_REFS_INVALID",media_refs="not a list")

    def test_wrong_sequence_id_and_name_rejected(self):
        self.reject("E_FX_MANAGED_SEQUENCE_INVALID",
                    managed_sequence_id="not-a-guid")
        self.reject("E_FX_MANAGED_SEQUENCE_INVALID",
                    managed_sequence_name="PersonalWork")
        self.reject("E_FX_MANAGED_SEQUENCE_INVALID",
                    managed_sequence_name="AIJSON_MANAGED_Ok\nInjected")

    def test_tampered_four_track_timing_or_sha_rejected(self):
        other=copy.deepcopy(self.track)
        other["placements"][0]["end_frame"]+=1
        self.reject("E_FX_TRACK_PLAN_CHANGED",track_plan=other)
        other=copy.deepcopy(self.track)
        other["operation_sha256"]="b"*64
        self.reject("E_FX_TRACK_PLAN_CHANGED",track_plan=other)
        other=copy.deepcopy(self.track)
        other["can_assemble"]=True
        self.reject("E_FX_TRACK_PLAN_INVALID",track_plan=other)
        other=copy.deepcopy(self.track)
        other["ticks_per_frame"]="0"
        self.reject("E_FX_TRACK_PLAN_INVALID",track_plan=other)

    def test_candidate_can_never_be_upgraded_into_host_ready(self):
        result=self.bind()
        for name,value in (("can_assemble",True),
                           ("host_verified",True),
                           ("node_id_host_verified",True),
                           ("clip_end_host_verified",True),
                           ("status","READY"),
                           ("item_id","ASSET_A002"),
                           ("binding_sha256","b"*64)):
            mutated=copy.deepcopy(result)
            mutated[name]=value
            with self.subTest(field=name):
                with self.assertRaises(FadeBindingError) as context:
                    validate_native_fade_binding(
                        mutated,self.fade,self.track,self.refs,
                        managed_sequence_id=SEQUENCE,
                        managed_sequence_name=NAME)
                self.assertEqual(context.exception.code,
                                 "E_FX_FADE_BINDING_TAMPERED")

    def test_media_node_binding_change_requires_regeneration(self):
        first=self.bind()
        changed=copy.deepcopy(self.refs)
        for r in changed:
            if r["item_id"]=="ASSET_A001":
                r["node_id"]="NewNode"
        second=self.bind(media_refs=changed)
        self.assertNotEqual(first["binding_sha256"],second["binding_sha256"])
        with self.assertRaises(FadeBindingError):
            validate_native_fade_binding(
                first,self.fade,self.track,changed,
                managed_sequence_id=SEQUENCE,managed_sequence_name=NAME)

if __name__=="__main__":
    unittest.main()
