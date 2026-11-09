"""Smoke test: every template must build a caption file for a few awkward sentences, and the settings / models modules must behave.
Run:  python tests/test_smoke.py   (needs only Pillow and Flask; no video, GPU or model)"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SENTENCES = [
    "hello",
    "a",
    "this is a really wonderful morning today friends and family",
    "ek minute mein captions ready ho jayenge bhai",
    "wow. no way! really? yes",
    "I",
]


def words(text):
    return [{"w": x, "s": i * 0.35, "e": i * 0.35 + 0.3} for i, x in enumerate(text.split())]


def test_templates():
    from engine.ass import build_ass
    from engine.styles import STYLES, TEMPLATE_GROUPS
    assert len(STYLES) >= 100, "expected 100+ templates, found %d" % len(STYLES)
    missing = [i for g in TEMPLATE_GROUPS.values() for i in g if i not in STYLES]
    assert not missing, "ids in groups but not defined: %s" % missing
    for sid, st in STYLES.items():
        for text in SENTENCES:
            doc = build_ass(words(text), sid, split=bool(st["behind"]))
            parts = doc if isinstance(doc, tuple) else (doc,)
            assert all(isinstance(p, str) and "[Events]" in p for p in parts), sid
    print("templates ok:", len(STYLES))


def test_models_registry():
    from engine import models
    for mid, info in models.REGISTRY.items():
        assert info["size_mb"] > 0 and info["label"] and info["dir"], mid
        assert ("repo" in info) or ("url" in info), mid
    rows = models.status()
    assert {r["id"] for r in rows} == set(models.REGISTRY)
    try:
        models.resolve("definitely-not-downloaded") and None
    except RuntimeError:
        pass
    print("models ok")


def test_settings_never_leak_key():
    from engine import settings
    old_file, old_old = settings.FILE, settings.OLD_FILE
    with tempfile.TemporaryDirectory() as d:
        from pathlib import Path
        settings.FILE, settings.OLD_FILE = Path(d) / "settings.json", Path(d) / "ai.json"
        for k in ("AI_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY"):
            os.environ.pop(k, None)
        assert settings.ai_config() is None            # no key -> AI polish is off
        settings.update_ai({"key": "sk-test-1234567890", "provider": "openai", "url": "https://x/y", "model": "m"})
        pub = settings.public()
        assert "key" not in pub["ai"] and "1234567890" not in str(pub), "the key must never be sent to the browser"
        assert pub["ai"]["key_hint"].endswith("7890")
        assert settings.ai_config()["key"] == "sk-test-1234567890"
        os.environ["AI_API_KEY"] = "from-env"
        assert settings.ai_config()["key"] == "from-env"   # the environment wins
        os.environ.pop("AI_API_KEY")
    settings.FILE, settings.OLD_FILE = old_file, old_old
    print("settings ok")


if __name__ == "__main__":
    test_templates()
    test_models_registry()
    test_settings_never_leak_key()
    print("ALL OK")
