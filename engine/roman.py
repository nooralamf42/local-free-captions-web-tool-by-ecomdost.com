"""Devanagari -> Hinglish (Roman letters) with Hindi schwa deletion.

Used for 'Hinglish' mode when Whisper returns Devanagari. Latin words pass through untouched.
Spelling follows how people actually type Hinglish (hai, kya, mein, accha), not strict ISO transliteration.
"""
import re

CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "ळ": "l", "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh", "फ़": "f",
}
NUKTA = {"क": "क़", "ख": "ख़", "ग": "ग़", "ज": "ज़", "ड": "ड़", "ढ": "ढ़", "फ": "फ़"}
INDEP = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
         "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o", "ऍ": "e"}
MATRA = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri", "े": "e", "ै": "ai",
         "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "e"}
VIRAMA = "्"
NUKTA_CH = "़"
ANUSVARA = "ं"
CHANDRA = "ँ"
VISARGA = "ः"
DIGITS = {c: str(i) for i, c in enumerate("०१२३४५६७८९")}

# common words where the phonetic rule gives an unnatural spelling
WORDS = {
    "है": "hai", "हैं": "hain", "में": "mein", "मैं": "main", "और": "aur", "का": "ka", "की": "ki", "के": "ke",
    "को": "ko", "से": "se", "यह": "yeh", "ये": "ye", "वह": "woh", "वो": "wo", "क्या": "kya", "तो": "to",
    "भी": "bhi", "नहीं": "nahi", "नही": "nahi", "कि": "ki", "जो": "jo", "पर": "par", "या": "ya", "हो": "ho",
    "था": "tha", "थी": "thi", "थे": "the", "हूँ": "hoon", "हूं": "hoon", "कैसे": "kaise", "क्यों": "kyun",
    "आप": "aap", "हम": "hum", "तुम": "tum", "मेरा": "mera", "मेरी": "meri", "मेरे": "mere", "अपना": "apna",
    "अपनी": "apni", "अपने": "apne", "ज़रूर": "zaroor", "जरूर": "zaroor", "ताकि": "taaki", "फिर": "phir",
    "एक": "ek", "अच्छा": "accha", "अच्छी": "acchi", "अच्छे": "acche", "बहुत": "bahut", "कुछ": "kuch",
    "लोग": "log", "बिना": "bina", "दोस्तों": "doston", "नमस्ते": "namaste", "आज": "aaj", "बताऊंगा": "bataunga",
    "बताऊँगा": "bataunga", "ज्यादा": "zyada", "ज़्यादा": "zyada", "देख": "dekh", "सकें": "sakein", "सकते": "sakte",
    "सकता": "sakta", "करो": "karo", "करें": "karein", "करना": "karna", "करते": "karte", "करता": "karta",
    "रहे": "rahe", "रहा": "raha", "रही": "rahi", "लिए": "liye", "इसके": "iske", "उसका": "uska", "उसकी": "uski",
    "जिसकी": "jiski", "बाद": "baad", "सबसे": "sabse", "पहले": "pehle", "आवाज़": "awaaz", "आवाज": "awaaz",
}


