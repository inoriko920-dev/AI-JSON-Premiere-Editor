"""Pure deterministic V1/V2/V3/A1 frame-lane preparation for Premiere 2024.

This module calculates a *non-executable* lane map. The caller MUST supply
host-confirmed whole-frame source durations, never a rounded FFprobe estimate.
No Premiere writes, source trimming, audio padding, waveform edits, or FFmpeg.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


class LanePlanError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _frames(n: Any) -> bool:
    return type(n) is int and n > 0


def plan_lanes(
    placement: dict[str, Any],
    *,
    background_source_frames: int,
    narration_source_frames: int,
    max_background_segments: int,
) -> dict[str, Any]:
    """Map verified source lengths against intended timeline frames.

    Final V1 segment may require trim: it is explicitly flagged as pending.
    A1 narration must exactly match the frame horizon; never silently pad/cut.
    Visuals carry unresolved still source duration/transition transforms.
    """
    if (type(placement) is not dict or
        placement.get("schema_version") != "host-tick-placement-draft-v1" or
        placement.get("status") != "DRAFT_NOT_EXECUTABLE" or
        placement.get("can_assemble") is not False or
        not _frames(background_source_frames) or
        not _frames(narration_source_frames) or
        not _frames(max_background_segments)):
        raise LanePlanError("E_LANE_INPUT_UNVERIFIED")
    source = placement.get("placements")
    if not isinstance(source, list) or not source:
        raise LanePlanError("E_LANE_INPUT_UNVERIFIED")
    # The host timebase is carried as a string; no conversion to float or fps.
    ticks = placement.get("ticks_per_frame")
    end_ticks = placement.get("sequence_end_ticks")
    if (not isinstance(ticks, str) or not ticks.isascii() or not ticks.isdecimal()
        or int(ticks) <= 0 or not isinstance(end_ticks, str) or
        not end_ticks.isascii() or not end_ticks.isdecimal()):
        raise LanePlanError("E_LANE_TIMEBASE_UNVERIFIED")
    total_ticks = int(end_ticks)
    frame_ticks = int(ticks)
    if total_ticks <= 0 or total_ticks % frame_ticks:
        raise LanePlanError("E_LANE_TIMEBASE_UNVERIFIED")
    total = total_ticks // frame_ticks
    if not _frames(total):
        raise LanePlanError("E_LANE_INPUT_UNVERIFIED")
    if narration_source_frames != total:
        raise LanePlanError("E_NARRATION_DURATION_POLICY")
    needed = (total + background_source_frames - 1) // background_source_frames
    if needed > max_background_segments:
        raise LanePlanError("E_RESOURCE_LIMIT")

    v1: list[dict[str, Any]] = []
    for i in range(needed):
        start = i * background_source_frames
        end = min(total, start + background_source_frames)
        duration = end - start
        v1.append({
            "track": "V1", "media_role": "background",
            "segment_index": i,
            "start_frame": start, "end_frame": end,
            "source_in_frame": 0, "source_out_frame": duration,
            "start_ticks": str(start * frame_ticks),
            "end_ticks": str(end * frame_ticks),
            "requires_source_trim": duration != background_source_frames,
            "status": "SOURCE_RANGE_HOST_UNVERIFIED"
        })
    a1 = [{
        "track": "A1", "media_role": "narration",
        "start_frame": 0, "end_frame": total,
        "start_ticks": "0", "end_ticks": end_ticks,
        "source_in_frame": 0, "source_out_frame": total,
        "requires_source_trim": False,
        "status": "SOURCE_RANGE_HOST_UNVERIFIED"
    }]
    visuals = []
    for p in source:
        if (not isinstance(p, dict) or p.get("track") not in ("V2","V3")
            or p.get("readback_verified") is not False
            or type(p.get("start_frame")) is not int
            or type(p.get("end_frame")) is not int
            or not 0 <= p["start_frame"] < p["end_frame"] <= total
            or p.get("start_ticks") != str(p["start_frame"]*frame_ticks)
            or p.get("end_ticks") != str(p["end_frame"]*frame_ticks)):
            raise LanePlanError("E_LANE_VISUAL_INVALID")
        visuals.append({
            "track": p["track"], "instance_key": p["instance_key"],
            "start_frame": p["start_frame"], "end_frame": p["end_frame"],
            "start_ticks": p["start_ticks"], "end_ticks": p["end_ticks"],
            "source_out_frame": None,
            "requires_source_trim": None,
            "status": "STILL_DURATION_AND_LAYOUT_UNVERIFIED"
        })
    lanes = {"V1": v1, "V2": [x for x in visuals if x["track"] == "V2"],
             "V3": [x for x in visuals if x["track"] == "V3"], "A1": a1}
    canonical = json.dumps(lanes, sort_keys=True, separators=(",",":"),
                           ensure_ascii=False).encode("utf-8")
    return {
        "schema_version": "four-lane-intent-v1",
        "status": "DRAFT_NOT_EXECUTABLE",
        "can_assemble": False,
        "total_frames": total,
        "ticks_per_frame": ticks,
        "background_segment_count": needed,
        "lanes": lanes,
        "digest_sha256": hashlib.sha256(canonical).hexdigest(),
        "pending": [
            "SOURCE_OUTPOINT_PER_CLIP_PREMIERE",
            "STILL_IMAGE_DEFAULT_DURATION_AND_TRIM",
            "NATIVE_TRACK_INSERT_AND_READBACK",
            "APPROVED_SINGLE_DOUBLE_LAYOUT",
            "TWENTY_ONE_BOTH_EFFECTS",
            "PREMIERE_HOST_G3"
        ]
    }
