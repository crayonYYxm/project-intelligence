#!/usr/bin/env python3
"""Thin, backwards-compatible Project Intelligence CLI facade.

The implementation lives in ``project_intel_lib.application``.  Executing the
application source in this module namespace deliberately preserves historical
direct imports and monkey-patching of public helpers while keeping this entry
file limited to loading and dispatch.
"""

from pathlib import Path


_APPLICATION = Path(__file__).resolve().parent / "project_intel_lib" / "application.py"
exec(compile(_APPLICATION.read_text(encoding="utf-8"), str(_APPLICATION), "exec"), globals(), globals())
