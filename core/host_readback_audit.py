"""STEP14: fail-closed, read-only reconciliation of Premiere track readback.

This is NOT an Adobe host bridge or cryptographic attestation. It compares the
post-operation observation to the exact prefix of a frozen four-track candidate,
including source-relative IN/OUT. A matching mocked response cannot authorize
editing and must never be treated as G3 host evidence.
"""
from __future__ import annotations

import re
from typing import Any

TRACKS = {"V1": 0, "V2": 1, "V3": 2, "A1": 0}
SHA = re.compile(r"[a-f0-9]{64}\Z")
TICKS = re.compile(r"(0|[1-9][0-9]{0,35})\Z")
POSITIVE_TICK = re.compile(r"[1-9][0-9]{0,25}\Z")
SAFE_ID = re.compile(r"[A-Za-z0-9_.:-]{1,200}\Z")
GUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")


class ReadbackAuditError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ReadbackAuditError(code)


def _tick(value: Any) -> bool:
    return type(value) is str and TICKS.fullmatch(value) is not None


def _frame(value: Any) -> bool:
    return type(value) is int and 0 <= value <= 10000000


def _id(value: Any) -> bool:
    return type(value) is str and SAFE_ID.fullmatch(value) is not None


def _expected(candidate: dict, refs: dict[str, str], index: int,
              max_operations: int) -> dict[str, list[dict]]:
    _require(type(candidate) is dict and
             candidate.get("schema_version") in (
                 "track-placement-candidate-v1", "derived-track-candidate-v1")
             and candidate.get("status") == "CANDIDATE_NOT_EXECUTABLE"
             and candidate.get("can_import") is False
             and candidate.get("can_assemble") is False
             and type(candidate.get("operation_sha256")) is str
             and SHA.fullmatch(candidate["operation_sha256"]) is not None,
             "E_READBACK_PLAN_INVALID")
    operations = candidate.get("placements")
    _require(type(operations) is list and type(max_operations) is int
             and 0 < max_operations <= 100000
             and 0 < len(operations) <= max_operations
             and type(index) is int and -1 <= index < len(operations),
             "E_READBACK_OPERATION_INDEX_INVALID")
    tb = candidate.get("ticks_per_frame")
    _require(type(tb) is str and POSITIVE_TICK.fullmatch(tb) is not None,
             "E_READBACK_TIMEBASE_INVALID")
    timebase = int(tb)
    _require(type(refs) is dict and 0 < len(refs) <= max_operations
             and all(_id(k) and _id(v) for k, v in refs.items())
             and len(set(refs.values())) == len(refs),
             "E_READBACK_MEDIA_REFS_INVALID")
    out = {track: [] for track in TRACKS}
    keys: set[str] = set()
    for pos, row in enumerate(operations):
        _require(type(row) is dict and
                 type(row.get("instance_key")) is str and row["instance_key"]
                 and row["instance_key"] not in keys
                 and row.get("target_track") in TRACKS
                 and _id(row.get("item_id"))
                 and row["item_id"] in refs,
                 "E_READBACK_PLAN_INVALID")
        keys.add(row["instance_key"])
        start, end = row.get("start_frame"), row.get("end_frame")
        source_in, source_out = row.get("source_in_frame"), row.get("source_out_frame")
        _require(all(_frame(x) for x in (start, end, source_in, source_out))
                 and start < end and source_in < source_out
                 and source_out - source_in == end - start
                 and row.get("zero_based_track_index") == TRACKS[row["target_track"]]
                 and row.get("start_ticks") == str(start * timebase)
                 and row.get("end_ticks") == str(end * timebase),
                 "E_READBACK_PLAN_TIMING_INVALID")
        if pos <= index:
            out[row["target_track"]].append({
                "item_node_id": refs[row["item_id"]],
                "start_ticks": row["start_ticks"],
                "end_ticks": row["end_ticks"],
                "source_in_ticks": str(source_in * timebase),
                "source_out_ticks": str(source_out * timebase),
            })
    for track, rows in out.items():
        rows.sort(key=lambda x: int(x["start_ticks"]))
        if any(int(rows[i]["start_ticks"]) < int(rows[i-1]["end_ticks"])
               for i in range(1, len(rows))):
            raise ReadbackAuditError("E_READBACK_PLAN_TRACK_OVERLAP")
    return out


