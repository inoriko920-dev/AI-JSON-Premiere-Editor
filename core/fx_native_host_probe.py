"""STEP22 fail-closed parser for read-only Premiere Opacity component inventory.

Never interpret local/mock inventory as host-certified evidence or as
permission to mutate a timeline. The inspected component/parameter names are
opaque diagnostics; the real Premiere 24.x matchNames/Time coordinate system
must still be verified through a separate host gate.
"""
from __future__ import annotations

from hashlib import sha256
import re
from typing import Any
from urllib.parse import quote, unquote

from .fx_native_fade import validate_native_fade_candidate, NativeFadeError


class NativeHostInspectError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


_NAME_ENCODING = re.compile(r"[A-Za-z0-9_.!~*'()%-]{1,180}\Z")
_HOST_VERSION = re.compile(r"24\.[0-9]+(?:\.[0-9]+){0,2}\Z")


def _component_name(token: str) -> str:
    if not _NAME_ENCODING.fullmatch(token):
        raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
    try:
        value = unquote(token, encoding="utf-8", errors="strict")
    except UnicodeError as error:
        raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED") from error
    if (not 1 <= len(value) <= 80 or
            any(ord(c) < 32 or ord(c) == 127 for c in value) or
            "%" in value or
            quote(value, safe="~!*'()-._") != token):
        raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
    return value


def inspect_native_fade_host(
    candidate: dict[str, Any], raw_host_inventory: str
) -> dict[str, Any]:
    """Bind a B02 FADE candidate to a diagnostic-only component readback.

    No matchName heuristic, locale-derived automation, or mock pass can change
    host_verified/can_assemble. Values are intentionally never read or set.
    """
    try:
        validate_native_fade_candidate(candidate)
    except (NativeFadeError, TypeError, ValueError) as error:
        raise NativeHostInspectError("E_FX_NATIVE_CANDIDATE_INVALID") from error
    if (type(raw_host_inventory) is not str or
            not 0 < len(raw_host_inventory) <= 8192):
        raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
    if raw_host_inventory.startswith("S22|1|BLOCKED|"):
        raise NativeHostInspectError("E_FX_HOST_PROBE_BLOCKED")
    parts = raw_host_inventory.split("|")
    if (len(parts) != 6 or parts[:3] !=
            ["S22", "1", "OBSERVED_UNCERTIFIED"] or
            not _HOST_VERSION.fullmatch(parts[3]) or
            not re.fullmatch(r"[1-9]|1[0-9]|20", parts[4])):
        raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
    count = int(parts[4])
    components = parts[5].split(";")
    if len(components) != count:
        raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
    parsed = []
    unique = set()
    for row in components:
        if row.count(":") != 1:
            raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
        name, properties = row.split(":")
        match_name = _component_name(name)
        if match_name in unique:
            raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
        unique.add(match_name)
        raw_properties = [] if properties == "" else properties.split(",")
        if len(raw_properties) > 32:
            raise NativeHostInspectError("E_FX_HOST_PROBE_MALFORMED")
        decoded = [_component_name(prop) for prop in raw_properties]
        parsed.append({"match_name_unverified": match_name,
                       "property_labels_unverified": decoded})
    return {
        "schema_version": "native-fade-host-inventory-candidate-v1",
        "status": "HOST_COMPONENTS_OBSERVED_NOT_CERTIFIED",
        "candidate_sha256": candidate["candidate_sha256"],
        "reported_host_version_untrusted": parts[3],
        "inventory_sha256": sha256(raw_host_inventory.encode("utf-8")).hexdigest(),
        "components": parsed,
        "host_component_match_name": None,
        "host_parameter_match_name": None,
        "time_coordinate_verified": False,
        "opacity_value_units_verified": False,
        "readback_verified": False,
        "host_verified": False,
        "can_assemble": False,
    }
