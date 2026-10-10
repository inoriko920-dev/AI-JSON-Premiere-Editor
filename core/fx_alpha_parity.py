"""STEP25 exact-frame Fade candidate-vs-FFmpeg alpha parity verifier.

Checks a decoded 1x1 RGBA rawvideo sample from a *temporary* FFmpeg MOV.
No PNG, UI asset, screenshot, motion preset, or Premiere host mutation.
Requires an already-approved FADE.BOTH B02 reference and independently
recompiled FFmpeg filter, not arbitrary expression strings from JSON.
"""
from __future__ import annotations

from typing import Any
from .fx_native_fade import validate_native_fade_candidate, NativeFadeError
from .fx_alpha_backend import compile_filter, AlphaBackendError


class FadeParityError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _filter_from_native(candidate: dict[str, Any]) -> dict[str, Any]:
    start, end = candidate["start_frame"], candidate["end_frame"]
    inside, outside = candidate["in_frames"], candidate["out_frames"]
    synthetic = {
        "instance_key": candidate["instance_key"],
        "preset": "FADE", "direction": "NONE", "mode": "BOTH",
        "speed": "MEDIUM", "can_render": False,
        "effect_backend": "NOT_IMPLEMENTED", "keyframes": None,
        "source_reference": "STEP01_B02_PROPOSED_21",
        "reference_evidence": candidate["reference_evidence"],
        "start_frame": start, "end_frame": end,
        "in_frames": inside, "out_frames": outside,
        "in_range": [start, start + inside],
        "hold_range": [start + inside, end - outside],
        "out_range": [end - outside, end],
    }
    try:
        return compile_filter(synthetic)
    except (AlphaBackendError, KeyError, TypeError, ValueError) as exc:
        raise FadeParityError("E_FX_PARITY_REFERENCE_INVALID") from exc


def verify_native_fade_alpha_parity(
    native_candidate: dict[str, Any],
    filter_candidate: dict[str, Any], rgba_frames: bytes,
) -> dict[str, Any]:
    """Compare EVERY 30-fps local frame, not just the IN/OUT endpoints.

    Input comes from an independently decoded 1x1 red+opaque lavfi sample of
    a QTRLE/ARGB MOV. This proves only reference alpha *parity* in an offline
    test: not pixel coverage, source alpha, Canva fidelity or Premiere G3.
    """
    try:
        validate_native_fade_candidate(native_candidate)
    except (NativeFadeError, TypeError, ValueError) as error:
        raise FadeParityError("E_FX_PARITY_NATIVE_INVALID") from error
    expected_filter = _filter_from_native(native_candidate)
    if type(filter_candidate) is not dict or filter_candidate != expected_filter:
        raise FadeParityError("E_FX_PARITY_FILTER_CHANGED")
    total = native_candidate["duration_frames"]
    samples = native_candidate["samples"]
    if (type(rgba_frames) is not bytes or
            total > 10000 or len(rgba_frames) != total * 4):
        raise FadeParityError("E_FX_PARITY_RAW_INVALID")
    max_error = 0
    for frame in range(total):
        # Derive opacity from native keyframe samples, independently of the
        # FFmpeg geq progress formula. Holds and zero-length hold are allowed.
        for prev, after in zip(samples, samples[1:]):
            if prev["frame"] <= frame <= after["frame"]:
                span = after["frame"] - prev["frame"]
                fraction = (frame - prev["frame"]) / span if span else 0
                expected = (prev["opacity_percent"] +
                    fraction * (after["opacity_percent"] -
                                prev["opacity_percent"])) * 255 / 100
                break
        else:
            raise FadeParityError("E_FX_PARITY_KEYFRAME_GAP")
        r, g, b, a = rgba_frames[frame * 4:frame * 4 + 4]
        # Fixture is a known opaque red video source, so a background swap
        # or fully blank decoder cannot make a fake alpha test pass.
        if r < 235 or g > 20 or b > 20:
            raise FadeParityError("E_FX_PARITY_SOURCE_CHANGED")
        delta = abs(a - expected)
        if delta > 3:
            raise FadeParityError("E_FX_PARITY_ALPHA_MISMATCH")
        max_error = max(max_error, delta)
    return {
        "schema_version": "native-fade-ffmpeg-alpha-parity-v1",
        "status": "OFFLINE_FULL_TIMELINE_ALPHA_PARITY_ONLY",
        "preset": "FADE", "mode": "BOTH", "speed": "MEDIUM",
        "checked_frames": total, "checked_rgba_samples": total,
        "max_absolute_alpha_error": round(max_error, 4),
        "source_test_pattern": "LAVFI_OPAQUE_RED_ONLY",
        "source_png_verified": False,
        "full_frame_verified": False,
        "canva_fidelity_verified": False,
        "native_premiere_verified": False,
        "host_verified": False,
        "can_assemble": False,
    }
