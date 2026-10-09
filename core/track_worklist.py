"""Offline V1/V2/V3/A1 track operation planner.

Everything here remains DRAFT_NOT_EXECUTABLE. Frame spans are exact integer
half-open intervals. Media durations must come from separately reviewed source
metadata and are NOT inferred from filename/JSON timestamps or rounded floats.
No Premiere edits, downloads, trimming, media writes, or "READY" transition.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .host_ticks import HostTickDraftError, compile_tick_draft, frame_to_ticks


HASH = re.compile(r"[a-f0-9]{64}\Z")
TRACK_IDX = {"V1": 0, "V2": 1, "V3": 2, "A1": 0}
KIND = {"V1": "background", "V2": "png", "V3": "png", "A1": "audio"}
ORDER = {"V1": 0, "V2": 1, "V3": 2, "A1": 3}


class TrackWorklistError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _positive(value: Any) -> bool:
    return type(value) is int and value > 0


def _item_ids(snapshot: dict[str, Any]) -> dict[str, str]:
    if (type(snapshot) is not dict or
            snapshot.get("schema_version") != "verified-media-snapshot-v1" or
            snapshot.get("status") != "CANDIDATE_NOT_AUTHORIZED" or
            snapshot.get("can_import") is not False or
            not isinstance(snapshot.get("items"), list) or
            not isinstance(snapshot.get("inventory_sha256"), str) or
            HASH.fullmatch(snapshot["inventory_sha256"]) is None):
        raise TrackWorklistError("E_TRACK_MEDIA_SNAPSHOT_INVALID")
    ids: dict[str, str] = {}
    for item in snapshot["items"]:
        if type(item) is not dict or not item.get("import_to_premiere"):
            continue
        key, kind = item.get("item_id"), item.get("kind")
        if (not isinstance(key, str) or not isinstance(kind, str) or
                key in ids):
            raise TrackWorklistError("E_TRACK_MEDIA_SNAPSHOT_INVALID")
        ids[key] = kind
    return ids


def build_track_worklist(draft: dict[str, Any],
                         snapshot: dict[str, Any],
                         durations: dict[str, Any],
                         ticks_per_frame: str, *,
                         max_operations: int) -> dict[str, Any]:
    """Create a read-only worklist for ALL 4 tracks from verified input shapes.

    durations = {"background_frames": N, "audio_frames": N,
                 "measurement": "EXTERNAL_MEDIA_REVIEW_PENDING_HOST",
                 "snapshot_sha256": snapshot digest}.
    Caller must obtain frame-accurate durations independently. This function
    does not certify those inputs even when supplied. Native media source trim,
    audio sync, 21 effects and Premiere readback remain mandatory blockers.
    """
    if type(max_operations) is not int or not (1 <= max_operations <= 200000):
        raise TrackWorklistError("E_TRACK_LIMIT_UNVERIFIED")
    if (type(durations) is not dict or
            durations.get("measurement") != "EXTERNAL_MEDIA_REVIEW_PENDING_HOST" or
            not _positive(durations.get("background_frames")) or
            not _positive(durations.get("audio_frames")) or
            durations.get("snapshot_sha256") != snapshot.get("inventory_sha256")):
        raise TrackWorklistError("E_TRACK_DURATION_UNVERIFIED")
    ids = _item_ids(snapshot)
    if ids.get("SOURCE_BACKGROUND") != "background" or ids.get("SOURCE_AUDIO") != "audio":
        raise TrackWorklistError("E_TRACK_MEDIA_SNAPSHOT_INVALID")
    try:
        ticks = compile_tick_draft(draft, ticks_per_frame)
    except HostTickDraftError as ex:
        raise TrackWorklistError(ex.code) from ex
    total = draft["total_frames"]
    if durations["audio_frames"] < total:
        raise TrackWorklistError("E_TRACK_NARRATION_TOO_SHORT")
    bg_frames = durations["background_frames"]
    loops = (total + bg_frames - 1) // bg_frames
    if loops + len(ticks["placements"]) + 1 > max_operations:
        raise TrackWorklistError("E_RESOURCE_LIMIT")

    def make(kind: str, key: str, start: int, end: int,
             source_start: int | None, source_end: int | None) -> dict[str, Any]:
        if not 0 <= start < end <= total:
            raise TrackWorklistError("E_TRACK_SPAN_INVALID")
        return {
            "operation_id": key,
            "media_item_id": kind if kind.startswith("SOURCE_") else "ASSET_" + kind,
            "track": ("V1" if kind == "SOURCE_BACKGROUND" else
                      "A1" if kind == "SOURCE_AUDIO" else ""),
            "start_frame": start, "end_frame": end,
            "start_ticks": frame_to_ticks(start, ticks_per_frame),
            "end_ticks": frame_to_ticks(end, ticks_per_frame),
            "duration_ticks": frame_to_ticks(end - start, ticks_per_frame),
            "source_in_frame": source_start, "source_out_frame": source_end,
            "source_in_ticks": (frame_to_ticks(source_start, ticks_per_frame)
                                if source_start is not None else None),
            "source_out_ticks": (frame_to_ticks(source_end, ticks_per_frame)
                                 if source_end is not None else None),
            "readback_verified": False,
            "native_trim_verified": False
        }

    ops: list[dict[str, Any]] = []
    for i in range(loops):
        start = i * bg_frames
        end = min(total, start + bg_frames)
        op = make("SOURCE_BACKGROUND", f"BG_{i:06d}", start, end, 0, end - start)
        op["zero_based_track_index"] = 0
        ops.append(op)
    for placement in ticks["placements"]:
        identity = placement["instance_key"]
        if not isinstance(identity, str) or identity.count("/") != 1:
            raise TrackWorklistError("E_TRACK_MEDIA_MAPPING_INVALID")
        asset_id = identity.split("/")[1]
        if ids.get("ASSET_" + asset_id) != "png":
            raise TrackWorklistError("E_TRACK_MEDIA_MAPPING_INVALID")
        op = make(asset_id, "IMG_" + identity, placement["start_frame"],
                  placement["end_frame"], None, None)
        op["track"] = placement["track"]
        op["zero_based_track_index"] = TRACK_IDX[op["track"]]
        ops.append(op)
    audio = make("SOURCE_AUDIO", "AUDIO_NARRATION", 0, total, 0, total)
    audio["zero_based_track_index"] = 0
    ops.append(audio)
    ops.sort(key=lambda item: (
        ORDER[item["track"]], item["start_frame"], item["operation_id"]))
    seen = set()
    by_track: dict[str, list[tuple[int, int]]] = {k: [] for k in TRACK_IDX}
    for op in ops:
        if op["operation_id"] in seen:
            raise TrackWorklistError("E_TRACK_OPERATION_DUPLICATE")
        seen.add(op["operation_id"])
        if ids.get(op["media_item_id"]) != KIND[op["track"]]:
            raise TrackWorklistError("E_TRACK_MEDIA_MAPPING_INVALID")
        intervals = by_track[op["track"]]
        if intervals and op["start_frame"] < intervals[-1][1]:
            raise TrackWorklistError("E_HOST_TRACK_OVERLAP")
        intervals.append((op["start_frame"], op["end_frame"]))
    if (not by_track["V1"] or by_track["V1"][0][0] != 0 or
            by_track["V1"][-1][1] != total or
            any(by_track["V1"][i][0] != by_track["V1"][i-1][1]
                for i in range(1, len(by_track["V1"]))) or
            by_track["A1"] != [(0, total)]):
        raise TrackWorklistError("E_TRACK_COVERAGE_INCOMPLETE")
    stable = {
        "spec": "track-worklist-v1",
        "source_digest_sha256": snapshot["inventory_sha256"],
        "draft_digest_sha256": draft["operation_digest_sha256"],
        "ticks_per_frame": ticks_per_frame, "total_frames": total,
        "operations": ops
    }
    encoded = json.dumps(stable, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "schema_version": "track-worklist-v1",
        "status": "DRAFT_NOT_EXECUTABLE", "can_assemble": False,
        "snapshot_digest_sha256": snapshot["inventory_sha256"],
        "draft_digest_sha256": draft["operation_digest_sha256"],
        "operation_digest_sha256": hashlib.sha256(encoded).hexdigest(),
        "total_frames": total, "ticks_per_frame": ticks_per_frame,
        "track_counts": {k: len(v) for k, v in by_track.items()},
        "operations": ops,
        "missing_capabilities": [
            "APPROVED_FRAME_ACCURATE_SOURCE_DURATIONS",
            "PREMIERE_NATIVE_SOURCE_TRIM_AND_READBACK",
            "STILL_CLIP_EXACT_LENGTH_AND_ALPHA",
            "PREMIERE_MANAGED_SEQUENCE_INTEGRITY",
            "LAYOUT_CROP_AND_21_BOTH_EFFECTS",
            "HOST_G3_AND_FINAL_ACCEPTANCE"
        ]
    }
