"""Run STEP04 read-only validator under Python -I.

Invoked by a trusted CEP Node bridge with an explicit absolute interpreter.
The script location is fixed inside the installed CEP extension. It does not
parse shell commands, dynamically import user files, or mutate a Premiere project.
"""
from __future__ import annotations

import sys
from pathlib import Path

EXTENSION_ROOT = Path(__file__).resolve().parent.parent
if not (EXTENSION_ROOT / "core" / "contracts.py").is_file():
    raise SystemExit(5)
sys.path.insert(0, str(EXTENSION_ROOT))

from core.validate_cli import run  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run())
