# AI polish (optional) and where to put your API key

After the speech model writes the transcript, the app can send it to an AI model for a light clean-up:

| Before | After |
|---|---|
| `bis command aur hai` | `20 command aur hai` |
| `yah / vah / ke lie / pahle` | `ye / wo / ke liye / pehle` |
| `chat GPT`, `Google flow` | `ChatGPT`, `Google Flow` |
| obvious mis-hearings, judged from the sentence | corrected |

It keeps one output word per input word, so **word timings never change**. If the AI call fails, the original transcript is used.

## Privacy

When AI polish is on, **the transcript text** (not your video or audio) is sent to the provider you picked, in batches of about 45 words.
Choose a provider whose terms you are comfortable with, or leave AI polish off.

## Setting it up

### Option A: in the app (easiest)

**Settings (gear icon) → AI polish**

1. Pick a **provider**. Its address and a sensible model fill in automatically.
2. Paste your **API key** and press **Test**. It makes one tiny request and tells you whether the key works.
3. Press **Save**.

The key is stored on your computer in `workspace/settings.json` (this folder is git-ignored). The browser never gets the key back: it only shows the last 4 characters.

### Option B: environment variable (servers, containers, shared computers)

Set one of these before starting the app. It overrides anything saved in Settings.

| Provider | Variable |
|---|---|
| any | `AI_API_KEY` |
| Groq | `GROQ_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| xAI | `XAI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |

```bash
# Linux / macOS
export GROQ_API_KEY=your-key && ./run.sh
```
```powershell
# Windows PowerShell
$env:GROQ_API_KEY="your-key"; .\ui.bat
```

## Providers

| Provider | Where to get a key | Default model |
|---|---|---|
| Groq (free tier) | <https://console.groq.com/keys> | `openai/gpt-oss-120b` |
| OpenAI | <https://platform.openai.com/api-keys> | `gpt-4o-mini` |
| xAI (Grok) | <https://console.x.ai> | `grok-3-mini` |
| OpenRouter | <https://openrouter.ai/keys> | `openai/gpt-4o-mini` |
| Other | any service with an OpenAI-compatible `/chat/completions` endpoint | you choose |

Model names change often. If **Test** says "the model name or URL is wrong", look up the provider's current model list and type a name into the **Model** box.
You can also set a **backup model** that is tried if the first one fails.

## Turning it off

Switch off **Use AI to polish transcripts** in Settings, or leave the key empty.

## Never commit your key

`workspace/` is in `.gitignore`. Do not paste keys into source files, screenshots or issues. If a key leaks, revoke it in the provider's console and create a new one.
