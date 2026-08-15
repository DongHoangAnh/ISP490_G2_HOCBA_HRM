import os
import psycopg2

def main():
    # Read env vars or defaults
    host = "ep-cool-wave-aoam4gfh-pooler.c-2.ap-southeast-1.aws.neon.tech"
    port = "5432"
    user = "neondb_owner"
    password = "npg_93IDXZaQneRu"
    dbname = "neondb"

    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k == "DB_HOST": host = v
                    elif k == "DB_PORT": port = v
                    elif k == "DB_USER": user = v
                    elif k == "DB_PASSWORD": password = v
                    elif k == "DB_NAME": dbname = v

    print(f"Connecting to {host}:{port}/{dbname} as {user}...")
    conn = psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=dbname, sslmode="require"
    )
    cur = conn.cursor()

    print("\n--- BATCHES FOR AUGUST 2026 / RECENT ---")
    cur.execute("""
        SELECT id, name, date_start, date_end, state, compute_status 
        FROM hb_payslip_run 
        WHERE (date_start >= '2026-08-01' AND date_start <= '2026-08-31')
           OR name LIKE '%08%' OR name LIKE '%8/2026%' OR name LIKE '%tháng 8%' OR name LIKE '%Tháng 8%'
        ORDER BY id DESC;
    """)
    august_batches = cur.fetchall()
    for b in august_batches:
        print(f"Batch ID: {b[0]} | Name: {b[1]} | Dates: {b[2]} -> {b[3]} | State: {b[4]} | Compute: {b[5]}")

    print("\n--- ALL RECENT BATCHES ---")
    cur.execute("SELECT id, name, date_start, date_end, state FROM hb_payslip_run ORDER BY id DESC LIMIT 10;")
    for b in cur.fetchall():
        print(f"Batch ID: {b[0]} | Name: {b[1]} | Dates: {b[2]} -> {b[3]} | State: {b[4]}")

    print("\n--- PAYSLIPS FOR AUGUST 2026 / RECENT ---")
    cur.execute("""
        SELECT count(*), state, x_employee_confirm 
        FROM hb_payslip 
        WHERE date_from >= '2026-08-01' AND date_from <= '2026-08-31'
        GROUP BY state, x_employee_confirm;
    """)
    for row in cur.fetchall():
        print(f"Count: {row[0]} | State: {row[1]} | Employee Confirm: {row[2]}")

    print("\n--- BANK FILES ---")
    cur.execute("SELECT id, name, batch_id, total_amount, state FROM hb_bank_file ORDER BY id DESC LIMIT 5;")
    for bf in cur.fetchall():
        print(f"BankFile ID: {bf[0]} | Name: {bf[1]} | BatchID: {bf[2]} | Amount: {bf[3]} | State: {bf[4]}")

    conn.close()

if __name__ == "__main__":
    main()
