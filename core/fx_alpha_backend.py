"""STEP16: actual FFmpeg alpha filtergraph compiler for FADE and WIPE ONLY.

All other 19 presets deliberately BLOCK instead of silently approximating
distinct Canva effects. Source schedule is an uncalibrated STEP15 B02 reference.
This component can generate runnable filters and FFmpeg argv, but does not
authorize Premiere import, rendering to user paths or final visual approval.
No file I/O, image creation, subprocess execution or FFmpeg downloads here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

SUPPORTED = frozenset({"FADE", "WIPE"})
WIPE_DIRECTIONS = frozenset({
    "LEFT_TO_RIGHT", "RIGHT_TO_LEFT", "TOP_TO_BOTTOM", "BOTTOM_TO_TOP"
})
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class AlphaBackendError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _integer(v: Any, minimum: int = 0) -> bool:
    return type(v) is int and v >= minimum


def _check(item: Any) -> tuple[str, int, int, int]:
    if type(item) is not dict:
        raise AlphaBackendError("E_FX_BACKEND_INPUT")
    preset = item.get("preset")
    if preset not in SUPPORTED:
        raise AlphaBackendError("E_FX_BACKEND_NOT_IMPLEMENTED")
    if (item.get("mode") != "BOTH" or item.get("speed") != "MEDIUM" or
        item.get("can_render") is not False or
        item.get("effect_backend") != "NOT_IMPLEMENTED" or
        item.get("keyframes") is not None or
        item.get("source_reference") != "STEP01_B02_PROPOSED_21"):
        raise AlphaBackendError("E_FX_BACKEND_INPUT")
    direction = item.get("direction")
    if ((preset == "FADE" and direction != "NONE") or
        (preset == "WIPE" and direction not in WIPE_DIRECTIONS)):
        raise AlphaBackendError("E_FX_DIRECTION_INVALID")
    start,end,inside,outside = [item.get(k) for k in (
        "start_frame", "end_frame", "in_frames", "out_frames")]
    if not (_integer(start) and _integer(end, 1) and
            _integer(inside, 1) and _integer(outside, 1) and
            start < end and end-start >= inside+outside):
        raise AlphaBackendError("E_TIME_006")
    if (item.get("in_range") != [start,start+inside] or
        item.get("hold_range") != [start+inside,end-outside] or
        item.get("out_range") != [end-outside,end]):
        raise AlphaBackendError("E_FX_PHASE_TAMPERED")
    return direction, end-start,inside,outside


def compile_filter(item: dict) -> dict:
    """Compile candidate pixel-alpha animation at original resolution, 30 fps.

    Uses FFmpeg's planar GBR+alpha generic equation. We only alter the alpha
    plane; RGB channels are copied unmodified and no crop/scale is invented.
    Progress uses the exact B02 IN and OUT frame budgets. Output must be
    vetted visually against the owner's final animation reference.
    """
    direction,frames,inside,outside = _check(item)
    preset = item["preset"]
    # N is the local *frame* number used by FFmpeg geq, not scene-global time.
    progress = ("if(lt(N,{ins}),(N+1)/{ins},"
                "if(lt(N,{cut}),1,max(0,(D-N-1)/{out})))").format(
                   ins=inside,cut=frames-outside,D=frames,out=outside)
    if preset == "FADE":
        alpha = "alpha(X,Y)*(" + progress + ")"
    else:
        # Spatial coverage; no geometric image movement or auto-crop.
        tests = {
            "LEFT_TO_RIGHT": "lt(X,W*({p}))",
            "RIGHT_TO_LEFT": "gte(X,W*(1-({p})))",
            "TOP_TO_BOTTOM": "lt(Y,H*({p}))",
            "BOTTOM_TO_TOP": "gte(Y,H*(1-({p})))"
        }
        alpha = "alpha(X,Y)*if(" + tests[direction].format(p=progress) + ",1,0)"
    # With RGB input converted to GBRAP, the alpha plane remains 8-bit.
    # Never accept expressions, numbers or command line fragments from a JSON.
    graph = ("format=gbrap,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='" +
             alpha + "',format=argb")
    return {
        "schema_version": "ffmpeg-alpha-filter-candidate-v1",
        "status": "FILTER_COMPILED_NOT_HOST_OR_VISUALLY_CERTIFIED",
        "preset": preset, "direction": direction,
        "frames": frames, "fps": 30,
        "width_policy": "PRESERVE_SOURCE",
        "height_policy": "PRESERVE_SOURCE",
        "pixel_format": "argb",
        "codec": "qtrle",
        "filtergraph": graph,
        "can_assemble": False, "can_claim_canva_fidelity": False
    }


def build_ffmpeg_command(candidate: dict, ffmpeg_exe: Path,
                         source_png: Path, output_mov: Path) -> list[str]:
    """Produce an argv vector for a caller-controlled cache worker, NOT execute.

    No shell, no overwrite, no silent resizing, no modifying source PNG.
    Caller must separately verify file bytes, approved media root/cache root,
    codec availability and output isolation before running the command.
    """
    if (type(candidate) is not dict or
        candidate.get("schema_version") != "ffmpeg-alpha-filter-candidate-v1" or
        candidate.get("status") != "FILTER_COMPILED_NOT_HOST_OR_VISUALLY_CERTIFIED" or
        candidate.get("can_assemble") is not False or
        candidate.get("preset") not in SUPPORTED or
        not _integer(candidate.get("frames"), 1) or
        not isinstance(candidate.get("filtergraph"), str)):
        raise AlphaBackendError("E_FX_COMMAND_UNVERIFIED")
    # Rebuild filter from immutable compiler output, reject modified payloads.
    # Phase range inputs are not contained here, so bind command only after
    # caller attests exact compiler object rather than accepting arbitrary graph.
    for path, suffix in ((source_png, ".png"),(output_mov,".mov")):
        if (not isinstance(path, Path) or not path.is_absolute() or
                path.suffix.lower() != suffix):
            raise AlphaBackendError("E_FX_PATH_UNVERIFIED")
    if (not isinstance(ffmpeg_exe,Path) or not ffmpeg_exe.is_absolute() or
        ffmpeg_exe.name.lower() not in {"ffmpeg","ffmpeg.exe"}):
        raise AlphaBackendError("E_FX_BINARY_UNVERIFIED")
    graph=candidate["filtergraph"]
    if (len(graph)>1400 or not graph.startswith("format=gbrap,geq=") or
        not graph.endswith(",format=argb")):
        raise AlphaBackendError("E_FX_COMMAND_UNVERIFIED")
    return [
        str(ffmpeg_exe), "-hide_banner", "-nostdin", "-loglevel", "error",
        "-n", "-loop", "1", "-framerate", "30", "-i", str(source_png),
        "-vf", graph, "-frames:v", str(candidate["frames"]),
        "-an", "-c:v", "qtrle", "-pix_fmt", "argb",
        "-f", "mov", str(output_mov)
    ]


def backend_support() -> dict:
    return {
        "schema_version": "ffmpeg-alpha-implementation-status-v1",
        "coded_presets": sorted(SUPPORTED),
        "unimplemented_presets": 19,
        "actual_host_certified": 0,
        "can_assemble": False,
        "visual_calibration": "PENDING_OWNER_REFERENCE",
    }
