"""Debug: cek semua sitemap dan API endpoints"""
import cloudscraper
from bs4 import BeautifulSoup
import json

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "android", "mobile": True}
)
scraper.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36"
})

import os
if os.path.exists("cookies.json"):
    with open("cookies.json") as f:
        for k,v in json.load(f).items():
            scraper.cookies.set(k, v, domain=".mgkomik.cc")
    print("[OK] Cookies loaded")

urls_to_test = [
    "https://web.mgkomik.cc/sitemap.xml",
    "https://web.mgkomik.cc/sitemap_index.xml",
    "https://web.mgkomik.cc/wp-sitemap.xml",
    "https://web.mgkomik.cc/wp-sitemap-posts-wp-manga-1.xml",
    "https://web.mgkomik.cc/robots.txt",
    "https://web.mgkomik.cc/wp-json/wp/v2/wp-manga?per_page=3&_fields=link",
    "https://web.mgkomik.cc/wp-json/wp/v2/manga?per_page=3&_fields=link",
]

for url in urls_to_test:
    try:
        r = scraper.get(url, timeout=15)
        ct = r.headers.get("content-type","")
        preview = r.text[:200].replace("\n"," ")
        print(f"[{r.status_code}] {url}")
        print(f"  CT: {ct}")
        print(f"  Preview: {preview}")
        print()
    except Exception as e:
        print(f"[ERR] {url}: {e}")
        print()
