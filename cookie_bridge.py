"""
Cookie Bridge - Cara kerja:
1. Jalankan script ini di server: python3 cookie_bridge.py
2. Akan muncul LINK, buka link itu di browser HP kamu
3. Browser HP otomatis kirim cookies ke server
4. Bot langsung jalan otomatis
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import threading
import subprocess
import urllib.parse

PORT = 8899
COOKIE_FILE = "cookies.json"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MGKomik Bot - Cookie Bridge</title>
  <style>
    body {{ font-family: Arial; padding: 20px; background: #1a1a2e; color: white; text-align: center; }}
    .box {{ background: #16213e; border-radius: 12px; padding: 20px; margin: 20px auto; max-width: 400px; }}
    button {{ background: #e94560; color: white; border: none; padding: 15px 30px; border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; margin-top: 10px; }}
    .status {{ margin-top: 15px; padding: 10px; border-radius: 8px; }}
    .ok {{ background: #27ae60; }}
    .err {{ background: #c0392b; }}
  </style>
</head>
<body>
  <div class="box">
    <h2>\U0001f916 MGKomik Bot</h2>
    <p>Klik tombol di bawah untuk kirim cookies ke server dan jalankan bot.</p>
    <button onclick="sendCookies()">\U0001f511 Kirim Cookies & Jalankan Bot</button>
    <div id="status"></div>
  </div>
  <script>
    async function sendCookies() {{
      const status = document.getElementById('status');
      status.innerHTML = '<div class="status">Mengirim cookies...</div>';
      
      // Kunjungi web.mgkomik.cc dulu supaya dapat cookies CF
      try {{
        await fetch('https://web.mgkomik.cc/', {{mode:'no-cors', credentials:'include'}});
      }} catch(e) {{}}
      
      const cookies = document.cookie;
      
      // Kirim ke server
      try {{
        const resp = await fetch('/receive_cookies', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{
            cookies: cookies,
            user_agent: navigator.userAgent,
            timestamp: Date.now()
          }})
        }});
        const data = await resp.json();
        if (data.ok) {{
          status.innerHTML = '<div class="status ok">\u2713 Berhasil! Bot sedang jalan di server.</div>';
        }} else {{
          status.innerHTML = '<div class="status err">Error: ' + data.msg + '</div>';
        }}
      }} catch(e) {{
        status.innerHTML = '<div class="status err">Error: ' + e.message + '</div>';
      }}
    }}
    
    // Auto-kirim cookies dari web.mgkomik.cc saat halaman dibuka
    window.onload = async function() {{
      // Inject iframe web.mgkomik.cc untuk trigger cookies
    }}
  </script>
</body>
</html>
"""

