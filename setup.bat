@echo off
REM One-time setup on Windows: Python virtual environment + packages.
REM Needs Python 3.10+ and ffmpeg on PATH (winget install Gyan.FFmpeg). See docs\INSTALL.md
cd /d "%~dp0"
where ffmpeg >nul 2>nul || ( echo.&echo ffmpeg was not found. Install it first:  winget install Gyan.FFmpeg  ^(then open a new terminal^)&echo.&pause&exit /b 1 )
if not exist .venv ( py -3 -m venv .venv || python -m venv .venv )
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
REM faster-whisper pulls in the CPU onnxruntime, which hides the GPU (DirectML) one and makes the person cut-out ~8x slower
.venv\Scripts\python.exe -m pip uninstall -y onnxruntime onnxruntime-directml
.venv\Scripts\python.exe -m pip install --no-deps onnxruntime-directml==1.23.0
echo.
echo Setup done. Start the app with ui.bat, then open Settings ^(gear icon^) -^> Models to download a speech model.
pause
