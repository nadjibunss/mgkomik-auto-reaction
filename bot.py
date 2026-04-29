import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re
import os

# =============================================
# KONFIGURASI - EDIT DI SINI
# =============================================
USERNAME       = "Nasky"
PASSWORD       = "sukasari05"  # GANTI PASSWORD!
REACTION_TYPES = ["upvote", "funny", "love"]  # pilihan: upvote funny love surprised angry sad
MAX_PAGES      = 2
MAX_CHAPTERS_PER_KOMIK = 5
DELAY_MIN      = 3
DELAY_MAX      = 7
LOOP_INTERVAL  = 1800  # ulang tiap 30 menit

# URL - LOGIN dulu ke komentar, lalu reaction di web
LOGIN_URL  = "https://komentar.mgkomik.cc/login.php"
BASE_URL   = "https://web.mgkomik.cc"
KOMENTAR   = "https://komentar.mgkomik.cc"

# =============================================
# LOGGING
# =============================================
os.makedirs("logs", exist_ok=True)

def log(msg):
    print(msg, flush=True)
    with open("logs/bot.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# =============================================
# SESSION (shared untuk komentar + web)
# =============================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
})

# =============================================
# LOGIN ke komentar.mgkomik.cc/login.php
# =============================================
def login():
    log("[*] Login ke https://komentar.mgkomik.cc/login.php ...")
    try:
        # GET halaman login untuk ambil CSRF / form fields
        r = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Cari semua hidden input
        payload = {}
        form = soup.find("form")
        if form:
            for inp in form.find_all("input"):
                name = inp.get("name")
                val  = inp.get("value", "")
                if name:
                    payload[name] = val

        # Isi username & password
        # Coba berbagai kemungkinan nama field
        for key in ["username", "user", "email", "login"]:
            if key in payload or not payload:
                payload[key] = USERNAME
                break
        for key in ["password", "pass", "passwd", "pwd"]:
            if key in payload or not payload:
                payload[key] = PASSWORD
                break

        # Pastikan field username & password terisi
        payload["username"] = USERNAME
        payload["password"] = PASSWORD

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_URL,
            "Origin": KOMENTAR,
        }

        r2 = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True, timeout=15)

        # Debug: print respons awal
        log(f"    Status: {r2.status_code} | URL: {r2.url}")

        if r2.status_code in [200, 302]:
            if any(k in r2.text.lower() for k in ["logout", "keluar", "dashboard", "profil", USERNAME.lower()]):
                log("[✓] Login BERHASIL!")
                return True
            else:
                log("[!] Halaman login tidak menunjukkan konfirmasi, tapi lanjut...")
                # Print 300 karakter pertama untuk debug
                log(f"    Preview: {r2.text[:300]}")
                return True
        else:
            log(f"[✗] Login gagal! HTTP {r2.status_code}")
            return False
    except Exception as e:
        log(f"[✗] Error login: {e}")
        return False

