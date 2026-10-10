"""STEP24 single-use, exact-selector-bound Premiere read-only diagnostics.

Nonce prevents accepting a previous session's *unchanged* response; it is not
a cryptographic signature, and a malicious/fake Premiere response cannot
certify a native Opacity parameter. This module never authorizes host edits.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import re
import secrets
from typing import Any
from urllib.parse import quote, unquote

from .fx_native_fade_binding import (
    FadeBindingError, validate_native_fade_binding)
from .fx_native_host_probe import (
    NativeHostInspectError, inspect_native_fade_host)

_NONCE = re.compile(r"[a-f0-9]{32}\Z")
_ALLOWED_SAFE = "~!*'()-._"


class FadeReadbackError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class FadeReadbackSession:
    """One-shot challenge, rebound to the same trusted STEP23 candidate inputs.

    No request is accepted twice, even after a parse exception. A fresh session
    is needed for a second readback. Actual Premiere G3 is still unverified.
    """
    def __init__(
        self, binding: dict[str, Any], fade: dict[str, Any],
        track_plan: dict[str, Any], media_refs: list[dict[str, str]], *,
        managed_sequence_id: str, managed_sequence_name: str,
    ) -> None:
        try:
            validate_native_fade_binding(
                binding, fade, track_plan, media_refs,
                managed_sequence_id=managed_sequence_id,
                managed_sequence_name=managed_sequence_name)
        except (FadeBindingError, TypeError, ValueError) as error:
            raise FadeReadbackError("E_FX_BINDING_INVALID") from error
        self._binding = deepcopy(binding)
        self._fade = deepcopy(fade)
        self._track = deepcopy(track_plan)
        self._refs = deepcopy(media_refs)
        self._id = managed_sequence_id
        self._name = managed_sequence_name
        self._nonce = secrets.token_hex(16)
        self._used = False
        selector = binding["selector"]
        self._args = (
            self._nonce, binding["binding_sha256"], selector["sequence_id"],
            selector["sequence_name"], selector["track"],
            selector["start_ticks"], selector["end_ticks"],
            selector["source_node_id"],
        )

    @property
    def host_args(self) -> tuple[str, ...]:
        """Forward unchanged to STEP24 .inspect(...), no shell and no writes."""
        return self._args

    def consume(
        self, reply: str, *, current_binding: dict[str, Any],
    ) -> dict[str, Any]:
        if self._used:
            raise FadeReadbackError("E_FX_READBACK_REPLAY")
        # Consume challenge before any untrusted parsing or exceptions.
        self._used = True
        try:
            validate_native_fade_binding(
                current_binding, self._fade, self._track, self._refs,
                managed_sequence_id=self._id,
                managed_sequence_name=self._name)
        except (FadeBindingError, TypeError, ValueError) as error:
            raise FadeReadbackError("E_FX_BINDING_CHANGED") from error
        if current_binding != self._binding:
            raise FadeReadbackError("E_FX_BINDING_CHANGED")
        if type(reply) is not str or not 0 < len(reply) <= 26000:
            raise FadeReadbackError("E_FX_READBACK_MALFORMED")
        if reply.startswith("S24|1|BLOCKED|"):
            raise FadeReadbackError("E_FX_READBACK_BLOCKED")
        fields = reply.split("|")
        if (len(fields) != 12 or fields[:3] !=
                ["S24", "1", "OBSERVED_UNCERTIFIED"] or
                tuple(fields[3:11]) != self._args):
            raise FadeReadbackError("E_FX_READBACK_STALE_OR_MISMATCHED")
        encoded = fields[11]
        if not encoded or len(encoded) > 24576 or "|" in encoded:
            raise FadeReadbackError("E_FX_READBACK_MALFORMED")
        try:
            s22 = unquote(encoded, encoding="utf-8", errors="strict")
        except UnicodeError as error:
            raise FadeReadbackError("E_FX_READBACK_MALFORMED") from error
        if quote(s22, safe=_ALLOWED_SAFE) != encoded:
            raise FadeReadbackError("E_FX_READBACK_MALFORMED")
        try:
            details = inspect_native_fade_host(self._fade, s22)
        except NativeHostInspectError as error:
            raise FadeReadbackError("E_FX_HOST_INSPECTION_INVALID") from error
        return {
            "schema_version": "native-fade-readback-diagnostic-v1",
            "status": "SOURCE_AND_SELECTOR_ECHOED_NOT_HOST_CERTIFIED",
            "binding_sha256": self._binding["binding_sha256"],
            "response_sha256": sha256(reply.encode("utf-8")).hexdigest(),
            "inventory_sha256": details["inventory_sha256"],
            "reported_host_version_untrusted":
                details["reported_host_version_untrusted"],
            "component_count": len(details["components"]),
            "nonce_consumed": True,
            "source_node_id_host_verified": False,
            "clip_end_host_verified": False,
            "parameter_matchname_verified": False,
            "time_coordinate_verified": False,
            "readback_certified": False,
            "host_verified": False,
            "can_assemble": False,
        }
