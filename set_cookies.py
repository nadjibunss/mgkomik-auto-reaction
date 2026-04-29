"""
Jalankan script ini SATU KALI untuk simpan cookies dari browser HP.
Setelah itu bot.py akan otomatis pakai cookies tersebut.
"""
import json

print("="*50)
print("Setup Cookies dari Browser HP")
print("="*50)
print()
print("Paste semua isi cookies dari browser HP kamu.")
print("Format: key=value; key=value; ...")
print("Tekan Enter 2x kalau sudah selesai paste.")
print()

lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)

raw = " ".join(lines)

cookies = {}
for part in raw.split(";"):
    part = part.strip()
    if "=" in part:
        k, _, v = part.partition("=")
        cookies[k.strip()] = v.strip()

if not cookies:
    print("[!] Tidak ada cookie yang berhasil diparsing.")
else:
    with open("cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"[OK] {len(cookies)} cookies disimpan ke cookies.json:")
    for k,v in cookies.items():
        print(f"  {k} = {v[:40]}..." if len(v) > 40 else f"  {k} = {v}")
    print()
    print("Sekarang jalankan: python3 bot.py")
