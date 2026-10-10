"""STEP17 alpha cache worker mock subprocess tests; no images generated or edited.

The PNG fixture consists only of a small IHDR byte header, not a real image.
No real Adobe host, ffmpeg codec/alpha pixel correctness or UI artwork is claimed.
"""
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from core.fx_alpha_verify import AlphaPixelError

from core.animation_phases import build_both_phase_candidate
from core.fx_cache_worker import (
    AlphaCacheError, render_candidate, verify_cached_report,
    verify_cache_for_candidate,
)

ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]
HEADER=(b"\x89PNG\r\n\x1a\n"+(13).to_bytes(4,"big")+b"IHDR"+
        (64).to_bytes(4,"big")+(64).to_bytes(4,"big")+
        b"\x08\x06\x00\x00\x00"+b"\0"*8)


def candidate(preset="FADE", direction="NONE"):
    edit,animation=demo()
    animation["decisions"][0]["preset"]=preset
    animation["decisions"][0]["direction"]=direction
    return build_both_phase_candidate(edit,animation,max_instances=10)["entries"][0]


class AlphaCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.media=root/"media"
        self.cache=root/"cache"
        self.binary=root/"bin"
        for d in (self.media,self.cache,self.binary):
            d.mkdir()
        self.source=self.media/"approved.png"
        self.source.write_bytes(HEADER)
        self.input_sha=hashlib.sha256(HEADER).hexdigest()
        self.ffmpeg=self.binary/"ffmpeg.exe"
        self.ffprobe=self.binary/"ffprobe.exe"
        self.ffmpeg.write_bytes(b"fixture_binary")
        self.ffprobe.write_bytes(b"fixture_binary")
        self.calls=[]
        self.problem=None
        self.output_codec="qtrle"
        self.frame_count="150"
        self.extra_stream=False
        self.overwrite_race=False
        # Mocked FFmpeg creates only bogus bytes, so alpha verifier MUST be
        # explicitly mocked here; real integration is tested in STEP19 CI.
        self.mock_pixels=patch("core.fx_cache_worker.verify_alpha_pixels")
        self.alpha_checker=self.mock_pixels.start()
        self.addCleanup(self.mock_pixels.stop)
        self.alpha_checker.return_value={
            "pixel_alpha_checked": True, "sampled_frames": 6,
            "checked_alpha_samples": 120}

    def tearDown(self):
        self.tmp.cleanup()

    def runner(self,argv,**kwargs):
        self.calls.append((argv,kwargs))
        if Path(argv[0]).samefile(self.ffmpeg):
            if self.problem=="ffmpeg-exit":
                return subprocess.CompletedProcess(argv,2,b"",b"no details")
            if self.problem=="ffmpeg-timeout":
                raise subprocess.TimeoutExpired(argv,kwargs["timeout"])
            target=Path(argv[-1])
            target.write_bytes(b"synthetic_MOV_BYTES_ONLY_MOCK_NO_REAL_CODEC")
            return subprocess.CompletedProcess(argv,0,b"",b"")
        if Path(argv[0]).samefile(self.ffprobe):
            if self.problem=="probe-exit":
                return subprocess.CompletedProcess(argv,2,b"",b"")
            data={"streams":[{
                "codec_type":"video",
                "codec_name":self.output_codec,"pix_fmt":"argb",
                "width":64,"height":64,"nb_read_frames":self.frame_count,
                "r_frame_rate":"30/1"
            }]}
            if self.extra_stream:
                data["streams"].append({
                    "codec_type":"audio","codec_name":"aac"})
            if self.problem=="change-cache-on-probe":
                path=Path(argv[-1])
                if path.name.startswith("fx_"):
                    path.write_bytes(b"modified after sha but during probe")
            if self.problem=="probe-malformed":
                data=b"not json"
            else:
                data=json.dumps(data).encode()
            return subprocess.CompletedProcess(argv,0,data,b"")
        raise AssertionError("Only verified fixed executables may run")

    def kwargs(self,**overrides):
        return dict(item=candidate(),source_png=Path("approved.png"),
            media_root=self.media,cache_root=self.cache,
            expected_sha256=self.input_sha,ffmpeg_exe=self.ffmpeg,
            ffprobe_exe=self.ffprobe,max_source_bytes=100000,
            max_pixels=100000,max_frames=200,
            timeout_seconds=10,runner=self.runner,**overrides)

    def go(self,**overrides):
        args=self.kwargs()
        args.update(overrides)
        return render_candidate(**args)

    def audit(self,report,**overrides):
        kwargs=dict(report=report,cache_root=self.cache,
                    ffprobe_exe=self.ffprobe,max_cached_bytes=100000,
                    timeout_seconds=10,runner=self.runner)
        kwargs.update(overrides)
        return verify_cached_report(**kwargs)

    def assert_audit_code(self,code,report,**overrides):
        with self.assertRaises(AlphaCacheError) as ctx:
            self.audit(report,**overrides)
        self.assertEqual(ctx.exception.code,code)

    def reuse(self,report,**overrides):
        kwargs=dict(
            report=report,item=candidate(),
            expected_source_sha256=self.input_sha,
            expected_source_dimensions=(64,64),
            cache_root=self.cache,ffprobe_exe=self.ffprobe,
            max_cached_bytes=100000,timeout_seconds=10,runner=self.runner)
        kwargs.update(overrides)
        return verify_cache_for_candidate(**kwargs)

    def assert_reuse_code(self,code,report,**overrides):
        with self.assertRaises(AlphaCacheError) as ctx:
            self.reuse(report,**overrides)
        self.assertEqual(ctx.exception.code,code)

    def assert_code(self,code,**overrides):
        with self.assertRaises(AlphaCacheError) as ctx:
            self.go(**overrides)
        self.assertEqual(ctx.exception.code,code)

    def test_successful_mock_render_is_cache_only_and_not_certified(self):
        r=self.go()
        self.assertEqual(r["status"],
            "RENDERED_SAMPLED_ALPHA_VERIFIED_NOT_HOST_CERTIFIED")
        self.assertFalse(r["can_assemble"])
        self.assertTrue(r["alpha_pixels_verified"])
        self.assertFalse(r["whole_frame_verified"])
        self.alpha_checker.assert_called_once()
        self.assertFalse(r["host_verified"])
        self.assertEqual(r["size"],[64,64])
        self.assertEqual(r["frames"],150)
        self.assertEqual(self.source.read_bytes(),HEADER)
        outputs=list(self.cache.glob("fx_*.mov"))
        self.assertEqual(len(outputs),1)
        self.assertFalse(list(self.cache.glob(".fx_work_*")))
        self.assertEqual(len(r["cache_key_sha256"]),64)
        self.assertEqual(hashlib.sha256(outputs[0].read_bytes()).hexdigest(),
                         r["output_sha256"])
        self.assertEqual(len(self.calls),2)
        for argv,options in self.calls:
            self.assertFalse(options["shell"])
            self.assertEqual(options["timeout"],10)
        ffmpeg_args=self.calls[0][0]
        self.assertIn("-n",ffmpeg_args)
        self.assertNotIn("-y",ffmpeg_args)
        self.assertEqual(ffmpeg_args[ffmpeg_args.index("-frames:v")+1],"150")
        self.assertEqual(self.calls[1][0][self.calls[1][0].index("-count_frames")],
                         "-count_frames")
        self.assertNotIn("-select_streams",self.calls[1][0])

    def test_no_overwrite_even_when_cache_key_reused(self):
        original=self.go()
        self.assert_code("E_FX_CACHE_EXISTS_NO_OVERWRITE")
        self.assertEqual(len(self.calls),2)
        self.assertEqual(len(list(self.cache.glob("fx_*.mov"))),1)
        self.assertEqual(original["frames"],150)

    def test_source_hash_tamper_never_runs_ffmpeg(self):
        self.assert_code("E_FX_SOURCE_HASH",expected_sha256="a"*64)
        self.assertEqual(self.calls,[])
        self.assertFalse(list(self.cache.iterdir()))

    def test_invalid_png_header_never_renders(self):
        new=b"broken PNG"
        self.source.write_bytes(new)
        self.assert_code("E_FX_SOURCE_LIMIT",
            expected_sha256=hashlib.sha256(new).hexdigest())
        self.assertFalse(self.calls)
        new=b"X"*len(HEADER)
        self.source.write_bytes(new)
        self.assert_code("E_FX_PNG_INVALID",
            expected_sha256=hashlib.sha256(new).hexdigest())

    def test_rejects_png_without_alpha(self):
        data=bytearray(HEADER)
        data[25]=2 # RGB, no alpha
        self.source.write_bytes(data)
        self.assert_code("E_FX_PNG_PROFILE_UNVERIFIED",
                         expected_sha256=hashlib.sha256(data).hexdigest())
        self.assertEqual(self.calls,[])

    def test_path_traversal_and_cache_root_collision_are_blocked(self):
        self.assert_code("E_FX_SOURCE_PATH",source_png=Path("../approved.png"))
        self.assert_code("E_FX_CACHE_ROOT_COLLISION",cache_root=self.media)
        self.assertFalse(self.calls)

    def test_bad_resource_limits_and_unsupported_preset_are_blocked(self):
        self.assert_code("E_FX_RESOURCE_LIMIT_UNVERIFIED",max_frames=0)
        self.assert_code("E_FX_RESOURCE_LIMIT",max_frames=100)
        self.assert_code("E_FX_BACKEND_NOT_IMPLEMENTED",
                         item=candidate("BRUSH","LEFT_TO_RIGHT"))

    def test_invalid_or_missing_binary_refused_before_render(self):
        self.assert_code("E_FX_BINARY_UNVERIFIED",
                         ffmpeg_exe=self.binary/"not-ffmpeg.exe")
        self.assert_code("E_FX_BINARY_UNVERIFIED",
                         ffprobe_exe=Path("ffprobe.exe"))
        self.assertEqual(self.calls,[])

    def test_ffmpeg_errors_clean_private_workdir_without_publishing(self):
        for name,expected in (("ffmpeg-exit","E_FX_RENDER_FAILED"),
                              ("ffmpeg-timeout","E_FX_RENDER_EXEC_FAILED")):
            self.problem=name
            self.assert_code(expected)
            self.assertFalse(list(self.cache.iterdir()))
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_bad_ffprobe_data_aborts_publish_without_orphan(self):
        for name,expected in (("probe-exit","E_FX_PROBE_FAILED"),
                              ("probe-malformed","E_FX_PROBE_FAILED")):
            self.problem=name
            self.assert_code(expected)
            self.assertFalse(list(self.cache.iterdir()))
        self.problem=None
        self.output_codec="h264"
        self.assert_code("E_FX_PROBE_MISMATCH")
        self.assertFalse(list(self.cache.iterdir()))
        self.output_codec="qtrle"
        self.frame_count="149"
        self.assert_code("E_FX_PROBE_MISMATCH")
        self.assertFalse(list(self.cache.iterdir()))

    def test_extra_mov_audio_stream_rejected_before_publish(self):
        self.extra_stream=True
        self.assert_code("E_FX_PROBE_FAILED")
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertEqual(list(self.cache.iterdir()),[])

    def test_cache_reuse_is_bound_to_exact_source_preset_and_timing(self):
        report=self.go()
        before=len(self.calls)
        approved=self.reuse(report)
        self.assertEqual(approved["cache_input_binding"],
                         "DECLARED_SOURCE_SHA_EFFECT_TIMING_AND_SIZE_MATCHED")
        self.assertEqual(approved["candidate_preset"],"FADE")
        self.assertEqual(approved["candidate_direction"],"NONE")
        self.assertFalse(approved["source_bytes_reverified"])
        self.assertFalse(approved["alpha_pixels_reverified"])
        self.assertFalse(approved["host_verified"])
        self.assertFalse(approved["can_assemble"])
        self.assertEqual(len(self.calls),before+1)
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_reuse_rejects_different_source_sha_without_probing(self):
        report=self.go()
        before=len(self.calls)
        self.assert_reuse_code("E_FX_CACHE_CANDIDATE_MISMATCH",report,
                               expected_source_sha256="a"*64)
        self.assertEqual(len(self.calls),before)
        self.assertEqual(len(list(self.cache.glob("fx_*.mov"))),1)
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_reuse_rejects_same_source_but_different_preset_and_direction(self):
        report=self.go()
        before=len(self.calls)
        for effect,direction in (
                ("WIPE","LEFT_TO_RIGHT"),("WIPE","RIGHT_TO_LEFT"),
                ("WIPE","TOP_TO_BOTTOM"),("WIPE","BOTTOM_TO_TOP")):
            with self.subTest(effect=effect,direction=direction):
                self.assert_reuse_code(
                    "E_FX_CACHE_CANDIDATE_MISMATCH",report,
                    item=candidate(effect,direction))
        self.assertEqual(len(self.calls),before)

    def test_reuse_rejects_wrong_source_dimensions_and_corrupt_report(self):
        report=self.go()
        before=len(self.calls)
        for dimensions in ((65,64),(64,65),(1,1)):
            with self.subTest(dimensions=dimensions):
                self.assert_reuse_code("E_FX_CACHE_CANDIDATE_MISMATCH",
                                      report,expected_source_dimensions=dimensions)
        forged=dict(report,preset="WIPE")
        self.assert_reuse_code("E_FX_CACHE_CANDIDATE_MISMATCH",forged)
        forged=dict(report,frames=149)
        self.assert_reuse_code("E_FX_CACHE_CANDIDATE_MISMATCH",forged)
        self.assertEqual(len(self.calls),before)

    def test_reuse_rejects_unpinned_source_or_noninteger_geometry(self):
        report=self.go()
        before=len(self.calls)
        for source in ("a"*63,"A"*64,None,123):
            with self.subTest(source=source):
                self.assert_reuse_code("E_FX_CACHE_INPUT_UNPINNED",report,
                                       expected_source_sha256=source)
        for dimensions in ((True,64),[64,64],(64,0),(64,-1),"64x64"):
            with self.subTest(dimensions=dimensions):
                self.assert_reuse_code("E_FX_CACHE_INPUT_UNPINNED",report,
                                       expected_source_dimensions=dimensions)
        self.assertEqual(len(self.calls),before)

    def test_reuse_hash_valid_item_still_requires_unmodified_mov(self):
        report=self.go()
        next(self.cache.glob("fx_*.mov")).write_bytes(b"corrupt")
        self.assert_reuse_code("E_FX_CACHE_HASH_MISMATCH",report)
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertEqual(len(list(self.cache.glob("fx_*.mov"))),1)

    def test_stage_mov_modified_during_ffprobe_never_reaches_cache(self):
        # The mocked probe reports success but another writer changes the
        # private output immediately afterward. Prior to STEP30, such bytes
        # could be alpha-verified by a mock then published with a fresh SHA.
        def mutate_after_probe(argv,**kwargs):
            result=self.runner(argv,**kwargs)
            if Path(argv[0]).samefile(self.ffprobe):
                Path(argv[-1]).write_bytes(b"changed after probed")
            return result
        self.assert_code("E_FX_CACHE_CHANGED",runner=mutate_after_probe)
        self.assertEqual(list(self.cache.iterdir()),[])
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_stage_mov_modified_during_alpha_readback_never_publishes(self):
        original=self.alpha_checker.return_value
        def mutate_alpha(*args,**kwargs):
            Path(kwargs["output_mov"]).write_bytes(b"changed during pixels")
            return original
        self.alpha_checker.side_effect=mutate_alpha
        self.assert_code("E_FX_CACHE_CHANGED")
        self.assertEqual(list(self.cache.iterdir()),[])
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.alpha_checker.assert_called_once()

    def test_identical_mov_bytes_replaced_inode_during_alpha_is_rejected(self):
        original=self.alpha_checker.return_value
        def swap_inode(*args,**kwargs):
            path=Path(kwargs["output_mov"])
            replacement=path.with_suffix(".swapped")
            replacement.write_bytes(path.read_bytes())
            os.replace(replacement,path)
            return original
        self.alpha_checker.side_effect=swap_inode
        self.assert_code("E_FX_CACHE_CHANGED")
        self.assertEqual(list(self.cache.iterdir()),[])
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.alpha_checker.assert_called_once()

    def test_original_png_inode_swap_during_private_copy_refused(self):
        # A same-byte/same-mtime source swap must fail descriptor identity,
        # not be accepted merely because its SHA matches the pinned hash.
        original_fstat=os.fstat
        count=[0]
        def fake_second_fstat(fd):
            info=original_fstat(fd)
            count[0]+=1
            if count[0] == 2:
                return SimpleNamespace(
                    st_mode=info.st_mode, st_dev=info.st_dev,
                    st_ino=info.st_ino + 99, st_size=info.st_size,
                    st_mtime_ns=info.st_mtime_ns,
                    st_ctime_ns=info.st_ctime_ns)
            return info
        with patch("core.fx_cache_worker.os.fstat",side_effect=fake_second_fstat):
            self.assert_code("E_FX_SOURCE_CHANGED")
        self.assertGreaterEqual(count[0],2)
        self.assertEqual(self.calls,[])
        self.assertFalse(list(self.cache.iterdir()))
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_mutated_private_staged_png_during_alpha_blocks_publish(self):
        original_result=self.alpha_checker.return_value
        def modified_staged(*args,**kwargs):
            Path(kwargs["source_png"]).write_bytes(b"changed staged source")
            return original_result
        self.alpha_checker.side_effect=modified_staged
        self.assert_code("E_FX_SOURCE_CHANGED")
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertFalse(list(self.cache.iterdir()))
        self.alpha_checker.assert_called_once()

    def test_replaced_private_png_same_bytes_during_alpha_blocks_publish(self):
        original_result=self.alpha_checker.return_value
        def swapped_staged(*args,**kwargs):
            path=Path(kwargs["source_png"])
            replacement=path.with_suffix(".replacement")
            replacement.write_bytes(path.read_bytes())
            os.replace(replacement,path)
            return original_result
        self.alpha_checker.side_effect=swapped_staged
        self.assert_code("E_FX_SOURCE_CHANGED")
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertFalse(list(self.cache.iterdir()))
        self.alpha_checker.assert_called_once()

    def test_publish_rechecks_sha_on_final_path_after_atomic_link(self):
        # Simulate an outside writer modifying the newly published inode
        # during the gap between pre-publication SHA and final report.
        real_link=os.link
        def link_then_modify(source,destination):
            real_link(source,destination)
            Path(destination).write_bytes(b"changed after first SHA")
        with patch("core.fx_cache_worker.os.link",side_effect=link_then_modify):
            self.assert_code("E_FX_CACHE_CHANGED")
        # Do not silently delete modified media; a subsequent attempt must
        # refuse overwrite rather than reuse an untrusted cache entry.
        files=list(self.cache.glob("fx_*.mov"))
        self.assertEqual(len(files),1)
        self.assertEqual(files[0].read_bytes(),b"changed after first SHA")
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertFalse(list(self.cache.glob(".fx_work_*")))
        self.assert_code("E_FX_CACHE_EXISTS_NO_OVERWRITE")
        self.assertEqual(len(list(self.cache.glob("fx_*.mov"))),1)

    def test_publish_rejects_replaced_target_after_link(self):
        real_link=os.link
        def link_then_replace(source,destination):
            real_link(source,destination)
            replacement=Path(destination).with_suffix(".tmp")
            replacement.write_bytes(Path(destination).read_bytes())
            os.replace(replacement,destination)
        with patch("core.fx_cache_worker.os.link",side_effect=link_then_replace):
            self.assert_code("E_FX_CACHE_CHANGED")
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertEqual(len(list(self.cache.glob("fx_*.mov"))),1)
        self.assertFalse(list(self.cache.glob(".fx_work_*")))

    def test_successful_publish_sha_survives_restart_audit(self):
        report=self.go()
        audit=self.audit(report)
        self.assertEqual(audit["output_sha256"],report["output_sha256"])
        self.assertEqual(report["output_sha256"],
                         hashlib.sha256(next(self.cache.glob("fx_*.mov"))
                                        .read_bytes()).hexdigest())
        self.assertFalse(audit["host_verified"])

    def test_reopen_cache_report_checks_sha_and_codec_read_only(self):
        report=self.go()
        inspected=self.audit(report)
        self.assertEqual(inspected["cache_integrity"],
                         "SHA256_AND_METADATA_CHECKED")
        self.assertFalse(inspected["host_verified"])
        self.assertFalse(inspected["alpha_pixels_reverified"])
        self.assertFalse(inspected["can_assemble"])
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertEqual(len(list(self.cache.glob("fx_*.mov"))),1)
        self.assertNotIn("-select_streams",self.calls[-1][0])

    def test_reopen_cache_rejects_corrupt_hash_without_deletion(self):
        report=self.go()
        cached=next(self.cache.glob("fx_*.mov"))
        cached.write_bytes(b"damaged content")
        self.assert_audit_code("E_FX_CACHE_HASH_MISMATCH",report)
        self.assertEqual(cached.read_bytes(),b"damaged content")
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_reopen_cache_rejects_forged_report_or_missing_file(self):
        report=self.go()
        invalid=dict(report,cache_key_sha256="../unsafe-path")
        self.assert_audit_code("E_FX_CACHE_REPORT_INVALID",invalid)
        invalid=dict(report,host_verified=True)
        self.assert_audit_code("E_FX_CACHE_REPORT_INVALID",invalid)
        invalid=dict(report,output_sha256="not-hash")
        self.assert_audit_code("E_FX_CACHE_REPORT_INVALID",invalid)
        self.assert_audit_code("E_FX_CACHE_RESOURCE_LIMIT",report,
                               max_cached_bytes=1)
        next(self.cache.glob("fx_*.mov")).unlink()
        self.assert_audit_code("E_FX_CACHE_MISSING",report)

    def test_reopen_cache_rejects_audio_or_mutation_during_probe(self):
        report=self.go()
        self.extra_stream=True
        self.assert_audit_code("E_FX_PROBE_FAILED",report)
        self.extra_stream=False
        self.problem="change-cache-on-probe"
        self.assert_audit_code("E_FX_CACHE_CHANGED",report)
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_reopen_cache_refuses_symlink_without_deleting_target(self):
        report=self.go()
        cached=next(self.cache.glob("fx_*.mov"))
        cached.unlink()
        try:
            cached.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("Creating test symlinks unavailable on this OS")
        self.assert_audit_code("E_FX_CACHE_UNSAFE",report)
        self.assertEqual(self.source.read_bytes(),HEADER)

    def test_alpha_verification_failure_blocks_publish_without_source_mutation(self):
        self.alpha_checker.side_effect=AlphaPixelError(
            "E_FX_ALPHA_PIXELS_MISMATCH")
        self.assert_code("E_FX_ALPHA_PIXELS_MISMATCH")
        self.assertFalse(list(self.cache.iterdir()))
        self.assertEqual(self.source.read_bytes(),HEADER)
        self.assertEqual(len(self.calls),2)
        self.alpha_checker.assert_called_once()

    def test_alpha_verifier_cannot_return_unverified_status(self):
        self.alpha_checker.return_value={"pixel_alpha_checked":False}
        self.assert_code("E_FX_ALPHA_UNVERIFIED")
        self.assertFalse(list(self.cache.iterdir()))

    def test_cache_and_source_are_never_overwritten_by_json_values(self):
        r=self.go()
        self.assertFalse(r["canva_fidelity_verified"])
        self.assertTrue(all(".fx_work_" not in x.name for x in self.cache.iterdir()))
        self.assertTrue(self.source.is_file())
        self.assertFalse(any(p.name=="approved.png" for p in self.cache.iterdir()))

if __name__=="__main__":
    unittest.main()
