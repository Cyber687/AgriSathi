@echo off
:: Ensures the script runs in the folder it is placed in
cd /d "%~dp0"
title AgriSathi Windows Installer
echo Starting AgriSathi One-Click Installation...

echo.
echo 1. Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo 2. Installing Python dependencies...
pip install -r requirements.txt
pip install faster-whisper edge-tts deep-translator

echo.
echo 3. Setting up llama.cpp...
IF NOT EXIST "llama.cpp" (
    git clone https://github.com/ggerganov/llama.cpp
)

echo.
echo 4. Compiling llama.cpp (Requires CMake and Visual Studio Build Tools)...
cd llama.cpp
cmake -B build
cmake --build . --config Release
cd ..

echo.
echo 5. Creating .env file...
IF NOT EXIST ".env" (
    echo OPENWEATHER_API_KEY= > .env
    echo DATA_GOV_IN_API_KEY= >> .env
)

echo.
echo Installation Complete!
echo To start the app, double-click start_agrisathi.bat
pause
