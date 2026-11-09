"""Apply transcript text edits while keeping word timings."""
import difflib


def retime(old_words, new_text):
    """old_words: [{'w','s','e'}]; new_text: str. Unchanged words keep timing; new ones are interpolated."""
    new = new_text.split()
    if not old_words:
        return []
    if not new:
        return []
    ow = [w["w"].lower().strip(".,!?;:।") for w in old_words]
    nw = [w.lower().strip(".,!?;:।") for w in new]
    sm = difflib.SequenceMatcher(a=ow, b=nw, autojunk=False)
    out = [None] * len(new)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                o = old_words[i1 + k]
                out[j1 + k] = {"w": new[j1 + k], "s": o["s"], "e": o["e"]}
        elif tag in ("replace", "insert"):
            # time span available: from end of previous known word to start of next known word (or old span)
            if tag == "replace":
                s0, e0 = old_words[i1]["s"], old_words[i2 - 1]["e"]
            else:
                s0 = old_words[i1 - 1]["e"] if i1 > 0 else old_words[0]["s"]
                e0 = old_words[i1]["s"] if i1 < len(old_words) else old_words[-1]["e"]
                if e0 - s0 < 0.08 * (j2 - j1):
                    e0 = s0 + 0.18 * (j2 - j1)
            n = j2 - j1
            lens = [max(1, len(new[j])) for j in range(j1, j2)]
            tot = float(sum(lens))
            t = s0
            for k, j in enumerate(range(j1, j2)):
                d = (e0 - s0) * lens[k] / tot
                out[j] = {"w": new[j], "s": t, "e": t + d}
                t += d
    return [w for w in out if w]


def apply_edits(transcript, texts):
    """texts: list of str (one per segment, same order). Returns new transcript."""
    segs = []
    for seg, txt in zip(transcript["segments"], texts):
        if txt is None or txt.strip() == seg["text"].strip():
            segs.append(seg)
            continue
        words = retime(seg["words"], txt)
        if words:
            segs.append({"start": words[0]["s"], "end": words[-1]["e"], "text": txt.strip(), "words": words})
    out = dict(transcript)
    out["segments"] = segs
    return out
