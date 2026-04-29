# MGKomik Auto Reaction Bot 🤖

Bot otomatis reaction di [web.mgkomik.cc](https://web.mgkomik.cc) — **Pure Python, tanpa Docker**.

---

## 🚀 Deploy di Cloud Terminal

### Step 1 — Clone repo
```bash
git clone https://github.com/nadjibunss/mgkomik-auto-reaction
cd mgkomik-auto-reaction
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Jalankan bot
```bash
python3 bot.py
```

atau pakai script otomatis:
```bash
bash start.sh
```

### Jalankan di background (agar tetap jalan walau terminal ditutup)
```bash
nohup python3 bot.py > logs/output.log 2>&1 &
echo "Bot berjalan! PID: $!"
```

### Lihat log live
```bash
tail -f logs/bot.log
```

### Stop bot
```bash
# Cari PID
ps aux | grep bot.py
# Kill
kill <PID>
```

---

## ⚙️ Konfigurasi (edit bot.py)

| Variable | Default | Keterangan |
|---|---|---|
| `USERNAME` | `Nasky` | Username MGKomik |
| `PASSWORD` | _(isi sendiri)_ | Password MGKomik |
| `REACTION_TYPES` | `["upvote","funny","love"]` | Reaction acak |
| `MAX_PAGES` | `2` | Halaman komik discan |
| `MAX_CHAPTERS_PER_KOMIK` | `5` | Chapter per komik |
| `DELAY_MIN` | `3` | Delay min (detik) |
| `DELAY_MAX` | `7` | Delay max (detik) |
| `LOOP_INTERVAL` | `1800` | Jeda antar ronde (detik) |

---

## 📋 Fitur
- ✅ Login otomatis
- ✅ Scan semua komik & chapter
- ✅ Reaction acak: Upvote, Funny, Love, Surprised, Angry, Sad
- ✅ Loop otomatis tiap 30 menit
- ✅ Log tersimpan di `logs/bot.log`
- ✅ Bisa jalan di background dengan `nohup`
