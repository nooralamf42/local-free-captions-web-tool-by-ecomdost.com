"""Speech -> word-timestamped transcript using faster-whisper (CUDA int8_float16, CPU int8 fallback).

Robustness notes (learned the hard way on real Reels):
* Whisper decodes in 30 s windows and sometimes silently stops mid-window, dropping 10+ s of speech.
  So we cut the audio at silences with Silero VAD into <=14 s chunks and decode each chunk on its own,
  then verify every speech chunk got words and re-decode the ones that did not.
* In 'translate' mode Whisper's *word* timestamps are unreliable (English tokens vs Hindi audio), so we use the
  segment timestamps and spread the English words across each segment.
"""
import time

import numpy as np

from . import models
from .roman import has_devanagari, romanize
from .util import MODELS, probe, setup_cuda_paths

import re

_BRAND = re.compile(r"^(m[ie]{1,2}s?h[ou]|mesho|mishoo)((?:\.com)?\W*)$", re.I)
SR = 16000
MAX_CHUNK = 14.0
_models = {}
_state = {"device": None, "compute": None}


def _load(name, device):
    from faster_whisper import WhisperModel
    key = (name, device)
    if key in _models:
        return _models[key]
    MODELS.mkdir(exist_ok=True)
    if device == "cuda":
        m = WhisperModel(name, device="cuda", compute_type="int8_float16", download_root=str(MODELS))
        _state.update(device="cuda", compute="int8_float16")
    else:
        m = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=8, download_root=str(MODELS))
        _state.update(device="cpu", compute="int8")
    _models.clear()  # keep only one model in memory (VRAM is tight)
    _models[key] = m
    return m


def unload():
    """free VRAM (the person cut-out needs the GPU too)"""
    _models.clear()
    import gc
    gc.collect()


def cuda_ok():
    setup_cuda_paths()
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def speech_chunks(audio, max_len=MAX_CHUNK):
    """Silero-VAD speech spans in seconds, merged into chunks <= max_len that break at silences."""
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    ts = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=250, speech_pad_ms=120,
                                                 min_speech_duration_ms=150, max_speech_duration_s=max_len))
    spans = [[t["start"] / SR, t["end"] / SR] for t in ts]
    merged = []
    for s, e in spans:
        if merged and s - merged[-1][1] < 0.6 and e - merged[-1][0] <= max_len:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return merged


def _decode(model, audio, clips, language, task, words, progress, duration, prompt=None):
    flat = [x for c in clips for x in c]
    segs, info = model.transcribe(
        audio, language=language, task=task, word_timestamps=words, beam_size=5,
        vad_filter=False, clip_timestamps=flat, condition_on_previous_text=False, initial_prompt=prompt,
        temperature=(0.0, 0.2, 0.4), no_speech_threshold=None, compression_ratio_threshold=2.4)
    out = []
    for s in segs:  # generator: real work happens here
        if words:
            ws = [{"w": w.word.strip(), "s": float(w.start), "e": float(w.end)} for w in (s.words or []) if w.word.strip()]
        else:
            ws = _spread(s.text, float(s.start), float(s.end))
        if ws:
            out.append({"start": float(s.start), "end": float(s.end), "text": s.text.strip(), "words": ws})
        if progress and duration:
            progress(min(0.99, s.end / duration))
    return out, info


def _spread(text, start, end):
    """Evenly (length-weighted) time the words of a segment across [start, end]."""
    toks = text.split()
    if not toks:
        return []
    wt = [len(t) + 1.5 for t in toks]
    tot = float(sum(wt))
    t, out = start, []
    for tok, w in zip(toks, wt):
        d = (end - start) * w / tot
        out.append({"w": tok, "s": t, "e": t + d})
        t += d
    return out


def _words_in(segs, a, b):
    return [w for s in segs for w in s["words"] if a - 0.05 <= (w["s"] + w["e"]) / 2 <= b + 0.05]


