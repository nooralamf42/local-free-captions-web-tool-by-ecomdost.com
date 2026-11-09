"""Applies the numbers the reference style's own editor uses for its looks (engine/preset_looks.json: fonts, sizes, positions, colours,
shadows, how the big word is chosen and fitted) to our templates of the same names.

the reference style's sizes are in pixels of a ~360 px wide player, so they are scaled up to our 1080 px frame: small captions by SMALL_K,
the big ("impact") word by BIG_K - the two factors measured against the reference style's own preview videos (Outhaul, Netting, Jetty).
"""
import json
import re

from .util import ROOT

SMALL_K = 6.0
BIG_K = 4.65
_WEIGHTS = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700,
            "ExtraBold": 800, "Black": 900}
_ALIAS = {"interstory": "inter", "poppinsstory": "poppins", "poppinsbold": "poppins", "inter tight": "inter",
          "workSans": "inter", "helveticabold": "inter", "helvetica": "inter", "futura": "jost", "drukwide": "archivoblack",
          "komikaaxis": "bangers", "clashdisplay": "poppins", "instrumentserifitalic": "instrumentserif", "dmsans": "inter", "aeinter": "inter", "fredokaone": "fredoka"}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _pick_font(css, weight, files):
    """('Montserrat, sans-serif', 800) -> the key of the nearest face we have, or None."""
    name = re.split(r",", css or "")[0].strip("'\" ")
    n = _norm(name)
    if n.startswith("ae"):
        n = n[2:]
    n = _ALIAS.get(n, n)
    best = None
    for key in files:
        root, _, rest = key.partition(" ")
        # families have spaces ("Press Start 2P"): match the longest family prefix
        for cut in range(len(key), 0, -1):
            if key[:cut].strip() and _norm(key[:cut]) == n and (cut == len(key) or key[cut] == " "):
                tail = key[cut:].strip()
                w = _WEIGHTS.get(tail.replace(" ", ""), 400 if not tail else None)
                if w is None:
                    break
                score = abs(w - (weight or 400))
                if best is None or score < best[0]:
                    best = (score, key)
                break
    return best[1] if best else None


def _hex(rgba):
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgba or "")
    return "#%02X%02X%02X" % tuple(int(x) for x in m.groups()) if m else None


def apply(STYLES, FONT_FILES):
    path = ROOT / "engine" / "preset_looks.json"
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for cid, v in data.items():
        sid = re.sub(r"[^a-z0-9]+", "-", v["name"].lower()).strip("-")
        if sid not in STYLES:
            continue
        st = STYLES[sid]
        upd = {}
        small = _pick_font(v.get("font"), v.get("weight"), FONT_FILES)
        if small:
            upd["font"] = small
        if v.get("sizePx"):
            upd["size"] = int(v["sizePx"] * SMALL_K)
        if v.get("positionYPct") is not None:
            upd["y"] = v["positionYPct"]
        if v.get("color"):
            upd["color"] = v["color"]
        if v.get("accent"):
            upd["active"] = v["accent"]
        upd["strip_punct"] = False
        if v.get("transform") == "uppercase":
            upd["uppercase"] = True
        if v.get("letterSpacingEm") is not None:
            upd["spacing"] = int(v["letterSpacingEm"] * upd.get("size", st["size"]))
        sh = v.get("shadow")
        if isinstance(sh, dict):
            upd["shadow"] = max(2, int(sh.get("offsetY", 3) * 1.2))
            upd["blur"] = max(1, int(sh.get("blurPx", 8) / 8))
            if _hex(sh.get("color")):
                upd["shadow_color"] = _hex(sh["color"])
        upd["words"] = int(v.get("maxWords") or st["words"])
        if v.get("boxWidthPct"):
            upd["box_w"] = v["boxWidthPct"]
        upd["mode"] = "reveal" if v.get("reveal") else "highlight"
        upd["anim"] = "fade" if v.get("animIn") in ("fade", "fadeDown", "fadeUp") else "none"

        imp = v.get("impact")
        hero_font = None
        if isinstance(imp, dict):
            hero_font = _pick_font(imp.get("font"), imp.get("weight", 400), FONT_FILES)
        elif v.get("accentFont"):
            hero_font = _pick_font(v["accentFont"], v.get("accentWeight", 400), FONT_FILES)
        if hero_font:
            upd["hero_font"] = hero_font
        if isinstance(imp, dict):
            upd["hero_size"] = int(imp.get("sizePx", 50) * BIG_K)
            chip = imp.get("chip")
            upd["hero_y"] = imp.get("yPct", 26) + (8.5 if isinstance(chip, dict) else 0)
            upd["hero_fit"] = imp.get("widthPct", 92)
            upd.update(hero_grow=False, hero_seq=True, hero_upper=bool(imp.get("uppercase")), hero_italic=bool(imp.get("italic")))
            upd["hero_color"] = imp.get("color") or v.get("accent", "#FFFFFF")
            if imp.get("letterSpacingEm") is not None:
                upd["hero_spacing"] = int(imp["letterSpacingEm"] * upd["hero_size"])
            upd["hero_max"] = int(imp.get("maxPerClip", 3))
            upd["hero_pick"] = imp.get("select", "longest")
            if isinstance(chip, dict):
                upd["hero_box"] = chip.get("bg", "#96FF1A")
                upd["hero_box_pad"] = 20
            else:
                upd["hero_box"] = None
            upd["hero_blur"] = 0
        elif v.get("accent"):
            upd["hero_color"] = v["accent"]
        st.update(upd)
        n += 1
    return n


