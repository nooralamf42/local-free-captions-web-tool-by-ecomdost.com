"""The "dynamic" looks of popular caption editors with a layout of their own - Illusion, Editor Masala, Aura, Swiss, Big Red, Scribble, Archives,
Blockbuster, Journal, Interlock - laid out the way the reference style's renderer lays them out (sizes in multiples of its base size, which words are the
big ones, where each row sits, how each word comes in) and drawn as ASS.

Every builder takes a phrase (its words, with start / end times) and returns events (layer, t0, t1, text, style); words stay to the end
of the phrase. Animations are sampled per frame with the reference style's ease-out curve, so they move like its own."""
import math
import re
import zlib

from .ass import WEAK, _TOK, _font_ratio, c, clean_word, text_width
from .styles import FONT_FILES
from .util import FONTS

BS = chr(92)
EMPH_SKIP = {"the", "and", "that", "this", "with", "have", "from", "your", "you", "are", "for", "was", "but", "not", "they"}


def rnd(key):
    return (zlib.crc32(key.encode("utf-8")) & 0xFFFFFF) / float(0x1000000)


def _eo(u):
    return 1 - (1 - max(0.0, min(1.0, u))) ** 3


def _css(font, fs):
    """libass size -> CSS px of that font"""
    return fs / _font_ratio(FONTS / FONT_FILES.get(font, "Poppins-ExtraBold.ttf"))


def _fsz(font, css_px):
    return int(round(css_px * _font_ratio(FONTS / FONT_FILES.get(font, "Poppins-ExtraBold.ttf"))))


def tw(font, fs, text, sp=0):
    return text_width(font, fs, text, sp)


def pick_emph(ws, st, n=1):
    """indexes of the words the reference style would stress: the flagged ones, else the longest content words"""
    flagged = [i for i, w in enumerate(ws) if w.get("hero")]
    if flagged:
        return flagged[:n]
    cand = []
    for i, w in enumerate(ws):
        t = _TOK.sub("", w["w"].lower())
        if len(t) >= 4 and not WEAK.match(t) and t not in EMPH_SKIP:
            cand.append(i)
    if not cand:
        cand = [max(range(len(ws)), key=lambda i: len(_TOK.sub("", ws[i]["w"])))] if ws else []
    return sorted(sorted(cand, key=lambda i: -len(ws[i]["w"]))[:n])


def base_tags(font, fs, color, bord=0, bordc="#000000", shad=0, shadc="#000000", blur=0, italic=False, sp=0, bold=False, shadow_blur=0):
    t = BS + "fn" + font + BS + "fs%d" % fs + BS + "1c" + c(color) + BS + "bord%.1f" % bord + BS + "3c" + c(bordc)
    t += BS + "shad%.1f" % shad + BS + "4c" + c(shadc) + BS + "i%d" % (1 if italic else 0) + BS + "b%d" % (1 if bold else 0)
    if sp:
        t += BS + "fsp%.1f" % sp
    if blur:
        t += BS + "blur%.1f" % blur
    return t


def anim_events(t0, t1, x, y, text, base, dx=0.0, dy=0.0, dur=0.38, opdur=0.2, blur=0.0, scale0=1.0, rot0=0.0, rot=0.0, fps=30,
                layer=1, fix=""):
    """A word coming in: per-frame events from (x+dx, y+dy) to (x, y) on ease-out, fading over opdur, blur and scale settling."""
    out = []
    n = int(math.ceil(dur * fps))
    for k in range(n):
        a = t0 + k / float(fps)
        if a >= t1:
            break
        b = min(t1, a + 1.0 / fps)
        tt = (k + 0.5) / float(fps)
        u = _eo(tt / dur)
        op = min(1.0, tt / max(0.001, opdur))
        sc = scale0 + (1 - scale0) * u
        r = rot0 * (1 - u) + rot
        tags = BS + "an5" + BS + "pos(%d,%d)" % (x + dx * (1 - u), y + dy * (1 - u)) + BS + "alpha&H%02X&" % int(round((1 - op) * 255))
        tags += BS + "fscx%d" % (100 * sc) + BS + "fscy%d" % (100 * sc)
        if r:
            tags += BS + "frz%.2f" % -r
        if blur and u < 1:
            tags += BS + "blur%.1f" % (blur * (1 - u) ** 2 + 0.01)
        out.append((layer, a, b, "{" + base + tags + fix + "}" + text, "Cap"))
    end = t0 + n / float(fps)
    if end < t1:
        tags = BS + "an5" + BS + "pos(%d,%d)" % (x, y) + BS + "alpha&H00&"
        if rot:
            tags += BS + "frz%.2f" % -rot
        out.append((layer, end, t1, "{" + base + tags + fix + "}" + text, "Cap"))
    return out