def transcribe(path, lang="auto", mode="spoken", model="turbo", device="auto", roman_method="translit",
               progress=None, log=None, refine=True):
    """mode: spoken | roman (Hinglish in Roman letters) | translate (to English)."""
    from faster_whisper.audio import decode_audio
    log = log or (lambda *_: None)
    setup_cuda_paths()
    t0 = time.time()
    duration = probe(path)["duration"]
    language = None if lang in ("auto", "", None) else lang
    if mode == "translate" and model in ("turbo", "apex"):
        model = "large"   # turbo / Apex were not trained for the translate task
        log("translate mode: using Whisper large-v3")
    if model == "apex" and language not in (None, "en", "hi", "ur"):
        model = "turbo"   # Apex is for Hindi / Hinglish / English; any other language goes to turbo
        log("language %s: using large-v3-turbo instead of Apex" % language)
    if model == "apex":
        language = "en"   # Apex writes Hindi / Hinglish in Roman letters under the English token ("hi" would give Devanagari)
    name, _ = models.resolve(model)   # raises a clear message if the model has not been downloaded yet
    dev = "cuda" if device in ("auto", "cuda") and cuda_ok() else "cpu"
    task = "translate" if mode == "translate" else "transcribe"
    word_ts = task != "translate"
    warnings = []

    log("Reading audio and finding speech…")
    audio = decode_audio(str(path), sampling_rate=SR)
    chunks = speech_chunks(audio)
    if not chunks:
        raise RuntimeError("No speech found in this file.")
    log("Found %d speech chunks (%.0f s of speech)" % (len(chunks), sum(e - s for s, e in chunks)))

    def attempt(dev):
        if (name, dev) not in _models:
            log("Loading speech model %s on %s (first load takes ~30 s)…" % (name, dev.upper()))
        m = _load(name, dev)
        lg = language
        if lg is None:
            log("Detecting language…")
            lg, prob, _ = m.detect_language(audio[:SR * 30])
            log("detected language: %s (%.2f)" % (lg, prob))
        if mode == "roman" and lg == "ur":
            lg = "hi"  # Hinglish speakers: Whisper often labels it Urdu; decode as Hindi
        log("Transcribing speech%s…" % (" and translating to English" if task == "translate" else ""))
        segs, info = _decode(m, audio, chunks, lg, task, word_ts, progress, duration)
        # ---- gap repair: every speech chunk must have words; re-decode the ones that came back empty/thin ----
        for ci, (a, b) in enumerate(chunks):
            have = _words_in(segs, a, b)
            if b - a >= 1.2 and len(have) < max(1, int((b - a) * 0.6)):
                log("Re-checking %.1f–%.1f s (only %d words found)…" % (a, b, len(have)))
                extra, _ = _decode(m, audio, [[max(0, a - 0.2), b + 0.2]], lg, task, word_ts, None, duration)
                got = _words_in(extra, a, b)
                if len(got) > len(have):
                    segs = [s for s in segs if not (a - 0.05 <= (s["start"] + s["end"]) / 2 <= b + 0.05)] + extra
                    segs.sort(key=lambda s: s["start"])
                if len(_words_in(segs, a, b)) < 1:
                    warnings.append("No speech recognised between %.1fs and %.1fs" % (a, b))
        return segs, info

    try:
        segs, info = attempt(dev)
    except Exception as e:  # missing cuDNN/cuBLAS, OOM, etc -> CPU
        if dev == "cuda":
            log("CUDA failed (%s) -> falling back to CPU" % str(e)[:200])
            _models.clear()
            segs, info = attempt("cpu")
            dev = "cpu"
        else:
            raise
    if task == "translate":
        # keep captions on screen through short pauses: stretch each segment to the next one when the gap is small
        for i in range(len(segs) - 1):
            if 0 < segs[i + 1]["start"] - segs[i]["end"] <= 0.8:
                segs[i]["end"] = segs[i + 1]["start"]
        for s in segs:
            s["words"] = _spread(s["text"], s["start"], s["end"])
    if mode == "roman":
        for s in segs:
            for w in s["words"]:
                if has_devanagari(w["w"]):
                    w["w"] = romanize(w["w"])
            s["text"] = " ".join(w["w"] for w in s["words"])
    for s in segs:  # brand names Whisper mangles ("Misho", "Mishu", "Meesho.com" etc.)
        for w in s["words"]:
            w["w"] = _BRAND.sub(lambda m: "Meesho" + m.group(2), w["w"])
        s["text"] = " ".join(w["w"] for w in s["words"])
    if refine and mode != "translate":   # LLM pass: numbers as digits, natural Hinglish spelling, English words in English (engine/refine.py)
        from . import refine as _refine
        if _refine.available():
            log("Polishing the transcript with AI (numbers, spelling)…")
            n = _refine.refine_segments(segs, log)
            log("AI polish changed %d words" % n)
    if progress:
        progress(1.0)
    for w in warnings:
        log("WARNING: " + w)
    return {
        "language": info.language, "mode": mode, "model": model, "device": _state["device"],
        "compute": _state["compute"], "duration": duration, "seconds": round(time.time() - t0, 1),
        "segments": segs, "warnings": warnings,
    }


