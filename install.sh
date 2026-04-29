#!/bin/bash
echo "[1] Install Python packages..."
pip install -r requirements.txt

echo "[2] Install Playwright browsers (Chromium)..."
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

echo "[DONE] Siap! Jalankan: python3 bot.py"
