"""User settings kept in workspace/settings.json (never in git): the AI-polish provider, model and API key.

The API key can also come from the environment (AI_API_KEY, or the provider's usual name: GROQ_API_KEY, OPENAI_API_KEY, XAI_API_KEY,
OPENROUTER_API_KEY); the environment wins over the saved value, so a server or container never needs a file."""
import json
import os

from .util import WORK

FILE = WORK / "settings.json"
OLD_FILE = WORK / "ai.json"   # earlier versions

PROVIDERS = {
    "groq": {"label": "Groq (free tier, fast)", "url": "https://api.groq.com/openai/v1/chat/completions", "model": "openai/gpt-oss-120b",
             "env": "GROQ_API_KEY", "keys_url": "https://console.groq.com/keys"},
    "openai": {"label": "OpenAI", "url": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o-mini",
               "env": "OPENAI_API_KEY", "keys_url": "https://platform.openai.com/api-keys"},
    "xai": {"label": "xAI (Grok)", "url": "https://api.x.ai/v1/chat/completions", "model": "grok-3-mini",
            "env": "XAI_API_KEY", "keys_url": "https://console.x.ai"},
    "openrouter": {"label": "OpenRouter", "url": "https://openrouter.ai/api/v1/chat/completions", "model": "openai/gpt-4o-mini",
                   "env": "OPENROUTER_API_KEY", "keys_url": "https://openrouter.ai/keys"},
    "custom": {"label": "Other (any OpenAI-compatible API)", "url": "", "model": "", "env": "AI_API_KEY", "keys_url": ""},
}

DEFAULT_AI = {"enabled": True, "provider": "groq", "url": PROVIDERS["groq"]["url"], "model": PROVIDERS["groq"]["model"], "fallback": "", "key": ""}


def load():
    data = {}
    try:
        if FILE.exists():
            data = json.loads(FILE.read_text(encoding="utf-8"))
        elif OLD_FILE.exists():   # migrate the earlier ai.json
            old = json.loads(OLD_FILE.read_text(encoding="utf-8"))
            data = {"ai": {k: old[k] for k in ("provider", "url", "model", "fallback", "key") if k in old}}
    except Exception:
        data = {}
    ai = dict(DEFAULT_AI)
    ai.update(data.get("ai") or {})
    return {"ai": ai}


def save(data):
    WORK.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=1), encoding="utf-8")
    try:
        FILE.chmod(0o600)   # the key is a secret (no effect on Windows)
    except OSError:
        pass


def ai_key(ai=None):
    ai = ai or load()["ai"]
    prov = PROVIDERS.get(ai.get("provider") or "", {})
    for name in ("AI_API_KEY", prov.get("env", "")):
        if name and os.environ.get(name):
            return os.environ[name].strip(), "environment (%s)" % name
    return (ai.get("key") or "").strip(), "settings"


def ai_config():
    """The config refine.py uses, or None when AI polish is off or has no key."""
    ai = load()["ai"]
    key, _ = ai_key(ai)
    if not ai.get("enabled") or not key or not ai.get("url") or not ai.get("model"):
        return None
    return {"url": ai["url"], "model": ai["model"], "fallback": ai.get("fallback") or "", "key": key}


def public():
    """What the browser may see: everything except the key itself."""
    ai = load()["ai"]
    key, src = ai_key(ai)
    return {"ai": {"enabled": bool(ai["enabled"]), "provider": ai["provider"], "url": ai["url"], "model": ai["model"], "fallback": ai.get("fallback", ""),
                   "key_set": bool(key), "key_hint": ("…" + key[-4:]) if key else "", "key_source": src if key else ""},
            "providers": {k: {"label": v["label"], "url": v["url"], "model": v["model"], "keys_url": v["keys_url"]} for k, v in PROVIDERS.items()}}


def update_ai(patch):
    data = load()
    ai = data["ai"]
    for k in ("enabled", "provider", "url", "model", "fallback"):
        if k in patch:
            ai[k] = patch[k]
    if patch.get("clear_key"):
        ai["key"] = ""
    elif isinstance(patch.get("key"), str) and patch["key"].strip():
        ai["key"] = patch["key"].strip()
    save(data)
    if OLD_FILE.exists():
        try:
            OLD_FILE.unlink()
        except OSError:
            pass
