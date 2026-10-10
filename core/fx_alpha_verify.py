"""STEP19: bounded, fail-closed alpha-pixel verification of an existing PNG and MOV.

Decode only sampled RGBA pixels via ffmpeg pipes. Never generate, save, or
modify any images; this module reads a caller-pinned private PNG snapshot and
a private MOV candidate. Sampling verifies codec-decoded alpha behavior, NOT
Canva visual fidelity, whole-frame equivalence, or Premiere host support.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Callable

_GRID = 8
_PIX_BYTES = _GRID * _GRID * 4
_MAX_CAPTURE = 4096


class AlphaPixelError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _run_pixels(ffmpeg: Path, path: Path, filtergraph: str, count: int,
                timeout_seconds: int, runner: Callable[..., Any]) -> bytes:
    # No shell, no output files or user-provided filters.
    args = [str(ffmpeg), "-hide_banner", "-nostdin", "-loglevel", "error",
            "-i", str(path), "-vf", filtergraph, "-fps_mode", "passthrough",
            "-frames:v", str(count), "-pix_fmt", "rgba", "-f", "rawvideo", "-"]
    try:
        call = runner(args, shell=False, capture_output=True,
                      timeout=timeout_seconds, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AlphaPixelError("E_FX_ALPHA_READBACK_FAILED") from exc
    if (call.returncode != 0 or not isinstance(call.stdout, bytes) or
            len(call.stdout) != count * _PIX_BYTES):
        raise AlphaPixelError("E_FX_ALPHA_READBACK_FAILED")
    return call.stdout


def _progress(n: int, frames: int, inside: int, outside: int) -> float:
    if n < inside:
        return n / (inside - 1)
    if n < frames - outside:
        return 1.0
    return max(0.0, (frames - n - 1) / (outside - 1))


def _spatial(direction: str, x: int, y: int, p: float) -> tuple[bool, bool]:
    """Visible, boundary ambiguity. Use nearest-neighbor 8x8 sampling."""
    u = (x + 0.5) / _GRID
    v = (y + 0.5) / _GRID
    if direction == "LEFT_TO_RIGHT":
        d = p - u
    elif direction == "RIGHT_TO_LEFT":
        d = u - (1 - p)
    elif direction == "TOP_TO_BOTTOM":
        d = p - v
    else:
        d = v - (1 - p)
    # One scaled-pixel margin prevents resampling rounding from yielding
    # false claims. Boundaries are deliberately not certified.
    return d >= 0, abs(d) <= 1 / _GRID


def verify_alpha_pixels(*, ffmpeg_exe: Path, source_png: Path,
                        output_mov: Path, width: int, height: int,
                        frames: int, in_frames: int, out_frames: int,
                        preset: str, direction: str, timeout_seconds: int,
                        runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    """Verify source-relative alpha at IN/HOLD/OUT and direction-specific masks.

    A valid source may be transparent at some pixels. If all sampled pixels
    have zero alpha, correctness cannot be established and verification fails.
    This does not authorize host rendering or end-to-end assembly.
    """
    if (any(type(v) is not int or v < 1 for v in
            (width, height, frames, in_frames, out_frames, timeout_seconds)) or
            width < _GRID or height < _GRID or
            frames < in_frames + out_frames or
            in_frames < 2 or out_frames < 2 or
            preset not in ("FADE", "WIPE") or
            (preset == "FADE" and direction != "NONE") or
            (preset == "WIPE" and direction not in
             ("LEFT_TO_RIGHT", "RIGHT_TO_LEFT", "TOP_TO_BOTTOM", "BOTTOM_TO_TOP"))):
        raise AlphaPixelError("E_FX_ALPHA_POLICY_INVALID")
    indexes = sorted({0, in_frames // 2, in_frames - 1,
                      frames - out_frames, frames - out_frames // 2,
                      frames - 1})
    # The only FFmpeg expressions are fixed integer frame indexes compiled
    # from the validated B02 candidate, never user expressions or file paths.
    selector = "+".join("eq(n\\,{})".format(n) for n in indexes)
    png = _run_pixels(ffmpeg_exe, source_png,
                      "scale=8:8:flags=neighbor,format=rgba", 1,
                      timeout_seconds, runner)
    mov = _run_pixels(ffmpeg_exe, output_mov,
                      "select='{}',scale=8:8:flags=neighbor,format=rgba".format(selector),
                      len(indexes), timeout_seconds, runner)
    source = [png[pos + 3] for pos in range(0, _PIX_BYTES, 4)]
    if max(source) < 16:
        raise AlphaPixelError("E_FX_ALPHA_UNOBSERVABLE")
    checked = 0
    for i, n in enumerate(indexes):
        p = _progress(n, frames, in_frames, out_frames)
        for y in range(_GRID):
            for x in range(_GRID):
                offset = y * _GRID + x
                original = source[offset]
                actual = mov[i * _PIX_BYTES + 4 * offset + 3]
                # Masking/fading cannot increase original source alpha. Check
                # EVERY grid pixel, including transparent and WIPE boundaries,
                # before skipping samples unsuitable for effect observability.
                if actual > original + 5:
                    raise AlphaPixelError("E_FX_ALPHA_PIXELS_MISMATCH")
                if original < 16:
                    continue
                if preset == "FADE":
                    scale = p
                else:
                    visible, boundary = _spatial(direction, x, y, p)
                    if boundary:
                        continue
                    scale = 1.0 if visible else 0.0
                expected = original * scale
                if abs(actual - expected) > 5:
                    raise AlphaPixelError("E_FX_ALPHA_PIXELS_MISMATCH")
                checked += 1
    if checked < len(indexes):
        raise AlphaPixelError("E_FX_ALPHA_UNOBSERVABLE")
    return {"pixel_alpha_checked": True,
            "source_grid": [_GRID, _GRID],
            "sampled_frames": len(indexes),
            "checked_alpha_samples": checked,
            "whole_frame_verified": False,
            "canva_fidelity_verified": False,
            "host_verified": False}
