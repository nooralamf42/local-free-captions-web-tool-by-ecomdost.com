"""Dev tool: renders one template over a plain background as a 360x640 / 32 fps test video, so you can look at how it animates without
uploading a video.   usage: python tools/our_clip.py <template-id> <out.mp4> ['{"size": 90}']   (needs ffmpeg on PATH)"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.ass import build_ass  # noqa: E402
from engine.render import _ass_filter, _write_ass  # noqa: E402
from engine.util import ROOT  # noqa: E402

FF = shutil.which("ffmpeg") or "ffmpeg"
WORDS = [("Maine", .45, .65), ("bas", .65, .80), ("video", .80, 1.05), ("upload", 1.05, 1.35), ("kiya,", 1.35, 1.9),
         ("ek", 2.0, 2.15), ("template", 2.15, 2.5), ("choose", 2.5, 2.9), ("aur", 3.4, 3.55), ("literally", 3.55, 4.2),
         ("ek", 4.2, 4.4), ("minute", 4.4, 4.7), ("mein", 4.7, 4.85), ("captions", 4.85, 5.3), ("ready.", 5.3, 5.8),
         ("That's", 6.0, 6.3), ("it.", 6.3, 6.7)]

if __name__ == "__main__":
    style, out = sys.argv[1], sys.argv[2]
    OV = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    ass = _write_ass(build_ass([{"w": w, "s": s, "e": e} for w, s, e in WORDS], style, dict({"safe": False}, **OV)))
    rel = ass.relative_to(ROOT).as_posix()
    subprocess.run([FF, '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=0x20242c:s=1080x1920:d=7.25:r=32', '-vf',
                    _ass_filter(rel) + ',scale=360:640', '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', out], cwd=str(ROOT))
    print(out)
