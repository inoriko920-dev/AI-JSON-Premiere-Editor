"""STEP04 deterministic draft compiler tests (not Premiere host evidence)."""
import copy
import json
import runpy
from pathlib import Path
import unittest

from core.draft_compiler import build_draft, DraftCompileError

ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]


class DraftCompilerTests(unittest.TestCase):
    def test_canonical_v3_timing_and_tracks(self):
        edit, animation = demo()
        r=build_draft(edit, animation)
        self.assertEqual(r["status"],"DRAFT_NOT_EXECUTABLE")
        self.assertFalse(r["can_assemble"])
        self.assertEqual(r["scene_count"],2)
        self.assertEqual(r["asset_instance_count"],3)
        self.assertEqual(r["total_frames"],330)
        self.assertEqual([
            (x["scene_id"],x["asset_id"],x["target_track"],
             x["start_frame"],x["end_frame"])
            for x in r["asset_placements"]
        ],[
            ("V001","A001","V2",0,150),
            ("V002","A002","V2",150,330),
            ("V002","A003","V3",192,330)
        ])
        self.assertTrue(all(x["mode"]=="BOTH" for x in r["asset_placements"]))
        self.assertTrue(all(x["phase_frames"] is None for x in r["asset_placements"]))
        self.assertEqual(r["track_intent"]["V1"],"BACKGROUND_LOOP_PENDING_MEDIA_DURATION")
        self.assertEqual(r["track_intent"]["A1"],"NARRATION_DURATION_UNVERIFIED")

    def test_same_semantic_input_has_same_digest_across_json_roundtrip(self):
        edit,animation=demo()
        original=build_draft(edit,animation)
        copied=build_draft(json.loads(json.dumps(edit)),json.loads(json.dumps(animation)))
        self.assertEqual(original["operation_digest_sha256"],copied["operation_digest_sha256"])

    def test_changes_timing_or_preset_change_digest(self):
        edit,animation=demo()
        old=build_draft(edit,animation)["operation_digest_sha256"]
        e2,a2=copy.deepcopy(edit),copy.deepcopy(animation)
        e2["scenes"][1]["assets"][1]["start_frame"]=193
        self.assertNotEqual(old,build_draft(e2,a2)["operation_digest_sha256"])
        e2,a2=copy.deepcopy(edit),copy.deepcopy(animation)
        a2["decisions"][1]["preset"]="RISE"
        a2["decisions"][1]["direction"]="FROM_BOTTOM"
        self.assertNotEqual(old,build_draft(e2,a2)["operation_digest_sha256"])

    def test_reject_split_effect_and_missing_decision(self):
        edit,animation=demo()
        animation["decisions"][0]["exit_effect"]="FADE"
        with self.assertRaises(DraftCompileError) as ctx:
            build_draft(edit,animation)
        self.assertIn("E_ANIM_MODE",ctx.exception.codes)
        edit,animation=demo()
        animation["decisions"].pop()
        with self.assertRaises(DraftCompileError) as ctx:
            build_draft(edit,animation)
        self.assertIn("E_PLAN_PAIR",ctx.exception.codes)

    def test_refuse_unreviewed_speed_direction_and_unknown_nested(self):
        edit,animation=demo()
        animation["decisions"][0]["speed"]="FAST"
        with self.assertRaises(DraftCompileError) as ctx:
            build_draft(edit,animation)
        self.assertIn("E_FX_SPEED_UNCALIBRATED",ctx.exception.codes)
        edit,animation=demo()
        edit["scenes"][1]["extra_field"]="unknown"
        with self.assertRaises(DraftCompileError) as ctx:
            build_draft(edit,animation)
        self.assertIn("E_NESTED_UNKNOWN",ctx.exception.codes)

    def test_refuse_scene_gap_or_locked_false(self):
        edit,animation=demo()
        edit["scenes"][1]["start_frame"]=160
        edit["scenes"][1]["assets"][0]["start_frame"]=160
        with self.assertRaises(DraftCompileError):
            build_draft(edit,animation)
        edit,animation=demo()
        animation["decisions"][0]["locked"]=False
        with self.assertRaises(DraftCompileError) as ctx:
            build_draft(edit,animation)
        self.assertIn("E_LOCK_REVIEW",ctx.exception.codes)

    def test_no_raw_file_paths_or_untrusted_input_contents_in_draft(self):
        edit,animation=demo()
        edit["assets"]["A001"]["path"]="assets/super-secret.png"
        r=build_draft(edit,animation)
        serialized=json.dumps(r)
        self.assertNotIn("super-secret.png",serialized)
        self.assertNotIn("narasi.srt",serialized)
        self.assertNotIn("output/video_final.mp4",serialized)
        self.assertNotIn('"can_assemble": true', serialized)


if __name__=="__main__":
    unittest.main()
