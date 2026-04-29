import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os

# =============================================
# KONFIGURASI
# =============================================
USERNAME    = "Nasky"
PASSWORD    = "sukasari05"  # GANTI PASSWORD!

# Reaction yang dipilih acak tiap kali
# Pilihan: upvote, funny, love, surprised, angry, sad
REACTION_TYPES = ["upvote", "funny", "love"]

DELAY_BETWEEN_REACTION = 2   # detik antar reaction (jangan terlalu cepat)
DELAY_BETWEEN_KOMIK    = 3   # detik antar komik
DELAY_BETWEEN_PAGE     = 2   # detik antar halaman listing

START_PAGE  = 1   # mulai dari halaman berapa
MAX_PAGES   = 999 # scan semua halaman (stop otomatis kalau sudah habis)
MAX_CHAPTER = 999 # semua chapter per komik

LOGIN_URL   = "https://komentar.mgkomik.cc/login.php"
KOMENTAR    = "https://komentar.mgkomik.cc"
BASE_URL    = "https://web.mgkomik.cc"
LIST_URL    = "https://web.mgkomik.cc/komik/"

# =============================================
# LOGGING
# =============================================
os.makedirs("logs", exist_ok=True)

def log(msg):
    print(msg, flush=True)
    with open("logs/bot.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# =============================================
# SESSION
# =============================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Connection": "keep-alive",
})

# =============================================
# LOGIN
# =============================================
def login():
    log("\n" + "="*50)
    log(f"[*] Login ke {LOGIN_URL}")
    try:
        r = session.get(LOGIN_URL, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        payload = {}
        form = soup.find("form")
        if form:
            for inp in form.find_all("input"):
                n = inp.get("name")
                v = inp.get("value", "")
                if n:
                    payload[n] = v

        payload["username"] = USERNAME
        payload["password"] = PASSWORD

        h = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_URL,
            "Origin": KOMENTAR,
        }
        r2 = session.post(LOGIN_URL, data=payload, headers=h, allow_redirects=True, timeout=20)
        log(f"    Status: {r2.status_code} | Redirect: {r2.url}")

        # Cek login berhasil
        checks = ["logout", "keluar", "dashboard", "profil", USERNAME.lower(), "sign out", "signout"]
        if any(c in r2.text.lower() for c in checks):
            log("[✓] LOGIN BERHASIL!")
            return True

        # Coba cek cookies
        cookies = dict(session.cookies)
        if any("session" in k.lower() or "token" in k.lower() or "user" in k.lower() or "auth" in k.lower() for k in cookies):
            log(f"[✓] Login OK via cookie: {list(cookies.keys())}")
            return True

        log(f"[!] Login tidak terkonfirmasi. Preview: {r2.text[:200]}")
        return True  # tetap lanjut, mungkin sudah login
    except Exception as e:
        log(f"[✗] Error login: {e}")
        return False

# =============================================
# AMBIL SEMUA KOMIK DARI HALAMAN LISTING
# =============================================
def get_komik_page(page=1):
    url = f"{LIST_URL}?page={page}"
    try:
        r = session.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            # Link komik: mengandung /komik/ tapi BUKAN /chapter
            if "/komik/" in href and "/chapter" not in href and href.rstrip("/") != LIST_URL.rstrip("/"):
                full = href if href.startswith("http") else BASE_URL + href
                # Pastikan bukan halaman listing itu sendiri
                if full.rstrip("/") != LIST_URL.rstrip("/") and full not in links:
                    links.append(full)

        return list(set(links))
    except Exception as e:
        log(f"[!] Error ambil halaman {page}: {e}")
        return []