def _row_x(items, gap, cx, align="center", left=None, right=None):
    """items: [(width, ...)] -> list of centre xs and total width"""
    total = sum(i[0] for i in items) + gap * max(0, len(items) - 1)
    if align == "left":
        x0 = left
    elif align == "right":
        x0 = right - total
    else:
        x0 = cx - total / 2.0
    xs, x = [], x0
    for i in items:
        xs.append(x + i[0] / 2.0)
        x += i[0] + gap
    return xs, total


# ---------------------------------------------------------------------------------------------------------------------------------
def illusion(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    font, r = st["font"], st["size"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.94 * W
    key = ws[0]["w"] + str(int(ws[0]["s"] * 10))
    t1 = p["disp_end"]
    ev = []
    emph = pick_emph(ws, st, 1) if len(ws) > 2 else []
    gap = 8
    if not emph:
        # one row (or wrapped), each word rising in from below on its own time
        wid = [tw(font, r, t) for t in texts]
        tot = sum(wid) + gap * (len(wid) - 1)
        k = min(1.0, avail / tot) if tot else 1
        fs = int(r * k)
        wid = [w * k for w in wid]
        xs, _ = _row_x([(w,) for w in wid], gap, cx)
        for i, w in enumerate(ws):
            ev += anim_events(w["s"], t1, xs[i], cy, texts[i], base_tags(font, fs, st["color"], shad=3, shadc="#000000", blur=0), dy=40, dur=.38, blur=12)
        return ev
    e = emph[0]
    big = int(r * 2.8)
    bw = tw(font, big, texts[e])
    if bw > avail:
        big = int(big * avail / bw)
        bw = avail
    before, after = list(range(0, e)), list(range(e + 1, len(ws)))
    if rnd(key + ":swap") < .5:
        before, after = after, before
    rows = []
    for idxs, kind in ((before, "top"), (after, "bot")):
        if not idxs:
            rows.append(None)
            continue
        wid = [tw(font, r, texts[i]) for i in idxs]
        tot = sum(wid) + gap * (len(wid) - 1)
        k = min(1.0, avail / tot) if tot else 1
        rows.append((idxs, [w * k for w in wid], int(r * k)))
    colw = max([bw] + [sum(rw[1]) + gap * (len(rw[1]) - 1) for rw in rows if rw])
    left, right = cx - colw / 2.0, cx + colw / 2.0
    line = r * 0.8
    top_h = line if rows[0] else 0
    bot_h = line if rows[1] else 0
    mb = 0.12 * r
    total_h = top_h + (mb if rows[0] else 0) + big + (mb if rows[1] else 0) + bot_h
    y = cy - total_h / 2.0
    ys = {}
    if rows[0]:
        ys["top"] = y + top_h / 2.0
        y += top_h + mb
    ys["emph"] = y + big / 2.0
    y += big + (mb if rows[1] else 0)
    if rows[1]:
        ys["bot"] = y + bot_h / 2.0
    for rw, kind, al in ((rows[0], "top", "left" if rnd(key + ":tj") < .5 else "right"), (rows[1], "bot", "left" if rnd(key + ":bj") < .5 else "right")):
        if not rw:
            continue
        xs, _ = _row_x([(w,) for w in rw[1]], gap, cx, al, left, right)
        for j, i in enumerate(rw[0]):
            ev += anim_events(ws[i]["s"], t1, xs[j], ys[kind], texts[i], base_tags(font, rw[2], st["color"], shad=2), dy=40, dur=.38, blur=12, fix=BS + "fscx100")
    col = st["active"] or st["color"]
    ev += anim_events(ws[e]["s"], t1, cx, ys["emph"], texts[e], base_tags(font, big, col, shad=3), dy=104, dur=.38, blur=28)
    return ev


def editor_masala(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    a = st["size"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.94 * W
    h = zlib.crc32(("".join(texts)).encode()) & 0x7FFFFFFF
    persona = "A" if h % 2 == 0 else "B"
    e = pick_emph(ws, st, 1)[0]
    ctxf = st["font"]
    if persona == "A":
        hf, hc, hs, ital, txt = "Instrument Serif", "#FFFFFF", int(a * 2.5), True, texts[e].lower()
    else:
        hf, hc, hs, ital, txt = "Montserrat Black", st["active"], int(a * 2.2), False, texts[e].upper()
    hw = tw(hf, hs, txt)
    if hw > avail:
        hs = int(hs * avail / hw)
        hw = avail
    before, after = list(range(0, e)), list(range(e + 1, len(ws)))
    if zlib.crc32((("".join(texts)) + "hemi").encode()) & 1:
        before, after = after, before
    diag = (zlib.crc32((("".join(texts)) + "diag").encode()) & 1) == 0
    shift = 1.5 * a
    ev = []
    t1 = p["disp_end"]
    rows = [before, after]
    gap = 8
    sizes, ws_rows = [], []
    for idxs in rows:
        if not idxs:
            ws_rows.append(None)
            continue
        wid = [tw(ctxf, a, texts[i]) for i in idxs]
        tot = sum(wid) + gap * (len(wid) - 1)
        k = min(1.0, avail / tot)
        ws_rows.append((idxs, [x * k for x in wid], int(a * k)))
    line = a * 0.8
    mb = 0.12 * a
    th = (line + mb if ws_rows[0] else 0) + hs + (mb + line if ws_rows[1] else 0)
    y = cy - th / 2.0
    ys = []
    if ws_rows[0]:
        ys.append(y + line / 2.0)
        y += line + mb
    else:
        ys.append(None)
    ycen = y + hs / 2.0
    y += hs + mb
    ys.append(y + line / 2.0 if ws_rows[1] else None)
    for ri, rw in enumerate(ws_rows):
        if not rw:
            continue
        off = (shift if diag else -shift) * (1 if ri == 0 else -1)
        xs, _ = _row_x([(w,) for w in rw[1]], gap, cx + off)
        for j, i in enumerate(rw[0]):
            ev += anim_events(ws[i]["s"], t1, xs[j], ys[ri], texts[i], base_tags(ctxf, rw[2], st["color"], shad=3), dy=40, dur=.32, blur=10)
    glow = dict(bord=10, bordc="#FFFFFF") if persona == "B" else {}
    base = base_tags(hf, hs, hc, shad=0 if persona == "B" else 3, italic=ital, **glow)
    if persona == "B":
        base += BS + "3a&HB0&"
    ev += anim_events(ws[e]["s"], t1, cx, ycen, txt, base, dy=96, dur=.32, blur=10)
    return ev


def aura(p, st, W, H, ctx):
    """Aura / Swiss: roles - the key word (accent, bold caps, 2x), other long words (bold caps 1.9x), one cursive word (2.6x) and the small
    support words, stacked in up to three rows that drift left / right."""
    swiss = ctx.get("swiss")
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    a = st["size"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.92 * W
    key = "".join(texts)
    em = pick_emph(ws, st, 1)
    emph = em[0] if em else -1
    cursive = -1
    best = 3
    for i, t in enumerate(texts):
        if i == emph:
            continue
        n_ = len(_TOK.sub("", t))
        if n_ >= best and not WEAK.match(_TOK.sub("", t.lower())):
            best, cursive = n_, i
    if swiss:
        cursive = -1
    roles = []
    for i, t in enumerate(texts):
        k = _TOK.sub("", t.lower())
        if i == emph:
            roles.append("EMPH")
        elif i == cursive:
            roles.append("CURSIVE")
        elif len(k) <= 3 or WEAK.match(k):
            roles.append("SUPPORT")
        else:
            roles.append("BOLD")
    if all(r_ == "SUPPORT" for r_ in roles) and texts:
        roles[max(range(len(texts)), key=lambda i: len(texts[i]))] = "BOLD"
    bold_f = st["hero_font"]
    cur_f = "Playfair Display"
    sup_f = st["font"]
    spec = []
    for i, t in enumerate(texts):
        r_ = roles[i]
        if r_ == "CURSIVE":
            spec.append((cur_f, int(a * 2.6), "#FFFFFF", t, True))
        elif r_ == "EMPH":
            spec.append((bold_f, int(a * 2.0), st["active"], t.upper(), False))
        elif r_ == "BOLD":
            spec.append((bold_f, int(a * 1.9), "#FFFFFF", t.upper(), False))
        else:
            spec.append((sup_f, int(a * 0.95), "#FFFFFF", t, False))
    gap = 0.35 * a

    def width(items):
        return sum(tw(spec[i][0], spec[i][1], spec[i][3]) for i in items) + gap * max(0, len(items) - 1)
    rows_ = []
    for i, r_ in enumerate(roles):
        if r_ == "SUPPORT" and rows_ and all(roles[j] == "SUPPORT" for j in rows_[-1]) and width(rows_[-1] + [i]) <= avail:
            rows_[-1].append(i)
        else:
            rows_.append([i])
    while len(rows_) > 3:
        k = next((q for q, rw in enumerate(rows_) if all(roles[j] == "SUPPORT" for j in rw)), len(rows_) - 1)
        tgt = k + 1 if k + 1 < len(rows_) else k - 1
        if tgt < k:
            rows_[tgt].extend(rows_[k])
        else:
            rows_[tgt][0:0] = rows_[k]
        rows_.pop(k)
    scale_rows = []
    for rw in rows_:
        w_ = width(rw)
        scale_rows.append(min(1.0, avail / w_) if w_ else 1.0)
    heights = [max(spec[i][1] for i in rw) * scale_rows[q] for q, rw in enumerate(rows_)]
    total_h = sum(heights)
    y = cy - total_h / 2.0
    dirn = 1 if rnd(key + "splash") > .5 else -1
    splash = 1.6 * a
    ev = []
    t1 = p["disp_end"]
    for q, rw in enumerate(rows_):
        k = scale_rows[q]
        wids = [(tw(spec[i][0], spec[i][1], spec[i][3]) * k,) for i in rw]
        tot = sum(w_[0] for w_ in wids) + gap * k * (len(wids) - 1)
        slack = max(0.0, (avail - tot) / 2.0)
        off = max(-slack, min(slack, dirn * (q - (len(rows_) - 1) / 2.0) * splash))
        xs, _ = _row_x(wids, gap * k, cx + off)
        yc = y + heights[q] / 2.0
        y += heights[q]
        for j, i in enumerate(rw):
            f, fs, col, t, ital = spec[i]
            fs = int(fs * k)
            idx = i
            t0 = ws[i]["s"] if swiss else ws[0]["s"] + 0.11 * idx
            mode = int(rnd(key + "a%d" % idx) * 3)
            base = base_tags(f, fs, col, shad=3 if roles[i] != "SUPPORT" else 2, italic=ital and not swiss, shadc="#000000")
            if mode == 1:
                ev.append((1, t0, t1, "{" + base + BS + "an5" + BS + "pos(%d,%d)" % (xs[j], yc) + BS + "alpha&HFF&" + BS + "t(0,180," + BS + "alpha&H00&)}" + t, "Cap"))
            elif mode == 2:
                ev += anim_events(t0, t1, xs[j], yc, t, base, dx=1.3 * a, dur=.45, opdur=.27)
            else:
                ev += anim_events(t0, t1, xs[j], yc, t, base, dy=0.5 * a, dur=.45, opdur=.27, blur=0.24 * a)
    return ev


def big_red(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.94 * W
    em = pick_emph(ws, st, 2 if len(ws) > 4 else 1)
    t1, t0 = p["disp_end"], p["start"]
    ev = []
    red = st["active"]
    small = st["size"]
    f_small, f_big = st["font"], st["hero_font"]
    bigsz = _fsz(f_big, 184)
    ew = [tw(f_big, bigsz, texts[i].upper()) for i in em]
    gapb = 0.22 * bigsz
    tot = sum(ew) + gapb * max(0, len(ew) - 1)
    k = min(1.0, avail / tot) if tot else 1
    xs, _ = _row_x([(w * k,) for w in ew], gapb * k, cx)
    for j, i in enumerate(em):
        tags = BS + "an5" + BS + "pos(%d,%d)" % (xs[j], cy) + BS + "fscx%d" % (100 * k) + BS + "fscy%d" % (135 * k)
        tags += BS + "fn" + f_big + BS + "fs%d" % bigsz + BS + "1c" + c(red) + BS + "bord0" + BS + "shad6" + BS + "4c&H1A1A55&" + BS + "4a&H80&" + BS + "blur1.5"
        ev.append((0, t0, t1, "{" + tags + "}" + texts[i].upper(), "Cap"))
    rest = [i for i in range(len(ws)) if i not in em]
    if rest:
        wid = [tw(f_small, small, texts[i]) for i in rest]
        gap = 24
        tot = sum(wid) + gap * (len(wid) - 1)
        k2 = min(1.0, 0.95 * W / tot)
        xs2, _ = _row_x([(w * k2,) for w in wid], gap * k2, cx)
        for j, i in enumerate(rest):
            tags = BS + "an5" + BS + "pos(%d,%d)" % (xs2[j], cy) + BS + "fn" + f_small + BS + "fs%d" % int(small * k2) + BS + "1c" + c("#FFFFFF") + BS + "bord0" + BS + "shad3" + BS + "4c&H000000&"
            ev.append((1, ws[i]["s"], t1, "{" + tags + "}" + texts[i], "Cap"))
    return ev


def _rrect(w, h, r, jit):
    pts = ["m %d %d" % (r + jit[0], 0), "l %d %d" % (w - r, jit[1]), "l %d %d" % (w, r + jit[2]), "l %d %d" % (w - jit[3], h - r),
           "l %d %d" % (w - r, h), "l %d %d" % (r, h - jit[0]), "l %d %d" % (0, h - r), "l %d %d" % (jit[1], r)]
    return " ".join(pts)


def scribble(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    font = st["font"]
    r = st["size"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.94 * W
    key = "".join(texts)
    n_mark = 2 if len(ws) >= 6 else 1
    marked = pick_emph(ws, st, n_mark)
    others = [i for i in range(len(ws)) if i not in marked]
    circled = max(others, key=lambda i: len(texts[i])) if len(ws) > 3 and others else -1
    sizes = []
    for i, t in enumerate(texts):
        sizes.append(int(r * (1.35 if i in marked else 1.18 if i == circled else 1.0)))
    gap = 28
    wid = [tw(font, sizes[i], texts[i]) for i in range(len(ws))]
    tot = sum(wid) + gap * (len(wid) - 1)
    k = min(1.0, avail / tot)
    sizes = [int(s * k) for s in sizes]
    wid = [w * k for w in wid]
    xs, _ = _row_x([(w,) for w in wid], gap * k, cx)
    t1 = p["disp_end"]
    ev = []
    for i, w in enumerate(ws):
        t0 = w["s"]
        rot = 6 * rnd(key + ":rot%d" % i) - 3
        room = max(0.12, ((ws[i + 1]["s"] if i + 1 < len(ws) else w["e"]) - t0))
        if i in marked:
            hw, hh = wid[i] * 1.14, sizes[i] * 1.0
            jit = [int(hh * rnd(key + "h%d%d" % (i, q)) * .12) for q in range(4)]
            tag = BS + "an7" + BS + "pos(%d,%d)" % (xs[i] - hw / 2.0, cy - hh * .55) + BS + "1c" + c(st["box_color"]) + BS + "bord0" + BS + "shad0" + BS + "frz%.1f" % (-rot * .4) + BS + "p1"
            tag += BS + "fscx0" + BS + "t(%d,%d,%s)" % (int(.26 * room * 1000), int(.56 * room * 1000), BS + "fscx100")
            ev.append((0, t0, t1, "{" + tag + "}" + _rrect(int(hw), int(hh), int(hh * .3), jit) + "{" + BS + "p0}", "Cap"))
        col = "#241C12" if i in marked else st["color"]
        base = base_tags(font, sizes[i], col, shad=0 if i in marked else 3, shadc="#1E140A", bold=True)
        ev += anim_events(t0, t1, xs[i], cy, texts[i], base, dur=max(.18, .42 * room), opdur=.1, scale0=.5, rot0=-8, rot=rot)
        if i == circled:
            ew, eh = wid[i] * 1.24, sizes[i] * 1.32
            n_pts = 36
            pts = []
            for q in range(n_pts + 1):
                ang = 2 * math.pi * q / n_pts
                pts.append((ew / 2 * (1 + math.cos(ang)), eh / 2 * (1 + math.sin(ang))))
            path = "m %d %d " % pts[0] + " ".join("l %d %d" % pq for pq in pts[1:])
            tag = BS + "an7" + BS + "pos(%d,%d)" % (xs[i] - ew / 2, cy - eh / 2) + BS + "1a&HFF&" + BS + "3c" + c(st["hero_color"] if st["hero_color"] != "#FFFFFF" else "#FF5D5D") + BS + "bord4" + BS + "shad0" + BS + "p1"
            tag += BS + "3a&HFF&" + BS + "t(%d,%d,%s)" % (int(.4 * room * 1000), int(.6 * room * 1000), BS + "3a&H00&")
            ev.append((1, t0, t1, "{" + tag + "}" + path + "{" + BS + "p0}", "Cap"))
    return ev


def archives(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    font, n = st["font"], st["size"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    emph = pick_emph(ws, st, 1)
    ei = emph[0] if emph else -1
    sizes = [int(n * (1.22 if i == ei else 1)) for i in range(len(ws))]
    gap = 0.34 * n
    wid = [tw(font, sizes[i], texts[i]) for i in range(len(ws))]
    tot = sum(wid) + gap * (len(wid) - 1)
    k = min(1.0, 0.94 * W / tot)
    sizes = [max(8, int(s * k)) for s in sizes]
    wid = [w * k for w in wid]
    xs, _ = _row_x([(w,) for w in wid], gap * k, cx)
    t1 = p["disp_end"]
    ev = []
    fps = 10   # the "boil": each word re-jittered ten times a second
    for i, w in enumerate(ws):
        t0 = w["s"]
        col = st["color"]
        steps = int(max(1, math.ceil((t1 - t0) * fps)))
        for q in range(steps):
            a = t0 + q / float(fps)
            b = min(t1, a + 1.0 / fps)
            if a >= t1:
                break
            dx = (rnd("%s%d%d:x" % (texts[0], i, q % 8)) - .5) * 3.2
            dy = (rnd("%s%d%d:y" % (texts[0], i, q % 8)) - .5) * 3.2
            rot = (rnd("%s%d%d:r" % (texts[0], i, q % 8)) - .5) * 1.4
            tags = BS + "an5" + BS + "pos(%.1f,%.1f)" % (xs[i] + dx, cy + dy) + BS + "frz%.2f" % rot
            if q == 0:
                tags += BS + "alpha&HFF&" + BS + "t(0,100," + BS + "alpha&H00&)"
            ev.append((1, a, b, "{" + base_tags(font, sizes[i], col, shad=4, shadc="#000000", blur=.6) + tags + "}" + texts[i], "Cap"))
        if i == ei:
            uw = wid[i] * 1.16
            uy = cy + sizes[i] * 0.42
            seg = []
            m = 14
            for q in range(m + 1):
                seg.append((uw * q / m, 3 * math.sin(q * 1.3 + rnd(texts[0]) * 6)))
            top = "m %d %d " % seg[0] + " ".join("l %d %d" % s for s in seg[1:])
            bot = " ".join("l %d %d" % (s[0], s[1] + 5) for s in reversed(seg))
            tag = BS + "an7" + BS + "pos(%d,%d)" % (xs[i] - uw / 2, uy) + BS + "1c" + c(col) + BS + "bord0" + BS + "shad0" + BS + "p1"
            tag += BS + "fscx0" + BS + "t(0,300," + BS + "fscx100)"
            ev.append((1, t0 + 0.12, t1, "{" + tag + "}" + top + " " + bot + "{" + BS + "p0}", "Cap"))
    return ev


def blockbuster(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    cond, script = "Anton", "Great Vibes"
    a = _fsz(cond, 0.0705 * 270 * 4 * 0.98)
    l = int(a * 1.355)
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.92 * W
    tr = 0.035 * _css(cond, a)
    wid_c = [tw(cond, a, t.upper(), tr) for t in texts]
    # the first words (as many as fit in ~64% of the width) are the red capitals, the rest the white script below
    acc, v = 0.0, 0
    for i, w_ in enumerate(wid_c):
        acc += w_ + 0.194 * a
        if acc > 0.64 * W and i > 0:
            break
        v = i + 1
    if v >= len(ws) and len(ws) > 1:
        v = len(ws) - 1
    top_i, bot_i = list(range(0, v)), list(range(v, len(ws)))
    rows = []
    for idxs, f, fs, up, gap in ((top_i, cond, a, True, 0.194 * a), (bot_i, script, l, False, 0.524 * l)):
        if not idxs:
            rows.append(None)
            continue
        wid = [tw(f, fs, texts[i].upper() if up else texts[i], tr if up else 0) for i in idxs]
        tot = sum(wid) + gap * (len(wid) - 1)
        k = min(1.0, avail / tot)
        rows.append((idxs, f, int(fs * k), up, [w * k for w in wid], gap * k))
    hts = [(rw[2] if rw else 0) for rw in rows]
    overlap = 0.387 * a if rows[0] and rows[1] else 0
    total = hts[0] + hts[1] - overlap
    y0 = cy - total / 2.0
    ys = [y0 + hts[0] / 2.0, y0 + hts[0] - overlap + hts[1] / 2.0]
    ev = []
    t1 = p["disp_end"]
    red = st["active"]
    for ri, rw in enumerate(rows):
        if not rw:
            continue
        idxs, f, fs, up, wid, gap = rw
        xs, _ = _row_x([(w,) for w in wid], gap, cx)
        for j, i in enumerate(idxs):
            t = texts[i].upper() if up else texts[i]
            if up:
                base = base_tags(f, fs, red, bord=3, bordc=red, shad=4, shadc="#000000", sp=tr)
                base += BS + "3a&H80&"
            else:
                base = base_tags(f, fs, "#FFFFFF", bord=3, bordc="#FFFFFF", shad=5, shadc="#000000")
                base += BS + "3a&H90&"
            ev += anim_events(ws[i]["s"], t1, xs[j], ys[ri], t, base, dy=0.2 * fs, dur=.3, opdur=.2, blur=3, layer=1 + ri)
    return ev


def journal(p, st, W, H, ctx):
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    font = st["font"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    base = st["size"]
    gap = 0.34 * base
    avail = 0.92 * W
    wid = [tw(font, base, t) for t in texts]
    # greedy wrap, then shrink to fit as the reference style does
    lines, cur, curw = [], [], 0.0
    for i, w_ in enumerate(wid):
        add = w_ if not cur else gap + w_
        if cur and curw + add > avail:
            lines.append(cur)
            cur, curw = [i], w_
        else:
            cur.append(i)
            curw += add
    if cur:
        lines.append(cur)
    lh = base * 1.0
    total_h = lh * len(lines)
    y = cy - total_h / 2.0
    ev = []
    t1 = p["disp_end"]
    n = len(ws)
    exit_ms = 0.42
    fade_ms = 0.46
    stagger = min(0.08, 0.8 * (exit_ms + fade_ms) / max(1, n - 1)) if n > 1 else 0
    start_exit = max(ws[0]["s"], t1 - (exit_ms + fade_ms + stagger * (n - 1)))
    for li, ln in enumerate(lines):
        wv = [(wid[i],) for i in ln]
        xs, _ = _row_x(wv, gap, cx)
        yc = y + lh * (li + 0.5)
        for j, i in enumerate(ln):
            t0 = ws[i]["s"]
            e0 = start_exit + stagger * i
            ent = max(0.17, min(0.46, 0.85 * max(0.05, (ws[i + 1]["s"] if i + 1 < n else ws[i]["e"]) - t0)))
            ev += anim_events(t0, min(t1, e0), xs[j], yc, texts[i], base_tags(font, base, st["color"], bord=2, bordc=st["color"], shad=3, shadc="#000000"),
                              dur=ent, opdur=ent, blur=0.12 * base, scale0=.95)
            if e0 < t1:
                # the exit: the word turns red while it travels, then fades
                steps = int(math.ceil((t1 - e0) * 30))
                for q in range(steps):
                    a = e0 + q / 30.0
                    b = min(t1, a + 1 / 30.0)
                    u = min(1.0, (a - e0) / exit_ms)
                    fade = 1.0 - max(0.0, min(1.0, (a - e0 - exit_ms) / fade_ms))
                    col = _mix(st["color"], "#E8202A", u)
                    tags = BS + "an5" + BS + "pos(%d,%d)" % (xs[j], yc) + BS + "alpha&H%02X&" % int(round((1 - fade) * 255))
                    ev.append((1, a, b, "{" + base_tags(font, base, col, bord=2, bordc=col, shad=3) + tags + "}" + texts[i], "Cap"))
    return ev


def _mix(c1, c2, u):
    def rgb(h):
        h = h.lstrip("#")
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    a, b = rgb(c1), rgb(c2)
    return "#%02X%02X%02X" % tuple(int(round(x + (y - x) * u)) for x, y in zip(a, b))


def interlock(p, st, W, H, ctx):
    """A huge italic serif key word with small spaced capitals nested around it: the words said before above, those after below."""
    ws = p["words"]
    texts = [clean_word(w["w"], st) for w in ws]
    hero_f, caps_f = "Playfair Display", st["font"]
    cx, cy = st["x"] / 100.0 * W, st["y"] / 100.0 * H
    avail = 0.96 * W
    e = pick_emph(ws, st, 1)
    t1 = p["disp_end"]
    caps = st["size"]
    tr = st["spacing"]
    ev = []
    if not e:
        return ev
    e = e[0]
    hs = _fsz(hero_f, 0.215 * 270 * 4)
    hw = tw(hero_f, hs, texts[e])
    if hw > avail:
        hs = int(hs * avail / hw)
        hw = avail
    before, after = list(range(0, e)), list(range(e + 1, len(ws)))
    gap = 0.4 * caps
    rows = []
    for idxs in (before, after):
        if not idxs:
            rows.append(None)
            continue
        wid = [tw(caps_f, caps, texts[i].upper(), tr) for i in idxs]
        tot = sum(wid) + gap * (len(wid) - 1)
        k = min(1.0, avail / tot)
        rows.append((idxs, [w * k for w in wid], int(caps * k)))
    ch = caps * 1.0
    th = (ch if rows[0] else 0) + hs * 0.82 + (ch if rows[1] else 0)
    y = cy - th / 2.0
    ys = [None, None]
    if rows[0]:
        ys[0] = y + ch / 2.0
        y += ch
    yh = y + hs * 0.41
    y += hs * 0.82
    if rows[1]:
        ys[1] = y + ch / 2.0
    left, right = cx - hw / 2.0, cx + hw / 2.0
    for ri, rw in enumerate(rows):
        if not rw:
            continue
        xs, _ = _row_x([(w,) for w in rw[1]], gap, cx, "left" if ri == 0 else "right", left, right)
        for j, i in enumerate(rw[0]):
            ev += anim_events(ws[i]["s"], t1, xs[j], ys[ri], texts[i].upper(), base_tags(caps_f, rw[2], st["color"], shad=3, sp=tr), dy=12, dur=.24, opdur=.24)
    ev += anim_events(ws[e]["s"], t1, cx, yh, texts[e], base_tags(hero_f, hs, st["hero_color"], shad=4, italic=True), dy=0, dur=.34, opdur=.34, layer=0)
    return ev


def swiss(p, st, W, H, ctx):
    return aura(p, st, W, H, dict(ctx, swiss=True))


BUILDERS = {"illusion": illusion, "editor_masala": editor_masala, "aura": aura, "swiss": swiss,
            "big_red": big_red, "scribble": scribble, "archives": archives, "blockbuster": blockbuster, "journal": journal, "interlock": interlock}


def build(phrases, st, W, H):
    fn = BUILDERS[st["layout"]]
    ev = []
    for p in phrases:
        if not p["words"]:
            continue
        ev += fn(p, st, W, H, {})
    return ev
