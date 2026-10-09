"""STEP11 fail-closed, append-only local transaction *audit journal*.

This is a durable offline foundation for a future audited Premiere dispatcher;
it does NOT call Adobe or authorize project mutation. Intent must be durably
recorded before a future host call; a missing result after a crash is UNKNOWN,
not permission to retry. SHA chaining detects corruption, NOT malicious edits
(an unkeyed digest is not an authenticity signature).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

from .contracts import loads_strict

JOB_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{7,63}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
TICK = re.compile(r"(0|[1-9][0-9]{0,35})\Z")
EVENTS = {"START", "INTENT", "RESULT", "CLOSE"}
MAX_JOURNAL_BYTES = 8 * 1024 * 1024  # Development anti-abuse bound only.
MAX_LINE_BYTES = 1024 * 1024


class JournalError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canonical(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(data: Any) -> str:
    return hashlib.sha256(_canonical(data)).hexdigest()


def _valid_sha(x: Any) -> bool:
    return type(x) is str and SHA.fullmatch(x) is not None


def _valid_index(x: Any) -> bool:
    return type(x) is int and x >= 0


def _root(root: Path) -> Path:
    try:
        given = Path(root)
        if given.is_symlink() or not given.is_dir():
            raise JournalError("E_JOURNAL_ROOT_INVALID")
        result = given.resolve(strict=True)
        if not result.is_dir():
            raise JournalError("E_JOURNAL_ROOT_INVALID")
        return result
    except (TypeError, OSError, ValueError) as e:
        raise JournalError("E_JOURNAL_ROOT_INVALID") from e


def _path(root: Path, job_id: str) -> Path:
    if type(job_id) is not str or JOB_ID.fullmatch(job_id) is None:
        raise JournalError("E_JOURNAL_JOB_ID_INVALID")
    return _root(root) / ("AIJSON_JOB_" + job_id + ".jsonl")


def _check_candidate(candidate: dict, max_operations: int) -> list[str]:
    if (type(candidate) is not dict or
        candidate.get("schema_version") not in (
            "track-placement-candidate-v1", "derived-track-candidate-v1") or
        candidate.get("status") != "CANDIDATE_NOT_EXECUTABLE" or
        candidate.get("can_import") is not False or
        candidate.get("can_assemble") is not False or
        not _valid_sha(candidate.get("operation_sha256")) or
        type(max_operations) is not int or max_operations <= 0 or
        type(candidate.get("placements")) is not list or
        not 0 < len(candidate["placements"]) <= max_operations):
        raise JournalError("E_JOURNAL_CANDIDATE_INVALID")
    hashes = []
    seen = set()
    for p in candidate["placements"]:
        if type(p) is not dict:
            raise JournalError("E_JOURNAL_CANDIDATE_INVALID")
        key = p.get("instance_key")
        start, end = p.get("start_ticks"), p.get("end_ticks")
        if (type(key) is not str or not 0 < len(key) <= 144 or
            key in seen or type(p.get("target_track")) is not str or
            p["target_track"] not in ("V1", "V2", "V3", "A1") or
            type(start) is not str or TICK.fullmatch(start) is None or
            type(end) is not str or TICK.fullmatch(end) is None or
            int(start) >= int(end)):
            raise JournalError("E_JOURNAL_CANDIDATE_INVALID")
        seen.add(key)
        hashes.append(_digest(p))
    return hashes


def _event(kind: str, seq: int, previous: str, job_id: str,
           **extra: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "schema_version": "operation-journal-entry-v1",
        "event": kind, "seq": seq,
        "prev_sha256": previous, "job_id": job_id,
    }
    entry.update(extra)
    entry["entry_sha256"] = _digest(entry)
    return entry


def _decode_lines(raw: bytes) -> list[dict[str, Any]]:
    if not raw or len(raw) > MAX_JOURNAL_BYTES or not raw.endswith(b"\n"):
        raise JournalError("E_JOURNAL_TRUNCATED")
    result = []
    for line in raw.splitlines():
        if not line or len(line) > MAX_LINE_BYTES:
            raise JournalError("E_JOURNAL_CORRUPT")
        try:
            event = loads_strict(line)
        except (TypeError, ValueError, UnicodeError) as exc:
            raise JournalError("E_JOURNAL_CORRUPT") from exc
        if type(event) is not dict:
            raise JournalError("E_JOURNAL_CORRUPT")
        result.append(event)
    return result


def _state(records: list[dict[str, Any]]) -> dict[str, Any]:
    prev = "0" * 64
    job_id: str | None = None
    hashes: list[str] | None = None
    completed = 0
    pending: int | None = None
    status = "NOT_STARTED"
    for i, row in enumerate(records):
        if (row.get("schema_version") != "operation-journal-entry-v1" or
                row.get("event") not in EVENTS or row.get("seq") != i or
                row.get("prev_sha256") != prev or
                type(row.get("job_id")) is not str or
                not _valid_sha(row.get("entry_sha256"))):
            raise JournalError("E_JOURNAL_CORRUPT")
        sha = row["entry_sha256"]
        material = dict(row)
        del material["entry_sha256"]
        if _digest(material) != sha:
            raise JournalError("E_JOURNAL_HASH_MISMATCH")
        prev = sha
        event = row["event"]
        if event == "START":
            h = row.get("operation_hashes")
            if (i != 0 or set(row) != {
                    "schema_version", "event", "seq", "prev_sha256",
                    "job_id", "entry_sha256", "plan_sha256", "operation_hashes"} or
                    not _valid_sha(row.get("plan_sha256")) or
                    type(h) is not list or not h or len(h) > 10000 or
                    not all(_valid_sha(x) for x in h) or
                    JOB_ID.fullmatch(row["job_id"]) is None):
                raise JournalError("E_JOURNAL_CORRUPT")
            hashes = h
            job_id = row["job_id"]
            status = "OPEN_NOT_AUTHORIZED"
        elif job_id is None or row["job_id"] != job_id or hashes is None:
            raise JournalError("E_JOURNAL_CORRUPT")
        elif event == "INTENT":
            if (set(row) != {"schema_version", "event", "seq", "prev_sha256",
                             "job_id", "entry_sha256", "operation_index",
                             "operation_hash"} or
                    status != "OPEN_NOT_AUTHORIZED" or pending is not None or
                    completed >= len(hashes) or
                    row.get("operation_index") != completed or
                    row.get("operation_hash") != hashes[completed]):
                raise JournalError("E_JOURNAL_CORRUPT")
            pending = completed
            status = "UNKNOWN_AFTER_INTENT"
        elif event == "RESULT":
            if (set(row) != {"schema_version", "event", "seq", "prev_sha256",
                             "job_id", "entry_sha256", "operation_index",
                             "outcome", "result_code"} or
                    status != "UNKNOWN_AFTER_INTENT" or
                    row.get("operation_index") != pending or
                    row.get("outcome") not in ("READBACK_MATCHED", "INCOMPLETE") or
                    type(row.get("result_code")) is not str or
                    re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", row["result_code"]) is None):
                raise JournalError("E_JOURNAL_CORRUPT")
            pending = None
            if row["outcome"] == "INCOMPLETE":
                status = "INCOMPLETE_MANUAL_REVIEW"
            else:
                completed += 1
                status = "OPEN_NOT_AUTHORIZED"
        else:  # CLOSE
            if (set(row) != {"schema_version", "event", "seq", "prev_sha256",
                             "job_id", "entry_sha256"} or
                    status != "OPEN_NOT_AUTHORIZED" or
                    pending is not None or completed != len(hashes)):
                raise JournalError("E_JOURNAL_CORRUPT")
            status = "CLOSED_RECORDED_UNVERIFIED"
    if job_id is None or hashes is None:
        raise JournalError("E_JOURNAL_CORRUPT")
    return {
        "status": status, "job_id": job_id, "operation_count": len(hashes),
        "completed_count": completed, "pending_index": pending,
        "last_sha256": prev, "next_seq": len(records), "operation_hashes": hashes,
        "can_retry": False, "can_assemble": False, "host_verified": False,
    }


def read_journal(root: Path, job_id: str) -> dict[str, Any]:
    path = _path(root, job_id)
    if path.is_symlink():
        raise JournalError("E_JOURNAL_UNSAFE_FILE")
    try:
        with path.open("rb") as f:
            raw = f.read(MAX_JOURNAL_BYTES + 1)
    except OSError as exc:
        raise JournalError("E_JOURNAL_READ_FAILED") from exc
    state = _state(_decode_lines(raw))
    if state["job_id"] != job_id:
        raise JournalError("E_JOURNAL_CORRUPT")
    return state


class TransactionJournal:
    """One intentional append at a time; no persistent lock cleanup on crash."""

    def __init__(self, root: Path, job_id: str):
        self.root = _root(root)
        self.job_id = job_id
        self.path = _path(self.root, job_id)
        self.lock = self.path.with_suffix(".lock")

    @classmethod
    def start(cls, root: Path, job_id: str, candidate: dict[str, Any],
              *, max_operations: int) -> "TransactionJournal":
        hashes = _check_candidate(candidate, max_operations)
        journal = cls(root, job_id)
        event = _event("START", 0, "0" * 64, job_id,
                       plan_sha256=candidate["operation_sha256"],
                       operation_hashes=hashes)
        try:
            with journal.path.open("xb") as f:
                os.chmod(journal.path, 0o600)
                f.write(_canonical(event) + b"\n")
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError as exc:
            raise JournalError("E_JOURNAL_ALREADY_EXISTS") from exc
        except OSError as exc:
            raise JournalError("E_JOURNAL_CREATE_FAILED") from exc
        return journal

    def _append(self, kind: str, **kwargs: Any) -> dict[str, Any]:
        # .lock is an exclusive lease. If a process dies, the stale lock is
        # deliberately NOT removed automatically: an operator must inspect it.
        try:
            lock_fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise JournalError("E_JOURNAL_LOCKED") from exc
        except OSError as exc:
            raise JournalError("E_JOURNAL_LOCK_FAILED") from exc
        try:
            os.close(lock_fd)
            state = read_journal(self.root, self.job_id)
            event = _event(kind, state["next_seq"], state["last_sha256"],
                           self.job_id, **kwargs)
            # Validate transitions by replaying the would-be next event,
            # before any physical append.
            with self.path.open("rb") as f:
                prior = _decode_lines(f.read(MAX_JOURNAL_BYTES + 1))
            projected = _state(prior + [event])
            data = _canonical(event) + b"\n"
            if self.path.stat().st_size + len(data) > MAX_JOURNAL_BYTES:
                raise JournalError("E_JOURNAL_RESOURCE_LIMIT")
            with self.path.open("ab") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            return projected
        except JournalError:
            raise
        except (OSError, ValueError) as exc:
            raise JournalError("E_JOURNAL_WRITE_FAILED") from exc
        finally:
            # Only remove the lock created by this call, not the journal.
            try:
                self.lock.unlink()
            except OSError:
                pass

    def record_intent(self, index: int) -> dict[str, Any]:
        if not _valid_index(index):
            raise JournalError("E_JOURNAL_INDEX_INVALID")
        state = read_journal(self.root, self.job_id)
        if index >= state["operation_count"]:
            raise JournalError("E_JOURNAL_INDEX_INVALID")
        return self._append("INTENT", operation_index=index,
                            operation_hash=state["operation_hashes"][index])

    def record_result(self, index: int, outcome: str, code: str) -> dict[str, Any]:
        if (not _valid_index(index) or outcome not in ("READBACK_MATCHED", "INCOMPLETE")
                or type(code) is not str or
                re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", code) is None):
            raise JournalError("E_JOURNAL_RESULT_INVALID")
        return self._append("RESULT", operation_index=index, outcome=outcome,
                            result_code=code)

    def close(self) -> dict[str, Any]:
        return self._append("CLOSE")
