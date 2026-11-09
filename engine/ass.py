"""Generate ASS subtitles (libass) for a style. Every effect is built from plain ASS tags so ffmpeg can burn it in."""
import re

from PIL import ImageFont

from . import motion
from .chunk import WEAK, flatten, make_phrases
from .styles import DEFAULT_STYLE, FONT_FILES, STYLES, _BASE
from .util import FONTS

W, H = 1080, 1920
BS = chr(92)
# Instagram Reels UI: bottom ~22% (caption/buttons), top ~12%, right rail ~12%
SAFE = dict(top=0.12, bottom=0.22, left=0.07, right=0.12)
MAX_TEXT_W = 860

OVERRIDE_KEYS = set(_BASE.keys())

_fonts = {}


def _font_ratio(path):
    f = _fonts.get(("r", path))
    if f is None:
        a, d = ImageFont.truetype(str(path), 100).getmetrics()
        f = _fonts[("r", path)] = (a + d) / 100.0
    return f


def text_width(font, fs, text, spacing=0):
    path = FONTS / FONT_FILES.get(font, "Poppins-ExtraBold.ttf")
    em = fs / _font_ratio(path)
    key = (str(path), round(em, 1))
    f = _fonts.get(key)
    if f is None:
        f = _fonts[key] = ImageFont.truetype(str(path), em)
    return f.getlength(text) + spacing * len(text)


def _bgr(hexcol):
    h = hexcol.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = h[0:2], h[2:4], h[4:6]
    return (b + g + r).upper()


def c(hexcol, alpha=0):
    """ASS inline colour &HBBGGRR& (alpha separate)."""
    return "&H" + _bgr(hexcol) + "&"


def style_color(hexcol, alpha=0):
    return "&H%02X%s" % (alpha, _bgr(hexcol))


def ts(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def resolve_style(name, overrides=None):
    st = dict(STYLES.get(name) or STYLES[DEFAULT_STYLE])
    for k, v in (overrides or {}).items():
        if k in OVERRIDE_KEYS and v is not None and v != "":
            st[k] = v
    for k in ("size", "outline", "shadow", "blur", "box_pad", "active_scale", "words", "max_chars", "y", "x", "spacing", "box_alpha", "hero_size", "hero_outline", "hero_shadow", "hero_blur", "hero_spacing", "hero_wmax", "hero_box_pad", "hero_opacity", "hero_y", "hero_x"):
        st[k] = float(st[k]) if k in ("y", "x", "hero_y", "hero_x") else int(float(st[k]))
    for k in ("safe", "behind", "hero_upper", "hero_italic", "hero_fill", "emph", "hero_seq"):
        st[k] = st.get(k, True) not in (False, 0, "0", "false", "False")
    st["uppercase"] = bool(st["uppercase"]) if not isinstance(st["uppercase"], str) else st["uppercase"].lower() in ("1", "true", "yes", "on")
    return st


_PUNCT_STRIP = re.compile(r"[,.;:।…\"“”()\[\]]+")


def clean_word(w, st):
    t = w.strip()
    t = _PUNCT_STRIP.sub("", t) if st.get("strip_punct", True) else t
    t = t.replace("{", "(").replace("}", ")").replace("\\", "")
    if st["uppercase"]:
        t = t.upper()
    return t


def layout_lines(words, st, maxw=None):
    """Greedy line break. Returns (lines [[idx...]], fs)."""
    fs = st["size"]
    maxw = maxw or (st.get("box_w") and st["box_w"] / 100.0 * W) or MAX_TEXT_W
    extra_k = max(0.0, st["active_scale"] / 100.0 - 1.0)  # active word grows; reserve its extra width
    if st["box"] in ("card", "capsule"):
        maxw -= 2 * st["box_pad"]
    for _ in range(6):
        space = text_width(st["font"], fs, " ", st["spacing"]) + word_gap(st)
        wid = [text_width(st["font"], fs, w, st["spacing"]) for w in words]
        extra = extra_k * max(wid)
        lines, cur, curw = [], [], 0.0
        for i, ww in enumerate(wid):
            add = ww if not cur else space + ww
            if cur and curw + add + extra > maxw:
                lines.append(cur)
                cur, curw = [i], ww
            else:
                cur.append(i)
                curw += add
        if cur:
            lines.append(cur)
        widest = max(sum(wid[i] for i in ln) + space * (len(ln) - 1) for ln in lines) + extra
        if widest <= maxw or fs < 30:
            return lines, fs, widest
        fs = int(fs * maxw / widest * 0.98)
    return lines, fs, widest


def word_gap(st):
    """extra px between words so thick outlines of neighbours don't touch"""
    if st["gap_em"]:
        return int(st["gap_em"] * st["size"])
    return max(4, int(st["outline"] * 1.1)) if st["box"] not in ("card", "capsule", "bubble") else 0


def _anim_tags(anim, sc, hidden=False):
    """Run-level tags for 'newly appeared' element, scale sc in percent."""
    if anim == "pop":
        return r"\fscx%d\fscy%d\t(0,110,\fscx%d\fscy%d)\t(110,190,\fscx%d\fscy%d)" % (
            sc * 0.78, sc * 0.78, sc * 1.07, sc * 1.07, sc, sc)
    if anim == "bounce":
        return r"\fscx%d\fscy%d\t(0,100,\fscx%d\fscy%d)\t(100,200,\fscx%d\fscy%d)" % (
            sc * 0.55, sc * 0.55, sc * 1.18, sc * 1.18, sc, sc)
    if anim in ("fade", "rise"):
        return r"\fscx%d\fscy%d\alpha&HFF&\t(0,130,\alpha&H00&)" % (sc, sc)
    return r"\fscx%d\fscy%d" % (sc, sc)


def _style_line(name, font, size, primary, secondary, outline_col, back, italic, spacing, bs, outw, shadow_w):
    return "Style: %s,%s,%d,%s,%s,%s,%s,0,%d,0,0,100,100,%d,0,%d,%d,%d,5,40,40,40,1" % (
        name, font, size, primary, secondary, outline_col, back, 1 if italic else 0, spacing, bs, outw, shadow_w)


def _doc(width, height, style_lines, events):
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\nScaledBorderAndShadow: yes\n"
        "YCbCr Matrix: None\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding\n%s\n\n[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" % (width, height, "\n".join(style_lines)))
    body = "\n".join("Dialogue: %d,%s,%s,%s,,0,0,0,,%s" % (ly, ts(a), ts(b), sn, t) for ly, a, b, t, sn in events)
    return header + body + "\n"


