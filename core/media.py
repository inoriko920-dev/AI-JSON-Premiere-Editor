"""Read-only local media and SRT audit for STEP04.

No automatic downloads, no media writes, no FFmpeg launch or Premiere mutation.
An acceptable signature/hash is NOT proof of audio/video decode compatibility.
All paths must stay inside explicit project media root, including symlinks.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path, PureWindowsPath
from typing import Any


SRT_TIMECODE = re.compile(
    r"^(\d{2,}):([0-5]\d):([0-5]\d),(\d{3})\s*-->\s*"
    r"(\d{2,}):([0-5]\d):([0-5]\d),(\d{3})(?:\s+.*)?$"
)
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def issue(code: str, pointer: str, message: str, severity="ERROR") -> dict[str,str]:
    return {"code": code, "pointer": pointer,
            "message": message, "severity": severity}


def resolved_path(root: Path, relative: str) -> Path:
    """Resolve and verify confinement, even if the final file is a symlink."""
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ValueError("E_MEDIA_PATH")
    windows = PureWindowsPath(relative)
    if windows.drive or windows.root or relative.startswith(("/", "\\")):
        raise ValueError("E_MEDIA_PATH")
    posix = relative.replace("\\", "/")
    parts = posix.split("/")
    if any(p in ("..", "", ".") for p in parts):
        raise ValueError("E_MEDIA_PATH")
    canonical = root.resolve(strict=True)
    if not canonical.is_dir():
        raise ValueError("E_MEDIA_PATH")
    result = canonical.joinpath(*parts).resolve(strict=True)
    if not result.is_relative_to(canonical) or not result.is_file():
        raise ValueError("E_MEDIA_PATH")
    return result


def _bounded_hash(path: Path, max_bytes: int) -> tuple[str, int, bytes]:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise ValueError("E_CONFIG_LIMITS_UNVERIFIED")
    if path.stat().st_size > max_bytes:
        raise ValueError("E_RESOURCE_LIMIT")
    hasher = hashlib.sha256()
    total = 0
    first = b""
    with path.open("rb") as f:
        while True:
            data = f.read(1024*1024)
            if not data:
                break
            total += len(data)
            if total > max_bytes:
                raise ValueError("E_RESOURCE_LIMIT")
            if not first:
                first = data[:32]
            hasher.update(data)
    return hasher.hexdigest(), total, first


def _milliseconds(groups: tuple[str,...]) -> int:
    hours, minutes, seconds, fraction = map(int, groups)
    return (((hours*60)+minutes)*60+seconds)*1000+fraction


def parse_srt(raw: bytes, *, max_cues: int) -> list[dict[str, Any]]:
    """No word timing is inferred. Cue text stays local, not included in report."""
    if not isinstance(max_cues, int) or isinstance(max_cues, bool) or max_cues <= 0:
        raise ValueError("E_CONFIG_LIMITS_UNVERIFIED")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError("E_SRT_MALFORMED") from e
    normalized = text.replace("\r\n","\n").replace("\r","\n").strip()
    if not normalized:
        raise ValueError("E_SRT_MALFORMED")
    blocks = re.split(r"\n[ \t]*\n", normalized)
    if len(blocks) > max_cues:
        raise ValueError("E_RESOURCE_LIMIT")
    cues = []
    used = set()
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            raise ValueError("E_SRT_MALFORMED")
        index = lines[0].strip()
        if not index.isdecimal():
            raise ValueError("E_SRT_MALFORMED")
        cue_id = int(index)
        match = SRT_TIMECODE.fullmatch(lines[1].strip())
        if cue_id in used or match is None or not any(x.strip() for x in lines[2:]):
            raise ValueError("E_SRT_MALFORMED")
        first, last = match.groups()[:4], match.groups()[4:8]
        start, end = _milliseconds(first), _milliseconds(last)
        if end <= start:
            raise ValueError("E_SRT_MALFORMED")
        used.add(cue_id)
        cues.append({"cue_id": cue_id, "start_ms": start, "end_ms": end})
    return cues


def _format_supported(name: str, first: bytes) -> tuple[bool, dict | None]:
    """Cheap structural sniff, deliberately NOT a decoder/alpha quality test."""
    low = name.lower()
    if low.endswith(".png"):
        if not first.startswith(PNG_SIG) or len(first) < 24 or first[12:16] != b"IHDR":
            return False,None
        w,h=struct.unpack(">II",first[16:24])
        return w>0 and h>0,{"width":w,"height":h}
    if low.endswith(".wav"):
        return first[:4] in (b"RIFF",b"RF64") and first[8:12] == b"WAVE",None
    if low.endswith(".mp3"):
        return first.startswith(b"ID3") or (
            len(first)>=2 and first[0] == 0xFF and first[1] & 0xE0 == 0xE0
        ),None
    if low.endswith(".mp4"):
        return len(first)>=12 and first[4:8] == b"ftyp",None
    if low.endswith(".srt"):
        return True,None
    return False,None


def inspect_media(edit: dict, root: Path, *, max_file_bytes: int,
                  max_srt_cues: int) -> dict[str, Any]:
    """Perform actual path, hash, magic and cue-reference checks.

    All resource budgets are explicit caller-provided development limits,
    NOT certified production caps. Return NEEDS_REVIEW even for all-good files.
    """
    errors: list[dict[str, str]] = []
    inventory: list[dict[str, Any]] = []
    try:
        root = Path(root).resolve(strict=True)
        if not root.is_dir() or type(max_file_bytes) is not int or max_file_bytes<=0 or (
            type(max_srt_cues) is not int or max_srt_cues<=0
        ):
            raise ValueError("E_CONFIG_LIMITS_UNVERIFIED")
    except (ValueError,OSError):
        return {"status":"PREFLIGHT_FAIL","can_assemble":False,"files":[],
                "issues":[issue("E_CONFIG_LIMITS_UNVERIFIED","/media",
                                "Media root atau batas pemeriksaan tidak valid.")]}
    queue: list[tuple[str,str,dict[str,Any]]] = []
    sources = edit.get("sources",{}) if type(edit) is dict else {}
    for key in ("srt","audio","background"):
        doc=sources.get(key,{}) if type(sources) is dict else {}
        if type(doc) is dict:
            queue.append((f"/sources/{key}", key, doc))
    for aid, doc in (edit.get("assets",{}) if type(edit) is dict and type(edit.get("assets")) is dict else {}).items():
        if type(doc) is dict:
            queue.append((f"/assets/{aid}", "asset",doc))
    cue_ids: set[int] = set()
    for pointer,category,record in queue:
        rel=record.get("path")
        if not isinstance(rel,str):
            errors.append(issue("E_MEDIA_MISSING",pointer,"Media wajib tidak memiliki path."))
            continue
        try:
            path=resolved_path(root,rel)
            digest,count,first=_bounded_hash(path,max_file_bytes)
            good,meta=_format_supported(rel,first)
            if not good:
                errors.append(issue("E_MEDIA_FORMAT",pointer,
                                    "Format header media tidak sesuai ekstensi."))
            expected=record.get("sha256")
            if isinstance(expected,str):
                if not re.fullmatch(r"[a-fA-F0-9]{64}",expected) or digest.lower()!=expected.lower():
                    errors.append(issue("E_MEDIA_HASH",pointer,
                                        "Hash media nyata tidak cocok dengan deklarasi."))
            else:
                errors.append(issue("E_MEDIA_HASH_UNPINNED",pointer,
                                    "Hash asli belum disertakan dalam JSON.","REVIEW"))
            if category=="srt" and good:
                try:
                    if count>max_file_bytes:
                        raise ValueError("E_RESOURCE_LIMIT")
                    cues=parse_srt(path.read_bytes(),max_cues=max_srt_cues)
                    cue_ids={c["cue_id"] for c in cues}
                except (ValueError,UnicodeError):
                    errors.append(issue("E_SRT_MALFORMED",pointer,
                                        "Cue SRT tidak dapat diverifikasi."))
            item={"pointer":pointer,"bytes":count,"sha256":digest,"header_ok":good}
            if meta:
                item.update(meta)
            inventory.append(item)
        except (OSError,ValueError,RuntimeError) as e:
            code=str(e) if str(e) in ("E_RESOURCE_LIMIT","E_MEDIA_PATH",
                                       "E_CONFIG_LIMITS_UNVERIFIED") else "E_MEDIA_MISSING"
            errors.append(issue(code,pointer,
                                "File wajib hilang, tidak dapat dibaca, di luar root, atau terlalu besar."))
    for i,scene in enumerate(edit.get("scenes",[]) if type(edit) is dict and isinstance(edit.get("scenes"),list) else []):
        if not isinstance(scene,dict):
            continue
        for j,ins in enumerate(scene.get("assets",[]) if isinstance(scene.get("assets"),list) else []):
            if not isinstance(ins,dict):
                continue
            evidence=ins.get("entry_evidence",{})
            if not isinstance(evidence,dict) or evidence.get("accuracy") != "EXACT_CUE":
                continue
            if evidence.get("cue_id") not in cue_ids:
                errors.append(issue("E_SRT_AMBIGUOUS",f"/scenes/{i}/assets/{j}/entry_evidence",
                                    "cue_id tidak ditemukan dalam SRT yang dibaca."))
    errors.append(issue("E_MEDIA_DECODE_UNVERIFIED","/media",
                        "Header PNG/audio/MP4 bukan bukti FFprobe, decode dan alpha Premiere.",
                        "REVIEW"))
    errors.append(issue("E_HOST_UNVERIFIED","/host",
                        "Host Premiere dan seluruh efek masih memerlukan uji akhir.",
                        "REVIEW"))
    status="PREFLIGHT_FAIL" if any(e["severity"]=="ERROR" for e in errors) else "NEEDS_REVIEW"
    return {"status":status,"can_assemble":False,"files":inventory,"issues":errors,
            "cue_count":len(cue_ids)}
