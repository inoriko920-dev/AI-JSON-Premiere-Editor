"""STEP12 durable fsync journal + simulation-only dispatcher regressions."""
import copy
from pathlib import Path
import tempfile
import unittest

from core.transaction_dispatcher import (
    DispatchError, SimulatedReadback, simulate_one_operation, inspect_dispatch_state,
)
from core.transaction_journal import TransactionJournal, read_journal
from tests.test_core_transaction_journal import JOB, candidate


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plan = candidate()
        self.journal = TransactionJournal.start(
            self.root, JOB, self.plan, max_operations=20)

    def tearDown(self):
        self.tmp.cleanup()

    def one(self, index=0, simulator=None, plan=None):
        return simulate_one_operation(
            self.root, JOB, self.plan if plan is None else plan,
            index=index, max_operations=20,
            simulator=simulator if simulator is not None else SimulatedReadback())

    def code(self, expected, call):
        with self.assertRaises(DispatchError) as err:
            call()
        self.assertEqual(err.exception.code, expected)

    def test_intent_result_order_and_disk_resume(self):
        simulated = SimulatedReadback()
        for index in range(3):
            result = self.one(index, simulated)
            self.assertEqual(result["status"], "SIMULATED_MATCH_UNVERIFIED")
            self.assertEqual(result["completed_count"], index+1)
            self.assertFalse(result["can_execute"])
            self.assertFalse(result["host_verified"])
        self.assertEqual(len(simulated.calls), 3)
        state = inspect_dispatch_state(self.root, JOB)
        self.assertEqual(state["completed_count"], 3)
        self.assertFalse(state["can_retry"])
        self.assertEqual(self.journal.close()["status"], "CLOSED_RECORDED_UNVERIFIED")

    def test_out_of_order_index_has_no_side_effects(self):
        fake=SimulatedReadback()
        original=self.journal.path.read_bytes()
        self.code("E_DISPATCH_SEQUENCE_MISMATCH",lambda: self.one(1,fake))
        self.assertEqual(fake.calls,())
        self.assertEqual(self.journal.path.read_bytes(),original)

    def test_only_built_in_mock_can_execute(self):
        original=self.journal.path.read_bytes()
        class ExternalHost:
            def apply(self,*args):
                raise Exception("would have modified Premiere")
        for suspicious in (ExternalHost(),lambda *_:"MATCH",None,{}):
            self.code("E_DISPATCH_HOST_NOT_APPROVED",lambda x=suspicious:
                      simulate_one_operation(self.root,JOB,self.plan,index=0,
                                            max_operations=20,simulator=x))
        self.assertEqual(self.journal.path.read_bytes(),original)

    def test_crash_preserves_unknown_intent_with_no_retry(self):
        fake=SimulatedReadback({0:"CRASH"})
        self.code("E_DISPATCH_UNKNOWN_AFTER_INTENT",lambda: self.one(0,fake))
        state=read_journal(self.root,JOB)
        self.assertEqual(state["status"],"UNKNOWN_AFTER_INTENT")
        self.assertEqual(state["pending_index"],0)
        self.assertFalse(state["can_retry"])
        self.code("E_JOURNAL_MANUAL_REVIEW_REQUIRED",lambda: self.one(0))
        self.assertEqual(len(fake.calls),1)

    def test_readback_mismatch_stops_remaining_operations(self):
        result=self.one(0,SimulatedReadback({0:"MISMATCH"}))
        self.assertEqual(result["journal_status"],"INCOMPLETE_MANUAL_REVIEW")
        self.assertFalse(result["can_retry"])
        self.code("E_JOURNAL_MANUAL_REVIEW_REQUIRED",lambda: self.one(1))

    def test_changed_original_plan_is_refused_without_host_call(self):
        changed=copy.deepcopy(self.plan)
        changed["placements"][0]["end_ticks"]="9999999"
        original=self.journal.path.read_bytes()
        fake=SimulatedReadback()
        self.code("E_JOURNAL_PLAN_CHANGED",lambda: self.one(0,fake,changed))
        self.assertEqual(fake.calls,())
        self.assertEqual(self.journal.path.read_bytes(),original)

    def test_boolean_negative_and_noninteger_index_fail_early(self):
        original=self.journal.path.read_bytes()
        for index in (True,-1,1.5,"0"):
            self.code("E_DISPATCH_INDEX_INVALID",lambda n=index:self.one(n))
        self.assertEqual(self.journal.path.read_bytes(),original)

    def test_reopening_cannot_replay_completed_index(self):
        fake=SimulatedReadback()
        self.one(0,fake)
        self.code("E_DISPATCH_SEQUENCE_MISMATCH",lambda:self.one(0,fake))
        self.assertEqual(len(fake.calls),1)
        later=SimulatedReadback()
        self.one(1,later)
        self.assertEqual([i for i,_ in later.calls],[1])

    def test_orphaned_lock_keeps_journal_unmodified(self):
        self.journal.lock.write_text("operator",encoding="utf8")
        fake=SimulatedReadback()
        self.code("E_JOURNAL_LOCKED",lambda:self.one(0,fake))
        self.assertEqual(fake.calls,())
        self.assertEqual(self.journal.lock.read_text(),"operator")

    def test_public_state_cannot_authorize_assembly_or_leak_media(self):
        progress=inspect_dispatch_state(self.root,JOB)
        for field in ("can_execute","can_retry","can_assemble","host_verified"):
            self.assertIs(progress[field],False)
        self.assertNotIn("Private",str(progress))

    def test_simulation_config_rejects_bad_outcomes(self):
        for config in ({True:"MATCH"},{-1:"MATCH"},{0:"READY"},{0:None}):
            self.code("E_SIMULATOR_CONFIGURATION_INVALID",
                      lambda x=config:SimulatedReadback(x))

    def test_corrupt_journal_does_not_fake_progress(self):
        self.journal.path.write_bytes(b"broken partial")
        self.code("E_JOURNAL_TRUNCATED",lambda:
                  inspect_dispatch_state(self.root,JOB))
        self.code("E_JOURNAL_TRUNCATED",lambda:self.one(0))


if __name__=="__main__":
    unittest.main()
