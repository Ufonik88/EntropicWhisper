# EntropicWhisper

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
pipx install git+https://github.com/Ufonik88/EntropicWhisper.git
entropicwhisper init
export GROQ_API_KEY="your-key"
```

For Wayland clipboard support:

```bash
sudo apt install -y wl-clipboard
```

Optional hotkey mode:

```bash
pipx inject entropicwhisper pynput
entropicwhisper hotkey --seconds 20
```

## Web UI

EntropicWhisper includes a clean, minimal web interface for dictation and meeting notes.

```bash
# Install Flask dependency
pipx inject entropicwhisper flask

# Launch the UI (opens browser automatically)
entropicwhisper ui
```

The UI runs at **http://127.0.0.1:8420** and provides:

- **Record** — Click the microphone to record, auto-transcribe and clean with AI
- **Cleanup** — Paste raw text and clean with AI or local-only mode
- **Meeting Notes** — Save transcripts as structured Markdown, view past notes
- **Vocabulary** — Manage custom terms (product names, jargon, client words)
- **Settings** — View current provider/model configuration

Options:
```bash
entropicwhisper ui --port 9000           # custom port
entropicwhisper ui --host 0.0.0.0        # listen on all interfaces
entropicwhisper ui --no-open             # don't auto-open browser
```

## Usage

### Clean rough transcript text locally

```bash
echo "um hello there , this is uh a test ." | entropicwhisper cleanup --local
```

### Clean with AI and copy to clipboard

```bash
entropicwhisper cleanup "raw dictated text" --copy
```

### Record 20 seconds, transcribe, clean, copy

```bash
entropicwhisper record --seconds 20 --copy
```

### Record and paste into active window

```bash
entropicwhisper record --seconds 20 --paste
```

### Save meeting notes

```bash
entropicwhisper meeting --seconds 1800 --title "Weekly pipeline review"
```

### Use an existing transcript file

```bash
entropicwhisper meeting --transcript ./meeting.txt --title "Client call" --no-summarize
```

## Configuration

`entropicwhisper init` creates:

- `~/.config/entropicwhisper/config.env`
- `~/.config/entropicwhisper/vocabulary.txt`
- notes default: `~/.local/share/entropicwhisper/meetings.md`

Example config:

```env
PROVIDER=groq
API_BASE=https://api.groq.com/openai/v1
API_KEY_ENV=GROQ_API_KEY
MODEL=whisper-large-v3-turbo
LLM_MODEL=llama-3.1-8b-instant
HOTKEY=ctrl+space
TOGGLE_HOTKEY=ctrl+shift+space
NOTES_FILE=/home/YOU/.local/share/entropicwhisper/meetings.md
VOCABULARY_FILE=/home/YOU/.config/entropicwhisper/vocabulary.txt
```

## OpenAI-compatible providers

EntropicWhisper expects:

- transcription endpoint: `POST {API_BASE}/audio/transcriptions`
- chat endpoint: `POST {API_BASE}/chat/completions`

Groq works out of the box with `GROQ_API_KEY`.

## Privacy

There is no EntropicWhisper server. Audio/text only goes to the provider you configure.

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