def audit_prefix(candidate: dict, observed: dict, refs: dict[str, str], *,
                 operation_index: int, sequence_id: str,
                 max_operations: int) -> dict[str, Any]:
    """Read-only check after operation_index; no journal writes or Premiere calls.

    All observed tracks MUST be present (including empty), to detect unwanted
    linked audio/video. Observations may come from mocks or an untrusted caller;
    this only verifies internal consistency, not actual host provenance.
    """
    try:
        expect = _expected(candidate, refs, operation_index, max_operations)
        _require(type(sequence_id) is str and GUID.fullmatch(sequence_id) is not None,
                 "E_READBACK_SEQUENCE_INVALID")
        _require(type(observed) is dict and
                 observed.get("schema_version") == "premiere-track-readback-v1"
                 and observed.get("status") == "CAPTURED_UNVERIFIED"
                 and observed.get("can_assemble") is False
                 and observed.get("sequence_id") == sequence_id,
                 "E_READBACK_SEQUENCE_MISMATCH")
        _require(observed.get("ticks_per_frame") == candidate["ticks_per_frame"],
                 "E_READBACK_TIMEBASE_MISMATCH")
        tracks = observed.get("tracks")
        _require(type(tracks) is dict and set(tracks) == set(TRACKS),
                 "E_READBACK_TRACK_SET_INVALID")
        seen_clip_ids: set[str] = set()
        count = 0
        for track in TRACKS:
            clips, intended = tracks[track], expect[track]
            _require(type(clips) is list and len(clips) <= max_operations,
                     "E_READBACK_TRACK_INVALID")
            _require(len(clips) == len(intended), "E_READBACK_CLIP_COUNT_MISMATCH")
            pairs = []
            for clip in clips:
                _require(type(clip) is dict and
                         set(clip) == {"clip_id", "item_node_id", "start_ticks",
                                      "end_ticks", "source_in_ticks",
                                      "source_out_ticks"}
                         and _id(clip.get("clip_id"))
                         and _id(clip.get("item_node_id"))
                         and clip["clip_id"] not in seen_clip_ids
                         and all(_tick(clip.get(k)) for k in
                                 ("start_ticks", "end_ticks",
                                  "source_in_ticks", "source_out_ticks")),
                         "E_READBACK_CLIP_INVALID")
                seen_clip_ids.add(clip["clip_id"])
                _require(int(clip["start_ticks"]) < int(clip["end_ticks"]) and
                         int(clip["source_in_ticks"]) < int(clip["source_out_ticks"]),
                         "E_READBACK_CLIP_TIMING_INVALID")
                pairs.append(clip)
            pairs.sort(key=lambda x: int(x["start_ticks"]))
            for actual, expected in zip(pairs, intended):
                if actual["item_node_id"] != expected["item_node_id"]:
                    raise ReadbackAuditError("E_READBACK_MEDIA_ID_MISMATCH")
                if (actual["start_ticks"] != expected["start_ticks"]
                        or actual["end_ticks"] != expected["end_ticks"]):
                    raise ReadbackAuditError("E_READBACK_SEQUENCE_TIMING_MISMATCH")
                if (actual["source_in_ticks"] != expected["source_in_ticks"]
                        or actual["source_out_ticks"] != expected["source_out_ticks"]):
                    raise ReadbackAuditError("E_READBACK_SOURCE_TRIM_MISMATCH")
            count += len(clips)
        return {
            "schema_version": "prefix-readback-audit-v1",
            "status": "READBACK_MATCHED_UNVERIFIED",
            "operation_index": operation_index,
            "matched_clip_count": count,
            "can_assemble": False, "host_verified": False,
            "can_retry": False, "code": "E_HOST_PROVENANCE_UNVERIFIED"
        }
    except ReadbackAuditError as exc:
        return {
            "schema_version": "prefix-readback-audit-v1",
            "status": "READBACK_MISMATCH",
            "operation_index": operation_index if type(operation_index) is int else None,
            "matched_clip_count": 0,
            "can_assemble": False, "host_verified": False,
            "can_retry": False, "code": exc.code
        }