# English words Hindi speakers write in Devanagari -> proper English spelling (the usual Hinglish convention)
LOAN = {
    "प्रोडक्ट": "product", "प्रोडक्ट्स": "products", "प्रोडक्शन": "production", "ऑनलाइन": "online", "आउनलाइन": "online",
    "ओनलाइन": "online", "अकाउंट": "account", "अकाउन्ट": "account", "डिमांड": "demand", "रील": "reel", "रील्स": "reels",
    "रिल": "reel", "रिल्स": "reels", "वीडियो": "video", "विडियो": "video", "विडीयो": "video", "वीडियोज": "videos",
    "वीडियोज़": "videos", "कैप्शन": "caption", "कैप्शंस": "captions", "कैप्शन्स": "captions", "मीशो": "Meesho",
    "मिशो": "Meesho", "फ्लिपकार्ट": "Flipkart", "अमेज़न": "Amazon", "अमेजन": "Amazon", "इंस्टाग्राम": "Instagram",
    "फॉलोवर": "follower", "फॉलोवर्स": "followers", "फॉलोअर": "follower", "फॉलोअर्स": "followers", "सेलर": "seller",
    "सेलर्स": "sellers", "सेलिंग": "selling", "सेल": "sale", "ऑर्डर": "order", "ऑर्डर्स": "orders", "आर्डर": "order",
    "डिलीवरी": "delivery", "डिलिवरी": "delivery", "पेमेंट": "payment", "रिटर्न": "return", "रिटर्न्स": "returns",
    "कस्टमर": "customer", "कस्टमर्स": "customers", "बिज़नेस": "business", "बिजनेस": "business", "ऑफर": "offer",
    "ऑफ़र": "offer", "डिस्काउंट": "discount", "प्राइस": "price", "मार्केटिंग": "marketing", "ब्रांड": "brand",
    "ब्रैंड": "brand", "क्वालिटी": "quality", "कैटलॉग": "catalog", "कैटलॉग्स": "catalogs", "लिस्टिंग": "listing",
    "पैकेजिंग": "packaging", "शिपिंग": "shipping", "रेटिंग": "rating", "रिव्यू": "review", "रिव्यूज": "reviews",
    "लाइक": "like", "शेयर": "share", "कमेंट": "comment", "सब्सक्राइब": "subscribe", "चैनल": "channel",
    "ट्रेंड": "trend", "वायरल": "viral", "कंटेंट": "content", "क्रिएटर": "creator", "क्रिएटर्स": "creators",
    "मोबाइल": "mobile", "फोन": "phone", "ऐप": "app", "एप": "app", "एप्लीकेशन": "application", "वेबसाइट": "website",
    "लिंक": "link", "ऑफिस": "office", "स्टार्ट": "start", "फ्री": "free", "प्रीमियम": "premium",
    "ट्यूटोरियल": "tutorial", "टिप्स": "tips", "ट्रिक": "trick", "स्टेप": "step", "स्टेप्स": "steps", "प्लान": "plan",
    "मैसेज": "message", "व्हाट्सएप": "WhatsApp", "व्हाट्सऐप": "WhatsApp", "वॉट्सऐप": "WhatsApp", "गूगल": "Google",
    "यूट्यूब": "YouTube", "फेसबुक": "Facebook", "ओके": "okay", "सॉरी": "sorry", "प्लीज": "please", "थैंक्यू": "thank you",
    "हेलो": "hello", "टाइम": "time", "मिनट": "minute", "सेकंड": "second", "आईडिया": "idea", "प्रॉफिट": "profit",
    "लॉस": "loss", "इन्वेस्ट": "invest", "रिजल्ट": "result", "सिस्टम": "system", "पासवर्ड": "password",
    "लॉगिन": "login", "ईमेल": "email", "ऑप्शन": "option", "सेटिंग": "setting", "सेटिंग्स": "settings",
    "डाउनलोड": "download", "अपलोड": "upload", "एडिट": "edit", "फिल्टर": "filter", "सर्च": "search", "टॉप": "top",
    "बेस्ट": "best", "नंबर": "number", "सर्विस": "service", "सपोर्ट": "support", "मैनेजर": "manager", "कैश": "cash",
    "कैशबैक": "cashback", "कूपन": "coupon", "स्टॉक": "stock", "स्टोर": "store", "शॉप": "shop", "शॉपिंग": "shopping",
    "बैंक": "bank", "कार्ड": "card", "डेटा": "data", "रिपोर्ट": "report", "एनालिटिक्स": "analytics", "ग्रोथ": "growth",
    "टारगेट": "target", "गोल": "goal", "मोटिवेशन": "motivation", "रीच": "reach", "एंगेजमेंट": "engagement",
    "हैशटैग": "hashtag", "एल्गोरिदम": "algorithm", "एक्सटेंशन": "extension", "क्रोम": "Chrome", "ब्राउज़र": "browser",
    "ब्राउजर": "browser", "सेलेक्ट": "select", "क्लिक": "click", "डिज़ाइन": "design", "डिजाइन": "design",
    "फोटो": "photo", "इमेज": "image", "टेम्पलेट": "template", "सॉफ्टवेयर": "software", "टूल": "tool", "टूल्स": "tools",
    "स्टाइल": "style", "सब्सक्रिप्शन": "subscription", "डैशबोर्ड": "dashboard", "ट्रैकिंग": "tracking",
    "ट्रैक": "track", "लॉन्च": "launch", "सक्सेस": "success", "रिस्क": "risk", "कॉल": "call", "मीटिंग": "meeting",
}


