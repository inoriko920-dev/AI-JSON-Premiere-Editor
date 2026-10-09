"""Import candidate inventory security and change-detection regression tests."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from core.import_snapshot import (
    ImportSnapshotError, prepare_media_snapshot, recheck_media_snapshot
)

PNG = (b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4, "big") + b"IHDR" +
       (960).to_bytes(4, "big") + (540).to_bytes(4, "big") + b"\x08\x06\x00\x00\x00")
WAV = b"RIFF\x10\x00\x00\x00WAVEfmt " + b"\x00" * 16
MP4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 20
SRT = b"1\n00:00:00,000 --> 00:00:01,000\nOriginal cue\n"


class ImportSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.edit = {
            "project_id": "TEST_IMPORT",
            "validation": {"status": "READY", "issues": []},
            "sources": {},
            "assets": {"A001": {"path": "assets/A001.png"},
                       "A002": {"path": "assets/A002.png"}}
        }
        for kind, path, data in (
            ("srt", "narration.srt", SRT),
            ("audio", "audio.wav", WAV),
            ("background", "background.mp4", MP4)
        ):
            (self.root / path).write_bytes(data)
            self.edit["sources"][kind] = {
                "path": path, "sha256": hashlib.sha256(data).hexdigest()
            }
        for aid in ("A001", "A002"):
            p = self.root / "assets" / (aid + ".png")
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(PNG)
            self.edit["assets"][aid]["sha256"] = hashlib.sha256(PNG).hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self):
        return prepare_media_snapshot(
            self.edit, self.root, max_file_bytes=100000,
            max_import_items=10
        )

    def assert_code(self, code):
        with self.assertRaises(ImportSnapshotError) as ex:
            self.snapshot()
        self.assertEqual(ex.exception.code, code)

    def test_inventory_has_all_sources_and_unique_assets(self):
        r = self.snapshot()
        self.assertEqual(r["status"], "CANDIDATE_NOT_AUTHORIZED")
        self.assertFalse(r["can_import"])
        self.assertFalse(r["can_assemble"])
        self.assertEqual(r["item_count"], 5)
        self.assertEqual(r["import_count"], 4)
        self.assertEqual(r["items"][0]["kind"], "srt")
        self.assertFalse(r["items"][0]["import_to_premiere"])
        self.assertTrue(all(len(x["sha256"]) == 64 for x in r["items"]))
        self.assertTrue(recheck_media_snapshot(r, max_file_bytes=100000))

    def test_deterministic_digest_includes_paths_bytes_and_mtime(self):
        a, b = self.snapshot(), self.snapshot()
        self.assertEqual(a["inventory_sha256"], b["inventory_sha256"])
        self.assertEqual(a["items"], b["items"])

    def test_stale_file_rejected_even_same_length(self):
        r = self.snapshot()
        (self.root / "audio.wav").write_bytes(b"0" * len(WAV))
        self.assertFalse(recheck_media_snapshot(r, max_file_bytes=100000))

    def test_json_ready_claim_never_authorizes_import(self):
        r = self.snapshot()
        self.assertFalse(r["can_import"])

    def test_unpinned_png_rejected(self):
        del self.edit["assets"]["A001"]["sha256"]
        self.assert_code("E_MEDIA_HASH_UNPINNED")

    def test_hash_mismatch_rejected(self):
        self.edit["sources"]["audio"]["sha256"] = "a" * 64
        self.assert_code("E_MEDIA_HASH")

    def test_deleted_required_media_rejected(self):
        (self.root / "background.mp4").unlink()
        self.assert_code("E_MEDIA_MISSING")

    def test_rejects_path_escape_before_any_import(self):
        self.edit["assets"]["A001"]["path"] = "../escape.png"
        self.assert_code("E_MEDIA_PATH")

    def test_duplicate_path_for_two_assets_fails_closed(self):
        self.edit["assets"]["A002"]["path"] = self.edit["assets"]["A001"]["path"]
        self.assert_code("E_MEDIA_ALIAS_AMBIGUOUS")

    def test_invalid_role_extension_rejected(self):
        self.edit["sources"]["audio"]["path"] = "background.mp4"
        self.assert_code("E_MEDIA_FORMAT")

    def test_rejects_header_spoofed_as_png(self):
        bad = b"NOT PNG BYTES"
        (self.root / "assets" / "A001.png").write_bytes(bad)
        self.edit["assets"]["A001"]["sha256"] = hashlib.sha256(bad).hexdigest()
        self.assert_code("E_MEDIA_FORMAT")

    def test_resource_limits_are_developer_explicit(self):
        with self.assertRaises(ImportSnapshotError) as ex:
            prepare_media_snapshot(self.edit, self.root, max_file_bytes=10,
                                   max_import_items=10)
        self.assertEqual(ex.exception.code, "E_RESOURCE_LIMIT")

    def test_tampered_digest_and_snapshot_array_refused(self):
        r = self.snapshot()
        r["inventory_sha256"] = "0" * 64
        self.assertFalse(recheck_media_snapshot(r, max_file_bytes=100000))
        r = self.snapshot()
        r["items"][0]["absolute_path"] = "C:/other/malicious.srt"
        self.assertFalse(recheck_media_snapshot(r, max_file_bytes=100000))

    def test_symlink_outside_project_root_rejected(self):
        with tempfile.TemporaryDirectory() as outer:
            path = Path(outer) / "out.png"
            path.write_bytes(PNG)
            link = self.root / "assets" / "out.png"
            try:
                link.symlink_to(path)
            except (OSError, NotImplementedError):
                self.skipTest("symlink unavailable on this Windows runner")
            self.edit["assets"]["A002"]["path"] = "assets/out.png"
            self.assert_code("E_MEDIA_PATH")

if __name__ == "__main__":
    unittest.main()
