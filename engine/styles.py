"""Caption style presets.

mode:
  highlight  whole phrase visible, spoken word gets the 'active' look (like videocaptions 'Highlight')
  sweep      karaoke fill sweeping across each word as it is spoken ('Encore')
  reveal     words appear one by one and stay till phrase ends ('Reveal'); words=1 gives 'Pop'
  flash      whole phrase appears at once ('Flash')
box: None | 'pill' (colored blob behind active word) | 'card' (solid box behind whole line)
Every value can be overridden per render (see ass.OVERRIDE_KEYS).
"""

def _scan_fonts():
    """family name (as libass will see it) -> file, for every .ttf in fonts/"""
    from PIL import ImageFont
    from .util import FONTS
    out = {}
    for f in sorted(FONTS.glob("*.ttf")):
        try:
            fam, sub = ImageFont.truetype(str(f), 20).getname()
        except Exception:
            continue
        if sub == "Italic" and fam in out:
            continue            # the italic face is chosen with the italic flag
        out[fam if sub in ("Regular", "Italic") else "%s %s" % (fam, sub)] = f.name
    return out


FONT_FILES = _scan_fonts()

_BASE = dict(
    mode="highlight", font="Poppins ExtraBold", size=84, uppercase=False, italic=False,
    color="#FFFFFF", active="#FFE600", dim=None,
    outline_color="#000000", outline=7, shadow=0, shadow_color="#000000", blur=0,
    box=None, box_color="#000000", box_alpha=0, box_pad=14,
    anim="pop", active_scale=100, words=3, max_chars=22, y=66, x=50, safe=True, spacing=0,
    palette=None,
    # --- "text behind you" templates: hero word behind the person + small caption line in front
    behind=False, hero_mode="word", hero_font="Poppins Black", hero_size=240, hero_color="#FFFFFF", hero_outline=0,
    hero_outline_color="#000000", hero_shadow=0, hero_shadow_color="#000000", hero_blur=0, hero_upper=True, hero_italic=False,
    hero_fill=True, hero_opacity=100, hero_box=None, hero_box_pad=18, hero_spacing=0, hero_anim="pop", hero_y=24, hero_x=50,
    hero_wmax=1000,
    # --- "key words stacked" (Glow Key / Shadow Key / Classic Key): the content words of a phrase come in BIG, one under the
    # other, below the small line; they use the hero_* look. emph_max = how many per phrase, emph_gap = line height / size.
    emph=False, emph_max=2, emph_gap=1.18, emph_glow=0,
    # seconds each caption fades in / out over (0 = a hard cut, as most the reference style looks do)
    fade_in=0.0, fade_out=0.0,
    # highlight: words already said stay in the spoken colour (Ali Abdaal's card), not only the one being said
    keep_spoken=False,
    # "center" or "left": left sets the line from x (percent of the width) outward, as the reference style's small lines are
    align="center",
    # the hero word is sized to span this percent of the frame width (0 = the size given), as the reference style's big words do
    hero_fit=0,
    # each key word of a phrase takes the hero slot in turn, as it is said (the reference style's behind-you looks), instead of one per phrase
    hero_seq=False,
    # with hero_fit: False = only shrink a long word to fit, never enlarge a short one
    hero_grow=True,
    # how many key words per phrase take the hero slot, and which: "longest", or the first ("leading") / last ("trailing") ones
    hero_max=3, hero_pick="longest",
    # width of the small caption box as a percent of the frame (0 = the default 80 %)
    box_w=0,
    # gap between words, in ems of the caption size, over the plain space (0 = as it comes)
    gap_em=0,
    # the key-word column (the reference style Glow): its vertical centre as a percent of the frame height, and the widest a key word may run
    col_y=84.4, emph_wmax=68.9,
    # behind-you looks that change layout from phrase to phrase (the reference style's Sash): the big word's rotation in degrees (counter-clockwise),
    # its colour in turn per phrase, and the second layout every other phrase takes (hero_y, small line y, small line size scale)
    hero_motion="", hero_motion_t=0.0, support_motion="", motion_fps=30,
    hero_align="center", hero_front=False,
    # highlight mode: opacity of the words not yet said (1 = as the rest)
    unsaid_opacity=1.0, emph_italic=False,
    # a layout of its own (engine/dynamic.py): illusion, editor_masala, aura, swiss, big_red, scribble, archives, blockbuster, journal, interlock
    layout="",
    hero_rot=0, hero_colors=None, alt_hero_y=0, alt_y=0, alt_size=1.0,
    # the bubble pill: horizontal padding and total height, in ems of the caption size
    pill_padx=0.5, pill_h=1.5,
)


def _s(label, desc, **kw):
    d = dict(_BASE)
    d.update(kw)
    d["label"], d["desc"] = label, desc
    return d


