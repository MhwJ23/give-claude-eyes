#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Give Claude Eyes — config generator.

Creates config.json (next to this script) with the user's own vision API details.

Usage:
  python setup.py                                            # interactive (asks each value)
  python setup.py --base-url URL --model NAME --api-key KEY  # non-interactive
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

FIELDS = [
    ("base_url", "Base URL (OpenAI-compatible endpoint, e.g. https://api.openai.com/v1)"),
    ("model", "Model name (e.g. gpt-4o, doubao-seed-2-1-pro-260628, a DeepSeek-VL id, ...)"),
    ("api_key", "API key"),
]


def is_interactive():
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Generate config.json for Give Claude Eyes")
    ap.add_argument("--base-url", dest="base_url", default=None,
                    help="vision API base URL")
    ap.add_argument("--model", default=None, help="vision model name")
    ap.add_argument("--api-key", default=None, help="vision API key")
    ap.add_argument("--force", action="store_true", help="overwrite existing config.json")
    args = ap.parse_args()

    values = {"base_url": args.base_url, "model": args.model, "api_key": args.api_key}
    interactive = is_interactive()

    if os.path.exists(CONFIG_PATH) and not args.force:
        print(f"config.json already exists: {CONFIG_PATH}", file=sys.stderr)
        print("Use --force to overwrite, or edit it manually.", file=sys.stderr)
        sys.exit(1)

    print("Give Claude Eyes — vision API config")
    print("(Press Enter to leave a value blank for now; you can edit config.json later.)")
    print()

    for field, label in FIELDS:
        if values[field]:
            shown = "(set)" if field == "api_key" else values[field]
            print(f"{label}: {shown}  (from flag)")
            continue
        if interactive:
            values[field] = input(f"{label}: ").strip()
        else:
            values[field] = ""

    cfg = {"base_url": values["base_url"], "api_key": values["api_key"], "model": values["model"]}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n[written] {CONFIG_PATH}")

    missing = [f for f, _ in FIELDS if not cfg[f]]
    if missing:
        print(f"Note: still empty — fill before use: {', '.join(missing)}")
    else:
        print("Done. Try: python vision.py <image>")


if __name__ == "__main__":
    main()
