from passlib.context import CryptContext
import psycopg2

hashed = CryptContext(["pbkdf2_sha512"]).hash("admin")

conn = psycopg2.connect(
    dbname="hocba_hrm",
    user="odoo",
    password="odoo_password",
    host="db",
    port=5432
)
cur = conn.cursor()
cur.execute("UPDATE res_users SET password = %s WHERE login = 'admin'", (hashed,))
print(f"Updated {cur.rowcount} row(s). Hash: {hashed[:30]}...")
conn.commit()
cur.close()
conn.close()