def _cap_style_line(st):
    boxed = st["box"] == "card"   # "block" is drawn as a rectangle of its own
    bs = 3 if st["box"] == "card" else 1
    outline_col = st["box_color"] if boxed else st["outline_color"]
    outw = st["box_pad"] if boxed else st["outline"]
    box_alpha = st["box_alpha"] if boxed else 0
    shadow_w = 0 if boxed else st["shadow"]
    return _style_line(
        "Cap", st["font"], st["size"],
        style_color(st["active"] if st["mode"] == "sweep" else st["color"]),
        style_color(st["color"] if st["mode"] == "sweep" else st["active"]),
        style_color(outline_col, box_alpha), style_color(st["shadow_color"]), st["italic"], st["spacing"], bs, outw, shadow_w)


def _rrect_path(w, h, r):
    """An ASS drawing of a w by h rectangle with corner radius r, from (0, 0)."""
    r = min(r, w / 2.0, h / 2.0)
    k = 0.5523 * r
    pts = [
        "m %d %d" % (r, 0),
        "l %d %d" % (w - r, 0),
        "b %d %d %d %d %d %d" % (w - r + k, 0, w, r - k, w, r),
        "l %d %d" % (w, h - r),
        "b %d %d %d %d %d %d" % (w, h - r + k, w - r + k, h, w - r, h),
        "l %d %d" % (r, h),
        "b %d %d %d %d %d %d" % (r - k, h, 0, h - r + k, 0, h - r),
        "l %d %d" % (0, r),
        "b %d %d %d %d %d %d" % (0, r - k, r - k, 0, r, 0),
    ]
    return " ".join(pts)


def _pill_path(w, h):
    """An ASS drawing of a pill (a rectangle with fully round ends) w by h from (0, 0)."""
    r, k = h / 2.0, 0.5523 * h / 2.0
    return ("m %d 0 l %d 0 b %d 0 %d %d %d %d b %d %d %d %d %d %d l %d %d b %d %d %d %d %d %d b %d %d %d 0 %d 0"
            % (r, w - r, w - r + k, w, r - k, w, r, w, r + k, w - r + k, h, w - r, h, r, h, r - k, h, 0, r + k, 0, r, 0, r - k, r - k, r))


def _events_for(phrases, st, width, height):
    """The caption events of a template: its own layout (engine/dynamic.py) when it has one, else the standard line."""
    if st.get("layout"):
        from . import dynamic
        return dynamic.build(phrases, st, width, height)
    return _emit_events(phrases, st, width, height)


