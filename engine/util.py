"""Paths, CUDA DLL setup, ffmpeg/ffprobe helpers."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
MODELS = ROOT / "models"
WORK = ROOT / "workspace"
OUTPUTS = ROOT / "outputs"

_NOWIN = {"creationflags": 0x08000000} if sys.platform == "win32" else {}  # CREATE_NO_WINDOW


_cuda_paths_done = False


def setup_cuda_paths():
    """faster-whisper (CTranslate2) needs cublas/cudnn DLLs; pip wheels put them in site-packages/nvidia/*/bin."""
    global _cuda_paths_done
    if sys.platform != "win32" or _cuda_paths_done:
        return  # run once: re-prepending PATH on every job grew it past Windows' 32 KB limit
    _cuda_paths_done = True
    import site
    roots = list(site.getsitepackages()) + [site.getusersitepackages()]
    for r in roots:
        nv = Path(r) / "nvidia"
        if not nv.is_dir():
            continue
        for sub in nv.iterdir():
            b = sub / "bin"
            if b.is_dir():
                if str(b) not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = str(b) + os.pathsep + os.environ.get("PATH", "")
                try:
                    os.add_dll_directory(str(b))
                except (AttributeError, OSError):
                    pass


def ffmpeg_bin():
    p = shutil.which("ffmpeg")
    if not p:
        raise RuntimeError("ffmpeg not found on PATH. Install: winget install Gyan.FFmpeg")
    return p


def probe(path):
    """Return dict(width,height,duration,fps,has_audio,acodec,rotation-corrected size)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, **_NOWIN)
    if out.returncode != 0:
        raise RuntimeError("ffprobe failed: " + out.stderr.strip()[:300])
    j = json.loads(out.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    info = {"duration": float(j["format"].get("duration") or 0), "has_audio": a is not None,
            "acodec": a["codec_name"] if a else None, "width": 0, "height": 0, "fps": 30.0}
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = rot or int((v.get("tags") or {}).get("rotate", 0) or 0)
        if abs(rot) in (90, 270):
            w, h = h, w
        info.update(width=w, height=h)
        try:
            n, d = v.get("avg_frame_rate", "30/1").split("/")
            info["fps"] = float(n) / float(d) if float(d) else 30.0
        except Exception:
            pass
        if not info["duration"]:
            info["duration"] = float(v.get("duration") or 0)
    return info


def safe_name(s):
    keep = "".join(c if c.isalnum() or c in "-_." else "_" for c in s)
    return keep.strip("._") or "video"
