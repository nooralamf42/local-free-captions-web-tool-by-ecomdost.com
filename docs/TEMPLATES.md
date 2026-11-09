# Templates

The editor's **Templates** tab holds 100+ templates, grouped as Popular, Behind you, Bold & animated, Clean, Property reels, Around you and More.
Hover a card to see it animate.

> Template names describe a look (Aura, Delhi, Sash, Glow Key ...). This project is not affiliated with any caption product. Fonts are open-source
> (see [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)).

## What you can customise (Customize tab)

Position (drag on the phone map), caption size, words per screen, lines per caption, letter case, colours (text, highlight, said and unsaid words, outline, box),
font, outline, shadow, how words come in (pop / bounce / fade / slide, letter-by-letter typing), caption fade in and out, and for "Behind you" looks the big word's
size, height, colour, font, tilt, softness and entrance motion (rise, drop, zoom, blur, wipe, type, stretch, skid, flip, stamp, flicker, pop).

## How a template is defined

A template is a dictionary of settings in `engine/templates.py` (base defaults in `engine/styles.py`). The renderer (`engine/ass.py`) turns the settings and the
word timings into an ASS subtitle file, which ffmpeg's `ass` filter burns into the video. Typical settings: `font`, `size`, `color`, `active` (colour of the spoken word),
`mode` (`highlight`, `reveal`, `flash`, `sweep`), `anim`, `words`, `outline`, `shadow`, `box`, and for big-word looks `hero_font`, `hero_size`, `hero_motion`.

Some templates have a layout of their own in `engine/dynamic.py` (stacked key-word layouts, marker highlights, hand-drawn underlines). Entrance motions are in `engine/motion.py`.
`engine/preset_*.json` hold per-template fonts, sizes and colours that are applied on top of the base settings.

## Adding a template

1. Open `engine/templates.py` and copy a similar `reg(...)` call (caption in front of the speaker) or `beh(...)` call (big word behind the speaker).
2. Give it a new id and label, then change fonts, colours and sizes.
3. If you need a font, drop the `.ttf` into `fonts/` (open-source licence only) and list it in `fonts/README.md`.
4. Add the id to a group in `engine/styles.py` (`TEMPLATE_GROUPS`) so it shows up in a tab.
5. Preview without a video: `python tools/our_clip.py <id> test.mp4`, then open `test.mp4`.
6. Run `python tests/test_smoke.py`.
