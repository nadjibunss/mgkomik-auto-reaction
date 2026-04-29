import asyncio
import random
import re
import os
import json
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

# =============================================
# KONFIGURASI
# =============================================
USERNAME    = "Nasky"
PASSWORD    = "sukasari05"  # GANTI PASSWORD!

REACTION_TYPES = ["upvote", "funny", "love"]

DELAY_REACTION   = 2
DELAY_KOMIK      = 3
NAV_TIMEOUT      = 120000  # 2 menit timeout navigasi
CF_WAIT          = 15      # detik tunggu Cloudflare challenge selesai

MAX_CHAPTER = 999

LOGIN_URL = "https://komentar.mgkomik.cc/login.php"
BASE_URL  = "https://web.mgkomik.cc"
LIST_URL  = "https://web.mgkomik.cc/komik/"
KOMENTAR  = "https://komentar.mgkomik.cc"

# =============================================
# LOGGING
# =============================================
os.makedirs("logs", exist_ok=True)

def log(msg):
    print(msg, flush=True)
    with open("logs/bot.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# =============================================
# NAVIGASI DENGAN BYPASS CLOUDFLARE
# =============================================
async def goto_safe(page, url, retries=3):
    """Navigasi ke URL, tunggu Cloudflare challenge selesai."""
    for attempt in range(1, retries + 1):
        try:
            log(f"    [nav] {url} (attempt {attempt})")
            # Pakai domcontentloaded bukan networkidle (tidak hang di CF)
            await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)

            # Cek apakah Cloudflare challenge muncul
            for _ in range(CF_WAIT):
                title = await page.title()
                if "just a moment" in title.lower() or "checking" in title.lower():
                    log(f"    [CF] Cloudflare challenge, tunggu... ({_+1}s)")
                    await asyncio.sleep(1)
                    # Coba klik tombol verify kalau ada
                    try:
                        btn = await page.query_selector("input[type='button'], button[type='button']")
                        if btn:
                            await btn.click()
                    except:
                        pass
                else:
                    break

            title = await page.title()
            if "just a moment" in title.lower():
                log(f"    [!] CF masih aktif setelah {CF_WAIT}s")
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
            return True
        except Exception as e:
            log(f"    [!] Nav error attempt {attempt}: {e}")
            if attempt < retries:
                await asyncio.sleep(5)
    return False

