import asyncio
import random
import re
import os
import json
import time
from playwright.async_api import async_playwright

# =============================================
# KONFIGURASI
# =============================================
USERNAME    = "Nasky"
PASSWORD    = "sukasari05"  # GANTI PASSWORD!

REACTION_TYPES = ["upvote", "funny", "love"]

DELAY_REACTION = 2
DELAY_KOMIK    = 3
DELAY_NAVIGATE = 3  # tunggu setelah navigasi

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
# MAIN BOT
# =============================================
async def run():
    async with async_playwright() as p:
        # Launch Chromium headless - terlihat seperti browser nyata
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            viewport={"width": 390, "height": 844},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
        )
        page = await context.new_page()

        # Sembunyikan tanda automation
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)

        # ---- LOGIN ----
        log("\n" + "="*50)
        log(f"[*] Login ke {LOGIN_URL}")
        await page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)

        try:
            await page.fill('input[name="username"]', USERNAME)
            await page.fill('input[name="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(2)
            log(f"    URL setelah login: {page.url}")
            if "profile" in page.url or "dashboard" in page.url:
                log("[✓] LOGIN BERHASIL!")
            else:
                log("[!] Login mungkin berhasil, lanjut...")
        except Exception as e:
            log(f"[!] Error login: {e}")

        # ---- AMBIL DAFTAR KOMIK ----
        log(f"\n[*] Buka halaman listing: {LIST_URL}")
        komik_list = []
        page_num = 1

        while True:
            url = f"{LIST_URL}?page={page_num}" if page_num > 1 else LIST_URL
            log(f"\n[PAGE {page_num}] {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(DELAY_NAVIGATE)

                title = await page.title()
                log(f"    Title: {title}")

                if "just a moment" in title.lower():
                    log("    [!] Cloudflare challenge, tunggu...")
                    await asyncio.sleep(10)
                    await page.wait_for_load_state("networkidle", timeout=30000)

                # Ambil semua link komik
                links = await page.eval_on_selector_all(
                    "a[href]",
                    """els => els
                        .map(e => e.href)
                        .filter(h => h.includes('/komik/') && !h.includes('/chapter') && !h.endsWith('/komik/'))
                    """
                )
                links = list(set(links))
                if not links:
                    log(f"    [!] Tidak ada komik di halaman {page_num}. Selesai listing.")
                    break

                log(f"    [✓] {len(links)} komik di halaman {page_num}")
                komik_list.extend(links)
                page_num += 1

            except Exception as e:
                log(f"    [!] Error halaman {page_num}: {e}")
                break

        log(f"\n[*] Total komik: {len(komik_list)}")
        if not komik_list:
            log("[!] Tidak ada komik ditemukan. Stop.")
            await browser.close()
            return

        # ---- PROSES TIAP KOMIK ----
        total = 0
        for komik_url in komik_list:
            total += 1
            name = komik_url.rstrip("/").split("/")[-1]
            log(f"\n[{total}] ▶ {name}")

            try:
                # Buka halaman komik
                await page.goto(komik_url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(DELAY_NAVIGATE)

                # Reaction di halaman komik
                r1 = random.choice(REACTION_TYPES)
                log(f"    Reaction komik: {r1}")
                await do_reaction(page, r1)
                await asyncio.sleep(DELAY_REACTION)

                # Ambil chapter links
                chapters = await page.eval_on_selector_all(
                    "a[href]",
                    """els => els
                        .map(e => e.href)
                        .filter(h => h.includes('/chapter'))
                    """
                )
                chapters = sorted(list(set(chapters)))[:MAX_CHAPTER]
                log(f"    Chapter: {len(chapters)}")

                for i, ch_url in enumerate(chapters, 1):
                    ch_name = ch_url.rstrip("/").split("/")[-1]
                    r2 = random.choice(REACTION_TYPES)
                    log(f"    [{i}/{len(chapters)}] {ch_name} → {r2}")
                    try:
                        await page.goto(ch_url, wait_until="networkidle", timeout=60000)
                        await asyncio.sleep(DELAY_NAVIGATE)
                        await do_reaction(page, r2)
                        await asyncio.sleep(DELAY_REACTION)
                    except Exception as e:
                        log(f"    [!] Skip chapter: {e}")

                log(f"    ✓ Selesai: {name}")
            except Exception as e:
                log(f"    [!] Skip komik: {e}")

            await asyncio.sleep(DELAY_KOMIK)

        log("\n" + "="*50)
        log(f"  SELESAI! Total komik: {total}")
        log("="*50)
        await browser.close()


async def do_reaction(page, reaction_type):
    """Klik tombol reaction atau kirim via JS fetch"""
    reaction_map = {"upvote": 1, "funny": 2, "love": 3, "surprised": 4, "angry": 5, "sad": 6}
    reaction_id = reaction_map.get(reaction_type, 1)

    # Coba klik tombol reaction langsung
    selectors = [
        f".reaction-{reaction_type}",
        f"[data-reaction='{reaction_type}']",
        f"[data-type='{reaction_type}']",
        f".reaction[data-id='{reaction_id}']",
        f"button.{reaction_type}",
    ]
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click()
                log(f"    [✓] Klik reaction {reaction_type}")
                return
        except:
            pass

    # Fallback: kirim via fetch JS
    current_url = page.url
    result = await page.evaluate(f"""
        async () => {{
            const apis = [
                '/api/reaction',
                '/wp-json/manga/v1/reaction',
                '/reaction',
            ];
            for (const api of apis) {{
                try {{
                    const resp = await fetch(api, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}},
                        body: JSON.stringify({{reaction: {reaction_id}, url: '{current_url}'}})
                    }});
                    if (resp.ok) return 'ok:' + api;
                }} catch(e) {{}}
            }}
            return 'no-api';
        }}
    """)
    log(f"    [fetch] {reaction_type} → {result}")


if __name__ == "__main__":
    log("="*50)
    log("  MGKomik Auto Reaction Bot (Playwright)")
    log(f"  User: {USERNAME}")
    log("="*50)
    asyncio.run(run())
