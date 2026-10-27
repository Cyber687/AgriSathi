@echo off
cd /d "%~dp0"
title AgriSathi Uninstaller
echo WARNING: This will delete your virtual environment and compiled AI files.
set /p confirm="Are you sure you want to uninstall? (y/n): "
if /i "%confirm%" neq "y" exit /b

echo Uninstalling...
:: Remove Python virtual environment
IF EXIST "venv" rmdir /s /q venv

:: Remove compiled C++ build files
IF EXIST "llama.cpp\build" rmdir /s /q llama.cpp\build

echo.
echo Uninstalled cleanly. Your .env and knowledge_base JSONs are safe.
pause
