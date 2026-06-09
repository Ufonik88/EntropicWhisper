from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .audio import record_wav
from .clipboard import copy_text, paste_text
from .config import AppConfig
from .context import get_selected_text
from .notes import MeetingNote, append_meeting_note
from .providers import cleanup_transcript, summarize_meeting, transcribe_audio
from .text import clean_transcript_locally


def _config(args: argparse.Namespace) -> AppConfig:
    return AppConfig.load(Path(args.config) if getattr(args, "config", None) else None)


def cmd_init(args: argparse.Namespace) -> int:
    config = _config(args)
    path = config.write_default_files()
    print(f"Created config: {path}")
    print(f"Add your API key: export {config.api_key_env}=...")
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    config = _config(args)
    raw = args.text or sys.stdin.read()
    if args.local:
        cleaned = clean_transcript_locally(raw)
    else:
        cleaned = cleanup_transcript(raw, config, context=args.context or get_selected_text())
    print(cleaned)
    if args.copy:
        copy_text(cleaned)
    if args.paste:
        paste_text(cleaned)
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    config = _config(args)
    config.ensure_dirs()
    audio_path = Path(args.output) if args.output else config.data_dir / "last_recording.wav"
    print(f"Recording {args.seconds}s to {audio_path}...", file=sys.stderr)
    record_wav(audio_path, seconds=args.seconds)
    raw = transcribe_audio(audio_path, config)
    cleaned = cleanup_transcript(raw, config, context=get_selected_text()) if args.clean else raw
    print(cleaned)
    if args.copy:
        copy_text(cleaned)
    if args.paste:
        paste_text(cleaned)
    return 0


def cmd_meeting(args: argparse.Namespace) -> int:
    config = _config(args)
    config.ensure_dirs()
    audio_path = Path(args.audio) if args.audio else config.data_dir / "meeting.wav"
    if not args.audio and not args.transcript:
        print(f"Recording meeting for {args.seconds}s...", file=sys.stderr)
        record_wav(audio_path, seconds=args.seconds)
    if args.transcript:
        transcript = Path(args.transcript).read_text()
    else:
        transcript = transcribe_audio(audio_path, config)
    summary = summarize_meeting(transcript, config) if args.summarize else ""
    title = args.title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    note = MeetingNote(title=title, transcript=transcript, summary=summary)
    target = Path(args.notes_file) if args.notes_file else config.notes_file
    if target is None:
        raise RuntimeError("No notes file configured")
    append_meeting_note(target, note)
    print(f"Saved meeting note: {target}")
    return 0


def cmd_hotkey(args: argparse.Namespace) -> int:
    try:
        from pynput import keyboard
    except ImportError:
        print("Hotkey mode needs pynput: pipx inject entopicwhisper pynput", file=sys.stderr)
        return 2

    config = _config(args)
    print(f"EntopicWhisper hotkey mode. Press {config.hotkey} to record {args.seconds}s.")

    def on_activate() -> None:
        synthetic_args = argparse.Namespace(
            config=args.config,
            seconds=args.seconds,
            output=None,
            clean=True,
            copy=True,
            paste=True,
        )
        try:
            cmd_record(synthetic_args)
        except Exception as exc:  # pragma: no cover - interactive mode
            print(f"Error: {exc}", file=sys.stderr)

    parsed_hotkey = keyboard.HotKey.parse(_pynput_hotkey(config.hotkey))
    hotkey = keyboard.HotKey(parsed_hotkey, on_activate)

    def for_canonical(listener: Any, fn: Any) -> Any:
        return lambda key: fn(listener.canonical(key))

    with keyboard.Listener(
        on_press=for_canonical(keyboard.Listener, hotkey.press),
        on_release=for_canonical(keyboard.Listener, hotkey.release),
    ) as listener:
        listener.join()
    return 0


def _pynput_hotkey(value: str) -> str:
    parts = [part.strip().lower() for part in value.split("+") if part.strip()]
    converted = []
    for part in parts:
        if part in {"ctrl", "control", "shift", "alt", "cmd", "super"}:
            converted.append(f"<{part}>")
        else:
            converted.append(part)
    return "+".join(converted)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="entopicwhisper",
        description="Ubuntu dictation and meeting notes",
    )
    parser.add_argument("--config", help="Path to config.env")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create default config and vocabulary")
    init.set_defaults(func=cmd_init)

    cleanup = sub.add_parser("cleanup", help="Clean raw text from args or stdin")
    cleanup.add_argument("text", nargs="?", help="Raw transcript text")
    cleanup.add_argument("--context", default="", help="Nearby context")
    cleanup.add_argument("--local", action="store_true", help="Use local lightweight cleanup only")
    cleanup.add_argument("--copy", action="store_true", help="Copy result to clipboard")
    cleanup.add_argument("--paste", action="store_true", help="Paste result into active app")
    cleanup.set_defaults(func=cmd_cleanup)

    record = sub.add_parser("record", help="Record microphone, transcribe, and optionally paste")
    record.add_argument("--seconds", type=int, default=30)
    record.add_argument("--output")
    record.add_argument("--clean", action=argparse.BooleanOptionalAction, default=True)
    record.add_argument("--copy", action="store_true")
    record.add_argument("--paste", action="store_true")
    record.set_defaults(func=cmd_record)

    meeting = sub.add_parser(
        "meeting",
        help="Record/transcribe a meeting and append markdown notes",
    )
    meeting.add_argument("--seconds", type=int, default=1800)
    meeting.add_argument("--audio", help="Existing audio file to transcribe")
    meeting.add_argument("--transcript", help="Existing transcript text file")
    meeting.add_argument("--title")
    meeting.add_argument("--notes-file")
    meeting.add_argument("--summarize", action=argparse.BooleanOptionalAction, default=True)
    meeting.set_defaults(func=cmd_meeting)

    hotkey = sub.add_parser("hotkey", help="Run global hotkey listener")
    hotkey.add_argument("--seconds", type=int, default=20)
    hotkey.set_defaults(func=cmd_hotkey)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
