#!/bin/bash
# Script otomatis install dan jalankan bot di Termux

echo "====================================="
echo "  MGKomik Auto Reaction Bot - Termux"
echo "====================================="

# Update dan install Python jika belum ada
if ! command -v python3 &>/dev/null; then
    echo "[*] Install Python..."
    pkg update -y && pkg install python -y
fi

# Install pip jika belum
if ! command -v pip &>/dev/null; then
    echo "[*] Install pip..."
    pkg install python-pip -y
fi

# Install dependencies
echo "[*] Install dependencies..."
pip install -r requirements.txt -q

# Jalankan bot
echo "[*] Menjalankan bot..."
python3 bot.py
