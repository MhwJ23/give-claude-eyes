#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odin's Eye — Claude Code launcher.

Shows an up/down menu to choose the vision mode (auto / manual), writes mode.txt,
then launches Claude Code. Cross-platform (Windows / macOS / Linux).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODE_FILE = os.path.join(HERE, "mode.txt")

OPTIONS = [
    ("auto", "Auto vision   (call the vision tool whenever an image is relevant)"),
    ("manual", "Manual vision (only call the vision tool when you ask for it)"),
]

IS_WIN = os.name == "nt"

if IS_WIN:
    import ctypes
    import msvcrt
else:
    import select
    import termios
    import tty


def _enable_vt():
    """Enable ANSI/VT escape processing on the Windows console (legacy cmd.exe)."""
    if not IS_WIN:
        return
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def _read_key():
    if IS_WIN:
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):  # classic Windows extended-key prefix
            ch2 = msvcrt.getwch()
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(ch2, ch2)
        if ch == "\x1b":  # some Windows terminals send ANSI escape sequences
            if msvcrt.kbhit():
                nxt = msvcrt.getwch()
                if nxt == "[":
                    ch2 = msvcrt.getwch()
                    return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(ch2, ch2)
            return "esc"
        if ch in ("\r", "\n"):
            return "enter"
        if ch in ("\x03", "\x04"):  # Ctrl-C / Ctrl-D
            return "esc"
        return ch

    # POSIX: read bytes directly off the raw fd (avoid Python's buffering so select()
    # observes the kernel buffer) and parse arrow keys (ESC [ A/B/C/D).
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        b = os.read(fd, 1)
        if not b:                    # EOF
            raise EOFError
        if b in (b"\x03", b"\x04"):  # Ctrl-C / Ctrl-D
            return "esc"
        if b in (b"\r", b"\n"):
            return "enter"
        if b == b"\x1b":
            if select.select([fd], [], [], 0.05)[0]:
                nxt = os.read(fd, 1)
                if nxt == b"[":
                    ch2 = os.read(fd, 1)
                    key = {b"A": "up", b"B": "down", b"C": "right", b"D": "left"}.get(ch2)
                    if key:
                        return key
            return "esc"
        return b.decode("utf-8", "replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render(idx):
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write("  Choose vision mode (up/down to move, Enter to confirm)\n\n")
    for i, (_, label) in enumerate(OPTIONS):
        if i == idx:
            sys.stdout.write(f"  \033[1;32m> {label}\033[0m\n")
        else:
            sys.stdout.write(f"    {label}\n")
    sys.stdout.flush()


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    _enable_vt()

    if not sys.stdin.isatty():
        # No interactive menu possible — launch directly.
        print("stdin is not a terminal; starting Claude Code without the mode menu.")
        subprocess.run(["claude"] + sys.argv[1:])
        return

    idx = 0
    try:
        while True:
            render(idx)
            k = _read_key()
            if k == "up":
                idx = (idx - 1) % len(OPTIONS)
            elif k == "down":
                idx = (idx + 1) % len(OPTIONS)
            elif k == "enter":
                break
            elif k == "esc":
                print("\nCancelled. Not started.")
                return
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return

    mode, label = OPTIONS[idx]
    with open(MODE_FILE, "w", encoding="utf-8") as f:
        f.write(mode + "\n")
    print(f"\nSelected: {label}. Starting Claude Code ...\n")
    subprocess.run(["claude"] + sys.argv[1:])


if __name__ == "__main__":
    main()
