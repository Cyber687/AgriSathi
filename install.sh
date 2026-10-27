#!/bin/bash
echo "🌱 Starting AgriSathi One-Click Installation..."

# 1. Install System Dependencies
echo "📦 Installing system packages (requires sudo)..."
sudo apt update
sudo apt install -y build-essential cmake python3-pip python3-venv git

# 2. Setup Python Environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install faster-whisper edge-tts deep-translator

# 3. Setup llama.cpp
if [ ! -d "llama.cpp" ]; then
    echo "🧠 Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp
fi

echo "🔨 Compiling llama.cpp (this takes a few minutes)..."
cd llama.cpp
cmake -B build
cmake --build build --config Release -j$(nproc)
cd ..

# 4. Check for .env
if [ ! -f ".env" ]; then
    echo "⚠️ Creating empty .env file. Please add your API keys later."
    echo "OPENWEATHER_API_KEY=" > .env
    echo "DATA_GOV_IN_API_KEY=" >> .env
fi

# 5. Auto-Generate the Start Script (start_agrisathi.sh)
echo "📝 Generating start_agrisathi.sh..."
cat << 'START_SCRIPT' > start_agrisathi.sh
#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_DIR="$PROJECT_DIR/llama.cpp"

x-terminal-emulator -e "bash -c 'cd $LLAMA_DIR; ./build/bin/llama-server -m models/sarvam-1-v0.5-Q8_0.gguf -c 2048 -t 4 --host 127.0.0.1 --port 8080; exec bash'" &
sleep 3
x-terminal-emulator -e "bash -c 'cd $PROJECT_DIR; source venv/bin/activate; python main.py; exec bash'" &
START_SCRIPT

chmod +x start_agrisathi.sh

# 6. Auto-Generate Desktop Shortcut
echo "🖥️ Creating Desktop Shortcut..."
cat << EOF > ~/Desktop/AgriSathi.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=AgriSathi
Comment=Start AgriSathi AI
Exec=$PWD/start_agrisathi.sh
Icon=utilities-terminal
Terminal=false
Categories=Development;Utility;
