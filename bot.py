import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re

# =============================================
# KONFIGURASI
# =============================================
USERNAME = "Nasky"
PASSWORD = "sukasari05"  # SEGERA GANTI PASSWORD!

LOGIN_URL = "https://komentar.mgkomik.cc/masuk"
BASE_URL  = "https://web.mgkomik.cc"

# Reaction yang akan dipilih secara acak
# Pilihan: upvote, funny, love, surprised, angry, sad
REACTION_TYPES = ["upvote", "funny", "love"]

DELAY_MIN = 3
DELAY_MAX = 7

# Berapa banyak halaman komik yang mau di-scan (1 halaman ~20 komik)
MAX_PAGES = 2

# Berapa chapter per komik yang direact
MAX_CHAPTERS_PER_KOMIK = 5

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
    print("[*] Mencoba login ke MGKomik...")
    try:
        r = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        csrf = None
        t = soup.find("input", {"name": "_token"})
        if t:
            csrf = t.get("value")

        payload = {
            "username": USERNAME,
            "password": PASSWORD,
        }
        if csrf:
            payload["_token"] = csrf

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_URL,
            "Origin": "https://komentar.mgkomik.cc",
        }

        r2 = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True, timeout=15)

        # Cek apakah login berhasil
        if r2.status_code == 200:
            if any(k in r2.text.lower() for k in ["logout", "keluar", USERNAME.lower(), "dashboard", "profil"]):
                print("[✓] Login BERHASIL!")
                return True
            else:
                print("[!] Login mungkin gagal - tidak ditemukan tanda login. Lanjut coba...")
                return True  # tetap lanjut, mungkin session sudah tersimpan
        else:
            print(f"[✗] Login gagal! HTTP {r2.status_code}")
            return False
    except Exception as e:
        print(f"[✗] Error saat login: {e}")
        return False

# =============================================
# AMBIL DAFTAR KOMIK
# =============================================
def get_komik_list(page=1):
    print(f"[*] Mengambil daftar komik halaman {page}...")
    url = f"{BASE_URL}/komik?page={page}"
    try:
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if "/komik/" in href and "/chapter" not in href and href not in links:
                full = href if href.startswith("http") else BASE_URL + href
                links.append(full)
        links = list(set(links))
        print(f"    Ditemukan {len(links)} komik.")
        return links
    except Exception as e:
        print(f"[!] Error ambil komik list: {e}")
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
            if "/chapter" in href and href not in chapters:
                full = href if href.startswith("http") else BASE_URL + href
                chapters.append(full)
        return list(set(chapters))[:MAX_CHAPTERS_PER_KOMIK]
    except Exception as e:
        print(f"[!] Error ambil chapter: {e}")
        return []

# =============================================
# KIRIM REACTION
# =============================================
def send_reaction(target_url, reaction_type="upvote"):
    reaction_map = {
        "upvote":    1,
        "funny":     2,
        "love":      3,
        "surprised": 4,
        "angry":     5,
        "sad":       6,
    }
    reaction_id = reaction_map.get(reaction_type, 1)

    try:
        r = session.get(target_url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        # Coba ambil post_id dari berbagai atribut HTML
        post_id = None
        for attr in ["data-post-id", "data-id", "data-comic-id", "data-chapter-id"]:
            el = soup.find(attrs={attr: True})
            if el:
                post_id = el.get(attr)
                break

        # Fallback: ambil dari URL
        if not post_id:
            m = re.search(r'/(\d+)', target_url)
            if m:
                post_id = m.group(1)

        # Coba ambil dari script JSON LD atau meta
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
            print(f"    [!] post_id tidak ditemukan untuk: {target_url}")
            return False

        # Kirim ke API reaction
        api_url = f"{BASE_URL}/api/reaction"
        payload = {"post_id": post_id, "reaction": reaction_id}
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": target_url,
        }

        rr = session.post(api_url, json=payload, headers=headers, timeout=15)

        if rr.status_code == 200:
            print(f"    [✓] {reaction_type.upper()} → {target_url.split('/')[-1]}")
            return True
        else:
            # Coba endpoint alternatif
            api_url2 = f"{BASE_URL}/reaction"
            rr2 = session.post(api_url2, json=payload, headers=headers, timeout=15)
            if rr2.status_code == 200:
                print(f"    [✓] {reaction_type.upper()} (alt) → {target_url.split('/')[-1]}")
                return True
            print(f"    [✗] Gagal reaction {rr.status_code}: {rr.text[:80]}")
            return False

    except Exception as e:
        print(f"    [!] Exception reaction: {e}")
        return False

# =============================================
# MAIN
# =============================================
def main():
    print("="*50)
    print("  MGKomik Auto Reaction Bot")
    print("="*50)

    if not login():
        print("[✗] Bot berhenti karena gagal login.")
        return

    total_ok = 0
    total_fail = 0

    for page in range(1, MAX_PAGES + 1):
        komik_list = get_komik_list(page)
        if not komik_list:
            print(f"[!] Tidak ada komik di halaman {page}, stop.")
            break

        for komik_url in komik_list:
            print(f"\n[→] {komik_url}")

            # Reaction di halaman komik
            reaction = random.choice(REACTION_TYPES)
            ok = send_reaction(komik_url, reaction)
            if ok:
                total_ok += 1
            else:
                total_fail += 1
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

            # Reaction di tiap chapter
            chapters = get_chapter_list(komik_url)
            print(f"    {len(chapters)} chapter ditemukan")
            for ch_url in chapters:
                reaction = random.choice(REACTION_TYPES)
                ok = send_reaction(ch_url, reaction)
                if ok:
                    total_ok += 1
                else:
                    total_fail += 1
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    print("\n" + "="*50)
    print(f"  SELESAI! Berhasil: {total_ok} | Gagal: {total_fail}")
    print("="*50)

if __name__ == "__main__":
    main()
