"""STEP17: isolated, no-overwrite candidate FFmpeg RGBA cache render worker.

Only FADE/WIPE filters from STEP16. The source is copied + SHA-256 pinned
into a private cache work directory BEFORE FFmpeg reads it; user PNG is
never edited. Candidate MOV is checked by actual FFprobe metadata. This
is NOT Canva equivalence, whole-frame verification or Premiere host approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import stat
import struct
import subprocess
from typing import Any, Callable

from .fx_alpha_backend import compile_filter, build_ffmpeg_command, AlphaBackendError
from .media import resolved_path
from .fx_alpha_verify import verify_alpha_pixels, AlphaPixelError

_SHA = frozenset("0123456789abcdef")
_PNG = b"\x89PNG\r\n\x1a\n"
_MAX_LOG = 4096


class AlphaCacheError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in _SHA for c in value)


def _binary(path: Path, kind: str) -> Path:
    if (not isinstance(path, Path) or not path.is_absolute() or
            path.name.lower() not in (kind, kind + ".exe") or
            path.is_symlink() or not path.is_file()):
        raise AlphaCacheError("E_FX_BINARY_UNVERIFIED")
    return path.resolve(strict=True)


def _root(root: Path) -> Path:
    if (not isinstance(root, Path) or not root.is_absolute() or
            root.is_symlink() or not root.is_dir()):
        raise AlphaCacheError("E_FX_CACHE_ROOT_INVALID")
    return root.resolve(strict=True)


def _safe_png_header(header: bytes, max_pixels: int) -> tuple[int, int]:
    if (len(header) < 33 or header[:8] != _PNG or
            header[12:16] != b"IHDR" or
            header[8:12] != b"\x00\x00\x00\x0d"):
        raise AlphaCacheError("E_FX_PNG_INVALID")
    width, height = struct.unpack(">II", header[16:24])
    bit_depth, color_type = header[24:26]
    # The original PNG must explicitly declare alpha; no invented transparency.
    if (width < 1 or height < 1 or width * height > max_pixels or
            bit_depth not in (8, 16) or color_type not in (4, 6)):
        raise AlphaCacheError("E_FX_PNG_PROFILE_UNVERIFIED")
    return width, height


def _copy_pinned(source: Path, target: Path, expected_sha: str,
                 max_source_bytes: int, max_pixels: int) -> tuple[int, int, int]:
    """Write only an exclusive private snapshot, fail on content/file races."""
    before = source.stat()
    if before.st_size < 33 or before.st_size > max_source_bytes:
        raise AlphaCacheError("E_FX_SOURCE_LIMIT")
    digest = hashlib.sha256()
    count = 0
    header = b""
    # Exclusive file creation prevents accidental writes onto a pre-existing path.
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    with source.open("rb") as inp, os.fdopen(os.open(target, flags, 0o600), "wb") as out:
        while True:
            chunk = inp.read(1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > max_source_bytes:
                raise AlphaCacheError("E_FX_SOURCE_LIMIT")
            if len(header) < 33:
                header = (header + chunk)[:33]
            digest.update(chunk)
            out.write(chunk)
        out.flush()
        os.fsync(out.fileno())
        after_fd = os.fstat(inp.fileno())
    after = source.stat()
    if (count != before.st_size or count != after.st_size or
            before.st_mtime_ns != after.st_mtime_ns or
            before.st_ino != after.st_ino or
            after_fd.st_size != after.st_size or
            after_fd.st_mtime_ns != after.st_mtime_ns):
        raise AlphaCacheError("E_FX_SOURCE_CHANGED")
    if digest.hexdigest() != expected_sha:
        raise AlphaCacheError("E_FX_SOURCE_HASH")
    return (*_safe_png_header(header, max_pixels), count)


def _probe(probe: Path, result: Path, width: int, height: int, frames: int,
           runner: Callable[..., Any], timeout_seconds: int) -> None:
    # Inspect ALL streams. A first-video-only probe could silently accept
    # an extra audio/data/video stream in a tampered published cache entry.
    argv = [str(probe), "-v", "error",
            "-count_frames", "-show_entries",
            "stream=codec_type,codec_name,pix_fmt,width,height,nb_read_frames,r_frame_rate",
            "-of", "json", str(result)]
    try:
        call = runner(argv, shell=False, capture_output=True,
                      timeout=timeout_seconds, check=False)
    except (OSError, subprocess.SubprocessError):
        raise AlphaCacheError("E_FX_PROBE_EXEC_FAILED")
    if (call.returncode != 0 or not isinstance(call.stdout, bytes) or
            len(call.stdout) > 128 * 1024):
        raise AlphaCacheError("E_FX_PROBE_FAILED")
    try:
        info = json.loads(call.stdout)
    except (UnicodeError, ValueError, TypeError):
        raise AlphaCacheError("E_FX_PROBE_FAILED")
    if (type(info) is not dict or type(info.get("streams")) is not list or
            len(info["streams"]) != 1):
        raise AlphaCacheError("E_FX_PROBE_FAILED")
    v = info["streams"][0]
    if (type(v) is not dict or v.get("codec_type") != "video" or
            v.get("codec_name") != "qtrle" or
            v.get("pix_fmt") != "argb" or v.get("width") != width or
            v.get("height") != height or
            v.get("r_frame_rate") != "30/1" or
            v.get("nb_read_frames") != str(frames)):
        raise AlphaCacheError("E_FX_PROBE_MISMATCH")




def _hash_stable_mov(path: Path) -> tuple[str, os.stat_result]:
    """Hash only a stable regular MOV, refusing symlink and inode swapping.

    Used before and after no-overwrite publication. We deliberately keep an
    interrupted/tampered published file for owner reconciliation; the caller
    MUST NOT mark the render successful after any integrity error.
    """
    try:
        original = path.lstat()
        if not stat.S_ISREG(original.st_mode) or original.st_size < 1:
            raise AlphaCacheError("E_FX_CACHE_CHANGED")
        flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        digest = hashlib.sha256()
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or
                    (opened.st_dev, opened.st_ino) !=
                    (original.st_dev, original.st_ino)):
                raise AlphaCacheError("E_FX_CACHE_CHANGED")
            total = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                total += len(chunk)
                digest.update(chunk)
            read_end = os.fstat(stream.fileno())
        after = path.lstat()
    except AlphaCacheError:
        raise
    except OSError as error:
        raise AlphaCacheError("E_FX_CACHE_CHANGED") from error
    before_state = (original.st_dev, original.st_ino, original.st_size,
                    original.st_mtime_ns, original.st_ctime_ns)
    opened_state = (opened.st_dev, opened.st_ino, opened.st_size,
                    opened.st_mtime_ns, opened.st_ctime_ns)
    read_state = (read_end.st_dev, read_end.st_ino, read_end.st_size,
                  read_end.st_mtime_ns, read_end.st_ctime_ns)
    end_state = (after.st_dev, after.st_ino, after.st_size,
                 after.st_mtime_ns, after.st_ctime_ns)
    if (not stat.S_ISREG(after.st_mode) or
            total != original.st_size or
            not (before_state == opened_state == read_state == end_state)):
        raise AlphaCacheError("E_FX_CACHE_CHANGED")
    return digest.hexdigest(), after


def verify_cached_report(
    report: dict[str, Any], *, cache_root: Path, ffprobe_exe: Path,
    max_cached_bytes: int, timeout_seconds: int,
    runner: Callable[..., Any] = subprocess.run
) -> dict[str, Any]:
    """Read-only restart audit for a previously published alpha cache MOV.

    The expected SHA and key must come from a trusted prior render report.
    No stale or tampered file is removed/replaced, and this does not re-prove
    per-pixel alpha, Canva fidelity, or Premiere host compatibility.
    """
    if (type(report) is not dict or
            report.get("schema_version") != "alpha-cache-render-report-v1" or
            report.get("status") !=
                "RENDERED_SAMPLED_ALPHA_VERIFIED_NOT_HOST_CERTIFIED" or
            report.get("alpha_pixels_verified") is not True or
            report.get("can_assemble") is not False or
            report.get("host_verified") is not False or
            report.get("whole_frame_verified") is not False or
            report.get("canva_fidelity_verified") is not False or
            not _is_hash(report.get("cache_key_sha256")) or
            not _is_hash(report.get("output_sha256")) or
            type(report.get("frames")) is not int or
            report["frames"] < 1 or
            type(report.get("size")) is not list or
            len(report["size"]) != 2 or
            any(type(n) is not int or n < 1 for n in report["size"])):
        raise AlphaCacheError("E_FX_CACHE_REPORT_INVALID")
    if (type(max_cached_bytes) is not int or max_cached_bytes < 1 or
            type(timeout_seconds) is not int or timeout_seconds < 1):
        raise AlphaCacheError("E_FX_RESOURCE_LIMIT_UNVERIFIED")
    cache = _root(cache_root)
    ffprobe = _binary(ffprobe_exe, "ffprobe")
    final = cache / ("fx_" + report["cache_key_sha256"] + ".mov")
    try:
        original = final.lstat()
    except FileNotFoundError as error:
        raise AlphaCacheError("E_FX_CACHE_MISSING") from error
    except OSError as error:
        raise AlphaCacheError("E_FX_CACHE_UNSAFE") from error
    if not stat.S_ISREG(original.st_mode):
        raise AlphaCacheError("E_FX_CACHE_UNSAFE")
    if original.st_size < 1 or original.st_size > max_cached_bytes:
        raise AlphaCacheError("E_FX_CACHE_RESOURCE_LIMIT")

    # Refuse symlink substitution and detect file changes during SHA and probe.
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    digest = hashlib.sha256()
    try:
        with os.fdopen(os.open(final, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or
                    (opened.st_dev, opened.st_ino) !=
                    (original.st_dev, original.st_ino)):
                raise AlphaCacheError("E_FX_CACHE_CHANGED")
            total = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                total += len(chunk)
                if total > max_cached_bytes:
                    raise AlphaCacheError("E_FX_CACHE_RESOURCE_LIMIT")
                digest.update(chunk)
            endfd = os.fstat(stream.fileno())
    except AlphaCacheError:
        raise
    except OSError as error:
        raise AlphaCacheError("E_FX_CACHE_UNSAFE") from error
    if total != original.st_size or (
            original.st_size, original.st_mtime_ns, original.st_ctime_ns) != (
            endfd.st_size, endfd.st_mtime_ns, endfd.st_ctime_ns):
        raise AlphaCacheError("E_FX_CACHE_CHANGED")
    if digest.hexdigest() != report["output_sha256"]:
        raise AlphaCacheError("E_FX_CACHE_HASH_MISMATCH")
    _probe(ffprobe, final, *report["size"], report["frames"],
           runner, timeout_seconds)
    try:
        after = final.lstat()
    except OSError as error:
        raise AlphaCacheError("E_FX_CACHE_CHANGED") from error
    if (not stat.S_ISREG(after.st_mode) or
            (after.st_dev, after.st_ino, after.st_size,
             after.st_mtime_ns, after.st_ctime_ns) !=
            (original.st_dev, original.st_ino, original.st_size,
             original.st_mtime_ns, original.st_ctime_ns)):
        raise AlphaCacheError("E_FX_CACHE_CHANGED")
    return {
        "cache_integrity": "SHA256_AND_METADATA_CHECKED",
        "cache_key_sha256": report["cache_key_sha256"],
        "output_sha256": report["output_sha256"],
        "host_verified": False, "can_assemble": False,
        "alpha_pixels_reverified": False,
        "whole_frame_verified": False,
        "canva_fidelity_verified": False
    }

def verify_cache_for_candidate(
    report: dict[str, Any], item: dict[str, Any], *,
    expected_source_sha256: str, expected_source_dimensions: tuple[int, int],
    cache_root: Path, ffprobe_exe: Path, max_cached_bytes: int,
    timeout_seconds: int,
    runner: Callable[..., Any] = subprocess.run
) -> dict[str, Any]:
    """Read-only cache use preflight tied to one approved animation and source.

    STEP20 verified the integrity of the MOV named by a *trusted* report.
    It did not ensure the report belongs to the currently requested source,
    preset/direction or timing. This extra preflight rejects that confusion
    BEFORE launching ffprobe or returning any positive metadata.
    """
    if (not _is_hash(expected_source_sha256) or
            type(expected_source_dimensions) is not tuple or
            len(expected_source_dimensions) != 2 or
            any(type(n) is not int or n < 1 for n in
                expected_source_dimensions)):
        raise AlphaCacheError("E_FX_CACHE_INPUT_UNPINNED")
    try:
        compiled = compile_filter(item)
    except AlphaBackendError as error:
        raise AlphaCacheError(error.code) from error
    if (type(report) is not dict or
            report.get("preset") != compiled["preset"] or
            type(report.get("frames")) is not int or
            report["frames"] != compiled["frames"] or
            report.get("size") != list(expected_source_dimensions) or
            report.get("cache_key_sha256") !=
                _cache_key(compiled, expected_source_sha256)):
        raise AlphaCacheError("E_FX_CACHE_CANDIDATE_MISMATCH")
    audited = verify_cached_report(
        report, cache_root=cache_root, ffprobe_exe=ffprobe_exe,
        max_cached_bytes=max_cached_bytes,
        timeout_seconds=timeout_seconds, runner=runner)
    return {
        **audited,
        "cache_input_binding":
            "DECLARED_SOURCE_SHA_EFFECT_TIMING_AND_SIZE_MATCHED",
        "candidate_preset": compiled["preset"],
        "candidate_direction": compiled["direction"],
        "source_bytes_reverified": False,
        "alpha_pixels_reverified": False,
        "host_verified": False,
        "can_assemble": False,
    }


def _cache_key(compiled: dict[str, Any], source_sha256: str) -> str:
    # One canonical cache-key algorithm for initial render and reuse check.
    material = {
        "version": "fx-alpha-cache-v2-alpha-sampled",
        "source_sha256": source_sha256, "preset": compiled["preset"],
        "direction": compiled["direction"], "frames": compiled["frames"],
        "filtergraph": compiled["filtergraph"], "codec": compiled["codec"],
    }
    return hashlib.sha256(json.dumps(
        material, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()


def render_candidate(
    item: dict[str, Any], *, source_png: Path, media_root: Path,
    cache_root: Path, expected_sha256: str, ffmpeg_exe: Path,
    ffprobe_exe: Path, max_source_bytes: int, max_pixels: int,
    max_frames: int, timeout_seconds: int,
    runner: Callable[..., Any] = subprocess.run
) -> dict[str, Any]:
    """One render attempt; a failed attempt can never replace cached output.

    The cache output is a NEW file; no arbitrary output path comes from JSON.
    The returned metadata does not mean Premiere can import the MOV.
    """
    for number in (max_source_bytes, max_pixels, max_frames, timeout_seconds):
        if type(number) is not int or number < 1:
            raise AlphaCacheError("E_FX_RESOURCE_LIMIT_UNVERIFIED")
    if not _is_hash(expected_sha256):
        raise AlphaCacheError("E_FX_SOURCE_HASH_UNPINNED")
    try:
        compiled = compile_filter(item)
    except AlphaBackendError as error:
        raise AlphaCacheError(error.code) from error
    if compiled["frames"] > max_frames:
        raise AlphaCacheError("E_FX_RESOURCE_LIMIT")
    ffmpeg = _binary(ffmpeg_exe, "ffmpeg")
    ffprobe = _binary(ffprobe_exe, "ffprobe")
    media = _root(media_root)
    cache = _root(cache_root)
    if cache == media or cache in media.parents or media in cache.parents:
        raise AlphaCacheError("E_FX_CACHE_ROOT_COLLISION")
    try:
        source = resolved_path(media, str(source_png))
    except (OSError, TypeError, ValueError, RuntimeError):
        raise AlphaCacheError("E_FX_SOURCE_PATH")
    if source.suffix.lower() != ".png":
        raise AlphaCacheError("E_FX_SOURCE_PATH")

    key = _cache_key(compiled, expected_sha256)
    final = cache / ("fx_" + key + ".mov")
    if final.exists() or final.is_symlink():
        raise AlphaCacheError("E_FX_CACHE_EXISTS_NO_OVERWRITE")
    work = cache / (".fx_work_" + key[:16] + "_" + secrets.token_hex(8))
    try:
        work.mkdir(mode=0o700)
    except OSError as error:
        raise AlphaCacheError("E_FX_CACHE_WORKDIR_FAILED") from error
    try:
        staged = work / "input.png"
        output = work / "derived.mov"
        width, height, _ = _copy_pinned(
            source, staged, expected_sha256, max_source_bytes, max_pixels)
        cmd = build_ffmpeg_command(compiled, ffmpeg, staged, output)
        try:
            call = runner(cmd, shell=False, capture_output=True,
                          timeout=timeout_seconds, check=False)
        except (OSError, subprocess.SubprocessError):
            raise AlphaCacheError("E_FX_RENDER_EXEC_FAILED")
        if call.returncode != 0:
            raise AlphaCacheError("E_FX_RENDER_FAILED")
        if (not output.is_file() or output.is_symlink() or
                output.stat().st_size < 1):
            raise AlphaCacheError("E_FX_RENDER_EMPTY")
        # Pin EXACT candidate bytes/inode before delegating to the two
        # external decoder checks. STEP26 previously pinned only AFTER both:
        # a swapped MOV between probe/pixel readback and initial hash could
        # be published with a valid SHA but without validation of those bytes.
        verified_input_hash, verified_input_stat = _hash_stable_mov(output)
        _probe(ffprobe, output, width, height, compiled["frames"],
               runner, timeout_seconds)
        # Metadata alone is insufficient. Source and output must both decode
        # to expected RGBA alpha pixels before the MOV can enter the cache.
        try:
            alpha = verify_alpha_pixels(
                ffmpeg_exe=ffmpeg, source_png=staged, output_mov=output,
                width=width, height=height, frames=compiled["frames"],
                in_frames=compiled["in_frames"], out_frames=compiled["out_frames"],
                preset=compiled["preset"], direction=compiled["direction"],
                timeout_seconds=timeout_seconds, runner=runner)
        except AlphaPixelError as error:
            raise AlphaCacheError(error.code) from error
        if alpha.get("pixel_alpha_checked") is not True:
            raise AlphaCacheError("E_FX_ALPHA_UNVERIFIED")
        # Hash a stable, regular, non-symlink candidate BEFORE publication.
        # Metadata+alpha checks are not enough if a local process replaces the
        # staged MOV between validation and the no-overwrite hard link.
        original_hash, source_stat = _hash_stable_mov(output)
        if (original_hash != verified_input_hash or
                (source_stat.st_dev, source_stat.st_ino) !=
                (verified_input_stat.st_dev, verified_input_stat.st_ino)):
            raise AlphaCacheError("E_FX_CACHE_CHANGED")
        # Hard link atomically publishes a NEW name only, never replaces cache.
        try:
            os.link(output, final)
        except FileExistsError as error:
            raise AlphaCacheError("E_FX_CACHE_EXISTS_NO_OVERWRITE") from error
        except OSError as error:
            raise AlphaCacheError("E_FX_CACHE_COMMIT_FAILED") from error
        # SHA on the final path detects mutation between the first digest
        # and publication. Any mismatch FAILS CLOSED and preserves the file
        # for manual reconciliation instead of deleting linked/user data.
        published_hash, published_stat = _hash_stable_mov(final)
        if (published_hash != original_hash or
                (published_stat.st_dev, published_stat.st_ino) !=
                (source_stat.st_dev, source_stat.st_ino)):
            raise AlphaCacheError("E_FX_CACHE_CHANGED")
        return {
            "schema_version": "alpha-cache-render-report-v1",
            "status": "RENDERED_SAMPLED_ALPHA_VERIFIED_NOT_HOST_CERTIFIED",
            "preset": compiled["preset"], "frames": compiled["frames"],
            "size": [width, height], "cache_key_sha256": key,
            "output_sha256": published_hash,
            "can_assemble": False, "host_verified": False,
            "alpha_pixels_verified": True,
            "alpha_sampled_frames": alpha["sampled_frames"],
            "alpha_checked_samples": alpha["checked_alpha_samples"],
            "whole_frame_verified": False,
            "canva_fidelity_verified": False
        }
    finally:
        # Only our unique private work directory is removed; source and any
        # existing cache output are never deleted, even on interrupted renders.
        if work.is_dir() and not work.is_symlink():
            shutil.rmtree(work)
