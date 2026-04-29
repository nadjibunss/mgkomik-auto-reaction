"""
Jalankan script ini di terminal untuk set cookies Cloudflare secara manual.
Caranya:
1. Buka web.mgkomik.cc di Chrome HP kamu
2. Buka DevTools (F12 di desktop, atau pakai VConsole di HP)
3. Pergi ke Application > Cookies > web.mgkomik.cc
4. Copy nilai 'cf_clearance' dan '__cf_bm'
5. Jalankan: python3 get_cookies.py
6. Masukkan nilai cookies yang diminta
"""

print("="*50)
print("Setup Cloudflare Cookies untuk MGKomik Bot")
print("="*50)
print()
print("Cara dapat cookies:")
print("1. Buka https://web.mgkomik.cc di browser HP")
print("2. Setelah halaman komik muncul (bukan 'Just a moment')")
print("3. Copy isi cookie 'cf_clearance' dari browser")
print()

cf_clearance = input("Paste nilai cf_clearance: ").strip()

if not cf_clearance:
    print("[!] cf_clearance kosong, skip")
else:
    with open("cookies.json", "w") as f:
        import json
        json.dump({"cf_clearance": cf_clearance}, f)
    print("[OK] Cookies disimpan ke cookies.json")
    print("Sekarang jalankan: python3 bot.py")
