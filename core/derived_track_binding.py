"""STEP10 bind a verified isolated background to a *draft* V1 track worklist.

All source validation is repeated immediately before binding. The resulting
internal worklist includes a cache path, but public_summary deliberately does
not. This object cannot authorize CEP, Premiere import, or clip insertion.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

from .background_overlay import prepare_background_overlay, OverlayError


SHA = re.compile(r"[a-f0-9]{64}\Z")


class DerivedTrackError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def bind_derived_v1_candidate(
    track_candidate: dict[str, Any],
    overlay: dict[str, Any],
    edit: dict[str, Any],
    original_snapshot: dict[str, Any],
    isolation_report: dict[str, Any],
    media_root: Path,
    cache_root: Path,
    *,
    ffprobe_exe: Path | None,
    max_media_bytes: int,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Replace ONLY draft V1 source references with provenance-pinned cache MP4.

    Refuses a plan without exactly contiguous V1 looping coverage. Does not
    silently trim video sources: source_in/out are retained as *requested*
    frame ranges for later Premiere readback and frame-accurate trim backend.
    """
    if (type(track_candidate) is not dict or
            track_candidate.get("schema_version") != "track-placement-candidate-v1"
            or track_candidate.get("status") != "CANDIDATE_NOT_EXECUTABLE"
            or track_candidate.get("can_import") is not False
            or track_candidate.get("can_assemble") is not False
            or type(track_candidate.get("total_frames")) is not int
            or track_candidate["total_frames"] <= 0
            or type(track_candidate.get("placements")) is not list
            or type(overlay) is not dict or
            overlay.get("schema_version") != "derived-background-overlay-v1"
            or overlay.get("status") != "CANDIDATE_NOT_AUTHORIZED"
            or overlay.get("can_import") is not False
            or overlay.get("can_assemble") is not False
            or type(overlay.get("overlay_sha256")) is not str or
            SHA.fullmatch(overlay["overlay_sha256"]) is None
            or type(track_candidate.get("operation_sha256")) is not str
            or SHA.fullmatch(track_candidate["operation_sha256"]) is None
            or track_candidate.get("media_digest") !=
               overlay.get("original_inventory_sha256")):
        raise DerivedTrackError("E_DERIVED_BINDING_INPUT_INVALID")
    # Caller cannot pass a forged "verified" overlay and skip hash/FFprobe:
    # repeat actual source+cache checks and compare all provenance fields.
    try:
        verified = prepare_background_overlay(
            edit, original_snapshot, isolation_report, media_root, cache_root,
            ffprobe_exe=ffprobe_exe, max_media_bytes=max_media_bytes,
            runner=runner)
    except OverlayError as exc:
        raise DerivedTrackError(exc.code) from exc
    for key in ("overlay_sha256", "derived_absolute_path",
                "source_sha256", "derived_sha256",
                "video_frame_count", "original_inventory_sha256"):
        if verified.get(key) != overlay.get(key):
            raise DerivedTrackError("E_DERIVED_BINDING_STALE")
    total=track_candidate["total_frames"]
    placements=[]
    v1=[]
    keys=set()
    for p in track_candidate["placements"]:
        if type(p) is not dict:
            raise DerivedTrackError("E_DERIVED_TRACK_INVALID")
        key=p.get("instance_key")
        start,end=p.get("start_frame"),p.get("end_frame")
        if (type(key) is not str or not key or key in keys
                or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= total):
            raise DerivedTrackError("E_DERIVED_TRACK_INVALID")
        keys.add(key)
        copy=dict(p)
        if p.get("target_track") == "V1":
            source_in,source_out=p.get("source_in_frame"),p.get("source_out_frame")
            if (p.get("item_id") != "SOURCE_BACKGROUND"
                    or p.get("source_policy") != "BACKGROUND_VIDEO_ONLY_UNVERIFIED"
                    or type(source_in) is not int or type(source_out) is not int
                    or source_in != 0 or source_out != end-start
                    or source_out > verified["video_frame_count"]):
                raise DerivedTrackError("E_DERIVED_V1_RANGE_INVALID")
            v1.append((start,end))
            copy.update({
                "item_id":"DERIVED_SOURCE_BACKGROUND",
                "source_policy":"DERIVED_VIDEO_ONLY_PENDING_HOST_READBACK",
                "source_sha256":verified["derived_sha256"],
                "derived_absolute_path":verified["derived_absolute_path"],
                "video_frame_count":verified["video_frame_count"],
                "trim_required":source_out != verified["video_frame_count"],
                "host_readback":"NOT_TESTED",
            })
        placements.append(copy)
    v1.sort()
    if (not v1 or v1[0][0] != 0 or v1[-1][1] != total or
            any(v1[i][1] != v1[i+1][0] for i in range(len(v1)-1))):
        raise DerivedTrackError("E_DERIVED_V1_COVERAGE_INVALID")
    counts=track_candidate.get("track_counts")
    if (type(counts) is not dict or counts.get("V1") != len(v1)):
        raise DerivedTrackError("E_DERIVED_TRACK_COUNT_INVALID")
    # Internal binding digest ties original plan, source inventory, derived
    # video-only cache identity and requested source trim ranges.
    payload={
        "track_operation_sha256":track_candidate.get("operation_sha256"),
        "overlay_sha256":verified["overlay_sha256"],
        "derived_sha256":verified["derived_sha256"],
        "placements":placements,
    }
    digest=hashlib.sha256(json.dumps(
        payload, ensure_ascii=False,sort_keys=True,
        separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()
    return {
        "schema_version":"derived-track-candidate-v1",
        "status":"CANDIDATE_NOT_EXECUTABLE",
        "can_import":False,"can_assemble":False,
        "operation_sha256":digest,
        "total_frames":total,"v1_clip_count":len(v1),
        "placements":placements,
        "derived_overlay_sha256":verified["overlay_sha256"],
        "public_summary":{
            "status":"CANDIDATE_NOT_EXECUTABLE",
            "can_import":False,"can_assemble":False,
            "v1_clip_count":len(v1),"total_frames":total,
            "operation_sha256":digest,
        },
        "remaining_blockers":[
            "HOST_SOURCE_TRIM_UNVERIFIED",
            "PREMIERE_LINKED_AUDIO_READBACK_UNVERIFIED",
            "LAYOUT_AND_21_BOTH_EFFECTS_UNVERIFIED",
            "HOST_CAPABILITY_AND_OWNER_GATE_UNVERIFIED",
        ],
    }
