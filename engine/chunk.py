"""Group Whisper words into on-screen phrases and tidy word timings."""
import re

END_PUNCT = re.compile(r"[.!?।…]+[\"')\]]*$")
SOFT_PUNCT = re.compile(r"[,;:—–-]+[\"')\]]*$")
# short function words that read badly at the end of a caption line (English + common Hinglish)
WEAK = re.compile(r"^(a|an|the|to|of|in|on|at|for|and|or|but|is|are|was|if|so|as|with|that|your|my|our|"
                  r"ka|ki|ke|ko|se|me|mein|par|aur|ya|ek|hai|ho|toh|to|ye|yeh|wo|woh|jo|ki)$")


def flatten(transcript):
    """transcript: {'segments':[{'words':[{'w','s','e'}]}]} -> list of words with seg index + seg_end flag."""
    out = []
    for si, seg in enumerate(transcript.get("segments", [])):
        ws = seg.get("words", [])
        for wi, w in enumerate(ws):
            d = dict(w)
            d["seg"] = si
            d["seg_end"] = wi == len(ws) - 1
            d["behind"] = seg.get("behind", True)
            out.append(d)
    return out


def tidy(words, max_gap_fill=0.3, min_dur=0.08):
    """Fix overlaps/zero-length words and close tiny gaps so highlight doesn't flicker."""
    for i, w in enumerate(words):
        if w["e"] - w["s"] < min_dur:
            w["e"] = w["s"] + min_dur
        if i + 1 < len(words):
            nx = words[i + 1]
            if w["e"] > nx["s"]:
                w["e"] = max(w["s"] + 0.04, nx["s"])
                if w["e"] > nx["s"]:
                    nx["s"] = w["e"]
            elif nx["s"] - w["e"] <= max_gap_fill:
                w["e"] = nx["s"]
    return words


def make_phrases(words, max_words=3, max_chars=22, split_gap=0.55, hold=0.22):
    """Return list of phrases: {'words':[...], 'start', 'end'}.

    Break on: sentence punctuation, speech pause, segment end, word/char limits.
    """
    words = tidy([dict(w) for w in words])
    phrases, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            phrases.append({"words": cur, "start": cur[0]["s"], "end": cur[-1]["e"]})
            cur = []

    for i, w in enumerate(words):
        if cur:
            chars = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            gap = w["s"] - cur[-1]["e"]
            if len(cur) >= max_words or chars > max_chars or gap > split_gap:
                # don't leave a dangling 'a / to / the / and' at the end of a phrase
                if len(cur) > 1 and gap <= split_gap and WEAK.search(cur[-1]["w"].lower()):
                    carry = cur.pop()
                    flush()
                    cur = [carry]
                else:
                    flush()
        cur.append(w)
        t = w["w"]
        nxt = words[i + 1] if i + 1 < len(words) else None
        if END_PUNCT.search(t) or w.get("seg_end"):
            flush()
        elif SOFT_PUNCT.search(t) and len(cur) >= 2:
            flush()
        elif nxt and len(cur) == max_words - 1 and max_words >= 3 and len(nxt["w"]) <= 2 and not SOFT_PUNCT.search(t):
            pass
    flush()
    # avoid one-word orphans at end of a sentence when max_words>=3: merge into previous if it fits
    if max_words >= 3:
        merged = []
        for p in phrases:
            if (merged and len(p["words"]) == 1 and len(merged[-1]["words"]) < max_words
                    and p["start"] - merged[-1]["end"] < 0.25
                    and not END_PUNCT.search(merged[-1]["words"][-1]["w"])
                    and sum(len(x["w"]) + 1 for x in merged[-1]["words"]) + len(p["words"][0]["w"]) <= max_chars):
                merged[-1]["words"] += p["words"]
                merged[-1]["end"] = p["end"]
            else:
                merged.append(p)
        phrases = merged
    # display end: hold a little after last word but never overlap next phrase
    for i, p in enumerate(phrases):
        end = p["end"] + hold
        if i + 1 < len(phrases):
            end = min(end, phrases[i + 1]["start"] - 0.01)
        p["disp_end"] = max(end, p["end"])
    return phrases


