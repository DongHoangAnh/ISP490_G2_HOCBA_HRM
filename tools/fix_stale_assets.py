#!/usr/bin/env python3
"""
Chạy trước khi khởi động Odoo để dọn sạch web asset attachments lỗi.
Áp dụng khi filestore local bị xóa nhưng Neon DB vẫn còn records cũ.
"""
import os
import sys
import psycopg2

DB_HOST = os.environ.get("DB_HOST") or os.environ.get("HOST")
DB_PORT = int(os.environ.get("DB_PORT") or os.environ.get("PORT") or 5432)
DB_USER = os.environ.get("DB_USER") or os.environ.get("USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or os.environ.get("PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "neondb")
DB_SSLMODE = os.environ.get("DB_SSLMODE", "require")
FILESTORE = f"/var/lib/odoo/.local/share/Odoo/filestore/{DB_NAME}"

def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD, sslmode=DB_SSLMODE,
            connect_timeout=10,
        )
    except Exception as e:
        print(f"[fix_stale_assets] Cannot connect to DB: {e}", file=sys.stderr)
        return

    cur = conn.cursor()

    # 1. Xóa web asset attachments (luôn regenerate được)
    cur.execute("DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'")
    n_assets = cur.rowcount

    # 2. Xóa attachments có store_fname nhưng file không còn trên disk
    cur.execute("SELECT id, store_fname FROM ir_attachment WHERE store_fname IS NOT NULL")
    stale_ids = []
    for row_id, store_fname in cur.fetchall():
        path = os.path.join(FILESTORE, store_fname[:2], store_fname)
        if not os.path.exists(path):
            stale_ids.append(row_id)

    if stale_ids:
        cur.execute(
            "DELETE FROM ir_attachment WHERE id = ANY(%s)",
            (stale_ids,),
        )

    conn.commit()
    conn.close()

    print(f"[fix_stale_assets] Cleared {n_assets} web asset(s), {len(stale_ids)} stale filestore record(s)")

if __name__ == "__main__":
    main()
