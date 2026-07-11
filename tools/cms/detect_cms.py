#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nhận diện CMS (Strapi / Directus / Ghost / WordPress) tại cms.dangch.tech và
thử đăng nhập tài khoản admin để lấy API token cho hướng tích hợp "Cách A".

Chạy bằng Python THUẦN (chỉ stdlib, không cần requests/Odoo/MySQL):

    python tools/cms/detect_cms.py

Khi server CMS còn sập sẽ thấy HTTP 530 ở mọi endpoint -> chưa làm gì được,
đợi người quản lý bật server lại rồi chạy lại script này.

Khi server sống: script in ra (1) CMS là gì, (2) đăng nhập admin có ra token
không. Gửi toàn bộ output cho mình là viết được phần tích hợp vào dự án HRM.
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request

# Ép stdout/stderr ra UTF-8 để in tiếng Việt trên console Windows (cp1252).
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 - python cũ / stream đặc biệt
        pass

BASE = (sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://cms.dangch.tech")

# Credential lấy từ biến môi trường — KHÔNG hardcode secret vào code.
#   set CMS_ADMIN_EMAIL / CMS_ADMIN_PASSWORD  (Windows: $env:CMS_ADMIN_PASSWORD="...")
ADMIN_EMAIL = os.environ.get("CMS_ADMIN_EMAIL", "admin@local.com")
ADMIN_PASSWORD = os.environ.get("CMS_ADMIN_PASSWORD")

# Bỏ kiểm chứng chỉ SSL cho chắc (nhiều server self-host cert lởm). Chỉ là
# công cụ khảo sát nội bộ, không phải production.
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

TIMEOUT = 12


def _call(method, path, body=None, headers=None):
    """Trả về (status_code, text, dict_or_None). status_code=0 nếu lỗi mạng."""
    url = BASE + path
    data = None
    hdrs = {"Accept": "application/json", "User-Agent": "hocba-cms-probe/1.0"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_CTX) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, raw, _as_json(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace") if e.fp else ""
        return e.code, raw, _as_json(raw)
    except Exception as e:  # noqa: BLE001 - khảo sát, gộp mọi lỗi mạng
        return 0, "NETWORK_ERROR: %s" % e, None


def _as_json(raw):
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


def _short(raw, n=180):
    return " ".join((raw or "").split())[:n]


def main():
    print("=" * 64)
    print("Dò CMS tại:", BASE)
    print("=" * 64)

    # 1) Server sống chưa? (530 = Cloudflare up nhưng origin chết)
    code, raw, _ = _call("GET", "/")
    print("\n[1] GET /  ->  HTTP %s" % code)
    if code == 530 or code == 0 or code == 521 or code == 522:
        print("    => SERVER ĐANG SẬP / KHÔNG TỚI ĐƯỢC (origin down).")
        print("       Đợi bật server lại rồi chạy lại script. Dừng tại đây.")
        return

    # 2) Nhận diện công nghệ qua HTML trang chủ.
    print("\n[2] Nhận diện stack frontend:")
    _, home_html, _ = _call("GET", "/")
    is_vite = "/@vite/client" in home_html or "/src/main.jsx" in home_html
    if is_vite:
        print("    => SPA React + Vite (đang chạy DEV mode). 'CMS' này là web tự code,")
        print("       KHÔNG phải Strapi/Directus/Ghost/WP. API đi qua gateway dưới /api/*.")
    else:
        # Fallback: dò sản phẩm đóng gói nếu sau này đổi.
        for kind, path in (("Strapi", "/admin/init"), ("Directus", "/server/ping"),
                           ("Ghost", "/ghost/api/admin/site/"), ("WordPress", "/wp-json/")):
            code, raw, _ = _call("GET", path)
            if 200 <= code < 300:
                print("    [%s] có vẻ là %s (%s)" % (code, kind, path))

    # 3) Đăng nhập admin qua API thật: POST /api/auth/login.
    print("\n[3] Đăng nhập admin qua /api/auth/login (%s):" % ADMIN_EMAIL)
    if not ADMIN_PASSWORD:
        print("    Bỏ qua: chưa set biến môi trường CMS_ADMIN_PASSWORD.")
        print("    Ví dụ (PowerShell): $env:CMS_ADMIN_PASSWORD=\"...\"; python tools/cms/detect_cms.py")
        return
    code, raw, js = _call("POST", "/api/auth/login",
                          {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    print("    HTTP %s" % code)
    token = None
    if js:
        data = js.get("data") or {}
        token = data.get("accessToken") or data.get("access_token") or data.get("token")
    if not token:
        print("    ✗ Không lấy được token. Body:", _short(raw))
        print("    => endpoint login có thể đã đổi; gửi output này cho mình.")
    else:
        print("    ✓ LOGIN OK. accessToken:", token[:40], "...")
        print("    Header dùng cho các request sau: Authorization: Bearer <accessToken>")
        claims = _decode_jwt(token)
        if claims:
            print("    JWT claims:", json.dumps(claims, ensure_ascii=False))
            exp, iat = claims.get("exp"), claims.get("iat")
            if exp and iat:
                print("    Token sống ~%d phút. roles=%s" % ((exp - iat) // 60, claims.get("roles")))
        print("    => Base API: %s/api  |  Auth: Bearer JWT (1h, có refreshToken)" % BASE)

    print("\n" + "=" * 64)
    print("XONG. Copy toàn bộ output ở trên gửi cho mình.")
    print("=" * 64)


def _decode_jwt(token):
    """Giải payload JWT (phần giữa) không kiểm chữ ký — chỉ để xem claims."""
    try:
        import base64
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)  # pad base64url
        return json.loads(base64.urlsafe_b64decode(part).decode("utf-8", "replace"))
    except Exception:  # noqa: BLE001
        return None


if __name__ == "__main__":
    main()
