"""STEP23: immutable, non-executable Fade-to-visual-track binding candidate.

Links STEP21 FADE.BOTH samples to the existing STEP09 four-track placement
manifest and STEP06 imported-item identity labels. No source paths, no host
API calls and no claim that the supplied node IDs or tick timebase are
authenticated by Adobe Premiere. Never use this as an execution token.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

from .fx_native_fade import validate_native_fade_candidate, NativeFadeError
from .host_ticks import frame_to_ticks, HostTickDraftError

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_GUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
_MANAGED = re.compile(r"AIJSON_MANAGED_[A-Za-z0-9_-]{4,64}\Z")
_NODE = re.compile(r"[A-Za-z0-9_.-]{1,80}\Z")
_INSTANCE = re.compile(r"([A-Za-z0-9_-]+)/([A-Za-z0-9][A-Za-z0-9_.-]{0,89})\Z")
_ITEM = re.compile(r"(?:SOURCE_(?:BACKGROUND|AUDIO)|ASSET_[A-Za-z0-9][A-Za-z0-9_.-]{0,89})\Z")
_INDEX = {"V1": 0, "V2": 1, "V3": 2, "A1": 0}


class FadeBindingError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _valid_plan(plan: Any) -> None:
    """Verify the original track-plan material and every placement, not just target."""
    if (type(plan) is not dict or
            plan.get("schema_version") != "track-placement-candidate-v1" or
            plan.get("status") != "CANDIDATE_NOT_EXECUTABLE" or
            plan.get("can_import") is not False or
            plan.get("can_assemble") is not False or
            type(plan.get("placements")) is not list or
            not 1 <= len(plan["placements"]) <= 10000 or
            type(plan.get("total_frames")) is not int or
            not 1 <= plan["total_frames"] <= 10000000 or
            type(plan.get("ticks_per_frame")) is not str or
            not _SHA.fullmatch(str(plan.get("source_digest"))) or
            not _SHA.fullmatch(str(plan.get("media_digest"))) or
            not _SHA.fullmatch(str(plan.get("operation_sha256"))) or
            type(plan.get("project_id")) is not str or
            not plan["project_id"]):
        raise FadeBindingError("E_FX_TRACK_PLAN_INVALID")
    try:
        frame_to_ticks(plan["total_frames"], plan["ticks_per_frame"])
        original = {k: plan[k] for k in (
            "schema_version", "project_id", "source_digest", "media_digest",
            "ticks_per_frame", "total_frames", "placements")}
        if _digest(original) != plan["operation_sha256"]:
            raise FadeBindingError("E_FX_TRACK_PLAN_CHANGED")
        seen = set()
        for p in plan["placements"]:
            if type(p) is not dict:
                raise FadeBindingError("E_FX_TRACK_PLAN_INVALID")
            key, track = p.get("instance_key"), p.get("target_track")
            a, b = p.get("start_frame"), p.get("end_frame")
            si, so = p.get("source_in_frame"), p.get("source_out_frame")
            if (type(key) is not str or not key or key in seen or
                    track not in _INDEX or
                    type(p.get("zero_based_track_index")) is not int or
                    p["zero_based_track_index"] != _INDEX[track] or
                    type(a) is not int or type(b) is not int or
                    not 0 <= a < b <= plan["total_frames"] or
                    type(si) is not int or type(so) is not int or
                    si != 0 or so != b - a or
                    p.get("start_ticks") != frame_to_ticks(a, plan["ticks_per_frame"]) or
                    p.get("end_ticks") != frame_to_ticks(b, plan["ticks_per_frame"]) or
                    p.get("media_readback") != "NOT_TESTED" or
                    type(p.get("item_id")) is not str or
                    not _ITEM.fullmatch(p["item_id"])):
                raise FadeBindingError("E_FX_TRACK_PLAN_INVALID")
            if ((track == "V1" and p["item_id"] != "SOURCE_BACKGROUND") or
                    (track == "A1" and p["item_id"] != "SOURCE_AUDIO") or
                    (track in ("V2", "V3") and
                     not p["item_id"].startswith("ASSET_"))):
                raise FadeBindingError("E_FX_TRACK_PLAN_INVALID")
            seen.add(key)
    except (KeyError, TypeError, ValueError, HostTickDraftError) as error:
        if isinstance(error, FadeBindingError):
            raise
        raise FadeBindingError("E_FX_TRACK_PLAN_INVALID") from error


def bind_native_fade_candidate(
    fade: dict[str, Any], track_plan: dict[str, Any],
    media_refs: list[dict[str, str]], *,
    managed_sequence_id: str, managed_sequence_name: str,
) -> dict[str, Any]:
    """Bind exactly one Fade instance and media node ID to a timeline selector.

    All refs are untrusted candidate data: hash checks here only establish
    internal consistency, NOT a real Premiere import/clip/host readback.
    """
    try:
        validate_native_fade_candidate(fade)
    except (NativeFadeError, TypeError, ValueError) as error:
        raise FadeBindingError("E_FX_NATIVE_CANDIDATE_INVALID") from error
    _valid_plan(track_plan)
    if (type(managed_sequence_id) is not str or
            not _GUID.fullmatch(managed_sequence_id) or
            type(managed_sequence_name) is not str or
            not _MANAGED.fullmatch(managed_sequence_name)):
        raise FadeBindingError("E_FX_MANAGED_SEQUENCE_INVALID")
    match = _INSTANCE.fullmatch(fade["instance_key"])
    if match is None:
        raise FadeBindingError("E_FX_FADE_INSTANCE_INVALID")
    item_id = "ASSET_" + match.group(2)
    target = [x for x in track_plan["placements"]
              if x["instance_key"] == fade["instance_key"]]
    if len(target) != 1:
        raise FadeBindingError("E_FX_FADE_TARGET_MISSING_OR_DUPLICATE")
    p = target[0]
    if (p["target_track"] not in ("V2", "V3") or
            p["item_id"] != item_id or
            p["start_frame"] != fade["start_frame"] or
            p["end_frame"] != fade["end_frame"] or
            p["end_frame"] - p["start_frame"] != fade["duration_frames"] or
            p.get("source_policy") != "IMAGE_FX_AND_LAYOUT_UNVERIFIED"):
        raise FadeBindingError("E_FX_FADE_TARGET_MISMATCH")
    if (type(media_refs) is not list or not 1 <= len(media_refs) <= 2000):
        raise FadeBindingError("E_FX_MEDIA_REFS_INVALID")
    by_id, by_node = {}, set()
    for ref in media_refs:
        if (type(ref) is not dict or set(ref) != {"item_id", "node_id"} or
                type(ref["item_id"]) is not str or
                not _ITEM.fullmatch(ref["item_id"]) or
                type(ref["node_id"]) is not str or
                not _NODE.fullmatch(ref["node_id"]) or
                ref["item_id"] in by_id or ref["node_id"] in by_node):
            raise FadeBindingError("E_FX_MEDIA_REFS_INVALID")
        by_id[ref["item_id"]] = ref["node_id"]
        by_node.add(ref["node_id"])
    required_ids = {x["item_id"] for x in track_plan["placements"]}
    if set(by_id) != required_ids:
        raise FadeBindingError("E_FX_MEDIA_REFS_MISMATCH")
    samples = [
        {"instance_frame": v["frame"], "instance_ticks":
         frame_to_ticks(v["frame"], track_plan["ticks_per_frame"]),
         "opacity_percent": v["opacity_percent"]}
        for v in fade["samples"]
    ]
    material = {
        "schema_version": "native-fade-track-binding-candidate-v1",
        "status": "SELECTOR_BOUND_NOT_HOST_AUTHORIZED",
        "fade_candidate_sha256": fade["candidate_sha256"],
        "track_plan_sha256": track_plan["operation_sha256"],
        "media_ref_map_sha256": _digest(sorted(media_refs,
                                             key=lambda x: x["item_id"])),
        "selector": {
            "sequence_id": managed_sequence_id.lower(),
            "sequence_name": managed_sequence_name,
            "track": p["target_track"],
            "start_ticks": p["start_ticks"],
            "end_ticks": p["end_ticks"],
            "source_node_id": by_id[item_id],
        },
        "instance_key": fade["instance_key"],
        "item_id": item_id,
        "local_keyframe_samples": samples,
        "time_coordinate_verified": False,
        "node_id_host_verified": False,
        "clip_end_host_verified": False,
        "opacity_matchname_verified": False,
        "readback_verified": False,
        "host_verified": False,
        "can_assemble": False,
    }
    return {**material, "binding_sha256": _digest(material)}


def validate_native_fade_binding(
    binding: dict[str, Any], fade: dict[str, Any],
    track_plan: dict[str, Any], media_refs: list[dict[str, str]], *,
    managed_sequence_id: str, managed_sequence_name: str,
) -> None:
    """Never accept a mutated or renamed binding without recompilation."""
    try:
        verified = bind_native_fade_candidate(
            fade, track_plan, media_refs,
            managed_sequence_id=managed_sequence_id,
            managed_sequence_name=managed_sequence_name)
    except FadeBindingError:
        raise
    if type(binding) is not dict or binding != verified:
        raise FadeBindingError("E_FX_FADE_BINDING_TAMPERED")
