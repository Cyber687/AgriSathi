#!/bin/bash
echo "🔄 Updating AgriSathi..."

# Pull latest code
git pull origin main || echo "⚠️ Git pull failed. Ensure you are in a git repo."

# Update Python packages
source venv/bin/activate
pip install -r requirements.txt
pip install faster-whisper edge-tts deep-translator

# Rebuild llama.cpp if it exists
if [ -d "llama.cpp" ]; then
    echo "🔨 Rebuilding llama.cpp..."
    cd llama.cpp
    cmake --build build --config Release -j$(nproc)
    cd ..
fi

echo "✅ Update Complete!"
