"""Subject cut-out for 'text behind you' templates: Robust Video Matting (ONNX) -> grayscale matte video.

matte.mp4 is white where the person is, black elsewhere, same framing (fit applied) as the 540x960 preview proxy.
Export then composes:  background video  <  text  <  person (video * matte)  <  front captions.
"""
import subprocess
import time
from pathlib import Path

import numpy as np

from .render import video_filter
from .util import MODELS, _NOWIN, ffmpeg_bin, probe, setup_cuda_paths

MODEL = MODELS / "matting" / "rvm_mobilenetv3_fp32.onnx"
W, H = 540, 960


def matte_available():
    return MODEL.exists()


def make_matte(video, out, fit="auto", progress=None, log=None):
    """Writes `out` (mp4, yuv420p, full-range gray). Returns dict(frames, seconds, provider)."""
    import onnxruntime as ort
    if not MODEL.exists():
        raise RuntimeError("The person cut-out model is not downloaded yet. Open Settings (gear icon) -> Models and press Download.")
    log = log or (lambda *_: None)
    setup_cuda_paths()
    t0 = time.time()
    info = probe(video)
    vf, _ = video_filter(info, W, H, fit)
    fps = min(30.0, max(10.0, info["fps"]))
    total = max(1, int(info["duration"] * fps))
    so = ort.SessionOptions()
    so.log_severity_level = 3
    so.enable_mem_pattern = False   # required by the DirectML provider
    avail = ort.get_available_providers()
    order = [p for p in ("DmlExecutionProvider", "CUDAExecutionProvider") if p in avail] + ["CPUExecutionProvider"]
    sess = ort.InferenceSession(str(MODEL), so, providers=order)
    prov = sess.get_providers()[0]
    log("Cutting out the person (%s)…" % ("GPU" if prov != "CPUExecutionProvider" else "CPU — slower"))
    rec = [np.zeros([1, 1, 1, 1], dtype=np.float32) for _ in range(4)]
    ratio = np.array([0.5], dtype=np.float32)

    vfs = (vf + "," if vf != "null" else "") + "fps=%.3f,format=rgb24" % fps
    dec = subprocess.Popen([ffmpeg_bin(), "-v", "error", "-i", str(video), "-an", "-vf", vfs, "-f", "rawvideo", "-"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **_NOWIN)
    out = Path(out)
    tmp = out.with_suffix(".part.mp4")
    enc = subprocess.Popen([ffmpeg_bin(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "%dx%d" % (W, H),
                            "-r", "%.3f" % fps, "-i", "-", "-vf", "scale=out_range=full:flags=fast_bilinear,format=yuvj420p",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-color_range", "pc", "-g", "12",
                            "-movflags", "+faststart", str(tmp)],
                           stdin=subprocess.PIPE, stderr=subprocess.DEVNULL, **_NOWIN)
    n, fsz = 0, W * H * 3
    try:
        while True:
            buf = dec.stdout.read(fsz)
            if len(buf) < fsz:
                break
            src = np.frombuffer(buf, np.uint8).reshape(1, H, W, 3).transpose(0, 3, 1, 2).astype(np.float32) / 255.0
            _, pha, *rec = sess.run(None, {"src": np.ascontiguousarray(src), "r1i": rec[0], "r2i": rec[1], "r3i": rec[2],
                                           "r4i": rec[3], "downsample_ratio": ratio})
            alpha = (np.clip(pha[0, 0], 0, 1) * 255).astype(np.uint8)
            enc.stdin.write(alpha.tobytes())
            n += 1
            if progress and n % 15 == 0:
                progress(min(0.99, n / total))
    finally:
        try:
            enc.stdin.close()
        except Exception:
            pass
        enc.wait()
        dec.stdout.close()
        dec.wait()
    if n == 0 or enc.returncode != 0:
        raise RuntimeError("matte encode failed")
    tmp.replace(out)
    if progress:
        progress(1.0)
    return {"frames": n, "seconds": round(time.time() - t0, 1), "provider": prov}

