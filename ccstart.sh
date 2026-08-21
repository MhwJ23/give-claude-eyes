#!/bin/bash
# Odin's Eye launcher (Linux / macOS terminal)
cd "$(dirname "$0")" || exit 1
python3 ccstart.py "$@"
