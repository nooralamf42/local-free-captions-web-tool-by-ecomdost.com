"""Style preview images (cached) rendered through the exact same ASS+ffmpeg path as real output."""
import hashlib
import json
import os
import subprocess
import threading

from .ass import build_ass, resolve_style
from .render import render_sample_frame
from .util import ROOT, WORK, _NOWIN, ffmpeg_bin

SAMPLE = ["Make", "every", "word", "pop"]


def sample_words(text=None):
    ws = (text or " ".join(SAMPLE)).split()
    return [{"w": w, "s": i * 0.25, "e": i * 0.25 + 0.25} for i, w in enumerate(ws)]


def style_preview(style, overrides=None, t=0.6, text=None):
    d = WORK / "previews"
    d.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(json.dumps([style, overrides or {}, t, text], sort_keys=True).encode()).hexdigest()[:12]
    p = d / ("%s_%s.png" % (style, key))
    if not p.exists():
        words = sample_words(text)
        st = resolve_style(style, overrides)
        render_sample_frame(build_ass(words, style, overrides), p, t, crop_y=st["y"] / 100 * 1920)
    return p


PREVIEW_DIR = ROOT / "samples" / "preview"
_PV_LOCK = threading.Lock()      # one cut-out at a time
_PV_SEM = threading.Semaphore(2)  # and at most two preview renders at once


def _preview_matte():
    """Person cut-out of the preview clip, made once (RVM) and kept."""
    out = WORK / "previews" / "preview_matte.mp4"
    with _PV_LOCK:
        if not out.exists():
            from .matte import make_matte
            out.parent.mkdir(parents=True, exist_ok=True)
            make_matte(PREVIEW_DIR / "clip.mp4", out, fit="cover")
    return out


def style_clip(style, overrides=None):
    """(mp4, png) preview of a template on a short clip of a real person, through the same renderer as real output.
    The big word is set High and the small text Large, which shows a look off best; cached by style+overrides."""
    from .render import render_video
    d = WORK / "previews"
    d.mkdir(parents=True, exist_ok=True)
    ov = dict(overrides or {})
    st = resolve_style(style, ov)
    if st["behind"]:
        ov.setdefault("hero_y", 13)
    if st["behind"]:
        ov.setdefault("size", int(st["size"] * 1.3))
    ov["safe"] = False
    key = hashlib.md5(json.dumps([style, ov, "v19"], sort_keys=True).encode()).hexdigest()[:12]
    mp4, png = d / ("clip_%s_%s.mp4" % (style, key)), d / ("clip_%s_%s.png" % (style, key))
    if not (mp4.exists() and png.exists()):
        words = [{"w": w, "s": s0, "e": e0} for w, s0, e0 in json.loads((PREVIEW_DIR / "words.json").read_text(encoding="utf-8"))]
        with _PV_SEM:
            if not (mp4.exists() and png.exists()):
                doc = build_ass(words, style, ov, split=bool(st["behind"]))
                behind_doc, ass = doc if st["behind"] else (None, doc)
                tmp = mp4.with_suffix(".part.mp4")
                render_video(PREVIEW_DIR / "clip.mp4", ass, tmp, fit="cover", encoder="x264", quality=27,
                             behind_ass=behind_doc, matte=_preview_matte() if st["behind"] else None, out_size=(360, 640))
                os.replace(tmp, mp4)
                subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-ss", "1.7", "-i", str(mp4),
                                "-frames:v", "1", str(png)], capture_output=True, **_NOWIN)
    return mp4, png
