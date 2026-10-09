"""STEP10 non-destructive provenance binding for FFmpeg video-only background.

A background MP4 that originally contains audio is NOT safe to place directly
on Premiere video track V1: Track.overwriteClip might create linked audio.
This module binds the independently produced VIDEO-ONLY cache item back to
the full original source snapshot, verifies both file hashes and exact video
frame topology, and produces a *non-executable* derived-source overlay.

It never rewrites EDIT_PLAN, changes user media, launches FFmpeg, copies files,
authorizes a host import, or claims Premiere 2024 has passed G3.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

from .import_snapshot import recheck_media_snapshot
from .media import _bounded_hash, resolved_path


HEX64 = re.compile(r"[a-f0-9]{64}\Z")
MAX_RESPONSE = 128 * 1024
FRAME_RATE = "30/1"


class OverlayError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _source_metadata(path: Path, ffprobe: Path, runner: Callable[..., Any]) -> dict[str, Any]:
    args = [
        str(ffprobe), "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,"
        "avg_frame_rate,nb_frames,duration,start_time",
        "-of", "json", str(path),
    ]
    try:
        proc = runner(args, shell=False, capture_output=True,
                      timeout=20, check=False)
        if (proc.returncode != 0 or type(proc.stdout) is not bytes or
                len(proc.stdout) > MAX_RESPONSE):
            raise OverlayError("E_OVERLAY_FFPROBE_FAILED")
        data = json.loads(proc.stdout, parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError("nonfinite JSON constant")))
    except (OSError, UnicodeError, subprocess.SubprocessError, ValueError, TypeError) as exc:
        if isinstance(exc, OverlayError):
            raise
        raise OverlayError("E_OVERLAY_FFPROBE_FAILED") from exc
    if type(data) is not dict or type(data.get("streams")) is not list:
        raise OverlayError("E_OVERLAY_STREAMS_INVALID")
    streams = data["streams"]
    if any(type(s) is not dict for s in streams):
        raise OverlayError("E_OVERLAY_STREAMS_INVALID")
    videos = [s for s in streams if s.get("codec_type") == "video"]
    other = [s for s in streams if s.get("codec_type") not in ("video", "audio")]
    if len(videos) != 1 or other:
        raise OverlayError("E_OVERLAY_STREAMS_INVALID")
    video = videos[0]
    width, height = video.get("width"), video.get("height")
    codec = video.get("codec_name")
    if (type(codec) is not str or not codec or len(codec) > 50
            or type(width) is not int or type(height) is not int
            or width < 1 or height < 1 or width > 16384 or height > 16384):
        raise OverlayError("E_OVERLAY_VIDEO_PROFILE_INVALID")
    if video.get("avg_frame_rate") != FRAME_RATE:
        raise OverlayError("E_OVERLAY_FRAME_RATE_UNVERIFIED")
    frames = video.get("nb_frames")
    if type(frames) is not str or not frames.isdecimal() or not 1 <= int(frames) <= 10_000_000:
        raise OverlayError("E_OVERLAY_FRAME_COUNT_UNVERIFIED")
    def decimal(value: Any) -> Decimal:
        if type(value) is not str:
            raise OverlayError("E_OVERLAY_VIDEO_TIMING_UNVERIFIED")
        try:
            n = Decimal(value)
            if not n.is_finite() or n < 0:
                raise ValueError("bad time")
            return n
        except (InvalidOperation, ValueError) as exc:
            raise OverlayError("E_OVERLAY_VIDEO_TIMING_UNVERIFIED") from exc
    start = decimal(video.get("start_time"))
    duration = decimal(video.get("duration"))
    if duration <= 0:
        raise OverlayError("E_OVERLAY_VIDEO_TIMING_UNVERIFIED")
    return {
        "codec": codec, "width": width, "height": height,
        "frames": int(frames), "start": start, "duration": duration,
        "audio_count": sum(s.get("codec_type") == "audio" for s in streams),
        "stream_count": len(streams),
    }


def prepare_background_overlay(
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
    """Return *unapproved* derived-background candidate; all byte checks real.

    Deliberately requires both video streams to have exact 30/1 frame rate and
    explicit n_frames and start/duration metadata. A remux that changes even
    one encoded video frame or clip PTS relationship is NOT silently approved.
    """
    if type(max_media_bytes) is not int or max_media_bytes <= 0:
        raise OverlayError("E_CONFIG_LIMITS_UNVERIFIED")
    try:
        root = Path(media_root).resolve(strict=True)
        cache_input = Path(cache_root)
        cache = cache_input.resolve(strict=True)
        exe = Path(ffprobe_exe) if ffprobe_exe is not None else None
        if (not root.is_dir() or not cache.is_dir() or
                cache == root or cache.is_relative_to(root) or
                root.is_relative_to(cache) or cache_input.is_symlink() or
                exe is None or not exe.is_absolute() or not exe.is_file() or
                exe.is_symlink() or exe.name.lower() not in ("ffprobe", "ffprobe.exe")):
            raise ValueError("invalid dirs or ffprobe")
    except (OSError, ValueError, TypeError) as exc:
        raise OverlayError("E_OVERLAY_PATH_OR_TOOL_INVALID") from exc
    if (type(edit) is not dict or type(isolation_report) is not dict or
            type(original_snapshot) is not dict or
            type(edit.get("sources")) is not dict):
        raise OverlayError("E_OVERLAY_REQUEST_INVALID")
    bg = edit["sources"].get("background", {})
    if type(bg) is not dict or type(bg.get("path")) is not str or (
            type(bg.get("sha256")) is not str or
            HEX64.fullmatch(bg["sha256"].lower()) is None):
        raise OverlayError("E_OVERLAY_SOURCE_UNPINNED")
    if (original_snapshot.get("schema_version") != "verified-media-snapshot-v1"
            or original_snapshot.get("status") != "CANDIDATE_NOT_AUTHORIZED"
            or original_snapshot.get("can_import") is not False
            or original_snapshot.get("can_assemble") is not False
            or original_snapshot.get("media_root") != str(root)
            or not recheck_media_snapshot(original_snapshot,
                                          max_file_bytes=max_media_bytes)):
        raise OverlayError("E_OVERLAY_ORIGINAL_SNAPSHOT_STALE")
    items = original_snapshot.get("items", [])
    entries = [i for i in items if type(i) is dict and
               i.get("item_id") == "SOURCE_BACKGROUND"]
    if (len(entries) != 1 or entries[0].get("sha256") != bg["sha256"].lower()
            or entries[0].get("relative_path") != bg["path"].replace("\\", "/")):
        raise OverlayError("E_OVERLAY_SNAPSHOT_MISMATCH")
    original = resolved_path(root, bg["path"])
    if (isolation_report.get("status") != "VIDEO_ONLY_CANDIDATE_UNVERIFIED"
            or isolation_report.get("output_created") is not True
            or isolation_report.get("audio_streams") != 0
            or isolation_report.get("can_import") is not False
            or isolation_report.get("can_assemble") is not False
            or isolation_report.get("source_sha256") != entries[0]["sha256"]
            or type(isolation_report.get("sha256")) is not str or
            HEX64.fullmatch(isolation_report["sha256"]) is None):
        raise OverlayError("E_OVERLAY_ISOLATION_REPORT_INVALID")
    try:
        candidate_input = Path(isolation_report["candidate_path"])
        candidate = candidate_input.resolve(strict=True)
        expected_name = "BG_NO_AUDIO_" + entries[0]["sha256"][:24] + ".mp4"
        if (not candidate_input.is_absolute() or candidate_input.is_symlink()
                or not candidate.is_file() or candidate.parent != cache
                or candidate.name != expected_name):
            raise ValueError("unsafe candidate")
        pre = candidate.stat()
        digest, length, _ = _bounded_hash(candidate, max_media_bytes)
        if (digest != isolation_report["sha256"] or
                length != isolation_report["byte_size"] or
                length != pre.st_size):
            raise ValueError("hash mismatch")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise OverlayError("E_OVERLAY_DERIVED_FILE_INVALID") from exc
    before_original = original.stat()
    try:
        source_profile = _source_metadata(original, exe, runner)
        derived_profile = _source_metadata(candidate, exe, runner)
    except OverlayError:
        raise
    if (source_profile["audio_count"] < 1 or
            derived_profile["audio_count"] != 0 or
            derived_profile["stream_count"] != 1):
        raise OverlayError("E_OVERLAY_AUDIO_TOPOLOGY_INVALID")
    for key in ("codec", "width", "height", "frames"):
        if derived_profile[key] != source_profile[key]:
            raise OverlayError("E_OVERLAY_VIDEO_IDENTITY_CHANGED")
    # No tolerance heuristics: exact video stream start and duration are
    # required before binding a source into a candidate clip worklist.
    if (derived_profile["start"] != source_profile["start"] or
            derived_profile["duration"] != source_profile["duration"]):
        raise OverlayError("E_OVERLAY_VIDEO_TIMING_CHANGED")
    try:
        old_digest, old_size, _ = _bounded_hash(original, max_media_bytes)
        new_digest, new_size, _ = _bounded_hash(candidate, max_media_bytes)
        if (old_digest != entries[0]["sha256"] or
                old_size != before_original.st_size or
                original.stat().st_mtime_ns != before_original.st_mtime_ns or
                new_digest != digest or new_size != length or
                candidate.stat().st_mtime_ns != pre.st_mtime_ns or
                not recheck_media_snapshot(original_snapshot,
                                           max_file_bytes=max_media_bytes)):
            raise OverlayError("E_OVERLAY_FILE_CHANGED_DURING_PROBE")
    except (ValueError, OSError) as exc:
        raise OverlayError("E_OVERLAY_FILE_CHANGED_DURING_PROBE") from exc
    # Internal plan fingerprint binds original project inventory to derived MP4.
    # No actual user file path or original file contents exposed in public view.
    canonical = json.dumps({
        "source_inventory": original_snapshot["inventory_sha256"],
        "source_sha256": old_digest, "derived_sha256": digest,
        "derived_path": str(candidate), "frames": source_profile["frames"],
        "frame_rate": FRAME_RATE, "codec": source_profile["codec"],
        "video_duration_s": str(source_profile["duration"]),
        "video_start_s": str(source_profile["start"]),
    }, sort_keys=True, separators=(",", ":")).encode()
    fingerprint = hashlib.sha256(canonical).hexdigest()
    return {
        "schema_version": "derived-background-overlay-v1",
        "status": "CANDIDATE_NOT_AUTHORIZED",
        "can_import": False, "can_assemble": False,
        "original_inventory_sha256": original_snapshot["inventory_sha256"],
        "source_sha256": old_digest, "derived_sha256": digest,
        "derived_absolute_path": str(candidate),
        "derived_byte_size": new_size,
        "video_frame_count": source_profile["frames"],
        "video_fps": FRAME_RATE,
        "video_codec": source_profile["codec"],
        "overlay_sha256": fingerprint,
        "public_summary": {
            "status": "CANDIDATE_NOT_AUTHORIZED",
            "can_import": False, "can_assemble": False,
            "video_frame_count": source_profile["frames"],
            "video_fps": FRAME_RATE, "overlay_sha256": fingerprint,
        },
        "remaining_blockers": [
            "NO_HOST_PROVEN_AUDIO_LINK_READBACK",
            "NO_FX_OR_CROP_BACKEND_CERTIFICATION",
            "NO_APPROVED_SEQUENCE_DISPATCHER",
        ],
    }
