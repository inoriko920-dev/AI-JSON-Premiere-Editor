"""Read-only offline diagnostics; no Premiere operations or unapproved READY status.

Example:
 python -m core.validate_cli --edit ./EDIT_PLAN.json \
     --animation ./ANIMATION_PLAN.json --max-json-bytes 1048576

This user-supplied max is a DEVELOPMENT read bound, not the production
resource-limit approval required by ADR-002.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .contracts import loads_strict, validate_pair
from .media import inspect_media


def error(code: str, message: str) -> dict:
    return {"schema_version": "structure-validation-report-v1",
            "status": "PREFLIGHT_FAIL", "can_assemble": False,
            "error_count": 1, "review_count": 0,
            "scene_count": 0, "asset_instance_count": 0,
            "issues": [{"code": code, "severity": "ERROR",
                        "pointer": "/inputs", "message": message}]}


def read_json(path: Path, max_bytes: int) -> object:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError("E_RESOURCE_LIMIT")
    if not path.is_file():
        raise OSError("File tidak tersedia.")
    with path.open("rb") as f:
        blob = f.read(max_bytes + 1)
    if len(blob) > max_bytes:
        raise ValueError("E_RESOURCE_LIMIT")
    return loads_strict(blob)


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edit", required=True, type=Path)
    parser.add_argument("--animation", required=True, type=Path)
    parser.add_argument("--max-json-bytes", required=True, type=int,
                        help="Development per-file read cap, explicit; not production approval")
    parser.add_argument("--caps", type=Path,
                        help="Optional future independently approved resource manifest")
    parser.add_argument("--media-root", type=Path, help="Optional explicit media project root")
    parser.add_argument("--max-media-bytes", type=int, help="Required when auditing media")
    parser.add_argument("--max-srt-cues", type=int, help="Required when auditing media")
    args = parser.parse_args(argv)
    if args.max_json_bytes <= 0:
        result = error("E_CONFIG_LIMITS_UNVERIFIED",
                       "Batas baca JSON harus integer positif.")
    else:
        try:
            edit = read_json(args.edit, args.max_json_bytes)
            animation = read_json(args.animation, args.max_json_bytes)
            caps = read_json(args.caps, args.max_json_bytes) if args.caps else None
            if caps is not None and type(caps) is not dict:
                raise ValueError("E_CONFIG_LIMITS_UNVERIFIED")
            result = validate_pair(edit, animation, caps=caps)
            if args.media_root is not None:
                if (args.max_media_bytes is None or args.max_srt_cues is None or
                    args.max_media_bytes <= 0 or args.max_srt_cues <= 0):
                    result["issues"].append({
                        "code":"E_CONFIG_LIMITS_UNVERIFIED","severity":"ERROR",
                        "pointer":"/media",
                        "message":"Batas baca media dan cue wajib disediakan oleh pemanggil."})
                elif result["error_count"]:
                    result["issues"].append({
                        "code":"E_MEDIA_AUDIT_SKIPPED","severity":"REVIEW",
                        "pointer":"/media",
                        "message":"Audit media ditunda sampai kontrak JSON bebas error."})
                else:
                    media_report = inspect_media(
                        edit, args.media_root,
                        max_file_bytes=args.max_media_bytes,
                        max_srt_cues=args.max_srt_cues)
                    result["issues"].extend(media_report["issues"])
                    result["media_file_count"] = len(media_report["files"])
                    result["srt_cue_count"] = media_report.get("cue_count",0)
                result["error_count"] = sum(x["severity"]=="ERROR" for x in result["issues"])
                result["review_count"] = sum(x["severity"]=="REVIEW" for x in result["issues"])
                result["status"] = "PREFLIGHT_FAIL" if result["error_count"] else "NEEDS_REVIEW"
                result["can_assemble"] = False
        except (OSError, UnicodeError, ValueError, TypeError, OverflowError) as ex:
            # Never print untrusted file content or absolute paths in reports.
            code = "E_RESOURCE_LIMIT" if str(ex) == "E_RESOURCE_LIMIT" else "E_JSON_SCHEMA"
            result = error(code, "Gagal membaca atau mem-parsing file JSON.")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    # Distinguish invalid and pending manual/host/media review from READY.
    return 2 if result["status"] == "PREFLIGHT_FAIL" else 3


if __name__ == "__main__":
    sys.exit(run())
