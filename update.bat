@echo off
cd /d "%~dp0"
title AgriSathi Updater
echo Updating AgriSathi...

echo.
echo 1. Pulling latest code from GitHub...
git pull origin main

echo.
echo 2. Updating Python packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo 3. Rebuilding llama.cpp...
IF EXIST "llama.cpp" (
    cd llama.cpp
    cmake --build . --config Release
    cd ..
)

echo.
echo Update Complete!
pause