STYLES = {
    "hormozi": _s("Hormozi", "Bold caps, 3 words, spoken word pops yellow.",
                  font="Poppins Black", size=104, uppercase=True, active="#FFE600", words=3, max_chars=20,
                  outline=9, shadow=2, anim="pop", active_scale=108),
    "green-pop": _s("Green Pop", "Hormozi look with a green spoken word.",
                    font="Poppins Black", size=104, uppercase=True, active="#2BFF5E", words=3, max_chars=20,
                    outline=9, shadow=2, anim="pop", active_scale=108),
    "mrbeast": _s("MrBeast", "One huge word at a time, bouncy pop, changing colours.",
                  mode="reveal", font="Bangers", size=170, uppercase=True, words=1, max_chars=14,
                  outline=12, shadow=4, anim="bounce", color="#FFFFFF", active="#FFFFFF",
                  palette=["#FFFFFF", "#FFE600", "#2BFF5E", "#FF3B3B", "#33C3FF"], y=62),
    "karaoke": _s("Karaoke", "Words fill with colour as they are spoken.",
                  mode="sweep", font="Poppins ExtraBold", size=80, uppercase=False, color="#FFFFFF",
                  active="#FFD400", dim="#FFFFFF", outline=7, shadow=2, words=5, max_chars=26, anim="fade"),
    "headliner": _s("Headliner", "Spoken word sits in a colour box.",
                    mode="highlight", box="pill", font="Poppins ExtraBold", size=78, uppercase=False,
                    color="#FFFFFF", active="#FFFFFF", box_color="#7C3AED", outline=0, shadow=0, words=4,
                    max_chars=26, anim="pop", box_pad=16),
    "clean": _s("Clean", "White semibold text, soft shadow, words fade in.",
                mode="reveal", font="Poppins SemiBold", size=70, uppercase=False, color="#FFFFFF",
                active="#FFFFFF", outline=0, shadow=3, shadow_color="#000000", blur=1, words=5,
                max_chars=30, anim="fade"),
    "ali": _s("Ali Card", "Dark text on a white card, spoken word in full ink.",
              mode="highlight", box="card", font="Poppins Bold", size=66, uppercase=False,
              color="#8A8A8A", active="#111111", dim="#8A8A8A", box_color="#FFFFFF", outline=0, words=5,
              max_chars=30, anim="fade", box_pad=18),
    "box": _s("Black Box", "White text on a black box, whole line at once.",
              mode="flash", box="card", font="Poppins Bold", size=64, uppercase=True, color="#FFFFFF",
              active="#FFFFFF", box_color="#000000", box_alpha=40, outline=0, words=5, max_chars=28,
              anim="fade", box_pad=18),
    "neon": _s("Neon", "Glowing lyrics, spoken word lights up.",
               mode="highlight", font="Poppins Bold", size=80, uppercase=True, color="#C9D6FF",
               active="#39FFF5", dim="#8793B8", outline=3, outline_color="#0A2A8C", shadow=0, blur=5,
               words=3, max_chars=22, anim="fade", active_scale=104),
    "comic": _s("Pop Comics", "One word at a time, comic outline + 3D shadow.",
                mode="reveal", font="Bangers", size=150, uppercase=True, color="#FFE600", active="#FFE600",
                outline=14, outline_color="#000000", shadow=9, shadow_color="#E11D48", words=1, max_chars=14,
                anim="bounce", y=62),
    "serif": _s("Serif Premiere", "Elegant serif, spoken word italic red.",
                mode="highlight", font="DM Serif Display", size=92, uppercase=False, color="#FFFFFF",
                active="#FF4D4D", outline=0, shadow=4, blur=1, words=4, max_chars=24, anim="fade",
                active_scale=100),
    "tagline": _s("Tagline", "One word on a red bar, key-word energy.",
                  mode="reveal", box="card", font="Poppins ExtraBold", size=92, uppercase=True, color="#FFFFFF",
                  active="#FFFFFF", box_color="#E11D48", outline=0, words=1, max_chars=14, anim="pop", box_pad=20),
    "minimal": _s("Minimal", "Small, calm, lowercase-friendly, no effects.",
                  mode="flash", font="Poppins Medium", size=58, uppercase=False, color="#FFFFFF",
                  active="#FFFFFF", outline=4, shadow=1, words=6, max_chars=34, anim="fade", y=70),
    # --- more looks, following the families of videocaptions.ai (Masthead, Stamp Flow, Halo, Upper Dynamic, ...)
    "masthead": _s("Masthead", "Serif lines on a shaded box, spoken word at full strength, the rest dimmed.",
                   mode="highlight", box="card", font="DM Serif Display", size=84, uppercase=False, color="#B9B2A5",
                   active="#FFFFFF", dim="#B9B2A5", box_color="#000000", box_alpha=70, outline=0, words=4,
                   max_chars=26, anim="fade", box_pad=18),
    "stamp": _s("Stamp Flow", "Clean white words land on a red bar, one by one.",
                mode="reveal", box="card", font="Poppins Bold", size=76, uppercase=True, color="#FFFFFF",
                active="#FFFFFF", box_color="#D7263D", outline=0, words=3, max_chars=22, anim="slide", box_pad=16),
    "halo": _s("Halo", "Quiet serif, words fade in, the newest glows in italic ice-blue.",
               mode="highlight", font="DM Serif Display", size=88, italic=True, uppercase=False, color="#FFFFFF",
               active="#9FD8FF", dim="#FFFFFF", outline=0, shadow=3, blur=2, words=4, max_chars=26, anim="fade"),
    "upper": _s("Upper Dynamic", "Electric-blue spotlight caps with a drop shadow.",
                mode="highlight", font="Poppins ExtraBold", size=88, uppercase=True, color="#FFFFFF",
                active="#2F7BFF", dim="#FFFFFF", outline=0, shadow=5, shadow_color="#0A1B5C", words=3,
                max_chars=22, anim="pop", active_scale=106),
    "bebas": _s("Bebas Gold", "Tall condensed caps, golden spoken word.",
                mode="highlight", font="Bebas Neue", size=150, uppercase=True, color="#FFFFFF",
                active="#FFC83D", outline=8, shadow=3, words=3, max_chars=20, anim="pop", active_scale=108),
    "anton": _s("Anton Red", "Heavy poster caps, red spotlight.",
                mode="highlight", font="Anton", size=130, uppercase=True, color="#FFFFFF",
                active="#FF3B30", outline=9, shadow=4, words=3, max_chars=20, anim="bounce", active_scale=108),
    "sticker": _s("Sticker Flash", "Whole line at once on a thick white sticker border.",
                  mode="flash", font="Bangers", size=120, uppercase=True, color="#FFE600", active="#FFE600",
                  outline=16, outline_color="#FFFFFF", shadow=6, shadow_color="#222222", words=3, max_chars=20,
                  anim="bounce"),
    "pop-black": _s("Pop Black", "One word at a time, Archivo Black, no animation.",
                    mode="reveal", font="Archivo Black", size=150, uppercase=True, color="#FFFFFF", active="#FFFFFF",
                    outline=10, shadow=0, words=1, max_chars=14, anim="none", y=62),
}

