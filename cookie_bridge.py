"""
Cookie Bridge v4 - Manual JS cookies
Cara kerja:
1. python3 cookie_bridge.py  -> muncul link
2. Buka web.mgkomik.cc di HP sampai halaman komik muncul
3. Di address bar ketik: javascript:fetch('http://IP:8899/cookies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookies:document.cookie,ua:navigator.userAgent})}).then(r=>r.json()).then(d=>alert(d.ok?'BOT AKTIF!':'Error:'+d.msg))
4. Bot langsung jalan!
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, threading, subprocess, urllib.request

PORT = 8899
COOKIE_FILE = "cookies.json"


class Handler(BaseHTTPRequestHandler):
    server_ip = "localhost"

    def log_message(self, fmt, *args):
        print(f"[HTTP] {fmt % args}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/bridge"):
            ip = Handler.server_ip
            js_cmd = f"javascript:fetch('http://{ip}:{PORT}/cookies',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{cookies:document.cookie,ua:navigator.userAgent}})}}).then(r=>r.json()).then(d=>alert(d.ok?'BOT AKTIF! Cek terminal server':'Error: '+d.msg))"
            html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MGKomik Bot Bridge</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:Arial;background:#0d0d1a;color:#fff;min-height:100vh;padding:20px;display:flex;align-items:flex-start;justify-content:center;}}
.card{{background:#16213e;border-radius:16px;padding:24px;width:100%;max-width:440px;margin-top:30px;}}
h2{{color:#e94560;font-size:20px;margin-bottom:6px;text-align:center;}}
.step{{background:#0f3460;border-radius:10px;padding:14px;margin:12px 0;font-size:13px;line-height:1.8;}}
.step b{{color:#e94560;font-size:14px;}}
.num{{background:#e94560;color:white;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-weight:bold;margin-right:6px;font-size:12px;}}
.code{{background:#0a0a1a;border:1px solid #333;border-radius:8px;padding:10px;font-size:11px;word-break:break-all;color:#6fcf97;margin-top:8px;cursor:pointer;user-select:all;}}
.btn{{background:#e94560;color:white;border:none;padding:14px;border-radius:10px;font-size:15px;font-weight:bold;cursor:pointer;width:100%;margin-top:4px;}}
.note{{color:#8892a4;font-size:11px;margin-top:6px;text-align:center;}}
.ok{{background:#0d2e1a;border:1px solid #27ae60;color:#6fcf97;border-radius:8px;padding:12px;margin-top:10px;display:none;text-align:center;}}
</style>
</head>
<body>
<div class="card">
  <h2>&#129302; MGKomik Bot Setup</h2>

  <div class="step">
    <span class="num">1</span><b>Buka web.mgkomik.cc</b><br>
    Klik tombol di bawah:
    <a href="https://web.mgkomik.cc/komik/" target="_blank">
      <button class="btn" style="margin-top:10px;">&#127760; Buka MGKomik</button>
    </a>
    <div class="note">Tunggu sampai halaman komik muncul (CF selesai)</div>
  </div>

  <div class="step">
    <span class="num">2</span><b>Kirim cookies ke server</b><br>
    Setelah halaman MGKomik terbuka, ketik/paste kode ini di <b>address bar</b> browser dan tekan Enter:
    <div class="code" onclick="copyJS()" id="jscode">{js_cmd}</div>
    <div class="note">&#128077; Klik kode di atas untuk copy otomatis</div>
  </div>

  <div class="step">
    <span class="num">3</span><b>Atau klik tombol ini</b> (kalau masih di tab yg sama):<br>
    <button class="btn" onclick="sendNow()" style="margin-top:10px;">&#128273; Kirim Cookies Sekarang</button>
    <div class="note">Hanya works kalau kamu sudah buka web.mgkomik.cc sebelumnya</div>
  </div>

  <div class="ok" id="ok">&#10003; <b>Cookies terkirim! Bot sedang jalan di server.</b></div>
</div>

<script>
const API = 'http://{ip}:{PORT}';

async function sendNow() {{
  try {{
    const r = await fetch(API + '/cookies', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{cookies: document.cookie, ua: navigator.userAgent}})
    }});
    const d = await r.json();
    if (d.ok) {{
      document.getElementById('ok').style.display = 'block';
      alert('BOT AKTIF! Cek terminal server');
    }} else {{
      alert('Error: ' + d.msg);
    }}
  }} catch(e) {{
    alert('Tidak bisa connect ke server: ' + e.message);
  }}
}}

function copyJS() {{
  const txt = document.getElementById('jscode').innerText;
  navigator.clipboard.writeText(txt).then(() => {{
    alert('Kode berhasil dicopy! Sekarang:\n1. Buka tab web.mgkomik.cc\n2. Tap address bar\n3. Hapus semua, paste kode\n4. Tekan Enter');
  }}).catch(() => {{
    // Select all
    const el = document.getElementById('jscode');
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    sel.removeAllRanges();
    sel.addRange(range);
    alert('Teks sudah diselect. Tekan Copy lalu paste di address bar MGKomik.');
  }});
}}
</script>
</body>
</html>"""
            self._html(html)
        elif self.path == "/ping":
            self._json({"ok": True, "msg": "pong"})
        elif self.path == "/status":
            self._json({"running": os.path.exists(".bot_running")})
        else:
            self._json({"ok": False, "msg": "not found"}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
        except:
            data = {}

        if self.path == "/cookies":
            raw = data.get("cookies", "")
            ua  = data.get("ua", "")
            parsed = {}
            for part in raw.split(";"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    parsed[k.strip()] = v.strip()
            print(f"[*] Cookies diterima: {list(parsed.keys())}")
            print(f"[*] cf_clearance: {'cf_clearance' in parsed}")
            if ua:
                parsed["_user_agent"] = ua
            with open(COOKIE_FILE, "w") as f:
                json.dump(parsed, f, indent=2)
            print(f"[*] Disimpan ke {COOKIE_FILE}")
            _start_bot()
            self._json({"ok": True, "msg": f"Bot aktif! Cookies: {len(parsed)}, cf_clearance: {'cf_clearance' in parsed}"})

        elif self.path == "/trigger":
            ua = data.get("ua", "")
            if ua:
                cookies = {}
                if os.path.exists(COOKIE_FILE):
                    try:
                        with open(COOKIE_FILE) as f:
                            cookies = json.load(f)
                    except: pass
                cookies["_user_agent"] = ua
                with open(COOKIE_FILE, "w") as f:
                    json.dump(cookies, f, indent=2)
            _start_bot()
            self._json({"ok": True})

        else:
            self._json({"ok": False, "msg": "not found"}, 404)

    def _html(self, html):
        b = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(b))
        self._cors()
        self.end_headers()
        self.wfile.write(b)

    def _json(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(b))
        self._cors()
        self.end_headers()
        self.wfile.write(b)


_bot_thread = None

def _start_bot():
    global _bot_thread
    if _bot_thread and _bot_thread.is_alive():
        print("[!] Bot sudah jalan!")
        return
    print("[*] Jalankan bot.py...")
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
        return "localhost"


if __name__ == "__main__":
    ip = get_ip()
    Handler.server_ip = ip
    print("=" * 50)
    print("  MGKomik Cookie Bridge v4")
    print("=" * 50)
    print(f"\n  BUKA DI CHROME HP: http://{ip}:{PORT}")
    print(f"  Ping test: http://{ip}:{PORT}/ping")
    print("=" * 50)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
