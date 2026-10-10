"""Offline media root, SHA-256 and SRT audit tests; no UI images created."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.media import inspect_media, parse_srt, resolved_path


SRT = b"\xef\xbb\xbf1\r\n00:00:00,000 --> 00:00:05,000\r\nHalo dunia\r\n\r\n" \
      b"2\r\n00:00:05,000 --> 00:00:11,000\r\nDua baris\r\nsubtitle\r\n"
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + (13).to_bytes(4,"big")+b"IHDR"+ \
             (1280).to_bytes(4,"big")+(720).to_bytes(4,"big")+b"\x08\x06\x00\x00\x00"
WAV_HEADER = b"RIFF"+b"\x00"*4+b"WAVEfmt "+b"\x00"*16
MP4_HEADER = b"\x00\x00\x00\x18ftypisom"+b"\x00"*20


def cases():
    return {
      "canvas":{"fps_num":30,"fps_den":1},
      "sources":{
        "srt":{"path":"sub/narasi.srt"},
        "audio":{"path":"audio/narasi.wav"},
        "background":{"path":"video/background.mp4","required":True,"audio_policy":"MUTE"}},
      "assets":{"A001":{"path":"assets/A001.png"}},
      "scenes":[{"assets":[{"asset_id":"A001","start_frame":0,"entry_evidence":{"accuracy":"EXACT_CUE","cue_id":1}}]}]
    }


def codes(report):
    return [x["code"] for x in report["issues"]]


class MediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.edit=cases()
        for name,blob in (("sub/narasi.srt",SRT),("audio/narasi.wav",WAV_HEADER),
                          ("video/background.mp4",MP4_HEADER),("assets/A001.png",PNG_HEADER)):
            p=self.root/name
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(blob)
        for _,meta in self.edit["sources"].items():
            meta["sha256"]=hashlib.sha256((self.root/meta["path"]).read_bytes()).hexdigest()
        self.edit["assets"]["A001"]["sha256"]=hashlib.sha256(PNG_HEADER).hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def inspect(self,edit=None,max_bytes=1024*1024,max_cues=10):
        return inspect_media(self.edit if edit is None else edit,self.root,
                             max_file_bytes=max_bytes,max_srt_cues=max_cues)

    def test_all_files_checked_but_not_ready(self):
        report=self.inspect()
        self.assertEqual(report["status"],"NEEDS_REVIEW",report["issues"])
        self.assertEqual(report["cue_count"],2)
        self.assertEqual(len(report["files"]),4)
        self.assertTrue(all(x["header_ok"] for x in report["files"]))
        self.assertFalse(report["can_assemble"])
        self.assertIn("E_MEDIA_DECODE_UNVERIFIED",codes(report))
        self.assertEqual(report["files"][-1]["width"],1280)

    def test_srt_modified_after_hash_cannot_certify_old_exact_cue(self):
        from core.media import _bounded_hash
        srt=self.root/"sub/narasi.srt"
        changed=SRT.replace(b"00:00:00,000",b"00:00:01,000",1)
        self.assertEqual(len(changed),len(SRT))
        def swap_after_hash(path,limit):
            result=_bounded_hash(path,limit)
            if path==srt:
                srt.write_bytes(changed)
            return result
        with patch("core.media._bounded_hash",side_effect=swap_after_hash):
            report=self.inspect()
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_MEDIA_CHANGED",codes(report))
        self.assertFalse(report["can_assemble"])

    def test_srt_growth_after_hash_stays_within_read_budget(self):
        from core.media import _bounded_hash
        srt=self.root/"sub/narasi.srt"
        max_bytes=8192
        def grow_after_hash(path,limit):
            result=_bounded_hash(path,limit)
            if path==srt:
                srt.write_bytes(SRT+b"x"*(max_bytes+1))
            return result
        with patch("core.media._bounded_hash",side_effect=grow_after_hash):
            report=self.inspect(max_bytes=max_bytes)
        self.assertEqual(report["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_RESOURCE_LIMIT",codes(report))
        self.assertFalse(report["can_assemble"])

    def test_utf8_bom_multiline_srt(self):
        cues=parse_srt(SRT,max_cues=10)
        self.assertEqual(len(cues),2)
        self.assertEqual(cues[1]["end_ms"],11000)

    def test_invalid_cue_timestamp_fails(self):
        with self.assertRaises(ValueError):
            parse_srt(b"1\n00:00:05,000 --> 00:00:04,000\nBad\n",max_cues=3)

    def test_repeated_cue_id_fails(self):
        with self.assertRaises(ValueError):
            parse_srt(SRT+b"\n\n1\n00:00:12,000 --> 00:00:13,000\nAgain",max_cues=5)

    def test_srt_wrong_encoding_fails(self):
        with self.assertRaises(ValueError):
            parse_srt(b"\xff\xfe\x00",max_cues=3)

    def test_missing_cue_reference_errors(self):
        self.edit["scenes"][0]["assets"][0]["entry_evidence"]["cue_id"]=99
        self.assertIn("E_SRT_AMBIGUOUS",codes(self.inspect()))

    def test_missing_media_blocks(self):
        (self.root/"audio/narasi.wav").unlink()
        self.assertIn("E_MEDIA_MISSING",codes(self.inspect()))

    def test_hash_mismatch_blocks(self):
        self.edit["sources"]["audio"]["sha256"]="f"*64
        self.assertIn("E_MEDIA_HASH",codes(self.inspect()))

    def test_missing_declared_hash_is_review(self):
        del self.edit["assets"]["A001"]["sha256"]
        self.assertIn("E_MEDIA_HASH_UNPINNED",codes(self.inspect()))
        self.assertEqual(self.inspect()["status"],"NEEDS_REVIEW")

    def test_wrong_png_header_blocks(self):
        (self.root/"assets/A001.png").write_bytes(b"not a png")
        self.edit["assets"]["A001"]["sha256"]=hashlib.sha256(b"not a png").hexdigest()
        self.assertIn("E_MEDIA_FORMAT",codes(self.inspect()))

    def test_file_over_budget_fails(self):
        self.assertIn("E_RESOURCE_LIMIT",codes(self.inspect(max_bytes=10)))

    def test_explicit_root_required(self):
        self.assertIn("E_CONFIG_LIMITS_UNVERIFIED",
                      codes(inspect_media(self.edit,self.root,max_file_bytes=0,max_srt_cues=10)))

    def test_traversal_absolute_windows_and_unc_rejected(self):
        for rel in ("../secret.png","C:\\private\\secret.png",
                    "C:secret.png","\\\\server\\share\\asset.png",
                    "/etc/passwd","sub/../../secret.png","a//b.png"):
            with self.assertRaises(ValueError,msg=rel):
                resolved_path(self.root,rel)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            leak=Path(other)/"leak.png"
            leak.write_bytes(PNG_HEADER)
            symlink=self.root/"assets"/"escape.png"
            try:
                symlink.symlink_to(leak)
            except (OSError,NotImplementedError):
                self.skipTest("symlinks not supported in this Windows runner")
            with self.assertRaises(ValueError):
                resolved_path(self.root,"assets/escape.png")

    def test_valid_nested_relative_path(self):
        self.assertEqual(resolved_path(self.root,"sub\\narasi.srt"),
                         (self.root/"sub/narasi.srt").resolve())

    def test_missing_srt_cannot_claim_exact_cue(self):
        (self.root/"sub/narasi.srt").unlink()
        result=self.inspect()
        self.assertEqual(result["status"],"PREFLIGHT_FAIL")
        self.assertIn("E_SRT_AMBIGUOUS",codes(result))


if __name__=="__main__":
    unittest.main()