DEFAULT_STYLE = "hormozi"


from .templates import add_all  # noqa: E402

add_all(STYLES, _s)

from .preset_static import apply_static as _apply_static  # noqa: E402
from .preset_data import apply as _apply_presets, apply_motion as _apply_motion, apply_reel as _apply_reel, apply_spatial as _apply_spatial  # noqa: E402

_apply_presets(STYLES, FONT_FILES)
_apply_motion(STYLES)
_apply_reel(STYLES, FONT_FILES)
_apply_spatial(STYLES, FONT_FILES)
_apply_static(STYLES, FONT_FILES)


# The tabs of popular caption editors/templates, by our ids (a look can sit in two, as it does there).
TEMPLATE_GROUPS = {
    "Popular": ["glow-key", "ali", "shadow-key", "classic-key", "clean", "bubble", "hormozi", "boxed", "mrbeast", "mr-beast-2",
                "iman", "prism", "highlighted", "clean-glow", "plain-clean", "black-punch"],
    "Behind you": ["big-reveal", "beacon", "cove", "driftwood", "ellis", "ferrier", "garnet", "hawser", "ibis", "jetty", "keel",
                   "lanyard", "mizzen", "netting", "outhaul", "painter", "quay", "scupper", "taffrail", "underway", "vang",
                   "windlass", "yawl", "abbey", "belfry", "cloister", "dovecote", "effigy", "mullion"],
    "Bold & animated": ["glow-key", "shadow-key", "classic-key", "delhi", "illusion", "editor-masala", "aura", "swiss", "big-red",
                        "scribble", "archives", "blockbuster", "journal", "interlock", "anchorage", "rudder"],
    "Clean": ["ali", "clean", "bubble", "hormozi", "boxed", "mrbeast", "mr-beast-2", "iman", "prism", "highlighted", "clean-glow",
              "plain-clean", "black-punch", "word-focus", "pixelated", "liquid", "tabahi", "deep-glow", "seedha", "cinematic"],
    "Property reels": ["iron", "jamb", "newel", "soffit", "casement", "sash", "muntin", "louver", "shutter", "patio", "porch",
                       "awning", "sill", "joist", "foyer", "loft", "attic", "chimney", "baluster", "banister"],
    "Around you": ["oriel", "lantern", "atrium", "oculus", "fanlight", "clerestory", "tread", "riser", "parquet", "terrazzo",
                   "fresco", "mural", "gazebo", "eave", "adobe", "tile", "thatch", "dome", "stucco", "shingle", "lath"],
}
