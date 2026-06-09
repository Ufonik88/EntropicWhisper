from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def xdg_config_home() -> Path:
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))


def xdg_data_home() -> Path:
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def parse_vocabulary(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def resolve_backend() -> str:
    if os.getenv("WAYLAND_DISPLAY"):
        return "wayland"
    if os.getenv("DISPLAY"):
        return "x11"
    return "headless"


@dataclass(slots=True)
class AppConfig:
    provider: str = "groq"
    api_base: str = "https://api.groq.com/openai/v1"
    api_key_env: str = "GROQ_API_KEY"
    model: str = "whisper-large-v3-turbo"
    llm_model: str = "llama-3.1-8b-instant"
    hotkey: str = "ctrl+space"
    toggle_hotkey: str = "ctrl+shift+space"
    max_context_chars: int = 4000
    vocabulary: list[str] = field(default_factory=list)
    notes_file: Path | None = None
    config_dir: Path = field(default_factory=lambda: xdg_config_home() / "entopicwhisper")
    data_dir: Path = field(default_factory=lambda: xdg_data_home() / "entopicwhisper")

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        config_dir = xdg_config_home() / "entopicwhisper"
        data_dir = xdg_data_home() / "entopicwhisper"
        path = path or config_dir / "config.env"
        values: dict[str, str] = {}
        if path.exists():
            for raw_line in path.read_text().splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")

        vocab_file = Path(values.get("VOCABULARY_FILE", config_dir / "vocabulary.txt"))
        vocabulary = parse_vocabulary(vocab_file.read_text()) if vocab_file.exists() else []
        notes_file = Path(values.get("NOTES_FILE", data_dir / "meetings.md"))
        try:
            max_context_chars = int(values.get("MAX_CONTEXT_CHARS", "4000"))
        except (TypeError, ValueError):
            max_context_chars = 4000

        return cls(
            provider=values.get("PROVIDER", "groq"),
            api_base=values.get("API_BASE", "https://api.groq.com/openai/v1"),
            api_key_env=values.get("API_KEY_ENV", "GROQ_API_KEY"),
            model=values.get("MODEL", "whisper-large-v3-turbo"),
            llm_model=values.get("LLM_MODEL", "llama-3.1-8b-instant"),
            hotkey=values.get("HOTKEY", "ctrl+space"),
            toggle_hotkey=values.get("TOGGLE_HOTKEY", "ctrl+shift+space"),
            max_context_chars=max_context_chars,
            vocabulary=vocabulary,
            notes_file=notes_file,
            config_dir=config_dir,
            data_dir=data_dir,
        )

    def api_key(self) -> str:
        return os.getenv(self.api_key_env, "")

    def ensure_dirs(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def write_default_files(self) -> Path:
        self.ensure_dirs()
        config_path = self.config_dir / "config.env"
        vocab_path = self.config_dir / "vocabulary.txt"
        if not config_path.exists():
            config_path.write_text(
                "# EntopicWhisper config\n"
                "PROVIDER=groq\n"
                "API_BASE=https://api.groq.com/openai/v1\n"
                "API_KEY_ENV=GROQ_API_KEY\n"
                "MODEL=whisper-large-v3-turbo\n"
                "LLM_MODEL=llama-3.1-8b-instant\n"
                "HOTKEY=ctrl+space\n"
                "TOGGLE_HOTKEY=ctrl+shift+space\n"
                f"NOTES_FILE={self.data_dir / 'meetings.md'}\n"
                f"VOCABULARY_FILE={vocab_path}\n"
            )
        if not vocab_path.exists():
            vocab_path.write_text("Ajax Systems\nJeweller\nFibra\nHub Hybrid\nSuperior\n")
        return config_path