# =============================================
# MAIN BOT
# =============================================
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=390,844",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            viewport={"width": 390, "height": 844},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
            extra_http_headers={
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
            }
        )
        page = await context.new_page()

        # Anti-detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'languages', {get: () => ['id-ID', 'id', 'en-US']});
        """)

        if HAS_STEALTH:
            await stealth_async(page)
            log("[*] Stealth mode aktif")

        # ---- LOGIN ----
        log("\n" + "="*50)
        log(f"[*] Login ke {LOGIN_URL}")
        ok = await goto_safe(page, LOGIN_URL)
        if ok:
            try:
                await page.fill('input[name="username"]', USERNAME)
                await asyncio.sleep(0.5)
                await page.fill('input[name="password"]', PASSWORD)
                await asyncio.sleep(0.5)
                await page.click('button[type="submit"], input[type="submit"]')
                await asyncio.sleep(3)
                log(f"    URL: {page.url}")
                if "profile" in page.url:
                    log("[✓] LOGIN BERHASIL!")
                else:
                    log("[!] Lanjut...")
            except Exception as e:
                log(f"[!] Login error: {e}")

        # ---- AMBIL DAFTAR KOMIK ----
        log(f"\n[*] Buka listing: {LIST_URL}")
        komik_list = []
        page_num = 1

        while True:
            url = f"{LIST_URL}?page={page_num}" if page_num > 1 else LIST_URL
            log(f"\n[PAGE {page_num}]")
            ok = await goto_safe(page, url)
            if not ok:
                log(f"    [!] Gagal buka halaman {page_num}")
                break

            await asyncio.sleep(2)
            title = await page.title()
            log(f"    Title: {title}")

            if "just a moment" in title.lower():
                log("    [!] Cloudflare tidak bisa dilewati. Coba lagi nanti.")
                break

            links = await page.eval_on_selector_all(
                "a[href]",
                """els => [...new Set(
                    els.map(e=>e.href)
                    .filter(h => h.includes('/komik/') && !h.includes('/chapter') && !h.endsWith('/komik/'))
                )]"""
            )

            if not links:
                log(f"    [!] Tidak ada komik, selesai listing.")
                # Print 500 char HTML untuk debug
                html = await page.content()
                log(f"    HTML sample: {html[:500]}")
                break

            log(f"    [✓] {len(links)} komik")
            komik_list.extend(links)
            page_num += 1
            await asyncio.sleep(2)

        log(f"\n[*] Total komik: {len(komik_list)}")
        if not komik_list:
            log("[!] Tidak ada komik. Stop.")
            await browser.close()
            return

        # ---- PROSES TIAP KOMIK ----
        total = 0
        for komik_url in komik_list:
            total += 1
            name = komik_url.rstrip("/").split("/")[-1]
            log(f"\n[{total}] ▶ {name}")
            try:
                await goto_safe(page, komik_url)
                await asyncio.sleep(2)
                r1 = random.choice(REACTION_TYPES)
                log(f"    Reaction: {r1}")
                await do_reaction(page, r1)
                await asyncio.sleep(DELAY_REACTION)

                chapters = await page.eval_on_selector_all(
                    "a[href]",
                    """els => [...new Set(els.map(e=>e.href).filter(h=>h.includes('/chapter')))]"""
                )
                chapters = sorted(chapters)[:MAX_CHAPTER]
                log(f"    Chapter: {len(chapters)}")

                for i, ch_url in enumerate(chapters, 1):
                    ch_name = ch_url.rstrip("/").split("/")[-1]
                    r2 = random.choice(REACTION_TYPES)
                    log(f"    [{i}/{len(chapters)}] {ch_name} → {r2}")
                    try:
                        await goto_safe(page, ch_url)
                        await asyncio.sleep(2)
                        await do_reaction(page, r2)
                        await asyncio.sleep(DELAY_REACTION)
                    except Exception as e:
                        log(f"    [!] Skip chapter: {e}")

                log(f"    ✓ Selesai: {name}")
            except Exception as e:
                log(f"    [!] Skip komik: {e}")
            await asyncio.sleep(DELAY_KOMIK)

        log("\n" + "="*50)
        log(f"  SELESAI! Total: {total}")
        await browser.close()


async def do_reaction(page, reaction_type):
    reaction_map = {"upvote": 1, "funny": 2, "love": 3, "surprised": 4, "angry": 5, "sad": 6}
    reaction_id = reaction_map.get(reaction_type, 1)
    current_url = page.url

    for sel in [
        f".reaction-{reaction_type}",
        f"[data-reaction='{reaction_type}']",
        f"[data-type='{reaction_type}']",
        f".reaction[data-id='{reaction_id}']",
    ]:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click()
                log(f"    [✓] Klik {reaction_type}")
                return
        except:
            pass

    result = await page.evaluate(f"""
        async () => {{
            for (const api of ['/api/reaction','/wp-json/manga/v1/reaction','/reaction']) {{
                try {{
                    const r = await fetch(api, {{
                        method:'POST',
                        headers:{{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'}},
                        body: JSON.stringify({{reaction:{reaction_id},url:'{current_url}'}})
                    }});
                    if(r.ok) return 'ok:'+api;
                }} catch(e) {{}}
            }}
            return 'no-api';
        }}
    """)
    log(f"    [fetch] {reaction_type} → {result}")


if __name__ == "__main__":
    log("="*50)
    log("  MGKomik Auto Reaction Bot (Playwright Stealth)")
    log(f"  User: {USERNAME}")
    log(f"  Stealth: {HAS_STEALTH}")
    log("="*50)
    asyncio.run(run())
