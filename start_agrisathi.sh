#!/bin/bash

PROJECT_DIR="/mnt/agrisathi_data/AgriSathi"
LLAMA_DIR="$PROJECT_DIR/llama.cpp"

# Launch AI Server (The & at the end makes it run in the background)
x-terminal-emulator -e "bash -c 'cd $LLAMA_DIR; ./build/bin/llama-server -m models/sarvam-1-v0.5-Q8_0.gguf -c 2048 -t 4 --host 127.0.0.1 --port 8080; exec bash'" &

# Wait 3 seconds to let the AI server load
sleep 3

# Launch Python Backend (Also runs in the background)
x-terminal-emulator -e "bash -c 'cd $PROJECT_DIR; source venv/bin/activate; python main.py; exec bash'" &

echo "✅ Both terminals launched!"
