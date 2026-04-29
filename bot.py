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

DELAY_REACTION = 2   # detik antar reaction
DELAY_KOMIK    = 3   # detik antar komik
DELAY_PAGE     = 2   # detik antar halaman

MAX_PAGES   = 999  # scan semua halaman listing
MAX_CHAPTER = 999  # semua chapter

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
# SESSION
# =============================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
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
        log(f"    Status: {r2.status_code} | URL: {r2.url}")
        if "profile" in r2.url or any(c in r2.text.lower() for c in ["logout","keluar","dashboard","profil",USERNAME.lower()]):
            log("[✓] LOGIN BERHASIL!")
            return True
        log(f"[!] Login tidak pasti, lanjut... Preview: {r2.text[:200]}")
        return True
    except Exception as e:
        log(f"[✗] Error login: {e}")
        return False

# =============================================
# CARI API ENDPOINT KOMIK (auto-detect)
# =============================================
def find_api_and_komik_list(page=1):
    """
    MGKomik mungkin pakai:
    1. WordPress REST API
    2. Custom JSON API
    3. HTML biasa dengan server-side rendering
    Coba semua kemungkinan.
    """
    links = []

    # ---- CARA 1: WordPress REST API ----
    wp_endpoints = [
        f"{BASE_URL}/wp-json/wp/v2/posts?per_page=20&page={page}&_fields=link,slug",
        f"{BASE_URL}/wp-json/manga/v1/comics?page={page}&per_page=20",
        f"{BASE_URL}/wp-json/wp/v2/manga?per_page=20&page={page}&_fields=link,slug",
        f"{BASE_URL}/wp-json/wp/v2/manhwa?per_page=20&page={page}&_fields=link,slug",
    ]
    for ep in wp_endpoints:
        try:
            r = session.get(ep, timeout=15, headers={"Accept": "application/json"})
            if r.status_code == 200 and r.headers.get("content-type","").startswith("application/json"):
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        url = item.get("link") or item.get("url") or item.get("permalink") or ""
                        if url and url not in links:
                            links.append(url)
                    if links:
                        log(f"    [✓] API ditemukan: {ep} ({len(links)} komik)")
                        return links
        except:
            pass

    # ---- CARA 2: HTML langsung dari /komik/?page=N ----
    html_urls = [
        f"{LIST_URL}?page={page}",
        f"{LIST_URL}page/{page}/",
        f"{BASE_URL}/komik?page={page}",
        f"{BASE_URL}/manga?page={page}",
    ]
    for url in html_urls:
        try:
            r = session.get(url, timeout=20)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")

            # Coba berbagai selector
            selectors = [
                "a.series-title",
                "h3.mgklnk a",
                ".bsx a",
                ".bs a",
                ".bssx a",
                ".listupd a",
                ".seriestulist a",
                ".utao a",
                ".uta a",
                "div.bsx > a",
                "div.bs > a",
                "article a[href]",
                "h2 a[href]",
                "h3 a[href]",
            ]
            for sel in selectors:
                for a in soup.select(sel):
                    href = a.get("href","")
                    if href and "/chapter" not in href and "#" not in href:
                        full = href if href.startswith("http") else BASE_URL + href
                        if full not in links and BASE_URL in full:
                            links.append(full)
                if links:
                    break

            # Fallback: semua link yang mengandung /komik/ slug
            if not links:
                for a in soup.select("a[href]"):
                    href = a.get("href","")
                    if "/komik/" in href and "/chapter" not in href:
                        full = href if href.startswith("http") else BASE_URL + href
                        # Filter: bukan halaman listing itu sendiri
                        if full.rstrip("/") != LIST_URL.rstrip("/") and full not in links:
                            links.append(full)

            if links:
                log(f"    [✓] HTML scrape dari {url}: {len(links)} komik")
                return list(set(links))
            else:
                # Debug: print judul halaman
                title = soup.find("title")
                log(f"    [~] {url} -> 0 link | Title: {title.text if title else 'N/A'}")
        except Exception as e:
            log(f"    [!] Error {url}: {e}")

    # ---- CARA 3: Coba fetch dengan header Accept: application/json ----
    try:
        r = session.get(f"{LIST_URL}?page={page}", timeout=20, headers={
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        })
        ct = r.headers.get("content-type","")
        if "json" in ct:
            data = r.json()
            log(f"    [?] JSON response: {str(data)[:200]}")
    except:
        pass

    return []

# =============================================
# AMBIL SEMUA CHAPTER DARI HALAMAN KOMIK
# =============================================
def get_chapters(komik_url):
    try:
        r = session.get(komik_url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        chapters = []

        selectors = [
            "#chapterlist a",
            ".eplister a",
            ".cl a",
            ".chapterlist a",
            "ul.clstyle a",
            "div.epcheck a",
            "li.wp-manga-chapter a",
            "a[href*='/chapter']",
        ]
        for sel in selectors:
            for a in soup.select(sel):
                href = a.get("href","")
                if href and ("/chapter" in href or "/ch-" in href):
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
    reaction_map = {
        "upvote": 1, "funny": 2, "love": 3,
        "surprised": 4, "angry": 5, "sad": 6,
    }
    reaction_id = reaction_map.get(reaction_type, 1)

    try:
        r = session.get(target_url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # Cari post_id
        post_id = None
        for attr in ["data-post-id","data-id","data-comic-id","data-chapter-id","data-manga-id","data-entry-id"]:
            el = soup.find(attrs={attr: True})
            if el:
                post_id = el.get(attr)
                break
        if not post_id:
            for script in soup.find_all("script"):
                txt = script.string or ""
                m = re.search(r'(?:post_id|postId|comic_id|chapter_id|entry_id|"id")["\s:=>]+["\']?([\d]{3,})', txt)
                if m:
                    post_id = m.group(1)
                    break
        if not post_id:
            # Dari meta og:url atau canonical
            for tag in [soup.find("link", {"rel":"shortlink"}), soup.find("meta", {"property":"og:url"})]:
                if tag:
                    m = re.search(r'[?&]p=(\d+)', tag.get("href",tag.get("content","")))
                    if m:
                        post_id = m.group(1)
                        break
        if not post_id:
            post_id = target_url.rstrip("/").split("/")[-1]

        payload = {"post_id": post_id, "reaction": reaction_id}
        req_h = {
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
            f"{BASE_URL}/wp-admin/admin-ajax.php",
        ]
        for api in endpoints:
            try:
                rr = session.post(api, json=payload, headers=req_h, timeout=10)
                if rr.status_code == 200:
                    log(f"    [✓] {reaction_type.upper()} pid={post_id} | {rr.text[:60]}")
                    return True
            except:
                continue

        log(f"    [✗] Semua API gagal: {target_url.split('/')[-1]}")
        return False
    except Exception as e:
        log(f"    [!] {e}")
        return False

# =============================================
# PROSES 1 KOMIK (reaction komik + semua chapter)
# =============================================
def process_komik(komik_url, nomor):
    name = komik_url.rstrip("/").split("/")[-1]
    log(f"\n[{nomor}] ▶ {name}")

    r1 = random.choice(REACTION_TYPES)
    log(f"    Reaction halaman komik: {r1}")
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
        log(f"\n{'='*50}")
        log(f"[PAGE {page}] Mengambil daftar komik...")
        komik_list = find_api_and_komik_list(page)

        if not komik_list:
            log(f"[!] Halaman {page} kosong. Selesai.")
            break

        log(f"    {len(komik_list)} komik di halaman {page}")
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
