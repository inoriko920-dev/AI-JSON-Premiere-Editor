"""STEP22 native host inventory parser: untrusted diagnostics, no writes."""
from __future__ import annotations

from pathlib import Path
import runpy
import unittest

from core.animation_phases import build_both_phase_candidate
from core.fx_native_fade import compile_native_fade
from core.fx_native_host_probe import NativeHostInspectError, inspect_native_fade_host

ROOT = Path(__file__).resolve().parents[1]
demo = runpy.run_path(str(ROOT / "tests/test_core_contracts.py"))["demo"]


def candidate():
    edit, animation=demo()
    animation["decisions"][0]["preset"]="FADE"
    animation["decisions"][0]["direction"]="NONE"
    entry=build_both_phase_candidate(edit,animation,max_instances=10)["entries"][0]
    return compile_native_fade(entry)


class NativeHostProbeTests(unittest.TestCase):
    def setUp(self):
        self.candidate=candidate()
        self.report=("S22|1|OBSERVED_UNCERTIFIED|24.6.3|2|"
                     "Mock.Component.Opacity:Opacity;"
                     "Mock.Component.Motion:Motion%20Scale")

    def code(self,error,raw=None,source=None):
        with self.assertRaises(NativeHostInspectError) as raised:
            inspect_native_fade_host(self.candidate if source is None else source,
                                     self.report if raw is None else raw)
        self.assertEqual(raised.exception.code,error)

    def test_host_inventory_can_be_read_but_never_claims_certification(self):
        result=inspect_native_fade_host(self.candidate,self.report)
        self.assertEqual(result["status"],"HOST_COMPONENTS_OBSERVED_NOT_CERTIFIED")
        self.assertEqual(result["reported_host_version_untrusted"],"24.6.3")
        self.assertEqual(len(result["components"]),2)
        self.assertEqual(result["components"][1]["property_labels_unverified"],
                         ["Motion Scale"])
        self.assertEqual(len(result["inventory_sha256"]),64)
        self.assertEqual(result["candidate_sha256"],
                         self.candidate["candidate_sha256"])
        self.assertFalse(result["host_verified"])
        self.assertFalse(result["can_assemble"])
        self.assertFalse(result["readback_verified"])
        self.assertFalse(result["time_coordinate_verified"])
        self.assertIsNone(result["host_component_match_name"])

    def test_host_falsified_certified_never_parses_as_approved(self):
        self.code("E_FX_HOST_PROBE_MALFORMED",
                  self.report.replace("OBSERVED_UNCERTIFIED","CERTIFIED"))
        self.code("E_FX_HOST_PROBE_BLOCKED",
                  "S22|1|BLOCKED|HOST_VERSION_UNVERIFIED")

    def test_version_count_and_missing_comp_rejected(self):
        for value in (
            self.report.replace("24.6.3","25.0"),
            self.report.replace("|2|","|3|"),
            self.report.replace("|2|","|02|"),
            self.report.replace("|2|","|-1|"),
            self.report.replace(";", "|"),
            self.report+";unexpected",
            "S22|1|OBSERVED_UNCERTIFIED|24.0|0|"
        ):
            with self.subTest(value=value):
                self.code("E_FX_HOST_PROBE_MALFORMED",value)

    def test_rejects_injections_unsafe_utf8_and_noncanonical_encoding(self):
        for token in ("Opacity%0AInjected", "Opacity%zz",
                      "Opacity%2520", "Name%2fSlash", "%C3%28",
                      "Opacity:other"):
            raw="S22|1|OBSERVED_UNCERTIFIED|24.3|1|Mock:"+token
            with self.subTest(token=token):
                self.code("E_FX_HOST_PROBE_MALFORMED",raw)
        self.code("E_FX_HOST_PROBE_MALFORMED","S22|1|OBSERVED_UNCERTIFIED|24.0|1|")
        self.code("E_FX_HOST_PROBE_MALFORMED",self.report*100)

    def test_duplicate_components_and_excess_properties_denied(self):
        raw=("S22|1|OBSERVED_UNCERTIFIED|24.0|2|"
             "Same:Opacity;Same:Scale")
        self.code("E_FX_HOST_PROBE_MALFORMED",raw)
        raw=("S22|1|OBSERVED_UNCERTIFIED|24.0|1|"
             "Same:"+",".join("P"+str(x) for x in range(33)))
        self.code("E_FX_HOST_PROBE_MALFORMED",raw)

    def test_invalid_native_fade_candidate_cannot_consume_inventory(self):
        wrong=dict(self.candidate,host_verified=True)
        self.code("E_FX_NATIVE_CANDIDATE_INVALID",source=wrong)
        wrong=dict(self.candidate,preset="POP")
        self.code("E_FX_NATIVE_CANDIDATE_INVALID",source=wrong)

    def test_unicode_labels_are_diagnostics_only(self):
        report="S22|1|OBSERVED_UNCERTIFIED|24.0|1|Fx:%E9%80%8F%E6%98%8E%E5%BA%A6"
        parsed=inspect_native_fade_host(self.candidate,report)
        self.assertEqual(parsed["components"][0]["property_labels_unverified"],
                         ["透明度"])
        self.assertFalse(parsed["host_verified"])


if __name__=="__main__":
    unittest.main()
