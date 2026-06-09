from __future__ import annotations

import shutil
import subprocess


def get_selected_text() -> str:
    if shutil.which("xclip"):
        try:
            result = subprocess.run(
                ["xclip", "-selection", "primary", "-o"],
                text=True,
                capture_output=True,
                timeout=2,
                check=False,
            )
            return result.stdout.strip()
        except Exception:
            return ""
    return ""
