#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Odin's Eye — SessionStart hook: read mode.txt and inject the vision-mode note."""
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
MODE_FILE = os.path.join(HERE, "mode.txt")

try:
    with open(MODE_FILE, "r", encoding="utf-8") as f:
        mode = f.read().strip().lower()
except Exception:
    mode = "auto"

if mode == "manual":
    print(
        "[Odin's Eye] vision mode: MANUAL (手动) — "
        "only call the vision tool when the user asks to identify an image."
    )
else:
    print(
        "[Odin's Eye] vision mode: AUTO (自动) — "
        "when an image is relevant, call the vision tool yourself, then analyze."
    )
