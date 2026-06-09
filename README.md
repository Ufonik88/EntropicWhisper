# EntopicWhisper

Ubuntu voice dictation and meeting-notes app inspired by FreeFlow / Wispr Flow.

**v0.1 goal:** simple, usable Ubuntu workflow:

- Record from microphone with ALSA `arecord` or optional Python `sounddevice`
- Transcribe with Groq Whisper or any OpenAI-compatible transcription endpoint
- Clean dictation with an OpenAI-compatible chat model
- Copy or paste into the active app (`xclip`/`xdotool` on X11, `wl-copy` on Wayland)
- Save meeting transcripts and summaries as Markdown
- Keep vocabulary for names, product terms, client jargon, and project words

## Quick install on Ubuntu

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv pipx alsa-utils xclip xdotool
pipx install git+https://github.com/Ufonik88/EntopicWhisper.git
entopicwhisper init
export GROQ_API_KEY="your-key"
```

For Wayland clipboard support:

```bash
sudo apt install -y wl-clipboard
```

Optional hotkey mode:

```bash
pipx inject entopicwhisper pynput
entopicwhisper hotkey --seconds 20
```

## Web UI

EntopicWhisper includes a clean, minimal web interface for dictation and meeting notes.

```bash
# Install Flask dependency
pipx inject entopicwhisper flask

# Launch the UI (opens browser automatically)
entopicwhisper ui
```

The UI runs at **http://127.0.0.1:8420** and provides:

- **Record** — Click the microphone to record, auto-transcribe and clean with AI
- **Cleanup** — Paste raw text and clean with AI or local-only mode
- **Meeting Notes** — Save transcripts as structured Markdown, view past notes
- **Vocabulary** — Manage custom terms (product names, jargon, client words)
- **Settings** — View current provider/model configuration

Options:
```bash
entopicwhisper ui --port 9000           # custom port
entopicwhisper ui --host 0.0.0.0        # listen on all interfaces
entopicwhisper ui --no-open             # don't auto-open browser
```

## Usage

### Clean rough transcript text locally

```bash
echo "um hello there , this is uh a test ." | entopicwhisper cleanup --local
```

### Clean with AI and copy to clipboard

```bash
entopicwhisper cleanup "raw dictated text" --copy
```

### Record 20 seconds, transcribe, clean, copy

```bash
entopicwhisper record --seconds 20 --copy
```

### Record and paste into active window

```bash
entopicwhisper record --seconds 20 --paste
```

### Save meeting notes

```bash
entopicwhisper meeting --seconds 1800 --title "Weekly pipeline review"
```

### Use an existing transcript file

```bash
entopicwhisper meeting --transcript ./meeting.txt --title "Client call" --no-summarize
```

## Configuration

`entopicwhisper init` creates:

- `~/.config/entopicwhisper/config.env`
- `~/.config/entopicwhisper/vocabulary.txt`
- notes default: `~/.local/share/entopicwhisper/meetings.md`

Example config:

```env
PROVIDER=groq
API_BASE=https://api.groq.com/openai/v1
API_KEY_ENV=GROQ_API_KEY
MODEL=whisper-large-v3-turbo
LLM_MODEL=llama-3.1-8b-instant
HOTKEY=ctrl+space
TOGGLE_HOTKEY=ctrl+shift+space
NOTES_FILE=/home/YOU/.local/share/entopicwhisper/meetings.md
VOCABULARY_FILE=/home/YOU/.config/entopicwhisper/vocabulary.txt
```

## OpenAI-compatible providers

EntopicWhisper expects:

- transcription endpoint: `POST {API_BASE}/audio/transcriptions`
- chat endpoint: `POST {API_BASE}/chat/completions`

Groq works out of the box with `GROQ_API_KEY`.

## Privacy

There is no EntopicWhisper server. Audio/text only goes to the provider you configure.

## Current limitations (v0.1)

- Linux desktop automation differs by X11/Wayland. X11 paste is best supported.
- Global hotkeys are experimental and depend on `pynput`/desktop permissions.
- Meeting recording is a single fixed-duration capture in v0.1.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest -q
ruff check .
```
