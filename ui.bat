@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
.venv\Scripts\python.exe captions.py serve
pause
