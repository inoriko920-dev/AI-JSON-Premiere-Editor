"""Immutable read-only source inventory for eventual Premiere media import.

This module PREPARES a candidate inventory: it never imports anything and does
not grant approval. Only fresh, pinned SHA-256 bytes may be added to a later
host-capability/owner-authorized import transaction. SRT is verified but is
NOT passed to Premiere as a visual/audio clip.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .media import _bounded_hash, _format_supported, resolved_path


class ImportSnapshotError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def prepare_media_snapshot(
    edit: dict[str, Any], media_root: Path, *,
    max_file_bytes: int, max_import_items: int
) -> dict[str, Any]:
    """Return a deterministic candidate inventory, NEVER host-executable.

    Every referenced media file must have a declared hash; missing hashes
    cannot be approved by the JSON's pre-existing validation.status field.
    Explicit positive budgets are developer read caps, not production approvals.
    """
    if (type(edit) is not dict or
            type(max_file_bytes) is not int or max_file_bytes <= 0 or
            type(max_import_items) is not int or max_import_items <= 0):
        raise ImportSnapshotError("E_CONFIG_LIMITS_UNVERIFIED")
    sources, assets = edit.get("sources"), edit.get("assets")
    if type(sources) is not dict or type(assets) is not dict or not assets:
        raise ImportSnapshotError("E_IMPORT_CONTRACT_INVALID")
    try:
        root = Path(media_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("not directory")
    except (TypeError, OSError, ValueError) as ex:
        raise ImportSnapshotError("E_MEDIA_ROOT_INVALID") from ex

    jobs: list[tuple[str, str, dict[str, Any], bool]] = []
    for label in ("srt", "audio", "background"):
        info = sources.get(label)
        if type(info) is not dict:
            raise ImportSnapshotError("E_IMPORT_CONTRACT_INVALID")
        jobs.append((f"SOURCE_{label.upper()}", label, info, label != "srt"))
    for asset_id in sorted(assets):
        info = assets[asset_id]
        if (type(asset_id) is not str or not asset_id.isascii() or
                not asset_id.replace("_", "").replace("-", "").isalnum() or
                type(info) is not dict):
            raise ImportSnapshotError("E_IMPORT_CONTRACT_INVALID")
        jobs.append(("ASSET_" + asset_id, "png", info, True))
    if len(jobs) - 1 > max_import_items:  # subtract SRT (not imported)
        raise ImportSnapshotError("E_RESOURCE_LIMIT")

    seen: set[str] = set()
    inventory: list[dict[str, Any]] = []
    for item_id, kind, info, imported in jobs:
        relative = info.get("path")
        expected = info.get("sha256")
        if (type(relative) is not str or type(expected) is not str or
                len(expected) != 64 or
                not all(char in "0123456789abcdefABCDEF" for char in expected)):
            raise ImportSnapshotError("E_MEDIA_HASH_UNPINNED")
        low = relative.lower()
        permitted = ((".srt",) if kind == "srt" else
                     (".mp3", ".wav") if kind == "audio" else
                     (".mp4",) if kind == "background" else (".png",))
        if not low.endswith(permitted):
            raise ImportSnapshotError("E_MEDIA_FORMAT")
        try:
            absolute = resolved_path(root, relative)
            identity = str(absolute).casefold()
            if identity in seen:
                raise ImportSnapshotError("E_MEDIA_ALIAS_AMBIGUOUS")
            seen.add(identity)
            before = absolute.stat()
            actual, count, header = _bounded_hash(absolute, max_file_bytes)
            after = absolute.stat()
        except ImportSnapshotError:
            raise
        except ValueError as ex:
            if str(ex) == "E_RESOURCE_LIMIT":
                raise ImportSnapshotError("E_RESOURCE_LIMIT") from ex
            raise ImportSnapshotError("E_MEDIA_PATH") from ex
        except (OSError, RuntimeError) as ex:
            raise ImportSnapshotError("E_MEDIA_MISSING") from ex
        if (before.st_size != after.st_size or
                before.st_mtime_ns != after.st_mtime_ns or
                count != after.st_size):
            raise ImportSnapshotError("E_MEDIA_CHANGED_DURING_SNAPSHOT")
        if actual.lower() != expected.lower():
            raise ImportSnapshotError("E_MEDIA_HASH")
        matches, _ = _format_supported(relative, header)
        if not matches:
            raise ImportSnapshotError("E_MEDIA_FORMAT")
        inventory.append({
            "item_id": item_id, "kind": kind, "import_to_premiere": imported,
            "relative_path": relative.replace("\\", "/"),
            "absolute_path": str(absolute),
            "sha256": actual, "byte_size": count,
            "mtime_ns": after.st_mtime_ns,
        })
    # This string is an integrity fingerprint, not cryptographic approval.
    canonical = json.dumps(inventory, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return {
        "schema_version": "verified-media-snapshot-v1",
        "status": "CANDIDATE_NOT_AUTHORIZED",
        "can_import": False, "can_assemble": False,
        "project_id": edit.get("project_id"),
        "media_root": str(root),
        "item_count": len(inventory),
        "import_count": sum(bool(x["import_to_premiere"]) for x in inventory),
        "inventory_sha256": digest,
        "items": inventory,
        "warnings": [
            "Snapshot is invalidated by any file change; re-hash immediately before host operation.",
            "Neither media decoding, effect support nor Premiere host permissions are certified."
        ],
    }


def recheck_media_snapshot(snapshot: dict[str, Any], *,
                           max_file_bytes: int) -> bool:
    """Re-hash every pinned source; caller must abort on any false result.

    Rechecking here does not prevent edits between this check and Adobe import.
    Host File.length checks and final readback provide separate defenses.
    """
    if (type(snapshot) is not dict or
            snapshot.get("schema_version") != "verified-media-snapshot-v1" or
            snapshot.get("can_import") is not False or
            type(max_file_bytes) is not int or max_file_bytes <= 0 or
            type(snapshot.get("items")) is not list):
        return False
    items = snapshot["items"]
    if snapshot.get("item_count") != len(items) or not items:
        return False
    try:
        canonical = json.dumps(items, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != snapshot["inventory_sha256"]:
            return False
        for item in items:
            path = resolved_path(Path(snapshot["media_root"]), item["relative_path"])
            if str(path) != item["absolute_path"]:
                return False
            before = path.stat()
            digest, size, _ = _bounded_hash(path, max_file_bytes)
            after = path.stat()
            if (digest != item["sha256"] or size != item["byte_size"]
                    or size != after.st_size or before.st_mtime_ns != after.st_mtime_ns
                    or after.st_mtime_ns != item["mtime_ns"]):
                return False
    except (OSError, KeyError, TypeError, ValueError, RuntimeError):
        return False
    return True
