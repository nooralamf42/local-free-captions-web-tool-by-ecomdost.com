"""Second pass over a transcript with an LLM (any OpenAI-compatible API; provider, model and key are set in Settings -> AI polish): spoken numbers become digits, Hinglish is
written in natural Roman spelling, English words get their English spelling, names/brands are fixed. Word timings are kept: the model returns
one string per original word (same count); a word merged into the one before it comes back as "" and its time goes to that word."""
import json
import re
import time
import urllib.error
import urllib.request

from . import settings

CHUNK = 45

SYSTEM = (
    "You fix a speech-to-text transcript of a Hindi-English (Hinglish) video. The speaker mixes Hindi and English words. You get a JSON "
    "array of words in order. Return JSON {\"words\": [...]} with EXACTLY the same number of items.\n"
    "Rules:\n"
    "1. Hindi words stay in Roman letters, spelled the way people type Hinglish in chats: ye, wo, yahan, wahan, pehle, ke liye, kya, hai, "
    "nahi, bahut, jayega (not yah, vah, lie, pahle, jaega). Do not translate anything.\n"
    "2. English words, tech terms and brand names use normal English spelling: prompt, generate, image, ChatGPT, Google Flow, UGC, Meesho, "
    "Instagram, reel.\n"
    "3. Spoken NUMBERS and QUANTITIES become digits: thirty -> 30, bis/bees -> 20, do sau -> 200, ek lakh -> 1 lakh, pachaas -> 50, "
    "teen steps -> 3 steps. But 'ek' used as the article 'a / one kind of' (ek baat, ek new chat, ek accha product) stays 'ek'.\n"
    "4. When several input words form one thing (e.g. 'do' 'sau' -> '200'), put the whole result on the FIRST word and \"\" on the others.\n"
    "5. Do not move, add or delete the punctuation that is already attached to the input words.\n"
    "6. Capitalise only the first word right after a full stop / question mark, and proper nouns (ChatGPT, Google Flow, Meesho). Every other "
    "word is lowercase.\n"
    "7. If a word is clearly a mis-hearing given the sentence (e.g. 'nan Press karne ke baad' after talking about a prompt -> 'prompt paste karne "
    "ke baad'), replace it with the intended word, keeping one output item per input item. If unsure leave it.\n"
    "8. yahaan/vahaan -> yahan/wahan, hamaare -> hamare, chaahie -> chahiye, jaega -> jayega.\n"
    "Return only the JSON."
)


def available():
    return settings.ai_config() is not None


def _parse(txt):
    try:
        return json.loads(txt)["words"]
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)   # some models wrap the JSON in prose or code fences
        return json.loads(m.group(0))["words"]


def _call(cfg, words, ctx_before, model=None, json_mode=True):
    model = model or cfg["model"]
    msg = [{"role": "system", "content": SYSTEM},
           {"role": "user", "content": json.dumps({"previous_words": ctx_before, "words": words}, ensure_ascii=False)}]
    payload = {"model": model, "messages": msg, "temperature": 0}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload).encode()
    for attempt in range(3):
        req = urllib.request.Request(cfg["url"], data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["key"],
                                                                      "User-Agent": "captions-studio/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            return _parse(out["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as e:
            if e.code == 400 and json_mode:   # a provider without JSON mode: ask again without it
                return _call(cfg, words, ctx_before, model, json_mode=False)
            if e.code in (401, 403, 404) or attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def refine_words(words, log=None):
    """words: [{'w','s','e'}] -> same-length list of corrected strings, '' = merged into the previous word. Chunks that fail stay as they are."""
    log = log or (lambda *_: None)
    cfg = settings.ai_config()
    if cfg is None:
        return [w["w"] for w in words]
    texts = [w["w"] for w in words]
    out = list(texts)
    for a in range(0, len(texts), CHUNK):
        part = texts[a:a + CHUNK]
        try:
            try:
                got = _call(cfg, part, texts[max(0, a - 8):a])
            except Exception:
                if not cfg.get("fallback"):
                    raise
                got = _call(cfg, part, texts[max(0, a - 8):a], cfg["fallback"])
            if not isinstance(got, list) or len(got) != len(part) or not all(isinstance(x, str) for x in got):
                got = _call(cfg, part, texts[max(0, a - 8):a])
            if isinstance(got, list) and len(got) == len(part) and all(isinstance(x, str) for x in got):
                # a sanity net: never let the model empty everything
                if sum(1 for x in got if x.strip()) >= max(1, int(len(part) * 0.5)):
                    out[a:a + len(part)] = [x.strip() for x in got]
                    continue
            log("AI fix: kept the original for words %d-%d (answer did not line up)" % (a, a + len(part)))
        except Exception as e:
            log("AI fix unavailable (%s) - kept the original" % str(e)[:120])
            return texts
    return out


def refine_segments(segs, log=None):
    """Apply refine_words to a transcript's segments in place (timings kept, merged words folded into their neighbour)."""
    words = [w for s in segs for w in s["words"]]
    if not words:
        return 0
    new = refine_words(words, log)
    changed = 0
    # flat order == segment order
    k = 0
    for s in segs:
        out = []
        for w in s["words"]:
            t = new[k]
            k += 1
            if t == "" and out:
                out[-1]["e"] = max(out[-1]["e"], w["e"])
                changed += 1
                continue
            if t and t != w["w"]:
                changed += 1
                w["w"] = t
            out.append(w)
        s["words"] = out
        s["text"] = " ".join(w["w"] for w in out)
    return changed


def test(cfg):
    """Settings -> 'Test the key': one tiny request. Returns (ok, message)."""
    try:
        got = _call(cfg, ["bis", "commands", "chahiye"], [])
        if isinstance(got, list) and len(got) == 3:
            return True, "Works. Sample: %s" % " ".join(str(x) for x in got)
        return False, "The model answered, but not in the expected format: %s" % str(got)[:120]
    except urllib.error.HTTPError as e:
        hint = {401: "the key was rejected", 403: "the key is not allowed to use this model", 404: "the model name or URL is wrong", 429: "rate limit reached"}.get(e.code, "")
        return False, "HTTP %d%s" % (e.code, (" - " + hint) if hint else "")
    except Exception as e:
        return False, str(e)[:200]
