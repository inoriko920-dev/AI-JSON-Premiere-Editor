"""STEP15 deterministic BOTH phase scheduler for 21 reference presets.

A phase schedule is NOT an effect renderer, keyframe implementation, Premiere
host authorization or evidence that an animation looks like Canva. MEDIUM frame
references come from the project's B02 table, with their provisional evidence
levels carried forward. No adjustment, scaling, rerolling or hidden fallback.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .draft_compiler import DraftCompileError, build_draft

_REFERENCE = Path(__file__).with_name("animation_timings_b02.json")
_VALID_EVIDENCE = {
    "V2_EXACT_LITERAL", "V3_EXACT_LITERAL",
    "PROPOSAL_SOURCE_SEMANTICS", "INFERRED_NONE_FROM_ENGINE",
}


class PhasePlanError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canonical(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _reference() -> dict:
    try:
        with _REFERENCE.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        with _REFERENCE.with_name("direction_registry.json").open(
                "r", encoding="utf-8") as stream:
            directions = json.load(stream)["directions"]
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise PhasePlanError("E_FX_REFERENCE_UNAVAILABLE") from error
    if (type(data) is not dict or
            data.get("schema_version") != "proposed-medium-both-phase-reference-v1"
            or data.get("source_status") != "B02_REFERENCE_TIMING_NOT_HOST_CALIBRATED"
            or data.get("fps_num") != 30 or data.get("fps_den") != 1
            or type(data.get("entries")) is not dict
            or set(data["entries"]) != set(directions)
            or len(directions) != 21):
        raise PhasePlanError("E_FX_REFERENCE_INVALID")
    for key, entry in data["entries"].items():
        if (type(entry) is not dict or
                set(entry) != {"in_frames", "out_frames", "evidence_level"}
                or type(entry["in_frames"]) is not int or
                type(entry["out_frames"]) is not int or
                entry["in_frames"] < 1 or entry["out_frames"] < 1 or
                entry["evidence_level"] not in _VALID_EVIDENCE):
            raise PhasePlanError("E_FX_REFERENCE_INVALID")
    return data


def build_both_phase_candidate(edit: dict, animation: dict, *,
                               max_instances: int) -> dict:
    """Non-executable schedule for every asset occurrence; no file writes."""
    if type(max_instances) is not int or max_instances <= 0:
        raise PhasePlanError("E_FX_RESOURCE_LIMIT_UNVERIFIED")
    try:
        draft = build_draft(edit, animation)
    except (DraftCompileError, KeyError, TypeError, ValueError) as error:
        raise PhasePlanError("E_FX_INPUT_PLAN_UNVERIFIED") from error
    reference = _reference()
    placements = draft["asset_placements"]
    if len(placements) > max_instances:
        raise PhasePlanError("E_FX_RESOURCE_LIMIT")
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for p in placements:
        key = p["instance_key"]
        if key in seen:
            raise PhasePlanError("E_FX_INSTANCE_DUPLICATE")
        seen.add(key)
        if (p["speed"] != "MEDIUM" or p["preset"] not in reference["entries"]
                or p["mode"] != "BOTH"):
            raise PhasePlanError("E_FX_REFERENCE_UNCALIBRATED")
        ref = reference["entries"][p["preset"]]
        start, end = p["start_frame"], p["end_frame"]
        duration = end - start
        inside, outside = ref["in_frames"], ref["out_frames"]
        # No shortening, shifting or speed adjustment without policy approval.
        if duration < inside + outside:
            raise PhasePlanError("E_TIME_006")
        intro_end = start + inside
        outro_start = end - outside
        entries.append({
            "instance_key": key,
            "scene_id": p["scene_id"],
            "asset_id": p["asset_id"],
            "target_track": p["target_track"],
            "preset": p["preset"],
            "direction": p["direction"],
            "speed": "MEDIUM",
            "mode": "BOTH",
            "reference_evidence": ref["evidence_level"],
            "source_reference": "STEP01_B02_PROPOSED_21",
            "start_frame": start, "end_frame": end,
            "in_frames": inside, "out_frames": outside,
            "in_range": [start, intro_end],
            "hold_range": [intro_end, outro_start],
            "out_range": [outro_start, end],
            "zero_hold_needs_visual_review": intro_end == outro_start,
            "effect_backend": "NOT_IMPLEMENTED",
            "keyframes": None,
            "can_render": False,
        })
    material = {
        "schema_version": "both-phase-reference-candidate-v1",
        "project_id": edit["project_id"],
        "edit_plan_revision": edit["revision"],
        "animation_plan_revision": animation["revision"],
        "source_draft_sha256": draft["operation_digest_sha256"],
        "profile_claim_sha256": animation["animation_profile"]["sha256"],
        "reference_sha256": sha256(_canonical(reference)).hexdigest(),
        "entries": entries,
    }
    return {
        **material,
        "status": "REFERENCE_SCHEDULE_ONLY",
        "can_render": False,
        "can_assemble": False,
        "host_verified": False,
        "animation_backend_verified": False,
        "instance_count": len(entries),
        "operation_sha256": sha256(_canonical(material)).hexdigest(),
        "remaining": [
            "21_NATIVE_OR_FFMPEG_EFFECT_BACKENDS",
            "PREMIERE_KEYFRAME_OR_RGBA_RENDEDR_READBACK",
            "APPROVED_LAYOUT_CROP",
            "B02_TIMING_DIRECTION_PROFILE_SIGNOFF",
            "REAL_WINDOWS_PREMIERE_24X_HOST_EVIDENCE",
        ],
    }
