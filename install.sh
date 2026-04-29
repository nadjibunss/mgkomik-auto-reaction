#!/bin/bash
echo "[1] Install Python packages..."
pip install -r requirements.txt

echo "[2] Install playwright-stealth..."
pip install playwright-stealth

echo "[3] Install Playwright Chromium..."
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

echo "[DONE] Selesai! Jalankan: python3 bot.py"
