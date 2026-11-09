#!/usr/bin/env bash
cd "$(dirname "$0")"
PYTHONPATH="$PWD" exec .venv/bin/python captions.py serve "$@"
