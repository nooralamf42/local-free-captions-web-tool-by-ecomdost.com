# Local Captions

**Free, private auto-captions for Reels, Shorts and TikToks. Runs on your own computer.**

Drop in a video, get word-by-word animated captions burned into the MP4. No account, no credits, no watermark, no upload limit.
Speech recognition runs locally (faster-whisper); the optional AI clean-up sends only the transcript *text* to the provider you choose.

- **100+ caption templates** — highlight, reveal, pop, karaoke, boxed, glow, handwriting, stacked key-word layouts and more, with hover-to-preview
- **"Text behind you"** templates — a huge key word sits *behind* the speaker (person cut-out runs on your GPU)
- **Made for Hinglish** — a Hindi + English speech model (Apex) that writes Roman letters, plus optional AI polish (numbers as digits, natural spelling)
- **Editor** — live preview, word timeline (drag to retime, split, trim), text editing, per-template customising (size, colours, fonts, motion, position, fades)
- **Export** up to **2K (1440×2560) at 60 FPS**, as many template versions per video as you like
- **Full screen** preview, undo/redo, keyboard shortcuts, CLI for batch jobs

> Not affiliated with, or endorsed by, any other caption product. Template names describe their look; see [docs/TEMPLATES.md](docs/TEMPLATES.md).

## Quick start

You need **Python 3.10+** and **ffmpeg**.

**Windows**
```bat
winget install Gyan.FFmpeg
setup.bat
ui.bat
```

**Linux / macOS**
```bash
sudo apt install ffmpeg        # or: brew install ffmpeg
./setup.sh
./run.sh
```

Then open **http://127.0.0.1:8765**, click **Settings (gear icon) → Models** and press **Download** on the speech model you want
(**Hinglish Apex** for Hindi + English, **Whisper large-v3-turbo** for everything else). Models are *not* bundled with the app, and nothing is downloaded
until you press a button. Prefer the terminal? `python captions.py download apex`.

Step-by-step help: [docs/INSTALL.md](docs/INSTALL.md).

## Using it

1. **Add videos** — drop them anywhere on the Videos page.
2. **Pick the speech settings** — language, *Captions written as* (as spoken / Hinglish in Roman letters / English), and the model.
3. **Generate captions**, then **Open editor**.
4. **Choose a template** (hover a card to see it animate), tweak it in **Customize**, fix words on the timeline.
5. **Export** — choose 1080p / 2K and 30 / 60 FPS at the top; finished videos land in `outputs/`.

## Optional: AI polish and your API key

Speech models make small mistakes: numbers written as words, odd Hinglish spelling, English words spelled phonetically. An AI pass can fix these
(“bis commands” → “20 commands”, “yah” → “ye”, “chait jeepeeti” → “ChatGPT”). It works with **any OpenAI-compatible API**: Groq (free tier), OpenAI, xAI, OpenRouter, or your own.

Put your key in **Settings → AI polish** (stored only on your computer in `workspace/settings.json`), or set an environment variable such as `GROQ_API_KEY`.
Details and privacy notes: [docs/AI_POLISH.md](docs/AI_POLISH.md). Without a key everything still works; you just skip the polish step.

## Models

| Model | Good for | Size |
|---|---|---|
| **Hinglish Apex** (recommended for Hindi) | Hindi + English mixed speech, Roman-letter output | ~0.8 GB |
| Whisper large-v3-turbo | English and 90+ languages, fast | ~1.6 GB |
| Whisper large-v3 | Most accurate; needed to translate to English | ~3.1 GB |
| Whisper medium / small | Smaller computers, quick drafts | 1.5 GB / 0.5 GB |
| Person cut-out (Robust Video Matting) | "Text behind you" templates | 14 MB |

More in [docs/MODELS.md](docs/MODELS.md).

## Command line

```bash
python captions.py reel.mp4 --style hormozi
python captions.py a.mp4 b.mp4 --style hormozi --style karaoke --mode roman --model apex
python captions.py reel.mp4 --transcript-only --srt
python captions.py --list-styles
python captions.py download apex        # fetch a model
python captions.py serve                # the web app
```

## Hardware

- **NVIDIA GPU** (4 GB+) — fastest: speech on CUDA, export on NVENC. Install is automatic via `requirements.txt`.
- **Other GPUs on Windows** — person cut-out uses DirectML; speech runs on the CPU.
- **CPU only / macOS** — works, slower (use the *small* or *Apex* model for drafts). macOS has no GPU speech acceleration in faster-whisper.

Tested on Windows 11 with an NVIDIA GTX 1650 SUPER (4 GB). Linux and macOS should work but are less tested — please report problems.

## Project layout

```
captions.py        command line + `serve`
server.py          local web server (Flask) and API
engine/            transcription, caption layout (ASS subtitles), motion, rendering, models, settings
frontend/          React + Vite + Tailwind UI source        web/  its built output (served by Flask)
fonts/             bundled open-source fonts
docs/              guides
```

The server listens on `127.0.0.1` only. Do not expose it to the internet: it has no login, and it can read the videos you upload and use your saved API key.

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Licence: [MIT](LICENSE). Third-party components and fonts: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
