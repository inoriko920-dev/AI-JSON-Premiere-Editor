"""CLI read-only process smoke cases, no real Premiere."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

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


if __name__=="__main__":
    unittest.main()