LOAN.update({
    "कॉम्प्टेटर": "competitor", "कॉम्पटीटर": "competitor", "कंपेटिटर": "competitor", "कॉम्पिटिटर": "competitor",
    "कॉम्पिटीशन": "competition", "कॉम्पटीशन": "competition", "कंपटीशन": "competition", "कॉम्पटिशन": "competition",
    "सप्लायर": "supplier", "सप्लाइयर": "supplier", "सप्लायर्स": "suppliers", "पैनल": "panel", "पेनल": "panel",
    "डेस्कटॉप": "desktop", "डेस्कटाप": "desktop", "डीटेल": "detail", "डिटेल": "detail", "डीटेल्स": "details",
    "डिटेल्स": "details", "इनसाइट": "insight", "इन्साइट": "insight", "यूसफुल": "useful", "यूजफुल": "useful",
    "अल्रेडी": "already", "ऑलरेडी": "already", "ऑलरेडी": "already", "सेम": "same", "रैंडम": "random", "रेंडम": "random",
    "पिक": "pick", "प्रोडक": "product", "प्रोड़क": "product", "प्रोड़क्ट": "product", "प्रोडक्ट्स": "products",
    "ऑर्डर": "order", "ओर्डर": "order", "ओर्डर्स": "orders", "आर्डर्स": "orders", "डेटा": "data", "डाटा": "data",
    "लॉगिन": "login", "लॉग": "log", "इन": "in", "सेफ": "save", "सेव": "save", "रील": "reel", "ओपन": "open",
    "सर्च": "search", "सेलेक्ट": "select", "सेल": "sale", "लिस्ट": "list", "लिस्टेड": "listed", "फ्री": "free",
    "बैंगल": "bangle", "बैंगल्स": "bangles", "चेक": "check", "प्राइस": "price", "रैंक": "rank", "रैंकिंग": "ranking",
    "रांग": "ranking", "वर्क": "work", "डेस्क": "desk", "नंबर": "number", "फोन": "phone", "सुपर": "super",
    "डिस्काउंट": "discount", "गेम": "game", "क्लिक": "click", "डिलीट": "delete", "अपडेट": "update",
})


def _norm(w):
    return (w.replace(NUKTA_CH, "").replace(CHANDRA, ANUSVARA).replace("ऑ", "ओ").replace("ड़", "ड").replace("ढ़", "ढ")
            .replace("ॉ", "ो"))


_LOAN_N = {_norm(k): v for k, v in LOAN.items()}
_LOAN_KEYS = [k for k in _LOAN_N if len(k) >= 4]
_WORDS_N = {_norm(k): v for k, v in WORDS.items()}
_glossary = None


def _load_glossary():
    global _glossary
    if _glossary is None:
        _glossary = {}
        try:
            import json
            from .util import ROOT
            p = ROOT / "glossary.json"
            if p.exists():
                _glossary = {k.lower(): v for k, v in json.loads(p.read_text(encoding="utf-8")).items()}
        except Exception:
            pass
    return _glossary


