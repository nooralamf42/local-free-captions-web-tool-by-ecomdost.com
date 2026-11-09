# Contributing

Thanks for helping! Bug reports, template ideas, translations of the docs and pull requests are all welcome.

## Set up for development

```bash
git clone https://github.com/nooralamf42/local-free-captions-web-tool-by-ecomdost.com.git
cd local-free-captions-web-tool-by-ecomdost.com
./setup.sh        # Windows: setup.bat
cd frontend && npm install && npm run build && cd ..
```

Run the app: `./run.sh` (Windows: `ui.bat`). Python code is in `engine/` and `server.py`; the interface is `frontend/src/`, built into `web/`.
If you change `frontend/`, rebuild with `npm run build` and commit the updated `web/` folder too (so people can use the app without Node).

## Before you open a pull request

- `python tests/test_smoke.py` must pass (it builds captions for every template with a few awkward sentences).
- Keep changes focused; describe what you changed and how you checked it.
- New fonts must be open-source (OFL / Apache) and listed in `fonts/README.md`.
- Never commit API keys, models, videos or anything from `workspace/`, `outputs/`, `models/`.
- Do not copy code, fonts, artwork or templates from other products. Original work only.

## Good first issues

- More templates (see [docs/TEMPLATES.md](docs/TEMPLATES.md))
- More providers in `engine/settings.py` (`PROVIDERS`)
- Linux and macOS testing and fixes
- Spelling normalisation for Hinglish (`engine/roman.py`, `glossary.json`)

## Reporting a bug

Include your OS, GPU, the model you used, and the text of the **Activity** log from the home page. Do not include API keys.
