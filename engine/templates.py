"""More templates, modelled on popular caption-editor families: a big HERO word sitting BEHIND the person plus a small caption
line in front ('Behind you'), and a batch of extra clean / bold / glass / pixel looks.
`add_all(STYLES, _s)` is called at the end of engine/styles.py.
"""


def add_all(STYLES, _s):
    # ---------------- behind-you templates -------------------------------------------------------------------
    def beh(sid, label, desc, hero_font, hero_color, size=240, y=24, upper=True, active=None, small_color="#FFFFFF",
            small_font="Poppins SemiBold", small_size=76, small_y=71, hero_mode="word", **kw):
        STYLES[sid] = _s(label, desc, behind=True, mode="highlight", font=small_font, size=small_size, color=small_color,
                         active=active or hero_color, dim=small_color, outline=0, shadow=3, shadow_color="#000000", blur=1,
                         words=4, max_chars=24, anim="fade", y=small_y, hero_font=hero_font, hero_color=hero_color,
                         hero_size=size, hero_y=y, hero_upper=upper, hero_mode=hero_mode, **kw)
        # the reference style's big behind-you words take the slot one at a time as they are said, each sized to span the frame
        if hero_mode == "word" and size >= 190:
            STYLES[sid].update(hero_fit=92, hero_seq=True, strip_punct=False)

    beh("beacon", "Beacon", "Big blue script word behind you.", "Yellowtail", "#2F4BFF", size=300, upper=False)
    beh("cove", "Cove", "Pixel-font hero in hot pink.", "Press Start 2P", "#FF5CA8", size=150, hero_blur=0, hero_shadow=4,
        hero_shadow_color="#5A0F34")
    beh("driftwood", "Driftwood", "Bubbly orange caps behind you.", "Luckiest Guy", "#FF6A1F", size=260)
    beh("ellis", "Ellis", "Cobalt script, lowercase.", "Yellowtail", "#3A5BFF", size=290, upper=False)
    beh("ferrier", "Ferrier", "Soft olive rounded lowercase.", "Lilita One", "#6E8B2D", size=270, upper=False)
    beh("garnet", "Garnet", "Neon lime caps.", "Poppins Black", "#B6FF1F", size=250, active="#B6FF1F")
    beh("hawser", "Hawser", "The whole line, huge, stacked behind you.", "Anton", "#FFFFFF", size=250, y=20, hero_mode="phrase",
        hero_wmax=900)
    beh("ibis", "Ibis", "Wide white caps, yellow spoken word.", "Archivo Black", "#FFFFFF", size=230, active="#E9FF3B")
    beh("jetty", "Jetty", "Glowing red rounded capitals filling the width; light serif words below.", "Bowlby One", "#FF2412", size=260, y=15,
        hero_blur=7, hero_outline=7, hero_outline_color="#FF5A48", small_font="Instrument Serif", small_size=235, small_y=78)
    STYLES["jetty"].update(hero_fit=92, hero_seq=True, mode="reveal", anim="none", words=3, max_chars=26, outline=0, shadow=0, blur=0, strip_punct=False)
    beh("netting", "Netting", "Tight black italic word on a lime box; plain white words below.", "Montserrat Bold", "#101010", size=190, y=26.6,
        upper=False, hero_box="#86F000", hero_box_pad=20, hero_italic=True, hero_spacing=-3, small_font="Poppins Medium", small_size=140,
        small_y=77, small_color="#FFFFFF", active="#FFFFFF")
    STYLES["netting"].update(hero_seq=True, hero_fit=68, hero_grow=False, strip_punct=False, mode="reveal", anim="none", words=3, max_chars=26)
    beh("outhaul", "Outhaul", "Condensed lime capitals across the top; handwritten words above them.", "Anton", "#8DFF00", size=540, y=27,
        small_font="Shadows Into Light Two", small_size=175, small_y=14.5, small_color="#FFFFFF", active="#8DFF00")
    STYLES["outhaul"].update(hero_seq=True, hero_fit=92, hero_grow=False, strip_punct=False, mode="highlight", anim="none", words=3,
                             max_chars=24, hero_blur=0)
    beh("painter", "Painter", "Heavy yellow poster caps.", "Anton", "#FFEB00", size=300, y=22, hero_outline=0)
    beh("quay", "Quay", "Elegant red serif.", "Abril Fatface", "#E01B24", size=270, upper=False, small_font="DM Serif Display",
        active="#E01B24")
    beh("rudder", "Rudder", "Chrome-white word over the chest, behind the face.", "Poppins Black", "#E8EEF7", size=190, y=52,
        upper=False, hero_outline=0, hero_shadow=4, hero_shadow_color="#8AA1C8", small_y=62)
    beh("scupper", "Scupper", "Thin white caps on top, bold line below.", "Poppins ExtraBold", "#FFFFFF", size=170, y=11,
        small_font="Poppins ExtraBold", small_y=64)
    beh("taffrail", "Taffrail", "Violet gradient-look caps.", "Poppins Black", "#8B7BFF", size=250, y=15, upper=False)
    beh("underway", "Underway", "Small lime heading.", "Poppins Bold", "#B5E04B", size=110, y=9)
    beh("vang", "Vang", "Slim white heading.", "Poppins Bold", "#FFFFFF", size=100, y=8, upper=False, small_y=66)
    beh("windlass", "Windlass", "Cream rounded word.", "Poppins ExtraBold", "#FBFFB0", size=170, y=14, upper=False, x=50)
    beh("yawl", "Yawl", "Lime-yellow rounded word on top.", "Poppins ExtraBold", "#E4FF4A", size=190, y=10, upper=False)
    beh("abbey", "Abbey", "Mustard chunky serif.", "Caprasimo", "#F6C23E", size=250, y=15, upper=False)
    beh("cloister", "Cloister", "Black stencil word on a white bar.", "Archivo Black", "#101010", size=170, y=70, hero_box="#FFFFFF",
        hero_box_pad=20, small_y=79, active="#FFFFFF")
    beh("dovecote", "Dovecote", "Marker-pen yellow.", "Permanent Marker", "#FFD84A", size=160, y=22, upper=False)
    beh("effigy", "Effigy", "Thin white serif caps.", "Gloock", "#FFFFFF", size=130, y=34, small_y=68, hero_shadow=0)
    beh("iron", "Iron", "Violet bold word.", "Bowlby One", "#A83CF6", size=250, y=30, upper=False)
    beh("jamb", "Jamb", "Deep purple caps.", "Poppins Black", "#7B3FF6", size=230, y=14)
    beh("newel", "Newel", "Gold serif caps.", "Yeseva One", "#D9C090", size=210, y=17, upper=False, hero_shadow=0)
    beh("soffit", "Soffit", "Hot orange block caps.", "Bungee", "#FF5A2B", size=200, y=12)
    beh("casement", "Casement", "Teal outline-only letters.", "Poppins Black", "#5EC8D8", size=230, y=13, upper=False,
        hero_fill=False, hero_outline=5, hero_outline_color="#5EC8D8")
    beh("sash", "Sash", "A big handwritten word, tilted, in turn white, peach, mint and pink; small handwritten words around it.", "Caveat",
        "#FFFFFF", size=370, y=29, upper=False, small_font="Mynerve", small_size=140, small_y=20, small_color="#FFF8EE", active="#FFF8EE")
    STYLES["sash"].update(hero_seq=True, hero_fit=88, hero_grow=False, hero_motion="type", hero_rot=4, hero_colors=["#FFFFFF", "#FFD6A5", "#CDEAC0", "#FFC8DD"],
                          alt_hero_y=79, alt_y=72, strip_punct=False, mode="reveal", anim="none", words=4, max_chars=34, hero_max=1,
                          shadow=3, blur=0)
    beh("muntin", "Muntin", "Big white word, bottom left.", "Poppins Black", "#FFFFFF", size=260, y=78, x=30, upper=False,
        small_y=66, hero_shadow=4)
    beh("louver", "Louver", "Plain big white caps.", "Poppins Black", "#FFFFFF", size=220, y=10)
    beh("shutter", "Shutter", "White serif outline.", "DM Serif Display", "#FFFFFF", size=200, y=14, hero_fill=False,
        hero_outline=3, hero_outline_color="#FFFFFF", hero_italic=True, upper=True)
    beh("patio", "Patio", "Arcade green glow.", "Silkscreen", "#3CFF4F", size=200, y=13, hero_blur=2)
    beh("porch", "Porch", "Yellow caps with a thick black edge.", "Poppins Black", "#FFD400", size=220, y=12, hero_outline=10)
    beh("awning", "Awning", "Gold serif.", "Abril Fatface", "#D4A24C", size=250, y=16, upper=False, hero_shadow=0)
    beh("sill", "Sill", "Teal chunky word.", "Poppins Black", "#2EC4B6", size=240, y=16, upper=False)
    beh("joist", "Joist", "Coral-orange caps.", "Poppins Black", "#FF6A3D", size=230, y=12)
    beh("foyer", "Foyer", "Pink serif italic.", "DM Serif Display", "#F7A8C8", size=250, y=16, upper=False, hero_italic=True)
    beh("loft", "Loft", "White heavy word at the bottom.", "Poppins Black", "#FFFFFF", size=250, y=72, upper=False, small_y=62,
        x=62)
    beh("marker", "Marker", "Retro stencil caps.", "Black Ops One", "#FFFFFF", size=210, y=14, hero_outline=0)
    beh("neon-hero", "Neon Hero", "Glowing cyan caps.", "Poppins Black", "#39FFF5", size=230, y=14, hero_blur=4,
        hero_outline=3, hero_outline_color="#0A8F8A")
    beh("mono", "Monoton", "Retro neon lines.", "Monoton", "#FF4FD8", size=170, y=15, upper=True)
    beh("big-reveal", "Big Reveal", "Heavy yellow caps across the top.", "Poppins Black", "#FFD400", size=230, y=12)
    beh("keel", "Keel", "Thin gold serif caps.", "Gloock", "#EBCB5E", size=210, y=12, hero_shadow=0)
    beh("lanyard", "Lanyard", "Heavy white lowercase.", "Poppins Black", "#FFFFFF", size=240, y=12, upper=False)
    beh("mizzen", "Mizzen", "Small slate-blue italic serif.", "DM Serif Display", "#7AA0B8", size=120, y=11, upper=False,
        hero_italic=True, hero_shadow=0)
    beh("belfry", "Belfry", "Soft cream italic serif.", "Instrument Serif", "#F3EBD3", size=270, y=13, upper=False,
        hero_italic=True, hero_shadow=0)
    beh("mullion", "Mullion", "Yellow caps across the top.", "Poppins ExtraBold", "#FFD400", size=200, y=10)
    # property reels
    beh("attic", "Attic", "Neon-pink condensed word behind you, small white words fading in.", "Anton", "#FF2FD0", size=330, y=15,
        hero_blur=7, hero_outline=5, hero_outline_color="#FF8BEA", hero_anim="fade", small_font="Poppins Medium", small_size=46, small_y=64)
    STYLES["attic"].update(mode="reveal", anim="fade", words=3, max_chars=22)
    beh("chimney", "Chimney", "Giant red caps, cut off at the edge.", "Poppins Black", "#E0242C", size=340, y=22, x=34)
    beh("baluster", "Baluster", "Small white heading.", "Poppins Bold", "#FFFFFF", size=120, y=12, upper=False)
    beh("banister", "Banister", "White word on a green sticker.", "Poppins ExtraBold", "#FFFFFF", size=150, y=18, upper=False,
        hero_box="#1B9E77", hero_box_pad=20, active="#1B9E77")
    # around you
    beh("oriel", "Oriel", "Red heavy sans, two big lines.", "Poppins Black", "#FF2A2A", size=210, y=16, hero_mode="phrase")
    beh("lantern", "Lantern", "Yellow glowing italic.", "Poppins ExtraBold", "#FFD84A", size=170, y=26, upper=False, hero_italic=True,
        hero_blur=4)
    beh("atrium", "Atrium", "Red heavy italic words.", "Poppins Black", "#FF3B30", size=190, y=15, upper=False, hero_italic=True)
    beh("oculus", "Oculus", "Gold serif, stacked.", "DM Serif Display", "#D9B24C", size=210, y=14, upper=True)
    beh("fanlight", "Fanlight", "Purple heavy italic.", "Poppins Black", "#8B6BFF", size=220, y=14, upper=True, hero_italic=True)
    beh("clerestory", "Clerestory", "Lime heavy italic.", "Poppins Black", "#B6FF1F", size=220, y=14, upper=True, hero_italic=True)
    beh("tread", "Tread", "Small cream italic serif.", "Instrument Serif", "#F3E9C8", size=120, y=14, upper=False, hero_italic=True,
        hero_shadow=0)
    beh("riser", "Riser", "Blue heavy caps.", "Poppins Black", "#5B8CFF", size=200, y=13)
    beh("parquet", "Parquet", "Pink thin italic serif.", "Instrument Serif", "#FF9ACB", size=210, y=16, upper=False, hero_italic=True,
        hero_shadow=0)
    beh("terrazzo", "Terrazzo", "Coral italic serif.", "Instrument Serif", "#FF8A7A", size=240, y=16, upper=False, hero_italic=True,
        hero_shadow=0)
    beh("fresco", "Fresco", "Lime heavy italic words.", "Poppins Black", "#B6FF1F", size=200, y=16, upper=True, hero_italic=True)
    beh("mural", "Mural", "Yellow caps with a black edge.", "Poppins Black", "#FFD400", size=200, y=18, hero_outline=9)
    beh("gazebo", "Gazebo", "Icy-blue glow.", "Poppins ExtraBold", "#7CC8FF", size=160, y=20, upper=False, hero_blur=5)
    beh("eave", "Eave", "Pink-orange glow.", "Poppins ExtraBold", "#FF7A6B", size=160, y=20, upper=False, hero_blur=5)
    beh("adobe", "Adobe", "Amber glowing serif italic.", "DM Serif Display", "#FFB23A", size=170, y=18, upper=False, hero_italic=True,
        hero_blur=4)
    beh("tile", "Tile", "Violet glow, italic.", "Poppins ExtraBold", "#A78BFF", size=170, y=20, upper=False, hero_italic=True,
        hero_blur=5)
    beh("thatch", "Thatch", "Soft pink smear of light.", "Poppins ExtraBold", "#FF5FBF", size=160, y=22, upper=False, hero_blur=6)
    beh("dome", "Dome", "Orange caps arched over the head.", "Poppins Black", "#FF8A1F", size=190, y=14, hero_outline=2,
        hero_outline_color="#7A3A00")
    beh("stucco", "Stucco", "Small gold serif, arched.", "Yeseva One", "#D9B24C", size=120, y=15, upper=False, hero_shadow=0)
    beh("shingle", "Shingle", "Hot-pink glowing words.", "Poppins Black", "#FF3DD0", size=170, y=15, upper=False, hero_blur=5)
    beh("lath", "Lath", "Cyan glowing words.", "Poppins ExtraBold", "#39E0FF", size=160, y=15, upper=False, hero_blur=5)

    # ---------------- regular (in front) templates, in the spirit of reference's first rows -------------------------
    def reg(sid, label, desc, **kw):
        STYLES[sid] = _s(label, desc, **kw)

    reg("classic-key", "Classic Key", "Soft white captions, calm fade.", mode="highlight", font="Poppins SemiBold", size=62, color="#FFFFFF",
        active="#FFFFFF", dim="#D5D5D5", outline=0, shadow=4, blur=1, words=3, max_chars=20, anim="fade", y=72)
    reg("glow-key", "Glow Key", "White text with a soft glow.", mode="highlight", font="Poppins Bold", size=66, color="#FFFFFF",
        active="#FFFFFF", dim="#E7E7E7", outline=2, outline_color="#FFFFFF", shadow=0, blur=6, words=3, max_chars=20, anim="fade", y=72)
    reg("shadow-key", "Shadow Key", "Small white caps with a deep shadow.", mode="highlight", font="Poppins Medium", size=56,
        color="#FFFFFF", active="#FFFFFF", dim="#E1E1E1", outline=0, shadow=7, shadow_color="#000000", blur=2, words=3,
        max_chars=22, anim="fade", y=72)
    reg("bubble", "Bubble", "Every word in a rounded green bubble when spoken.", mode="highlight", box="pill", font="Poppins Bold",
        size=64, color="#FFFFFF", active="#06241A", box_color="#2BD67B", outline=0, shadow=0, words=3, max_chars=22, anim="pop",
        box_pad=16, active_scale=104)
    reg("boxed", "Boxed", "Orange block, white caps, two lines.", mode="flash", box="card", font="Poppins ExtraBold", size=74,
        color="#FFFFFF", active="#FFFFFF", box_color="#F08A00", outline=0, words=4, max_chars=18, anim="slide", box_pad=22, y=70)
    reg("iman", "Iman", "Tiny white caps on black label.", mode="reveal", box="card", font="Poppins Bold", size=48, color="#FFFFFF",
        active="#FFFFFF", box_color="#000000", box_alpha=30, outline=0, words=3, max_chars=26, anim="fade", box_pad=12, uppercase=True)
    reg("prism", "Prism", "Violet caps with a bright spoken word.", mode="highlight", font="Poppins ExtraBold", size=80, color="#9C6BFF",
        active="#E9DCFF", dim="#9C6BFF", uppercase=True, outline=0, shadow=5, shadow_color="#2A0F6B", words=3, max_chars=20, anim="pop")
    reg("highlighted", "Highlighted Word", "Gold spoken word, white rest.", mode="highlight", font="Poppins ExtraBold", size=76,
        color="#FFFFFF", active="#FFC83D", dim="#FFFFFF", outline=0, shadow=5, words=4, max_chars=26, anim="fade", active_scale=104)
    reg("black-punch", "Black Punch", "Caps in thin white boxes.", mode="highlight", box="pill", font="Archivo Black", size=60,
        color="#FFFFFF", active="#000000", box_color="#FFFFFF", outline=0, shadow=0, uppercase=True, words=3, max_chars=20, anim="pop", box_pad=12)
    reg("pixelated", "Pixelated", "Pixel font, lime highlight.", mode="highlight", font="Press Start 2P", size=44, color="#FFFFFF",
        active="#C6FF1F", dim="#FFFFFF", outline=4, shadow=0, uppercase=True, words=3, max_chars=22, anim="none", y=72)
    reg("liquid", "Liquid Glass", "Frosted pill behind soft white text.", mode="flash", box="card", font="Poppins Medium", size=54,
        color="#FFFFFF", active="#FFFFFF", box_color="#FFFFFF", box_alpha=170, outline=0, words=5, max_chars=34, anim="fade", box_pad=22, y=72)
    reg("deep-glow", "Deep Glow", "Violet glow, bright spoken word.", mode="highlight", font="Poppins ExtraBold", size=76,
        color="#C9B5FF", active="#FFFFFF", dim="#B79CFF", outline=3, outline_color="#7A3CFF", shadow=0, blur=8, words=3, max_chars=22, anim="fade")
    reg("seedha", "Seedha Saadha", "Plain white, no fuss.", mode="flash", font="Poppins SemiBold", size=60, color="#FFFFFF", active="#FFFFFF",
        outline=5, shadow=0, words=5, max_chars=32, anim="none", y=72)
    reg("cinematic", "Thora Cinematic", "Spaced serif caps, film style.", mode="flash", font="DM Serif Display", size=54, color="#F2EBDD",
        active="#F2EBDD", outline=0, shadow=3, uppercase=True, spacing=6, words=6, max_chars=36, anim="fade", y=78)
    reg("editor-masala", "Editor Masala", "Chunky yellow with a magenta shadow.", mode="highlight", font="Bangers", size=110, color="#FFFFFF",
        active="#FFE600", outline=8, shadow=7, shadow_color="#FF2D95", uppercase=True, words=3, max_chars=18, anim="bounce")
    reg("aura", "Aura", "Italic serif, bold yellow key word.", mode="highlight", font="DM Serif Display", size=84, color="#FFFFFF",
        active="#FFE23A", dim="#FFFFFF", italic=True, outline=0, shadow=4, words=3, max_chars=22, anim="fade", y=60)
    reg("big-red", "The Big Red", "Large red serif caps with a small white line.", mode="flash", font="Abril Fatface", size=130, color="#E0242C",
        active="#E0242C", uppercase=True, outline=0, shadow=4, words=2, max_chars=14, anim="slide", y=30, safe=False)
    reg("scribble", "Scribble", "Yellow marker blob behind the spoken word.", mode="highlight", box="pill", font="Permanent Marker", size=72,
        color="#FFFFFF", active="#111111", box_color="#FFD21F", outline=0, shadow=0, words=3, max_chars=20, anim="pop", box_pad=18)
    reg("archives", "Archives", "Faded italic serif.", mode="flash", font="DM Serif Display", size=64, color="#E7DFD0", active="#E7DFD0",
        italic=True, outline=0, shadow=3, words=5, max_chars=30, anim="fade", y=74)
    reg("blockbuster", "Blockbuster", "Tall condensed titles.", mode="flash", font="Staatliches", size=120, color="#FFFFFF", active="#FFFFFF",
        outline=0, shadow=6, uppercase=True, spacing=3, words=3, max_chars=20, anim="fade")
    reg("journal", "Journal", "Handwritten feel.", mode="flash", font="Permanent Marker", size=62, color="#FFF4D0", active="#FFF4D0",
        outline=0, shadow=4, words=5, max_chars=28, anim="fade", y=74)
    beh("interlock", "Interlock", "Big white italic serif, small caps beneath.", "Instrument Serif", "#FFFFFF", size=290, y=60,
        upper=False, hero_italic=True, hero_shadow=0, small_y=72)
    reg("anchorage", "Anchorage", "Yellow label, uppercase.", mode="flash", box="card", font="Poppins ExtraBold", size=62, color="#101010",
        active="#101010", box_color="#FFDD00", outline=0, uppercase=True, words=3, max_chars=22, anim="pop", box_pad=16, y=68)

    reg("mr-beast-2", "Mr Beast Style 2", "Small yellow caps with a black edge.", mode="flash", font="Poppins ExtraBold", size=64,
        color="#FFE600", active="#FFE600", outline=6, shadow=0, uppercase=True, words=4, max_chars=26, anim="none", y=72)
    reg("clean-glow", "Clean Glow Style", "Clean white words with a soft glow.", mode="flash", font="Poppins SemiBold", size=58,
        color="#FFFFFF", active="#FFFFFF", outline=0, shadow=0, blur=5, words=5, max_chars=32, anim="fade", y=72)
    reg("plain-clean", "Plain Clean", "Plain white lines, calm.", mode="flash", font="Poppins SemiBold", size=56, color="#FFFFFF",
        active="#FFFFFF", outline=0, shadow=3, words=5, max_chars=30, anim="none", y=72)
    reg("word-focus", "Word Focus", "One or two white words at a time.", mode="reveal", font="Poppins Bold", size=70,
        color="#FFFFFF", active="#FFFFFF", outline=0, shadow=4, words=2, max_chars=18, anim="none", y=72)
    reg("tabahi", "Tabahi", "White caps in a black box.", mode="flash", box="card", font="Poppins ExtraBold", size=58,
        color="#FFFFFF", active="#FFFFFF", box_color="#000000", box_alpha=0, outline=0, uppercase=True, words=5, max_chars=30,
        anim="none", box_pad=14, y=72)
    reg("delhi", "Delhi", "Small white captions, no fuss.", mode="flash", font="Poppins Medium", size=54, color="#FFFFFF",
        active="#FFFFFF", outline=3, shadow=1, words=5, max_chars=32, anim="none", y=74)
    reg("illusion", "Illusion", "Light white captions, faded in.", mode="flash", font="Poppins Medium", size=52, color="#F4F4F4",
        active="#FFFFFF", outline=0, shadow=3, blur=1, words=6, max_chars=36, anim="fade", y=74)
    reg("swiss", "Swiss", "Helvetica-style caps stacked, yellow spoken word.", mode="highlight", font="Poppins Bold", size=70,
        color="#FFFFFF", active="#FFD400", dim="#FFFFFF", outline=0, shadow=3, uppercase=True, words=2, max_chars=14,
        anim="none", y=58)

    # ---------------- the 16 Popular looks, redrawn from popular reference styles (sizes in px of a 1080x1920 frame) -------
    TEAL = "#0AB1CD"
    _CAP = dict(mode="reveal", font="Inter Bold", size=97, color="#FFFFFF", active="#FFFFFF", outline=1, outline_color="#FFFFFF",
                blur=3, shadow=0, words=4, max_chars=80, anim="none", y=74.5, x=15, align="left", emph=True, emph_max=2, strip_punct=False,
                hero_font="Inter Black", hero_size=222, hero_color=TEAL, hero_upper=True, hero_y=77.53, hero_outline=0,
                hero_shadow=0, emph_gap=0.88)
    reg("glow-key", "Glow Key", "Small words, the key words big in teal with a soft glow beneath.", **{**_CAP, "emph_glow": 14})
    reg("shadow-key", "Shadow Key", "Small words, the key words big and lowercase in teal with a shadow.", **{
        **_CAP, "hero_upper": False, "hero_shadow": 6, "hero_shadow_color": "#06303A"})
    reg("classic-key", "Classic Key", "Small words, the key words big in teal.", **{**_CAP, "outline": 0, "blur": 0, "shadow": 3})
    reg("ali", "Ali Abdaal", "A white pill; words said turn dark, the rest wait in a faint grey.", mode="highlight", box="capsule", font="Poppins ExtraBold",
        size=70, color="#D3D3D4", dim="#D3D3D4", active="#000000", keep_spoken=True, box_color="#FFFFFF", box_pad=22, outline=0, shadow=0,
        words=4, max_chars=34, anim="none", y=85)
    reg("clean", "Clean Motion", "Small light words that fade up one by one.", mode="reveal", font="Inter", size=70, color="#FFFFFF",
        active="#FFFFFF", outline=0, shadow=3, spacing=1, words=4, max_chars=34, anim="rise", y=85)
    reg("bubble", "Bubble Style", "A green pill follows the word being said.", mode="highlight", box="bubble", font="Montserrat Bold", size=50,
        color="#FFFFFF", dim="#FFFFFF", active="#000000", box_color="#48A680", outline=0, shadow=0, words=4, max_chars=34, anim="none",
        gap_em=1.0, pill_padx=0.45, pill_h=1.44, strip_punct=False, y=85)
    reg("hormozi", "Hormozi Style", "Lime Anton capitals with an olive drop shadow.", mode="highlight", font="Anton", size=104,
        uppercase=True, color="#9FF747", dim="#9FF747", active="#9FF747", outline=0, shadow=14, shadow_color="#474F2E", blur=3, words=4, max_chars=24,
        anim="none", active_scale=100, y=85)
    reg("boxed", "Editing Skool", "Orange box, white Inter capitals; it fades in.", mode="flash", box="block", font="Inter Bold", size=100, spacing=4,
        uppercase=True, color="#FFFFFF", active="#FFFFFF", box_color="#F48601", box_pad=28, outline=0, shadow=0, words=5, max_chars=26, anim="none",
        fade_in=0.1, fade_out=0.1, y=85, x=14.7, align="left")
    reg("mrbeast", "Mr Beast Style 1", "White comic capitals with a thick black edge.", mode="highlight", font="Luckiest Guy", size=46, uppercase=True,
        color="#FFFFFF", dim="#FFFFFF", active="#FFFFFF", outline=9, outline_color="#000000", shadow=0, spacing=2, words=4, max_chars=26, anim="none", y=85)
    reg("mr-beast-2", "Mr Beast Style 2", "Gold capitals, a hard shadow falling below.", mode="highlight", font="Montserrat ExtraBold", size=60,
        uppercase=True, color="#FFD700", dim="#FFD700", active="#FFD700", outline=2, outline_color="#000000", shadow=9, shadow_color="#000000",
        words=4, max_chars=26, anim="none", y=85)
    reg("iman", "Iman Gadzhi", "Bold white capitals, widely spaced.", mode="highlight", font="Poppins SemiBold", size=56, uppercase=True, color="#FFFFFF",
        dim="#FFFFFF", active="#FFFFFF", spacing=6, outline=0, shadow=3, shadow_color="#000000", words=4, max_chars=30, anim="none", y=85)
    reg("prism", "Devin Jatho", "Violet Montserrat capitals, widely spaced.", mode="highlight", font="Montserrat Bold", size=54,
        uppercase=True, color="#A34EFF", dim="#A34EFF", active="#A34EFF", spacing=3, outline=0, shadow=0, blur=0, words=4, max_chars=30, anim="none", y=85)
    reg("highlighted", "Highlighted Word", "White Montserrat words; the one said turns orange.", mode="highlight", font="Montserrat Bold", size=86,
        color="#FFFFFF", dim="#FFFFFF", active="#F5A623", outline=0, shadow=3, words=4, max_chars=30, anim="none", y=85)
    reg("clean-glow", "Clean Glow Style", "Clean white Inter words with a soft white glow.", mode="flash", font="Inter", size=90, color="#FFFFFF",
        active="#FFFFFF", outline=3, outline_color="#FFFFFF", blur=7, shadow=0, words=4, max_chars=30, anim="none", y=85)
    reg("plain-clean", "Plain Clean", "Plain white Inter words with a light shadow.", mode="flash", font="Inter", size=88, color="#FFFFFF",
        active="#FFFFFF", outline=0, shadow=2, shadow_color="#000000", blur=1, words=4, max_chars=30, anim="none", y=85)
    reg("black-punch", "Black Punch", "Black Anton capitals with a thick white stroke.", mode="flash", font="Anton", size=82, uppercase=True,
        color="#000000", active="#000000", outline=7, outline_color="#FFFFFF", shadow=0, words=4, max_chars=26, anim="none", y=85)
