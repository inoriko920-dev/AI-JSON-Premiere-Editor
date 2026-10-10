"""Import candidate inventory security and change-detection regression tests."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
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

    def test_descriptor_inode_replacement_mid_hash_rejected_at_source(self):
        # Simulated inode swap (same content/size/mtime) via one fstat result.
        # Uses existing WAV fixture; no new PNG or visual is generated.
        original=os.fstat
        calls=[0]
        def swapped_fstat(fd):
            result=original(fd)
            calls[0]+=1
            if calls[0] == 2:
                return SimpleNamespace(
                    st_mode=result.st_mode,st_dev=result.st_dev,
                    st_ino=result.st_ino+1,st_size=result.st_size,
                    st_mtime_ns=result.st_mtime_ns,
                    st_ctime_ns=result.st_ctime_ns)
            return result
        with patch("core.import_snapshot.os.fstat",side_effect=swapped_fstat):
            self.assert_code("E_MEDIA_CHANGED_DURING_SNAPSHOT")
        self.assertGreaterEqual(calls[0],2)

    def test_recheck_fails_closed_on_inode_swap_during_read(self):
        r=self.snapshot()
        original=os.fstat
        calls=[0]
        def switched(fd):
            result=original(fd)
            calls[0]+=1
            if calls[0]==2:
                return SimpleNamespace(
                    st_mode=result.st_mode,st_dev=result.st_dev,
                    st_ino=result.st_ino+101,st_size=result.st_size,
                    st_mtime_ns=result.st_mtime_ns,
                    st_ctime_ns=result.st_ctime_ns)
            return result
        with patch("core.import_snapshot.os.fstat",side_effect=switched):
            self.assertFalse(recheck_media_snapshot(r,max_file_bytes=100000))
        self.assertGreaterEqual(calls[0],2)
        self.assertTrue(recheck_media_snapshot(r,max_file_bytes=100000))

    def test_same_bytes_same_mtime_inode_swap_after_snapshot_is_stale(self):
        snapshot=self.snapshot()
        audio=self.root/"audio.wav"
        old=audio.stat()
        data=audio.read_bytes()
        replacement=self.root/"new-audio.wav"
        replacement.write_bytes(data)
        os.utime(replacement,ns=(old.st_atime_ns,old.st_mtime_ns))
        os.replace(replacement,audio)
        fresh=audio.stat()
        # Every field available to the old recheck still agrees. This is
        # nevertheless a different source file, which must invalidate it.
        self.assertEqual(audio.read_bytes(),data)
        self.assertEqual(fresh.st_size,old.st_size)
        self.assertEqual(fresh.st_mtime_ns,old.st_mtime_ns)
        self.assertTrue((fresh.st_dev,fresh.st_ino,fresh.st_ctime_ns) !=
                        (old.st_dev,old.st_ino,old.st_ctime_ns))
        self.assertFalse(recheck_media_snapshot(snapshot,max_file_bytes=100000))
        # A fresh snapshot correctly binds the replacement, but remains
        # non-authorizing until the host gate independently succeeds.
        replacement_snapshot=self.snapshot()
        self.assertTrue(recheck_media_snapshot(replacement_snapshot,
                                               max_file_bytes=100000))
        self.assertFalse(replacement_snapshot["can_import"])
        self.assertNotEqual(snapshot["inventory_sha256"],
                            replacement_snapshot["inventory_sha256"])

    def test_identity_fields_are_in_snapshot_digest_and_required_on_recheck(self):
        snapshot=self.snapshot()
        self.assertTrue(recheck_media_snapshot(snapshot,max_file_bytes=100000))
        for item in snapshot["items"]:
            for key in ("device_id","file_id","ctime_ns"):
                self.assertIs(type(item[key]),int)
                self.assertGreaterEqual(item[key],0)
        for missing in ("device_id","file_id","ctime_ns"):
            with self.subTest(missing=missing):
                copied=self.snapshot()
                del copied["items"][0][missing]
                # Even an internally consistent legacy-style manifest
                # cannot claim to preserve original file identity.
                import json
                copied["inventory_sha256"]=hashlib.sha256(json.dumps(
                    copied["items"],sort_keys=True,ensure_ascii=False,
                    separators=(",",":"),allow_nan=False
                ).encode("utf-8")).hexdigest()
                self.assertFalse(recheck_media_snapshot(
                    copied,max_file_bytes=100000))

    def test_recheck_rejects_promoted_or_inconsistent_authority_flags(self):
        snapshot=self.snapshot()
        self.assertTrue(recheck_media_snapshot(snapshot,max_file_bytes=100000))
        for field,value in (
            ("status","READY"),
            ("status","CANDIDATE_EXECUTABLE"),
            ("can_import",True),
            ("can_assemble",True),
            ("import_count",0),
            ("import_count",True),
            ("item_count",True),
        ):
            with self.subTest(field=field,value=value):
                tampered=copy.deepcopy(snapshot)
                tampered[field]=value
                self.assertFalse(recheck_media_snapshot(
                    tampered,max_file_bytes=100000))
        # Mutating a detached snapshot cannot grant import or assembly.
        self.assertFalse(snapshot["can_import"])
        self.assertFalse(snapshot["can_assemble"])

    def test_recheck_rejects_role_tampering_even_with_recomputed_digest(self):
        snapshot=self.snapshot()
        for role, field, value in (
            ("SOURCE_SRT","import_to_premiere",True),
            ("SOURCE_AUDIO","import_to_premiere",False),
            ("SOURCE_BACKGROUND","kind","png"),
            ("ASSET_A001","kind","srt"),
            ("ASSET_A001","item_id","SOURCE_AUDIO"),
        ):
            with self.subTest(role=role,field=field):
                tampered=copy.deepcopy(snapshot)
                entry=next(x for x in tampered["items"] if x["item_id"]==role)
                entry[field]=value
                tampered["import_count"]=sum(
                    x["import_to_premiere"] for x in tampered["items"])
                tampered["inventory_sha256"]=hashlib.sha256(
                    json.dumps(tampered["items"],sort_keys=True,
                               ensure_ascii=False,separators=(",",":"),
                               allow_nan=False).encode("utf-8")).hexdigest()
                self.assertFalse(recheck_media_snapshot(
                    tampered,max_file_bytes=100000))
        self.assertTrue(recheck_media_snapshot(snapshot,max_file_bytes=100000))

    def test_snapshot_hash_never_requests_more_than_remaining_read_budget(self):
        # The caller may cap reads to a few dozen bytes. Even a small file
        # must not cause the hasher to request an unconditional 1-MiB block.
        from core.import_snapshot import _stable_media_hash
        path=self.root/"audio.wav"
        limit=len(WAV)+5
        observed=[]
        real_fdopen=os.fdopen

        class RecordingStream:
            def __init__(self, stream):
                self.stream=stream
            def __enter__(self):
                self.stream.__enter__()
                return self
            def __exit__(self, *args):
                return self.stream.__exit__(*args)
            def fileno(self):
                return self.stream.fileno()
            def read(self, requested):
                observed.append(requested)
                self_test.assertLessEqual(requested,limit+1)
                return self.stream.read(requested)

        self_test=self
        with patch("core.import_snapshot.os.fdopen",side_effect=lambda fd,mode:
                   RecordingStream(real_fdopen(fd,mode))):
            digest,size,header,_=_stable_media_hash(path,limit)
        self.assertEqual(size,len(WAV))
        self.assertEqual(digest,hashlib.sha256(WAV).hexdigest())
        self.assertTrue(observed)
        self.assertEqual(header[:4],b"RIFF")

    def test_snapshot_hash_rejects_file_growth_within_bounded_read(self):
        from core.import_snapshot import _stable_media_hash
        path=self.root/"audio.wav"
        limit=len(WAV)+4
        original_open=os.open
        injected=[False]
        def grow_before_open(file, flags, *args, **kwargs):
            if Path(file)==path and not injected[0]:
                injected[0]=True
                path.write_bytes(WAV+b"x"*(limit+10))
            return original_open(file,flags,*args,**kwargs)
        with patch("core.import_snapshot.os.open",side_effect=grow_before_open):
            with self.assertRaisesRegex(ValueError,"E_RESOURCE_LIMIT"):
                _stable_media_hash(path,limit)
        self.assertTrue(injected[0])

    def test_stale_file_rejected_even_same_length(self):
        r = self.snapshot()
        (self.root / "audio.wav").write_bytes(b"0" * len(WAV))
        self.assertFalse(recheck_media_snapshot(r, max_file_bytes=100000))

    def test_json_ready_claim_never_authorizes_import(self):
        r = self.snapshot()
        self.assertFalse(r["can_import"])

    def test_valid_dotted_and_underscored_asset_id_uses_same_contract(self):
        self.edit["assets"]["A.extra_part-02"] = self.edit["assets"].pop("A002")
        result=self.snapshot()
        self.assertTrue(any(x["item_id"]=="ASSET_A.extra_part-02" for x in result["items"]))

    def test_mixed_type_asset_keys_fail_with_structured_contract_error(self):
        # Do not let sorted(dict) raise a raw TypeError on unexpected
        # non-string keys supplied to the direct snapshot API.
        for invalid in (None, 3, False):
            with self.subTest(asset_key=invalid):
                self.edit["assets"][invalid] = {
                    "path": "assets/A002.png",
                    "sha256": hashlib.sha256(PNG).hexdigest()
                }
                self.assert_code("E_IMPORT_CONTRACT_INVALID")
                del self.edit["assets"][invalid]
        self.assertTrue(recheck_media_snapshot(self.snapshot(),
                                               max_file_bytes=100000))

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

    def test_hard_link_asset_alias_fails_even_with_distinct_paths(self):
        original=self.root/"assets"/"A001.png"
        alias=self.root/"assets"/"A002.png"
        alias.unlink()
        try:
            os.link(original,alias)
        except (OSError, NotImplementedError):
            self.skipTest("filesystem hard links unavailable")
        self.assertNotEqual(original.resolve(),alias.resolve())
        self.assertEqual(original.stat().st_ino,alias.stat().st_ino)
        self.assert_code("E_MEDIA_ALIAS_AMBIGUOUS")

    def test_simulated_hard_link_identity_alias_fails_on_all_platforms(self):
        # The regression must execute even when the Windows runner cannot
        # create hard links on its temporary filesystem.
        from core.import_snapshot import _stable_media_hash
        original=_stable_media_hash
        existing=(self.root/"assets"/"A001.png").stat()
        def same_inode(path,budget):
            digest,size,header,metadata=original(path,budget)
            if Path(path).name=="A002.png":
                metadata=SimpleNamespace(
                    st_dev=existing.st_dev,st_ino=existing.st_ino,
                    st_size=metadata.st_size,
                    st_mtime_ns=metadata.st_mtime_ns,
                    st_ctime_ns=metadata.st_ctime_ns)
            return digest,size,header,metadata
        with patch("core.import_snapshot._stable_media_hash",side_effect=same_inode):
            self.assert_code("E_MEDIA_ALIAS_AMBIGUOUS")

    def test_recheck_rejects_forged_duplicate_file_ids_before_file_io(self):
        snapshot=self.snapshot()
        entries=snapshot["items"]
        first=next(x for x in entries if x["item_id"]=="ASSET_A001")
        second=next(x for x in entries if x["item_id"]=="ASSET_A002")
        second["device_id"]=first["device_id"]
        second["file_id"]=first["file_id"]
        snapshot["inventory_sha256"]=hashlib.sha256(
            json.dumps(entries,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False,allow_nan=False).encode("utf-8")
        ).hexdigest()
        with patch("core.import_snapshot._stable_media_hash",
                   side_effect=AssertionError("must reject before filesystem reads")):
            self.assertFalse(recheck_media_snapshot(snapshot,max_file_bytes=100000))

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

    def test_import_budget_rejected_before_asset_sort_or_source_read(self):
        # Two fixed import slots are audio and background; SRT is not
        # imported. Any additional asset beyond the caller's item budget
        # must fail before even sorting untrusted asset identifiers.
        self.edit["assets"]["A003"] = {"path": "missing-extra.png",
                                        "sha256": "0"*64}
        with patch("builtins.sorted", side_effect=AssertionError(
                "asset list must never be sorted past resource cap")), \
             patch("core.import_snapshot._stable_media_hash", side_effect=AssertionError(
                 "files must never be hashed past resource cap")):
            with self.assertRaises(ImportSnapshotError) as error:
                prepare_media_snapshot(
                    self.edit, self.root, max_file_bytes=100000,
                    max_import_items=4)
        self.assertEqual(error.exception.code, "E_RESOURCE_LIMIT")

    def test_exact_import_budget_still_accepts_two_assets_and_two_sources(self):
        snapshot=prepare_media_snapshot(
            self.edit, self.root, max_file_bytes=100000,
            max_import_items=4)
        self.assertEqual(snapshot["import_count"], 4)
        self.assertEqual(snapshot["item_count"], 5)
        self.assertFalse(snapshot["can_import"])
        self.assertFalse(snapshot["can_assemble"])
        self.assertTrue(recheck_media_snapshot(snapshot,max_file_bytes=100000))

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
