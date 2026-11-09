#!/usr/bin/env bash
# One-time setup on Linux / macOS. Needs Python 3.10+ and ffmpeg (apt install ffmpeg / brew install ffmpeg). See docs/INSTALL.md
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "ffmpeg was not found. Install it first (apt install ffmpeg  |  brew install ffmpeg)."; exit 1; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
echo
echo "Setup done. Start the app with ./run.sh, then open Settings (gear icon) -> Models to download a speech model."
