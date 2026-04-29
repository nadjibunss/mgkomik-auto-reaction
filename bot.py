import cloudscraper
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import os
import json

# =============================================
# KONFIGURASI
# =============================================
USERNAME    = "Nasky"
PASSWORD    = "sukasari05"  # GANTI PASSWORD!

REACTION_TYPES = ["upvote", "funny", "love"]  # upvote funny love surprised angry sad

DELAY_REACTION = 2
DELAY_KOMIK    = 3
DELAY_PAGE     = 2

MAX_PAGES   = 999
MAX_CHAPTER = 999

LOGIN_URL  = "https://komentar.mgkomik.cc/login.php"
KOMENTAR   = "https://komentar.mgkomik.cc"
BASE_URL   = "https://web.mgkomik.cc"
LIST_URL   = "https://web.mgkomik.cc/komik/"

# =============================================
# LOGGING
# =============================================
os.makedirs("logs", exist_ok=True)

def log(msg):
    print(msg, flush=True)
    with open("logs/bot.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# =============================================
# SESSION - pakai cloudscraper + inject cf_clearance
# =============================================
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "android", "mobile": True}
)
scraper.headers.update({
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
})

# Load cookies dari file jika ada
COOKIE_FILE = "cookies.json"
if os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE) as f:
        saved = json.load(f)
    cf = saved.get("cf_clearance","")
    if cf:
        scraper.cookies.set("cf_clearance", cf, domain=".mgkomik.cc")
        log(f"[*] Loaded cf_clearance dari {COOKIE_FILE}")

# =============================================
# LOGIN
# =============================================
def login():
    log("\n" + "="*50)
    log(f"[*] Login ke {LOGIN_URL}")
    try:
        r = scraper.get(LOGIN_URL, timeout=30)
        log(f"    GET status: {r.status_code}")
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
        r2 = scraper.post(LOGIN_URL, data=payload, headers=h, allow_redirects=True, timeout=30)
        log(f"    POST status: {r2.status_code} | URL: {r2.url}")
        if "profile" in r2.url or any(c in r2.text.lower() for c in ["logout","keluar",USERNAME.lower(),"dashboard","profil"]):
            log("[✓] LOGIN BERHASIL!")
            return True
        log(f"[!] Lanjut... Preview: {r2.text[:200]}")
        return True
    except Exception as e:
        log(f"[✗] Error login: {e}")
        return False

# =============================================
# AMBIL DAFTAR KOMIK
# =============================================
def get_komik_list(page=1):
    urls = [
        f"{LIST_URL}?page={page}",
        f"{LIST_URL}page/{page}/",
        f"{BASE_URL}/komik?page={page}",
    ]
    for url in urls:
        try:
            r = scraper.get(url, timeout=30)
            log(f"    [{r.status_code}] {url}")
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.text if soup.title else "N/A"
            if "just a moment" in title.lower():
                log(f"    [!] Masih kena Cloudflare. Perlu cf_clearance baru.")
                log(f"    Jalankan: python3 get_cookies.py")
                continue
            log(f"    Title: {title}")
            links = []
            for sel in [".bsx a",".bs a","div.bsx > a",".listupd .bsx a",
                        ".seriestulist a","article a[href]",".utao .uta a",
                        "h3 a[href]","h2 a[href]",".tt a"]:
                for a in soup.select(sel):
                    href = a.get("href","")
                    if href and "/komik/" in href and "/chapter" not in href:
                        full = href if href.startswith("http") else BASE_URL + href
                        if full.rstrip("/") != LIST_URL.rstrip("/") and full not in links:
                            links.append(full)
                if links:
                    break
            if not links:
                for a in soup.select("a[href]"):
                    href = a.get("href","")
                    if "/komik/" in href and "/chapter" not in href and "#" not in href:
                        full = href if href.startswith("http") else BASE_URL + href
                        if full.rstrip("/") != LIST_URL.rstrip("/") and full not in links:
                            links.append(full)
            links = list(set(links))
            if links:
                log(f"    [✓] {len(links)} komik ditemukan")
                return links
            log(f"    [~] 0 komik. Sample: {str(soup.body)[:200] if soup.body else r.text[:200]}")
        except Exception as e:
            log(f"    [!] Error {url}: {e}")
    return []

