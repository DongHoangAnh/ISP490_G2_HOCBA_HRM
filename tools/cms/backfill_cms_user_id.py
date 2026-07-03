#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill `x_cms_user_id` cho giáo viên đã import vào HRM (Neon Postgres).

Bối cảnh: 167 giáo viên được import từ CMS nhưng KHÔNG được gán x_cms_user_id
(builder cũ bỏ mất cột user_id) → lịch dạy luôn rỗng vì controller lấy lịch theo
đúng khoá này (hocba_hrm/controllers/main.py: _teaching_today_rows).

Script này:
  1. Đọc CMS MySQL: {email -> user.id} cho ROLE_TEACHER.
  2. CHẨN ĐOÁN: kiểm tra tutor_id trong class_session có thật sự là user.id không
     (nếu không, backfill sẽ vô ích — cần map qua tutor_profile thay vì user.id).
  3. Cập nhật hr_employee.x_cms_user_id trên Neon theo work_email (chỉ khi rỗng/khác).

Mặc định DRY-RUN (chỉ đọc + báo cáo). Ghi thật: thêm cờ --apply.

Chạy (PowerShell):
    $env:CMS_DB_PASSWORD="..."; $env:DB_PASSWORD="..."
    python tools/cms/backfill_cms_user_id.py            # DRY-RUN
    python tools/cms/backfill_cms_user_id.py --apply    # ghi thật vào Neon

Kết nối lấy từ biến môi trường (giống export_teachers.py / .env):
    CMS_DB_HOST/PORT/USER/PASSWORD   — MySQL CMS
    DB_HOST/USER/PASSWORD/NAME       — Neon Postgres
"""
import os
import sys

ROLE = "ROLE_TEACHER"
APPLY = "--apply" in sys.argv


def _load_dotenv():
    """Nạp .env ở gốc repo vào os.environ (không ghi đè biến đã có)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

# CMS: ưu tiên CMS_DB_* (export_teachers.py), fallback CMS_MYSQL_* (.env / cms_connector).
CMS = dict(
    host=os.environ.get("CMS_DB_HOST") or os.environ.get("CMS_MYSQL_HOST", "14.232.211.255"),
    port=int(os.environ.get("CMS_DB_PORT") or os.environ.get("CMS_MYSQL_PORT", "58008")),
    user=os.environ.get("CMS_DB_USER") or os.environ.get("CMS_MYSQL_USER", "root"),
    password=os.environ.get("CMS_DB_PASSWORD") or os.environ.get("CMS_MYSQL_PASSWORD"),
    connection_timeout=15,
)
PG = dict(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER", "neondb_owner"),
    password=os.environ.get("DB_PASSWORD"),
    dbname=os.environ.get("DB_NAME", "neondb"),
    sslmode="require",
    connect_timeout=15,
)


def _need(val, name):
    if not val:
        raise SystemExit("Thiếu %s. Đặt biến môi trường rồi chạy lại." % name)