def _emit_events(phrases, st, width, height):
    """Caption-line events (the 'Cap' style) for already-chunked phrases."""
    sy0 = st["y"] / 100.0 * height
    events = []
    blur = "\\blur%d" % st["blur"] if st["blur"] else ""

    for pi, p in enumerate(phrases):
        sy = p["y_pct"] / 100.0 * height if p.get("y_pct") is not None else sy0
        ws = [clean_word(w["w"], st) for w in p["words"]]
        keep = [i for i, t in enumerate(ws) if t]
        if not keep:
            continue
        pw = [p["words"][i] for i in keep]
        ws = [ws[i] for i in keep]
        emph_set = set()
        if st["emph_italic"] and len(pw) > 2:   # Delhi: the stressed word in an italic serif with a soft glow
            from .dynamic import pick_emph
            emph_set = set(pick_emph(pw, st, 1))
        lines, fs, widest = layout_lines(ws, st)
        nlines = len(lines)
        block_h = nlines * fs * 1.2
        if st["safe"]:  # keep inside the Reels safe area (top 12 %, bottom 22 %)
            ymin = SAFE["top"] * height + block_h / 2
            ymax = (1 - SAFE["bottom"]) * height - block_h / 2
        else:           # free placement: only keep it on screen
            ymin, ymax = block_h / 2 + 8, height - block_h / 2 - 8
        y = int(min(max(sy, ymin), max(ymin, ymax)))
        half = widest / 2 + 24
        xpx = int(min(max(st["x"] / 100.0 * width, half), max(half, width - half)))
        if st["align"] == "left":
            pos = r"\an4\pos(%d,%d)" % (int(p["left_px"]) if p.get("left_px") is not None else int(st["x"] / 100.0 * width), y)
        else:
            pos = r"\an5\pos(%d,%d)" % (xpx, y)
        pos0 = pos
        if st["anim"] == "slide":
            pos0 = r"\an5\move(%d,%d,%d,%d,0,160)" % (xpx, y + 46, xpx, y)
        n = len(ws)
        starts = [w["s"] for w in pw]
        starts[0] = min(starts[0], p["start"])
        ends = starts[1:] + [p["disp_end"]]
        pal = st["palette"]

        sep = "{\\fsp%d} {\\fsp%d}" % (st["spacing"] + word_gap(st), st["spacing"])

        def join(parts):
            return "\\N".join(sep.join(parts[i] for i in ln) for ln in lines)

        def word_color(i, active):
            if pal:
                return pal[(p.get("idx", pi) + i) % len(pal)] if st["words"] == 1 else st["color"]
            if st["mode"] == "highlight":
                return st["active"] if active else (st["dim"] or st["color"])
            return st["color"]

        is_card = st["box"] == "card"

        if st["mode"] == "sweep":
            parts = []
            for i, t in enumerate(ws):
                dur = max(1, int(round((ends[i] - starts[i]) * 100))) if i + 1 < n else max(1, int(round((pw[i]["e"] - starts[i]) * 100)))
                parts.append("{\\kf%d}%s" % (dur, t))
            txt = "{%s\\fs%d%s%s}" % (pos0, fs, blur, r"\fad(110,90)") + join(parts)
            events.append((1, p["start"], p["disp_end"], txt, "Cap"))
            continue

        if st["mode"] == "flash" and st["box"] == "block":
            padx, pady = st["box_pad"] * 2.4, st["box_pad"]
            lh = fs * 1.0
            bw, bh = widest + 2 * padx, nlines * lh + 2 * pady
            if st["align"] == "left":
                bx = int(st["x"] / 100.0 * width - padx)
            else:
                bx = int(xpx - widest / 2 - padx)
            by = int(y - bh / 2)
            rect = "{\\an7\\pos(%d,%d)\\1c%s\\bord0\\shad0\\p1}m 0 0 l %d 0 %d %d 0 %d{\\p0}" % (bx, by, c(st["box_color"]), bw, bw, bh, bh)
            events.append((0, p["start"], p["disp_end"], rect, "Cap"))
        if st["mode"] == "flash":
            sc = 100
            parts = []
            for i, t in enumerate(ws):
                parts.append("{\\1c%s%s}%s" % (c(word_color(i, False)), _anim_tags(st["anim"], sc), t))
            txt = "{%s\\fs%d%s\\fad(0,80)}" % (pos0, fs, blur) + join(parts)
            events.append((1, p["start"], p["disp_end"], txt, "Cap"))
            continue

        for i in range(n):
            t0 = starts[i] if i else p["start"]
            t1 = ends[i]
            if t1 - t0 < 0.02:
                continue
            first = i == 0
            parts, boxparts = [], []
            for j, t in enumerate(ws):
                if st["mode"] == "reveal":
                    visible = j <= i
                    newest = j == i
                    col = word_color(j, newest)
                    sc = 100
                    tags = "\\1c%s" % c(col)
                    if not visible:
                        tags += "\\1a&HFF&\\3a&HFF&\\4a&HFF&"
                        if is_card:
                            tags += "\\bord0"
                    elif newest and st["support_motion"] == "type":
                        # the reference style's "type": the letters of the word appear one after another
                        dur = int(motion.duration("type", 0, len(t)) * 1000)
                        step = dur / float(max(1, len(t)))
                        tags += "\\fscx100\\fscy100"
                        t = "".join("{\\alpha&HFF&\\t(%d,%d,\\alpha&H00&)}%s" % (k * step, k * step + 1, ch) for k, ch in enumerate(t))
                    elif newest:
                        tags += _anim_tags(st["anim"], sc)
                    else:
                        tags += "\\fscx100\\fscy100"
                    parts.append("{%s}%s" % (tags, t))
                    if st["box"] == "pill":
                        boxparts.append("{%s}%s" % ("\\1a&HFF&\\3a&HFF&\\bord0\\shad0", t))
                else:  # highlight
                    active = j == i
                    sc = st["active_scale"] if active else 100
                    col = word_color(j, active or (st["keep_spoken"] and j < i))
                    anim = _anim_tags(st["anim"], sc) if first else "\\fscx%d\\fscy%d" % (sc, sc)
                    if j in emph_set:
                        anim += BS + "fnInstrument Serif" + BS + "i1" + BS + "bord3" + BS + "3c&HFFFFFF&" + BS + "3a&H90&" + BS + "blur1.5"
                    if st["unsaid_opacity"] < 1 and j > i:   # not said yet: faded (Delhi, Word Focus, Deep Glow)
                        anim += "\\alpha&H%02X&" % int(round((1 - st["unsaid_opacity"]) * 255))
                    parts.append("{%s\\1c%s%s}%s" % ("\\r" if st["emph_italic"] else "", c(col), anim, t))
                    if st["box"] == "bubble" and active:
                        # a true pill behind the word said, placed from the measured line, cut in with a very short fade
                        space = text_width(st["font"], fs, " ", st["spacing"]) + word_gap(st)
                        wid = [text_width(st["font"], fs, w_, st["spacing"]) for w_ in ws]
                        for li, ln in enumerate(lines):
                            if j in ln:
                                total = sum(wid[q] for q in ln) + space * (len(ln) - 1)
                                left = (xpx - total / 2.0) if st["align"] != "left" else st["x"] / 100.0 * width
                                x0 = left + sum(wid[q] + space for q in ln[:ln.index(j)])
                                cy = y - nlines * fs * 1.2 / 2 + (li + 0.5) * fs * 1.2
                                pw, ph = wid[j] + 2 * st["pill_padx"] * fs, st["pill_h"] * fs
                                tags = "{" + BS + "an7" + BS + "pos(%d,%d)" % (x0 - st["pill_padx"] * fs, cy - ph / 2) + BS + "1c%s" % c(st["box_color"]) + BS + "bord0" + BS + "shad0" + BS + "alpha&H28&" + BS + "t(0,35," + BS + "alpha&H00&)" + BS + "p1}"
                                events.append((0, t0, t1, tags + _pill_path(pw, ph) + "{" + BS + "p0}", "Cap"))
                    if st["box"] == "pill":
                        if active:
                            boxparts.append("{\\1a&HFF&\\3c%s\\3a&H00&\\bord%d\\shad0%s%s}%s" % (
                                c(st["box_color"]), st["box_pad"], "\\blur1",
                                "\\fscx%d\\fscy%d" % (sc, sc), t))
                        else:
                            boxparts.append("{\\1a&HFF&\\3a&HFF&\\bord0\\shad0}%s" % t)
            fade = ""
            if st["mode"] == "highlight" and st["anim"] == "fade" and first:
                fade = "\\fad(110,0)"
            fin = int(st["fade_in"] * 1000) if first else 0
            fout = int(st["fade_out"] * 1000) if i == n - 1 else 0
            if fin or fout:   # the caption as a whole fades in / out (Customize: caption in / out)
                fade = "\\fad(%d,%d)" % (fin, fout)
            base ="%s\\fs%d%s%s" % (pos0 if first else pos, fs, blur, fade)
            if st["box"] == "capsule":
                bw = widest + 2 * st["box_pad"] * 1.8
                bh = nlines * fs * 1.2 + 2 * st["box_pad"] * 0.9
                bx = (xpx - widest / 2.0 - st["box_pad"] * 1.8) if st["align"] != "left" else st["x"] / 100.0 * width - st["box_pad"] * 1.8
                tags = "{" + BS + "an7" + BS + "pos(%d,%d)" % (bx, y - bh / 2.0) + BS + "1c%s" % c(st["box_color"]) + BS + "bord0" + BS + "shad0" + BS + "p1}"
                events.append((0, t0, t1, tags + _rrect_path(bw, bh, st["box_pad"] * 1.4) + "{" + BS + "p0}", "Cap"))
            if st["box"] == "bubble":
                # each word at its own measured place, so the text and the pill behind it always line up
                space = text_width(st["font"], fs, " ", st["spacing"]) + word_gap(st)
                wid = [text_width(st["font"], fs, w_, st["spacing"]) for w_ in ws]
                for li, ln in enumerate(lines):
                    total = sum(wid[q] for q in ln) + space * (len(ln) - 1)
                    left = (xpx - total / 2.0) if st["align"] != "left" else st["x"] / 100.0 * width
                    cy = y - nlines * fs * 1.2 / 2 + (li + 0.5) * fs * 1.2
                    for k, q in enumerate(ln):
                        x0 = left + sum(wid[r_] + space for r_ in ln[:k])
                        col = st["active"] if q == i else (st["dim"] or st["color"])
                        tags = "{" + BS + "an4" + BS + "pos(%d,%d)" % (x0, cy) + BS + "fs%d" % fs + BS + "fsp%d" % st["spacing"] + BS + "bord0" + BS + "shad0" + BS + "1c%s" % c(col) + "}"
                        events.append((1, t0, t1, tags + ws[q], "Cap"))
            elif st["box"] == "pill":
                events.append((0, t0, t1, "{%s}" % base + join(boxparts), "Cap"))
                # text layer: no outline when pill
                events.append((1, t0, t1, "{%s\\bord0\\shad0}" % base + join(parts), "Cap"))
            else:
                events.append((1, t0, t1, "{%s}" % base + join(parts), "Cap"))
    return events


