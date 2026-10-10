"""Bounded, read-only FFprobe stream/duration inspection.

FFprobe must be an explicitly configured executable, never taken from either
JSON file. This is media metadata only, NOT full decode or Premiere proof.
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import subprocess
from typing import Any, Callable

from .media import resolved_path, issue


MAX_STDOUT = 128 * 1024
MAX_SECONDS = 12
# Representation bound, not a permitted project-length policy: safely convert
# FFprobe seconds to signed 64-bit milliseconds without giant-decimal overflow.
MAX_DURATION_SECONDS = Decimal(2**63 - 1) / Decimal(1000)
AUDIO_CODECS = {"mp3", "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le",
                "pcm_f64le", "pcm_u8", "pcm_s8"}
VIDEO_CODECS_PREVIEW = {"h264", "hevc"}


def _duration(value: Any) -> Decimal | None:
    if not isinstance(value, (str, int, float)):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    # A finite but astronomical exponent can overflow Decimal arithmetic or
    # throw while converting the duration to int milliseconds downstream.
    return (number if number.is_finite() and
            0 < number <= MAX_DURATION_SECONDS else None)


def _exact_duration_milliseconds(value: Decimal) -> tuple[int, bool]:
    """Convert a positive bounded FFprobe duration without context rounding.

    Decimal multiplication uses the current 28-digit precision by default:
    11.00000000000000000000000000001 * 1000 wrongly becomes 11000.
    Work directly from the coefficient and base-10 exponent so a sub-ms
    narration tail stays detectable and background milliseconds floor safely.
    The maximum accepted seconds bounds the integer prefix to 19 digits.
    """
    parts = value.as_tuple()
    exponent = parts.exponent + 3
    digits = parts.digits
    if exponent >= 0:
        return int("".join(map(str, digits))) * (10 ** exponent), True
    integer_length = len(digits) + exponent
    if integer_length <= 0:
        return 0, False
    milliseconds = int("".join(map(str, digits[:integer_length])))
    has_fraction = any(digits[integer_length:])
    return milliseconds, not has_fraction


def inspect_ffprobe(
    edit: dict[str, Any],
    media_root: Path,
    *,
    ffprobe_exe: Path | None,
    runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    """Inspect narration audio and background video, fail closed.

    Missing optional executable remains REVIEW, never a false PASS. Real subprocess
    failures become ERROR. Full actual decoding and host compatibility remain pending.
    """
    issues: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    if ffprobe_exe is None:
        return {
            "status": "NEEDS_REVIEW", "can_assemble": False, "streams": [],
            "issues": [issue("E_FFPROBE_UNAVAILABLE", "/ffprobe",
                             "FFprobe belum disediakan oleh pengguna/paket.", "REVIEW")]
        }
    try:
        binary = Path(ffprobe_exe)
        if (not binary.is_absolute() or not binary.is_file() or binary.is_symlink()
                or binary.name.lower() not in ("ffprobe", "ffprobe.exe")):
            raise ValueError("untrusted binary path")
    except (OSError, ValueError, TypeError):
        return {
            "status": "PREFLIGHT_FAIL", "can_assemble": False, "streams": [],
            "issues": [issue("E_FFPROBE_PATH", "/ffprobe",
                             "FFprobe executable absolut dan terpercaya wajib ada.")]
        }
    for source, media_kind in (("audio", "audio"), ("background", "video")):
        pointer = f"/sources/{source}"
        try:
            rel = edit["sources"][source]["path"]
            path = resolved_path(Path(media_root), rel)
        except (KeyError, TypeError, OSError, ValueError):
            issues.append(issue("E_MEDIA_MISSING", pointer,
                                "File input wajib tidak tersedia untuk pemeriksaan stream."))
            continue
        args = [
            str(binary), "-v", "error", "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,"
            "sample_rate,channels,duration", "-of", "json", str(path)
        ]
        try:
            proc = runner(args, shell=False, capture_output=True,
                          timeout=MAX_SECONDS, check=False)
        except subprocess.TimeoutExpired:
            issues.append(issue("E_FFPROBE_TIMEOUT", pointer, "Pemeriksaan media melewati timeout."))
            continue
        except (OSError, ValueError, subprocess.SubprocessError):
            issues.append(issue("E_FFPROBE_EXEC_FAILED", pointer,
                                "FFprobe tidak dapat menjalankan pemeriksaan."))
            continue
        output = proc.stdout
        if (proc.returncode != 0 or not isinstance(output, bytes)
                or len(output) > MAX_STDOUT):
            issues.append(issue("E_FFPROBE_BAD_RESPONSE", pointer,
                                "Hasil FFprobe gagal, tidak terbaca, atau terlalu besar."))
            continue
        try:
            data = json.loads(output, parse_constant=lambda name: (_ for _ in ()).throw(
                ValueError("nonfinite numeric constant")))
        except (UnicodeError, ValueError, TypeError, RecursionError):
            issues.append(issue("E_FFPROBE_BAD_RESPONSE", pointer,
                                "FFprobe mengembalikan JSON rusak."))
            continue
        if not isinstance(data, dict) or not isinstance(data.get("streams"), list):
            issues.append(issue("E_FFPROBE_BAD_RESPONSE", pointer,
                                "Informasi stream tidak tersedia."))
            continue
        if source == "background":
            # The JSON audio_policy=MUTE is only intent, NOT actual proof.
            # A background MP4 with linked audio (or an unfamiliar stream)
            # cannot be placed safely using the current Premiere adapter.
            topology = data["streams"]
            if any(type(s) is not dict or s.get("codec_type") not in
                   ("video", "audio") for s in topology):
                issues.append(issue("E_BACKGROUND_STREAM_TOPOLOGY_UNKNOWN", pointer,
                                    "Background has unsupported or unknown media streams."))
                continue
            if any(s["codec_type"] == "audio" for s in topology):
                issues.append(issue("E_BACKGROUND_AUDIO_NOT_ISOLATED", pointer,
                                    "Background audio must be removed from a verified copy before timeline placement."))
                continue
            video_tracks = sum(s["codec_type"] == "video" for s in topology)
            if video_tracks == 0:
                issues.append(issue("E_FFPROBE_STREAM_MISSING", pointer,
                                    "Required background video stream is missing."))
                continue
            if video_tracks != 1:
                issues.append(issue("E_BACKGROUND_VIDEO_STREAM_AMBIGUOUS", pointer,
                                    "Background must contain exactly one selected video stream."))
                continue
        tracks = [s for s in data["streams"] if isinstance(s, dict)
                  and s.get("codec_type") == media_kind]
        if not tracks:
            issues.append(issue("E_FFPROBE_STREAM_MISSING", pointer,
                                "Stream wajib tidak ditemukan."))
            continue
        # Never silently pick the first of several narration audio streams:
        # Premiere selection is not established by metadata order.
        if source == "audio" and len(tracks) != 1:
            issues.append(issue("E_AUDIO_STREAM_AMBIGUOUS", pointer,
                                "File narasi memiliki beberapa audio stream; pilihan sumber belum terverifikasi."))
            continue
        stream = tracks[0]
        codec = stream.get("codec_name")
        if not isinstance(codec, str) or not codec or len(codec) > 50:
            issues.append(issue("E_FFPROBE_BAD_RESPONSE", pointer, "Nama codec invalid."))
            continue
        if source == "audio" and codec not in AUDIO_CODECS:
            issues.append(issue("E_AUDIO_CODEC_REVIEW", pointer,
                                "Codec narasi membutuhkan kebijakan decoder.", "REVIEW"))
        if source == "background" and codec not in VIDEO_CODECS_PREVIEW:
            issues.append(issue("E_VIDEO_CODEC_REVIEW", pointer,
                                "Codec background belum dikalibrasi untuk Premiere.", "REVIEW"))
        if source == "background":
            width, height = stream.get("width"), stream.get("height")
            if (type(width) is not int or type(height) is not int
                    or width < 1 or height < 1 or width > 16384 or height > 16384):
                issues.append(issue("E_FFPROBE_DIMENSIONS", pointer,
                                    "Dimensi video tidak valid atau melampaui batas inspeksi."))
                continue
        else:
            sample_rate = stream.get("sample_rate")
            if (type(sample_rate) is not str or
                    not 1 <= len(sample_rate) <= 6 or
                    not sample_rate.isascii() or not sample_rate.isdecimal()
                    or not 1 <= int(sample_rate) <= 384000):
                issues.append(issue("E_FFPROBE_SAMPLE_RATE", pointer,
                                    "Sample rate audio tidak valid."))
                continue
        format_data = data.get("format")
        duration = (_duration(format_data.get("duration"))
                    if isinstance(format_data, dict) else None)
        if duration is None:
            duration = _duration(stream.get("duration"))
        duration_ms = None
        if duration is None:
            issues.append(issue("E_FFPROBE_DURATION_UNVERIFIED", pointer,
                                "Durasi aktual tidak ditemukan.", "REVIEW"))
        else:
            duration_ms, exact_millisecond = _exact_duration_milliseconds(duration)
            # Never round away even a tiny narration tail. Background video
            # remains conservatively floored to fully available milliseconds.
            if source == "audio" and not exact_millisecond:
                issues.append(issue("E_FFPROBE_DURATION_PRECISION_UNVERIFIED", pointer,
                                    "Durasi narasi memiliki pecahan milidetik tanpa kebijakan potong terverifikasi."))
                continue
        records.append({
            "pointer": pointer, "stream_kind": media_kind,
            "codec": codec,
            "duration_ms": duration_ms,
            **({"width": stream["width"], "height": stream["height"]}
               if source == "background" else
               {"sample_rate": int(stream["sample_rate"])})
        })
    status = ("PREFLIGHT_FAIL" if any(x["severity"] == "ERROR" for x in issues)
              else "NEEDS_REVIEW")
    issues.append(issue("E_DECODE_PREMIERE_UNVERIFIED", "/media",
                        "FFprobe metadata bukan bukti decode penuh, alpha, atau Premiere.",
                        "REVIEW"))
    return {"status": status, "can_assemble": False, "streams": records, "issues": issues}
