"""
Cookie Bridge v5 - Works di balik proxy (cyfuture/jupyter/ngrok dll)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, threading, subprocess, urllib.request

PORT = 8899
COOKIE_FILE = "cookies.json"


class Handler(BaseHTTPRequestHandler):

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
        if self.path in ("/", "/bridge", "/proxy/8899/", "/proxy/8899"):
            # Pakai URL RELATIF agar works di balik proxy apapun
            html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MGKomik Bot Bridge</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial;background:#0d0d1a;color:#fff;min-height:100vh;padding:20px;display:flex;align-items:flex-start;justify-content:center;}
.card{background:#16213e;border-radius:16px;padding:24px;width:100%;max-width:440px;margin-top:20px;}
h2{color:#e94560;font-size:20px;margin-bottom:4px;text-align:center;}
.sub{color:#888;font-size:12px;text-align:center;margin-bottom:16px;}
.step{background:#0f3460;border-radius:10px;padding:14px;margin:10px 0;font-size:13px;line-height:1.8;}
.num{background:#e94560;color:white;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-weight:bold;margin-right:6px;font-size:12px;}
.btn{background:#e94560;color:white;border:none;padding:13px;border-radius:10px;font-size:15px;font-weight:bold;cursor:pointer;width:100%;margin-top:8px;}
.btn2{background:#0f3460;border:1px solid #e94560;color:#e94560;border:none;padding:11px;border-radius:10px;font-size:13px;cursor:pointer;width:100%;margin-top:6px;}
.note{color:#8892a4;font-size:11px;margin-top:5px;}
.box{margin-top:12px;padding:12px;border-radius:8px;display:none;font-size:13px;text-align:center;}
.ok{background:#0d2e1a;border:1px solid #27ae60;color:#6fcf97;display:block;}
.err{background:#2e0d0d;border:1px solid #e74c3c;color:#f47f7f;display:block;}
.wait{background:#2d2000;border:1px solid #f39c12;color:#f9c74f;display:block;}
</style>
</head>
<body>
<div class="card">
  <h2>&#129302; MGKomik Bot</h2>
  <p class="sub">Cookie Bridge v5</p>

  <div class="step">
    <span class="num">1</span><b>Buka MGKomik di tab baru</b>
    <a href="https://web.mgkomik.cc/komik/" target="_blank">
      <button class="btn">&#127760; Buka web.mgkomik.cc</button>
    </a>
    <p class="note">Tunggu sampai halaman komik muncul penuh (bukan loading CF)</p>
  </div>

  <div class="step">
    <span class="num">2</span><b>Kirim cookies ke server</b><br>
    Setelah MGKomik terbuka, kembali ke sini dan klik:
    <button class="btn2" onclick="sendFromHere()">&#128273; Kirim Cookies (Tab Ini)</button>
    <p class="note">Atau kalau mau lebih pasti, paste kode JS ini di address bar tab MGKomik:</p>
    <textarea id="jscode" onclick="this.select()" readonly style="width:100%;height:60px;background:#0a0a1a;color:#6fcf97;border:1px solid #333;border-radius:6px;padding:8px;font-size:10px;margin-top:6px;resize:none;"></textarea>
    <button class="btn2" onclick="copyJS()">&#128203; Copy Kode JS</button>
  </div>

  <div class="box" id="result"></div>
</div>

<script>
// Pakai URL RELATIF - works di proxy manapun!
const BASE = location.origin + (location.pathname.includes('/proxy/') ? location.pathname.split('/proxy/')[0] + '/proxy/8899' : '');

// Generate JS command untuk dipaste di address bar MGKomik
const jsCmd = `javascript:fetch('${BASE}/cookies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookies:document.cookie,ua:navigator.userAgent})}).then(r=>r.json()).then(d=>alert(d.ok?'BOT AKTIF! '+d.msg:'Error: '+d.msg)).catch(e=>alert('Error: '+e.message))`;
document.getElementById('jscode').value = jsCmd;

function show(cls, msg) {
  const el = document.getElementById('result');
  el.className = 'box ' + cls;
  el.innerHTML = msg;
}

async function sendFromHere() {
  show('wait', '&#9203; Mengirim cookies...');
  try {
    const r = await fetch(BASE + '/cookies', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({cookies: document.cookie, ua: navigator.userAgent})
    });
    const d = await r.json();
    if (d.ok) {
      show('ok', '&#10003; <b>Berhasil!</b> ' + d.msg);
    } else {
      show('err', '&#10060; ' + d.msg);
    }
  } catch(e) {
    show('err', '&#10060; ' + e.message + '<br><small>Coba metode JS di address bar MGKomik</small>');
  }
}

function copyJS() {
  const ta = document.getElementById('jscode');
  ta.select();
  document.execCommand('copy');
  alert('Kode JS berhasil dicopy!\n\nLangkah:\n1. Buka tab web.mgkomik.cc\n2. Tap address bar\n3. Hapus semua\n4. Paste kode JS\n5. Tekan Enter');
}
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
            has_cf = "cf_clearance" in parsed
            print(f"[*] cf_clearance: {has_cf}")
            if ua:
                parsed["_user_agent"] = ua
            with open(COOKIE_FILE, "w") as f:
                json.dump(parsed, f, indent=2)
            print(f"[*] Saved {len(parsed)} cookies")
            _start_bot()
            msg = f"{len(parsed)} cookies, cf_clearance={'ADA' if has_cf else 'TIDAK ADA'}"
            self._json({"ok": True, "msg": msg})

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


if __name__ == "__main__":
    print("=" * 50)
    print("  MGKomik Cookie Bridge v5")
    print("=" * 50)
    print(f"  Port: {PORT}")
    print(f"  Akses via proxy URL cloud kamu")
    print("=" * 50)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
