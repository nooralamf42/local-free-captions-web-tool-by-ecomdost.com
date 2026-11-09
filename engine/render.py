"""Burn ASS captions into a 1080x1920 MP4 with ffmpeg (NVENC if available, else x264). Audio is kept."""
import os
import re
import subprocess
import uuid
from pathlib import Path

from .util import FONTS, ROOT, WORK, _NOWIN, ffmpeg_bin, probe

_nvenc_ok = None


def nvenc_available():
    global _nvenc_ok
    if _nvenc_ok is None:
        r = subprocess.run([ffmpeg_bin(), "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.2",
                            "-c:v", "h264_nvenc", "-f", "null", "-"], capture_output=True, text=True, **_NOWIN)
        _nvenc_ok = r.returncode == 0
    return _nvenc_ok


def video_filter(info, width, height, fit):
    ar = info["width"] / max(1, info["height"])
    target = width / height
    if fit == "auto":
        fit = "cover" if abs(ar - target) / target < 0.12 else "blur"
    if fit == "keep":
        return "null", fit
    if fit == "cover":
        return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1", fit
    if fit == "contain":
        return (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"), fit
    # blur background fill for landscape/square sources
    return (f"split[a][b];[a]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
            f"boxblur=40:6,eq=brightness=-0.08[bg];[b]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"), fit


def _ass_filter(ass_rel):
    # relative posix path (cwd=ROOT) avoids Windows drive-colon escaping in filter strings
    return f"ass=filename='{ass_rel}':fontsdir='{FONTS.relative_to(ROOT).as_posix()}'"


def _write_ass(ass_text):
    d = WORK / "tmp"
    d.mkdir(parents=True, exist_ok=True)
    p = d / (uuid.uuid4().hex[:10] + ".ass")
    p.write_text(ass_text, encoding="utf-8")
    return p


def render_video(video, ass_text, out, width=1080, height=1920, fit="auto", encoder="auto", quality=21,
                 progress=None, log=None, behind_ass=None, matte=None, out_size=None, fps=None):
    """Returns dict(encoder, seconds, fit). progress(frac) optional.
    behind_ass + matte: "text behind you" -> background < hero text < person (video x matte) < front captions."""
    import time
    info = probe(video)
    vf, used_fit = video_filter(info, width, height, fit)
    if fps:   # 60 fps etc.: set the frame rate first, so the captions are drawn on every output frame
        vf = "fps=%s,%s" % (fps, vf) if vf != "null" else "fps=%s" % fps
    ass = _write_ass(ass_text)
    rel = ass.relative_to(ROOT).as_posix()
    chain = (vf + "," + _ass_filter(rel)) if vf != "null" else _ass_filter(rel)
    if out_size:
        chain += ",scale=%d:%d" % out_size
    bass = None
    inputs = ["-i", str(video)]
    if behind_ass and matte:
        bass = _write_ass(behind_ass)
        brel = bass.relative_to(ROOT).as_posix()
        fps = float(fps) if fps else min(60.0, max(10.0, info["fps"]))
        inputs += ["-i", str(matte)]
        base = (vf if vf != "null" else "null")
        chain = (
            "[0:v]%s,format=rgba,split=2[bgA][bgB];"
            "color=c=black@0.0:s=%dx%d:r=%.3f:d=%.3f,format=rgba,%s:alpha=1[tb];"
            "[bgA][tb]overlay=format=auto:eof_action=pass[x];"
            "[1:v]scale=%d:%d:flags=bicubic,gblur=sigma=1.2,format=gray[m];"
            "[bgB][m]alphamerge[subj];"
            "[x][subj]overlay=format=auto:eof_action=pass[y];"
            "[y]%s%s,format=yuv420p[outv]" % (base, width, height, fps, info["duration"] + 0.5, _ass_filter(brel), width, height, _ass_filter(rel), (",scale=%d:%d" % out_size) if out_size else ""))
    use_nv = encoder == "nvenc" or (encoder == "auto" and nvenc_available())
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    def cmd(nv):
        c = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1", "-nostats",
             ] + inputs + (["-filter_complex", chain, "-map", "[outv]", "-map", "0:a:0?", "-t", "%.3f" % info["duration"]] if bass else ["-vf", chain, "-map", "0:v:0", "-map", "0:a:0?"])
        if nv:
            c += ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", str(quality + 2), "-b:v", "0",
                  "-profile:v", "high", "-level", "5.2"]
        else:
            c += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(quality), "-profile:v", "high"]
        c += ["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        c += (["-c:a", "copy"] if info["acodec"] in ("aac", "mp3") else ["-c:a", "aac", "-b:a", "192k"])
        c += [str(out)]
        return c

    t0 = time.time()
    dur = max(info["duration"], 0.1)
    for nv in ([True, False] if use_nv else [False]):
        p = subprocess.Popen(cmd(nv), cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **_NOWIN)
        for line in p.stdout:
            m = re.match(r"out_time_us=(\d+)", line)
            if m and progress:
                progress(min(0.99, int(m.group(1)) / 1e6 / dur))
        err = p.stderr.read()
        p.wait()
        if p.returncode == 0:
            ass.unlink(missing_ok=True)
            if bass:
                bass.unlink(missing_ok=True)
            if progress:
                progress(1.0)
            return {"encoder": "h264_nvenc" if nv else "libx264", "seconds": round(time.time() - t0, 1), "fit": used_fit}
        if log:
            log("ffmpeg failed (%s): %s" % ("nvenc" if nv else "x264", err.strip()[-400:]))
    raise RuntimeError("ffmpeg failed: " + err.strip()[-600:])


def render_sample_frame(ass_text, out_png, t, width=1080, height=1920, crop_y=None):
    """Style preview on a synthetic gradient background (no video needed). crop_y: centre of a 1080x540 strip."""
    ass = _write_ass(ass_text)
    rel = ass.relative_to(ROOT).as_posix()
    src = (f"gradients=s={width}x{height}:c0=0x1c2541:c1=0x7b2d5e:c2=0xf2a65a:x0=0:y0=0:x1={width}:y1={height}:d=1:r=10")
    vf = _ass_filter(rel) + f",trim=start={t:.3f}"
    if crop_y is not None:
        vf += ",crop=%d:540:0:%d" % (width, max(0, min(height - 540, int(crop_y - 270))))
    r = subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", src,
                        "-vf", vf, "-frames:v", "1", str(out_png)],
                       cwd=str(ROOT), capture_output=True, text=True, **_NOWIN)
    ass.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-500:])
    return out_png