_SUPPORT_ANIM = {"fade": "fade", "bounce": "bounce", "slide": "slide", "type": "none"}


def apply_motion(STYLES):
    """Each look's entrance animations as the reference style defines them (engine/preset_motion.json): the big word's motion and tilt, and how the
    small words come in."""
    path = ROOT / "engine" / "preset_motion.json"
    if not path.exists():
        return 0
    n = 0
    for cid, v in json.loads(path.read_text(encoding="utf-8")).items():
        st = STYLES.get(cid[5:])
        if not st:
            continue
        if v.get("heroMotion") and st["hero_seq"]:
            st["hero_motion"] = v["heroMotion"]
            if v.get("heroRotate") and not st["hero_rot"]:
                st["hero_rot"] = -float(v["heroRotate"])
        sm = v.get("supportMotion")
        if sm in _SUPPORT_ANIM and st["mode"] == "reveal":
            st["support_motion"] = sm if sm == "type" else ""
            st["anim"] = _SUPPORT_ANIM[sm]
        n += 1
    return n


def apply_reel(STYLES, FONT_FILES):
    """The Property reels (Newel, Sash, Louver ...): the reference style's own fonts, weights, colours, tracking, case, alignment and strokes for the big
    word (its accentFont) and the small words (its font), read from engine/preset_reel.json."""
    path = ROOT / "engine" / "preset_reel.json"
    if not path.exists():
        return 0
    n = 0
    for cid, v in json.loads(path.read_text(encoding="utf-8")).items():
        st = STYLES.get(cid[5:])
        r = v.get("reelTheme")
        if not st or not r:
            continue
        upd = {}
        small = _pick_font(v.get("font"), v.get("weight"), FONT_FILES)
        hero = _pick_font(v.get("accentFont"), v.get("accentWeight") or r.get("heroWeight"), FONT_FILES)
        if small:
            upd["font"] = small
        if hero:
            upd["hero_font"] = hero
        if v.get("contextSizePx"):
            upd["size"] = int(v["contextSizePx"] * SMALL_K * 1.0)
        acc = r.get("accents") or []
        if v.get("accent") and not acc:
            acc = [v["accent"]]
        if acc:
            upd["hero_color"] = acc[0]
            upd["hero_colors"] = acc if len(acc) > 1 else None
            upd["active"] = v.get("accent") or acc[0]
        if r.get("supportColor"):
            upd["color"] = r["supportColor"]
            upd["dim"] = r["supportColor"]
        upd["hero_upper"] = bool(r.get("heroUpper"))
        if r.get("supportUpper") is not None:
            upd["uppercase"] = bool(r["supportUpper"])
        hs = st["hero_size"]
        if r.get("heroTrackingEm") is not None:
            upd["hero_spacing"] = int(r["heroTrackingEm"] * hs)
        if r.get("supportTrackingEm") is not None:
            upd["spacing"] = int(r["supportTrackingEm"] * upd.get("size", st["size"]))
        if r.get("heroAlign") in ("left", "right"):
            upd["hero_align"] = r["heroAlign"]
        stroke = r.get("heroStroke")
        if isinstance(stroke, dict):
            upd["hero_outline"] = max(1, int(stroke.get("em", 0.06) / 2 * hs))
            if stroke.get("color"):
                upd["hero_outline_color"] = stroke["color"]
        glow = r.get("heroGlow")
        if glow:
            col = acc[0] if glow == "accent" and acc else (glow if str(glow).startswith("#") else (acc[0] if acc else "#FFFFFF"))
            upd.update(hero_outline=max(st["hero_outline"], 3), hero_outline_color=col, hero_blur=5)
        if r.get("planes") == "front":
            upd["hero_front"] = True
        st.update(upd)
        n += 1
    return n


def apply_spatial(STYLES, FONT_FILES):
    """Around-you looks are 3D scenes in the reference style; the flat part we can keep is its fonts, colours and sizes (engine/preset_spatial.json)."""
    path = ROOT / "engine" / "preset_spatial.json"
    if not path.exists():
        return 0
    n = 0
    for cid, v in json.loads(path.read_text(encoding="utf-8")).items():
        st = STYLES.get(cid[5:])
        if not st:
            continue
        upd = {}
        small = _pick_font(v.get("font"), v.get("weight"), FONT_FILES)
        hero = _pick_font(v.get("accentFont"), v.get("accentWeight"), FONT_FILES)
        if small:
            upd["font"] = small
        if hero:
            upd["hero_font"] = hero
        cap = (v.get("spatialTheme") or {}).get("caption") or {}
        if v.get("color") or cap.get("color"):
            upd["color"] = cap.get("color") or v["color"]
        acc = cap.get("emphasisColor") or v.get("accent")
        if acc:
            upd["active"] = acc
            upd["hero_color"] = acc
        if v.get("sizePx"):
            upd["size"] = int(v["sizePx"] * SMALL_K)
        st.update(upd)
        n += 1
    return n
