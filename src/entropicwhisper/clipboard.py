from __future__ import annotations

import shutil
import subprocess

from .config import resolve_backend


class ClipboardError(RuntimeError):
    pass


def copy_text(text: str) -> None:
    backend = resolve_backend()
    if backend == "wayland" and shutil.which("wl-copy"):
        subprocess.run(["wl-copy"], input=text, text=True, check=True)
        return
    if shutil.which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        return
    raise ClipboardError("Install xclip (X11) or wl-clipboard (Wayland) to copy text.")


def paste_text(text: str) -> None:
    copy_text(text)
    if resolve_backend() == "x11" and shutil.which("xdotool"):
        subprocess.run(["xdotool", "key", "ctrl+v"], check=True)
