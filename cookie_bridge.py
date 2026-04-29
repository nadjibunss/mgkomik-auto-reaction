"""
Cookie Bridge v3 - Fix CORS + endpoint
1. python3 cookie_bridge.py
2. Buka link di HP Chrome
3. Tekan Aktifkan Bot
4. Bot jalan otomatis
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, threading, subprocess, urllib.request

PORT = 8899
COOKIE_FILE = "cookies.json"

BRIDGE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MGKomik Bot Bridge</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial,sans-serif;background:#0d0d1a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}
.card{background:#16213e;border-radius:20px;padding:32px 24px;width:100%;max-width:400px;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,0.6);}
h2{color:#e94560;font-size:24px;margin-bottom:8px;}
.sub{color:#8892a4;font-size:13px;line-height:1.7;margin-bottom:24px;}
.btn{background:#e94560;color:#fff;border:none;padding:16px;border-radius:12px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;letter-spacing:.5px;transition:opacity .2s;}
.btn:disabled{opacity:.4;cursor:not-allowed;}
.box{margin-top:16px;padding:14px 16px;border-radius:10px;font-size:13px;line-height:1.6;display:none;}
.wait{background:#2d2000;border:1px solid #f39c12;color:#f9c74f;display:block;}
.ok{background:#0d2e1a;border:1px solid #27ae60;color:#6fcf97;display:block;}
.err{background:#2e0d0d;border:1px solid #e74c3c;color:#f47f7f;display:block;}
</style>
</head>
<body>
<div class="card">
  <h2>&#129302; MGKomik Bot</h2>
  <p class="sub">Klik tombol di bawah.<br>Browser akan buka <b>web.mgkomik.cc</b>,<br>tunggu CF selesai, lalu bot aktif otomatis.</p>
  <button class="btn" id="btn" onclick="bridge()">&#128273; Aktifkan Bot</button>
  <div class="box" id="box"></div>
</div>
<script>
const API = 'http://" + "{SERVER_IP}" + ":" + str(PORT) + "';

function show(cls, html) {
  const b = document.getElementById('box');
  b.className = 'box ' + cls;
  b.innerHTML = html;
}

async function bridge() {
  document.getElementById('btn').disabled = true;
  show('wait', '&#9203; <b>Step 1/3:</b> Membuka web.mgkomik.cc...<br><small>Izinkan popup jika diminta!</small>');

  const pw = window.open('https://web.mgkomik.cc/komik/', 'cf_window', 'width=420,height=650');
  if (!pw) {
    show('err', '&#10060; <b>Popup diblok!</b><br>Izinkan popup untuk halaman ini lalu coba lagi.<br><small>Settings > Site Settings > Pop-ups</small>');
    document.getElementById('btn').disabled = false;
    return;
  }

  // Tunggu CF challenge selesai (max 40 detik)
  show('wait', '&#9203; <b>Step 2/3:</b> Menunggu Cloudflare...<br><small>Jangan tutup popup!</small>');
  let title = '';
  for (let i = 1; i <= 40; i++) {
    await sleep(1000);
    try {
      title = pw.document.title || '';
      if (title && !/(just a moment|tunggu|checking|sebentar)/i.test(title)) {
        show('wait', `&#9203; <b>Step 2/3:</b> CF selesai! (${i}s)<br><small>Title: ${title}</small>`);
        break;
      }
      show('wait', `&#9203; <b>Step 2/3:</b> Menunggu CF... (${i}s)<br><small>${title || 'loading...'}</small>`);
    } catch(e) {
      show('wait', `&#9203; <b>Step 2/3:</b> Loading... (${i}s)`);
    }
  }

  // Kirim signal ke server
  show('wait', '&#9203; <b>Step 3/3:</b> Mengirim signal ke server...');
  await sleep(1000);

  const ua = navigator.userAgent;
  try {
    const r = await fetch(API + '/trigger', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ua: ua, title: title})
    });
    const d = await r.json();
    if (d.ok) {
      try { pw.close(); } catch(e) {}
      show('ok', '&#10003; <b>Berhasil! Bot sudah aktif di server.</b><br><small>Cek terminal server kamu.</small>');
    } else {
      show('err', '&#10060; Server error: ' + (d.msg || 'unknown'));
      document.getElementById('btn').disabled = false;
    }
  } catch(e) {
    show('err', '&#10060; <b>Tidak bisa connect:</b> ' + e.message + '<br><small>Pastikan cookie_bridge.py masih jalan di server.</small>');
    document.getElementById('btn').disabled = false;
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[HTTP] {fmt % args}")

    def _cors(self):
        """Tambah CORS headers agar fetch dari domain manapun bisa"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handle preflight CORS request"""
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/bridge":
            self._html(BRIDGE_HTML)
        elif self.path == "/ping":
            self._json({"ok": True, "msg": "pong"})
        elif self.path == "/status":
            running = os.path.exists(".bot_running")
            self._json({"running": running})
        else:
            self._json({"ok": False, "msg": "not found"}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
        except:
            data = {}

        if self.path == "/trigger":
            ua = data.get("ua", "")
            title = data.get("title", "")
            print(f"[*] Trigger dari HP")
            print(f"    UA  : {ua[:80]}")
            print(f"    Title mgkomik: {title}")

            # Simpan UA ke cookies.json
            cookies = {}
            if os.path.exists(COOKIE_FILE):
                try:
                    with open(COOKIE_FILE) as f:
                        cookies = json.load(f)
                except:
                    pass
            cookies["_user_agent"] = ua
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f, indent=2)

            _start_bot()
            self._json({"ok": True, "msg": "Bot berhasil dijalankan!"})

        elif self.path == "/cookies":
            raw = data.get("cookies", "")
            ua  = data.get("ua", "")
            parsed = {}
            for part in raw.split(";"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    parsed[k.strip()] = v.strip()
            print(f"[*] Cookies: {list(parsed.keys())}")
            if ua:
                parsed["_user_agent"] = ua
            with open(COOKIE_FILE, "w") as f:
                json.dump(parsed, f, indent=2)
            self._json({"ok": True})

        else:
            self._json({"ok": False, "msg": "endpoint not found"}, 404)

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
        return "IP_SERVER"


if __name__ == "__main__":
    ip = get_ip()

    # Inject IP ke HTML
    global BRIDGE_HTML
    BRIDGE_HTML = BRIDGE_HTML.replace("{SERVER_IP}", ip)

    print("=" * 50)
    print("  MGKomik Cookie Bridge v3")
    print("=" * 50)
    print(f"\n  \U0001f4f1 BUKA DI CHROME HP:")
    print(f"\n     http://{ip}:{PORT}")
    print(f"\n  \U0001f9ea Test ping: http://{ip}:{PORT}/ping")
    print("=" * 50)
    print()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stop.")
