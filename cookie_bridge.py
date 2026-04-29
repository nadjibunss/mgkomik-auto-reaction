"""
Cookie Bridge v2:
1. python3 cookie_bridge.py
2. Buka link di HP Chrome
3. Halaman redirect ke web.mgkomik.cc
4. Setelah CF selesai, halaman kirim cookies ke server
5. Bot jalan otomatis dengan cookies HP
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, threading, subprocess, urllib.request

PORT = 8899
COOKIE_FILE = "cookies.json"

# Halaman HTML yang akan dibuka di HP:
# - Redirect ke web.mgkomik.cc
# - Setelah CF selesai, kirim cookies balik ke server
BRIDGE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MGKomik Bot Bridge</title>
<style>
body{margin:0;font-family:Arial;background:#0f0f1a;color:white;display:flex;align-items:center;justify-content:center;min-height:100vh;}
.card{background:#1a1a2e;border-radius:16px;padding:30px 25px;max-width:380px;width:90%;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.5);}
h2{color:#e94560;margin:0 0 8px;font-size:22px;}
p{color:#aaa;font-size:13px;line-height:1.6;margin:8px 0;}
.btn{display:block;background:#e94560;color:white;border:none;padding:16px;border-radius:10px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;margin-top:20px;}
.btn:disabled{opacity:0.5;cursor:not-allowed;}
.status{margin-top:16px;padding:12px;border-radius:8px;font-size:13px;display:none;line-height:1.5;}
.ok{background:#1e6f3e;border:1px solid #27ae60;display:block;}
.wait{background:#7d4e00;border:1px solid #f39c12;display:block;}
.err{background:#6e1e1e;border:1px solid #e74c3c;display:block;}
.step{color:#f39c12;font-weight:bold;}
</style>
</head>
<body>
<div class="card">
  <h2>&#129302; MGKomik Bot</h2>
  <p>Klik tombol di bawah.<br>
  Browser akan buka <b>web.mgkomik.cc</b>,<br>
  tunggu sampai halaman komik muncul,<br>
  lalu cookies otomatis terkirim ke server.</p>
  <button class="btn" id="btn" onclick="bridge()">&#128273; Aktifkan Bot</button>
  <div class="status wait" id="st">Siap...</div>
</div>
<script>
const SERVER = location.origin;

async function bridge() {
  const btn = document.getElementById('btn');
  const st = document.getElementById('st');
  btn.disabled = true;

  function show(cls, msg) {
    st.className = 'status ' + cls;
    st.innerHTML = msg;
  }

  show('wait', '&#9203; <b>Step 1/3:</b> Membuka web.mgkomik.cc...<br>Jangan tutup popup!');

  // Buka mgkomik di popup
  const pw = window.open(
    'https://web.mgkomik.cc/komik/',
    'mgkomik',
    'width=400,height=600,scrollbars=yes'
  );

  if (!pw) {
    show('err', '&#10060; Popup diblok browser!<br>Izinkan popup untuk ' + location.hostname + ' lalu coba lagi.');
    btn.disabled = false;
    return;
  }

  show('wait', '&#9203; <b>Step 2/3:</b> Tunggu Cloudflare selesai...<br>(maks 30 detik)');

  // Tunggu popup load selesai (CF challenge + halaman komik)
  let ready = false;
  for (let i = 0; i < 35; i++) {
    await sleep(1000);
    try {
      const t = pw.document.title;
      if (t && !t.toLowerCase().includes('moment') && !t.toLowerCase().includes('tunggu') && !t.toLowerCase().includes('checking')) {
        ready = true;
        show('wait', '&#9203; <b>Step 3/3:</b> CF selesai! Mengambil cookies...');
        break;
      }
      show('wait', `&#9203; <b>Step 2/3:</b> Tunggu CF... (${i+1}s) | Title: ${t || '...'}`);
    } catch(e) {
      // Cross-origin belum accessible
      show('wait', `&#9203; <b>Step 2/3:</b> Loading... (${i+1}s)`);
    }
  }

  // Ambil cookies dari popup (same-origin trick via iframe redirect)
  // Cara: minta popup buka halaman bridge /getcookies
  let cookiesRaw = '';
  try {
    pw.location.href = SERVER + '/inject?next=' + encodeURIComponent('https://web.mgkomik.cc/komik/');
    await sleep(3000);
  } catch(e) {}

  // Kirim notif ke server bahwa HP sudah buka mgkomik
  try {
    const ua = navigator.userAgent;
    const resp = await fetch(SERVER + '/trigger', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ua: ua, ready: ready})
    });
    const d = await resp.json();
    if (d.ok) {
      try { pw.close(); } catch(e) {}
      show('ok', '&#10003; <b>Bot sudah aktif!</b><br>Cek terminal server kamu.');
    } else {
      show('err', '&#10060; Error: ' + d.msg);
      btn.disabled = false;
    }
  } catch(e) {
    show('err', '&#10060; Tidak bisa connect ke server: ' + e.message);
    btn.disabled = false;
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
</script>
</body>
</html>"""

