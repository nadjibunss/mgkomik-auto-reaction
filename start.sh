#!/bin/bash
# Jalankan bot langsung tanpa Docker

echo "====================================="
echo "  MGKomik Auto Reaction Bot"
echo "====================================="

# Install dependencies jika belum
pip install -r requirements.txt -q

# Jalankan bot
python3 bot.py