def _rom_word(w):
    """Romanize one Devanagari token (no spaces)."""
    g = _load_glossary()
    if w in g:
        return g[w]
    n = _norm(w)
    if n in _LOAN_N:
        return _LOAN_N[n]
    if len(n) >= 5:  # close spelling variants of known English loan-words (Whisper spells them differently each time)
        import difflib
        m = difflib.get_close_matches(n, _LOAN_KEYS, n=1, cutoff=0.86)
        if m:
            return _LOAN_N[m[0]]
    if w in WORDS:
        return WORDS[w]
    if n in _WORDS_N:
        return _WORDS_N[n]
    # build syllables: list of [consonant_roman, vowel_roman_or_None(inherent), has_matra]
    syl = []
    i, n = 0, len(w)
    pending_cons = ""  # accumulates conjunct consonants (with virama)
    while i < n:
        c = w[i]
        if i + 1 < n and w[i + 1] == NUKTA_CH and c in NUKTA:
            c = NUKTA[c]
            i += 1
        if c in CONS:
            r = CONS[c]
            i += 1
            if i < n and w[i] == VIRAMA:
                pending_cons += r
                i += 1
                continue
            r = pending_cons + r
            pending_cons = ""
            vowel, inherent = "a", True
            if i < n and w[i] in MATRA:
                vowel, inherent = MATRA[w[i]], False
                i += 1
            syl.append([r, vowel, inherent])
        elif c in INDEP:
            syl.append(["", INDEP[c], False])
            i += 1
        elif c in MATRA:  # stray vowel sign (Whisper glitch like 'एे'): drop it
            i += 1
        elif c in (ANUSVARA, CHANDRA):
            if syl:
                syl[-1].append("n")
            i += 1
        elif c == VISARGA:
            if syl:
                syl[-1].append("h")
            i += 1
        elif c in DIGITS:
            syl.append(["", DIGITS[c], False])
            i += 1
        elif c == VIRAMA or c == NUKTA_CH:
            i += 1
        else:
            syl.append([c, "", False])
            i += 1
    if pending_cons:
        syl.append([pending_cons, "", False])
    # schwa deletion: final always; medial if neighbour kept (right to left)
    last = len(syl) - 1
    deleted = [False] * len(syl)
    for k in range(last, -1, -1):
        s = syl[k]
        if not s[2] or s[1] != "a":
            continue
        if k == last and len(syl) > 1:
            deleted[k] = True
        elif 0 < k < last and not deleted[k + 1]:
            deleted[k] = True  # V C a C V: next syllable keeps its vowel -> drop this schwa
    out = []
    for k, s in enumerate(syl):
        r, v = s[0], s[1]
        if s[2] and deleted[k]:
            v = ""
        elif v == "aa" and k == last and not s[2] and len(syl) > 1:
            v = "a"  # word-final aa -> a (mera, kya, accha)
        elif v == "ee" and k == last and len(syl) > 1:
            v = "i"
        elif v == "oo" and k == last and len(syl) > 1:
            v = "u"
        out.append(r + v + "".join(s[3:]))
    res = "".join(out)
    res = re.sub(r"(.)\1\1+", r"\1\1", res)
    # banaae -> banaye, daalie -> daaliye, dikhaaie -> dikhaiye (how Hinglish is actually typed)
    res = re.sub(r"aaie$", "aiye", res)
    res = re.sub(r"aae$", "aye", res)
    res = re.sub(r"ie$", "iye", res)
    return res


_DEV = re.compile(r"[ऀ-ॣ०-ॿ]+")


def romanize(text):
    """Replace every Devanagari run in text with Hinglish; keep punctuation and Latin words."""
    return _DEV.sub(lambda m: _rom_word(m.group(0)), text).replace("।", ".")


def has_devanagari(text):
    return bool(_DEV.search(text))

