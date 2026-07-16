#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_SCRIPTS = PLUGIN_ROOT / "scripts"
if str(PLUGIN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS))

from project_intel_lib.design_documents import main


if __name__ == "__main__":
    raise SystemExit(main())
