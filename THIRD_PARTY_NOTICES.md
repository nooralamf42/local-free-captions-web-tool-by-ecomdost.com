# Third-party components

Local Captions is MIT-licensed. It uses, and in some cases downloads on request, the following. Each keeps its own licence.

## Software libraries (installed by `pip` / `npm`)

| Component | Use | Licence |
|---|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) / [CTranslate2](https://github.com/OpenNMT/CTranslate2) | speech recognition runtime | MIT |
| [Flask](https://flask.palletsprojects.com) | local web server | BSD-3-Clause |
| [Pillow](https://python-pillow.org), [NumPy](https://numpy.org), [OpenCV](https://opencv.org) | image and array handling | HPND, BSD, Apache-2.0 |
| [ONNX Runtime](https://onnxruntime.ai) | runs the person cut-out model | MIT |
| [huggingface_hub](https://github.com/huggingface/huggingface_hub) | model downloads | Apache-2.0 |
| [JASSUB](https://github.com/ThaUnknown/jassub) (libass compiled to WebAssembly) | caption preview in the browser | MIT / ISC |
| React, Vite, Tailwind CSS, Radix UI, lucide-react | interface | MIT / ISC |

## External programs (you install them)

| Component | Use | Licence |
|---|---|---|
| [FFmpeg](https://ffmpeg.org) with libass | video decoding, caption burn-in, encoding | LGPL / GPL, depending on the build you install |

## Models (downloaded only when you press Download)

| Model | Licence | Source |
|---|---|---|
| Whisper (OpenAI) large-v3, large-v3-turbo, medium, small (CTranslate2 conversions by Systran and Mobius Labs) | MIT | <https://github.com/openai/whisper> |
| Whisper-Hindi2Hinglish-Apex (Oriserve), int8 CTranslate2 conversion by abhayhadez | Apache-2.0 | <https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Apex> |
| Robust Video Matting, MobileNetV3 (Peter Lin et al.) | GPL-3.0 | <https://github.com/PeterL1n/RobustVideoMatting> |

The matting model is **not bundled**: it is downloaded to your own computer on request and used through ONNX Runtime. If you redistribute a build that includes that file, you must
comply with the GPL-3.0 for it.

## Fonts

Bundled in `fonts/`; all open-source (SIL OFL 1.1 or Apache 2.0). The list and notes are in [fonts/README.md](fonts/README.md).

## AI services (optional)

If you turn on AI polish you use a third-party API (Groq, OpenAI, xAI, OpenRouter or another) under that provider's own terms, with your own key.

## Trademarks

All product and company names mentioned are trademarks of their respective owners. This project is not affiliated with, sponsored by or endorsed by them.
