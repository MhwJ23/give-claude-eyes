#!/bin/bash
# Give Claude Eyes launcher (Linux / macOS terminal)
cd "$(dirname "$0")" || exit 1
python3 ccstart.py "$@"
