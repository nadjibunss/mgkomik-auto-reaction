# MGKomik Auto Reaction Bot 🤖

Bot otomatis reaction di [web.mgkomik.cc](https://web.mgkomik.cc)

---

## 🚀 Deploy di Cloud Terminal (Docker)

### Step 1 — Clone repo
```bash
git clone https://github.com/nadjibunss/mgkomik-auto-reaction
cd mgkomik-auto-reaction
```

### Step 2 — Edit password (WAJIB)
```bash
nano docker-compose.yml
```
Ganti bagian `PASSWORD=sukasari05` dengan password baru kamu.

### Step 3 — Jalankan bot
```bash
docker-compose up -d
```

### Step 4 — Lihat log live
```bash
docker-compose logs -f
```

### Stop bot
```bash
docker-compose down
```

---

## 🐳 Cara alternatif (tanpa docker-compose)

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

# Stop
docker stop mgkomik-bot
```

---

## ⚙️ Konfigurasi ENV di docker-compose.yml

| Variable | Default | Keterangan |
|---|---|---|
| `USERNAME` | `Nasky` | Username MGKomik |
| `PASSWORD` | _(isi sendiri)_ | Password MGKomik |
| `REACTION_TYPES` | `upvote,funny,love` | Reaction acak (pisah koma) |
| `MAX_PAGES` | `2` | Jumlah halaman komik discan |
| `MAX_CHAPTERS_PER_KOMIK` | `5` | Chapter per komik |
| `DELAY_MIN` | `3` | Delay min antar request (detik) |
| `DELAY_MAX` | `7` | Delay max antar request (detik) |

---

## 📋 Fitur
- ✅ Login otomatis
- ✅ Scan semua komik
- ✅ Reaction di halaman komik & tiap chapter
- ✅ Reaction acak: Upvote, Funny, Love, Surprised, Angry, Sad
- ✅ Loop otomatis tiap 30 menit
- ✅ Log tersimpan di `logs/bot.log`
- ✅ Konfigurasi via ENV variable
- ✅ Auto-restart jika container crash (`restart: unless-stopped`)
