"""Deterministic, NOT EXECUTABLE draft of timeline placement from two JSON plans.

No guessed layout/crop, animation frame phases, Premiere ticks, media source trim
or FFmpeg output. The output is never host-executable/READY. It is a safe, pure
reference for comparing future native Premiere readback with source frame timing.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import validate_pair


class DraftCompileError(ValueError):
    def __init__(self, codes: list[str]):
        self.codes = list(codes)
        super().__init__("Draft rejected: " + ", ".join(self.codes))


_ALLOWED_PENDING = {
    "E_CONFIG_LIMITS_UNVERIFIED", "E_MEDIA_UNVERIFIED",
    "E_PROFILE_UNVERIFIED", "E_HOST_UNVERIFIED",
}
TRACKS = {"SINGLE": "V2", "LEFT": "V2", "RIGHT": "V3"}


def build_draft(edit: dict[str, Any], animation: dict[str, Any]) -> dict[str, Any]:
    """Produce stable timing/track references; no filesystem or host side effects."""
    report = validate_pair(edit, animation)
    blocking = [i["code"] for i in report["issues"] if
                i["severity"] == "ERROR" or i["code"] not in _ALLOWED_PENDING]
    if blocking:
        raise DraftCompileError(sorted(set(blocking)))
    decisions = {(d["scene_id"],d["asset_id"]): d for d in animation["decisions"]}
    assignments = []
    last_end = 0
    for scene in edit["scenes"]:
        scene_start, scene_end = scene["start_frame"], scene["end_frame"]
        if scene_start != last_end:
            # Explicitly refuse invented gap/overlap-filling clips.
            raise DraftCompileError(["E_SCENE_CHRONOLOGY"])
        last_end = scene_end
        for occurrence in scene["assets"]:
            sid, aid = scene["scene_id"], occurrence["asset_id"]
            d = decisions[(sid, aid)]
            assignments.append({
                "instance_key": sid+"/"+aid,
                "scene_id": sid,
                "asset_id": aid,
                "slot": occurrence["slot"],
                "target_track": TRACKS[occurrence["slot"]],
                "start_frame": occurrence["start_frame"],
                "end_frame": occurrence["end_frame"],
                "duration_frames": occurrence["end_frame"]-occurrence["start_frame"],
                "preset": d["preset"], "speed": d["speed"],
                "direction": d["direction"], "mode": "BOTH",
                "effect_backend": "UNVERIFIED",
                "phase_frames": None,
                "layout_transform": None
            })
    assignments.sort(key=lambda x:(x["start_frame"],x["scene_id"],x["target_track"],x["asset_id"]))
    digest_material={
        "spec":"draft-timeline-v1",
        "project_id":edit["project_id"],
        "edit_plan_revision":edit["revision"],
        "animation_plan_revision":animation["revision"],
        "canvas":edit["canvas"],
        "total_frames":last_end,
        "instances":assignments
    }
    stable=json.dumps(digest_material,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")
    digest=hashlib.sha256(stable).hexdigest()
    return {
        "schema_version":"draft-timeline-manifest-v1",
        "status":"DRAFT_NOT_EXECUTABLE",
        "can_assemble":False,
        "operation_digest_sha256":digest,
        "project_id":edit["project_id"],
        "canvas":dict(edit["canvas"]),
        "scene_count":len(edit["scenes"]),
        "asset_instance_count":len(assignments),
        "total_frames":last_end,
        "asset_placements":assignments,
        "track_intent":{
            "V1":"BACKGROUND_LOOP_PENDING_MEDIA_DURATION",
            "V2":"SINGLE_OR_LEFT",
            "V3":"RIGHT",
            "A1":"NARRATION_DURATION_UNVERIFIED"
        },
        "missing_capabilities":[
            "MEDIA_DECODE_AND_HASH_CONFIRMATION",
            "APPROVED_LAYOUT_AND_CROP_TRANSFORMS",
            "ANIMATION_BOTH_PHASES_AND_BACKENDS",
            "HOST_TIMING_TICKS_AND_TRACK_INSERTION",
            "PREMIERE_READBACK",
        ],
        "notes":"Draft visual placement only. No input files modified, no host mutation."
    }
