"""V1/V2/V3/A1 deterministic track worklist, no Premiere host needed."""
import copy
import runpy
import unittest
from pathlib import Path

from core.draft_compiler import build_draft
from core.track_worklist import build_track_worklist, TrackWorklistError

ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]


def fixture(bg=120, audio=400, limit=100):
    e,a=demo()
    draft=build_draft(e,a)
    snap={"schema_version":"verified-media-snapshot-v1",
          "status":"CANDIDATE_NOT_AUTHORIZED",
          "can_import":False,"can_assemble":False,
          "inventory_sha256":"f"*64,
          "items":[
            {"item_id":"SOURCE_SRT","kind":"srt","import_to_premiere":False},
            {"item_id":"SOURCE_AUDIO","kind":"audio","import_to_premiere":True},
            {"item_id":"SOURCE_BACKGROUND","kind":"background","import_to_premiere":True},
            *[{"item_id":"ASSET_"+k,"kind":"png","import_to_premiere":True}
              for k in e["assets"]]
          ]}
    durations={"background_frames":bg,"audio_frames":audio,
               "measurement":"EXTERNAL_MEDIA_REVIEW_PENDING_HOST",
               "snapshot_sha256":snap["inventory_sha256"]}
    return draft,snap,durations,limit


class WorklistTests(unittest.TestCase):
    def build(self, bg=120, audio=400, limit=100):
        d,s,dur,cap=fixture(bg,audio,limit)
        return build_track_worklist(d,s,dur,"8467200000",max_operations=cap)

    def test_four_track_counts_and_background_repeat_with_exact_last_trim(self):
        r=self.build()
        self.assertEqual(r["status"],"DRAFT_NOT_EXECUTABLE")
        self.assertFalse(r["can_assemble"])
        self.assertEqual(r["track_counts"],{"V1":3,"V2":2,"V3":1,"A1":1})
        bg=[x for x in r["operations"] if x["track"]=="V1"]
        self.assertEqual([(x["start_frame"],x["end_frame"],
                           x["source_in_frame"],x["source_out_frame"])
                          for x in bg],
                         [(0,120,0,120),(120,240,0,120),(240,330,0,90)])
        imgs=[x for x in r["operations"] if x["track"] in ("V2","V3")]
        self.assertEqual([(x["track"],x["start_frame"],x["end_frame"])
                           for x in imgs],[("V2",0,150),("V2",150,330),("V3",192,330)])
        a=r["operations"][-1]
        self.assertEqual((a["track"],a["start_frame"],a["end_frame"],
                          a["source_out_frame"]),("A1",0,330,330))
        self.assertTrue(all(x["readback_verified"] is False for x in r["operations"]))
        self.assertTrue(all(x["native_trim_verified"] is False for x in r["operations"]))

    def test_exact_ticks_are_decimal_strings_not_js_number(self):
        r=self.build()
        self.assertEqual(r["operations"][0]["end_ticks"],str(120*8467200000))
        self.assertEqual(r["operations"][-1]["source_out_ticks"],str(330*8467200000))

    def test_same_inputs_stable_digest_and_unchanged_media_sources(self):
        d,s,dur,n=fixture()
        before=copy.deepcopy((d,s,dur))
        a=build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        b=build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        self.assertEqual(a["operation_digest_sha256"],b["operation_digest_sha256"])
        self.assertEqual(before,(d,s,dur))
        self.assertFalse(a["can_assemble"])

    def test_short_audio_fails_no_padding_silence(self):
        d,s,dur,n=fixture(audio=329)
        with self.assertRaises(TrackWorklistError) as e:
            build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        self.assertEqual(e.exception.code,"E_TRACK_NARRATION_TOO_SHORT")

    def test_zero_negative_bool_float_duration_rejected(self):
        for v in (0,-1,True,False,4.5,"120",None):
            d,s,dur,n=fixture()
            dur["background_frames"]=v
            with self.assertRaises(TrackWorklistError):
                build_track_worklist(d,s,dur,"8467200000",max_operations=n)

    def test_explicit_limit_blocks_many_background_loops(self):
        d,s,dur,n=fixture(bg=1,limit=5)
        with self.assertRaises(TrackWorklistError) as e:
            build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        self.assertEqual(e.exception.code,"E_RESOURCE_LIMIT")

    def test_missing_snapshot_asset_never_falls_back(self):
        d,s,dur,n=fixture()
        s["items"]=[x for x in s["items"] if x["item_id"]!="ASSET_A002"]
        with self.assertRaises(TrackWorklistError) as e:
            build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        self.assertEqual(e.exception.code,"E_TRACK_MEDIA_MAPPING_INVALID")

    def test_digest_or_timebase_missing_is_blocked(self):
        d,s,dur,n=fixture()
        dur["snapshot_sha256"]="0"*64
        with self.assertRaises(TrackWorklistError):
            build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        d,s,dur,n=fixture()
        with self.assertRaises(TrackWorklistError):
            build_track_worklist(d,s,dur,"0",max_operations=n)

    def test_second_visual_on_same_track_cannot_overlap(self):
        d,s,dur,n=fixture()
        d["asset_placements"][1]["start_frame"]=140
        with self.assertRaises(TrackWorklistError) as e:
            build_track_worklist(d,s,dur,"8467200000",max_operations=n)
        self.assertEqual(e.exception.code,"E_HOST_TRACK_OVERLAP")

    def test_background_longer_than_timeline_produces_single_trim_candidate(self):
        r=self.build(bg=500)
        self.assertEqual(r["track_counts"]["V1"],1)
        self.assertEqual(r["operations"][0]["source_out_frame"],330)

    def test_snapshot_claim_can_import_true_is_rejected(self):
        d,s,dur,n=fixture()
        s["can_import"]=True
        with self.assertRaises(TrackWorklistError):
            build_track_worklist(d,s,dur,"8467200000",max_operations=n)


if __name__ == "__main__":
    unittest.main()
