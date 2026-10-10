"""STEP21 native FADE keyframe compiler regression tests; no images created."""
from __future__ import annotations

import copy
import runpy
from pathlib import Path
import unittest

from core.animation_phases import build_both_phase_candidate
from core.fx_native_fade import (
    NativeFadeError, compile_native_fade, validate_native_fade_candidate
)

ROOT = Path(__file__).resolve().parents[1]
demo = runpy.run_path(str(ROOT / "tests/test_core_contracts.py"))["demo"]


def entry():
    edit, animation = demo()
    animation["decisions"][0]["preset"] = "FADE"
    animation["decisions"][0]["direction"] = "NONE"
    return build_both_phase_candidate(edit, animation, max_instances=10)["entries"][0]


class NativeFadeCandidateTests(unittest.TestCase):
    def test_exact_medium_both_fade_and_nonzero_scene_start(self):
        source=entry()
        source.update(start_frame=90,end_frame=240,
                      in_range=[90,105],hold_range=[105,233],
                      out_range=[233,240])
        result=compile_native_fade(source)
        self.assertEqual(result["duration_frames"],150)
        self.assertEqual(result["timebase_semantics"],"INSTANCE_LOCAL_FRAME_30FPS")
        self.assertEqual(result["samples"],[
            {"frame":0,"opacity_percent":0},
            {"frame":14,"opacity_percent":100},
            {"frame":143,"opacity_percent":100},
            {"frame":149,"opacity_percent":0}
        ])
        self.assertEqual(result["preset"],"FADE")
        self.assertEqual(result["mode"],"BOTH")
        self.assertEqual(result["direction"],"NONE")
        self.assertEqual(result["host_component_match_name"],None)
        self.assertFalse(result["host_verified"])
        self.assertFalse(result["can_assemble"])
        validate_native_fade_candidate(result)

    def test_zero_hold_and_exact_last_sample_are_valid(self):
        source=entry()
        source.update(start_frame=0,end_frame=22,
                      in_range=[0,15],hold_range=[15,15],
                      out_range=[15,22])
        result=compile_native_fade(source)
        self.assertEqual([row["frame"] for row in result["samples"]],[0,14,15,21])
        validate_native_fade_candidate(result)

    def test_short_clip_rejected_instead_of_auto_retimed(self):
        source=entry()
        source.update(start_frame=0,end_frame=21,
                      in_range=[0,15],hold_range=[15,14],out_range=[14,21])
        with self.assertRaises(NativeFadeError) as raised:
            compile_native_fade(source)
        self.assertEqual(raised.exception.code,"E_TIME_006")

    def test_other_presets_never_silently_substitute_fade(self):
        for preset in ("PAN","POP","RISE","WIPE","INK","STOMP"):
            source=entry()
            source["preset"]=preset
            with self.subTest(preset=preset):
                with self.assertRaises(NativeFadeError) as e:
                    compile_native_fade(source)
                self.assertEqual(e.exception.code,"E_FX_NATIVE_PRESET_UNSUPPORTED")

    def test_directions_mode_speed_phase_and_reference_cannot_change(self):
        for modify in (
                {"direction":"LEFT_TO_RIGHT"},
                {"mode":"IN"},
                {"mode":"OUT"},
                {"speed":"FAST"},
                {"can_render":True},
                {"effect_backend":"NATIVE"},
                {"reference_evidence":"V3_EXACT_LITERAL"},
                {"in_frames":14},
                {"start_frame":True},
                {"keyframes":[1,2,3]},
                {"in_range":[0,14]}):
            with self.subTest(modify=modify):
                source=entry()
                source.update(modify)
                with self.assertRaises(NativeFadeError):
                    compile_native_fade(source)

    def test_tampering_even_with_new_digest_cannot_approve_host(self):
        result=compile_native_fade(entry())
        for field,value in [
            ("status","READY"),("can_assemble",True),
            ("host_verified",True),
            ("readback_verified",True),
            ("host_component_match_name","SomeOp"),
            ("host_parameter_match_name","SomeParam"),
            ("interpolation","SMOOTH"),
            ("direction","FROM_LEFT"),("in_frames",25),
            ("duration_frames",999),
        ]:
            changed=copy.deepcopy(result)
            changed[field]=value
            with self.subTest(field=field):
                with self.assertRaises(NativeFadeError) as e:
                    validate_native_fade_candidate(changed)
                self.assertEqual(e.exception.code,
                                 "E_FX_NATIVE_CANDIDATE_TAMPERED")

    def test_hash_and_sample_modification_rejected(self):
        changed=copy.deepcopy(compile_native_fade(entry()))
        changed["samples"][0]["opacity_percent"]=100
        with self.assertRaises(NativeFadeError):
            validate_native_fade_candidate(changed)
        changed=copy.deepcopy(compile_native_fade(entry()))
        changed["candidate_sha256"]="a"*64
        with self.assertRaises(NativeFadeError):
            validate_native_fade_candidate(changed)


if __name__=="__main__":
    unittest.main()
