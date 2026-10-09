"""No Premiere runtime; verified frame counts are explicit fixtures."""
from pathlib import Path
import runpy
import unittest

from core.draft_compiler import build_draft
from core.host_ticks import compile_tick_draft
from core.timeline_lanes import plan_lanes, LanePlanError

demo=runpy.run_path(str(Path(__file__).parent/"test_core_contracts.py"))["demo"]


def mapped():
    e,a=demo()
    return compile_tick_draft(build_draft(e,a),"8467200000")


class TimelineLanesTests(unittest.TestCase):
    def plan(self, background=120, narration=330, limit=10):
        return plan_lanes(mapped(),background_source_frames=background,
                          narration_source_frames=narration,
                          max_background_segments=limit)

    def test_four_lanes_background_three_segments_and_audio_one(self):
        r=self.plan()
        self.assertEqual(r["total_frames"],330)
        self.assertEqual(r["status"],"DRAFT_NOT_EXECUTABLE")
        self.assertFalse(r["can_assemble"])
        self.assertEqual(r["background_segment_count"],3)
        self.assertEqual([(x["start_frame"],x["end_frame"])
                          for x in r["lanes"]["V1"]],[(0,120),(120,240),(240,330)])
        self.assertEqual([x["requires_source_trim"] for x in r["lanes"]["V1"]],
                         [False,False,True])
        self.assertEqual([(x["start_frame"],x["end_frame"])
                          for x in r["lanes"]["V2"]],[(0,150),(150,330)])
        self.assertEqual([(x["start_frame"],x["end_frame"])
                          for x in r["lanes"]["V3"]],[(192,330)])
        self.assertEqual(len(r["lanes"]["A1"]),1)
        self.assertIsNone(r["lanes"]["V2"][0]["source_out_frame"])

    def test_exact_divisible_background_has_no_trim(self):
        r=self.plan(background=110)
        self.assertEqual(r["background_segment_count"],3)
        self.assertTrue(all(x["requires_source_trim"] is False for x in r["lanes"]["V1"]))

    def test_long_background_one_clip(self):
        r=self.plan(background=600)
        self.assertEqual(len(r["lanes"]["V1"]),1)
        self.assertTrue(r["lanes"]["V1"][0]["requires_source_trim"])

    def test_unapproved_narration_silence_or_clip_refused(self):
        for n in (329,331,0):
            with self.assertRaises(LanePlanError) as caught:
                self.plan(narration=n)
            self.assertIn(caught.exception.code,
                          ("E_NARRATION_DURATION_POLICY","E_LANE_INPUT_UNVERIFIED"))

    def test_missing_or_float_budgets_refuse_without_truncation(self):
        for value in (None,0,-1,3.5,True):
            with self.assertRaises(LanePlanError):
                self.plan(background=value)

    def test_segment_cap_enforced_without_unbounded_loop(self):
        with self.assertRaises(LanePlanError) as caught:
            self.plan(background=1,limit=5)
        self.assertEqual(caught.exception.code,"E_RESOURCE_LIMIT")

    def test_deterministic_digest(self):
        self.assertEqual(self.plan()["digest_sha256"],self.plan()["digest_sha256"])
        self.assertNotEqual(self.plan(background=120)["digest_sha256"],
                            self.plan(background=150)["digest_sha256"])

    def test_malformed_tick_or_visual_rejected(self):
        x=mapped()
        x["sequence_end_ticks"]="11"
        with self.assertRaises(LanePlanError):
            plan_lanes(x,background_source_frames=120,
                       narration_source_frames=330,max_background_segments=10)
        x=mapped()
        x["placements"][0]["start_ticks"]="999"
        with self.assertRaises(LanePlanError) as ctx:
            plan_lanes(x,background_source_frames=120,
                       narration_source_frames=330,max_background_segments=10)
        self.assertEqual(ctx.exception.code,"E_LANE_VISUAL_INVALID")


if __name__=="__main__":
    unittest.main()
