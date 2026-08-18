#!/bin/bash
# Give Claude Eyes launcher (macOS — double-clickable)
cd "$(dirname "$0")" || exit 1
python3 ccstart.py "$@"
