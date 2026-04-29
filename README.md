# MGKomik Auto Reaction Bot 🤖

Bot otomatis reaction di [web.mgkomik.cc](https://web.mgkomik.cc) — support **Docker** dan **Termux**.

## 🐳 Deploy dengan Docker

### Cara 1 — Docker Compose (Direkomendasikan)
```bash
# Clone repo
git clone https://github.com/nadjibunss/mgkomik-auto-reaction
cd mgkomik-auto-reaction

# Edit password dulu!
nano docker-compose.yml

# Jalankan
docker-compose up -d

# Lihat log live
docker-compose logs -f
```

### Cara 2 — Docker biasa
```bash
docker build -t mgkomik-bot .
docker run -d --name mgkomik-bot \
  -e USERNAME=Nasky \
  -e PASSWORD=PASSWORD_KAMU \
  -e REACTION_TYPES=upvote,funny,love \
  -e MAX_PAGES=2 \
  -e MAX_CHAPTERS_PER_KOMIK=5 \
  --restart unless-stopped \
  mgkomik-bot

# Lihat log
docker logs -f mgkomik-bot
```

## 📱 Jalankan di Termux
```bash
pkg update && pkg install git python -y
git clone https://github.com/nadjibunss/mgkomik-auto-reaction
cd mgkomik-auto-reaction
pip install -r requirements.txt
python3 bot.py
```

## ⚙️ Konfigurasi ENV

| Variable | Default | Keterangan |
|---|---|---|
| `USERNAME` | `Nasky` | Username MGKomik |
| `PASSWORD` | `sukasari05` | Password MGKomik |
| `REACTION_TYPES` | `upvote,funny,love` | Reaction acak (pisah koma) |
| `MAX_PAGES` | `2` | Jumlah halaman komik |
| `MAX_CHAPTERS_PER_KOMIK` | `5` | Chapter per komik |
| `DELAY_MIN` | `3` | Delay min antar request (detik) |
| `DELAY_MAX` | `7` | Delay max antar request (detik) |

## 📋 Fitur
- ✅ Login otomatis
- ✅ Scan semua komik
- ✅ Reaction di halaman komik & setiap chapter
- ✅ Reaction acak: Upvote, Funny, Love, Surprised, Angry, Sad
- ✅ Loop otomatis tiap 30 menit
- ✅ Simpan log ke `logs/bot.log`
- ✅ Konfigurasi via ENV variable (Docker-friendly)
- ✅ Auto-restart jika container crash
