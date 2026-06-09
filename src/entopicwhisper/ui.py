from __future__ import annotations

import threading
import webbrowser
from typing import Any

from flask import Flask, jsonify, render_template, request

from .audio import record_wav
from .config import AppConfig
from .notes import MeetingNote, append_meeting_note
from .providers import cleanup_transcript, summarize_meeting, transcribe_audio
from .text import clean_transcript_locally

app = Flask(__name__, template_folder="templates", static_folder="static")

_config: AppConfig | None = None
_recording: dict[str, Any] = {"active": False, "path": None}


def _cfg() -> AppConfig:
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


# ── Pages ───────────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ── API ─────────────────────────────────────────────────────────────────────────


@app.route("/api/status")
def status():
    cfg = _cfg()
    key_set = bool(cfg.api_key())
    return jsonify(
        {
            "provider": cfg.provider,
            "model": cfg.model,
            "llm_model": cfg.llm_model,
            "hotkey": cfg.hotkey,
            "api_key_set": key_set,
            "notes_file": str(cfg.notes_file),
            "vocabulary_count": len(cfg.vocabulary),
            "recording": _recording["active"],
        }
    )


@app.route("/api/record", methods=["POST"])
def record():
    if _recording["active"]:
        return jsonify({"error": "Recording already in progress"}), 409

    seconds = request.json.get("seconds", 10) if request.is_json else 10
    cfg = _cfg()
    cfg.ensure_dirs()
    audio_path = cfg.data_dir / "ui_recording.wav"

    _recording["active"] = True
    _recording["path"] = str(audio_path)

    try:
        record_wav(audio_path, seconds=seconds)
        raw = transcribe_audio(audio_path, cfg)
        cleaned = cleanup_transcript(raw, cfg, context="")
        return jsonify({"raw": raw, "cleaned": cleaned})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        _recording["active"] = False


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """Transcribe uploaded audio file."""
    cfg = _cfg()
    audio = request.files.get("audio")
    if not audio:
        return jsonify({"error": "No audio file uploaded"}), 400

    cfg.ensure_dirs()
    tmp = cfg.data_dir / "upload_recording.wav"
    audio.save(str(tmp))

    try:
        raw = transcribe_audio(tmp, cfg)
        return jsonify({"raw": raw})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/cleanup", methods=["POST"])
def cleanup():
    data = request.get_json(force=True)
    raw = data.get("text", "")
    mode = data.get("mode", "ai")  # "ai" or "local"
    context = data.get("context", "")

    if mode == "local":
        return jsonify({"cleaned": clean_transcript_locally(raw)})

    cfg = _cfg()
    try:
        cleaned = cleanup_transcript(raw, cfg, context=context)
        return jsonify({"cleaned": cleaned})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/meeting", methods=["POST"])
def meeting():
    data = request.get_json(force=True)
    transcript = data.get("transcript", "")
    title = data.get("title", "")
    summarize_flag = data.get("summarize", True)

    if not transcript.strip():
        return jsonify({"error": "Transcript is required"}), 400

    cfg = _cfg()
    cfg.ensure_dirs()

    if not title:
        from datetime import datetime

        title = f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    summary = ""
    if summarize_flag:
        try:
            summary = summarize_meeting(transcript, cfg)
        except Exception as exc:
            summary = f"(Summary failed: {exc})"

    note = MeetingNote(title=title, transcript=transcript, summary=summary)
    target = cfg.notes_file
    if target is None:
        return jsonify({"error": "No notes file configured"}), 500

    append_meeting_note(target, note)
    return jsonify(
        {
            "saved": True,
            "file": str(target),
            "title": title,
            "summary": summary,
        }
    )


@app.route("/api/notes")
def notes():
    cfg = _cfg()
    target = cfg.notes_file
    if target is None or not target.exists():
        return jsonify({"notes": "", "file": None})
    content = target.read_text(encoding="utf-8")
    return jsonify({"notes": content, "file": str(target)})


@app.route("/api/vocabulary")
def vocabulary():
    cfg = _cfg()
    vocab_path = cfg.config_dir / "vocabulary.txt"
    words = cfg.vocabulary
    return jsonify({"words": words, "file": str(vocab_path)})


@app.route("/api/vocabulary", methods=["PUT"])
def update_vocabulary():
    cfg = _cfg()
    data = request.get_json(force=True)
    words = data.get("words", [])
    vocab_path = cfg.config_dir / "vocabulary.txt"
    vocab_path.write_text("\n".join(words) + "\n", encoding="utf-8")
    cfg.vocabulary = words
    return jsonify({"saved": True, "count": len(words)})


# ── Entrypoint ──────────────────────────────────────────────────────────────────


def run_ui(host: str = "127.0.0.1", port: int = 8420, open_browser: bool = True):
    cfg = _cfg()
    cfg.ensure_dirs()
    print(f"EntopicWhisper UI running at http://{host}:{port}")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
