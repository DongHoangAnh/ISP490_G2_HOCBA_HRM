#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xuất dữ liệu GIÁO VIÊN từ MySQL của CMS (Mabble ERP) ra CSV + JSON để đối chiếu
trước khi import vào HRM.

Nguồn: auth_erp_database.user ⨝ user_role/role (lọc role) ⨝ erp_database.tutor_profile

Chạy:
    python tools/cms/export_teachers.py                 # mặc định ROLE_TEACHER
    python tools/cms/export_teachers.py ROLE_HR         # đổi vai trò
File ra: tools/cms/exports/teachers_<role>_<timestamp>.csv (+ .json)

Kết nối lấy từ biến môi trường nếu có, không thì dùng mặc định đã biết:
    CMS_DB_HOST, CMS_DB_PORT, CMS_DB_USER, CMS_DB_PASSWORD
"""

import csv
import json
import os
import sys
from datetime import datetime

import mysql.connector as mysql

ROLE = sys.argv[1] if len(sys.argv) > 1 else "ROLE_TEACHER"

# Mật khẩu KHÔNG hardcode — set qua biến môi trường CMS_DB_PASSWORD.
#   PowerShell: $env:CMS_DB_PASSWORD="..."; python tools/cms/export_teachers.py
CONN = dict(
    host=os.environ.get("CMS_DB_HOST", "14.232.211.255"),
    port=int(os.environ.get("CMS_DB_PORT", "58008")),
    user=os.environ.get("CMS_DB_USER", "root"),
    password=os.environ.get("CMS_DB_PASSWORD"),
    connection_timeout=15,
)
if not CONN["password"]:
    raise SystemExit("Thiếu CMS_DB_PASSWORD. Đặt biến môi trường rồi chạy lại.")

# Cột xuất ra (theo thứ tự). Khoá = tên cột file, giá trị = biểu thức SQL.
COLUMNS = {
    "full_name":      "u.full_name",
    "email":          "u.email",
    "phone_number":   "u.phone_number",
    "unique_code":    "u.unique_code",
    "status":         "u.status",
    "email_verified": "u.email_verified",
    "address":        "u.address",
    "avatar_url":     "u.avatar_url",
    "qualification":  "tp.qualification",
    "rating":         "tp.rating",
    "total_students": "tp.total_students",
    "total_sessions": "tp.total_sessions",
    "short_description": "tp.short_description",
    "created_at":     "u.created_at",
    "user_id":        "u.id",
}

QUERY = """
  SELECT {cols}
  FROM auth_erp_database.user u
  JOIN auth_erp_database.user_role ur ON ur.user_id = u.id
  JOIN auth_erp_database.role r       ON r.id = ur.role_id AND r.name = %s
  LEFT JOIN erp_database.tutor_profile tp ON tp.user_id = u.id
  WHERE u.deleted = 0
  ORDER BY u.full_name
""".format(cols=", ".join("%s AS %s" % (expr, name) for name, expr in COLUMNS.items()))


def _jsonify(v):
    """Chuẩn hoá kiểu để ghi JSON/CSV (datetime, bytes bit(1))."""
    if isinstance(v, datetime):
        return v.isoformat(sep=" ")
    if isinstance(v, (bytes, bytearray)):
        return bool(v[0]) if v else False
    return v


def main():
    print("Kết nối MySQL %s:%s ..." % (CONN["host"], CONN["port"]))
    conn = mysql.connect(**CONN)
    cur = conn.cursor(dictionary=True)
    cur.execute(QUERY, (ROLE,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print("Lấy được %d người với vai trò %s." % (len(rows), ROLE))
    if not rows:
        print("Không có dữ liệu — kiểm tra lại tên vai trò.")
        return

    rows = [{k: _jsonify(v) for k, v in row.items()} for row in rows]

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(out_dir, "teachers_%s_%s" % (ROLE.lower(), stamp))

    csv_path = base + ".csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:  # BOM cho Excel
        w = csv.DictWriter(f, fieldnames=list(COLUMNS.keys()))
        w.writeheader()
        w.writerows(rows)

    json_path = base + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print("Đã ghi:")
    print("   CSV :", csv_path)
    print("   JSON:", json_path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