# ---------------------------------------------------------------------------------------------------------------
# 'Text behind you': a big hero word sits BEHIND the person, a small caption line sits in FRONT.
# ---------------------------------------------------------------------------------------------------------------
_TOK = re.compile(r"[^\w]", re.U)


def pick_hero(words):
    """Indexes of the words shown big behind the subject: user-flagged ones, else the most 'keyword-like' word."""
    flagged = [i for i, w in enumerate(words) if w.get("hero")]
    if flagged:
        return flagged
    def score(i):
        t = _TOK.sub("", words[i]["w"].lower())
        return (0 if WEAK.match(t) else 1, min(len(t), 14), -i)
    return [max(range(len(words)), key=score)]


def _hero_style(st):
    h = dict(st)
    h.update(font=st["hero_font"], size=st["hero_size"], uppercase=st["hero_upper"], outline=st["hero_outline"],
             spacing=st["hero_spacing"], box=st["hero_box"] and "card", box_pad=st["hero_box_pad"], active_scale=100,
             anim="none", italic=st["hero_italic"])
    return h


def _hero_style_line(st):
    bs = 3 if st["hero_box"] else 1
    outline_col = st["hero_box"] or st["hero_outline_color"]
    outw = st["hero_box_pad"] if st["hero_box"] else st["hero_outline"]
    shadow_w = 0 if st["hero_box"] else st["hero_shadow"]
    return _style_line("Hero", st["hero_font"], st["hero_size"], style_color(st["hero_color"]), style_color(st["hero_color"]),
                       style_color(outline_col), style_color(st["hero_shadow_color"]), st["hero_italic"], st["hero_spacing"],
                       bs, outw, shadow_w)


