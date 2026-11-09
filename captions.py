#!/usr/bin/env python
"""Free local auto-captions. Usage:

  python captions.py reel.mp4 --style hormozi
  python captions.py a.mp4 b.mp4 c.mp4 --style hormozi --style karaoke --mode roman
  python captions.py reel.mp4 --style all --mode translate
  python captions.py serve            # web UI on http://127.0.0.1:8765
  python captions.py download apex    # fetch a model (turbo | apex | large | medium | small | matting)
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from engine.util import OUTPUTS, safe_name  # noqa: E402


def build_parser():
    p = argparse.ArgumentParser(description="Free local auto-captions (faster-whisper + ffmpeg).")
    p.add_argument("videos", nargs="*", help="video/audio files; or the word 'serve' to start the web UI")
    p.add_argument("--style", action="append", help="style name (repeat for several outputs, or 'all'). see --list-styles")
    p.add_argument("--list-styles", action="store_true")
    p.add_argument("--mode", default="spoken", choices=["spoken", "roman", "translate"],
                   help="spoken = as said (Hindi in Devanagari); roman = Hinglish in Roman letters; translate = English")
    p.add_argument("--lang", default="auto", help="auto | en | hi | ... (language spoken)")
    p.add_argument("--model", default="turbo", help="turbo (default) | apex (Hinglish) | large | medium | small. Download models first: python captions.py download turbo")
    p.add_argument("--roman-method", default="translit", choices=["translit", "prompt"])
    p.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    p.add_argument("--out", default=str(OUTPUTS), help="output folder")
    p.add_argument("--fit", default="auto", choices=["auto", "cover", "contain", "blur", "keep"],
                   help="how to fit non-9:16 video into 1080x1920 (auto: blur background for landscape)")
    p.add_argument("--encoder", default="auto", choices=["auto", "nvenc", "x264"])
    p.add_argument("--quality", type=int, default=21, help="CRF/CQ (lower=better)")
    # style tweaks
    p.add_argument("--size", type=int, help="font size px (1080x1920 canvas)")
    p.add_argument("--y", type=float, help="caption vertical centre, %% of height (default per style ~66)")
    p.add_argument("--color", help="text colour #RRGGBB")
    p.add_argument("--active", help="highlight colour #RRGGBB")
    p.add_argument("--outline-color", help="outline colour #RRGGBB")
    p.add_argument("--box-color", help="box/pill colour #RRGGBB")
    p.add_argument("--words", type=int, help="max words on screen at once")
    p.add_argument("--font", help="font family from fonts/ (e.g. 'Poppins Black', Anton, Bangers)")
    p.add_argument("--upper", dest="uppercase", action="store_true", default=None)
    p.add_argument("--no-upper", dest="uppercase", action="store_false")
    p.add_argument("--offset", type=float, default=0.0, help="shift caption timing seconds (+ later, - earlier)")
    # workflow
    p.add_argument("--edit", action="store_true", help="pause after transcription so you can edit <name>.txt")
    p.add_argument("--transcript-only", action="store_true", help="only transcribe (writes .json .txt .srt)")
    p.add_argument("--retranscribe", action="store_true", help="ignore cached transcript")
    p.add_argument("--srt", action="store_true", help="also write .srt")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true", help="serve: don't open the browser")
    return p


def overrides_from(a):
    o = {}
    for k in ("size", "y", "color", "active", "outline_color", "box_color", "words", "font", "uppercase"):
        v = getattr(a, k)
        if v is not None:
            o[k] = v
    if a.words:
        o["max_chars"] = max(14, a.words * 9)
    return o


def main(argv=None):
    a = build_parser().parse_args(argv)
    from engine.styles import STYLES
    if a.list_styles:
        for k, s in STYLES.items():
            print("%-10s %-10s %s" % (k, s["mode"], s["desc"]))
        return 0
    if a.videos[:1] == ["download"]:
        from engine import models
        ids = a.videos[1:] or [m for m, i in models.REGISTRY.items() if i["kind"] == "speech" and m in ("turbo", "apex")] + ["matting"]
        for mid in ids:
            if mid not in models.REGISTRY:
                sys.exit("unknown model '%s'. choose from: %s" % (mid, ", ".join(models.REGISTRY)))
            if models.installed(mid):
                print("%s: already downloaded" % mid)
                continue
            print("%s: downloading %s (~%d MB)..." % (mid, models.REGISTRY[mid]["label"], models.REGISTRY[mid]["size_mb"]))
            models.download(mid)
            print("%s: done" % mid)
        return
    if a.videos[:1] == ["serve"]:
        import server
        server.run(port=a.port, open_browser=not a.no_browser)
        return 0
    if not a.videos:
        build_parser().print_help()
        return 1
    styles = a.style or ["hormozi"]
    if "all" in styles:
        styles = list(STYLES)
    for s in styles:
        if s not in STYLES:
            print("unknown style %r. try --list-styles" % s)
            return 2

    from engine.ass import build_ass, words_from_transcript, to_srt
    from engine.edit import apply_edits
    from engine.render import render_video
    from engine.transcribe import transcribe

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ov = overrides_from(a)
    T0 = time.time()
    summary = []
    for v in a.videos:
        vp = Path(v)
        if not vp.exists():
            print("missing:", v)
            continue
        stem = safe_name(vp.stem)
        jpath = out_dir / (stem + ".captions.json")
        tpath = out_dir / (stem + ".txt")
        print("\n== %s" % vp.name)
        if jpath.exists() and not a.retranscribe:
            tr = json.loads(jpath.read_text(encoding="utf-8"))
            if tr.get("mode") != a.mode:
                tr = None
            else:
                print("using cached transcript (%s). --retranscribe to redo" % jpath.name)
        else:
            tr = None
        if tr is None:
            last = [0]

            def prog(f):
                if f - last[0] >= 0.1 or f >= 1:
                    last[0] = f
                    print("  transcribing %3d%%" % (f * 100), end="\r", flush=True)

            tr = transcribe(vp, lang=a.lang, mode=a.mode, model=a.model, device=a.device,
                            roman_method=a.roman_method, progress=prog, log=lambda m: print("  " + m))
            print("  transcribed in %.1fs on %s (%s), lang=%s, model=%s" % (
                tr["seconds"], tr["device"], tr["compute"], tr["language"], tr["model"]))
            jpath.write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")
        tpath.write_text("\n".join(s["text"] for s in tr["segments"]) + "\n", encoding="utf-8")
        if a.edit:
            input("  edit %s (one line per caption line), save, press Enter... " % tpath)
            lines = tpath.read_text(encoding="utf-8").splitlines()
            tr = apply_edits(tr, lines + [None] * (len(tr["segments"]) - len(lines)))
            jpath.write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")
        words = words_from_transcript(tr)
        if a.srt or a.transcript_only:
            (out_dir / (stem + ".srt")).write_text(to_srt(words), encoding="utf-8")
            print("  wrote", stem + ".srt")
        if a.transcript_only:
            continue
        for st in styles:
            ass = build_ass(words, st, ov, offset=a.offset)
            outp = out_dir / ("%s_%s.mp4" % (stem, st))
            res = render_video(vp, ass, outp, fit=a.fit, encoder=a.encoder, quality=a.quality,
                               progress=lambda f: print("  render %-10s %3d%%" % (st, f * 100), end="\r", flush=True),
                               log=print)
            print("  %-10s -> %s  [%s, %.1fs]" % (st, outp, res["encoder"], res["seconds"]))
            summary.append((vp.name, st, str(outp), res["seconds"]))
    print("\nDone: %d video(s) in %.1fs" % (len(summary), time.time() - T0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
