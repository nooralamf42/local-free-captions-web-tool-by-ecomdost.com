# Installation

## 1. Requirements

| | Windows | Linux | macOS |
|---|---|---|---|
| Python 3.10 or newer | [python.org](https://www.python.org/downloads/) (tick "Add to PATH") | `sudo apt install python3 python3-venv` | `brew install python` |
| ffmpeg (with libass) | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` | `brew install ffmpeg` |
| Disk space | about 3 GB for the app plus one speech model (Apex 0.8 GB, turbo 1.6 GB) | | |
| GPU (optional) | NVIDIA 4 GB+ for fast transcription and export | | |

Check ffmpeg has the subtitle filter: `ffmpeg -filters` and look for `ass`.

## 2. Get the code

```bash
git clone https://github.com/nooralamf42/local-free-captions-web-tool-by-ecomdost.com.git
cd local-free-captions-web-tool-by-ecomdost.com
```

## 3. Install

- **Windows:** double-click `setup.bat` (or run it in a terminal).
- **Linux / macOS:** `./setup.sh`

This creates a `.venv` folder and installs the Python packages. It does **not** download any speech model.

## 4. Start

- **Windows:** `ui.bat`
- **Linux / macOS:** `./run.sh`

Open <http://127.0.0.1:8765>.

## 5. Download a model

In the app: **Settings (gear icon) → Models → Download**. Or in a terminal:

```bash
python captions.py download apex        # Hindi + English (Hinglish)
python captions.py download turbo       # English and other languages
python captions.py download matting     # person cut-out for "text behind you" templates
```

Use the virtual environment's Python: `.venv\Scripts\python.exe captions.py download apex` on Windows, `.venv/bin/python captions.py download apex` elsewhere.

## 6. (Optional) AI polish

See [AI_POLISH.md](AI_POLISH.md).

## Changing the interface (developers)

The app serves the pre-built interface in `web/`, so you do not need Node to use it. To change it:

```bash
cd frontend
npm install
npm run build        # writes ../web
```

## Updating

`git pull`, run the setup script again, and rebuild the interface only if you changed `frontend/`.
