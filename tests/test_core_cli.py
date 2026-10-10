"""CLI read-only process smoke cases, no real Premiere."""
import hashlib
import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from core.validate_cli import read_json, run as validate_run

ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]


class CoreCLIProcessTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.root=Path(self.folder.name)
        edit, animation=demo()
        self.edit=self.root/"edit.json"
        self.anim=self.root/"animation.json"
        self.edit.write_text(json.dumps(edit),encoding="utf-8")
        self.anim.write_text(json.dumps(animation),encoding="utf-8")

    def tearDown(self):
        self.folder.cleanup()

    def run_cli(self,*extra):
        args=[sys.executable,"-m","core.validate_cli",
              "--edit",str(self.edit),"--animation",str(self.anim),
              "--max-json-bytes","100000",*extra]
        done=subprocess.run(args,capture_output=True,text=True,cwd=ROOT,
                            timeout=15)
        self.assertTrue(done.stdout,done.stderr)
        return done.returncode,json.loads(done.stdout)

    def _create_real_import_fixture(self):
        from tests.test_core_import_snapshot import PNG, WAV, MP4
        edit=json.loads(self.edit.read_text(encoding="utf-8"))
        sources={
            "srt": b"1\\n00:00:00,000 --> 00:00:05,000\\nFirst\\n\\n2\\n00:00:05,000 --> 00:00:06,400\\nSecond\\n\\n3\\n00:00:06,400 --> 00:00:11,000\\nThird\\n",
            "audio": WAV,
            "background": MP4,
        }
        # Unescape the literal newline escapes once; cue text is test-only.
        sources["srt"]=sources["srt"].replace(b"\\n",b"\n")
        for key,data in sources.items():
            rel=edit["sources"][key]["path"]
            path=self.root/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
            edit["sources"][key]["sha256"]=hashlib.sha256(data).hexdigest()
        for aid,record in edit["assets"].items():
            path=self.root/record["path"]
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(PNG)
            record["sha256"]=hashlib.sha256(PNG).hexdigest()
        self.edit.write_text(json.dumps(edit),encoding="utf-8")

    def test_json_input_same_bytes_replacement_during_open_rejected(self):
        # Even an identical SHA does not excuse a different open file ID.
        alt=self.root/"same_bytes_replacement.json"
        alt.write_bytes(self.edit.read_bytes())
        original_open=os.open
        replacements=0

        def swap_before_open(path,flags,*args,**kwargs):
            nonlocal replacements
            if Path(path).name=="edit.json":
                os.replace(alt,self.edit)
                replacements+=1
            return original_open(path,flags,*args,**kwargs)

        with patch("core.validate_cli.os.open",side_effect=swap_before_open):
            with self.assertRaisesRegex(ValueError,"E_JSON_INPUT_CHANGED"):
                read_json(self.edit,100000)
        self.assertEqual(replacements,1)
        self.assertFalse(alt.exists())

    def test_json_input_growth_after_stat_cannot_bypass_byte_cap(self):
        alt=self.root/"grown_input.json"
        alt.write_bytes(self.edit.read_bytes()+b"x"*100001)
        original_open=os.open
        replacements=0

        def grow_before_open(path,flags,*args,**kwargs):
            nonlocal replacements
            if Path(path).name=="edit.json":
                os.replace(alt,self.edit)
                replacements+=1
            return original_open(path,flags,*args,**kwargs)

        with patch("core.validate_cli.os.open",side_effect=grow_before_open):
            with self.assertRaisesRegex(ValueError,"E_RESOURCE_LIMIT"):
                read_json(self.edit,100000)
        self.assertEqual(replacements,1)

    def test_json_input_swap_cli_is_sanitized_fail_closed(self):
        old=self.edit.read_bytes()
        altered=old.replace(b"DEMO_001",b"DEMO_002")
        self.assertNotEqual(old,altered)
        self.assertEqual(len(old),len(altered))
        alt=self.root/"changed_input.json"
        alt.write_bytes(altered)
        original_open=os.open
        swaps=0

        def swap_before_open(path,flags,*args,**kwargs):
            nonlocal swaps
            if Path(path).name=="edit.json":
                os.replace(alt,self.edit)
                swaps+=1
            return original_open(path,flags,*args,**kwargs)

        stdout=io.StringIO()
        with patch("core.validate_cli.os.open",side_effect=swap_before_open), \
             redirect_stdout(stdout):
            rc=validate_run(["--edit",str(self.edit),"--animation",str(self.anim),
                             "--max-json-bytes","100000"])
        report=json.loads(stdout.getvalue())
        self.assertEqual(swaps,1)
        self.assertEqual(rc,2)
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertFalse(report["can_assemble"])
        self.assertIn("E_JSON_INPUT_CHANGED",[x["code"] for x in report["issues"]])
        self.assertNotIn(str(self.root),stdout.getvalue())
        self.assertNotIn("DEMO_001",stdout.getvalue())

    def test_import_snapshot_cli_returns_only_non_authorizing_counts(self):
        self._create_real_import_fixture()
        code,r=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000","--max-srt-cues","10",
            "--include-import-snapshot","--max-import-items","8")
        self.assertEqual(code,3,r)
        snap=r["import_snapshot"]
        self.assertEqual(snap["status"],"CANDIDATE_NOT_AUTHORIZED")
        self.assertFalse(snap["can_import"])
        self.assertEqual(snap["item_count"],6)
        self.assertEqual(snap["import_count"],5)
        self.assertEqual(len(snap["inventory_sha256"]),64)
        self.assertNotIn(str(self.root),json.dumps(r))
        self.assertNotIn("absolute_path",json.dumps(r))
        self.assertFalse(r["can_assemble"])

    def test_import_snapshot_detects_alias_of_two_assets(self):
        self._create_real_import_fixture()
        edit=json.loads(self.edit.read_text(encoding="utf-8"))
        edit["assets"]["A003"]["path"]=edit["assets"]["A001"]["path"]
        self.edit.write_text(json.dumps(edit),encoding="utf-8")
        code,r=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000","--max-srt-cues","10",
            "--include-import-snapshot","--max-import-items","8")
        self.assertEqual(code,2)
        self.assertIn("E_MEDIA_ALIAS_AMBIGUOUS",
                      [x["code"] for x in r["issues"]])
        self.assertNotIn("import_snapshot",r)

    def test_import_snapshot_requires_explicit_development_item_limit(self):
        self._create_real_import_fixture()
        code,r=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000","--max-srt-cues","10",
            "--include-import-snapshot")
        self.assertEqual(code,2)
        self.assertIn("E_CONFIG_LIMITS_UNVERIFIED",
                      [x["code"] for x in r["issues"]])

    def test_missing_optional_ffprobe_stays_review_not_ready(self):
        code,result=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000","--max-srt-cues","100")
        self.assertEqual(code,2)
        self.assertFalse(result["can_assemble"])
        self.assertIn("E_FFPROBE_SKIPPED",
                      [x["code"] for x in result["issues"]])

    def test_four_track_preflight_requires_explicit_media_budgets(self):
        code,r=self.run_cli("--include-track-preflight")
        self.assertEqual(code,2)
        self.assertFalse(r["can_assemble"])
        self.assertIn("E_CONFIG_LIMITS_UNVERIFIED",
                      [x["code"] for x in r["issues"]])

    def test_four_track_preflight_skips_if_media_missing(self):
        code,r=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000","--max-srt-cues","10",
            "--max-import-items","20","--include-track-preflight")
        self.assertEqual(code,2)
        self.assertFalse(r["can_assemble"])
        self.assertIn("E_TRACK_PREFLIGHT_SKIPPED",
                      [x["code"] for x in r["issues"]])

    def test_medium_both_phase_reference_cli_never_claims_backend(self):
        code,result=self.run_cli("--include-animation-phases",
            "--max-animation-instances","20")
        self.assertEqual(code,3)
        phase=result["animation_phases"]
        self.assertEqual(phase["status"],"REFERENCE_SCHEDULE_ONLY")
        self.assertEqual(phase["instance_count"],3)
        self.assertEqual(phase["zero_hold_count"],0)
        self.assertFalse(phase["can_render"])
        self.assertFalse(result["can_assemble"])
        self.assertIn("E_FX_BACKEND_UNVERIFIED",
                      [x["code"] for x in result["issues"]])
        self.assertNotIn("asset_placements",str(phase))

    def test_animation_phases_budget_required_and_fail_closed(self):
        code,result=self.run_cli("--include-animation-phases")
        self.assertEqual(code,2)
        self.assertNotIn("animation_phases",result)
        self.assertIn("E_FX_RESOURCE_LIMIT_UNVERIFIED",
                      [x["code"] for x in result["issues"]])

    def test_both_reference_too_short_is_e_time_006(self):
        edit=json.loads(self.edit.read_text("utf-8"))
        edit["scenes"][0]["end_frame"]=47
        edit["scenes"][0]["assets"][0]["end_frame"]=47
        edit["scenes"][1]["start_frame"]=47
        edit["scenes"][1]["assets"][0]["start_frame"]=47
        self.edit.write_text(json.dumps(edit),encoding="utf-8")
        code,result=self.run_cli("--include-animation-phases",
            "--max-animation-instances","20")
        self.assertEqual(code,2)
        self.assertIn("E_TIME_006",[x["code"] for x in result["issues"]])
        self.assertNotIn("animation_phases",result)

    def test_draft_timeline_is_non_executable_and_deterministic(self):
        code,result=self.run_cli("--include-draft")
        self.assertEqual(code,3)
        self.assertEqual(result["draft"]["status"],"DRAFT_NOT_EXECUTABLE")
        self.assertFalse(result["draft"]["can_assemble"])
        self.assertEqual(result["draft"]["total_frames"],330)
        self.assertEqual(result["draft"]["asset_instance_count"],3)
        self.assertEqual(len(result["draft"]["operation_digest_sha256"]),64)

    def test_structural_candidate_is_review_not_ready(self):
        code,result=self.run_cli()
        self.assertEqual(code,3)
        self.assertEqual(result["status"],"NEEDS_REVIEW")
        self.assertEqual(result["error_count"],0)
        self.assertFalse(result["can_assemble"])
        self.assertEqual(result["asset_instance_count"],3)

    def test_malformed_document_exits_nonzero_and_hides_source(self):
        self.edit.write_text('{"top_secret":"do not print",}',encoding="utf-8")
        code,result=self.run_cli()
        self.assertEqual(code,2)
        self.assertEqual(result["status"],"PREFLIGHT_FAIL")
        self.assertNotIn("top_secret",json.dumps(result))
        self.assertNotIn(str(self.root),json.dumps(result))

    def test_media_root_missing_files_fail_closed(self):
        code,result=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000",
            "--max-srt-cues","100")
        self.assertEqual(code,2)
        self.assertEqual(result["status"],"PREFLIGHT_FAIL")
        self.assertEqual(result["media_file_count"],0)
        self.assertTrue(any(x["code"]=="E_MEDIA_MISSING"
                            for x in result["issues"]))

    def test_media_root_requires_explicit_dev_limits(self):
        code,result=self.run_cli("--media-root",str(self.root))
        self.assertEqual(code,2)
        self.assertFalse(result["can_assemble"])
        self.assertTrue(any(x["code"]=="E_CONFIG_LIMITS_UNVERIFIED" and
                            x["severity"]=="ERROR" for x in result["issues"]))

    def test_duplicate_key_rejected_without_leaking_json(self):
        original=self.edit.read_text(encoding="utf-8")
        self.edit.write_text(original.replace('"project_id": "DEMO_001"',
                           '"project_id":"other","project_id": "DEMO_001"'),encoding="utf-8")
        code,result=self.run_cli()
        self.assertEqual(code,2)
        self.assertIn("E_JSON_SCHEMA",[x["code"] for x in result["issues"]])
        self.assertNotIn("other",json.dumps(result))


    def test_invalid_pair_skips_media_audit_safely(self):
        edit=json.loads(self.edit.read_text(encoding="utf-8"))
        edit["scenes"][0]["assets"][0]["entry_evidence"]["cue_id"]=["BAD"]
        self.edit.write_text(json.dumps(edit),encoding="utf-8")
        code,result=self.run_cli("--media-root",str(self.root),
            "--max-media-bytes","100000","--max-srt-cues","20")
        self.assertEqual(code,2)
        self.assertIn("E_MEDIA_AUDIT_SKIPPED",
                      [x["code"] for x in result["issues"]])
        self.assertNotIn("media_file_count",result)

if __name__=="__main__":
    unittest.main()
