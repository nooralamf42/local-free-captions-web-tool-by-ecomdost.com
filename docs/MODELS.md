# Models

The app does not ship any AI model. Each one is downloaded when you press its **Download** button (Settings → Models) or run
`python captions.py download <id>`. They are saved under `models/` and work offline afterwards. Delete one with the trash icon.

| id | Name | Size | Licence | Source |
|---|---|---|---|---|
| `apex` | Hinglish Apex | ~0.8 GB | Apache-2.0 | [abhayhadez/anchor-hinglish-apex-ct2](https://huggingface.co/abhayhadez/anchor-hinglish-apex-ct2), an int8 conversion of [Oriserve/Whisper-Hindi2Hinglish-Apex](https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Apex) |
| `turbo` | Whisper large-v3-turbo | ~1.6 GB | MIT | [mobiuslabsgmbh/faster-whisper-large-v3-turbo](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo) |
| `large` | Whisper large-v3 | ~3.1 GB | MIT | [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) |
| `medium` | Whisper medium | ~1.5 GB | MIT | [Systran/faster-whisper-medium](https://huggingface.co/Systran/faster-whisper-medium) |
| `small` | Whisper small | ~0.5 GB | MIT | [Systran/faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small) |
| `matting` | Person cut-out (Robust Video Matting, MobileNetV3) | 14 MB | GPL-3.0 | [PeterL1n/RobustVideoMatting releases](https://github.com/PeterL1n/RobustVideoMatting/releases/tag/v1.0.0) |

## Which one should I use?

- **Hindi, Hinglish, or a mix of Hindi and English: `apex`.** It writes Roman letters directly ("ye photo upload kar do"), keeps English words in English
  ("ChatGPT open karna hai") and adds punctuation. Set *Language spoken* to Auto-detect and *Captions written as* to Hinglish.
- **English or another language: `turbo`.** Fast, accurate, 90+ languages. Hindi with turbo comes out in Devanagari; the app can convert it to Roman letters,
  but English words inside Hindi speech are often spelled phonetically.
- **Translate speech into English: `large`.** Only large-v3 can translate. Apex and turbo cannot.
- **Small computer or quick draft: `small`.**

Apex only handles Hindi, Hinglish and English. If you pick another language the app uses turbo instead (download it too).

## How Apex compared

On Hinglish test videos, Apex produced "type karke", "bhej denge" and "ChatGPT open karna hai" where turbo plus a Devanagari-to-Roman converter produced
"taaip karke", "vez denge" and "chait jeepeeti upan karna hai". Apex's Roman spelling is a little formal ("yah", "ke lie", "pahle"); the optional
[AI polish](AI_POLISH.md) normalises these. The model's authors publish word-error-rate numbers on its model card; they are self-reported, so try it on your own audio.

## Where files go, and using your own model

Models live in `models/<id>/` (speech models are CTranslate2 folders containing `model.bin`). If you already have a faster-whisper model folder you can copy it
to `models/<id>/`, or pass a path on the command line: `python captions.py reel.mp4 --model /path/to/model-folder`.

## GPU memory

- `apex` (int8) needs about 1 GB of GPU memory, `turbo` about 2.7 GB, `large` about 4 GB. If the GPU runs out of memory the app retries on the CPU.
- The person cut-out uses the GPU too (DirectML on Windows).
