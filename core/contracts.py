"""Fail-closed STRUCTURAL checker for EDIT_PLAN v2 and ANIMATION_PLAN v1.

This is *not* a Premiere/FX capability check, media preflight or READY gate.
Unknown nested keys are reported for review; unknown roots reject the pair.
See ADR-002. Preserve user source files, never mutate Premiere.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REGISTRY_FILE = Path(__file__).with_name("direction_registry.json")
EDIT_ROOT = {"schema_version", "project_id", "revision", "canvas", "sources",
             "profiles", "assets", "scenes", "render", "validation", "provenance"}
ANIM_ROOT = {"schema_version", "project_id", "edit_plan_revision", "revision",
             "mode", "animation_profile", "project_seed", "decisions", "provenance"}
DISALLOWED_SPLIT = {"enter_effect", "exit_effect", "enter_direction",
                    "exit_direction", "in_ms", "out_ms"}
DISALLOWED_SCENE_ANIM = DISALLOWED_SPLIT | {
    "enter", "exit", "preset", "speed", "direction", "duration_frames"}
DISALLOWED_DECISION = DISALLOWED_SPLIT | {
    "duration_frames", "start_frame", "end_frame", "layout", "path"}
DISALLOWED_ANIM_ROOT = {"layout", "scenes", "assets", "audio_path", "background_path"}
SPEEDS = {"SLOW", "MEDIUM", "FAST"}
HEX64 = re.compile(r"^[a-fA-F0-9]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
EVIDENCE_ACCURACY = {"EXACT_CUE", "EXACT_WORD", "APPROX_REVIEW",
                     "ESTIMATED_FROM_AUDIO", "UNRESOLVED"}


class DuplicateObjectKey(ValueError):
    """A duplicate key cannot be silently accepted as JSON last-write-wins."""


def _pairs_unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise DuplicateObjectKey(f"Duplicate object key: {name!r}")
        result[name] = value
    return result


def loads_strict(raw: str | bytes) -> Any:
    """Parse JSON without NaN/Infinity/duplicate object keys."""
    def invalid_float(name: str) -> None:
        raise ValueError(f"Invalid JSON constant: {name}")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", errors="strict")
    if not isinstance(raw, str):
        raise TypeError("JSON input must be UTF-8 text or bytes")
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    try:
        return json.loads(raw, object_pairs_hook=_pairs_unique,
                          parse_constant=invalid_float)
    except RecursionError as exc:
        # Deliberately do not raise global recursion limits for untrusted JSON.
        raise ValueError("E_JSON_NESTING_LIMIT") from exc


def _is_int(v: Any, minimum: int = 0) -> bool:
    return type(v) is int and v >= minimum


def _is_name(v: Any) -> bool:
    return isinstance(v, str) and bool(ID.fullmatch(v))


def _is_string(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _issue(issues: list[dict[str, str]], code: str,
           pointer: str, message: str, severity: str = "ERROR") -> None:
    issues.append({"code": code, "pointer": pointer,
                   "severity": severity, "message": message})


def _object(value: Any, issues: list[dict[str, str]], pointer: str) -> dict:
    if type(value) is not dict:
        _issue(issues, "E_JSON_SCHEMA", pointer, "Objek JSON wajib ada.")
        return {}
    return value


def _known(obj: dict, allowed: set[str], issues: list[dict[str, str]],
           pointer: str, *, nested: bool = True,
           forbidden: set[str] = frozenset()) -> None:
    for key in sorted(obj):
        if key in forbidden:
            _issue(issues, "E_ANIM_MODE", f"{pointer}/{key}",
                   "Field animasi IN/OUT atau animasi silang dokumen dilarang.")
        elif key not in allowed:
            _issue(issues, "E_JSON_SCHEMA" if not nested else "E_NESTED_UNKNOWN",
                   f"{pointer}/{key}",
                   "Field tidak ada dalam kontrak yang dibekukan.",
                   "ERROR" if not nested else "REVIEW")


def _required(obj: dict, fields: set[str], issues: list[dict[str, str]], pointer: str):
    for name in sorted(fields - obj.keys()):
        _issue(issues, "E_JSON_SCHEMA", f"{pointer}/{name}", "Field wajib tidak tersedia.")


def _check_basic(edit: dict, anim: dict, issues: list[dict[str, str]]) -> None:
    _known(edit, EDIT_ROOT, issues, "/EDIT_PLAN", nested=False,
           forbidden=DISALLOWED_SCENE_ANIM)
    _required(edit, EDIT_ROOT, issues, "/EDIT_PLAN")
    _known(anim, ANIM_ROOT, issues, "/ANIMATION_PLAN", nested=False,
           forbidden=DISALLOWED_SPLIT | DISALLOWED_ANIM_ROOT)
    _required(anim, ANIM_ROOT, issues, "/ANIMATION_PLAN")
    if edit.get("schema_version") != "edit-plan-v2":
        _issue(issues, "E_JSON_SCHEMA", "/EDIT_PLAN/schema_version", "Wajib edit-plan-v2.")
    if anim.get("schema_version") != "animation-plan-v1":
        _issue(issues, "E_JSON_SCHEMA", "/ANIMATION_PLAN/schema_version",
               "Wajib animation-plan-v1.")
    if not _is_name(edit.get("project_id")) or not _is_name(anim.get("project_id")):
        _issue(issues, "E_JSON_SCHEMA", "/project_id", "Identitas proyek tidak valid.")
    if not _is_int(edit.get("revision")) or not _is_int(anim.get("revision")) or (
        not _is_int(anim.get("edit_plan_revision"))
    ):
        _issue(issues, "E_JSON_SCHEMA", "/revision", "Revision wajib bilangan bulat nonnegatif.")
    if edit.get("project_id") != anim.get("project_id") or (
        edit.get("revision") != anim.get("edit_plan_revision")
    ):
        _issue(issues, "E_PLAN_PAIR", "/ANIMATION_PLAN/edit_plan_revision",
               "project_id / edit_plan_revision kedua JSON tidak cocok.")
    if anim.get("mode") != "BOTH":
        _issue(issues, "E_ANIM_MODE", "/ANIMATION_PLAN/mode",
               "Mode animasi harus BOTH (IN+OUT satu preset).")
    if not _is_int(anim.get("project_seed")):
        _issue(issues, "E_JSON_SCHEMA", "/ANIMATION_PLAN/project_seed",
               "project_seed wajib integer nonnegatif, bukan alasan random ulang.")


def _profile_and_source(edit: dict, anim: dict, issues: list[dict[str, str]]):
    c = _object(edit.get("canvas"), issues, "/EDIT_PLAN/canvas")
    _required(c, {"width", "height", "fps_num", "fps_den"}, issues, "/EDIT_PLAN/canvas")
    _known(c, {"width", "height", "fps_num", "fps_den"}, issues, "/EDIT_PLAN/canvas")
    for key, n in (("width", 1920), ("height", 1080),
                   ("fps_num", 30), ("fps_den", 1)):
        if c.get(key) != n or type(c.get(key)) is not int:
            _issue(issues, "E_PROFILE_010", f"/EDIT_PLAN/canvas/{key}",
                   f"Profil pilot hanya {n} (angka integer).")
    s = _object(edit.get("sources"), issues, "/EDIT_PLAN/sources")
    _required(s, {"srt", "audio", "background"}, issues, "/EDIT_PLAN/sources")
    _known(s, {"srt", "audio", "background"}, issues, "/EDIT_PLAN/sources")
    for kind in ("srt", "audio"):
        path = f"/EDIT_PLAN/sources/{kind}"
        val = _object(s.get(kind), issues, path)
        _required(val, {"path", "sha256"}, issues, path)
        _known(val, {"path", "sha256"}, issues, path)
        if not _is_string(val.get("path")) or not (
            isinstance(val.get("sha256"), str) and HEX64.fullmatch(val["sha256"])
        ):
            _issue(issues, "E_JSON_SCHEMA", path, "Path dan SHA-256 64 hex wajib untuk sumber.")
    bg = _object(s.get("background"), issues, "/EDIT_PLAN/sources/background")
    _required(bg, {"path", "required", "audio_policy"}, issues, "/EDIT_PLAN/sources/background")
    _known(bg, {"path", "required", "audio_policy", "sha256"},
           issues, "/EDIT_PLAN/sources/background")
    if not _is_string(bg.get("path")) or type(bg.get("required")) is not bool:
        _issue(issues, "E_JSON_SCHEMA", "/EDIT_PLAN/sources/background",
               "Path background dan flag required harus valid.")
    if bg.get("required") is not True:
        _issue(issues, "E_MEDIA_MISSING", "/EDIT_PLAN/sources/background/required",
               "Pilot membutuhkan background wajib; tidak membuat placeholder.")
    if bg.get("audio_policy") != "MUTE":
        _issue(issues, "E_NESTED_UNKNOWN", "/EDIT_PLAN/sources/background/audio_policy",
               "Kebijakan audio background selain MUTE perlu review.", "REVIEW")
    if "sha256" in bg and (type(bg["sha256"]) is not str or not HEX64.fullmatch(bg["sha256"])):
        _issue(issues, "E_JSON_SCHEMA", "/EDIT_PLAN/sources/background/sha256",
               "Hash yang dideklarasikan harus 64 hex.")
    profiles = _object(edit.get("profiles"), issues, "/EDIT_PLAN/profiles")
    _required(profiles, {"layout_id", "layout_hash"}, issues, "/EDIT_PLAN/profiles")
    _known(profiles, {"layout_id", "layout_hash"}, issues, "/EDIT_PLAN/profiles")
    if not _is_string(profiles.get("layout_id")) or not (
        isinstance(profiles.get("layout_hash"), str)
        and HEX64.fullmatch(profiles["layout_hash"])
    ):
        _issue(issues, "E_JSON_SCHEMA", "/EDIT_PLAN/profiles",
               "Profil layout harus memiliki ID dan hash valid.")
    ap = _object(anim.get("animation_profile"), issues, "/ANIMATION_PLAN/animation_profile")
    _required(ap, {"id", "sha256"}, issues, "/ANIMATION_PLAN/animation_profile")
    _known(ap, {"id", "sha256"}, issues, "/ANIMATION_PLAN/animation_profile")
    if not _is_string(ap.get("id")) or not (
        isinstance(ap.get("sha256"), str) and HEX64.fullmatch(ap["sha256"])
    ):
        _issue(issues, "E_JSON_SCHEMA", "/ANIMATION_PLAN/animation_profile",
               "Profil animasi harus memiliki ID dan hash valid.")
    return c


def _structure_and_pairs(edit: dict, anim: dict, issues: list[dict[str, str]]):
    assets = _object(edit.get("assets"), issues, "/EDIT_PLAN/assets")
    if not assets:
        _issue(issues, "E_JSON_SCHEMA", "/EDIT_PLAN/assets", "Peta asset tidak boleh kosong.")
    for aid, props in assets.items():
        p = f"/EDIT_PLAN/assets/{aid}"
        if not _is_name(aid):
            _issue(issues, "E_JSON_SCHEMA", p, "asset_id tidak valid.")
        d = _object(props, issues, p)
        _required(d, {"path"}, issues, p)
        _known(d, {"path", "sha256", "alpha", "width", "height", "provenance"}, issues, p)
        if not _is_string(d.get("path")):
            _issue(issues, "E_JSON_SCHEMA", f"{p}/path", "Path asset PNG wajib ada.")
        if "sha256" in d and (type(d["sha256"]) is not str or not HEX64.fullmatch(d["sha256"])):
            _issue(issues, "E_JSON_SCHEMA", f"{p}/sha256", "Hash asset tidak valid.")
    scenes = edit.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        _issue(issues, "E_JSON_SCHEMA", "/EDIT_PLAN/scenes", "Scenes harus array tidak kosong.")
        scenes = []
    seen_scenes: set[str] = set()
    instances: set[tuple[str, str]] = set()
    last_end = 0
    for i, raw in enumerate(scenes):
        p = f"/EDIT_PLAN/scenes/{i}"
        scene = _object(raw, issues, p)
        _required(scene, {"scene_id", "source_segment_ids", "narration_quote",
                          "layout_type", "start_frame", "end_frame", "assets",
                          "transition_policy"}, issues, p)
        _known(scene, {"scene_id", "source_segment_ids", "narration_quote", "layout_type",
                       "start_frame", "end_frame", "assets", "transition_policy",
                       "semantic_relation", "locked"}, issues, p,
               forbidden=DISALLOWED_SPLIT)
        # Contract currently supports CUT only. Unknown transitions must
        # never compile as an implicit CUT (nor share its review digest).
        if type(scene.get("transition_policy")) is not str or scene["transition_policy"] != "CUT":
            _issue(issues, "E_JSON_SCHEMA", f"{p}/transition_policy",
                   "Kebijakan transisi tidak didukung; hanya CUT yang disetujui.")
        sid = scene.get("scene_id")
        if not _is_name(sid) or sid in seen_scenes:
            _issue(issues, "E_PLAN_PAIR", f"{p}/scene_id",
                   "scene_id kosong, tidak valid, atau duplikat.")
        if _is_name(sid):
            seen_scenes.add(sid)
        if not isinstance(scene.get("source_segment_ids"), list):
            _issue(issues, "E_JSON_SCHEMA", f"{p}/source_segment_ids",
                   "Daftar sumber narasi harus array.")
        if not isinstance(scene.get("narration_quote"), str):
            _issue(issues, "E_JSON_SCHEMA", f"{p}/narration_quote",
                   "Kutipan narasi harus teks.")
        if scene.get("layout_type") not in ("SINGLE", "DOUBLE"):
            _issue(issues, "E_JSON_SCHEMA", f"{p}/layout_type",
                   "Hanya SINGLE atau DOUBLE.")
        start, end = scene.get("start_frame"), scene.get("end_frame")
        valid_scene_time = _is_int(start) and _is_int(end) and start < end
        if not valid_scene_time:
            _issue(issues, "E_JSON_SCHEMA", p, "Frame scene harus [start,end) valid.")
        elif start < last_end:
            _issue(issues, "E_JSON_SCHEMA", f"{p}/start_frame",
                   "Scene berurutan tidak boleh overlap tanpa policy tersertifikasi.")
        elif start > last_end:
            _issue(issues, "E_SCENE_GAP_POLICY", f"{p}/start_frame",
                   "Jeda scene memerlukan kebijakan timeline eksplisit.", "REVIEW")
        if valid_scene_time:
            last_end = end
        arr = scene.get("assets")
        if not isinstance(arr, list):
            _issue(issues, "E_JSON_SCHEMA", f"{p}/assets", "Assets scene harus array.")
            continue
        slots: list[str] = []
        local_ids: set[str] = set()
        for j, raw_instance in enumerate(arr):
            q = f"{p}/assets/{j}"
            ins = _object(raw_instance, issues, q)
            _required(ins, {"asset_id", "slot", "start_frame", "end_frame", "entry_evidence"},
                      issues, q)
            _known(ins, {"asset_id", "slot", "start_frame", "end_frame", "entry_evidence",
                         "stagger_frames", "timing_lock"}, issues, q,
                   forbidden=DISALLOWED_SCENE_ANIM)
            aid, slot = ins.get("asset_id"), ins.get("slot")
            if not _is_name(aid) or aid not in assets or aid in local_ids:
                _issue(issues, "E_PLAN_PAIR", f"{q}/asset_id",
                       "asset_id tidak dikenal, kosong, atau duplikat dalam scene.")
            if _is_name(aid):
                local_ids.add(aid)
                if _is_name(sid):
                    instances.add((sid, aid))
            if not isinstance(slot, str):
                _issue(issues, "E_JSON_SCHEMA", f"{q}/slot", "Slot harus string.")
            else:
                slots.append(slot)
            a_start, a_end = ins.get("start_frame"), ins.get("end_frame")
            if not (_is_int(a_start) and _is_int(a_end) and a_start < a_end):
                _issue(issues, "E_JSON_SCHEMA", q, "Frame asset harus [start,end) valid.")
            elif valid_scene_time and (a_start < start or a_end > end):
                _issue(issues, "E_JSON_SCHEMA", q,
                       "Instance asset melampaui batas scene yang disetujui.")
            ev = _object(ins.get("entry_evidence"), issues, f"{q}/entry_evidence")
            _known(ev, {"cue_id", "accuracy", "word_range", "source_span",
                        "occurrence", "confidence"}, issues, f"{q}/entry_evidence")
            accuracy = ev.get("accuracy")
            if not isinstance(accuracy, str) or accuracy not in EVIDENCE_ACCURACY:
                _issue(issues, "E_JSON_SCHEMA", f"{q}/entry_evidence/accuracy",
                       "Label accuracy tidak dikenal.")
            elif accuracy != "EXACT_CUE":
                _issue(issues, "E_SRT_AMBIGUOUS", f"{q}/entry_evidence/accuracy",
                       "Timing belum memiliki bukti cue terverifikasi sesuai profil.", "REVIEW")
            if accuracy == "EXACT_CUE" and not _is_int(ev.get("cue_id"), 1):
                _issue(issues, "E_JSON_SCHEMA", f"{q}/entry_evidence/cue_id",
                       "EXACT_CUE membutuhkan cue_id integer positif.")
        expect = ["SINGLE"] if scene.get("layout_type") == "SINGLE" else (
            ["LEFT", "RIGHT"] if scene.get("layout_type") == "DOUBLE" else []
        )
        if expect and sorted(slots) != sorted(expect):
            _issue(issues, "E_PLAN_PAIR", f"{p}/assets",
                   "SINGLE wajib satu SINGLE; DOUBLE tepat LEFT dan RIGHT.")
    decision_list = anim.get("decisions")
    if not isinstance(decision_list, list):
        _issue(issues, "E_JSON_SCHEMA", "/ANIMATION_PLAN/decisions",
               "decisions wajib array.")
        decision_list = []
    decisions: dict[tuple[str, str], dict] = {}
    with REGISTRY_FILE.open("r", encoding="utf-8") as f:
        registry = json.load(f)["directions"]
    for i, raw in enumerate(decision_list):
        p = f"/ANIMATION_PLAN/decisions/{i}"
        d = _object(raw, issues, p)
        _required(d, {"scene_id", "asset_id", "preset", "speed", "direction", "locked"},
                  issues, p)
        _known(d, {"scene_id", "asset_id", "preset", "speed", "direction", "locked"},
               issues, p, forbidden=DISALLOWED_DECISION)
        sid, aid = d.get("scene_id"), d.get("asset_id")
        if not _is_name(sid) or not _is_name(aid):
            _issue(issues, "E_JSON_SCHEMA", p, "Pasangan decision wajib ID valid.")
            continue
        key = sid, aid
        if key in decisions:
            _issue(issues, "E_PLAN_PAIR", p, "Duplikat animasi untuk pasangan scene/asset.")
        else:
            decisions[key] = d
        preset, speed, direction = d.get("preset"), d.get("speed"), d.get("direction")
        if not isinstance(preset, str) or preset not in registry:
            _issue(issues, "E_ANIM_PRESET", f"{p}/preset", "Preset tidak dikenal.")
        elif direction not in registry[preset]:
            _issue(issues, "E_ANIM_PRESET", f"{p}/direction",
                   "Direction tidak terdaftar untuk preset.")
        if not isinstance(speed, str) or speed not in SPEEDS:
            _issue(issues, "E_ANIM_PRESET", f"{p}/speed",
                   "Speed bukan SLOW/MEDIUM/FAST.")
        elif speed != "MEDIUM":
            _issue(issues, "E_FX_SPEED_UNCALIBRATED", f"{p}/speed",
                   "SLOW/FAST belum dikalibrasi terhadap bukti efek.", "REVIEW")
        if type(d.get("locked")) is not bool:
            _issue(issues, "E_JSON_SCHEMA", f"{p}/locked",
                   "locked wajib boolean JSON asli.")
        elif d["locked"] is False:
            _issue(issues, "E_LOCK_REVIEW", f"{p}/locked",
                   "locked=false tidak boleh diubah diam-diam.", "REVIEW")
    for sid, aid in sorted(instances - decisions.keys()):
        _issue(issues, "E_PLAN_PAIR", "/ANIMATION_PLAN/decisions",
               f"Tidak ada keputusan animasi untuk {sid}/{aid}.")
    for sid, aid in sorted(decisions.keys() - instances):
        _issue(issues, "E_PLAN_PAIR", "/ANIMATION_PLAN/decisions",
               f"Keputusan animasi ekstra untuk {sid}/{aid}.")
    return len(scenes), len(instances)


def validate_pair(edit: Any, anim: Any, *, caps: Mapping[str, Any] | None = None
                  ) -> dict[str, Any]:
    """Validate the *structure* only. Returns no READY or mutation authorization.

    caps = actual approved runtime limits evidence; no unverified numeric
    production caps are invented here. Missing caps always blocks host.
    """
    issues: list[dict[str, str]] = []
    edit_obj = _object(edit, issues, "/EDIT_PLAN")
    anim_obj = _object(anim, issues, "/ANIMATION_PLAN")
    _check_basic(edit_obj, anim_obj, issues)
    _profile_and_source(edit_obj, anim_obj, issues)
    scene_count, instances = _structure_and_pairs(edit_obj, anim_obj, issues)
    for doc, pointer in ((edit_obj, "/EDIT_PLAN"), (anim_obj, "/ANIMATION_PLAN")):
        prov = doc.get("provenance")
        if prov is not None and type(prov) is not dict:
            _issue(issues, "E_JSON_SCHEMA", f"{pointer}/provenance",
                   "provenance harus object audit.")
    for key in ("render", "validation"):
        value = edit_obj.get(key)
        if type(value) is not dict:
            _issue(issues, "E_JSON_SCHEMA", f"/EDIT_PLAN/{key}",
                   "Legacy metadata harus tetap object.")
    _known(_object(edit_obj.get("render"), issues, "/EDIT_PLAN/render"),
           {"codec", "pixel_format", "audio_codec", "audio_policy",
            "subtitles", "output_path"}, issues, "/EDIT_PLAN/render")
    _known(_object(edit_obj.get("validation"), issues, "/EDIT_PLAN/validation"),
           {"status", "issues"}, issues, "/EDIT_PLAN/validation")
    if not isinstance(caps, Mapping) or caps.get("approved") is not True:
        _issue(issues, "E_CONFIG_LIMITS_UNVERIFIED", "/runtime_limits",
               "Batas resource resmi belum disetujui/teruji untuk Windows 11.", "REVIEW")
    else:
        # This only records a cap declaration. Physical source, layout, effect,
        # alpha and host proof remain separate, mandatory blockers.
        required = {"json_bytes", "scenes", "assets", "instances"}
        for key in required:
            if not _is_int(caps.get(key), 1):
                _issue(issues, "E_CONFIG_LIMITS_UNVERIFIED", f"/runtime_limits/{key}",
                       "Batas resource positif belum tersedia.", "REVIEW")
        for key, value in (("scenes", scene_count), ("assets", len(edit_obj.get("assets", {}))
                            if type(edit_obj.get("assets")) is dict else 0),
                           ("instances", instances)):
            if _is_int(caps.get(key), 1) and value > caps[key]:
                _issue(issues, "E_RESOURCE_LIMIT", f"/runtime_limits/{key}",
                       "Input melampaui batas yang disetujui.")
    _issue(issues, "E_MEDIA_UNVERIFIED", "/media",
           "SRT/audio/PNG/background belum dibaca, di-hash, dan diprobe.", "REVIEW")
    _issue(issues, "E_PROFILE_UNVERIFIED", "/profiles",
           "Layout dan registry effect belum dicocokkan dengan file asli.", "REVIEW")
    _issue(issues, "E_HOST_UNVERIFIED", "/host",
           "Premiere Pro 2024 24.x dan backend 21 preset belum diuji.", "REVIEW")
    errors = sum(1 for x in issues if x["severity"] == "ERROR")
    return {"schema_version": "structure-validation-report-v1",
            "status": "PREFLIGHT_FAIL" if errors else "NEEDS_REVIEW",
            "can_assemble": False, "error_count": errors,
            "review_count": len(issues)-errors,
            "scene_count": scene_count, "asset_instance_count": instances,
            "issues": issues}