def _hero_events(phrases, st, width, height):
    """-> (hero events for the layer behind the person, phrases left for the front caption line)."""
    hst = _hero_style(st)
    events, front = [], []
    for p in phrases:
        ws = p["words"]
        if not ws or not ws[0].get("behind", True):
            front.append(p)
            continue
        idx = list(range(len(ws))) if st["hero_mode"] == "phrase" else pick_hero(ws)
        texts = []
        for i in idx:
            t = clean_word(ws[i]["w"], hst)
            if t:
                texts.append(t)
        rest = [w for i, w in enumerate(ws) if i not in idx]
        if rest:
            front.append({"words": rest, "start": p["start"], "end": rest[-1]["e"], "disp_end": p["disp_end"]})
        if not texts:
            continue
        lines, fs, widest = layout_lines(texts, hst, maxw=st["hero_wmax"])
        if st["hero_fit"] and len(lines) == 1:
            grown = max(fs * 0.35, min(fs * 1.9, fs * (st["hero_fit"] / 100.0 * width) / max(widest, 1)))
            widest, fs = widest * grown / fs, int(grown)
        block_h = len(lines) * fs * 1.15
        y = int(min(max(st["hero_y"] / 100.0 * height, block_h / 2 + 4), height - block_h / 2 - 4))
        half = widest / 2
        x = int(min(max(st["hero_x"] / 100.0 * width, half), max(half, width - half)))
        t0 = min(ws[idx[0]]["s"], p["end"])
        t1 = p["disp_end"]
        sep = "{\\fsp%d} {\\fsp%d}" % (st["hero_spacing"] + word_gap(hst), st["hero_spacing"])
        body = "\\N".join(sep.join(texts[i] for i in ln) for ln in lines)
        ov = ""
        if not st["hero_fill"]:
            ov += "\\1a&HFF&"
        elif st["hero_opacity"] < 100:
            ov += "\\1a&H%02X&" % int((100 - st["hero_opacity"]) * 2.55)
        if st["hero_blur"]:
            ov += "\\blur%d" % st["hero_blur"]
        pos = r"\an5\pos(%d,%d)" % (x, y)
        if st["hero_anim"] == "slide":
            pos = r"\an5\move(%d,%d,%d,%d,0,180)" % (x, y + 60, x, y)
        anim = _anim_tags(st["hero_anim"], 100) if st["hero_anim"] != "slide" else ""
        events.append((0, t0, t1, "{%s\\fs%d%s%s%s}%s" % (pos, fs, ov, anim, "\\fad(0,80)" if st["hero_anim"] in ("fade", "slide") else "", body), "Hero"))
    return events, front


# Hinglish words the reference style leaves small however long they are
EMPH_SKIP = {"maine", "bas", "kiya", "kiye", "kiyaa", "karo", "karna", "kaise", "kyun", "abhi", "phir", "mera", "meri", "mere", "tum",
             "aapko", "aapka", "hamara", "humne", "bhi", "choose"}


