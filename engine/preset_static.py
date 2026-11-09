"""The "static" and "dynamic" styles of popular caption editors (Delhi, Tabahi, Mr Beast, Aura ...), as the numbers in the reference style's own renderer give them.

the reference style sizes text with t4(n) = n/270 of the frame width, so n becomes n*4 CSS px on our 1080 frame; libass counts the font's whole line
height as its size, so `fs = css_px * (ascent+descent)/em` of the font. Outlines the reference style draws as eight text-shadows of radius r px (r in the
same 1/270 units) become an ASS outline of 4*r px. Words of a phrase all stay on screen; the one being said takes `active`, the ones not
yet said fade to `unsaid_opacity`.
"""
from PIL import ImageFont

from .util import FONTS

_ratio = {}


def _fs(font_files, font, n):
    path = FONTS / font_files.get(font, "Poppins-ExtraBold.ttf")
    r = _ratio.get(path)
    if r is None:
        a, d = ImageFont.truetype(str(path), 100).getmetrics()
        r = _ratio[path] = (a + d) / 100.0
    return int(round(n * 4 * r))


def _edge(n, em):
    """px of an outline `em` ems wide on text of the reference style size n"""
    return max(1, int(round(n * 4 * em)))


# id: (font, n, extra settings)
def _table(f):
    return {
        "ali": ("Poppins ExtraBold", 16, dict(color="#1F2022", active="#000000")),
        "clean": ("Inter", 18, dict(color="#FFFFFF")),
        "boxed": ("Inter Bold", 19, dict(spacing=_edge(19, .04), uppercase=True)),
        "mrbeast": ("Luckiest Guy", 20, dict(uppercase=True, outline=_edge(20, .2) + 1, outline_color="#000000", shadow=0, color="#FFFFFF", active="#FFFFFF")),
        "mr-beast-2": ("Jost Bold", 20, dict(uppercase=True, color="#FFD700", active="#FFD700", outline=2, outline_color="#000000", shadow=26,
                                              shadow_color="#000000", blur=1)),
        "iman": ("Mona Sans", 18, dict(uppercase=True, color="#FFFFFF", active="#FFFFFF", spacing=0, shadow=0)),
        "prism": ("Montserrat Bold", 19, dict(uppercase=True, spacing=_edge(19, .04), color="#A34EFF", active="#A34EFF")),
        "highlighted": ("Montserrat Bold", 17, dict(color="#FFFFFF", active="#F5A623")),
        "clean-glow": ("Inter", 18, dict(color="#FFFFFF")),
        "plain-clean": ("Inter", 18, dict(color="#FFFFFF", shadow=4)),
        "black-punch": ("Anton", 22, dict(uppercase=True, color="#000000", active="#000000", outline=_edge(22, .135), outline_color="#FFFFFF", shadow=0)),
        "word-focus": ("Inter SemiBold", 18, dict(color="#FFFFFF", active="#FFFFFF", unsaid_opacity=.18, keep_spoken=True, mode="highlight")),
        "delhi": ("Instrument Sans", 17, dict(emph_italic=True, color="#FFFFFF", active="#FFFFFF", unsaid_opacity=.2, keep_spoken=True, mode="highlight", outline=0,
                                               shadow=0)),
        "pixelated": ("Silkscreen Bold", 16, dict(uppercase=True, spacing=_edge(16, .1), words=1, color="#FFFFFF", active="#FFFFFF")),
        "liquid": ("Montserrat", 15, dict(color="#FFFFFF", active="#FFFFFF", dim="#918B7C")),
        "tabahi": ("Bangers", 20, dict(uppercase=True, color="#FFFFFF", active="#FFFFFF", outline=_edge(20, .2) + 2, outline_color="#000000", shadow=0,
                                        box=None)),
        "deep-glow": ("Anton", 20, dict(uppercase=True, color="#FF00FF", active="#FF00FF", outline=3, outline_color="#FF00FF", unsaid_opacity=.28,
                                         keep_spoken=True, mode="highlight", blur=2)),
        "seedha": ("Rubik Black", 22, dict(uppercase=True, color="#FFFFFF", active="#FFFFFF", outline=_edge(22, .2), outline_color="#000000", shadow=0)),
        "cinematic": ("Montserrat Bold", 16, dict(uppercase=True, spacing=_edge(16, .28), color="#FFFFFF", active="#FFFFFF", shadow=0)),
        # dynamic looks: the reference style's own default fonts and colours (resolve*Slots)
        "illusion": ("Open Sans Bold", 15, dict(color="#FFFFFF", active="#FFFFFF")),
        "editor-masala": ("Montserrat Bold", 15, dict(color="#FFFFFF", active="#FFD700")),
        "aura": ("Open Sans", 15, dict(color="#FFFFFF", active="#F5D300")),
        "swiss": ("Inter Bold", 15, dict(color="#FFFFFF", active="#F5D300")),
        "big-red": ("Poppins Bold", 15, dict(color="#FFFFFF", active="#D53E3E", y=52)),
        "scribble": ("Caveat", 16, dict(color="#FDFAF3", active="#241C12", box_color="#FFE042", shadow=2)),
        "archives": ("Kaushan Script", 17, dict(color="#E1CDC2", active="#E1CDC2", shadow=3)),
        "blockbuster": ("Anton", 15, dict(color="#FFFFFF", active="#FA232D", uppercase=True)),
        "journal": ("Caveat", 28, dict(color="#FFFFFF", active="#FFFFFF", shadow=3)),
        "interlock": ("Montserrat Bold", 15, dict(uppercase=True, spacing=_edge(15, .045), color="#F7F4EE", active="#F7F4EE")),
    }


# hero (big word) fonts of the dynamic looks that have one
_HERO = {
    "illusion": ("Open Sans Bold", "#FFFFFF"),
    "editor-masala": ("Instrument Serif Italic", "#FFFFFF"),
    "aura": ("Anton", "#F5D300"),
    "swiss": ("Inter Bold", "#F5D300"),
    "big-red": ("Poppins Bold", "#D53E3E"),
    "blockbuster": ("Great Vibes", "#FFFFFF"),
    "interlock": ("Playfair Display", "#F7F4EE"),
}


_LAYOUT = {"illusion": "illusion", "editor-masala": "editor_masala", "aura": "aura", "swiss": "swiss", "big-red": "big_red", "scribble": "scribble",
           "archives": "archives", "blockbuster": "blockbuster", "journal": "journal", "interlock": "interlock"}


def apply_static(STYLES, FONT_FILES):
    n = 0
    for sid, (font, size_n, extra) in _table(FONT_FILES).items():
        st = STYLES.get(sid)
        if not st:
            continue
        if font not in FONT_FILES:
            font = st["font"]
        st.update(font=font, size=_fs(FONT_FILES, font, size_n))
        st.update(extra)
        if sid in _LAYOUT:
            st["layout"] = _LAYOUT[sid]
            st["mode"] = "highlight"
            wn = {"illusion": 6, "editor-masala": 6, "aura": 6, "swiss": 5, "big-red": 5, "scribble": 5, "archives": 5, "blockbuster": 5,
                  "journal": 5, "interlock": 5}[sid]
            st["words"], st["max_chars"] = wn, wn * 8
        if sid in _HERO:
            hf, hc = _HERO[sid]
            if hf in FONT_FILES:
                st["hero_font"] = hf
            st["hero_color"] = hc
        n += 1
    return n
