"""Runnable FFmpeg filtergraph assembly, no user image/media generation."""
import copy
import json
import os
import runpy
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from core.fx_alpha_backend import (
    AlphaBackendError, backend_support, compile_filter,
    build_ffmpeg_command)
from core.animation_phases import build_both_phase_candidate

ROOT=Path(__file__).resolve().parents[1]
demo=runpy.run_path(str(ROOT/"tests/test_core_contracts.py"))["demo"]

def case(preset="FADE",direction="NONE"):
    edit,animation=demo()
    animation["decisions"][0]["preset"]=preset
    animation["decisions"][0]["direction"]=direction
    plan=build_both_phase_candidate(edit,animation,max_instances=10)
    return plan["entries"][0]


class FFmpegAlphaBackendTests(unittest.TestCase):
    def test_fade_candidate_uses_exact_both_reference_frames(self):
        item=case()
        out=compile_filter(item)
        self.assertEqual(out["preset"],"FADE")
        self.assertEqual(out["frames"],150)
        self.assertIn("(N+1)/15",out["filtergraph"])
        self.assertIn("(D-N-1)/7",out["filtergraph"])
        self.assertEqual(out["codec"],"qtrle")
        self.assertEqual(out["pixel_format"],"argb")
        self.assertFalse(out["can_assemble"])
        self.assertFalse(out["can_claim_canva_fidelity"])

    def test_wipe_four_directions_build_distinct_alpha_masks(self):
        graphs=set()
        for direction in ("LEFT_TO_RIGHT","RIGHT_TO_LEFT",
                          "TOP_TO_BOTTOM","BOTTOM_TO_TOP"):
            compiled=compile_filter(case("WIPE",direction))
            graphs.add(compiled["filtergraph"])
            self.assertIn("alpha(X,Y)",compiled["filtergraph"])
            self.assertEqual(compiled["frames"],150)
        self.assertEqual(len(graphs),4)

    def test_no_silent_substitute_for_19_uncoded_presets(self):
        support=backend_support()
        self.assertEqual(support["coded_presets"],["FADE","WIPE"])
        self.assertEqual(support["unimplemented_presets"],19)
        self.assertEqual(support["actual_host_certified"],0)
        for preset,direction in (("BRUSH","LEFT_TO_RIGHT"),
                                 ("POP","NONE"),("INK","CENTER"),
                                 ("PAN","FROM_LEFT"),("STOMP","NONE")):
            with self.assertRaises(AlphaBackendError) as ex:
                compile_filter(case(preset,direction))
            self.assertEqual(ex.exception.code,"E_FX_BACKEND_NOT_IMPLEMENTED")

    def test_wrong_direction_or_mode_fails(self):
        for change in ({"direction":"LEFT_TO_RIGHT"},
                       {"mode":"IN_ONLY"},
                       {"can_render":True},
                       {"speed":"FAST"},
                       {"effect_backend":"READY"}):
            item=case()
            item.update(change)
            with self.assertRaises(AlphaBackendError):
                compile_filter(item)
        item=case("WIPE","LEFT_TO_RIGHT")
        item["direction"]="NONE"
        with self.assertRaises(AlphaBackendError):
            compile_filter(item)

    def test_zero_hold_and_short_duration_boundaries(self):
        item=case()
        item.update(start_frame=0,end_frame=22,
                    in_range=[0,15],hold_range=[15,15],out_range=[15,22])
        self.assertEqual(compile_filter(item)["frames"],22)
        item["end_frame"]=21
        with self.assertRaises(AlphaBackendError) as ex:
            compile_filter(item)
        self.assertEqual(ex.exception.code,"E_TIME_006")

    def test_modified_phase_ranges_are_rejected(self):
        item=case();item["in_range"]=[0,8]
        with self.assertRaises(AlphaBackendError) as ex:
            compile_filter(item)
        self.assertEqual(ex.exception.code,"E_FX_PHASE_TAMPERED")

    def test_tampered_reference_durations_and_type_confusion_rejected(self):
        item=case()
        item["in_frames"]=16
        item["in_range"]=[0,16]
        with self.assertRaises(AlphaBackendError) as ex:
            compile_filter(item)
        self.assertEqual(ex.exception.code,"E_FX_REFERENCE_TAMPERED")
        for invalid in ([],{},None):
            item=case()
            item["preset"]=invalid
            with self.assertRaises(AlphaBackendError):
                compile_filter(item)

    def test_graph_never_carries_paths_or_json_user_expressions(self):
        item=case("WIPE","LEFT_TO_RIGHT")
        item["asset_id"]="source_private_file.png"
        output=compile_filter(item)
        self.assertNotIn("private",output["filtergraph"])
        self.assertNotIn("cmd",output["filtergraph"])

    def test_build_command_no_shell_and_no_overwrite(self):
        out=compile_filter(case())
        binary = Path("C:/ffmpeg/ffmpeg.exe") if os.name=="nt" else Path("/opt/ffmpeg")
        source = Path("C:/Job/source.png") if os.name=="nt" else Path("/tmp/source.png")
        target = Path("C:/Job/derived.mov") if os.name=="nt" else Path("/tmp/derived.mov")
        cmd=build_ffmpeg_command(out,binary,source,target)
        self.assertEqual(cmd[0],str(binary))
        self.assertIn("-n",cmd)
        self.assertNotIn("-y",cmd)
        self.assertEqual(cmd[-2:],["mov",str(target)])
        self.assertEqual(cmd[cmd.index("-frames:v")+1],"150")
        self.assertEqual(cmd[cmd.index("-vf")+1],out["filtergraph"])

    def test_bad_paths_binary_and_payload_are_blocked(self):
        out=compile_filter(case())
        with self.assertRaises(AlphaBackendError):
            build_ffmpeg_command(out,Path("ffmpeg"),Path("/tmp/x.png"),Path("/tmp/y.mov"))
        with self.assertRaises(AlphaBackendError):
            build_ffmpeg_command(out,Path("/usr/bin/ffmpeg"),Path("../x.png"),Path("/tmp/y.mov"))
        compromised=copy.deepcopy(out);compromised["status"]="READY"
        with self.assertRaises(AlphaBackendError):
            build_ffmpeg_command(compromised,Path("/usr/bin/ffmpeg"),Path("/tmp/x.png"),Path("/tmp/y.mov"))
        compromised=copy.deepcopy(out);compromised["filtergraph"]="movie=/etc/passwd,format=argb"
        with self.assertRaises(AlphaBackendError):
            build_ffmpeg_command(compromised,Path("/usr/bin/ffmpeg"),Path("/tmp/x.png"),Path("/tmp/y.mov"))
        compromised=copy.deepcopy(out)
        compromised["filtergraph"]=compromised["filtergraph"].replace("alpha(X,Y)","255")
        with self.assertRaises(AlphaBackendError):
            build_ffmpeg_command(compromised,Path("/usr/bin/ffmpeg"),Path("/tmp/x.png"),Path("/tmp/y.mov"))
        compromised=copy.deepcopy(out);compromised["in_frames"]=55
        with self.assertRaises(AlphaBackendError):
            build_ffmpeg_command(compromised,Path("/usr/bin/ffmpeg"),Path("/tmp/x.png"),Path("/tmp/y.mov"))

    @unittest.skipUnless(shutil.which("ffmpeg"),"optional FFmpeg binary unavailable")
    def test_real_ffmpeg_lavfi_alpha_filter_without_writing_assets(self):
        """Apply compiled graphs to synthetic lavfi frames; output discarded.

        No user images, generated PNGs, videos or project files are created.
        This is runnable filter syntax QA, NOT visual fidelity certification.
        """
        binary=shutil.which("ffmpeg")
        for item in (case(),case("WIPE","RIGHT_TO_LEFT"),
                     case("WIPE","TOP_TO_BOTTOM")):
            graph=compile_filter(item)["filtergraph"]
            cmd=[binary,"-hide_banner","-nostdin","-loglevel","error",
                 "-f","lavfi","-i","color=c=red:s=32x32:r=30:d=1,format=gbrap",
                 "-vf",graph,"-frames:v","30","-f","null","-"]
            done=subprocess.run(cmd,capture_output=True,timeout=25,check=False)
            self.assertEqual(done.returncode,0,done.stderr[:900])

if __name__=="__main__":
    unittest.main()