def _fade(events, st):
    """A look's own fade in / out on every caption event; 0 leaves the hard cut."""
    a, b = int(st["fade_in"] * 1000), int(st["fade_out"] * 1000)
    if not (a or b):
        return events
    out = []
    for ev in events:
        txt = ev[3]
        if txt.startswith("{") and "\\fad(" not in txt:
            txt = "{\\fad(%d,%d)" % (a, b) + txt[1:]
        out.append(ev[:3] + (txt,) + ev[4:])
    return out


def _emph_events(phrases, st, width, height):
    """Key words big, stacked under the small line, each cutting in as it is said and staying to the end of the phrase.
    -> (events, phrases left for the small line)."""
    hst = _hero_style(st)
    events, front = [], []
    maxw = 0.9 * width
    for p in phrases:
        ws = p["words"]
        cand = [i for i, w in enumerate(ws)
                if clean_word(w["w"], hst) and not WEAK.match(_TOK.sub("", w["w"].lower())) and _TOK.sub("", w["w"].lower()) not in EMPH_SKIP
                and len(_TOK.sub("", w["w"])) >= 5]
        # the longest ones, kept in the order they are said
        idx = sorted(sorted(cand, key=lambda i: -len(ws[i]["w"]))[:int(st["emph_max"])])
        rest = [w for i, w in enumerate(ws) if i not in idx]
        widths = []
        for i in idx:
            t_ = clean_word(ws[i]["w"], hst)
            f_ = st["hero_size"]
            w_ = text_width(st["hero_font"], f_, t_, st["hero_spacing"])
            widths.append(min(w_, maxw))
        srow = sum(text_width(st["font"], st["size"], clean_word(w["w"], st), st["spacing"]) for w in rest) +             text_width(st["font"], st["size"], " ", 0) * max(0, len(rest) - 1)
        column = max(widths + [srow]) if widths else srow
        if rest:
            front.append({"words": rest, "start": p["start"], "end": rest[-1]["e"], "disp_end": p["disp_end"],
                          "left_px": width / 2.0 - column / 2.0})
        y = st["hero_y"] / 100.0 * height
        for k, i in enumerate(idx):
            t = clean_word(ws[i]["w"], hst)
            fs = st["hero_size"]
            wd = text_width(st["hero_font"], fs, t, st["hero_spacing"])
            if wd > maxw:
                fs = int(fs * maxw / wd)
            glow = ""
            if st["emph_glow"]:
                glow = "\\bord%d\\3c%s\\3a&H70&\\blur%d" % (max(2, st["emph_glow"] // 2), c(st["hero_color"]), st["emph_glow"])
            elif st["hero_blur"]:
                glow = "\\blur%d" % st["hero_blur"]
            cy = y + st["hero_size"] * st["emph_gap"] * 0.5
            events.append((1, ws[i]["s"], p["disp_end"],
                           "{\\an5\\pos(%d,%d)\\fs%d%s}%s" % (width // 2, cy, fs, glow, t), "Hero"))
            y += st["hero_size"] * st["emph_gap"]
    return events, front


def _hero_seq_events(phrases, st, width, height):
    """The key words of a phrase one after another in the hero slot, each from when it is said to when the next is; the other
    words stay in the small line. -> (hero events, phrases left for the front caption line)."""
    BS = chr(92)
    hst = _hero_style(st)
    events, front = [], []
    for pi, p in enumerate(phrases):
        ws = p["words"]
        if not ws or not ws[0].get("behind", True):
            front.append(p)
            continue
        alt = bool(st["alt_hero_y"]) and pi % 2 == 1
        flagged = [i for i, w in enumerate(ws) if w.get("hero")]
        cand = flagged or [i for i, w in enumerate(ws)
                           if clean_word(w["w"], hst) and not WEAK.match(_TOK.sub("", w["w"].lower()))
                           and _TOK.sub("", w["w"].lower()) not in EMPH_SKIP and len(_TOK.sub("", w["w"])) >= 5]
        nmax = max(1, int(st["hero_max"]))
        if st["hero_pick"] == "leading":
            idx = cand[:nmax]
        elif st["hero_pick"] == "trailing":
            idx = cand[-nmax:]
        else:
            idx = sorted(sorted(cand, key=lambda i: -len(ws[i]["w"]))[:nmax])
        rest = [w for i, w in enumerate(ws) if i not in idx]
        if rest:
            front.append({"words": rest, "start": p["start"], "end": rest[-1]["e"], "disp_end": p["disp_end"],
                          "y_pct": st["alt_y"] if alt and st["alt_y"] else None})
        for k, i in enumerate(idx):
            text = clean_word(ws[i]["w"], hst)
            fs = st["hero_size"]
            wd = max(text_width(st["hero_font"], fs, text, st["hero_spacing"]), 1)
            if st["hero_fit"]:
                fs = max(fs * 0.35, min(fs * (1.9 if st["hero_grow"] else 1.0), fs * (st["hero_fit"] / 100.0 * width) / wd))
            elif wd > st["hero_wmax"]:
                fs = fs * st["hero_wmax"] / wd
            t0 = ws[i]["s"]
            t1 = ws[idx[k + 1]]["s"] if k + 1 < len(idx) else p["disp_end"]
            if t1 - t0 < 0.05:
                continue
            hy = st["alt_hero_y"] if alt else st["hero_y"]
            wfit = wd * fs / float(st["hero_size"])
            hx0 = st["hero_x"] / 100.0 * width
            if st["hero_align"] == "left":      # the reference style's heroAlign: the big word sits against the left / right margin
                hx0 = 0.06 * width + wfit / 2.0
            elif st["hero_align"] == "right":
                hx0 = width - 0.06 * width - wfit / 2.0
            front_hero = alt or st["hero_front"]
            tags = BS + "an5" + BS + "pos(%d,%d)" % (int(hx0), int(hy / 100.0 * height))
            tags += BS + "fs%d" % int(fs)
            if st["hero_rot"]:
                tags += BS + "frz%.1f" % st["hero_rot"]
            if st["hero_colors"]:
                tags += BS + "1c%s" % c(st["hero_colors"][pi % len(st["hero_colors"])])
            if not st["hero_fill"]:
                tags += BS + "1a&HFF&"
            if st["hero_blur"]:
                tags += BS + "blur%d" % st["hero_blur"]
            sty = "HeroFront" if front_hero else "Hero"
            if st["hero_motion"] and st["hero_fill"]:
                # the reference style's own entrance for the big word, sampled per frame
                kind = st["hero_motion"]
                dur = motion.duration(kind, st["hero_motion_t"] or (t1 - t0), len(text))
                dur = min(dur, max(0.12, t1 - t0))
                base = BS + "an5" + BS + "fs%d" % int(fs)
                if st["hero_colors"]:
                    base += BS + "1c%s" % c(st["hero_colors"][pi % len(st["hero_colors"])])
                if st["hero_blur"]:
                    base += BS + "blur%d" % st["hero_blur"]
                hx, hyp = int(hx0), int(hy / 100.0 * height)
                for e in motion.events(kind, t0, t1, dur, fs, hx, hyp, text, base, float(st["hero_rot"] or 0), wd * fs / float(st["hero_size"]), 0, sty, int(st["motion_fps"])):
                    events.append(e)
                continue
            # in the lower layout (the second of the two) the big word is drawn in FRONT of the person, as the reference style does
            events.append((0, t0, t1, "{" + tags + "}" + text, "HeroFront" if front_hero else "Hero"))
    return events, front


def _column_events(phrases, st, width, height):
    """Glow Key / Shadow Key / Classic Key: a column for each phrase, centred on the frame - the small words said before the first key
    word on top (left-aligned), each key word big and centred, the small words after it beneath (right-aligned). Every word cuts
    in at the moment it is said and stays to the end of the phrase. The column is as wide as its widest row; a key word is
    shrunk to st["emph_wmax"] percent of the frame. -> (events, [])."""
    BS = chr(92)
    hst = _hero_style(st)
    events = []
    small_h = st["size"] * 1.2
    gap = st["size"] * 0.09
    word_gap_px = st["size"] * 0.3
    pitch = st["hero_size"] * st["emph_gap"]
    for p in phrases:
        ws = p["words"]
        if not ws:
            continue
        cand = [i for i, w in enumerate(ws)
                if clean_word(w["w"], hst) and not WEAK.match(_TOK.sub("", w["w"].lower()))
                and _TOK.sub("", w["w"].lower()) not in EMPH_SKIP and len(_TOK.sub("", w["w"])) >= 5]
        idx = sorted(sorted(cand, key=lambda i: -len(ws[i]["w"]))[:int(st["emph_max"])])
        # rows: pre (before the first key word), then [key word, trailing] per key word
        blocks = []
        first = idx[0] if idx else len(ws)
        pre = list(range(0, first))
        if pre:
            blocks.append(("pre", pre))
        for k, i in enumerate(idx):
            blocks.append(("emph", [i]))
            end = idx[k + 1] if k + 1 < len(idx) else len(ws)
            trail = list(range(i + 1, end))
            if trail:
                blocks.append(("trail", trail))
        widths = {}
        sizes = {}
        for kind, members in blocks:
            if kind == "emph":
                i = members[0]
                t_ = clean_word(ws[i]["w"], hst)
                fs = st["hero_size"]
                wd = max(text_width(st["hero_font"], fs, t_, st["hero_spacing"]), 1)
                cap = st["emph_wmax"] / 100.0 * width
                if wd > cap:
                    fs = fs * cap / wd
                    wd = cap
                widths[id(members)] = wd
                sizes[id(members)] = fs
            else:
                widths[id(members)] = sum(text_width(st["font"], st["size"], clean_word(ws[q]["w"], st), st["spacing"]) for q in members) + \
                    word_gap_px * (len(members) - 1)
        colw = max(widths.values()) if widths else 0
        left, right = width / 2.0 - colw / 2.0, width / 2.0 + colw / 2.0
        heights = [pitch * sizes[id(m)] / st["hero_size"] if kind == "emph" else small_h for kind, m in blocks]
        total = sum(heights) + gap * max(0, len(blocks) - 1)
        top = st["col_y"] / 100.0 * height - total / 2.0
        end_t = p["disp_end"]
        for (kind, members), bh in zip(blocks, heights):
            if kind == "emph":
                i = members[0]
                t_ = clean_word(ws[i]["w"], hst)
                cy = top + bh / 2.0
                glow = ""
                if st["emph_glow"]:
                    glow = BS + "bord%d" % max(2, st["emph_glow"] // 2) + BS + "3c%s" % c(st["hero_color"]) + BS + "3a&H70&" + BS + "blur%d" % st["emph_glow"]
                tags = "{" + BS + "an5" + BS + "pos(%d,%d)" % (width / 2.0, cy) + BS + "fs%d" % sizes[id(members)] + glow + "}"
                events.append((1, ws[i]["s"], end_t, tags + t_, "Hero"))
            else:
                cy = top + bh / 2.0
                x = left if kind == "pre" else right - widths[id(members)]
                for q in members:
                    t_ = clean_word(ws[q]["w"], st)
                    if not t_:
                        continue
                    tags = "{" + BS + "an4" + BS + "pos(%d,%d)" % (x, cy) + BS + "fs%d" % st["size"] + BS + "fsp%d" % st["spacing"]
                    tags += BS + "blur%d" % st["blur"] + "}"
                    events.append((1, ws[q]["s"], end_t, tags + t_, "Cap"))
                    x += text_width(st["font"], st["size"], t_, st["spacing"]) + word_gap_px
            top += bh + gap
    return events, []


def _silhouette(width, height):
    """dark head-and-shoulders drawn in FRONT of the hero word (style previews only), to show the behind-you effect"""
    k = 0.5523
    def ell(cx, cy, rx, ry):
        return ("m %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d b %d %d %d %d %d %d" % (
            cx - rx, cy, cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry,
            cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy,
            cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry,
            cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy))
    d = ell(width // 2, int(height * 0.43), 150, 190) + " " + ell(width // 2, int(height * 0.66), 430, 300)
    return (1, 0.0, 5.0, "{\\an7\\pos(0,0)\\p1\\1c&H4A3E3A&\\bord0\\shad0}" + d + "{\\p0}", "Cap")


def build_ass(words, style="hormozi", overrides=None, width=W, height=H, offset=0.0, split=False, silhouette=False):
    """words: flat list [{'w','s','e'}] -> ASS document string.
    split=True and a 'behind' template -> (behind_doc, front_doc) so the exporter can slot the person in between."""
    st = resolve_style(style, overrides)
    flat = [dict(w) for w in words if w.get("w", "").strip()]
    for w in flat:
        w["s"] += offset
        w["e"] += offset
    phrases = make_phrases(flat, max_words=max(1, st["words"]), max_chars=st["max_chars"],
                           hold=0.12 if st["words"] == 1 else 0.22)
    if st["emph"] and not st["behind"]:
        emph_ev, front_phrases = _column_events(phrases, st, width, height)
        cap_ev = _events_for(front_phrases, st, width, height)
        doc = _doc(width, height, [_hero_style_line(st), _cap_style_line(st)], _fade(emph_ev + cap_ev, st))
        return (None, doc) if split else doc
    if st["behind"]:
        hero_ev, front_phrases = (_hero_seq_events if st["hero_seq"] else _hero_events)(phrases, st, width, height)
        cap_ev = _events_for(front_phrases, st, width, height)
        behind_ev = [e for e in hero_ev if e[4] != "HeroFront"]
        front_hero = [(1,) + e[1:] for e in hero_ev if e[4] == "HeroFront"]
        hero_line = _hero_style_line(st)
        styles = [hero_line, _cap_style_line(st), hero_line.replace("Style: Hero,", "Style: HeroFront,", 1)]
        if split:
            return (_doc(width, height, styles, behind_ev), _doc(width, height, styles, cap_ev + front_hero))
        return _doc(width, height, styles, hero_ev + ([_silhouette(width, height)] if silhouette else []) + cap_ev)
    doc = _doc(width, height, [_cap_style_line(st)], _fade(_events_for(phrases, st, width, height), st))
    return (None, doc) if split else doc


def to_srt(words, max_words=6, max_chars=38):
    flat = [dict(w) for w in words if w.get("w", "").strip()]
    ph = make_phrases(flat, max_words=max_words, max_chars=max_chars, hold=0.0)

    def t(x):
        ms = int(round(x * 1000))
        return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)

    out = []
    for i, p in enumerate(ph, 1):
        out.append("%d\n%s --> %s\n%s\n" % (i, t(p["start"]), t(p["end"]), " ".join(w["w"] for w in p["words"])))
    return "\n".join(out)


def words_from_transcript(tr):
    return flatten(tr)





