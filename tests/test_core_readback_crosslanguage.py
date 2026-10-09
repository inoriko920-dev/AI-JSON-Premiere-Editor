"""Cross-language actual ES3 observer JSON -> strict Python prefix audit."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from core.host_readback_audit import audit_prefix
from tests.test_core_host_readback_audit import candidate, mapping, SEQ

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node unavailable in local runtime")
class ObserverProtocolIntegration(unittest.TestCase):
    def test_actual_es3_observer_mock_payload_matches_python_audit(self):
        proc=subprocess.run(
            [shutil.which("node"), "tests/emit_readback_fixture.cjs"],
            cwd=ROOT, capture_output=True, timeout=10, check=False
        )
        self.assertEqual(proc.returncode,0,proc.stderr.decode("utf-8",errors="replace"))
        self.assertLessEqual(len(proc.stdout),524288)
        captured=json.loads(proc.stdout)
        self.assertEqual(captured["status"],"CAPTURED_UNVERIFIED")
        result=audit_prefix(candidate(),captured,mapping(),operation_index=5,
                            sequence_id=SEQ,max_operations=20)
        self.assertEqual(result["status"],"READBACK_MATCHED_UNVERIFIED",result)
        self.assertEqual(result["matched_clip_count"],6)
        self.assertFalse(result["host_verified"])
        self.assertFalse(result["can_assemble"])

    def test_one_real_es3_observer_field_changed_is_detected(self):
        proc=subprocess.run(
            [shutil.which("node"), "tests/emit_readback_fixture.cjs"],
            cwd=ROOT, capture_output=True, timeout=10, check=False
        )
        self.assertEqual(proc.returncode,0)
        captured=json.loads(proc.stdout)
        captured["tracks"]["V1"][1]["source_out_ticks"]="1"
        result=audit_prefix(candidate(),captured,mapping(),operation_index=5,
                            sequence_id=SEQ,max_operations=20)
        self.assertEqual(result["status"],"READBACK_MISMATCH")
        self.assertEqual(result["code"],"E_READBACK_SOURCE_TRIM_MISMATCH")
        self.assertFalse(result["can_retry"])


if __name__=="__main__":
    unittest.main()