def fetch_cms_teachers():
    """Trả về list dict {email, user_id, full_name} cho ROLE_TEACHER (chưa xoá)."""
    import pymysql
    conn = pymysql.connect(
        host=CMS["host"], port=CMS["port"], user=CMS["user"],
        password=CMS["password"], charset="utf8mb4", connect_timeout=15)
    try:
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT u.id AS user_id, u.email, u.full_name
            FROM auth_erp_database.user u
            JOIN auth_erp_database.user_role ur ON ur.user_id = u.id
            JOIN auth_erp_database.role r ON r.id = ur.role_id AND r.name = %s
            WHERE u.deleted = 0 AND u.email IS NOT NULL AND u.email <> ''
        """, (ROLE,))
        return cur.fetchall()
    finally:
        conn.close()


def diagnose_tutor_mapping(user_ids):
    """Kiểm tra xem user.id có xuất hiện trong class_session.tutor_id /
    class.main_tutor_id không. Nếu khớp ~0 → khoá map nên là tutor_profile.id
    chứ KHÔNG phải user.id, và backfill này sẽ vô ích."""
    import pymysql
    if not user_ids:
        return
    conn = pymysql.connect(
        host=CMS["host"], port=CMS["port"], user=CMS["user"],
        password=CMS["password"], charset="utf8mb4", connect_timeout=15)
    try:
        cur = conn.cursor()
        ids = list(user_ids)[:500]
        ph = ",".join(["%s"] * len(ids))
        cur.execute(
            "SELECT COUNT(DISTINCT tutor_id) FROM erp_database.class_session "
            "WHERE tutor_id IN (%s)" % ph, ids)
        by_session = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(DISTINCT main_tutor_id) FROM erp_database.class "
            "WHERE main_tutor_id IN (%s)" % ph, ids)
        by_class = cur.fetchone()[0]
        # So sánh: tutor_profile.id của các user này có khớp tutor_id hơn không?
        cur.execute(
            "SELECT COUNT(*) FROM erp_database.class_session cs "
            "JOIN erp_database.tutor_profile tp ON tp.id = cs.tutor_id "
            "WHERE tp.user_id IN (%s)" % ph, ids)
        via_profile = cur.fetchone()[0]
        print("=== CHẨN ĐOÁN khoá map tutor (mẫu %d user) ===" % len(ids))
        print("  class_session.tutor_id KHỚP user.id      :", by_session, "distinct")
        print("  class.main_tutor_id    KHỚP user.id      :", by_class, "distinct")
        print("  class_session.tutor_id -> tutor_profile.user_id :", via_profile, "rows")
        if by_session == 0 and by_class == 0 and via_profile > 0:
            print("  ⚠️  tutor_id KHÔNG phải user.id mà là tutor_profile.id!")
            print("      => x_cms_user_id nên = tutor_profile.id, và cms_connector")
            print("         cần đổi lại. DỪNG backfill cho tới khi xác định đúng khoá.")
        elif by_session == 0 and by_class == 0:
            print("  ⚠️  Không có buổi nào khớp — kiểm tra lại dữ liệu CMS.")
        else:
            print("  ✓ user.id khớp tutor_id — backfill x_cms_user_id = user.id hợp lý.")
    finally:
        conn.close()


def backfill_neon(email_to_uid):
    import psycopg2
    conn = psycopg2.connect(**PG)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, work_email, x_cms_user_id FROM hr_employee "
            "WHERE work_email IS NOT NULL AND work_email <> ''")
        to_set, already, no_match = [], 0, 0
        for emp_id, email, cur_cms in cur.fetchall():
            uid = email_to_uid.get((email or "").strip().lower())
            if not uid:
                no_match += 1
                continue
            if str(cur_cms or "") == str(uid):
                already += 1
                continue
            to_set.append((emp_id, email, str(uid)))

        print("\n=== Backfill hr_employee.x_cms_user_id (Neon) ===")
        print("  Sẽ set / cập nhật :", len(to_set))
        print("  Đã đúng (bỏ qua)  :", already)
        print("  Không khớp email  :", no_match)
        for emp_id, email, uid in to_set[:20]:
            print("    %-40s -> %s" % (email, uid))
        if len(to_set) > 20:
            print("    ... (%d dòng nữa)" % (len(to_set) - 20))

        if not APPLY:
            print("\n>>> DRY-RUN: không ghi gì. Thêm --apply để ghi thật.")
            return
        for emp_id, _email, uid in to_set:
            cur.execute(
                "UPDATE hr_employee SET x_cms_user_id = %s WHERE id = %s",
                (uid, emp_id))
        conn.commit()
        print("\n>>> ĐÃ COMMIT: cập nhật %d hồ sơ giáo viên." % len(to_set))
    finally:
        conn.close()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    _need(CMS["password"], "CMS_DB_PASSWORD / CMS_MYSQL_PASSWORD")
    _need(PG["host"], "DB_HOST")
    _need(PG["password"], "DB_PASSWORD")

    teachers = fetch_cms_teachers()
    print("CMS: lấy được %d giáo viên (%s)." % (len(teachers), ROLE))
    email_to_uid = {
        (t["email"] or "").strip().lower(): t["user_id"]
        for t in teachers if (t.get("email") or "").strip()
    }
    diagnose_tutor_mapping({t["user_id"] for t in teachers})
    backfill_neon(email_to_uid)


if __name__ == "__main__":
    main()
