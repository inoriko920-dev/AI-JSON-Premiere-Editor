"""All 21 BOTH preset phase references; no media writes/host calls."""
from __future__ import annotations

import copy
import json
import runpy
from pathlib import Path
import unittest

from core.animation_phases import build_both_phase_candidate, PhasePlanError
from core.draft_compiler import build_draft


ROOT = Path(__file__).resolve().parents[1]
demo = runpy.run_path(str(ROOT / "tests/test_core_contracts.py"))["demo"]
ref_file = ROOT / "core/animation_timings_b02.json"
registry_file = ROOT / "core/direction_registry.json"


class BothPhaseTests(unittest.TestCase):
    def test_reference_has_all_21_named_presets(self):
        reference=json.loads(ref_file.read_text("utf-8"))
        directions=json.loads(registry_file.read_text("utf-8"))["directions"]
        self.assertEqual(set(reference["entries"]),set(directions))
        self.assertEqual(len(reference["entries"]),21)
        self.assertTrue(all(v["in_frames"]>0 and v["out_frames"]>0
                            for v in reference["entries"].values()))

    def test_demo_exact_ranges_and_unchanged_preset_direction(self):
        edit,animation=demo()
        r=build_both_phase_candidate(edit,animation,max_instances=50)
        self.assertEqual(r["status"],"REFERENCE_SCHEDULE_ONLY")
        self.assertEqual(r["instance_count"],3)
        self.assertFalse(r["can_render"])
        self.assertFalse(r["can_assemble"])
        a=r["entries"][0]
        self.assertEqual(a["preset"],"BRUSH")
        self.assertEqual(a["direction"],"LEFT_TO_RIGHT")
        self.assertEqual(a["in_range"],[0,39])
        self.assertEqual(a["hold_range"],[39,141])
        self.assertEqual(a["out_range"],[141,150])
        self.assertEqual(a["mode"],"BOTH")
        self.assertIsNone(a["keyframes"])

    def test_all_21_med_speed_have_exclusive_nonoverlapping_ranges(self):
        reference=json.loads(ref_file.read_text("utf-8"))["entries"]
        directions=json.loads(registry_file.read_text("utf-8"))["directions"]
        for preset,ref in reference.items():
            with self.subTest(preset=preset):
                edit,animation=demo()
                animation["decisions"][0]["preset"]=preset
                animation["decisions"][0]["direction"]=directions[preset][0]
                output=build_both_phase_candidate(edit,animation,max_instances=3)
                item=next(x for x in output["entries"] if x["instance_key"]=="V001/A001")
                self.assertEqual(item["in_frames"],ref["in_frames"])
                self.assertEqual(item["out_frames"],ref["out_frames"])
                self.assertEqual(item["in_range"][1],item["hold_range"][0])
                self.assertEqual(item["hold_range"][1],item["out_range"][0])
                self.assertEqual(item["out_range"][1],150)
                self.assertFalse(item["can_render"])

    def test_duration_too_short_is_fail_closed_not_shortened(self):
        edit,animation=demo()
        # BRUSH needs exactly 48 frames total; force a 47-frame first scene.
        edit["scenes"][0]["end_frame"]=47
        edit["scenes"][0]["assets"][0]["end_frame"]=47
        edit["scenes"][1]["start_frame"]=47
        edit["scenes"][1]["assets"][0]["start_frame"]=47
        with self.assertRaises(PhasePlanError) as ctx:
            build_both_phase_candidate(edit,animation,max_instances=3)
        self.assertEqual(ctx.exception.code,"E_TIME_006")

    def test_boundary_equal_in_plus_out_has_zero_hold_review_flag(self):
        edit,animation=demo()
        edit["scenes"][0]["end_frame"]=48
        edit["scenes"][0]["assets"][0]["end_frame"]=48
        edit["scenes"][1]["start_frame"]=48
        edit["scenes"][1]["assets"][0]["start_frame"]=48
        r=build_both_phase_candidate(edit,animation,max_instances=3)
        p=r["entries"][0]
        self.assertEqual(p["hold_range"],[39,39])
        self.assertTrue(p["zero_hold_needs_visual_review"])
        self.assertFalse(r["can_render"])

    def test_repeated_asset_different_scene_remains_two_occurrences(self):
        edit,animation=demo()
        edit["scenes"][1]["assets"][1]["asset_id"]="A001"
        animation["decisions"][2]["asset_id"]="A001"
        out=build_both_phase_candidate(edit,animation,max_instances=3)
        self.assertEqual(out["instance_count"],3)
        self.assertEqual(len(set(x["instance_key"] for x in out["entries"])),3)

    def test_speed_fast_slow_and_locked_false_are_not_autocalibrated(self):
        for value in ("FAST","SLOW"):
            edit,animation=demo()
            animation["decisions"][0]["speed"]=value
            with self.assertRaises(PhasePlanError) as ctx:
                build_both_phase_candidate(edit,animation,max_instances=3)
            self.assertEqual(ctx.exception.code,"E_FX_INPUT_PLAN_UNVERIFIED")
        edit,animation=demo()
        animation["decisions"][0]["locked"]=False
        with self.assertRaises(PhasePlanError):
            build_both_phase_candidate(edit,animation,max_instances=3)

    def test_not_enough_budget_and_bad_types(self):
        edit,animation=demo()
        for cap in (0,True,2,"3",None):
            with self.assertRaises(PhasePlanError):
                build_both_phase_candidate(edit,animation,max_instances=cap)

    def test_digest_is_stable_and_changes_with_animation_choice(self):
        edit,animation=demo()
        a=build_both_phase_candidate(edit,animation,max_instances=10)
        b=build_both_phase_candidate(
            json.loads(json.dumps(edit)),json.loads(json.dumps(animation)),
            max_instances=10)
        self.assertEqual(a["operation_sha256"],b["operation_sha256"])
        changed=copy.deepcopy(animation)
        changed["decisions"][0]["preset"]="FADE"
        changed["decisions"][0]["direction"]="NONE"
        other=build_both_phase_candidate(edit,changed,max_instances=10)
        self.assertNotEqual(a["operation_sha256"],other["operation_sha256"])

    def test_no_source_paths_exposed(self):
        edit,animation=demo()
        edit["assets"]["A001"]["path"]="assets/private_secret.png"
        result=build_both_phase_candidate(edit,animation,max_instances=10)
        self.assertNotIn("private_secret",json.dumps(result))
        self.assertEqual(result["host_verified"],False)
        self.assertEqual(result["remaining"][0],"21_NATIVE_OR_FFMPEG_EFFECT_BACKENDS")


if __name__=="__main__":
    unittest.main()