# =============================================
# AMBIL SEMUA CHAPTER DARI HALAMAN KOMIK
# =============================================
def get_chapters(komik_url):
    try:
        r = session.get(komik_url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        chapters = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "/chapter" in href or "/ch-" in href:
                full = href if href.startswith("http") else BASE_URL + href
                if full not in chapters:
                    chapters.append(full)
        # Urutkan chapter dari awal ke akhir
        chapters = list(set(chapters))
        chapters.sort()
        return chapters[:MAX_CHAPTER]
    except Exception as e:
        log(f"    [!] Error ambil chapter: {e}")
        return []

# =============================================
# KIRIM REACTION KE SATU URL
# =============================================
def send_reaction(target_url, reaction_type):
    reaction_map = {
        "upvote": 1, "funny": 2, "love": 3,
        "surprised": 4, "angry": 5, "sad": 6,
    }
    reaction_id = reaction_map.get(reaction_type, 1)

    try:
        r = session.get(target_url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # Cari post_id dari HTML
        post_id = None

        # Cara 1: atribut data-*
        for attr in ["data-post-id", "data-id", "data-comic-id", "data-chapter-id", "data-manga-id", "data-entry-id"]:
            el = soup.find(attrs={attr: True})
            if el:
                post_id = el.get(attr)
                break

        # Cara 2: dari script inline
        if not post_id:
            for script in soup.find_all("script"):
                txt = script.string or ""
                m = re.search(r'(?:post_id|postId|comic_id|chapter_id|entry_id|the_id)["\s:=>]+["\']?([\d]+)', txt)
                if m:
                    post_id = m.group(1)
                    break

        # Cara 3: meta tag
        if not post_id:
            meta = soup.find("meta", {"property": "og:url"})
            if meta:
                m = re.search(r'p=(\d+)', meta.get("content", ""))
                if m:
                    post_id = m.group(1)

        # Cara 4: ambil dari URL slug → pakai sebagai ID
        if not post_id:
            slug = target_url.rstrip("/").split("/")[-1]
            post_id = slug

        payload = {"post_id": post_id, "reaction": reaction_id}
        req_headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": target_url,
            "Origin": BASE_URL,
        }

        endpoints = [
            f"{BASE_URL}/api/reaction",
            f"{BASE_URL}/wp-json/manga/v1/reaction",
            f"{BASE_URL}/reaction",
            f"{KOMENTAR}/api/reaction",
        ]

        for api in endpoints:
            try:
                rr = session.post(api, json=payload, headers=req_headers, timeout=10)
                if rr.status_code == 200:
                    resp = rr.text[:80]
                    log(f"    [✓] {reaction_type.upper()} | pid={post_id} | {resp}")
                    return True
            except:
                continue

        log(f"    [✗] Semua endpoint gagal untuk: {target_url.split('/')[-1]}")
        return False

    except Exception as e:
        log(f"    [!] Exception: {e}")
        return False

# =============================================
# PROSES SATU KOMIK LENGKAP
# =============================================
def process_komik(komik_url, nomor):
    name = komik_url.rstrip("/").split("/")[-1]
    log(f"\n[{nomor}] ▶ KOMIK: {name}")
    log(f"    URL: {komik_url}")

    # Reaction di halaman utama komik
    r1 = random.choice(REACTION_TYPES)
    log(f"    Reaction komik: {r1}")
    send_reaction(komik_url, r1)
    time.sleep(DELAY_BETWEEN_REACTION)

    # Ambil semua chapter
    chapters = get_chapters(komik_url)
    log(f"    Chapter ditemukan: {len(chapters)}")

    for i, ch_url in enumerate(chapters, 1):
        ch_name = ch_url.rstrip("/").split("/")[-1]
        r2 = random.choice(REACTION_TYPES)
        log(f"    [{i}/{len(chapters)}] Chapter: {ch_name} → {r2}")
        send_reaction(ch_url, r2)
        time.sleep(DELAY_BETWEEN_REACTION)

    log(f"    ✓ Komik selesai: {name}")

# =============================================
# MAIN
# =============================================
def main():
    log("="*50)
    log("  MGKomik Auto Reaction Bot")
    log(f"  User      : {USERNAME}")
    log(f"  Reactions : {REACTION_TYPES}")
    log(f"  List URL  : {LIST_URL}")
    log("="*50)

    if not login():
        log("[✗] Gagal login. Bot berhenti.")
        return

    total_komik = 0
    total_ok    = 0
    total_fail  = 0

    for page in range(START_PAGE, MAX_PAGES + 1):
        log(f"\n{'='*50}")
        log(f"[PAGE {page}] Mengambil daftar komik...")
        komik_list = get_komik_page(page)

        if not komik_list:
            log(f"[!] Halaman {page} kosong atau habis. Bot selesai.")
            break

        log(f"    {len(komik_list)} komik di halaman ini.")
        time.sleep(DELAY_BETWEEN_PAGE)

        for komik_url in komik_list:
            total_komik += 1
            try:
                process_komik(komik_url, total_komik)
                total_ok += 1
            except Exception as e:
                log(f"    [!] Error komik: {e}")
                total_fail += 1
            time.sleep(DELAY_BETWEEN_KOMIK)

    log("\n" + "="*50)
    log(f"  SELESAI!")
    log(f"  Total komik diproses : {total_komik}")
    log(f"  Berhasil             : {total_ok}")
    log(f"  Gagal                : {total_fail}")
    log("="*50)

if __name__ == "__main__":
    main()
