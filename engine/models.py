"""The models the app can use, and downloading them from inside the app (Settings -> Models).

Nothing is downloaded behind your back: a model is fetched only when the user presses its Download button. Speech models come from
Hugging Face (faster-whisper / CTranslate2 format); the person cut-out model from the Robust Video Matting GitHub release."""
import shutil
import threading
import time
import urllib.request

from .util import MODELS

# id -> info. size_mb: download size (used for the progress bar). dir: where it lives under models/.
REGISTRY = {
    "turbo": {"kind": "speech", "label": "Whisper large-v3-turbo", "repo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo", "dir": "large-v3-turbo",
              "size_mb": 1620, "license": "MIT",
              "desc": "Fast and accurate for English and 90+ languages. Hindi comes out in Devanagari (the app can convert it to Roman letters)."},
    "apex": {"kind": "speech", "label": "Hinglish Apex (recommended for Hindi + English)", "repo": "abhayhadez/anchor-hinglish-apex-ct2", "dir": "apex-ct2",
             "size_mb": 780, "license": "Apache-2.0",
             "desc": "Oriserve's Whisper-Hindi2Hinglish-Apex (large-v3-turbo fine-tuned on Indian speech), converted to int8. Writes Hinglish in Roman letters "
                     "and keeps English words in English."},
    "large": {"kind": "speech", "label": "Whisper large-v3 (slowest, most accurate)", "repo": "Systran/faster-whisper-large-v3", "dir": "large-v3",
              "size_mb": 3100, "license": "MIT", "desc": "Needed for 'translate to English'. About 3 GB."},
    "medium": {"kind": "speech", "label": "Whisper medium", "repo": "Systran/faster-whisper-medium", "dir": "medium", "size_mb": 1530, "license": "MIT",
               "desc": "Middle ground between speed and accuracy."},
    "small": {"kind": "speech", "label": "Whisper small (quick drafts)", "repo": "Systran/faster-whisper-small", "dir": "small", "size_mb": 485,
              "license": "MIT", "desc": "Small and quick; less accurate."},
    "matting": {"kind": "vision", "label": "Person cut-out (for 'text behind you' templates)", "dir": "matting", "size_mb": 14, "license": "GPL-3.0",
                "url": "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx",
                "file": "rvm_mobilenetv3_fp32.onnx",
                "desc": "Robust Video Matting (MobileNetV3). Lets big words sit behind the speaker. Downloaded from the project's GitHub release."},
}

_jobs = {}   # id -> {"state": "downloading"|"error", "error": str, "started": t}
_lock = threading.Lock()


def _dir(mid):
    return MODELS / REGISTRY[mid]["dir"]


def _cache_snapshot(mid):
    """a model downloaded by an earlier version of the app sits in the Hugging Face cache layout (models/models--org--name/snapshots/<hash>)"""
    repo = REGISTRY[mid].get("repo")
    if not repo:
        return None
    snaps = MODELS / ("models--" + repo.replace("/", "--")) / "snapshots"
    if snaps.is_dir():
        for s in sorted(snaps.iterdir()):
            if (s / "model.bin").exists():
                return s
    return None


def path(mid):
    """Where the finished model is, or None."""
    info = REGISTRY[mid]
    d = _dir(mid)
    if info["kind"] == "vision":
        f = d / info["file"]
        return f if f.exists() else None
    if (d / "model.bin").exists() and (d / "config.json").exists():
        return d
    return _cache_snapshot(mid)


def installed(mid):
    return path(mid) is not None


def _size(p):
    total = 0
    if p.exists():
        for f in p.rglob("*"):
            try:
                if f.is_file():
                    total += f.stat().st_size
            except OSError:
                pass
    return total


def status():
    out = []
    with _lock:
        jobs = {k: dict(v) for k, v in _jobs.items()}
    for mid, info in REGISTRY.items():
        j = jobs.get(mid)
        row = {"id": mid, "kind": info["kind"], "label": info["label"], "desc": info["desc"], "size_mb": info["size_mb"], "license": info["license"],
               "installed": installed(mid), "downloading": bool(j and j["state"] == "downloading"), "error": (j or {}).get("error", ""), "progress": 0.0}
        if row["downloading"]:
            tmp = _dir(mid) if info["kind"] == "speech" else _dir(mid) / (info["file"] + ".part")
            row["progress"] = min(0.99, _size(tmp) / (info["size_mb"] * 1024 * 1024 * 0.995))
        out.append(row)
    return out


def _download_speech(mid):
    from huggingface_hub import snapshot_download
    info = REGISTRY[mid]
    d = _dir(mid)
    d.mkdir(parents=True, exist_ok=True)
    snapshot_download(info["repo"], local_dir=str(d), allow_patterns=["*.json", "*.txt", "model.bin", "LICENSE*", "NOTICE*", "README*"])
    shutil.rmtree(d / ".cache", ignore_errors=True)


def _download_file(mid):
    info = REGISTRY[mid]
    d = _dir(mid)
    d.mkdir(parents=True, exist_ok=True)
    part = d / (info["file"] + ".part")
    req = urllib.request.Request(info["url"], headers={"User-Agent": "captions-studio"})
    with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    part.replace(d / info["file"])


def download(mid):
    """Blocking download (command line: python captions.py download apex)."""
    (_download_speech if REGISTRY[mid]["kind"] == "speech" else _download_file)(mid)


def _run(mid):
    try:
        (_download_speech if REGISTRY[mid]["kind"] == "speech" else _download_file)(mid)
        with _lock:
            _jobs.pop(mid, None)
    except Exception as e:  # network, disk full, ...
        with _lock:
            _jobs[mid] = {"state": "error", "error": str(e)[:300], "started": time.time()}


def start_download(mid):
    if mid not in REGISTRY:
        raise KeyError(mid)
    with _lock:
        j = _jobs.get(mid)
        if j and j["state"] == "downloading":
            return
        _jobs[mid] = {"state": "downloading", "error": "", "started": time.time()}
    threading.Thread(target=_run, args=(mid,), daemon=True).start()


def remove(mid):
    info = REGISTRY[mid]
    shutil.rmtree(_dir(mid), ignore_errors=True)
    snap = _cache_snapshot(mid)
    if snap is not None:
        shutil.rmtree(snap.parent.parent, ignore_errors=True)


def resolve(model):
    """A model id from the UI ('turbo', 'apex', ...) -> (path or name for faster-whisper, label). A path given directly is used as it is."""
    if model in REGISTRY and REGISTRY[model]["kind"] == "speech":
        p = path(model)
        if p is None:
            raise RuntimeError("The speech model '%s' is not downloaded yet. Open Settings (gear icon) -> Models and press Download." % REGISTRY[model]["label"])
        return str(p), model
    return model, model
