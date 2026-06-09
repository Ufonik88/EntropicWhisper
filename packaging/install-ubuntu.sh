#!/usr/bin/env bash
set -euo pipefail
sudo apt update
sudo apt install -y python3-pip python3-venv pipx alsa-utils xclip xdotool wl-clipboard
pipx install git+https://github.com/Ufonik88/EntopicWhisper.git --force
entopicwhisper init
printf '\nSet your API key before use:\n  export GROQ_API_KEY="your-key"\n'
