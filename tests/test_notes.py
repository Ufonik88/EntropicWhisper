from entopicwhisper.notes import MeetingNote, append_meeting_note, format_meeting_note


def test_format_meeting_note_contains_title_transcript_and_summary():
    note = MeetingNote(
        title="Pipeline review",
        transcript="We discussed Ajax Hub rollout.",
        summary="Ajax Hub rollout was discussed.",
        action_items=["Send updated proposal"],
        tags=["meeting", "ajax"],
    )

    rendered = format_meeting_note(note)

    assert "# Pipeline review" in rendered
    assert "Ajax Hub rollout was discussed." in rendered
    assert "- [ ] Send updated proposal" in rendered
    assert "We discussed Ajax Hub rollout." in rendered
    assert "#meeting" in rendered


def test_append_meeting_note_creates_file(tmp_path):
    target = tmp_path / "meetings.md"
    note = MeetingNote(title="Demo", transcript="Raw notes")

    append_meeting_note(target, note)

    assert target.exists()
    content = target.read_text()
    assert "# Demo" in content
    assert "Raw notes" in content
