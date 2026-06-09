from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class MeetingNote:
    title: str
    transcript: str
    summary: str = ""
    action_items: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=lambda: ["meeting"])
    created_at: datetime = field(default_factory=datetime.now)


def format_meeting_note(note: MeetingNote) -> str:
    tags = " ".join(f"#{tag.lstrip('#')}" for tag in note.tags)
    lines = [
        f"# {note.title}",
        "",
        f"- Date: {note.created_at.strftime('%Y-%m-%d %H:%M')}",
        f"- Tags: {tags}" if tags else "- Tags:",
        "",
    ]
    if note.summary:
        lines += ["## Summary", "", note.summary.strip(), ""]
    if note.action_items:
        lines += ["## Action Items", ""]
        lines += [f"- [ ] {item}" for item in note.action_items]
        lines.append("")
    lines += ["## Transcript", "", note.transcript.strip(), "", "---", ""]
    return "\n".join(lines)


def append_meeting_note(path: Path, note: MeetingNote) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(format_meeting_note(note))
