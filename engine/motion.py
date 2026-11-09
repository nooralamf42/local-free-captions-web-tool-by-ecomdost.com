"""the reference style's text motions, ported from its own editor code (the functions D and R of its caption renderer) and rendered as ASS.

A motion is a function of the time since a word starts: opacity, offsets in ems, scale, rotation, skew, blur, a left-to-right reveal and
the share of letters typed. `state(kind, t, dur)` is the port; `events(...)` samples it every 1/30 s into one ASS event per frame, so
the curves (ease-out, bounce, elastic, flicker steps) are exactly the reference style's rather than an approximation with a few \\t tags.
"""
import math

BS = chr(92)
BASE = dict(opacity=1.0, xEm=0.0, yEm=0.0, scale=1.0, scaleX=1.0, rotate=0.0, skewX=0.0, blurEm=0.0, reveal=1.0, letters=1.0, flipX=0.0)
KINDS = ("rise", "drop", "zoom", "blur", "wipe", "type", "stretch", "skid", "flip", "stamp", "flicker", "pop", "fade", "fadeUp",
         "fadeDown", "fadeLeft")


def _z(x):
    return max(0.0, min(1.0, x))


def _ease(i):          # ease out cubic
    return 1 - (1 - i) ** 3


def _back(i, s=1.9):   # back-out: overshoots, then settles
    return 1 + (s + 1) * (i - 1) ** 3 + s * (i - 1) ** 2


def _bounce(e):
    if e < 0.36363636363636365:
        return 7.5625 * e * e
    if e < 0.7272727272727273:
        t = e - 0.5454545454545454
        return 7.5625 * t * t + 0.75
    if e < 0.9090909090909091:
        t = e - 0.8181818181818182
        return 7.5625 * t * t + 0.9375
    t = e - 0.9545454545454546
    return 7.5625 * t * t + 0.984375


def _elastic(i):
    if i <= 0:
        return 0.0
    if i >= 1:
        return 1.0
    return 2 ** (-10 * i) * math.sin(2 * math.pi / 3 * (10 * i - 0.75)) + 1


_FLICKER = [(0.08, 0), (0.14, 0.7), (0.24, 0.05), (0.31, 0.9), (0.4, 0.35), (0.46, 1), (0.52, 0.55), (1, 1)]


def duration(kind, base, letters):
    """Seconds a motion takes: the reference style's function R. `base` is the time the word has (or its own default), `letters` its length."""
    if kind == "type":
        return min(1.1, max(0.3, 0.07 * letters))
    if kind == "drop":
        return max(0.55, 1.3 * base)
    if kind in ("stretch", "flicker"):
        return max(0.5, 1.2 * base)
    if kind == "blur":
        return max(0.5, 1.15 * base)
    if kind == "stamp":
        return max(0.32, 0.8 * base)
    return max(0.28, base)


