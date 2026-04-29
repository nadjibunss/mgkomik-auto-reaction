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
PASSWORD    = "sukasari05"

REACTION_TYPES = ["upvote", "funny", "love"]

DELAY_REACTION = 2
DELAY_KOMIK    = 3
NAV_TIMEOUT    = 90000
CF_WAIT        = 30

MAX_CHAPTER = 999

LOGIN_URL  = "https://komentar.mgkomik.cc/login.php"
BASE_URL   = "https://web.mgkomik.cc"
LIST_URL   = "https://web.mgkomik.cc/komik/"
KOMENTAR   = "https://komentar.mgkomik.cc"
COOKIE_FILE = "cookies.json"

# =============================================
# LOGGING
# =============================================
os.makedirs("logs", exist_ok=True)

def log(msg):
    print(msg, flush=True)
    with open("logs/bot.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# =============================================
# LOAD COOKIES
# =============================================
def load_cookies():
    if not os.path.exists(COOKIE_FILE):
        return [], ""
    with open(COOKIE_FILE) as f:
        data = json.load(f)
    ua = data.pop("_user_agent", "")
    cookies = []
    for k, v in data.items():
        cookies.append({
            "name": k,
            "value": v,
            "domain": ".mgkomik.cc",
            "path": "/",
        })
    return cookies, ua

# =============================================
# NAVIGASI SAFE
# =============================================
async def goto_safe(page, url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            # Tunggu CF selesai
            for i in range(CF_WAIT):
                title = await page.title()
                if any(x in title.lower() for x in ["just a moment", "tunggu", "checking", "sebentar"]):
                    if i % 5 == 0:
                        log(f"    [CF] {title} ({i+1}s)")
                    await asyncio.sleep(1)
                else:
                    break
            title = await page.title()
            if any(x in title.lower() for x in ["just a moment", "tunggu", "checking"]):
                log(f"    [!] CF masih block setelah {CF_WAIT}s")
                if attempt < retries:
                    await asyncio.sleep(5)
                    continue
                return False
            return True
        except Exception as e:
            log(f"    [nav err {attempt}] {e}")
            if attempt < retries:
                await asyncio.sleep(5)
    return False

# =============================================
# MAIN
# =============================================
async def run():
    cookies, saved_ua = load_cookies()
    ua = saved_ua or "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    log(f"[*] UA: {ua[:70]}")
    log(f"[*] Cookies loaded: {len(cookies)}")

    async with async_playwright() as p:
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
            user_agent=ua,
            viewport={"width": 390, "height": 844},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
            extra_http_headers={"Accept-Language": "id-ID,id;q=0.9"}
        )

        # Inject cookies dari HP ke context
        if cookies:
            await context.add_cookies(cookies)
            log(f"[*] {len(cookies)} cookies diinjek ke browser")

        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['id-ID','id','en-US']});
        """)
        if HAS_STEALTH:
            await stealth_async(page)

        # ---- LOGIN ----
        log("\n" + "="*50)
        log("[*] Login...")
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
                log("[✓] LOGIN BERHASIL!" if "profile" in page.url else "[!] Lanjut...")
            except Exception as e:
                log(f"[!] Login error: {e}")

        # ---- LISTING KOMIK ----
        log(f"\n[*] Listing komik dari {LIST_URL}")
        komik_list = []
        page_num = 1

        while True:
            url = f"{LIST_URL}?page={page_num}" if page_num > 1 else LIST_URL
            log(f"[PAGE {page_num}] {url}")
            ok = await goto_safe(page, url)
            if not ok:
                log("[!] CF masih block. Stop.")
                break

            await asyncio.sleep(2)
            title = await page.title()
            log(f"    Title: {title}")

            links = await page.eval_on_selector_all(
                "a[href]",
                """els => [...new Set(
                    els.map(e=>e.href)
                    .filter(h=>h.includes('/komik/') && !h.includes('/chapter') && !h.endsWith('/komik/'))
                )]"""
            )
            if not links:
                html_sample = await page.content()
                log(f"    [!] 0 komik. Sample: {html_sample[:300]}")
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

        # ---- PROSES KOMIK ----
        total = 0
        for komik_url in komik_list:
            total += 1
            name = komik_url.rstrip("/").split("/")[-1]
            log(f"\n[{total}] ▶ {name}")
            try:
                await goto_safe(page, komik_url)
                await asyncio.sleep(2)

                r1 = random.choice(REACTION_TYPES)
                await do_reaction(page, r1)
                await asyncio.sleep(DELAY_REACTION)

                chapters = await page.eval_on_selector_all(
                    "a[href]",
                    """els => [...new Set(els.map(e=>e.href).filter(h=>h.includes('/chapter')))]"""
                )
                chapters = sorted(chapters)[:MAX_CHAPTER]
                log(f"    Chapter: {len(chapters)}")

                for i, ch_url in enumerate(chapters, 1):
                    r2 = random.choice(REACTION_TYPES)
                    log(f"    [{i}/{len(chapters)}] {ch_url.split('/')[-1]} -> {r2}")
                    try:
                        await goto_safe(page, ch_url)
                        await asyncio.sleep(2)
                        await do_reaction(page, r2)
                        await asyncio.sleep(DELAY_REACTION)
                    except Exception as e:
                        log(f"    [!] Skip chapter: {e}")

                log(f"    ✓ {name}")
            except Exception as e:
                log(f"    [!] Skip: {e}")
            await asyncio.sleep(DELAY_KOMIK)

        log("\n" + "="*50)
        log(f"  SELESAI! Total: {total}")
        await browser.close()


async def do_reaction(page, reaction_type):
    reaction_map = {"upvote":1,"funny":2,"love":3,"surprised":4,"angry":5,"sad":6}
    rid = reaction_map.get(reaction_type, 1)
    url = page.url
    for sel in [f".reaction-{reaction_type}", f"[data-reaction='{reaction_type}']", f"[data-type='{reaction_type}']"]:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click()
                log(f"    [✓] klik {reaction_type}")
                return
        except: pass
    result = await page.evaluate(f"""
        async()=>{{
          for(const a of['/api/reaction','/wp-json/manga/v1/reaction','/reaction']){{
            try{{const r=await fetch(a,{{method:'POST',headers:{{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'}},body:JSON.stringify({{reaction:{rid},url:'{url}'}})}});if(r.ok)return'ok:'+a;}}catch(e){{}}
          }}return'no-api';
        }}
    """)
    log(f"    [fetch] {reaction_type} -> {result}")


if __name__ == "__main__":
    log("="*50)
    log("  MGKomik Auto Reaction (Playwright + Cookie Inject)")
    log(f"  User: {USERNAME} | Stealth: {HAS_STEALTH}")
    log("="*50)
    asyncio.run(run())