def render_frame(video, ass_text, out_png, t, width=1080, height=1920, fit="auto"):
    info = probe(video)
    vf, _ = video_filter(info, width, height, fit)
    ass = _write_ass(ass_text)
    rel = ass.relative_to(ROOT).as_posix()
    chain = (vf + "," + _ass_filter(rel)) if vf != "null" else _ass_filter(rel)
    r = subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-ss", "%.3f" % t, "-i", str(video),
                        "-vf", chain, "-frames:v", "1", str(out_png)], cwd=str(ROOT), capture_output=True, text=True, **_NOWIN)
    ass.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-500:])
    return out_png


def make_proxy(video, out, fit="auto", width=540, height=960):
    """Low-res 9:16 preview of exactly what the export frames (fit applied), keyframe-dense for scrubbing."""
    info = probe(video)
    vf, _ = video_filter(info, width, height, fit)
    vf = (vf + ",") if vf != "null" else ""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part.mp4")
    for nv in ([True, False] if nvenc_available() else [False]):
        enc = (["-c:v", "h264_nvenc", "-preset", "p2", "-rc", "vbr", "-cq", "30", "-b:v", "0", "-g", "12"] if nv else
               ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-g", "12"])
        r = subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf",
                            vf + "fps=30,format=yuv420p", "-map", "0:v:0", "-map", "0:a:0?"] + enc +
                           ["-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(tmp)],
                           capture_output=True, text=True, **_NOWIN)
        if r.returncode == 0:
            tmp.replace(out)
            return out
    raise RuntimeError("proxy failed: " + r.stderr.strip()[-300:])


def peaks(video, per_sec=20):
    """Waveform peaks 0..100 for the timeline."""
    import numpy as np
    r = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                       capture_output=True, **_NOWIN)
    a = np.abs(np.frombuffer(r.stdout, dtype=np.int16).astype("float32"))
    step = 8000 // per_sec
    n = len(a) // step
    if n == 0:
        return []
    p = a[: n * step].reshape(n, step).max(axis=1)
    p = (p / max(1.0, float(np.percentile(p, 99)))).clip(0, 1) * 100
    return [int(x) for x in p]


def render_clip(ass_text, out_mp4, out_png, crop_y, dur=2.23):
    """640x465 looping style-preview video + poster, same pipeline as real output."""
    ass = _write_ass(ass_text)
    rel = ass.relative_to(ROOT).as_posix()
    src = "gradients=s=1080x1920:c0=0x0b0b10:c1=0x23232e:x0=0:y0=0:x1=1080:y1=1920:d=%.2f:r=24" % dur
    cy = max(0, min(1920 - 786, int(crop_y - 393)))
    vf = _ass_filter(rel) + ",crop=1080:786:0:%d,scale=640:466,format=yuv420p" % cy
    r = subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", src, "-vf", vf,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-movflags", "+faststart", str(out_mp4)],
                       cwd=str(ROOT), capture_output=True, text=True, **_NOWIN)
    if r.returncode == 0:
        r = subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-ss", "1.25", "-i", str(out_mp4),
                            "-frames:v", "1", str(out_png)], capture_output=True, text=True, **_NOWIN)
    ass.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:])





