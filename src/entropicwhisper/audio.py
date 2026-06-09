from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class AudioError(RuntimeError):
    pass


def record_wav(output: Path, seconds: int = 30, sample_rate: int = 16000) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("arecord"):
        cmd = [
            "arecord",
            "-q",
            "-f",
            "S16_LE",
            "-r",
            str(sample_rate),
            "-c",
            "1",
            "-d",
            str(seconds),
            str(output),
        ]
        subprocess.run(cmd, check=True)
        return output

    try:
        import wave

        import numpy as np
        import sounddevice as sd
    except Exception as exc:  # pragma: no cover - depends on optional system packages
        raise AudioError(
            "No recorder available. Install ALSA arecord (`sudo apt install alsa-utils`) "
            "or install optional Python audio deps (`pipx inject entopicwhisper sounddevice "
            "numpy`)."
        ) from exc

    frames = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(np.asarray(frames).tobytes())
    return output
