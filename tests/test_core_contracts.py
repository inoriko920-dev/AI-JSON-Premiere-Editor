"""STEP04 strict JSON parser and semantic contract tests, no host needed."""
import copy
import json
import unittest

from core.contracts import DuplicateObjectKey, loads_strict, validate_pair

H = "a" * 64


def demo():
    edit = {
      "schema_version":"edit-plan-v2","project_id":"DEMO_001","revision":2,
      "canvas":{"width":1920,"height":1080,"fps_num":30,"fps_den":1},
      "sources":{"srt":{"path":"narasi.srt","sha256":H},
                 "audio":{"path":"narasi.wav","sha256":H},
                 "background":{"path":"background.mp4","required":True,"audio_policy":"MUTE"}},
      "profiles":{"layout_id":"CANVA_REFERENCE_V1","layout_hash":H},
      "assets":{"A001":{"path":"assets/A001.png"},
                "A002":{"path":"assets/A002.png"},
                "A003":{"path":"assets/A003.png"}},
      "scenes":[
        {"scene_id":"V001","source_segment_ids":["N0001"],"narration_quote":"Peristiwa pertama.",
         "layout_type":"SINGLE","start_frame":0,"end_frame":150,"transition_policy":"CUT",
         "assets":[{"asset_id":"A001","slot":"SINGLE","start_frame":0,"end_frame":150,
                    "entry_evidence":{"cue_id":1,"accuracy":"EXACT_CUE"}}]},
        {"scene_id":"V002","source_segment_ids":["N0002","N0003"],
         "narration_quote":"Dua pihak.","layout_type":"DOUBLE","start_frame":150,
         "end_frame":330,"transition_policy":"CUT",
         "assets":[{"asset_id":"A002","slot":"LEFT","start_frame":150,"end_frame":330,
                    "entry_evidence":{"cue_id":2,"accuracy":"EXACT_CUE"}},
                   {"asset_id":"A003","slot":"RIGHT","start_frame":192,"end_frame":330,
                    "entry_evidence":{"cue_id":3,"accuracy":"EXACT_CUE"}}]}],
      "render":{"codec":"libx264","pixel_format":"yuv420p","audio_codec":"aac",
                "audio_policy":"NARRATION_ONLY","subtitles":"NONE",
                "output_path":"output/video_final.mp4"},
      "validation":{"status":"READY","issues":[]},
      "provenance":{"scene_plan_schema":"asset-scene-plan-v2",
                    "timing_source":"SRT_EXACT_CUE","ai_decision_mode":"A_JSON_ALL"}
    }
    animation = {
      "schema_version":"animation-plan-v1","project_id":"DEMO_001",
      "edit_plan_revision":2,"revision":1,"mode":"BOTH",
      "animation_profile":{"id":"CANVA_BOTH_21_V1","sha256":H},
      "project_seed":827314,
      "decisions":[
       {"scene_id":"V001","asset_id":"A001","preset":"BRUSH","speed":"MEDIUM",
        "direction":"LEFT_TO_RIGHT","locked":True},
       {"scene_id":"V002","asset_id":"A002","preset":"PAN","speed":"MEDIUM",
        "direction":"FROM_LEFT","locked":True},
       {"scene_id":"V002","asset_id":"A003","preset":"WIPE","speed":"MEDIUM",
        "direction":"RIGHT_TO_LEFT","locked":True}],
      "provenance":{"source":"GPT_ANIMATION_DIRECTOR",
                    "registry":"GENERAL_15_REVEAL_6","decisions_are_final":True}
    }
    return edit, animation


def codes(report):
    return [x["code"] for x in report["issues"]]


def has(report, code, severity=None):
    return any(x["code"] == code and
               (severity is None or x["severity"] == severity)
               for x in report["issues"])


