"""Exact tick-string math, mocked host timebase; no actual Premiere."""
import copy
import runpy
from pathlib import Path
import unittest

from core.draft_compiler import build_draft
from core.host_ticks import frame_to_ticks, compile_tick_draft, HostTickDraftError


ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]


class HostTickTests(unittest.TestCase):
    def test_exact_demo_frames_30_fps_with_mocked_host_ticks(self):
        e,a=demo()
        draft=compile_tick_draft(build_draft(e,a),"8467200000")
        self.assertEqual(draft["status"],"DRAFT_NOT_EXECUTABLE")
        self.assertFalse(draft["can_assemble"])
        self.assertEqual(draft["sequence_end_ticks"],str(330*8467200000))
        self.assertEqual([
          (p["track"],p["start_frame"],p["end_frame"],p["start_ticks"])
          for p in draft["placements"]],[
            ("V2",0,150,"0"),
            ("V2",150,330,str(150*8467200000)),
            ("V3",192,330,str(192*8467200000))
        ])
        self.assertTrue(all(p["source_in_ticks"] is None for p in draft["placements"]))

    def test_large_integer_never_passes_through_floating_point(self):
        frame=2**53+1
        ticks="254016000000"
        self.assertEqual(frame_to_ticks(frame,ticks),str(frame*int(ticks)))
        self.assertEqual(frame_to_ticks(0,ticks),"0")

    def test_invalid_float_bool_negative_frame_refused(self):
        for frame in (True,False,-1,1.5,"150"):
            with self.assertRaises(HostTickDraftError):
                frame_to_ticks(frame,"8467200000")

    def test_unverified_or_zero_ticks_refused(self):
        for value in ("", "0", "0003","10.1", 8467200000,
                      "999999999999999999999999999999999"," 123 ",None):
            with self.assertRaises(HostTickDraftError):
                frame_to_ticks(150,value)

    def test_draft_never_becomes_executable_through_tick_conversion(self):
        e,a=demo();draft=build_draft(e,a)
        mapped=compile_tick_draft(draft,"8467200000")
        self.assertFalse(mapped["can_assemble"])
        self.assertTrue(all(p["readback_verified"] is False for p in mapped["placements"]))
        self.assertIn("ANIMATION_BOTH_BACKEND",mapped["missing"])

    def test_refuse_unexpected_readiness_or_duplicate_instances(self):
        e,a=demo();draft=build_draft(e,a)
        draft["can_assemble"]=True
        with self.assertRaises(HostTickDraftError):
            compile_tick_draft(draft,"8467200000")
        draft["can_assemble"]=False
        draft["asset_placements"].append(copy.deepcopy(draft["asset_placements"][0]))
        with self.assertRaises(HostTickDraftError):
            compile_tick_draft(draft,"8467200000")

    def test_track_overlap_is_not_auto_rippled_or_shortened(self):
        e,a=demo();draft=build_draft(e,a)
        draft["asset_placements"][1]["start_frame"]=149
        with self.assertRaises(HostTickDraftError) as context:
            compile_tick_draft(draft,"8467200000")
        self.assertEqual(context.exception.code,"E_HOST_TRACK_OVERLAP")

    def test_unknown_track_or_source_boundaries_refused(self):
        e,a=demo();draft=build_draft(e,a)
        draft["asset_placements"][0]["target_track"]="V99"
        with self.assertRaises(HostTickDraftError):
            compile_tick_draft(draft,"8467200000")
        draft=build_draft(e,a)
        draft["asset_placements"][0]["end_frame"]=1000
        with self.assertRaises(HostTickDraftError):
            compile_tick_draft(draft,"8467200000")


if __name__ == "__main__":
    unittest.main()
