"""Jalankan ini dulu untuk cari tahu struktur HTML/API MGKomik"""
import requests
from bs4 import BeautifulSoup
import json

BASE_URL  = "https://web.mgkomik.cc"
LIST_URL  = "https://web.mgkomik.cc/komik/"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/122.0.0.0 Mobile Safari/537.36",
})

print("[1] Fetch halaman listing komik...")
r = session.get(LIST_URL, timeout=20)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"URL akhir: {r.url}")

soup = BeautifulSoup(r.text, "html.parser")
print(f"Title: {soup.title.text if soup.title else 'N/A'}")

# Print semua link a[href] yang mengandung /komik/
print("\n[2] Link komik ditemukan:")
links = []
for a in soup.select("a[href]"):
    href = a.get("href","")
    if "/komik/" in href and "/chapter" not in href:
        full = href if href.startswith("http") else BASE_URL + href
        if full not in links and full.rstrip("/") != LIST_URL.rstrip("/"):
            links.append(full)
            print(" ", full)
print(f"Total: {len(links)}")

# Print semua div/article yang mungkin jadi container komik
print("\n[3] Container elements (div/article/li count):")
for tag in ["article", "div", "li", "section"]:
    items = soup.find_all(tag)
    if items:
        classes = set()
        for item in items[:30]:
            c = " ".join(item.get("class",[]))
            if c:
                classes.add(c)
        if classes:
            print(f"  {tag}: {list(classes)[:10]}")

# Cek apakah ada JSON di dalam script
print("\n[4] Script JSON (10 karakter pertama tiap script):")
for i, s in enumerate(soup.find_all("script")[:10]):
    txt = (s.string or "")[:100]
    if txt.strip():
        print(f"  script[{i}]: {txt}")

# Print 2000 karakter HTML pertama untuk lihat struktur
print("\n[5] HTML body (2000 char pertama):")
body = soup.find("body")
if body:
    print(str(body)[:2000])
else:
    print(r.text[:2000])
