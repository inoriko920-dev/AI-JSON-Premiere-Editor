"""STEP28: read-only source-snapshot → track-occurrence → FX cache preflight.

This is an *offline candidate consistency proof*, not authorization to
assemble Premiere tracks. No host, import, render, source mutation or image
generation. Caller may only use metadata from an independently prepared
source snapshot; never trust the previous cache report as a source reference.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable

from .animation_phases import build_both_phase_candidate
from .fx_alpha_backend import compile_filter, AlphaBackendError
from .fx_cache_worker import (
    AlphaCacheError, _safe_png_header, verify_cache_for_candidate)
from .fx_native_fade_binding import _valid_plan, FadeBindingError
from .import_snapshot import recheck_media_snapshot
from .media import resolved_path

_INSTANCE = re.compile(r"[A-Za-z0-9_-]+/([A-Za-z0-9][A-Za-z0-9_.-]{0,89})\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class MediaCacheTrackError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _snapshot_items(snapshot: Any, plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if (type(snapshot) is not dict or
            snapshot.get("schema_version") != "verified-media-snapshot-v1" or
            snapshot.get("status") != "CANDIDATE_NOT_AUTHORIZED" or
            snapshot.get("can_import") is not False or
            snapshot.get("can_assemble") is not False or
            snapshot.get("project_id") != plan["project_id"] or
            type(snapshot.get("items")) is not list or
            not 1 <= len(snapshot["items"]) <= 2000 or
            type(snapshot.get("item_count")) is not int or
            snapshot["item_count"] != len(snapshot["items"]) or
            type(snapshot.get("import_count")) is not int or
            not _SHA.fullmatch(str(snapshot.get("inventory_sha256")))):
        raise MediaCacheTrackError("E_FX_MEDIA_SNAPSHOT_INVALID")
    items = snapshot["items"]
    by_id = {}
    import_count = 0
    for x in items:
        if (type(x) is not dict or
                type(x.get("item_id")) is not str or
                x["item_id"] in by_id or
                x.get("kind") not in ("png", "srt", "audio", "background") or
                type(x.get("import_to_premiere")) is not bool or
                type(x.get("sha256")) is not str or
                not _SHA.fullmatch(x["sha256"]) or
                type(x.get("byte_size")) is not int or x["byte_size"] < 1 or
                type(x.get("mtime_ns")) is not int or x["mtime_ns"] < 0 or
                type(x.get("relative_path")) is not str or
                type(x.get("absolute_path")) is not str):
            raise MediaCacheTrackError("E_FX_MEDIA_SNAPSHOT_INVALID")
        by_id[x["item_id"]] = x
        import_count += int(x["import_to_premiere"])
    if (import_count != snapshot["import_count"] or
            plan["media_digest"] != snapshot["inventory_sha256"] or
            {p["item_id"] for p in plan["placements"]} !=
                {x["item_id"] for x in items if x["import_to_premiere"]}):
        raise MediaCacheTrackError("E_FX_MEDIA_TRACK_MISMATCH")
    data = json.dumps(items, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    if sha256(data).hexdigest() != snapshot["inventory_sha256"]:
        raise MediaCacheTrackError("E_FX_MEDIA_SNAPSHOT_CHANGED")
    return by_id


def _source_dimensions(snapshot: dict[str, Any], source: dict[str, Any],
                       max_pixels: int) -> tuple[int, int]:
    """Read only the owner-existing PNG header, never build a PNG fixture."""
    try:
        path = resolved_path(Path(snapshot["media_root"]), source["relative_path"])
        if (str(path) != source["absolute_path"] or
                path.suffix.lower() != ".png" or
                source["kind"] != "png" or
                source["import_to_premiere"] is not True):
            raise MediaCacheTrackError("E_FX_MEDIA_SOURCE_MISMATCH")
        with path.open("rb") as file:
            header = file.read(33)
        return _safe_png_header(header, max_pixels)
    except MediaCacheTrackError:
        raise
    except (AlphaCacheError, ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        raise MediaCacheTrackError("E_FX_MEDIA_SOURCE_UNREADABLE") from error


def inspect_media_cache_track(
    snapshot: dict[str, Any], plan: dict[str, Any], fx_item: dict[str, Any],
    report: dict[str, Any], *, cache_root: Path, ffprobe_exe: Path,
    max_media_bytes: int, max_pixels: int, max_cached_bytes: int,
    timeout_seconds: int, runner: Callable[..., Any] = subprocess.run
) -> dict[str, Any]:
    """Reject stale or wrong source/effect/scene before any FFprobe.

    Source snapshot recheck is immediate, but later user edits are always
    possible: caller must repeat the recheck at authorized host transaction.
    """
    for value in (max_media_bytes, max_pixels, max_cached_bytes,
                  timeout_seconds):
        if type(value) is not int or value < 1:
            raise MediaCacheTrackError("E_FX_RESOURCE_LIMIT_UNVERIFIED")
    try:
        _valid_plan(plan)
        compiled = compile_filter(fx_item)
    except (FadeBindingError, AlphaBackendError, KeyError, ValueError, TypeError) as error:
        raise MediaCacheTrackError("E_FX_PLAN_OR_PRESET_INVALID") from error
    by_id = _snapshot_items(snapshot, plan)
    if type(fx_item) is not dict:
        raise MediaCacheTrackError("E_FX_INSTANCE_INVALID")
    instance_key = fx_item.get("instance_key")
    match = _INSTANCE.fullmatch(instance_key) if type(instance_key) is str else None
    if match is None:
        raise MediaCacheTrackError("E_FX_INSTANCE_INVALID")
    target_id = "ASSET_" + match.group(1)
    targets = [p for p in plan["placements"]
               if p["instance_key"] == instance_key]
    if len(targets) != 1:
        raise MediaCacheTrackError("E_FX_INSTANCE_MISSING")
    place = targets[0]
    if (place["item_id"] != target_id or
            place["target_track"] not in ("V2", "V3") or
            place["source_policy"] != "IMAGE_FX_AND_LAYOUT_UNVERIFIED" or
            place["start_frame"] != fx_item["start_frame"] or
            place["end_frame"] != fx_item["end_frame"] or
            place["end_frame"] - place["start_frame"] != compiled["frames"]):
        raise MediaCacheTrackError("E_FX_TRACK_OCCURRENCE_MISMATCH")
    owner_source = by_id.get(target_id)
    if (owner_source is None or owner_source["kind"] != "png" or
            owner_source["import_to_premiere"] is not True):
        raise MediaCacheTrackError("E_FX_MEDIA_SOURCE_MISMATCH")
    # Reject mutated source immediately; no cache read until a fresh file hash.
    if not recheck_media_snapshot(snapshot, max_file_bytes=max_media_bytes):
        raise MediaCacheTrackError("E_FX_MEDIA_SNAPSHOT_STALE")
    dimensions = _source_dimensions(snapshot, owner_source, max_pixels)
    try:
        audit = verify_cache_for_candidate(
            report, fx_item, expected_source_sha256=owner_source["sha256"],
            expected_source_dimensions=dimensions, cache_root=cache_root,
            ffprobe_exe=ffprobe_exe, max_cached_bytes=max_cached_bytes,
            timeout_seconds=timeout_seconds, runner=runner)
    except AlphaCacheError as error:
        raise MediaCacheTrackError(error.code) from error
    # FFprobe/cache audit may take seconds. The user-owned PNG, SRT,
    # narration or background may be replaced *during* that audit.
    # Never publish a positive cross-stage report from a stale snapshot.
    # This does NOT grant safety after return or authorize Adobe writes.
    if not recheck_media_snapshot(snapshot, max_file_bytes=max_media_bytes):
        raise MediaCacheTrackError("E_FX_MEDIA_SNAPSHOT_STALE")
    return {
        "schema_version": "media-cache-track-preflight-v1",
        "status": "OFFLINE_SOURCE_OCCURRENCE_CACHE_MATCH_NOT_HOST_AUTHORIZED",
        "project_id": plan["project_id"],
        "media_inventory_sha256": snapshot["inventory_sha256"],
        "track_plan_sha256": plan["operation_sha256"],
        "instance_key": instance_key,
        "item_id": target_id,
        "target_track": place["target_track"],
        "source_sha256": owner_source["sha256"],
        "cache_key_sha256": audit["cache_key_sha256"],
        "output_sha256": audit["output_sha256"],
        "frames": compiled["frames"],
        "cache_metadata_checked": True,
        "source_recheck_at_preflight": True,
        "source_recheck_after_cache_audit": True,
        "source_recheck_at_host_transaction": False,
        "real_premiere_readback_verified": False,
        "host_verified": False,
        "can_import": False,
        "can_assemble": False,
    }
