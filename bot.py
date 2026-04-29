import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re
import os

# =============================================
# KONFIGURASI (bisa diset lewat ENV variable)
# =============================================
USERNAME       = os.environ.get("USERNAME", "Nasky")
PASSWORD       = os.environ.get("PASSWORD", "sukasari05")
REACTION_STR   = os.environ.get("REACTION_TYPES", "upvote,funny,love")
REACTION_TYPES = [r.strip() for r in REACTION_STR.split(",")]
MAX_PAGES      = int(os.environ.get("MAX_PAGES", 2))
MAX_CHAPTERS_PER_KOMIK = int(os.environ.get("MAX_CHAPTERS_PER_KOMIK", 5))
DELAY_MIN      = float(os.environ.get("DELAY_MIN", 3))
DELAY_MAX      = float(os.environ.get("DELAY_MAX", 7))

LOGIN_URL = "https://komentar.mgkomik.cc/masuk"
BASE_URL  = "https://web.mgkomik.cc"

# =============================================
# LOGGING
# =============================================
os.makedirs("logs", exist_ok=True)

def log(msg):
    print(msg, flush=True)
    with open("logs/bot.log", "a") as f:
        f.write(msg + "\n")

# =============================================
# SESSION
# =============================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Referer": BASE_URL,
})

# =============================================
# LOGIN
# =============================================
def login():
    log("[*] Mencoba login ke MGKomik...")
    try:
        r = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        csrf = None
        t = soup.find("input", {"name": "_token"})
        if t:
            csrf = t.get("value")

        payload = {"username": USERNAME, "password": PASSWORD}
        if csrf:
            payload["_token"] = csrf

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_URL,
            "Origin": "https://komentar.mgkomik.cc",
        }

        r2 = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True, timeout=15)

        if r2.status_code == 200:
            if any(k in r2.text.lower() for k in ["logout", "keluar", USERNAME.lower(), "dashboard", "profil"]):
                log("[✓] Login BERHASIL!")
                return True
            else:
                log("[!] Login mungkin berhasil (lanjut...)")
                return True
        else:
            log(f"[✗] Login gagal! HTTP {r2.status_code}")
            return False
    except Exception as e:
        log(f"[✗] Error login: {e}")
        return False

# =============================================
# AMBIL DAFTAR KOMIK
# =============================================
def get_komik_list(page=1):
    log(f"[*] Ambil daftar komik halaman {page}...")
    url = f"{BASE_URL}/komik?page={page}"
    try:
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "/komik/" in href and "/chapter" not in href:
                full = href if href.startswith("http") else BASE_URL + href
                if full not in links:
                    links.append(full)
        links = list(set(links))
        log(f"    {len(links)} komik ditemukan.")
        return links
    except Exception as e:
        log(f"[!] Error komik list: {e}")
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
            if "/chapter" in href:
                full = href if href.startswith("http") else BASE_URL + href
                if full not in chapters:
                    chapters.append(full)
        return list(set(chapters))[:MAX_CHAPTERS_PER_KOMIK]
    except Exception as e:
        log(f"[!] Error chapter list: {e}")
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

        post_id = None
        for attr in ["data-post-id", "data-id", "data-comic-id", "data-chapter-id"]:
            el = soup.find(attrs={attr: True})
            if el:
                post_id = el.get(attr)
                break

        if not post_id:
            m = re.search(r'/(\d+)', target_url)
            if m:
                post_id = m.group(1)

        if not post_id:
            for script in soup.find_all("script", {"type": "application/json"}):
                try:
                    d = json.loads(script.string)
                    post_id = str(d.get("id", "") or d.get("post_id", ""))
                    if post_id:
                        break
                except:
                    pass

        if not post_id:
            log(f"    [!] post_id tidak ditemukan: {target_url}")
            return False

        payload = {"post_id": post_id, "reaction": reaction_id}
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": target_url,
        }

        for api in [f"{BASE_URL}/api/reaction", f"{BASE_URL}/reaction"]:
            rr = session.post(api, json=payload, headers=headers, timeout=15)
            if rr.status_code == 200:
                log(f"    [✓] {reaction_type.upper()} → {target_url.split('/')[-1]}")
                return True

        log(f"    [✗] Gagal reaction: {rr.status_code}")
        return False

    except Exception as e:
        log(f"    [!] Exception: {e}")
        return False

# =============================================
# MAIN LOOP
# =============================================
def main():
    log("=" * 50)
    log("  MGKomik Auto Reaction Bot (Docker)")
    log("=" * 50)
    log(f"  User      : {USERNAME}")
    log(f"  Reactions : {REACTION_TYPES}")
    log(f"  Max Pages : {MAX_PAGES}")
    log(f"  Max Ch/Komik: {MAX_CHAPTERS_PER_KOMIK}")
    log("=" * 50)

    while True:  # loop terus agar container tidak mati
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
        log("[*] Tunggu 30 menit lalu ulang...\n")
        time.sleep(1800)  # ulang tiap 30 menit

if __name__ == "__main__":
    main()
