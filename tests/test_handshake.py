import json
import subprocess
import sys
import unittest
from pathlib import Path


class Step03HandshakeTests(unittest.TestCase):
    def test_probe_does_not_advertise_mutating_capabilities(self):
        root = Path(__file__).resolve().parents[1]
        run = subprocess.run(
            [sys.executable, str(root / "helper" / "handshake.py"), "--probe"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        data = json.loads(run.stdout)
        self.assertEqual(data["protocol"], "AIJSON_STEP03_P0")
        self.assertEqual(data["status"], "OK")
        self.assertTrue(all(not v for v in data["capabilities"].values()))

    def test_manifest_blocks_non_24_host(self):
        import xml.etree.ElementTree as ET
        root = Path(__file__).resolve().parents[1]
        manifest = ET.parse(root / "CSXS" / "manifest.xml").getroot()
        hosts = manifest.findall("./ExecutionEnvironment/HostList/Host")
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].get("Name"), "PPRO")
        self.assertEqual(hosts[0].get("Version"), "[24.0,24.99]")
        runtime = manifest.find("./ExecutionEnvironment/RequiredRuntimeList/RequiredRuntime")
        self.assertEqual(runtime.get("Name"), "CSXS")

    def test_static_safety_guards(self):
        root = Path(__file__).resolve().parents[1]
        panel = (root / "panel" / "index.html").read_text(encoding="utf-8")
        jsx = (root / "host" / "step03.jsx").read_text(encoding="utf-8")
        self.assertIn('disabled id="btn-assemble"', panel)
        self.assertIn('disabled id="btn-preflight"', panel)
        self.assertNotIn("createSequence(", jsx)
        self.assertNotIn("importFiles(", jsx)


if __name__ == "__main__":
    unittest.main()
