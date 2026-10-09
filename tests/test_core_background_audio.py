"""Safe background MP4 audio isolation worker, with fake FFmpeg binaries."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from core.background_audio import prepare_video_only_background, BackgroundIsolationError


def stream_data(audio):
    streams=[{"codec_type":"video","codec_name":"h264","width":1920,"height":1080}]
    if audio:
        streams.append({"codec_type":"audio","codec_name":"aac"})
    return json.dumps({"streams":streams}).encode()


class BackgroundIsolationTests(unittest.TestCase):
    def setUp(self):
        self.root_tmp=tempfile.TemporaryDirectory()
        self.cache_tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.root_tmp.name)
        self.cache=Path(self.cache_tmp.name)
        self.original=self.root/"video.mp4"
        self.original.write_bytes(b"ORIGINAL USER MEDIA - DO NOT CHANGE")
        self.digest=hashlib.sha256(self.original.read_bytes()).hexdigest()
        self.ffmpeg=self.cache/"ffmpeg.exe"
        self.ffprobe=self.cache/"ffprobe.exe"
        self.ffmpeg.write_bytes(b"worker test marker")
        self.ffprobe.write_bytes(b"worker test marker")
        self.calls=[]
        self.input_has_audio=True
        self.output_has_audio=False
        self.transcode_fails=False

    def tearDown(self):
        self.root_tmp.cleanup()
        self.cache_tmp.cleanup()

    def runner(self, args, **options):
        self.calls.append((args, options))
        self.assertFalse(options["shell"])
        self.assertTrue(options["capture_output"])
        if args[0] == str(self.ffprobe):
            is_original=not Path(args[-1]).name.startswith(".bg_work_")
            encoded=stream_data(self.input_has_audio if is_original else
                                self.output_has_audio)
            return subprocess.CompletedProcess(args,0,encoded,b"")
        self.assertEqual(args[0],str(self.ffmpeg))
        self.assertEqual(args[args.index("-c:v")+1],"copy")
        self.assertIn("-an",args)
        self.assertIn("-sn",args)
        self.assertIn("-dn",args)
        self.assertIn("-nostdin",args)
        if not self.transcode_fails:
            Path(args[-1]).write_bytes(b"GENERATED VIDEO ONLY")
        return subprocess.CompletedProcess(args,1 if self.transcode_fails else 0,b"",b"")

    def call(self, **overrides):
        kwargs=dict(ffmpeg_exe=self.ffmpeg,ffprobe_exe=self.ffprobe,
                    max_input_bytes=1_000_000,max_output_bytes=1_000_000,
                    runner=self.runner)
        kwargs.update(overrides)
        return prepare_video_only_background(self.root,"video.mp4",self.digest,
                                             self.cache,**kwargs)

    def assert_error(self,code,**opts):
        with self.assertRaises(BackgroundIsolationError) as exc:
            self.call(**opts)
        self.assertEqual(exc.exception.code,code)

    def test_creates_separate_verified_stream_candidate_without_touching_original(self):
        report=self.call()
        self.assertEqual(report["status"],"VIDEO_ONLY_CANDIDATE_UNVERIFIED")
        self.assertFalse(report["can_import"])
        self.assertFalse(report["can_assemble"])
        self.assertEqual(report["audio_streams"],0)
        self.assertTrue(report["output_created"])
        self.assertEqual(Path(report["candidate_path"]).read_bytes(),
                         b"GENERATED VIDEO ONLY")
        self.assertEqual(self.original.read_bytes(),b"ORIGINAL USER MEDIA - DO NOT CHANGE")
        self.assertEqual(len([x for x in self.cache.glob("*.mp4")]),1)

    def test_repeated_request_refuses_to_overwrite_cache_entry(self):
        report=self.call()
        prior=Path(report["candidate_path"]).read_bytes()
        self.assert_error("E_BACKGROUND_CACHE_TARGET_EXISTS")
        self.assertEqual(Path(report["candidate_path"]).read_bytes(),prior)

    def test_no_audio_source_needs_no_copy(self):
        self.input_has_audio=False
        report=self.call()
        self.assertEqual(report["status"],"ALREADY_VIDEO_ONLY_UNVERIFIED")
        self.assertFalse(report["output_created"])
        self.assertEqual(len(list(self.cache.glob("*.mp4"))),0)

    def test_ffmpeg_failure_keeps_original_and_no_output(self):
        self.transcode_fails=True
        self.assert_error("E_BACKGROUND_COPY_FAILED")
        self.assertEqual(self.original.read_bytes(),b"ORIGINAL USER MEDIA - DO NOT CHANGE")
        self.assertEqual(len(list(self.cache.glob("*.mp4"))),0)

    def test_output_still_has_audio_fails_closed(self):
        self.output_has_audio=True
        self.assert_error("E_BACKGROUND_AUDIO_NOT_ISOLATED")
        self.assertFalse(list(self.cache.glob("*.mp4")))

    def test_changed_hash_never_launches_commands(self):
        wrong="a"*64 if self.digest!="a"*64 else "b"*64
        with self.assertRaises(BackgroundIsolationError) as exc:
            prepare_video_only_background(self.root,"video.mp4",wrong,self.cache,
                ffmpeg_exe=self.ffmpeg,ffprobe_exe=self.ffprobe,
                max_input_bytes=100000,max_output_bytes=100000,runner=self.runner)
        self.assertEqual(exc.exception.code,"E_BACKGROUND_SOURCE_CHANGED")
        self.assertEqual(self.calls,[])

    def test_unclear_cache_root_or_source_traversal_blocks(self):
        with self.assertRaises(BackgroundIsolationError):
            prepare_video_only_background(self.root,"../escape.mp4",self.digest,
                self.cache,ffmpeg_exe=self.ffmpeg,ffprobe_exe=self.ffprobe,
                max_input_bytes=100000,max_output_bytes=100000,runner=self.runner)
        with self.assertRaises(BackgroundIsolationError) as exc:
            prepare_video_only_background(self.root,"video.mp4",self.digest,
                self.root,ffmpeg_exe=self.ffmpeg,ffprobe_exe=self.ffprobe,
                max_input_bytes=100000,max_output_bytes=100000,runner=self.runner)
        self.assertEqual(exc.exception.code,"E_BACKGROUND_PATH_INVALID")

    def test_invalid_tool_binary_refused_without_launch(self):
        self.assert_error("E_BACKGROUND_TOOL_UNAVAILABLE",ffmpeg_exe=self.root/"missing.exe")
        self.assertEqual(self.calls,[])

    def test_source_and_output_caps_enforced(self):
        self.assert_error("E_RESOURCE_LIMIT",max_input_bytes=3)
        self.assert_error("E_RESOURCE_LIMIT",max_output_bytes=3)
        self.assertFalse(list(self.cache.glob("*.mp4")))

    def test_audio_free_source_changed_during_probe_rejected(self):
        self.input_has_audio=False
        original_runner=self.runner
        def mutate_after_probe(args,**kwargs):
            result=original_runner(args,**kwargs)
            if args[0] == str(self.ffprobe) and args[-1] == str(self.original):
                self.original.write_bytes(b"CHANGED DURING READ")
            return result
        self.runner=mutate_after_probe
        self.assert_error("E_BACKGROUND_SOURCE_CHANGED")
        self.assertFalse(list(self.cache.glob("*.mp4")))

if __name__=="__main__":
    unittest.main()