def state(kind, t, dur):
    """the reference style's function D: the look of a word `t` seconds after it starts, the motion lasting `dur`. Before the word: hidden."""
    s = dict(BASE)
    if t < 0:
        s.update(opacity=0.0, letters=0.0, reveal=0.0)
        return s
    i = _z(t / max(0.05, dur))
    if i >= 1:
        return s
    r = _ease(i)
    if kind == "rise":
        s.update(opacity=_z(i / 0.5), yEm=0.45 * (1 - r), blurEm=0.02 * (1 - r))
    elif kind == "drop":
        s.update(opacity=_z(i / 0.12), yEm=-0.95 * (1 - _bounce(i)))
    elif kind == "zoom":
        s.update(opacity=_z(i / 0.4), scale=1 + 0.6 * (1 - r), blurEm=0.06 * (1 - r))
    elif kind == "blur":
        s.update(opacity=_z(i / 0.6), scale=1.04 - 0.04 * r, blurEm=0.14 * (1 - r) ** 2)
    elif kind == "wipe":
        s.update(reveal=_ease(i))
    elif kind == "type":
        s.update(letters=i)
    elif kind == "stretch":
        s.update(opacity=_z(i / 0.15), scaleX=0.08 + 0.92 * _elastic(i))
    elif kind == "skid":
        s.update(opacity=_z(i / 0.3), xEm=0.9 * (1 - r), skewX=-18 * (1 - r))
    elif kind == "flip":
        s.update(opacity=_z(i / 0.3), flipX=88 * (1 - _back(i, 1.2)))
    elif kind == "stamp":
        if i < 0.45:
            sc, rot = 2 - (i / 0.45) ** 2, 0.0
        else:
            k = (i - 0.45) / 0.55
            sc = 1 - 0.05 * math.sin(k * math.pi) * (1 - k)
            rot = 2.4 * math.sin(k * math.pi * 5) * (1 - k)
        s.update(opacity=_z(i / 0.18), scale=sc, rotate=rot)
    elif kind == "flicker":
        op = next((v for lim, v in _FLICKER if i < lim), 1)
        s.update(opacity=op)
    elif kind == "pop":
        s.update(opacity=_z(i / 0.18), scale=0.3 + 0.7 * _back(i, 2.4))
    elif kind == "fade":
        s.update(opacity=i)
    elif kind == "fadeUp":
        s.update(opacity=r, yEm=0.33 * (1 - r))
    elif kind == "fadeDown":
        s.update(opacity=r, yEm=-0.33 * (1 - r))
    elif kind == "fadeLeft":
        s.update(opacity=r, xEm=0.33 * (1 - r))
    return s


def _alpha(op):
    return "&H%02X&" % int(round((1 - _z(op)) * 255))


def tags_for(s, fs, x, y, rot_base=0.0, width_px=0.0, text_len=0):
    """ASS override tags that put a word in motion state `s`. Position is the word's centre (an5). rot_base: its fixed tilt, CCW degrees."""
    fscx, fscy = 100 * s["scale"] * s["scaleX"], 100 * s["scale"]
    out = BS + "alpha" + _alpha(s["opacity"])
    out += BS + "fscx%d" % max(1, fscx) + BS + "fscy%d" % max(1, fscy)
    frz = rot_base - s["rotate"]
    if frz:
        out += BS + "frz%.2f" % frz
    if s["skewX"]:
        out += BS + "fax%.3f" % (-math.tan(math.radians(s["skewX"])))
    if s["flipX"]:
        out += BS + "frx%.1f" % s["flipX"]
    if s["blurEm"]:
        out += BS + "blur%.1f" % (s["blurEm"] * fs)
    px, py = x + s["xEm"] * fs, y + s["yEm"] * fs
    out += BS + "pos(%d,%d)" % (px, py)
    if s["reveal"] < 1:
        left = px - width_px / 2.0 - 0.12 * width_px
        right = px + width_px / 2.0 - (1 - s["reveal"]) * width_px
        out += BS + "clip(%d,%d,%d,%d)" % (left, py - fs * 1.2, max(left, right), py + fs * 1.2)
    return out


def events(kind, t0, t1, dur, fs, x, y, text, base_tags, rot_base=0.0, width_px=0.0, layer=0, style="Hero", fps=30):
    """One ASS event per frame while the motion runs, then a steady one to t1. base_tags: tags that stay (size, colour, ...), without
    position/alpha/scale, which the motion sets."""
    out = []
    steps = int(math.ceil(dur * fps))
    n = len(text)
    for k in range(steps):
        a = t0 + k / float(fps)
        b = min(t1, a + 1.0 / fps)
        if a >= t1:
            break
        s = state(kind, a - t0 + 0.5 / fps, dur)
        body = text
        if kind == "type":
            shown = int(math.ceil(s["letters"] * n - 1e-9))
            body = text[:shown] + "{" + BS + "alpha&HFF&}" + text[shown:] if shown < n else text
            s = dict(s, letters=1.0)
        out.append((layer, a, b, "{" + base_tags + tags_for(s, fs, x, y, rot_base, width_px, n) + "}" + body, style))
    end = t0 + steps / float(fps)
    if end < t1:
        out.append((layer, end, t1, "{" + base_tags + tags_for(dict(BASE), fs, x, y, rot_base, width_px, n) + "}" + text, style))
    return out
