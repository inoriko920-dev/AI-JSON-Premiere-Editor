"""STEP12: fsynced one-operation journal coordinator, simulation only.

Not a Premiere host bridge. Reject every external host callable. A future
reviewed dispatcher needs separate owner/capability authorization.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .transaction_journal import (
    JournalError, TransactionJournal, inspect_resume, read_journal,
    _check_candidate, _digest,
)


class DispatchError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class SimulatedCrash(RuntimeError):
    """A test-only crash following durable INTENT; never safe to retry."""


class SimulatedReadback:
    """In-memory transport, no callbacks, shell, Premiere or network."""

    __slots__ = ("_results", "_calls")

    def __init__(self, results: dict[int, str] | None = None):
        if results is None:
            results = {}
        if type(results) is not dict or any(
            type(k) is not int or k < 0 or v not in ("MATCH", "MISMATCH", "CRASH")
            for k, v in results.items()
        ):
            raise DispatchError("E_SIMULATOR_CONFIGURATION_INVALID")
        self._results = dict(results)
        self._calls: list[tuple[int, str]] = []

    @property
    def calls(self) -> tuple[tuple[int, str], ...]:
        return tuple(self._calls)

    def apply(self, index: int, operation_hash: str) -> str:
        self._calls.append((index, operation_hash))
        status = self._results.get(index, "MATCH")
        if status == "CRASH":
            raise SimulatedCrash("test-only crash after intent")
        return status


def simulate_one_operation(
    root: Path, job_id: str, candidate: dict[str, Any], *,
    index: int, max_operations: int, simulator: SimulatedReadback
) -> dict[str, Any]:
    """One fsynced INTENT, one mock readback, one durable RESULT if returned.

    A missing result is UNKNOWN, not a reason to re-execute. This only accepts
    the exact in-memory simulator class, not a user-supplied external callback.
    """
    if type(simulator) is not SimulatedReadback:
        raise DispatchError("E_DISPATCH_HOST_NOT_APPROVED")
    if type(index) is not int or index < 0:
        raise DispatchError("E_DISPATCH_INDEX_INVALID")
    if type(candidate) is not dict:
        raise DispatchError("E_DISPATCH_PLAN_INVALID")
    plan = deepcopy(candidate)
    try:
        hashes = _check_candidate(plan, max_operations)
        resume = inspect_resume(root, job_id, plan, max_operations=max_operations)
    except JournalError as exc:
        raise DispatchError(exc.code) from exc
    if resume["next_index"] != index or index >= len(hashes):
        raise DispatchError("E_DISPATCH_SEQUENCE_MISMATCH")
    expected = hashes[index]
    if (resume["operation_hash"] != expected or
            _digest(plan["placements"][index]) != expected):
        raise DispatchError("E_DISPATCH_OPERATION_CHANGED")
    journal = TransactionJournal(root, job_id)
    try:
        after_intent = journal.record_intent(index)
    except JournalError as exc:
        raise DispatchError(exc.code) from exc
    if after_intent["status"] != "UNKNOWN_AFTER_INTENT":
        raise DispatchError("E_DISPATCH_INTENT_NOT_DURABLE")
    try:
        response = simulator.apply(index, expected)
    except Exception as exc:
        # Never write a fake RESULT when the action outcome is unknown.
        raise DispatchError("E_DISPATCH_UNKNOWN_AFTER_INTENT") from exc
    if response not in ("MATCH", "MISMATCH"):
        raise DispatchError("E_DISPATCH_UNKNOWN_AFTER_INTENT")
    outcome = "READBACK_MATCHED" if response == "MATCH" else "INCOMPLETE"
    code = ("SIMULATED_READBACK_MATCHED" if response == "MATCH"
            else "SIMULATED_READBACK_MISMATCH")
    try:
        state = journal.record_result(index, outcome, code)
    except JournalError as exc:
        raise DispatchError("E_DISPATCH_RESULT_UNRECORDED") from exc
    return {
        "schema_version": "simulation-dispatch-result-v1",
        "status": "SIMULATED_MATCH_UNVERIFIED" if response == "MATCH"
                  else "SIMULATED_INCOMPLETE_MANUAL_REVIEW",
        "operation_index": index, "operation_hash": expected,
        "journal_status": state["status"],
        "completed_count": state["completed_count"],
        "can_execute": False, "can_retry": False,
        "can_assemble": False, "host_verified": False,
    }


def inspect_dispatch_state(root: Path, job_id: str) -> dict[str, Any]:
    """Sanitized progress without media paths, original JSON, or host approval."""
    try:
        state = read_journal(root, job_id)
    except JournalError as exc:
        raise DispatchError(exc.code) from exc
    return {
        "schema_version": "simulation-dispatch-progress-v1",
        "status": state["status"],
        "completed_count": state["completed_count"],
        "operation_count": state["operation_count"],
        "pending_index": state["pending_index"],
        "can_execute": False, "can_retry": False,
        "can_assemble": False, "host_verified": False,
    }
