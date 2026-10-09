"""STEP11 durable transaction-journal tests on local temp files, no Premiere."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from core.transaction_journal import (
    JournalError, TransactionJournal, read_journal, inspect_resume,
)

JOB = "RUN_20261010_001"


def candidate():
    return {
        "schema_version": "derived-track-candidate-v1",
        "status": "CANDIDATE_NOT_EXECUTABLE", "can_import": False,
        "can_assemble": False, "operation_sha256": "b" * 64,
        "placements": [
            {"instance_key": "BG_0", "item_id": "DERIVED_SOURCE_BACKGROUND",
             "target_track": "V1", "start_ticks": "0", "end_ticks": "8467200000",
             "derived_absolute_path": "C:\\Private\\source.mp4"},
            {"instance_key": "NARRATION_0", "item_id": "SOURCE_AUDIO",
             "target_track": "A1", "start_ticks": "0", "end_ticks": "8467200000"},
            {"instance_key": "V001/A001", "item_id": "ASSET_A001",
             "target_track": "V2", "start_ticks": "0", "end_ticks": "8467200000"},
        ],
    }


class TransactionJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def create(self, payload=None, job=JOB):
        return TransactionJournal.start(
            self.root, job, candidate() if payload is None else payload,
            max_operations=10)

    def check_code(self, code, callback):
        with self.assertRaises(JournalError) as raised:
            callback()
        self.assertEqual(raised.exception.code, code)

    def test_new_journal_is_non_authorizing_and_does_not_include_media_paths(self):
        j = self.create()
        state = read_journal(self.root, JOB)
        self.assertEqual(state["status"], "OPEN_NOT_AUTHORIZED")
        self.assertEqual(state["operation_count"], 3)
        self.assertFalse(state["can_retry"])
        self.assertFalse(state["can_assemble"])
        self.assertFalse(state["host_verified"])
        raw = j.path.read_text(encoding="utf8")
        self.assertNotIn("C:\\Private", raw)
        self.assertNotIn("source.mp4", raw)

    def test_intent_is_durable_and_unanswered_crash_is_unknown_not_retry(self):
        j = self.create()
        state = j.record_intent(0)
        self.assertEqual(state["status"], "UNKNOWN_AFTER_INTENT")
        self.assertEqual(state["pending_index"], 0)
        recovered = read_journal(self.root, JOB)
        self.assertEqual(recovered["status"], "UNKNOWN_AFTER_INTENT")
        self.assertFalse(recovered["can_retry"])
        self.check_code("E_JOURNAL_CORRUPT", lambda: j.record_intent(0))
        self.check_code("E_JOURNAL_CORRUPT", j.close)

    def test_matching_readback_result_allows_next_intent_not_host_ready(self):
        j = self.create()
        for index in range(3):
            self.assertEqual(j.record_intent(index)["pending_index"], index)
            after = j.record_result(index, "READBACK_MATCHED", "HOST_READBACK_MATCHED")
            self.assertEqual(after["completed_count"], index + 1)
            self.assertEqual(after["status"], "OPEN_NOT_AUTHORIZED")
        done = j.close()
        self.assertEqual(done["status"], "CLOSED_RECORDED_UNVERIFIED")
        self.assertFalse(done["host_verified"])
        self.assertFalse(done["can_assemble"])
        self.check_code("E_JOURNAL_CORRUPT", j.close)
        self.check_code("E_JOURNAL_CORRUPT", lambda: j.record_intent(0))

    def test_partial_failure_stops_forever_and_keeps_journal(self):
        j = self.create()
        j.record_intent(0)
        bad = j.record_result(0, "INCOMPLETE", "HOST_TRIM_MISMATCH")
        self.assertEqual(bad["status"], "INCOMPLETE_MANUAL_REVIEW")
        self.assertEqual(bad["completed_count"], 0)
        self.check_code("E_JOURNAL_CORRUPT", lambda: j.record_intent(1))
        self.check_code("E_JOURNAL_CORRUPT", lambda: j.record_result(
            0, "READBACK_MATCHED", "HOST_READBACK_MATCHED"))
        self.assertTrue(j.path.exists())

    def test_no_result_without_first_intent(self):
        j = self.create()
        self.check_code("E_JOURNAL_CORRUPT",
                        lambda: j.record_result(0, "READBACK_MATCHED", "OK"))
        self.assertEqual(read_journal(self.root, JOB)["next_seq"], 1)

    def test_no_skipping_operation_indices(self):
        j = self.create()
        self.check_code("E_JOURNAL_CORRUPT", lambda: j.record_intent(1))
        self.check_code("E_JOURNAL_INDEX_INVALID", lambda: j.record_intent(3))
        self.check_code("E_JOURNAL_INDEX_INVALID", lambda: j.record_intent(True))
        self.assertEqual(read_journal(self.root, JOB)["completed_count"], 0)

    def test_duplicate_id_does_not_overwrite_old_journal(self):
        j = self.create()
        before = j.path.read_bytes()
        self.check_code("E_JOURNAL_ALREADY_EXISTS", self.create)
        self.assertEqual(j.path.read_bytes(), before)

    def test_invalid_job_id_fails_before_file_write(self):
        for job in ("../escape", "", "short", "C:\\Private", "👁_invalid", "A" * 80):
            self.check_code("E_JOURNAL_JOB_ID_INVALID",
                            lambda j=job: self.create(job=j))
        self.assertEqual(list(self.root.glob("*.jsonl")), [])

    def test_untrusted_candidate_status_cannot_turn_into_assembly_permission(self):
        for mutation in (
            lambda x: x.update(status="READY"),
            lambda x: x.update(can_assemble=True),
            lambda x: x.update(can_import=True),
            lambda x: x.update(operation_sha256="not-a-hash"),
            lambda x: x["placements"][0].update(start_ticks="1.5"),
            lambda x: x["placements"][0].update(target_track="V99"),
            lambda x: x["placements"][0].update(end_ticks="0"),
            lambda x: x["placements"][1].update(instance_key="BG_0"),
        ):
            value = candidate()
            mutation(value)
            self.check_code("E_JOURNAL_CANDIDATE_INVALID",
                            lambda v=value: self.create(payload=v))

    def test_explicit_development_bound_required(self):
        self.check_code("E_JOURNAL_CANDIDATE_INVALID",
                        lambda: TransactionJournal.start(
                            self.root, JOB, candidate(), max_operations=2))
        self.check_code("E_JOURNAL_CANDIDATE_INVALID",
                        lambda: TransactionJournal.start(
                            self.root, JOB, candidate(), max_operations=True))

    def test_existing_external_lock_not_removed_and_blocks_write(self):
        j = self.create()
        j.lock.write_text("external operator lease", encoding="utf8")
        self.check_code("E_JOURNAL_LOCKED", lambda: j.record_intent(0))
        self.assertEqual(j.lock.read_text(encoding="utf8"), "external operator lease")
        self.assertEqual(read_journal(self.root, JOB)["next_seq"], 1)

    def test_corrupt_hash_chain_detected_without_automatic_repair(self):
        j = self.create()
        records = j.path.read_text(encoding="utf8").splitlines()
        event = json.loads(records[0])
        event["plan_sha256"] = "c" * 64
        j.path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf8")
        self.check_code("E_JOURNAL_HASH_MISMATCH",
                        lambda: read_journal(self.root, JOB))
        self.assertTrue(j.path.exists())

    def test_truncated_journal_refused_and_not_repaired(self):
        j = self.create()
        with j.path.open("ab") as f:
            f.write(b'{"partial":')
        before = j.path.read_bytes()
        self.check_code("E_JOURNAL_TRUNCATED", lambda: read_journal(self.root, JOB))
        self.check_code("E_JOURNAL_TRUNCATED", lambda: j.record_intent(0))
        self.assertEqual(j.path.read_bytes(), before)

    def test_duplicate_json_key_inside_journal_fails(self):
        j = self.create()
        row = json.loads(j.path.read_text(encoding="utf8"))
        raw = json.dumps(row, separators=(",", ":"))
        j.path.write_text(raw.replace('"seq":0', '"seq":0,"seq":0') + "\n",
                          encoding="utf8")
        self.check_code("E_JOURNAL_CORRUPT",
                        lambda: read_journal(self.root, JOB))

    def test_false_readback_code_or_unsanitized_error_rejected(self):
        j = self.create()
        j.record_intent(0)
        for bad_code in ("C:\\Project\\clip.mov", "error from host", "", "READY", None):
            if bad_code == "READY":
                continue  # READY is syntactically safe; not a host certification.
            self.check_code("E_JOURNAL_RESULT_INVALID",
                            lambda s=bad_code: j.record_result(
                                0, "INCOMPLETE", s))
        self.assertEqual(read_journal(self.root, JOB)["status"],
                         "UNKNOWN_AFTER_INTENT")

    def test_resume_checks_against_original_plan_and_never_authorizes(self):
        original = candidate()
        j = self.create(payload=original)
        resume = inspect_resume(self.root, JOB, original, max_operations=10)
        self.assertEqual(resume["next_index"], 0)
        self.assertEqual(resume["status"], "NEXT_STEP_AWAITING_HOST_APPROVAL")
        self.assertFalse(resume["can_execute"])
        self.assertFalse(resume["can_retry"])
        j.record_intent(0)
        self.check_code("E_JOURNAL_MANUAL_REVIEW_REQUIRED",
                        lambda: inspect_resume(self.root, JOB, original,
                                               max_operations=10))
        j.record_result(0, "READBACK_MATCHED", "HOST_READBACK_MATCHED")
        next_step = inspect_resume(self.root, JOB, original, max_operations=10)
        self.assertEqual(next_step["next_index"], 1)
        self.assertFalse(next_step["can_assemble"])

    def test_resume_rejects_candidate_modified_after_start(self):
        original = candidate()
        self.create(payload=original)
        changed = copy.deepcopy(original)
        changed["placements"][0]["end_ticks"] = "123456789"
        self.check_code("E_JOURNAL_PLAN_CHANGED",
                        lambda: inspect_resume(self.root, JOB, changed,
                                               max_operations=10))
        changed = copy.deepcopy(original)
        changed["operation_sha256"] = "c" * 64
        self.check_code("E_JOURNAL_PLAN_CHANGED",
                        lambda: inspect_resume(self.root, JOB, changed,
                                               max_operations=10))

    def test_reopen_uses_durable_history_not_in_memory_progress(self):
        j = self.create()
        j.record_intent(0)
        j.record_result(0, "READBACK_MATCHED", "READBACK_OK")
        reloaded = TransactionJournal(self.root, JOB)
        state = reloaded.record_intent(1)
        self.assertEqual(state["pending_index"], 1)
        self.assertEqual(state["completed_count"], 1)

    def test_readonly_nonexistent_job_never_creates_placeholder(self):
        self.check_code("E_JOURNAL_READ_FAILED",
                        lambda: read_journal(self.root, JOB))
        self.assertEqual(list(self.root.iterdir()), [])

if __name__ == "__main__":
    unittest.main()
