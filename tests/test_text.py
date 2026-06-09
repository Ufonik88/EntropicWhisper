from entopicwhisper.text import build_cleanup_prompt, clean_transcript_locally, strip_empty_marker


def test_clean_transcript_locally_removes_fillers_and_fixes_spacing():
    raw = "um hello   there , this is uh a test ."
    assert clean_transcript_locally(raw) == "Hello there, this is a test."


def test_strip_empty_marker():
    assert strip_empty_marker("EMPTY") == ""
    assert strip_empty_marker("  EMPTY  ") == ""
    assert strip_empty_marker("Something") == "Something"


def test_build_cleanup_prompt_includes_vocabulary_and_context():
    prompt = build_cleanup_prompt(
        raw="meeting about fibrah",
        context="Ajax proposal notes",
        vocabulary=["Fibra", "Jeweller"],
        mode="dictation",
    )

    assert "meeting about fibrah" in prompt
    assert "Ajax proposal notes" in prompt
    assert "Fibra" in prompt
    assert "Return ONLY" in prompt