class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[HTTP] {fmt % args}")

    def do_GET(self):
        if self.path == "/" or self.path == "/bridge":
            # Halaman utama - redirect ke web.mgkomik.cc dulu, lalu balik
            html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MGKomik Cookie Bridge</title>
  <style>
    body{font-family:Arial;background:#1a1a2e;color:white;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
    .box{background:#16213e;border-radius:16px;padding:30px;text-align:center;max-width:380px;width:90%;}
    h2{color:#e94560;margin-bottom:10px;}
    p{color:#aaa;font-size:14px;line-height:1.5;}
    button{background:#e94560;color:white;border:none;padding:15px;border-radius:10px;font-size:16px;cursor:pointer;width:100%;margin-top:15px;font-weight:bold;}
    button:active{opacity:0.8;}
    .status{margin-top:15px;padding:12px;border-radius:8px;font-size:14px;display:none;}
    .ok{background:#27ae60;display:block;}
    .wait{background:#f39c12;display:block;}
    .err{background:#c0392b;display:block;}
  </style>
</head>
<body>
  <div class="box">
    <h2>&#129302; MGKomik Bot</h2>
    <p>Tekan tombol di bawah.<br>Browser akan buka <b>web.mgkomik.cc</b> dulu,<br>lalu otomatis kirim cookies ke server.</p>
    <button id="btn" onclick="startBridge()">&#128273; Aktifkan Bot</button>
    <div id="status" class="status wait">Membuka MGKomik...</div>
  </div>
  <script>
    async function startBridge() {
      document.getElementById('btn').disabled = true;
      const st = document.getElementById('status');
      st.className = 'status wait'; st.textContent = 'Membuka web.mgkomik.cc...';
      
      // Buka web.mgkomik.cc di tab baru supaya dapat cookies CF
      const w = window.open('https://web.mgkomik.cc/komik/', '_blank');
      
      st.textContent = 'Tunggu 10 detik untuk CF challenge selesai...';
      await sleep(10000);
      
      // Coba tutup tab dan kirim cookies
      try { w.close(); } catch(e) {}
      
      st.textContent = 'Mengirim cookies ke server...';
      
      // Kirim request ke bridge dengan cookies HP
      try {
        const r = await fetch('/send', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            ua: navigator.userAgent,
            ts: Date.now()
          })
        });
        const d = await r.json();
        if (d.ok) {
          st.className = 'status ok';
          st.textContent = '\u2713 Bot sudah aktif di server! Cek terminal.';
        } else {
          st.className = 'status err';
          st.textContent = 'Gagal: ' + d.msg;
        }
      } catch(e) {
        st.className = 'status err';
        st.textContent = 'Error: ' + e.message;
        document.getElementById('btn').disabled = false;
      }
    }
    
    function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
  </script>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())

        elif self.path == "/status":
            status = "running" if os.path.exists(".bot_running") else "idle"
            self.send_json({"status": status})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        
        if self.path == "/send":
            try:
                data = json.loads(body)
                ua = data.get("ua", "")
                print(f"[*] Menerima request dari HP")
                print(f"    UA: {ua[:60]}")
                
                # Simpan UA
                cfg = {"user_agent": ua}
                if os.path.exists(COOKIE_FILE):
                    with open(COOKIE_FILE) as f:
                        existing = json.load(f)
                    cfg.update(existing)
                with open(COOKIE_FILE, "w") as f:
                    json.dump(cfg, f, indent=2)
                
                print("[*] Menjalankan bot...")
                open(".bot_running", "w").close()
                
                def run_bot():
                    import subprocess
                    result = subprocess.run(
                        ["python3", "bot.py"],
                        capture_output=False
                    )
                    if os.path.exists(".bot_running"):
                        os.remove(".bot_running")
                
                t = threading.Thread(target=run_bot, daemon=True)
                t.start()
                
                self.send_json({"ok": True, "msg": "Bot berhasil dijalankan!"})
            except Exception as e:
                self.send_json({"ok": False, "msg": str(e)})
        
        elif self.path == "/receive_cookies":
            try:
                data = json.loads(body)
                raw_cookies = data.get("cookies", "")
                cookies = {}
                for part in raw_cookies.split(";"):
                    part = part.strip()
                    if "=" in part:
                        k, _, v = part.partition("=")
                        cookies[k.strip()] = v.strip()
                
                with open(COOKIE_FILE, "w") as f:
                    json.dump(cookies, f, indent=2)
                print(f"[*] Cookies diterima: {len(cookies)} cookies")
                
                open(".bot_running", "w").close()
                def run_bot():
                    subprocess.run(["python3", "bot.py"])
                    if os.path.exists(".bot_running"):
                        os.remove(".bot_running")
                threading.Thread(target=run_bot, daemon=True).start()
                
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "msg": str(e)})

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def get_public_ip():
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
    except:
        return "YOUR_SERVER_IP"


if __name__ == "__main__":
    ip = get_public_ip()
    print("=" * 50)
    print("  MGKomik Cookie Bridge")
    print("=" * 50)
    print(f"\n[*] Server berjalan di port {PORT}")
    print(f"\n  \U0001f4f1 BUKA LINK INI DI BROWSER HP KAMU:")
    print(f"\n  http://{ip}:{PORT}\n")
    print("  Tekan tombol 'Aktifkan Bot' di HP")
    print("  Bot akan otomatis jalan di server ini")
    print("=" * 50)
    
    server = HTTPServer(("0.0.0.0", PORT), BridgeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server berhenti.")
