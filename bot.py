import cloudscraper
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

MAX_CHAPTER = 999

LOGIN_URL  = "https://komentar.mgkomik.cc/login.php"
KOMENTAR   = "https://komentar.mgkomik.cc"
BASE_URL   = "https://web.mgkomik.cc"

# Sitemap URL candidates (tidak diproteksi Cloudflare biasanya)
SITEMAP_URLS = [
    "https://web.mgkomik.cc/sitemap.xml",
    "https://web.mgkomik.cc/sitemap_index.xml",
    "https://web.mgkomik.cc/wp-sitemap.xml",
    "https://web.mgkomik.cc/wp-sitemap-posts-wp-manga-1.xml",
    "https://web.mgkomik.cc/manga-sitemap.xml",
]

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
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "android", "mobile": True}
)
scraper.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
})

# Load cookies
COOKIE_FILE = "cookies.json"
if os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE) as f:
        saved_cookies = json.load(f)
    for k, v in saved_cookies.items():
        scraper.cookies.set(k, v, domain=".mgkomik.cc")
    log(f"[*] Loaded {len(saved_cookies)} cookies dari {COOKIE_FILE}")

# =============================================
# LOGIN
# =============================================
def login():
    log("\n" + "="*50)
    log(f"[*] Login ke {LOGIN_URL}")
    try:
        r = scraper.get(LOGIN_URL, timeout=30)
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
        r2 = scraper.post(LOGIN_URL, data=payload, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_URL,
            "Origin": KOMENTAR,
        }, allow_redirects=True, timeout=30)
        log(f"    {r2.status_code} | {r2.url}")
        if "profile" in r2.url or any(c in r2.text.lower() for c in ["logout",USERNAME.lower(),"profil"]):
            log("[✓] LOGIN BERHASIL!")
            return True
        log("[!] Lanjut...")
        return True
    except Exception as e:
        log(f"[✗] {e}")
        return False

# =============================================
# AMBIL KOMIK DARI SITEMAP XML
# =============================================
def get_komik_from_sitemap():
    """Coba semua sitemap URL. Sitemap XML tidak diblokir Cloudflare."""
    all_links = []

    for sm_url in SITEMAP_URLS:
        try:
            r = scraper.get(sm_url, timeout=30)
            log(f"    [{r.status_code}] {sm_url}")
            if r.status_code != 200:
                continue

            ct = r.headers.get("content-type","")
            # Kalau ini sitemap index, cari sub-sitemap
            if "xml" in ct or sm_url.endswith(".xml"):
                soup = BeautifulSoup(r.text, "xml")

                # Sitemap index
                sub_sitemaps = [loc.text for loc in soup.find_all("loc") if "sitemap" in loc.text.lower()]
                if sub_sitemaps:
                    log(f"    Found sitemap index, sub-sitemaps: {len(sub_sitemaps)}")
                    for sub in sub_sitemaps:
                        if "manga" in sub.lower() or "komik" in sub.lower() or "comic" in sub.lower():
                            try:
                                r2 = scraper.get(sub, timeout=30)
                                soup2 = BeautifulSoup(r2.text, "xml")
                                for loc in soup2.find_all("loc"):
                                    url = loc.text
                                    if "/komik/" in url and "/chapter" not in url:
                                        if url not in all_links:
                                            all_links.append(url)
                            except:
                                pass

                # Langsung komik di sitemap ini
                for loc in soup.find_all("loc"):
                    url = loc.text
                    if "/komik/" in url and "/chapter" not in url and url not in all_links:
                        all_links.append(url)

                if all_links:
                    log(f"    [✓] {len(all_links)} komik dari sitemap")
                    return all_links

        except Exception as e:
            log(f"    [!] Error {sm_url}: {e}")

    # Fallback: coba ambil dari API WordPress
    log("\n[*] Coba WP REST API...")
    page = 1
    while True:
        try:
            api_urls = [
                f"{BASE_URL}/wp-json/wp/v2/wp-manga?per_page=100&page={page}&_fields=link",
                f"{BASE_URL}/wp-json/wp/v2/manga?per_page=100&page={page}&_fields=link",
                f"{BASE_URL}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=link&categories_exclude=0",
            ]
            found = False
            for api in api_urls:
                r = scraper.get(api, timeout=30, headers={"Accept": "application/json"})
                if r.status_code == 200:
                    try:
                        data = r.json()
                        if isinstance(data, list) and len(data) > 0:
                            for item in data:
                                url = item.get("link","")
                                if url and url not in all_links:
                                    all_links.append(url)
                            log(f"    [API pg{page}] +{len(data)} komik")
                            found = True
                            break
                    except:
                        pass
            if not found:
                break
            page += 1
            if page > 50:
                break
        except Exception as e:
            log(f"    [!] API error: {e}")
            break

    return all_links

# =============================================
# AMBIL CHAPTER
# =============================================
def get_chapters(komik_url):
    try:
        r = scraper.get(komik_url, timeout=30)
        if r.status_code == 403:
            log(f"    [!] 403 chapter page: {komik_url.split('/')[-1]}")
            return []
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
    log("\n[*] Mengambil daftar komik dari sitemap...")
    komik_list = get_komik_from_sitemap()
    log(f"[*] Total komik ditemukan: {len(komik_list)}")
    if not komik_list:
        log("[!] Tidak ada komik ditemukan. Stop.")
        log("    Kemungkinan: semua endpoint diblok Cloudflare.")
        return
    total = 0
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
