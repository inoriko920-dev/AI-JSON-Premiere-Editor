"""STEP21 native Premiere FADE opacity keyframe *candidate*, no host execution.

The B02 MEDIUM/BOTH reference has exact frame budgets (15 IN, 7 OUT).
This is an editable-native preferred route in the approved Master V3, separate
from STEP16's valid prerender-alpha option. Source opacity is preserved:
0% -> 100% -> 100% -> 0%. Premiere component ids, clip-relative Time
semantics, interpolation and host readback are UNVERIFIED, so execution is
deliberately gated rather than silently editing a real timeline.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .fx_alpha_backend import AlphaBackendError, _check


class NativeFadeError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _digest(data: dict[str, Any]) -> str:
    return sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                            allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def compile_native_fade(item: dict[str, Any]) -> dict[str, Any]:
    """Produce a tamper-evident, frame-accurate read-only native keyframe plan.

    Uses 0-based *instance-local* samples so that a scene at a nonzero
    start_frame is not shifted. Never constructs host Time objects here.
    """
    if type(item) is not dict or item.get("preset") != "FADE":
        raise NativeFadeError("E_FX_NATIVE_PRESET_UNSUPPORTED")
    try:
        direction, frames, ins, outs = _check(item)
    except AlphaBackendError as err:
        raise NativeFadeError(err.code) from err
    if direction != "NONE" or ins < 2 or outs < 2:
        raise NativeFadeError("E_FX_NATIVE_FADE_INVALID")
    # IN and OUT fully reach their endpoints. With zero hold, they remain
    # separate adjacent frames. Never shorten phases to fit a clip.
    samples = [
        {"frame": 0, "opacity_percent": 0},
        {"frame": ins - 1, "opacity_percent": 100},
        {"frame": frames - outs, "opacity_percent": 100},
        {"frame": frames - 1, "opacity_percent": 0},
    ]
    material = {
        "schema_version": "native-fade-keyframes-candidate-v1",
        "status": "KEYFRAMES_PLANNED_HOST_UNVERIFIED",
        "instance_key": item.get("instance_key"),
        "preset": "FADE", "direction": "NONE", "mode": "BOTH",
        "speed": "MEDIUM", "start_frame": item["start_frame"],
        "end_frame": item["end_frame"],
        "duration_frames": frames, "in_frames": ins, "out_frames": outs,
        "parameter_semantics": "OPACITY_PERCENT",
        "timebase_semantics": "INSTANCE_LOCAL_FRAME_30FPS",
        "interpolation": "LINEAR_REFERENCE_CANDIDATE",
        "samples": samples,
        "reference_evidence": item["reference_evidence"],
        "source_reference": "STEP01_B02_PROPOSED_21",
        "host_component_match_name": None,
        "host_parameter_match_name": None,
        "can_assemble": False,
        "host_verified": False,
        "readback_verified": False,
        "can_claim_canva_fidelity": False,
    }
    if not isinstance(material["instance_key"], str) or not material["instance_key"]:
        raise NativeFadeError("E_FX_NATIVE_INSTANCE_INVALID")
    return {**material, "candidate_sha256": _digest(material)}


def validate_native_fade_candidate(candidate: dict[str, Any]) -> None:
    """Rebuild from documented frame and evidence, block forged host claims."""
    if type(candidate) is not dict or not isinstance(
            candidate.get("candidate_sha256"), str):
        raise NativeFadeError("E_FX_NATIVE_CANDIDATE_TAMPERED")
    original = dict(candidate)
    digest = original.pop("candidate_sha256")
    if (len(digest) != 64 or digest != _digest(original) or
            original.get("schema_version") != "native-fade-keyframes-candidate-v1"
            or original.get("status") != "KEYFRAMES_PLANNED_HOST_UNVERIFIED"
            or original.get("can_assemble") is not False
            or original.get("host_verified") is not False
            or original.get("readback_verified") is not False
            or original.get("can_claim_canva_fidelity") is not False
            or original.get("host_component_match_name") is not None
            or original.get("host_parameter_match_name") is not None):
        raise NativeFadeError("E_FX_NATIVE_CANDIDATE_TAMPERED")
    synthetic = {
        "instance_key": original.get("instance_key"),
        "preset": original.get("preset"),
        "direction": original.get("direction"),
        "mode": original.get("mode"),
        "speed": original.get("speed"),
        "start_frame": original.get("start_frame"),
        "end_frame": original.get("end_frame"),
        "in_frames": original.get("in_frames"),
        "out_frames": original.get("out_frames"),
        "in_range": [original.get("start_frame"), None],
        "hold_range": [None, None],
        "out_range": [None, original.get("end_frame")],
        "effect_backend": "NOT_IMPLEMENTED",
        "can_render": False,
        "keyframes": None,
        "source_reference": original.get("source_reference"),
        "reference_evidence": original.get("reference_evidence"),
    }
    # Reject bool-as-int, negatives and corrupted ranges before recomputing.
    start, end, ins, outs = (synthetic.get(k) for k in
                            ("start_frame", "end_frame", "in_frames", "out_frames"))
    if any(type(v) is not int for v in (start, end, ins, outs)):
        raise NativeFadeError("E_FX_NATIVE_CANDIDATE_TAMPERED")
    synthetic["in_range"][1] = start + ins
    synthetic["hold_range"] = [start + ins, end - outs]
    synthetic["out_range"][0] = end - outs
    try:
        recompiled = compile_native_fade(synthetic)
    except (NativeFadeError, KeyError, TypeError, ValueError) as exc:
        raise NativeFadeError("E_FX_NATIVE_CANDIDATE_TAMPERED") from exc
    if recompiled != candidate:
        raise NativeFadeError("E_FX_NATIVE_CANDIDATE_TAMPERED")
