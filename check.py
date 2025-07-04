#!/usr/bin/env python3
"""
Basic security sanity-check script for a Flask image host.

What it does
------------
1. Path-traversal probes on /images/<path>
2. Oversized upload test (≈1.1 GiB)      – should be rejected
3. Non-image masquerading as .png upload – should be rejected
4. Multipart field name/filename tricks  – should be sanitised
5. Simple health check

NOT a full pentest – just quick smoke tests.
"""

import os, io, requests, random, string, pathlib
from PIL import Image

BASE = "http://82.117.243.228:5000"
IMAGES = f"{BASE}/images"
UPLOAD = f"{BASE}/upload"
PASS = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"

s = requests.Session(); s.timeout = 10

def status(ok, msg): print(f"{PASS if ok else FAIL} {msg}")

# 1. PATH-TRAVERSAL PROBES
traversal_payloads = [
    "../../etc/passwd",
    "..%2f..%2f..%2fetc%2fpasswd",
    "..\\..\\windows\\win.ini"
]
for p in traversal_payloads:
    r = s.get(f"{IMAGES}/{p}")
    status(r.status_code in (400,404), f"path-traversal '{p}' ➜ {r.status_code}")

# 2. OVERSIZED UPLOAD (≈1.1 GiB of zeros sent as a fake PNG)
def big_body(size_bytes):
    yield b"\x89PNG\r\n\x1a\n"          # PNG header
    yield b"\x00" * (size_bytes-8)
big_size = 1100 * 1024**2
r = s.post(UPLOAD,
           files={"image": ("huge.png", big_body(big_size), "image/png")})
status(r.status_code >= 400, f"Oversized upload rejected (status {r.status_code})")

# 3. NON-IMAGE MASQUERADING AS PNG
r = s.post(UPLOAD,
           files={"image": ("not_really.png", b"#!/bin/sh\necho pwn\n", "image/png")})
status(r.status_code >= 400, f"Non-image upload rejected (status {r.status_code})")

# 4. WEIRD FILENAMES
weird_name = '../evil.png'
# generate tiny valid PNG
buf = io.BytesIO()
Image.new("RGB",(1,1)).save(buf, format="PNG"); buf.seek(0)
r = s.post(UPLOAD,
           files={"image": (weird_name, buf, "image/png")})
ok = (r.status_code == 200 and
      all(sep not in r.json().get("path","") for sep in ("..","\\")))
status(ok, f"Filename sanitised (‘{weird_name}’ → {r.json().get('path','?')})")

# 5. HEALTH ENDPOINT
r = s.get(f"{BASE}/health")
status(r.ok and r.json().get("status")=="ok", "/health returns ok")

print("\nDone – remember this is **not** exhaustive.")
