"""Pure, deterministic track placement CANDIDATE; never writes Premiere.

V1 background video loops, V2/V3 visuals from EDIT_PLAN, A1 narration.
Source-length/fps proofs still need decoder + actual Premiere verification.
No invented phase duration, crop, timing ticks or readiness permission.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .draft_compiler import DraftCompileError, build_draft
from .host_ticks import HostTickDraftError, compile_tick_draft, frame_to_ticks

TRACKS = ("V1", "V2", "V3", "A1")
MAX_OPERATIONS_DEV = 4096  # developer safe-memory cap, NOT approved production limit


class TimelineCandidateError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def build_timeline_candidate(edit: dict[str, Any],
                             animation: dict[str, Any],
                             snapshot: dict[str, Any],
                             *,
                             ticks_per_frame: str,
                             background_source_frames: int,
                             audio_source_frames: int) -> dict[str, Any]:
    """Plan precise non-overwriting clip placements for a NEW empty sequence only.

    duration arguments are separately observed *candidate* durations at 30fps;
    not accepted as a trusted real codec or host measurement. The final host
    transaction remains gated and disconnected.
    """
    if not isinstance(snapshot, dict) or (
        snapshot.get("schema_version") != "verified-media-snapshot-v1" or
        snapshot.get("status") != "CANDIDATE_NOT_AUTHORIZED" or
        snapshot.get("can_import") is not False or
        snapshot.get("can_assemble") is not False or
        snapshot.get("project_id") != edit.get("project_id") or
        not isinstance(snapshot.get("inventory_sha256"), str) or
        len(snapshot["inventory_sha256"]) != 64 or
        not isinstance(snapshot.get("items"), list)
    ):
        raise TimelineCandidateError("E_TIMELINE_SNAPSHOT_INVALID")
    if type(background_source_frames) is not int or background_source_frames < 1:
        raise TimelineCandidateError("E_BACKGROUND_LENGTH_UNVERIFIED")
    if type(audio_source_frames) is not int or audio_source_frames < 1:
        raise TimelineCandidateError("E_AUDIO_LENGTH_UNVERIFIED")
    try:
        draft = build_draft(edit, animation)
        host = compile_tick_draft(draft, ticks_per_frame)
    except (DraftCompileError, HostTickDraftError) as e:
        raise TimelineCandidateError("E_TIMELINE_CONTRACT_INVALID") from e
    total_frames = draft["total_frames"]
    if total_frames != audio_source_frames:
        # No arbitrary trim/loop/slow-motion for the narration.
        raise TimelineCandidateError("E_NARRATION_DURATION_MISMATCH")
    if snapshot.get("item_count") != len(snapshot["items"]):
        raise TimelineCandidateError("E_TIMELINE_SNAPSHOT_INVALID")
    imported = {}
    for item in snapshot["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("item_id"), str):
            raise TimelineCandidateError("E_TIMELINE_SNAPSHOT_INVALID")
        iid = item["item_id"]
        if iid in imported:
            raise TimelineCandidateError("E_TIMELINE_SNAPSHOT_INVALID")
        imported[iid] = item.get("kind")
    if imported.get("SOURCE_BACKGROUND") != "background" or (
        imported.get("SOURCE_AUDIO") != "audio" or
        imported.get("SOURCE_SRT") != "srt"
    ):
        raise TimelineCandidateError("E_TIMELINE_SNAPSHOT_INVALID")
    ops: list[dict[str, Any]] = []
    def add(key: str, track: str, item_id: str, start: int, end: int,
            source_start: int, source_end: int, slot: str) -> None:
        if track not in TRACKS or start < 0 or start >= end or (
            end > total_frames or source_start < 0 or source_start >= source_end or
            source_end - source_start != end - start or item_id not in imported
        ):
            raise TimelineCandidateError("E_TIMELINE_OPERATION_INVALID")
        ops.append({
            "key": key, "track": track,
            "item_id": item_id, "slot": slot,
            "start_frame": start, "end_frame": end,
            "source_in_frame": source_start, "source_out_frame": source_end,
            "start_ticks": frame_to_ticks(start, ticks_per_frame),
            "end_ticks": frame_to_ticks(end, ticks_per_frame),
            "duration_ticks": frame_to_ticks(end-start, ticks_per_frame),
            "source_in_ticks": frame_to_ticks(source_start, ticks_per_frame),
            "source_out_ticks": frame_to_ticks(source_end, ticks_per_frame),
            "readback_verified": False,
        })
        if len(ops) > MAX_OPERATIONS_DEV:
            raise TimelineCandidateError("E_RESOURCE_LIMIT")

    frame = 0
    loop = 0
    while frame < total_frames:
        length = min(background_source_frames, total_frames-frame)
        add(f"BG_{loop:05d}", "V1", "SOURCE_BACKGROUND",
            frame, frame+length, 0, length, "BACKGROUND")
        loop += 1
        frame += length
    for placement in host["placements"]:
        # Still PNG source; actual Premiere still-image extend/trim untested.
        item_id = "ASSET_" + placement["instance_key"].split("/", 1)[1]
        if imported.get(item_id) != "png":
            raise TimelineCandidateError("E_TIMELINE_ASSET_NOT_IMPORTED")
        a,b=placement["start_frame"],placement["end_frame"]
        add(placement["instance_key"], placement["track"], item_id,
            a,b,0,b-a,"VISUAL")
    add("NARRATION", "A1", "SOURCE_AUDIO",0,total_frames,0,total_frames,"AUDIO")

    # No overwrite/ripple allowed. Every track must have nonoverlapping ranges.
    by_track: dict[str, list[tuple[int, int]]] = {t: [] for t in TRACKS}
    for op in ops:
        by_track[op["track"]].append((op["start_frame"],op["end_frame"]))
    for intervals in by_track.values():
        intervals.sort()
        for i in range(1,len(intervals)):
            if intervals[i][0] < intervals[i-1][1]:
                raise TimelineCandidateError("E_TIMELINE_TRACK_OVERLAP")
    normalized = sorted(ops,key=lambda x:(
        TRACKS.index(x["track"]), x["start_frame"], x["key"]))
    fingerprint = hashlib.sha256(json.dumps({
        "ops": normalized, "snapshot_sha": snapshot["inventory_sha256"],
        "draft_sha": draft["operation_digest_sha256"]
    },ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()
    return {
        "schema_version":"timeline-placement-candidate-v1",
        "status":"CANDIDATE_NOT_EXECUTABLE",
        "can_assemble": False,
        "project_id":edit["project_id"],
        "snapshot_sha256":snapshot["inventory_sha256"],
        "draft_sha256":draft["operation_digest_sha256"],
        "operation_sha256":fingerprint,
        "ticks_per_frame":ticks_per_frame,
        "total_frames":total_frames,
        "operation_count":len(normalized),
        "operations":normalized,
        "pending":[
            "ACTUAL_PREMIERE_HOST_TICKS",
            "SOURCE_MEDIA_DURATION_DECODE_CONFIRMED",
            "MANAGED_SEQUENCE_AND_IMPORT_READBACK",
            "VIDEO_SOURCE_MUST_NOT_INSERT_LINKED_AUDIO",
            "STILL_IMAGE_SOURCE_TRIMMING",
            "APPROVED_LAYOUT_CROP_AND_21_BOTH_PRESETS"
        ]
    }
