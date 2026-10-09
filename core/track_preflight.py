"""STEP08 offline four-track preflight from REAL files and FFprobe metadata.

Read-only. Produces a deterministic candidate without user media paths in its
public summary. A ticks string supplied by a caller is *not* Premiere host
evidence. No result here authorizes Adobe project writes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import validate_pair
from .media import inspect_media
from .ffprobe import inspect_ffprobe
from .import_snapshot import (ImportSnapshotError, prepare_media_snapshot,
                              recheck_media_snapshot)
from .track_plan import compile_four_track_candidate, TrackPlanError

# Reviews that can remain unresolved in a NON-EXECUTABLE candidate only.
# Unknown policies, uncalibrated speeds, uncertain source timing block even
# the draft instead of silently applying fallback values.
CONTRACT_PENDING_ONLY = {
    "E_CONFIG_LIMITS_UNVERIFIED", "E_MEDIA_UNVERIFIED",
    "E_PROFILE_UNVERIFIED", "E_HOST_UNVERIFIED"
}
MEDIA_PENDING_ONLY = {"E_MEDIA_DECODE_UNVERIFIED", "E_HOST_UNVERIFIED"}
FFPROBE_PENDING_ONLY = {"E_DECODE_PREMIERE_UNVERIFIED", "E_FFPROBE_UNAVAILABLE"}


def _problem(code: str, stage: str, severity: str = "ERROR") -> dict[str, str]:
    return {"code": code, "severity": severity, "stage": stage}


def _finish(issues: list[dict[str, str]], candidate: dict | None = None
            ) -> dict[str, Any]:
    errors = sum(x["severity"] == "ERROR" for x in issues)
    result: dict[str, Any] = {
        "schema_version": "offline-track-preflight-v1",
        "status": "PREFLIGHT_FAIL" if errors else "NEEDS_REVIEW",
        "can_import": False, "can_assemble": False,
        "error_count": errors,
        "review_count": len(issues) - errors,
        "issues": issues,
        "track_candidate": None,
    }
    if candidate is not None and not errors:
        # No media root, absolute paths, clip paths, nested source inventory,
        # mutable frame list or inferred source data crosses the UI boundary.
        result["track_candidate"] = {
            "status": "CANDIDATE_NOT_EXECUTABLE",
            "can_assemble": False,
            "total_frames": candidate["total_frames"],
            "track_counts": dict(candidate["track_counts"]),
            "operation_sha256": candidate["operation_sha256"],
        }
    return result


def prepare_track_preflight(
    edit: dict[str, Any], animation: dict[str, Any],
    media_root: Path, *, ffprobe_exe: Path | None,
    ticks_per_frame: str | None, max_media_bytes: int,
    max_srt_cues: int, max_import_items: int,
    ffprobe_runner=None
) -> dict[str, Any]:
    """Do actual bounded file/SRT/FFprobe checks before a 4-track draft.

    This preflight is read-only and cannot grant READY even when all inputs
    are valid. A user/caller-provided timebase is explicitly untrusted until
    real Premiere host readback is available.
    """
    issues: list[dict[str, str]] = []
    if any(type(v) is not int or v <= 0 for v in
           (max_media_bytes, max_srt_cues, max_import_items)):
        return _finish([_problem("E_CONFIG_LIMITS_UNVERIFIED", "resource")])
    contract = validate_pair(edit, animation)
    for raw in contract["issues"]:
        if raw["severity"] == "ERROR" or raw["code"] not in CONTRACT_PENDING_ONLY:
            issues.append(_problem(raw["code"], "contract"))
    if issues:
        return _finish(issues)

    files = inspect_media(edit, media_root, max_file_bytes=max_media_bytes,
                          max_srt_cues=max_srt_cues)
    for raw in files["issues"]:
        if raw["severity"] == "ERROR" or raw["code"] not in MEDIA_PENDING_ONLY:
            issues.append(_problem(raw["code"], "media"))
    if issues:
        return _finish(issues)
    try:
        snapshot = prepare_media_snapshot(
            edit, media_root, max_file_bytes=max_media_bytes,
            max_import_items=max_import_items
        )
    except ImportSnapshotError as ex:
        return _finish([_problem(ex.code, "snapshot")])
    if not recheck_media_snapshot(snapshot, max_file_bytes=max_media_bytes):
        return _finish([_problem("E_MEDIA_SNAPSHOT_STALE", "snapshot")])

    kwargs: dict[str, Any] = {"ffprobe_exe": ffprobe_exe}
    if ffprobe_runner is not None:
        kwargs["runner"] = ffprobe_runner
    probe = inspect_ffprobe(edit, media_root, **kwargs)
    for raw in probe["issues"]:
        if raw["severity"] == "ERROR" or raw["code"] not in FFPROBE_PENDING_ONLY:
            # Even if FFprobe is absent, do not infer duration from scene or
            # narration quote. The user needs actual decoder metadata.
            issues.append(_problem(raw["code"], "ffprobe"))
    if issues:
        # FFprobe not configured is a non-authorizing REVIEW, not a false
        # claim of malformed user media. No candidate is emitted without
        # actual stream metadata and duration.
        return _finish(issues)
    durations: dict[str, int] = {}
    for item in probe["streams"]:
        pointer = item.get("pointer")
        kind = item.get("stream_kind")
        ms = item.get("duration_ms")
        expected = {
            "/sources/audio": "audio",
            "/sources/background": "video",
        }.get(pointer)
        if (expected is None or expected != kind or pointer in durations or
                type(ms) is not int or ms <= 0):
            return _finish([_problem("E_TRACK_SOURCE_DURATION_UNVERIFIED",
                                     "ffprobe")])
        durations[pointer] = ms
    if set(durations) != {"/sources/audio", "/sources/background"}:
        return _finish([_problem("E_TRACK_SOURCE_DURATION_UNVERIFIED",
                                 "ffprobe")])
    if ticks_per_frame is None:
        return _finish([_problem("E_HOST_TIMEBASE_UNVERIFIED", "host", "REVIEW")])
    try:
        plan = compile_four_track_candidate(
            edit, animation, ticks_per_frame=ticks_per_frame,
            audio_duration_ms=durations["/sources/audio"],
            background_duration_ms=durations["/sources/background"],
            media_snapshot=snapshot,
        )
    except (TrackPlanError, ValueError, KeyError, TypeError):
        return _finish([_problem("E_TRACK_CANDIDATE_REJECTED", "track")])
    # The source can change even while FFprobe was running.
    if not recheck_media_snapshot(snapshot, max_file_bytes=max_media_bytes):
        return _finish([_problem("E_MEDIA_SNAPSHOT_STALE", "snapshot")])
    issues.append(_problem("E_HOST_AND_FX_UNVERIFIED", "host", "REVIEW"))
    return _finish(issues, plan)
