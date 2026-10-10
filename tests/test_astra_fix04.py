"""ASTRA FIX04 input-contract regressions; no host or source media writes."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

from core.contracts import validate_pair
from core.draft_compiler import build_draft, DraftCompileError

ROOT = Path(__file__).resolve().parents[1]
demo = runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]


class AstraFix04Tests(unittest.TestCase):
    def test_unsupported_transition_never_falls_back_to_cut(self):
        edit, animation = demo()
        original = build_draft(edit, animation)["operation_digest_sha256"]
        for invalid in (None, {}, {"unsupported":"DISSOLVE"},
                        ["CUT"], "DISSOLVE", "", 3, True):
            with self.subTest(value=invalid):
                edit["scenes"][0]["transition_policy"] = invalid
                validation = validate_pair(edit, animation)
                self.assertEqual(validation["status"], "PREFLIGHT_FAIL")
                self.assertTrue(any(x["pointer"] ==
                    "/EDIT_PLAN/scenes/0/transition_policy" and
                    x["severity"] == "ERROR" for x in validation["issues"]))
                with self.assertRaises(DraftCompileError):
                    build_draft(edit, animation)
        edit["scenes"][0]["transition_policy"] = "CUT"
        self.assertEqual(build_draft(edit, animation)["operation_digest_sha256"],
                         original)

    def test_deep_json_is_sanitized_input_failure_not_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            edit = root/"EDIT_PLAN.json"
            animation = root/"ANIMATION_PLAN.json"
            edit.write_text("["*20000+"0"+"]"*20000, encoding="utf-8")
            animation.write_text("{}", encoding="utf-8")
            done = subprocess.run(
                [sys.executable, "-m", "core.validate_cli",
                 "--edit", str(edit), "--animation", str(animation),
                 "--max-json-bytes", "1048576"],
                cwd=ROOT, capture_output=True, text=True, timeout=15)
            self.assertEqual(done.returncode, 2, done.stderr)
            result = json.loads(done.stdout)
            self.assertEqual(result["status"], "PREFLIGHT_FAIL")
            self.assertFalse(result["can_assemble"])
            self.assertEqual(result["issues"][0]["code"], "E_JSON_NESTING_LIMIT")
            self.assertNotIn(str(root), done.stdout)
            self.assertNotIn("RecursionError", done.stderr)


if __name__ == "__main__":
    unittest.main()
