# MGKomik Auto Reaction Bot

Bot otomatis untuk memberi reaction di setiap komik dan chapter di [web.mgkomik.cc](https://web.mgkomik.cc).

## Fitur
- Login otomatis ke MGKomik
- Scan semua komik dari halaman daftar
- Reaction otomatis di halaman komik dan setiap chapter
- Pilihan reaction: Upvote, Funny, Love, Surprised, Angry, Sad
- Delay acak antar request untuk menghindari ban

## Cara Pakai di Termux

### 1. Install git dan clone repo
```bash
pkg update && pkg install git python -y
git clone https://github.com/nadjibunss/mgkomik-auto-reaction
cd mgkomik-auto-reaction
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Edit konfigurasi (opsional)
```bash
nano bot.py
# Ubah USERNAME, PASSWORD, REACTION_TYPES, MAX_PAGES, MAX_CHAPTERS_PER_KOMIK
```

### 4. Jalankan bot
```bash
bash run.sh
# atau langsung:
python3 bot.py
```

## Konfigurasi di bot.py

| Variabel | Default | Keterangan |
|---|---|---|
| `USERNAME` | `Nasky` | Username MGKomik |
| `PASSWORD` | `****` | Password MGKomik |
| `REACTION_TYPES` | `["upvote","funny","love"]` | Jenis reaction acak |
| `MAX_PAGES` | `2` | Halaman daftar komik |
| `MAX_CHAPTERS_PER_KOMIK` | `5` | Chapter per komik |
| `DELAY_MIN` | `3` | Delay minimum (detik) |
| `DELAY_MAX` | `7` | Delay maksimum (detik) |
