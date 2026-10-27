#!/bin/bash
echo "🗑️ Uninstalling AgriSathi..."

read -p "Are you sure? This deletes the venv and compiled AI engine (y/n): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    # Remove venv
    rm -rf venv
    
    # Remove compiled build files
    if [ -d "llama.cpp/build" ]; then
        rm -rf llama.cpp/build
    fi
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} +
    
    echo "✅ Uninstalled cleanly. (Your .env and knowledge_base JSONs are safe)."
else
    echo "❌ Uninstall cancelled."
fi
