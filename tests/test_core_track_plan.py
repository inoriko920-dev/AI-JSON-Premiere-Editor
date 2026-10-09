"""Four-track planner: exact frame coverage, source limits, no host editing."""
import copy
import runpy
from pathlib import Path
import unittest

from core.track_plan import compile_four_track_candidate, TrackPlanError

ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]


def snapshot(edit):
    return {"schema_version":"verified-media-snapshot-v1",
            "status":"CANDIDATE_NOT_AUTHORIZED","can_import":False,
            "can_assemble":False,
            "inventory_sha256":"a"*64,"import_count":len(edit["assets"])+2}


def make(*,bg=6000,audio=11000):
    e,a=demo()
    return compile_four_track_candidate(e,a,ticks_per_frame="8467200000",
        audio_duration_ms=audio,background_duration_ms=bg,
        media_snapshot=snapshot(e))


class FourTrackTests(unittest.TestCase):
    def test_two_scene_background_loops_and_narration_cover_exact_330_frames(self):
        r=make()
        self.assertFalse(r["can_assemble"])
        self.assertEqual(r["status"],"CANDIDATE_NOT_EXECUTABLE")
        self.assertEqual(r["total_frames"],330)
        self.assertEqual(r["track_counts"],{"V1":2,"V2":2,"V3":1,"A1":1})
        bg=[x for x in r["placements"] if x["target_track"]=="V1"]
        self.assertEqual([(x["start_frame"],x["end_frame"],x["source_in_frame"],x["source_out_frame"]) for x in bg],[
            (0,180,0,180),(180,330,0,150)])
        narration=[x for x in r["placements"] if x["target_track"]=="A1"]
        self.assertEqual(len(narration),1)
        self.assertEqual((narration[0]["start_frame"],narration[0]["end_frame"]),(0,330))
        visuals=[x for x in r["placements"] if x["target_track"] in ("V2","V3")]
        self.assertEqual([(x["target_track"],x["start_frame"],x["end_frame"]) for x in visuals],[
            ("V2",0,150),("V2",150,330),("V3",192,330)])

    def test_short_background_loops_conservatively(self):
        r=make(bg=990)
        self.assertEqual(r["track_counts"]["V1"],12)
        bg=[x for x in r["placements"] if x["target_track"]=="V1"]
        self.assertEqual(bg[0]["end_frame"],29)
        self.assertEqual(bg[-1]["end_frame"],330)

    def test_audio_must_cover_total_duration(self):
        e,a=demo()
        with self.assertRaises(TrackPlanError) as ctx:
            compile_four_track_candidate(e,a,ticks_per_frame="8467200000",
                audio_duration_ms=10999,background_duration_ms=6000,
                media_snapshot=snapshot(e))
        self.assertEqual(ctx.exception.code,"E_TRACK_NARRATION_TOO_SHORT")

    def test_zero_and_nan_duration_rejected(self):
        for duration in (0,-2,True,None,float("nan"),"6000"):
            e,a=demo()
            with self.assertRaises(TrackPlanError):
                compile_four_track_candidate(e,a,ticks_per_frame="8467200000",
                    audio_duration_ms=11000,background_duration_ms=duration,
                    media_snapshot=snapshot(e))

    def test_bad_media_snapshot_never_authorizes(self):
        e,a=demo()
        media=snapshot(e);media["can_import"]=True
        with self.assertRaises(TrackPlanError) as ctx:
            compile_four_track_candidate(e,a,ticks_per_frame="8467200000",
                audio_duration_ms=11000,background_duration_ms=6000,
                media_snapshot=media)
        self.assertEqual(ctx.exception.code,"E_TRACK_MEDIA_SNAPSHOT_UNVERIFIED")

    def test_unknown_background_audio_policy_fail_closed(self):
        e,a=demo();e["sources"]["background"]["audio_policy"]="KEEP"
        with self.assertRaises(TrackPlanError) as ctx:
            compile_four_track_candidate(e,a,ticks_per_frame="8467200000",
                audio_duration_ms=11000,background_duration_ms=6000,
                media_snapshot=snapshot(e))
        self.assertEqual(ctx.exception.code,"E_TRACK_AUDIO_POLICY_UNVERIFIED")

    def test_tick_string_exact_and_deterministic(self):
        x=make();y=make()
        self.assertEqual(x["operation_sha256"],y["operation_sha256"])
        self.assertEqual(x["placements"][1]["start_ticks"],"0")
        self.assertEqual(x["placements"][-1]["end_ticks"],str(330*8467200000))
        self.assertEqual(x["pending_requirements"][0],
                         "APPROVED_LAYOUT_CROP_AND_BOTH_ANIMATION")

    def test_same_background_source_asset_never_renamed_or_reselected(self):
        r=make()
        bg=[x for x in r["placements"] if x["target_track"]=="V1"]
        self.assertEqual([x["item_id"] for x in bg],
                         ["SOURCE_BACKGROUND","SOURCE_BACKGROUND"])

if __name__=="__main__":
    unittest.main()
