from entopicwhisper.config import AppConfig, parse_vocabulary, resolve_backend


def test_parse_vocabulary_strips_blanks_and_preserves_order():
    assert parse_vocabulary("Ajax Systems\n  Fibra  \n\nJeweller") == [
        "Ajax Systems",
        "Fibra",
        "Jeweller",
    ]


def test_app_config_defaults_to_safe_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    config = AppConfig.load()

    assert config.hotkey == "ctrl+space"
    assert config.provider == "groq"
    assert config.model == "whisper-large-v3-turbo"
    assert config.llm_model == "llama-3.1-8b-instant"
    assert config.config_dir == tmp_path / ".config" / "entopicwhisper"
    assert config.data_dir == tmp_path / ".local" / "share" / "entopicwhisper"


def test_resolve_backend_detects_x11_when_wayland_missing(monkeypatch):
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    assert resolve_backend() == "x11"


def test_resolve_backend_detects_wayland(monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert resolve_backend() == "wayland"
