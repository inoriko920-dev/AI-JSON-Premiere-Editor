"""STEP24 exact-selector, single-use Fade readback tests; no Premiere writes."""
from __future__ import annotations

import copy
import unittest
from urllib.parse import quote

from core.fx_native_fade_binding import bind_native_fade_candidate
from core.fx_native_readback_session import FadeReadbackError, FadeReadbackSession
from tests.test_core_fx_native_fade_binding import setup, SEQUENCE, NAME

INVENTORY=("S22|1|OBSERVED_UNCERTIFIED|24.6.3|2|"
           "Mock.Component.Opacity:Opacity;"
           "Mock.Component.Motion:Motion%20Scale")


class ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.fade,self.track,self.refs=setup()
        self.binding=bind_native_fade_candidate(
            self.fade,self.track,self.refs,
            managed_sequence_id=SEQUENCE,managed_sequence_name=NAME)
        self.session=self.make()

    def make(self):
        return FadeReadbackSession(
            self.binding,self.fade,self.track,self.refs,
            managed_sequence_id=SEQUENCE,managed_sequence_name=NAME)

    def report(self,session=None,inventory=INVENTORY):
        s=self.session if session is None else session
        fields=s.host_args
        return ("S24|1|OBSERVED_UNCERTIFIED|"+
                "|".join(fields)+"|"+quote(inventory,safe="~!*'()-._"))

    def blocked(self,code,raw=None,session=None,current=None):
        s=self.session if session is None else session
        payload=self.report(s) if raw is None else raw
        with self.assertRaises(FadeReadbackError) as result:
            s.consume(payload,current_binding=self.binding if current is None else current)
        self.assertEqual(result.exception.code,code)

    def test_exact_nonce_and_clip_selector_return_untrusted_diagnostic(self):
        raw=self.report()
        out=self.session.consume(raw,current_binding=self.binding)
        self.assertEqual(out["status"],
                         "SOURCE_AND_SELECTOR_ECHOED_NOT_HOST_CERTIFIED")
        self.assertEqual(out["binding_sha256"],self.binding["binding_sha256"])
        self.assertEqual(out["component_count"],2)
        self.assertTrue(out["nonce_consumed"])
        self.assertFalse(out["source_node_id_host_verified"])
        self.assertFalse(out["host_verified"])
        self.assertFalse(out["can_assemble"])
        self.assertEqual(out["reported_host_version_untrusted"],"24.6.3")
        self.blocked("E_FX_READBACK_REPLAY",raw=raw)

    def test_two_sessions_use_different_nonces_and_deny_old_response(self):
        old=self.report()
        fresh=self.make()
        self.assertNotEqual(self.session.host_args[0],fresh.host_args[0])
        self.blocked("E_FX_READBACK_STALE_OR_MISMATCHED",old,session=fresh)
        # Failed read attempt burns the nonce, even if later reply correct.
        self.blocked("E_FX_READBACK_REPLAY",self.report(fresh),session=fresh)

    def test_swapped_target_ids_timecodes_and_binding_sha_refused(self):
        for field,evil in ((1,"a"*64),(2,"99999999-abcd-49ef-88ab-123456789abc"),
                           (3,"AIJSON_MANAGED_Other"),(4,"V3"),
                           (5,"1"),(6,"999"),(7,"OtherNode"),(0,"b"*32)):
            s=self.make()
            parts=self.report(s).split("|")
            parts[3+field]=evil
            with self.subTest(field=field):
                self.blocked("E_FX_READBACK_STALE_OR_MISMATCHED",
                             "|".join(parts),session=s)

    def test_wrong_host_version_or_forged_certification_refused(self):
        for inventory in (
            INVENTORY.replace("24.6.3","25.0"),
            INVENTORY.replace("OBSERVED_UNCERTIFIED","CERTIFIED"),
            "S22|1|BLOCKED|CLIP_END_MISMATCH",
            INVENTORY+";Added"
        ):
            s=self.make()
            with self.subTest(inventory=inventory):
                self.blocked("E_FX_HOST_INSPECTION_INVALID",
                             self.report(s,inventory),session=s)

    def test_changed_binding_or_source_ref_cannot_consume_old_report(self):
        invalid=copy.deepcopy(self.binding)
        invalid["selector"]["source_node_id"]="OtherNode"
        self.blocked("E_FX_BINDING_CHANGED",current=invalid)
        self.blocked("E_FX_READBACK_REPLAY")
        invalid=copy.deepcopy(self.binding)
        invalid["host_verified"]=True
        self.blocked("E_FX_BINDING_CHANGED",session=self.make(),current=invalid)

    def test_bad_encoding_oversize_and_missing_content_refused(self):
        for value in (
            "S24|1|CERTIFIED|"+"|".join(self.session.host_args)+"|x",
            self.report().replace("%7C","%7c",1),
            self.report().replace("%7C","%257C",1),
            self.report().replace("%7C","%GG",1),
            "x"*26001,
            33,
        ):
            s=self.make()
            with self.subTest(value=str(value)[:60]):
                with self.assertRaises(FadeReadbackError):
                    s.consume(value,current_binding=self.binding)
                self.blocked("E_FX_READBACK_REPLAY",session=s)

    def test_forged_binding_rejected_when_initializing_challenge(self):
        corrupted=copy.deepcopy(self.binding)
        corrupted["binding_sha256"]="0"*64
        with self.assertRaises(FadeReadbackError) as error:
            FadeReadbackSession(
                corrupted,self.fade,self.track,self.refs,
                managed_sequence_id=SEQUENCE,managed_sequence_name=NAME)
        self.assertEqual(error.exception.code,"E_FX_BINDING_INVALID")

    def test_second_scene_uses_nonzero_start_while_samples_stay_local(self):
        fade,track,refs=setup(index=1)
        binding=bind_native_fade_candidate(
            fade,track,refs,managed_sequence_id=SEQUENCE,
            managed_sequence_name=NAME)
        session=FadeReadbackSession(
            binding,fade,track,refs,managed_sequence_id=SEQUENCE,
            managed_sequence_name=NAME)
        self.assertEqual(session.host_args[5],binding["selector"]["start_ticks"])
        self.assertNotEqual(session.host_args[5],"0")
        self.assertEqual(binding["local_keyframe_samples"][0]["instance_ticks"],"0")
        out=session.consume(self.report(session),current_binding=binding)
        self.assertFalse(out["host_verified"])


if __name__=="__main__":
    unittest.main()
