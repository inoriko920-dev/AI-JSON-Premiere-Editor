import json
import subprocess
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


class Step03HandshakeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_probe_does_not_advertise_mutating_capabilities(self):
        run = subprocess.run(
            [sys.executable, "-I", "-B",
             str(self.root / "helper" / "handshake.py"), "--probe"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        data = json.loads(run.stdout)
        self.assertEqual(data["protocol"], "AIJSON_STEP03_P0")
        self.assertEqual(data["status"], "OK")
        self.assertEqual(data["helper_version"], "0.0.3")
        self.assertTrue(all(v is False for v in data["capabilities"].values()))

    def test_manifest_limits_host_and_enables_node_securely(self):
        manifest = ET.parse(self.root / "CSXS" / "manifest.xml").getroot()
        hosts = manifest.findall("./ExecutionEnvironment/HostList/Host")
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].get("Name"), "PPRO")
        self.assertEqual(hosts[0].get("Version"), "[24.0,24.99]")
        runtime = manifest.find("./ExecutionEnvironment/RequiredRuntimeList/RequiredRuntime")
        self.assertEqual(runtime.get("Name"), "CSXS")
        cefs = manifest.findall(
            "./DispatchInfoList/Extension/DispatchInfo/Resources/CEFCommandLine/Parameter"
        )
        self.assertEqual([x.text for x in cefs], ["--enable-nodejs", "--mixed-context"])

    def test_static_safety_guards(self):
        panel = (self.root / "panel" / "index.html").read_text(encoding="utf-8")
        jsx = (self.root / "host" / "step03.jsx").read_text(encoding="utf-8")
        js = (self.root / "panel" / "helper_bridge.js").read_text(encoding="utf-8")
        self.assertIn('disabled id="btn-assemble"', panel)
        self.assertIn('disabled id="btn-preflight"', panel)
        self.assertIn('id="btn-helper" type="button" disabled', panel)
        self.assertNotIn("createSequence(", jsx)
        self.assertNotIn("importFiles(", jsx)
        self.assertIn("shell:false", js)
        self.assertIn('maxBuffer:MAX_STDOUT', js)


if __name__ == "__main__":
    unittest.main()