# =============================================
# AMBIL CHAPTER
# =============================================
def get_chapters(komik_url):
    try:
        r = scraper.get(komik_url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        chapters = []
        for sel in ["#chapterlist a",".eplister a",".cl a",".chapterlist a",
                    "ul.clstyle a","li.wp-manga-chapter a","a[href*='/chapter']"]:
            for a in soup.select(sel):
                href = a.get("href","")
                if href and "/chapter" in href:
                    full = href if href.startswith("http") else BASE_URL + href
                    if full not in chapters:
                        chapters.append(full)
            if chapters:
                break
        chapters = list(set(chapters))
        chapters.sort()
        return chapters[:MAX_CHAPTER]
    except Exception as e:
        log(f"    [!] Error chapter: {e}")
        return []

# =============================================
# KIRIM REACTION
# =============================================
def send_reaction(target_url, reaction_type):
    reaction_map = {"upvote":1,"funny":2,"love":3,"surprised":4,"angry":5,"sad":6}
    reaction_id = reaction_map.get(reaction_type, 1)
    try:
        r = scraper.get(target_url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        post_id = None
        for attr in ["data-post-id","data-id","data-comic-id","data-chapter-id","data-manga-id"]:
            el = soup.find(attrs={attr: True})
            if el:
                post_id = el.get(attr)
                break
        if not post_id:
            for script in soup.find_all("script"):
                txt = script.string or ""
                m = re.search(r'(?:post_id|postId|comic_id|"id")["\s:=>]+["\']?([\d]{3,})', txt)
                if m:
                    post_id = m.group(1)
                    break
        if not post_id:
            tag = soup.find("link", {"rel":"shortlink"})
            if tag:
                m = re.search(r'[?&]p=(\d+)', tag.get("href",""))
                if m:
                    post_id = m.group(1)
        if not post_id:
            post_id = target_url.rstrip("/").split("/")[-1]
        payload = {"post_id": post_id, "reaction": reaction_id}
        req_h = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": target_url,
            "Origin": BASE_URL,
        }
        for api in [
            f"{BASE_URL}/api/reaction",
            f"{BASE_URL}/wp-json/manga/v1/reaction",
            f"{BASE_URL}/reaction",
            f"{KOMENTAR}/api/reaction",
        ]:
            try:
                rr = scraper.post(api, json=payload, headers=req_h, timeout=15)
                if rr.status_code == 200:
                    log(f"    [✓] {reaction_type.upper()} pid={post_id} | {rr.text[:60]}")
                    return True
            except:
                continue
        log(f"    [✗] API gagal: {target_url.split('/')[-1]}")
        return False
    except Exception as e:
        log(f"    [!] {e}")
        return False

# =============================================
# PROSES 1 KOMIK
# =============================================
def process_komik(komik_url, nomor):
    name = komik_url.rstrip("/").split("/")[-1]
    log(f"\n[{nomor}] ▶ {name}")
    r1 = random.choice(REACTION_TYPES)
    log(f"    Reaction komik: {r1}")
    send_reaction(komik_url, r1)
    time.sleep(DELAY_REACTION)
    chapters = get_chapters(komik_url)
    log(f"    Chapter: {len(chapters)}")
    for i, ch in enumerate(chapters, 1):
        r2 = random.choice(REACTION_TYPES)
        log(f"    [{i}/{len(chapters)}] {ch.split('/')[-1]} → {r2}")
        send_reaction(ch, r2)
        time.sleep(DELAY_REACTION)
    log(f"    ✓ Selesai: {name}")

# =============================================
# MAIN
# =============================================
def main():
    log("="*50)
    log("  MGKomik Auto Reaction Bot")
    log(f"  User      : {USERNAME}")
    log(f"  Reactions : {REACTION_TYPES}")
    log("="*50)
    if not login():
        log("[✗] Gagal login. Stop.")
        return
    total = 0
    for page in range(1, MAX_PAGES + 1):
        log(f"\n{'='*40}")
        log(f"[PAGE {page}] Mengambil daftar komik...")
        komik_list = get_komik_list(page)
        if not komik_list:
            log(f"[!] Halaman {page} kosong. Selesai.")
            break
        log(f"    {len(komik_list)} komik")
        time.sleep(DELAY_PAGE)
        for komik_url in komik_list:
            total += 1
            try:
                process_komik(komik_url, total)
            except Exception as e:
                log(f"    [!] Skip: {e}")
            time.sleep(DELAY_KOMIK)
    log("\n" + "="*50)
    log(f"  SELESAI! Total komik: {total}")
    log("="*50)

if __name__ == "__main__":
    main()
