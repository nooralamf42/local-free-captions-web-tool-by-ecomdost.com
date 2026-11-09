# Troubleshooting

**"The speech model ... is not downloaded yet"**: open Settings (gear icon) → Models and press Download, or run `python captions.py download apex`.

**"ffmpeg not found"**: install it (`winget install Gyan.FFmpeg`, `sudo apt install ffmpeg`, `brew install ffmpeg`) and open a new terminal.

**"CUDA failed, falling back to CPU"**: the NVIDIA libraries are missing. Run `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` inside the virtual environment and update your
NVIDIA driver. CPU works but is several times slower; try the *small* or *Apex* model.

**Out of GPU memory**: close other GPU programs, use a smaller model, or don't run two jobs at once. The app retries on the CPU automatically.

**"The person cut-out model is not downloaded yet"**: Settings → Models → *Person cut-out* → Download (14 MB).

**The big word behind the person looks rough**: the cut-out works best on a single person in a clear shot. It runs at 540×960 and is scaled up.

**AI polish says "HTTP 401"**: the key was rejected; paste it again. **"HTTP 404"**: the model name or address is wrong for that provider. **"HTTP 429"**: rate limit, wait a moment.

**Captions slightly early or late**: Customize → Timing, or `--offset 0.08` on the command line.

**A Hinglish word is spelled oddly**: edit it on the timeline, turn on AI polish, or add it to `glossary.json` (`{"टीशर्ट": "t-shirt"}` maps a Devanagari word to what to print).

**The 2K / 60 FPS export is slow**: it has 1.8× the pixels and 2× the frames. With an NVIDIA GPU it uses NVENC and is fast; without one it uses x264 on the CPU.

**Preview shows nothing or fonts look wrong**: hard-refresh the page (Ctrl+F5). Fonts load from the `fonts/` folder.

**Port 8765 is in use**: `python captions.py serve --port 8800`.

Still stuck? Open an issue with the text of the *Activity* log on the home page, and your OS and GPU.
