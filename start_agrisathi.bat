@echo off
:: Ensures the script runs in the folder it is placed in
cd /d "%~dp0"
echo Starting AgriSathi AI Engine...
:: Starts the AI Server in a new window
start "AgriSathi AI Server" cmd /k "cd llama.cpp && build\bin\Release\llama-server.exe -m models\sarvam-1-v0.5-Q8_0.gguf -c 2048 -t 4 --host 127.0.0.1 --port 8080"

echo Waiting for AI server to load...
timeout /t 4 /nobreak >nul

echo Starting Web Backend...
:: Starts the Python Backend in a new window
start "AgriSathi Python Backend" cmd /k "call venv\Scripts\activate.bat && python main.py"

echo Both terminals have been launched!
timeout /t 3 >nul
