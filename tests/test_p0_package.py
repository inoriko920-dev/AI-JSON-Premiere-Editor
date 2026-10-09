"""STEP03 deterministic CEP test archive checks, no Premiere dependency."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PILOT = "AI_JSON_Premiere_P0_Pilot"


class PilotPackageTests(unittest.TestCase):
    def test_build_preserves_only_allowlisted_files_and_checksums(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "P0_pilot.zip"
            process = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_p0_pilot.py"),
                 "--output", str(dest)],
                cwd=ROOT, capture_output=True, text=True, timeout=20, check=True)
            self.assertIn("UNSIGNED_TEST_ONLY", process.stdout)
            with zipfile.ZipFile(dest) as z:
                self.assertIsNone(z.testzip())
                names = set(z.namelist())
                expected = {
                    f"{PILOT}/{path}" for path in (
                        "CSXS/manifest.xml", "panel/index.html", "panel/styles.css",
                        "panel/bridge.js", "panel/helper_bridge.js",
                        "panel/app.js", "host/step03.jsx", "helper/handshake.py"
                    )
                }
                self.assertEqual(names, expected | {
                    f"{PILOT}/P0_TEST_ONLY_README.txt",
                    f"{PILOT}/P0_SHA256SUMS.txt"})
                for file in expected:
                    original = (ROOT / file.removeprefix(f"{PILOT}/")).read_bytes()
                    self.assertEqual(z.read(file), original)
                sums = z.read(f"{PILOT}/P0_SHA256SUMS.txt").decode("ascii")
                lines = sums.splitlines()
                self.assertEqual(len(lines), 9)
                for line in lines:
                    digest, rel = line.split("  ", 1)
                    self.assertEqual(hashlib.sha256(z.read(f"{PILOT}/{rel}")).hexdigest(), digest)
                self.assertNotIn(".github", "\n".join(names))
                self.assertNotIn("docs/source", "\n".join(names))
                self.assertNotIn("node_modules", "\n".join(names))
                self.assertNotIn("UI_REFERENCE_FINAL", "\n".join(names))

    def test_build_reproducible_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            outputs = [Path(folder) / "one.zip", Path(folder) / "two.zip"]
            for out in outputs:
                subprocess.run(
                    [sys.executable, str(ROOT / "tools" / "build_p0_pilot.py"),
                     "--output", str(out)],
                    cwd=ROOT, capture_output=True, check=True, timeout=20)
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())

    def test_no_premiere_or_project_mutation_included(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "pilot.zip"
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_p0_pilot.py"),
                 "--output", str(output)], cwd=ROOT, capture_output=True,
                check=True, timeout=20)
            with zipfile.ZipFile(output) as z:
                script = z.read(f"{PILOT}/host/step03.jsx").decode("utf-8")
                html = z.read(f"{PILOT}/panel/index.html").decode("utf-8")
                self.assertNotIn("createSequence(", script)
                self.assertNotIn("importFiles(", script)
                self.assertIn('disabled id="btn-assemble"', html)
                self.assertIn('disabled id="btn-preflight"', html)
                self.assertIn("NOT AN INSTALLER", z.read(
                    f"{PILOT}/P0_TEST_ONLY_README.txt").decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
