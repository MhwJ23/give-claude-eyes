#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odin's Eye — vision extraction tool (pure visual extraction, no reasoning).

Usage:
  python vision.py <image path> "<what to extract>"          # single image
  python vision.py <image path>                              # single image, full objective description
  python vision.py <folder> "<instruction>" --ext .jpg,.png  # batch
  python vision.py <folder> "<instruction>" --json --out r.json  # batch + structured output

Options:
  --ext        comma-separated extensions to match in batch mode
  --max-batch  max images to process in batch mode (0 = unlimited)
  --json       output a JSON array (each item has file + data/content)
  --out FILE   write results to a file (default: print to stdout)

Config: config.json next to this script; env vars VISION_BASE_URL / VISION_API_KEY /
        VISION_MODEL override the file.
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

DEFAULT_SYSTEM = (
    "You are a pure visual information extraction tool. Output only the objectively "
    "visible information in the image: text (OCR), objects, class labels, bounding-box "
    "coordinates, counts, positions, colors, status, and raw field-by-field data. "
    "Do NOT reason, conclude, advise, judge, or explain."
)

DEFAULT_INSTRUCTION = (
    "List, completely and objectively, all visible information in this image, "
    "item by item: text (including OCR), objects and counts, spatial relationships, "
    "colors, status, etc. Do not omit anything and do not analyze."
)

IMG_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}


def load_config():
    """Read config.json (next to this script) and apply env-var overrides."""
    cfg = {"base_url": "", "api_key": "", "model": ""}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    cfg["base_url"] = os.environ.get("VISION_BASE_URL", cfg["base_url"])
    cfg["api_key"] = os.environ.get("VISION_API_KEY", cfg["api_key"])
    cfg["model"] = os.environ.get("VISION_MODEL", cfg["model"])
    return cfg


def config_ok(cfg):
    """True when all three required fields are present and non-empty."""
    return bool(cfg.get("base_url") and cfg.get("api_key") and cfg.get("model"))


def to_data_url(path):
    ext = os.path.splitext(path)[1].lower()
    mime = IMG_MIME.get(ext, "image/png")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def call_vision(cfg, image_path, instruction):
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": DEFAULT_SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": to_data_url(image_path)}},
                ],
            },
        ],
    }
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg["api_key"],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e}")
    return resp["choices"][0]["message"]["content"]


def list_images(path, exts):
    files = []
    if os.path.isdir(path):
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.isfile(full) and os.path.splitext(name)[1].lower() in exts:
                files.append(full)
    else:
        files.append(path)
    return files


def emit_results(results, json_mode, out_path):
    if json_mode:
        data = []
        for f, content in results:
            item = {"file": f}
            try:
                item["data"] = json.loads(content)
            except Exception:
                item["content"] = content
            data.append(item)
        text = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        parts = []
        n = len(results)
        for i, (f, content) in enumerate(results, 1):
            parts.append(f"===== [{i}/{n}] {f} =====" if n > 1 else f"===== {f} =====")
            parts.append(content)
        text = "\n".join(parts)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"[written] {out_path}")
    else:
        print(text)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(
        description="Odin's Eye — vision extraction tool "
                    "(works with any OpenAI-compatible vision model)"
    )
    ap.add_argument("target", help="image path or folder path")
    ap.add_argument("instruction", nargs="?", default=DEFAULT_INSTRUCTION,
                    help="what to extract (optional; default: full objective description)")
    ap.add_argument("--ext", default=".png,.jpg,.jpeg,.webp,.gif,.bmp",
                    help="comma-separated extensions in batch mode")
    ap.add_argument("--max-batch", type=int, default=0,
                    help="max images in batch mode (0 = unlimited)")
    ap.add_argument("--json", action="store_true", help="output a JSON array")
    ap.add_argument("--out", help="write results to a file")
    args = ap.parse_args()

    cfg = load_config()
    if not config_ok(cfg):
        print(
            "Missing config: run `python setup.py` or edit config.json, "
            "or set VISION_BASE_URL / VISION_API_KEY / VISION_MODEL.",
            file=sys.stderr,
        )
        sys.exit(2)

    exts = {e.strip().lower() for e in args.ext.split(",") if e.strip()}
    files = list_images(args.target, exts)
    if args.max_batch:
        files = files[: args.max_batch]
    if not files:
        print("No image files found.", file=sys.stderr)
        sys.exit(1)

    results = []
    for f in files:
        try:
            out = call_vision(cfg, f, args.instruction)
        except Exception as e:
            out = f"[recognition failed] {e}"
        results.append((f, out))
    emit_results(results, args.json, args.out)


if __name__ == "__main__":
    main()