# =============================================
# AMBIL DAFTAR KOMIK dari web.mgkomik.cc
# =============================================
def get_komik_list(page=1):
    log(f"[*] Ambil daftar komik halaman {page}...")

    # Coba berbagai endpoint daftar komik
    urls_to_try = [
        f"{BASE_URL}/komik?page={page}",
        f"{BASE_URL}/manga?page={page}",
        f"{BASE_URL}/daftar-komik?page={page}",
        f"{BASE_URL}/?page={page}",
    ]

    for url in urls_to_try:
        try:
            r = session.get(url, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            links = []

            # Selector 1: link yang mengandung /komik/ atau /manga/
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if any(pat in href for pat in ["/komik/", "/manga/", "/manhwa/", "/manhua/"]):
                    if "/chapter" not in href and "#" not in href:
                        full = href if href.startswith("http") else BASE_URL + href
                        if full not in links:
                            links.append(full)

            if links:
                links = list(set(links))
                log(f"    {len(links)} komik ditemukan dari {url}")
                return links
            else:
                log(f"    0 komik dari {url}, coba URL lain...")

        except Exception as e:
            log(f"    Error {url}: {e}")

    # Fallback: ambil dari halaman utama
    log("[*] Fallback: ambil dari halaman utama...")
    try:
        r = session.get(BASE_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if len(href) > 10 and "/chapter" not in href and "#" not in href:
                if any(pat in href for pat in ["/komik/", "/manga/", "/manhwa/", "/manhua/", "/series/"]):
                    full = href if href.startswith("http") else BASE_URL + href
                    if full not in links:
                        links.append(full)
        links = list(set(links))
        log(f"    {len(links)} komik dari halaman utama.")
        return links
    except Exception as e:
        log(f"[!] Fallback error: {e}")
        return []

# =============================================
# AMBIL DAFTAR CHAPTER
# =============================================
def get_chapter_list(komik_url):
    try:
        r = session.get(komik_url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        chapters = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "/chapter" in href or "/ch-" in href:
                full = href if href.startswith("http") else BASE_URL + href
                if full not in chapters:
                    chapters.append(full)
        return list(set(chapters))[:MAX_CHAPTERS_PER_KOMIK]
    except Exception as e:
        log(f"[!] Error chapter: {e}")
        return []

# =============================================
# KIRIM REACTION
# =============================================
def send_reaction(target_url, reaction_type="upvote"):
    reaction_map = {
        "upvote": 1, "funny": 2, "love": 3,
        "surprised": 4, "angry": 5, "sad": 6,
    }
    reaction_id = reaction_map.get(reaction_type, 1)

    try:
        r = session.get(target_url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Cari post_id dari berbagai atribut
        post_id = None
        for attr in ["data-post-id", "data-id", "data-comic-id", "data-chapter-id", "data-manga-id"]:
            el = soup.find(attrs={attr: True})
            if el:
                post_id = el.get(attr)
                break

        # Cari dari script tag
        if not post_id:
            for script in soup.find_all("script"):
                txt = script.string or ""
                m = re.search(r'(?:post_id|postId|comic_id|chapter_id)["\s:=]+([\d]+)', txt)
                if m:
                    post_id = m.group(1)
                    break

        # Fallback dari URL
        if not post_id:
            m = re.search(r'/(\d+)(?:/|$)', target_url)
            if m:
                post_id = m.group(1)

        if not post_id:
            log(f"    [!] post_id tidak ditemukan: {target_url}")
            return False

        payload = {"post_id": post_id, "reaction": reaction_id}
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": target_url,
            "Origin": BASE_URL,
        }

        # Coba beberapa endpoint API reaction
        for api in [
            f"{BASE_URL}/api/reaction",
            f"{BASE_URL}/reaction",
            f"{BASE_URL}/wp-admin/admin-ajax.php",
            f"{KOMENTAR}/api/reaction",
        ]:
            rr = session.post(api, json=payload, headers=headers, timeout=15)
            if rr.status_code == 200:
                log(f"    [✓] {reaction_type.upper()} → {target_url.split('/')[-1]}")
                return True

        log(f"    [✗] Semua endpoint gagal. Last: {rr.status_code}")
        return False

    except Exception as e:
        log(f"    [!] Exception: {e}")
        return False

# =============================================
# MAIN LOOP
# =============================================
def main():
    log("=" * 50)
    log("  MGKomik Auto Reaction Bot")
    log("=" * 50)
    log(f"  User       : {USERNAME}")
    log(f"  Login URL  : {LOGIN_URL}")
    log(f"  Reaction di: {BASE_URL}")
    log(f"  Reactions  : {REACTION_TYPES}")
    log(f"  Max Pages  : {MAX_PAGES}")
    log(f"  Max Chapter: {MAX_CHAPTERS_PER_KOMIK}")
    log("=" * 50)

    while True:
        if not login():
            log("[✗] Gagal login, coba lagi 60 detik...")
            time.sleep(60)
            continue

        total_ok = 0
        total_fail = 0

        for page in range(1, MAX_PAGES + 1):
            komik_list = get_komik_list(page)
            if not komik_list:
                log(f"[!] Tidak ada komik di halaman {page}.")
                break

            for komik_url in komik_list:
                log(f"\n[→] {komik_url}")

                reaction = random.choice(REACTION_TYPES)
                ok = send_reaction(komik_url, reaction)
                total_ok += 1 if ok else 0
                total_fail += 0 if ok else 1
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

                chapters = get_chapter_list(komik_url)
                log(f"    {len(chapters)} chapter")
                for ch_url in chapters:
                    reaction = random.choice(REACTION_TYPES)
                    ok = send_reaction(ch_url, reaction)
                    total_ok += 1 if ok else 0
                    total_fail += 0 if ok else 1
                    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        log(f"\n[✓] Ronde selesai! OK: {total_ok} | Gagal: {total_fail}")
        log(f"[*] Tunggu {LOOP_INTERVAL//60} menit lalu ulang...\n")
        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
