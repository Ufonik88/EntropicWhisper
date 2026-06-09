from __future__ import annotations

import re
from collections.abc import Sequence

_FILLER_RE = re.compile(r"\b(um+|uh+|erm|you know|like)\b[, ]*", re.IGNORECASE)
_SPACE_RE = re.compile(r"\s+")


def clean_transcript_locally(raw: str) -> str:
    text = raw.strip()
    if not text:
        return ""
    text = _FILLER_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])(?=\S)", r"\1 ", text)
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    return text


def strip_empty_marker(text: str) -> str:
    return "" if text.strip() == "EMPTY" else text


def build_cleanup_prompt(
    *, raw: str, context: str = "", vocabulary: Sequence[str] = (), mode: str = "dictation"
) -> str:
    vocab = "\n".join(f"- {item}" for item in vocabulary) or "- (none)"
    context = context[-4000:] if context else "(none)"
    return f'''You are EntopicWhisper, a dictation and meeting-note post-processor.

Mode: {mode}

Rules:
- Preserve the speaker's intent, tone, and meaning exactly.
- Remove filler words unless they carry meaning.
- Fix spelling, grammar, punctuation, and casing.
- Use nearby context and vocabulary ONLY to correct names/terms that were actually spoken.
- Never invent facts, names, tasks, commitments, dates, prices, or attendees.
- Return ONLY the cleaned text. No preamble. No markdown unless the user asked for structured notes.
- If the transcription is empty, return exactly: EMPTY

Custom vocabulary:
{vocab}

Nearby context:
{context}

RAW_TRANSCRIPTION:
{raw}
'''


def build_meeting_summary_prompt(transcript: str, vocabulary: Sequence[str] = ()) -> str:
    vocab = "\n".join(f"- {item}" for item in vocabulary) or "- (none)"
    return f'''Turn this transcript into concise meeting notes.

Return markdown with exactly these sections:
## Summary
## Decisions
## Action Items
## Risks / Open Questions

Rules:
- Use checkbox action items: - [ ] Owner/action/date if present.
- If a section has nothing, write "None captured."
- Do not invent absent details.
- Preserve domain terms using vocabulary.

Vocabulary:
{vocab}

Transcript:
{transcript}
'''