# Halaman inject: dibuka oleh popup mgkomik.cc, kirim cookies balik ke server
INJECT_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>...</title></head>
<body>
<script>
(async function() {
  const c = document.cookie;
  await fetch('/cookies_from_mgkomik', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({cookies: c, ua: navigator.userAgent})
  });
  window.close();
})();
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[HTTP] {fmt % args}")

    def do_GET(self):
        if self.path == "/":
            self._html(BRIDGE_HTML)
        elif self.path.startswith("/inject"):
            self._html(INJECT_HTML)
        elif self.path == "/status":
            running = os.path.exists(".bot_running")
            self._json({"running": running})
        else:
            self.send_error(404)

    def do_POST(self):
        body = json.loads(self._body())

        if self.path == "/cookies_from_mgkomik":
            raw = body.get("cookies", "")
            ua  = body.get("ua", "")
            cookies = {}
            for part in raw.split(";"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    cookies[k.strip()] = v.strip()
            print(f"[*] Cookies dari mgkomik: {list(cookies.keys())}")
            _save_cookies(cookies, ua)
            self._json({"ok": True})

        elif self.path == "/trigger":
            ua = body.get("ua", "")
            print(f"[*] Trigger dari HP: ua={ua[:60]}")
            # Muat cookies yang sudah ada + jalankan bot
            _start_bot()
            self._json({"ok": True})

        else:
            self.send_error(404)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def _html(self, html):
        b = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(b))
        self.end_headers()
        self.wfile.write(b)

    def _json(self, data):
        b = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(b))
        self.end_headers()
        self.wfile.write(b)


def _save_cookies(cookies, ua=""):
    existing = {}
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE) as f:
                existing = json.load(f)
        except:
            pass
    existing.update(cookies)
    if ua:
        existing["_user_agent"] = ua
    with open(COOKIE_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"[*] Saved {len(existing)} cookies ke {COOKIE_FILE}")


_bot_thread = None

def _start_bot():
    global _bot_thread
    if _bot_thread and _bot_thread.is_alive():
        print("[!] Bot sudah jalan!")
        return
    print("[*] Menjalankan bot...")
    open(".bot_running", "w").close()
    def _run():
        subprocess.run(["python3", "bot.py"])
        try: os.remove(".bot_running")
        except: pass
        print("[*] Bot selesai.")
    _bot_thread = threading.Thread(target=_run, daemon=True)
    _bot_thread.start()


def get_ip():
    try:
        return urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
    except:
        return "IP_SERVER"


if __name__ == "__main__":
    ip = get_ip()
    print("=" * 50)
    print("  MGKomik Cookie Bridge v2")
    print("=" * 50)
    print(f"\n  \U0001f4f1 BUKA DI CHROME HP KAMU:")
    print(f"\n     http://{ip}:{PORT}\n")
    print("  Tekan 'Aktifkan Bot' → tunggu → selesai!")
    print("=" * 50)
    print()
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
