#!/bin/bash
# Odin's Eye launcher (macOS — double-clickable)
cd "$(dirname "$0")" || exit 1
python3 ccstart.py "$@"