class ContractTests(unittest.TestCase):
    def test_valid_demo_is_structurally_sane_but_not_host_ready(self):
        e, a = demo()
        result = validate_pair(e, a)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["error_count"], 0, result["issues"])
        self.assertEqual(result["scene_count"], 2)
        self.assertEqual(result["asset_instance_count"], 3)
        self.assertFalse(result["can_assemble"])
        for code in ("E_HOST_UNVERIFIED","E_MEDIA_UNVERIFIED",
                     "E_PROFILE_UNVERIFIED","E_CONFIG_LIMITS_UNVERIFIED"):
            self.assertTrue(has(result, code, "REVIEW"))

    def test_real_json_roundtrip_preserves_demo(self):
        e, a = demo()
        left, right = loads_strict(json.dumps(e).encode()), loads_strict(json.dumps(a))
        self.assertEqual(validate_pair(left, right)["error_count"], 0)

    def test_duplicate_object_keys_rejected_even_when_nested(self):
        for raw in ('{"id":1,"id":2}', '{"x":{"a":1,"a":2}}'):
            with self.assertRaises(DuplicateObjectKey):
                loads_strict(raw)

    def test_non_finite_constants_not_accepted(self):
        for v in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValueError):
                loads_strict('{"n":'+v+'}')

    def test_utf8_bom_supported(self):
        self.assertEqual(loads_strict(b'\xef\xbb\xbf{"x":1}'), {"x":1})

    def test_wrong_schema_versions_rejected(self):
        e, a = demo()
        e["schema_version"] = "edit-plan-v9"
        a["schema_version"] = "animation-plan-v9"
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA"))

    def test_unknown_root_fails_not_review(self):
        e, a = demo()
        e["rogue_execute"] = "ignored"
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))

    def test_unknown_nested_field_review_not_ready(self):
        e, a = demo()
        e["scenes"][0]["new_editor_flag"] = True
        self.assertTrue(has(validate_pair(e,a),"E_NESTED_UNKNOWN","REVIEW"))

    def test_project_and_revision_pair_mismatch(self):
        e, a = demo()
        a["project_id"] = "OTHER"
        a["edit_plan_revision"] = 3
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))

    def test_both_is_strict(self):
        e, a = demo()
        a["mode"] = "IN_ONLY"
        self.assertTrue(has(validate_pair(e,a),"E_ANIM_MODE","ERROR"))

    def test_split_enter_exit_fields_are_fatal(self):
        for field in ("enter_effect","exit_effect","enter_direction",
                      "exit_direction","in_ms","out_ms"):
            e,a=demo()
            a["decisions"][0][field] = "X"
            self.assertTrue(has(validate_pair(e,a),"E_ANIM_MODE","ERROR"),field)

    def test_missing_decision_and_extra_are_errors(self):
        e,a=demo()
        a["decisions"].pop()
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))
        e,a=demo()
        a["decisions"].append({"scene_id":"VX","asset_id":"AX","preset":"FADE",
                               "speed":"MEDIUM","direction":"NONE","locked":True})
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))

    def test_duplicate_decision_not_overwritten(self):
        e,a=demo()
        a["decisions"].append(copy.deepcopy(a["decisions"][0]))
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))

    def test_repeated_asset_across_scenes_has_two_decisions(self):
        e,a=demo()
        e["scenes"][1]["assets"][1]["asset_id"]="A001"
        a["decisions"][2]["asset_id"]="A001"
        self.assertEqual(validate_pair(e,a)["error_count"], 0)

    def test_duplicate_scene_id_fatal(self):
        e,a=demo()
        e["scenes"][1]["scene_id"]="V001"
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))

    def test_missing_asset_definition_fatal(self):
        e,a=demo()
        del e["assets"]["A003"]
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))

    def test_single_and_double_slot_rules(self):
        e,a=demo()
        e["scenes"][0]["assets"][0]["slot"]="LEFT"
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))
        e,a=demo()
        e["scenes"][1]["assets"][1]["slot"]="LEFT"
        self.assertTrue(has(validate_pair(e,a),"E_PLAN_PAIR","ERROR"))

    def test_bad_frame_bounds_and_bool_rejected(self):
        e,a=demo()
        e["scenes"][0]["assets"][0]["end_frame"]=0
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))
        e,a=demo()
        e["scenes"][0]["start_frame"]=True
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))

    def test_asset_outside_scene_fatal(self):
        e,a=demo()
        e["scenes"][1]["assets"][1]["end_frame"]=331
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))

    def test_scene_gap_review(self):
        e,a=demo()
        e["scenes"][1]["start_frame"]=160
        e["scenes"][1]["assets"][0]["start_frame"]=160
        self.assertTrue(has(validate_pair(e,a),"E_SCENE_GAP_POLICY","REVIEW"))

    def test_unknown_preset_direction_speed(self):
        e,a=demo()
        a["decisions"][0]["preset"]="UNKNOWN"
        self.assertTrue(has(validate_pair(e,a),"E_ANIM_PRESET","ERROR"))
        e,a=demo()
        a["decisions"][1]["direction"]="LEFT_TO_RIGHT" # pan only FROM_LEFT
        self.assertTrue(has(validate_pair(e,a),"E_ANIM_PRESET","ERROR"))
        e,a=demo()
        a["decisions"][1]["speed"]="ULTRA"
        self.assertTrue(has(validate_pair(e,a),"E_ANIM_PRESET","ERROR"))

    def test_unhashable_speed_or_accuracy_fail_cleanly_not_crash(self):
        e,a=demo()
        a["decisions"][0]["speed"]=["MEDIUM"]
        self.assertTrue(has(validate_pair(e,a),"E_ANIM_PRESET","ERROR"))
        e,a=demo()
        e["scenes"][0]["assets"][0]["entry_evidence"]["accuracy"]=["EXACT_CUE"]
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))

    def test_locked_false_review_and_string_false_error(self):
        e,a=demo()
        a["decisions"][0]["locked"]=False
        self.assertTrue(has(validate_pair(e,a),"E_LOCK_REVIEW","REVIEW"))
        e,a=demo()
        a["decisions"][0]["locked"]="false"
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))

    def test_fast_slow_exist_but_need_calibration(self):
        for speed in ("FAST","SLOW"):
            e,a=demo()
            a["decisions"][0]["speed"]=speed
            self.assertTrue(has(validate_pair(e,a),"E_FX_SPEED_UNCALIBRATED","REVIEW"))

    def test_srt_evidence_unresolved_review(self):
        e,a=demo()
        e["scenes"][0]["assets"][0]["entry_evidence"]["accuracy"]="UNRESOLVED"
        self.assertTrue(has(validate_pair(e,a),"E_SRT_AMBIGUOUS","REVIEW"))

    def test_placeholder_hash_is_error(self):
        e,a=demo()
        e["sources"]["audio"]["sha256"]="<SHA256_AUDIO>"
        self.assertTrue(has(validate_pair(e,a),"E_JSON_SCHEMA","ERROR"))

    def test_input_READY_does_not_enable_assembly(self):
        e,a=demo()
        e["validation"]["status"]="READY"
        self.assertFalse(validate_pair(e,a)["can_assemble"])

    def test_caps_still_cannot_mark_ready_without_host(self):
        e,a=demo()
        caps={"approved":True,"json_bytes":1000000,
              "scenes":100,"assets":100,"instances":100}
        r=validate_pair(e,a,caps=caps)
        self.assertEqual(r["error_count"],0)
        self.assertEqual(r["status"],"NEEDS_REVIEW")
        self.assertTrue(has(r,"E_HOST_UNVERIFIED","REVIEW"))
        self.assertFalse(r["can_assemble"])

    def test_declared_resource_limit_enforced(self):
        e,a=demo()
        caps={"approved":True,"json_bytes":1000000,
              "scenes":1,"assets":100,"instances":100}
        self.assertTrue(has(validate_pair(e,a,caps=caps),
                            "E_RESOURCE_LIMIT","ERROR"))

if __name__=="__main__":
    unittest.main()
