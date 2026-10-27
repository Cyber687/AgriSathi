#!/bin/bash

# ============================================================
# AgriSathi - Automated Setup Script for Linux Mint
# ============================================================

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   Welcome to AgriSathi Setup Script       ${NC}"
echo -e "${BLUE}===========================================${NC}"

# --- 1. SYSTEM DEPENDENCIES ---
echo -e "\n${YELLOW}[1/4] Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y build-essential cmake git python3-pip python3-venv

# --- 2. COMPILE LLAMA.CPP ---
echo -e "\n${YELLOW}[2/4] Setting up llama.cpp...${NC}"
if [ ! -d "llama.cpp" ]; then
    echo "Cloning llama.cpp repository..."
    git clone https://github.com/ggerganov/llama.cpp
else
    echo "llama.cpp directory already exists. Skipping clone."
fi

cd llama.cpp
echo "Compiling llama.cpp (this may take a few minutes)..."
cmake -B build
cmake --build build --config Release -j$(nproc)
cd ..

# --- 3. CHECK FOR MODEL ---
echo -e "\n${YELLOW}[3/4] Checking for local AI model...${NC}"
MODEL_PATH="llama.cpp/models/sarvam-1-v0.5-Q8_0.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}WARNING: Model file not found at $MODEL_PATH${NC}"
    echo -e "Please download 'sarvam-1-v0.5-Q8_0.gguf' from Hugging Face"
    echo -e "and place it inside the 'llama.cpp/models/' folder before running the app."
else
    echo -e "${GREEN}Model found successfully!${NC}"
fi

# --- 4. SETUP PYTHON ENVIRONMENT ---
echo -e "\n${YELLOW}[4/4] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists. Skipping creation."
fi

# Activate the virtual environment
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install faster-whisper edge-tts

echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}   Setup Complete!                         ${NC}"
echo -e "${GREEN}===========================================${NC}"
echo -e "\nTo run the application, you need TWO terminal windows."
echo -e "\n${BLUE}Terminal 1 (Start the AI Server):${NC}"
echo -e "  cd llama.cpp"
echo -e "  ./build/bin/llama-server -m models/sarvam-1-v0.5-Q8_0.gguf -c 2048 -t 4 --host 127.0.0.1 --port 8080"
echo -e "\n${BLUE}Terminal 2 (Start the Web App):${NC}"
echo -e "  source venv/bin/activate"
echo -e "  python main.py"
echo -e "\nThen open your browser to: ${YELLOW}http://127.0.0.1:8000${NC}"