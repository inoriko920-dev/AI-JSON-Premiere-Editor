"""Immutable read-only source inventory for eventual Premiere media import.

This module PREPARES a candidate inventory: it never imports anything and does
not grant approval. Only fresh, pinned SHA-256 bytes may be added to a later
host-capability/owner-authorized import transaction. SRT is verified but is
NOT passed to Premiere as a visual/audio clip.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from .media import _format_supported, resolved_path


class ImportSnapshotError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _stable_media_hash(path: Path, max_bytes: int) -> tuple[str, int, bytes, os.stat_result]:
    """SHA bytes through one descriptor and prove the resolved path did not swap.

    Previous path.stat -> separate open -> path.stat allowed an outside writer
    to substitute another file while source inventory was being hashed.
    Check descriptor identity/size/ctime/mtime before/after, and the path
    identity after closing. No file mutation, no images generated.
    """
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("E_CONFIG_LIMITS_UNVERIFIED")
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("E_MEDIA_CHANGED_DURING_SNAPSHOT")
    if before.st_size > max_bytes:
        raise ValueError("E_RESOURCE_LIMIT")
    hasher = hashlib.sha256()
    size = 0
    first = b""
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("E_MEDIA_CHANGED_DURING_SNAPSHOT")
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("E_RESOURCE_LIMIT")
            if not first:
                first = chunk[:32]
            hasher.update(chunk)
        descriptor_end = os.fstat(stream.fileno())
    after = path.stat()
    def identity(meta: os.stat_result) -> tuple[int, int, int, int, int]:
        return (meta.st_dev, meta.st_ino, meta.st_size,
                meta.st_mtime_ns, meta.st_ctime_ns)
    if (not stat.S_ISREG(after.st_mode) or
            size != before.st_size or
            not (identity(before) == identity(opened) ==
                 identity(descriptor_end) == identity(after))):
        raise ValueError("E_MEDIA_CHANGED_DURING_SNAPSHOT")
    return hasher.hexdigest(), size, first, after


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
    # SRT is inspected but never imported; narration and background always
    # consume the two fixed import slots. Reject excessive asset collections
    # before sorting keys or allocating a queue for every asset.
    if len(assets) + 2 > max_import_items:
        raise ImportSnapshotError("E_RESOURCE_LIMIT")
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
    # Check key types BEFORE sorting: JSON-like direct callers may provide
    # mixed str/non-str keys and sorted(assets) would raise raw TypeError.
    if any(type(asset_id) is not str or
           re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", asset_id) is None
           for asset_id in assets):
        raise ImportSnapshotError("E_IMPORT_CONTRACT_INVALID")
    for asset_id in sorted(assets):
        info = assets[asset_id]
        if type(info) is not dict:
            raise ImportSnapshotError("E_IMPORT_CONTRACT_INVALID")
        jobs.append(("ASSET_" + asset_id, "png", info, True))
    seen: set[str] = set()
    # Two different paths may still name the exact same file via hard links.
    # A source must have an unambiguous identity before creating its
    # non-authorizing inventory, not merely a unique spelled pathname.
    seen_file_ids: set[tuple[int, int]] = set()
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
            actual, count, header, after = _stable_media_hash(
                absolute, max_file_bytes)
        except ImportSnapshotError:
            raise
        except ValueError as ex:
            if str(ex) in ("E_RESOURCE_LIMIT", "E_MEDIA_CHANGED_DURING_SNAPSHOT"):
                raise ImportSnapshotError(str(ex)) from ex
            raise ImportSnapshotError("E_MEDIA_PATH") from ex
        except (OSError, RuntimeError) as ex:
            raise ImportSnapshotError("E_MEDIA_MISSING") from ex
        if count != after.st_size:
            raise ImportSnapshotError("E_MEDIA_CHANGED_DURING_SNAPSHOT")
        file_id = (after.st_dev, after.st_ino)
        if file_id in seen_file_ids:
            raise ImportSnapshotError("E_MEDIA_ALIAS_AMBIGUOUS")
        seen_file_ids.add(file_id)
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
            # A same-byte replacement with restored mtime is still a new
            # source file. Bind the snapshot to its original file identity.
            "device_id": after.st_dev, "file_id": after.st_ino,
            "ctime_ns": after.st_ctime_ns,
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
            snapshot.get("status") != "CANDIDATE_NOT_AUTHORIZED" or
            snapshot.get("can_import") is not False or
            snapshot.get("can_assemble") is not False or
            type(max_file_bytes) is not int or max_file_bytes <= 0 or
            type(snapshot.get("items")) is not list):
        return False
    items = snapshot["items"]
    if (type(snapshot.get("item_count")) is not int or
            snapshot["item_count"] != len(items) or not items or
            type(snapshot.get("import_count")) is not int):
        return False
    try:
        canonical = json.dumps(items, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != snapshot["inventory_sha256"]:
            return False
        # Inventory role and import-count declarations are part of the
        # immutable read-only contract. A recomputed digest cannot promote
        # source-only SRT to an importable Premiere clip.
        required_sources = {
            "SOURCE_SRT": ("srt", False),
            "SOURCE_AUDIO": ("audio", True),
            "SOURCE_BACKGROUND": ("background", True),
        }
        seen_ids: set[str] = set()
        seen_file_ids: set[tuple[int, int]] = set()
        import_total = 0
        for item in items:
            if type(item) is not dict:
                return False
            item_id = item.get("item_id")
            kind = item.get("kind")
            imported = item.get("import_to_premiere")
            if (type(item_id) is not str or item_id in seen_ids or
                    type(imported) is not bool):
                return False
            seen_ids.add(item_id)
            file_device, file_inode = item.get("device_id"), item.get("file_id")
            if (type(file_device) is not int or file_device < 0 or
                    type(file_inode) is not int or file_inode < 0 or
                    (file_device, file_inode) in seen_file_ids):
                return False
            seen_file_ids.add((file_device, file_inode))
            if item_id in required_sources:
                if (kind, imported) != required_sources[item_id]:
                    return False
            elif not (item_id.startswith("ASSET_") and
                      re.fullmatch(r"ASSET_[A-Za-z0-9][A-Za-z0-9_.-]*", item_id)
                      and kind == "png" and imported is True):
                return False
            import_total += int(imported)
        if (not set(required_sources).issubset(seen_ids) or
                len(seen_ids) <= len(required_sources) or
                import_total != snapshot["import_count"]):
            return False
        for item in items:
            # Snapshot versions without immutable file identity metadata
            # cannot certify continued identity, even if the SHA still fits.
            if (type(item) is not dict or
                    any(type(item.get(k)) is not int or item[k] < 0 for k in
                        ("device_id", "file_id", "ctime_ns"))):
                return False
            path = resolved_path(Path(snapshot["media_root"]), item["relative_path"])
            if str(path) != item["absolute_path"]:
                return False
            digest, size, _, after = _stable_media_hash(
                path, max_file_bytes)
            if (digest != item["sha256"] or size != item["byte_size"]
                    or size != after.st_size
                    or after.st_mtime_ns != item["mtime_ns"]
                    or after.st_dev != item["device_id"]
                    or after.st_ino != item["file_id"]
                    or after.st_ctime_ns != item["ctime_ns"]):
                return False
    except (OSError, KeyError, TypeError, ValueError, RuntimeError):
        return False
    return True
