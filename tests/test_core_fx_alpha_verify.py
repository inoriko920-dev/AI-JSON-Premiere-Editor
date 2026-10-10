"""STEP19 mocked pixel readback security tests; no PNG or UI images created."""
from pathlib import Path
import subprocess
import unittest

from core.fx_alpha_verify import (
    AlphaPixelError, _progress, _spatial, verify_alpha_pixels
)

_GRID=8
_PNG=Path("/no_actual_asset/source.png")
_MOV=Path("/no_actual_asset/render.mov")
_FFMPEG=Path("/no_actual_asset/ffmpeg")


class AlphaPixelTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.problem=None
        self.tamper=False
        self.transparent=False

    def runner(self, argv, **options):
        self.calls.append((argv, options))
        self.assertFalse(options["shell"])
        self.assertEqual(options["timeout"], 11)
        self.assertNotIn("-y",argv)
        self.assertEqual(argv[-2:], ["rawvideo","-"])
        if self.problem=="error":
            raise subprocess.TimeoutExpired(argv,11)
        if self.problem=="exit":
            return subprocess.CompletedProcess(argv,1,b"",b"")
        path=argv[argv.index("-i")+1]
        if path==str(_PNG):
            raw=bytes((210,10,10,0 if self.transparent else 255))*(_GRID*_GRID)
        else:
            indices=[0,7,14,143,147,149]
            raw=bytearray()
            for n in indices:
                p=_progress(n,150,15,7)
                for y in range(_GRID):
                    for x in range(_GRID):
                        alpha=round(255*p)
                        raw+=bytes((210,10,10,alpha))
            if self.tamper:
                raw[3]=255
            raw=bytes(raw)
        if self.problem=="short":
            raw=raw[:-4]
        return subprocess.CompletedProcess(argv,0,raw,b"")

    def check(self,**changed):
        opts=dict(ffmpeg_exe=_FFMPEG, source_png=_PNG,
                  output_mov=_MOV,width=64,height=64,frames=150,
                  in_frames=15,out_frames=7,preset="FADE",
                  direction="NONE",timeout_seconds=11,runner=self.runner)
        opts.update(changed)
        return verify_alpha_pixels(**opts)

    def test_valid_source_relative_fade_checks_actual_alpha_samples(self):
        r=self.check()
        self.assertTrue(r["pixel_alpha_checked"])
        self.assertEqual(r["sampled_frames"],6)
        self.assertEqual(r["checked_alpha_samples"],6*64)
        self.assertFalse(r["whole_frame_verified"])
        self.assertFalse(r["host_verified"])
        self.assertEqual(len(self.calls),2)
        self.assertTrue(any("select=" in arg for arg in self.calls[1][0]))
        self.assertFalse(any(arg.startswith("-y") for call,_ in self.calls for arg in call))

    def test_pixel_mismatch_never_claims_success(self):
        self.tamper=True
        with self.assertRaises(AlphaPixelError) as caught:
            self.check()
        self.assertEqual(caught.exception.code,"E_FX_ALPHA_PIXELS_MISMATCH")

    def test_unobservable_source_alpha_must_fail_closed(self):
        self.transparent=True
        with self.assertRaises(AlphaPixelError) as caught:
            self.check()
        self.assertEqual(caught.exception.code,"E_FX_ALPHA_UNOBSERVABLE")

    def test_incomplete_stdout_and_ffmpeg_errors_fail(self):
        for problem in ("short","exit","error"):
            with self.subTest(problem=problem):
                self.problem=problem
                with self.assertRaises(AlphaPixelError) as caught:
                    self.check()
                self.assertEqual(caught.exception.code,"E_FX_ALPHA_READBACK_FAILED")

    def test_bad_policy_rejected_before_ffmpeg_execution(self):
        for change in ({"width":7},{"height":1},{"frames":5},
                       {"in_frames":1},{"out_frames":1},
                       {"preset":"BRUSH"},{"direction":"UP"},
                       {"timeout_seconds":0}):
            with self.subTest(change=change):
                self.calls.clear()
                with self.assertRaises(AlphaPixelError) as caught:
                    self.check(**change)
                self.assertEqual(caught.exception.code,"E_FX_ALPHA_POLICY_INVALID")
                self.assertFalse(self.calls)

    def test_direction_masks_cannot_all_be_identical(self):
        masks=set()
        for direction in ("LEFT_TO_RIGHT","RIGHT_TO_LEFT",
                          "TOP_TO_BOTTOM","BOTTOM_TO_TOP"):
            mask=tuple(_spatial(direction,x,y,.5)[0]
                       for y in range(_GRID) for x in range(_GRID))
            masks.add(mask)
        self.assertEqual(len(masks),4)

if __name__=="__main__":
    unittest.main()
