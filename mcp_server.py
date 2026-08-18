#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Give Claude Eyes — MCP (Model Context Protocol) server.

Exposes vision tools so a text-only Claude Code model can "see" images through any
OpenAI-compatible vision API. Zero-dependency; speaks newline-delimited JSON-RPC 2.0
over stdio.

Run as a stdio server (configure in Claude Code via /mcp or .mcp.json):
    python mcp_server.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import vision  # noqa: E402

SERVER_NAME = "give-claude-eyes"
SERVER_VERSION = "1.0.0"

TOOLS = [
    {
        "name": "vision_describe",
        "description": (
            "Extract objective visual information from a single image via a vision "
            "model. Returns OCR text, objects, counts, colors, positions, status, etc. "
            "No reasoning — the caller (you) does the analysis."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file.",
                },
                "instruction": {
                    "type": "string",
                    "description": (
                        "What to extract (optional). Defaults to a full objective "
                        "description. Examples: 'OCR all text', 'count the objects', "
                        "'output JSON with main color and shape'."
                    ),
                },
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "vision_batch",
        "description": (
            "Extract objective visual information from every image in a folder via a "
            "vision model. Returns per-image results. No reasoning."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder": {
                    "type": "string",
                    "description": "Path to a folder containing images.",
                },
                "instruction": {
                    "type": "string",
                    "description": "What to extract from each image (optional).",
                },
                "ext": {
                    "type": "string",
                    "description": (
                        "Comma-separated extensions to match (optional). "
                        "Default: .png,.jpg,.jpeg,.webp,.gif,.bmp"
                    ),
                },
                "max_batch": {
                    "type": "integer",
                    "description": "Max images to process (optional; 0 = unlimited).",
                },
            },
            "required": ["folder"],
        },
    },
]


def send_response(msg_id, result):
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result},
                   ensure_ascii=False) + "\n"
    )
    sys.stdout.flush()


def _text_result(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _config_guard():
    cfg = vision.load_config()
    if not vision.config_ok(cfg):
        return None, ("Missing config: run `python setup.py` or set "
                      "VISION_BASE_URL / VISION_API_KEY / VISION_MODEL.")
    return cfg, None


def handle_describe(args):
    cfg, err = _config_guard()
    if err:
        return _text_result(err, is_error=True)
    path = args.get("image_path")
    if not isinstance(path, str) or not path.strip():
        return _text_result("image_path is required (a non-empty string).", is_error=True)
    instruction = args.get("instruction") or vision.DEFAULT_INSTRUCTION
    try:
        return _text_result(vision.call_vision(cfg, path, instruction))
    except Exception as e:
        return _text_result(f"[recognition failed] {e}", is_error=True)


def handle_batch(args):
    cfg, err = _config_guard()
    if err:
        return _text_result(err, is_error=True)
    folder = args.get("folder")
    if not isinstance(folder, str) or not folder.strip():
        return _text_result("folder is required (a non-empty string).", is_error=True)
    ext = args.get("ext") or ".png,.jpg,.jpeg,.webp,.gif,.bmp"
    try:
        max_batch = int(args.get("max_batch") or 0)
    except (TypeError, ValueError):
        max_batch = 0
    exts = {e.strip().lower() for e in ext.split(",") if e.strip()}
    files = vision.list_images(folder, exts)
    if max_batch:
        files = files[: max_batch]
    if not files:
        return _text_result("No image files found.", is_error=True)
    instruction = args.get("instruction") or vision.DEFAULT_INSTRUCTION
    parts = []
    n = len(files)
    for i, f in enumerate(files, 1):
        try:
            out = vision.call_vision(cfg, f, instruction)
        except Exception as e:
            out = f"[recognition failed] {e}"
        parts.append(f"===== [{i}/{n}] {f} =====" if n > 1 else f"===== {f} =====")
        parts.append(out)
    return _text_result("\n".join(parts))


def _normalize_args(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def handle_tools_call(msg_id, params):
    name = params.get("name")
    args = _normalize_args(params.get("arguments"))
    if name == "vision_describe":
        result = handle_describe(args)
    elif name == "vision_batch":
        result = handle_batch(args)
    else:
        result = _text_result(f"Unknown tool: {name}", is_error=True)
    send_response(msg_id, result)


def handle_initialize(msg_id, params):
    protocol = (params or {}).get("protocolVersion", "2024-11-05")
    send_response(msg_id, {
        "protocolVersion": protocol,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    })


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        if not isinstance(msg, dict) or "method" not in msg:
            continue
        method = msg["method"]
        msg_id = msg.get("id")
        if method == "initialize":
            handle_initialize(msg_id, msg.get("params", {}))
        elif method == "ping":
            send_response(msg_id, {})
        elif method == "tools/list":
            send_response(msg_id, {"tools": TOOLS})
        elif method == "tools/call":
            handle_tools_call(msg_id, msg.get("params", {}))
        # Notifications (no "id"), e.g. notifications/initialized, are ignored.


if __name__ == "__main__":
    main()
