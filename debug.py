import cloudscraper
from bs4 import BeautifulSoup

LIST_URL = "https://web.mgkomik.cc/komik/"
BASE_URL = "https://web.mgkomik.cc"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "android", "mobile": True}
)

print("[1] Fetch halaman listing komik...")
r = scraper.get(LIST_URL, timeout=30)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"URL akhir: {r.url}")

from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, "html.parser")
print(f"Title: {soup.title.text if soup.title else 'N/A'}")

print("\n[2] Link /komik/ ditemukan:")
links = []
for a in soup.select("a[href]"):
    href = a.get("href","")
    if "/komik/" in href and "/chapter" not in href:
        full = href if href.startswith("http") else BASE_URL + href
        if full.rstrip("/") != LIST_URL.rstrip("/") and full not in links:
            links.append(full)
            print(" ", full)
print(f"Total: {len(links)}")

print("\n[3] HTML body (1500 char):")
if soup.body:
    print(str(soup.body)[:1500])
else:
    print(r.text[:1500])
