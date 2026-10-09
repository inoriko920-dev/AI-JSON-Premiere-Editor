"""Lossless integer-frame → Premiere tick *draft* conversion.

Sequence.timebase is a decimal STRING (ticks per frame). JavaScript Numbers are
unsafe for many Premiere tick values. This module never rounds seconds, calls
Premiere, nor enables assembly. Only the real host may supply the timebase after
probing; tests use a mock-provided example.
"""
from __future__ import annotations

import re
from typing import Any

DECIMAL_TICKS = re.compile(r"[1-9][0-9]{0,25}\Z")
TRACK_INDEX = {"V2": 1, "V3": 2}  # 0-based indices, V1 background is reserved.


class HostTickDraftError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def frame_to_ticks(frame: int, ticks_per_frame: str) -> str:
    if type(frame) is not int or frame < 0:
        raise HostTickDraftError("E_HOST_FRAME_INVALID")
    if type(ticks_per_frame) is not str or DECIMAL_TICKS.fullmatch(ticks_per_frame) is None:
        raise HostTickDraftError("E_HOST_TIMEBASE_UNVERIFIED")
    return str(frame * int(ticks_per_frame))


def compile_tick_draft(draft: dict[str, Any],
                       ticks_per_frame: str) -> dict[str, Any]:
    """Read-only placement target list, strictly not a host edit instruction."""
    if (type(draft) is not dict or draft.get("status") != "DRAFT_NOT_EXECUTABLE"
            or draft.get("can_assemble") is not False
            or type(draft.get("total_frames")) is not int
            or draft["total_frames"] <= 0
            or not isinstance(draft.get("asset_placements"), list)):
        raise HostTickDraftError("E_HOST_DRAFT_NOT_VERIFIED")
    # Explicitly validate timebase even if no asset entries.
    sequence_end = frame_to_ticks(draft["total_frames"], ticks_per_frame)
    placements: list[dict[str, Any]] = []
    intervals: dict[str, list[tuple[int, int]]] = {"V2": [], "V3": []}
    unique: set[str] = set()
    for item in draft["asset_placements"]:
        if type(item) is not dict:
            raise HostTickDraftError("E_HOST_DRAFT_INVALID")
        key = item.get("instance_key")
        start, end = item.get("start_frame"), item.get("end_frame")
        track = item.get("target_track")
        if (not isinstance(key, str) or not key or key in unique or
                track not in TRACK_INDEX or
                type(start) is not int or type(end) is not int or
                not 0 <= start < end <= draft["total_frames"] or
                item.get("mode") != "BOTH"):
            raise HostTickDraftError("E_HOST_DRAFT_INVALID")
        unique.add(key)
        intervals[track].append((start, end))
        placements.append({
            "instance_key": key,
            "track": track,
            "zero_based_track_index": TRACK_INDEX[track],
            "start_frame": start,
            "end_frame": end,
            "start_ticks": frame_to_ticks(start, ticks_per_frame),
            "end_ticks": frame_to_ticks(end, ticks_per_frame),
            "duration_ticks": frame_to_ticks(end-start, ticks_per_frame),
            "source_in_ticks": None,
            "source_out_ticks": None,
            "effect_backend": "UNVERIFIED",
            "readback_verified": False,
        })
    for spans in intervals.values():
        spans.sort()
        for i in range(1, len(spans)):
            if spans[i][0] < spans[i-1][1]:
                raise HostTickDraftError("E_HOST_TRACK_OVERLAP")
    return {
        "schema_version": "host-tick-placement-draft-v1",
        "status": "DRAFT_NOT_EXECUTABLE",
        "can_assemble": False,
        "ticks_per_frame": ticks_per_frame,
        "sequence_end_ticks": sequence_end,
        "placements": placements,
        "host_readback": "NOT_TESTED",
        "missing": ["MEDIA_SOURCE_IN_OUT",
                    "BACKGROUND_LOOP_AND_AUDIO",
                    "APPROVED_LAYOUT",
                    "ANIMATION_BOTH_BACKEND",
                    "PREMIERE_HOST_READBACK"],
    }
