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
from .ffprobe import inspect_ffprobe
from .draft_compiler import build_draft, DraftCompileError
from .import_snapshot import prepare_media_snapshot, ImportSnapshotError
from .track_preflight import prepare_track_preflight
from .animation_phases import build_both_phase_candidate, PhasePlanError


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
    parser.add_argument("--ffprobe-exe", type=Path,
                        help="Optional explicitly configured local FFprobe binary")
    parser.add_argument("--include-import-snapshot", action="store_true",
                        help="Audit pinned media import candidate, never import or authorize Premiere")
    parser.add_argument("--max-import-items", type=int,
                        help="Explicit developer limit for item inventory; not production cap")
    parser.add_argument("--include-track-preflight", action="store_true",
                        help="Read-only four-track source preflight (never production READY)")
    parser.add_argument("--candidate-timebase-ticks", type=str,
                        help="Optional UNVERIFIED candidate host ticks, only for offline planning")
    parser.add_argument("--include-animation-phases", action="store_true",
                        help="Draft 21 BOTH IN/HOLD/OUT references; no effect rendering")
    parser.add_argument("--max-animation-instances", type=int,
                        help="Explicit developer cap on visual occurrences")
    parser.add_argument("--include-draft", action="store_true",
                        help="Show deterministic non-executable timeline intent if structurally valid")
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
                    if not any(x["severity"] == "ERROR"
                               for x in media_report["issues"]):
                        probe = inspect_ffprobe(
                            edit, args.media_root, ffprobe_exe=args.ffprobe_exe)
                        result["issues"].extend(probe["issues"])
                        result["ffprobe_stream_count"] = len(probe["streams"])
                    else:
                        result["issues"].append({
                            "code":"E_FFPROBE_SKIPPED","severity":"REVIEW",
                            "pointer":"/ffprobe",
                            "message":"FFprobe menunggu file dan hash media valid."})
                result["error_count"] = sum(x["severity"]=="ERROR" for x in result["issues"])
                result["review_count"] = sum(x["severity"]=="REVIEW" for x in result["issues"])
                result["status"] = "PREFLIGHT_FAIL" if result["error_count"] else "NEEDS_REVIEW"
                result["can_assemble"] = False
            if args.include_import_snapshot:
                if (args.media_root is None or
                    type(args.max_import_items) is not int or
                    args.max_import_items <= 0 or
                    type(args.max_media_bytes) is not int or
                    args.max_media_bytes <= 0):
                    result["issues"].append({
                        "code":"E_CONFIG_LIMITS_UNVERIFIED","severity":"ERROR",
                        "pointer":"/import_snapshot",
                        "message":"Audit impor butuh media root dan batas sumber yang eksplisit."})
                elif result["error_count"]:
                    result["issues"].append({
                        "code":"E_IMPORT_SNAPSHOT_SKIPPED","severity":"REVIEW",
                        "pointer":"/import_snapshot",
                        "message":"Audit impor dilewati sampai seluruh error media/kontrak terselesaikan."})
                else:
                    try:
                        snapshot = prepare_media_snapshot(
                            edit, args.media_root,
                            max_file_bytes=args.max_media_bytes,
                            max_import_items=args.max_import_items)
                        # NEVER return absolute paths, mtimes or full inventory
                        # through the user-facing CEP CLI report.
                        result["import_snapshot"] = {
                            "status": "CANDIDATE_NOT_AUTHORIZED",
                            "can_import": False,
                            "item_count": snapshot["item_count"],
                            "import_count": snapshot["import_count"],
                            "inventory_sha256": snapshot["inventory_sha256"]
                        }
                    except ImportSnapshotError as exc:
                        result["issues"].append({
                            "code":exc.code,"severity":"ERROR",
                            "pointer":"/import_snapshot",
                            "message":"Audit sumber impor gagal; file proyek tidak diubah."})
                result["error_count"] = sum(x["severity"] == "ERROR" for x in result["issues"])
                result["review_count"] = sum(x["severity"] == "REVIEW" for x in result["issues"])
                result["status"] = "PREFLIGHT_FAIL" if result["error_count"] else "NEEDS_REVIEW"
                result["can_assemble"] = False
            if args.include_track_preflight:
                if (args.media_root is None or args.max_media_bytes is None or
                    args.max_srt_cues is None or args.max_import_items is None):
                    result["issues"].append({
                        "code":"E_CONFIG_LIMITS_UNVERIFIED", "severity":"ERROR",
                        "pointer":"/four_track_preflight",
                        "message":"Preflight 4-track butuh folder media dan batas yang eksplisit."})
                elif result["error_count"]:
                    result["issues"].append({
                        "code":"E_TRACK_PREFLIGHT_SKIPPED", "severity":"REVIEW",
                        "pointer":"/four_track_preflight",
                        "message":"Audit empat track menunggu JSON dan file media bebas kesalahan."})
                else:
                    report = prepare_track_preflight(
                        edit, animation, args.media_root,
                        ffprobe_exe=args.ffprobe_exe,
                        ticks_per_frame=args.candidate_timebase_ticks,
                        max_media_bytes=args.max_media_bytes,
                        max_srt_cues=args.max_srt_cues,
                        max_import_items=args.max_import_items
                    )
                    for item in report["issues"]:
                        result["issues"].append({
                            "code":item["code"], "severity":item["severity"],
                            "pointer":"/four_track_preflight/"+item["stage"],
                            "message":"Preflight offline empat track; tidak mengizinkan mutasi Premiere."})
                    if report["track_candidate"] is not None:
                        result["track_candidate"] = report["track_candidate"]
                result["error_count"] = sum(x["severity"]=="ERROR" for x in result["issues"])
                result["review_count"] = sum(x["severity"]=="REVIEW" for x in result["issues"])
                result["status"] = "PREFLIGHT_FAIL" if result["error_count"] else "NEEDS_REVIEW"
                result["can_assemble"] = False
            if args.include_animation_phases:
                if (type(args.max_animation_instances) is not int or
                        args.max_animation_instances <= 0):
                    result["issues"].append({
                        "code":"E_FX_RESOURCE_LIMIT_UNVERIFIED","severity":"ERROR",
                        "pointer":"/animation_phases",
                        "message":"Batas jumlah animasi developer harus integer positif."})
                elif result["error_count"]:
                    result["issues"].append({
                        "code":"E_FX_PHASES_SKIPPED","severity":"REVIEW",
                        "pointer":"/animation_phases",
                        "message":"Animasi menunggu kontrak JSON dan sumber bebas error."})
                else:
                    try:
                        planned=build_both_phase_candidate(
                            edit,animation,max_instances=args.max_animation_instances)
                        # Never forward per-image detailed effects or source paths
                        # through user-facing CEP without a versioned review.
                        result["animation_phases"] = {
                            "status":"REFERENCE_SCHEDULE_ONLY",
                            "can_render":False,"can_assemble":False,
                            "instance_count":planned["instance_count"],
                            "zero_hold_count":sum(
                                x["zero_hold_needs_visual_review"]
                                for x in planned["entries"]),
                            "operation_sha256":planned["operation_sha256"]
                        }
                        result["issues"].append({
                            "code":"E_FX_BACKEND_UNVERIFIED","severity":"REVIEW",
                            "pointer":"/animation_phases",
                            "message":"21 preset baru jadwal frame; native/FFmpeg belum tersedia."})
                    except PhasePlanError as exc:
                        result["issues"].append({
                            "code":exc.code,"severity":"ERROR",
                            "pointer":"/animation_phases",
                            "message":"Jadwal BOTH tidak dapat dibentuk dari durasi/preset."})
                result["error_count"] = sum(x["severity"]=="ERROR" for x in result["issues"])
                result["review_count"] = sum(x["severity"]=="REVIEW" for x in result["issues"])
                result["status"] = "PREFLIGHT_FAIL" if result["error_count"] else "NEEDS_REVIEW"
                result["can_assemble"] = False
            if args.include_draft and result["error_count"] == 0:
                try:
                    draft = build_draft(edit, animation)
                    result["draft"] = {
                        "status": "DRAFT_NOT_EXECUTABLE", "can_assemble": False,
                        "scene_count": draft["scene_count"],
                        "asset_instance_count": draft["asset_instance_count"],
                        "total_frames": draft["total_frames"],
                        "operation_digest_sha256": draft["operation_digest_sha256"]
                    }
                except DraftCompileError:
                    # Missing creative policy/uncertain timing still blocks draft.
                    result["draft_status"] = "BLOCKED_CONTRACT_REVIEW"
        except (OSError, UnicodeError, ValueError, TypeError, OverflowError) as ex:
            # Never print untrusted file content or absolute paths in reports.
            code = "E_RESOURCE_LIMIT" if str(ex) == "E_RESOURCE_LIMIT" else "E_JSON_SCHEMA"
            result = error(code, "Gagal membaca atau mem-parsing file JSON.")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    # Distinguish invalid and pending manual/host/media review from READY.
    return 2 if result["status"] == "PREFLIGHT_FAIL" else 3


if __name__ == "__main__":
    sys.exit(run())
