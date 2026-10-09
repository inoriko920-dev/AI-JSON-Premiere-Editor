"""STEP09 safe, non-destructive background video-only preparation.

Purpose: never rely on EDIT_PLAN background.audio_policy=MUTE as proof that a
Premiere Track.overwriteClip will not introduce linked audio. The original
source is NEVER overwritten. A separate owner-approved cache directory is
required, and the output is only a CANDIDATE, not host authorization.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Callable

from .media import _bounded_hash, resolved_path


SHA = re.compile(r"[a-fA-F0-9]{64}\Z")
MAX_PROBE_OUTPUT = 128 * 1024
CAP_SECONDS = 180


class BackgroundIsolationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _binary(path: Path | None, name: str) -> Path:
    try:
        p = Path(path) if path is not None else None
        if (p is None or not p.is_absolute() or not p.is_file() or
                p.is_symlink() or p.name.lower() not in (name, name + ".exe")):
            raise ValueError("invalid executable")
        return p
    except (TypeError, OSError, ValueError) as exc:
        raise BackgroundIsolationError("E_BACKGROUND_TOOL_UNAVAILABLE") from exc


def _probe(path: Path, binary: Path, runner: Callable[..., Any]) -> dict[str, Any]:
    command = [
        str(binary), "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height",
        "-of", "json", str(path)
    ]
    try:
        process = runner(command, shell=False, capture_output=True,
                         timeout=20, check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise BackgroundIsolationError("E_BACKGROUND_PROBE_FAILED") from exc
    if (process.returncode != 0 or not isinstance(process.stdout, bytes)
            or len(process.stdout) > MAX_PROBE_OUTPUT):
        raise BackgroundIsolationError("E_BACKGROUND_PROBE_FAILED")
    try:
        parsed = json.loads(process.stdout, parse_constant=lambda _: (
            _ for _ in ()).throw(ValueError("nonfinite")))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise BackgroundIsolationError("E_BACKGROUND_PROBE_FAILED") from exc
    if type(parsed) is not dict or type(parsed.get("streams")) is not list:
        raise BackgroundIsolationError("E_BACKGROUND_PROBE_FAILED")
    streams = parsed["streams"]
    videos = [s for s in streams if type(s) is dict and s.get("codec_type") == "video"]
    if (len(videos) != 1 or len(streams) != sum(type(s) is dict for s in streams)
            or not streams):
        raise BackgroundIsolationError("E_BACKGROUND_VIDEO_STREAM_AMBIGUOUS")
    video = videos[0]
    codec = video.get("codec_name")
    width, height = video.get("width"), video.get("height")
    if (type(codec) is not str or not codec or len(codec) > 50 or
            type(width) is not int or type(height) is not int or
            width < 1 or height < 1 or width > 16384 or height > 16384):
        raise BackgroundIsolationError("E_BACKGROUND_VIDEO_UNVERIFIED")
    # No arbitrary stream types on generated output; input may contain audio
    # but subtitle/data/attachment streams require separate creative review.
    kinds = [s.get("codec_type") for s in streams]
    if any(kind not in ("video", "audio") for kind in kinds):
        raise BackgroundIsolationError("E_BACKGROUND_STREAM_TOPOLOGY_UNKNOWN")
    return {"codec": codec, "width": width, "height": height,
            "audio_streams": kinds.count("audio"), "total_streams": len(streams)}


def prepare_video_only_background(
    media_root: Path, relative_source: str, expected_sha256: str,
    cache_root: Path, *, ffmpeg_exe: Path | None,
    ffprobe_exe: Path | None, max_input_bytes: int,
    max_output_bytes: int, runner: Callable[..., Any] = subprocess.run
) -> dict[str, Any]:
    """Create and verify ONE content-addressed, no-audio candidate in safe cache.

    No caller-supplied FFmpeg arguments, automatic cache deletion or overwrite.
    Host edit permission is always False. Duration/FX quality still needs proof.
    """
    if (type(expected_sha256) is not str or SHA.fullmatch(expected_sha256) is None
            or type(max_input_bytes) is not int or max_input_bytes <= 0
            or type(max_output_bytes) is not int or max_output_bytes <= 0
            or type(relative_source) is not str or
            not relative_source.lower().endswith(".mp4")):
        raise BackgroundIsolationError("E_BACKGROUND_REQUEST_INVALID")
    ffmpeg = _binary(ffmpeg_exe, "ffmpeg")
    ffprobe = _binary(ffprobe_exe, "ffprobe")
    try:
        root = Path(media_root).resolve(strict=True)
        source = resolved_path(root, relative_source)
        raw_cache = Path(cache_root)
        cache = raw_cache.resolve(strict=True)
        if (not cache.is_dir() or cache == root or cache.is_relative_to(root)
                or root.is_relative_to(cache) or raw_cache.is_symlink()):
            raise ValueError("cache overlaps media root")
    except (TypeError, OSError, ValueError) as exc:
        raise BackgroundIsolationError("E_BACKGROUND_PATH_INVALID") from exc
    try:
        initial = source.stat()
        digest, count, _ = _bounded_hash(source, max_input_bytes)
        if (digest != expected_sha256.lower() or count != initial.st_size or
                source.stat().st_mtime_ns != initial.st_mtime_ns):
            raise BackgroundIsolationError("E_BACKGROUND_SOURCE_CHANGED")
    except BackgroundIsolationError:
        raise
    except ValueError as exc:
        if str(exc) == "E_RESOURCE_LIMIT":
            raise BackgroundIsolationError("E_RESOURCE_LIMIT") from exc
        raise BackgroundIsolationError("E_BACKGROUND_SOURCE_CHANGED") from exc
    except OSError as exc:
        raise BackgroundIsolationError("E_BACKGROUND_SOURCE_CHANGED") from exc
    profile = _probe(source, ffprobe, runner)
    if profile["audio_streams"] == 0:
        try:
            current_digest, current_size, _ = _bounded_hash(source, max_input_bytes)
            current_time = source.stat().st_mtime_ns
        except (OSError, ValueError) as exc:
            raise BackgroundIsolationError("E_BACKGROUND_SOURCE_CHANGED") from exc
        if (current_digest != digest or current_size != count or
                current_time != initial.st_mtime_ns):
            raise BackgroundIsolationError("E_BACKGROUND_SOURCE_CHANGED")
        return {"status": "ALREADY_VIDEO_ONLY_UNVERIFIED",
                "can_import": False, "can_assemble": False,
                "sha256": digest, "byte_size": count,
                "audio_streams": 0, "output_created": False}
    target = cache / ("BG_NO_AUDIO_" + digest[:24] + ".mp4")
    if target.exists() or target.is_symlink():
        raise BackgroundIsolationError("E_BACKGROUND_CACHE_TARGET_EXISTS")
    fd, tmpname = tempfile.mkstemp(prefix=".bg_work_", suffix=".mp4", dir=cache)
    os.close(fd)
    temp = Path(tmpname)
    try:
        args = [
            str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "error",
            "-i", str(source), "-map", "0:v:0", "-c:v", "copy",
            "-an", "-sn", "-dn", "-map_metadata", "-1",
            "-movflags", "+faststart", "-f", "mp4", "-y", str(temp)
        ]
        try:
            result = runner(args, shell=False, capture_output=True,
                            timeout=CAP_SECONDS, check=False)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise BackgroundIsolationError("E_BACKGROUND_COPY_FAILED") from exc
        if result.returncode != 0:
            raise BackgroundIsolationError("E_BACKGROUND_COPY_FAILED")
        candidate = _probe(temp, ffprobe, runner)
        if candidate["total_streams"] != 1 or candidate["audio_streams"] != 0:
            raise BackgroundIsolationError("E_BACKGROUND_AUDIO_NOT_ISOLATED")
        for field in ("codec", "width", "height"):
            if candidate[field] != profile[field]:
                raise BackgroundIsolationError("E_BACKGROUND_VIDEO_CHANGED")
        size = temp.stat().st_size
        if size <= 0 or size > max_output_bytes:
            raise BackgroundIsolationError("E_RESOURCE_LIMIT")
        final_digest, counted, _ = _bounded_hash(temp, max_output_bytes)
        if size != counted:
            raise BackgroundIsolationError("E_BACKGROUND_OUTPUT_CHANGED")
        current_digest, current_count, _ = _bounded_hash(source, max_input_bytes)
        if (current_digest != digest or current_count != count or
                source.stat().st_mtime_ns != initial.st_mtime_ns):
            raise BackgroundIsolationError("E_BACKGROUND_SOURCE_CHANGED")
        # os.link refuses existing targets atomically; never os.replace()
        # because replacing could destroy a user's cached media.
        try:
            os.link(temp, target)
        except FileExistsError as exc:
            raise BackgroundIsolationError("E_BACKGROUND_CACHE_TARGET_EXISTS") from exc
        except OSError as exc:
            raise BackgroundIsolationError("E_BACKGROUND_CACHE_WRITE_FAILED") from exc
        return {"status": "VIDEO_ONLY_CANDIDATE_UNVERIFIED",
                "can_import": False, "can_assemble": False,
                "sha256": final_digest, "source_sha256": digest,
                "byte_size": counted, "audio_streams": 0,
                "output_created": True, "candidate_path": str(target)}
    finally:
        # Only clean up the freshly created disposable temp file; never touch
        # original media, pre-existing cache entries, or the final new target.
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
