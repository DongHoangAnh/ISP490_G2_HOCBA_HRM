import os
import psycopg2

def clean_august_payroll():
    # Read DB config
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

    print(f"Connecting to Neon DB ({host})...")
    conn = psycopg2.connect(
        host=host, port=port, user=user, password=password, dbname=dbname, sslmode="require"
    )
    cur = conn.cursor()

    # Find August 2026 batch IDs
    cur.execute("""
        SELECT id, name FROM hb_payslip_run 
        WHERE (date_start >= '2026-08-01' AND date_start <= '2026-08-31')
           OR name LIKE '%08/2026%' OR name LIKE '%Tháng 08/2026%';
    """)
    batches = cur.fetchall()
    batch_ids = [b[0] for b in batches]
    print(f"Found {len(batches)} August batches: {batches}")

    # Find August payslips
    cur.execute("""
        SELECT id FROM hb_payslip 
        WHERE (date_from >= '2026-08-01' AND date_from <= '2026-08-31')
           OR payslip_run_id IN %s;
    """, (tuple(batch_ids) if batch_ids else (-1,),))
    slips = cur.fetchall()
    slip_ids = [s[0] for s in slips]
    print(f"Found {len(slip_ids)} August payslips.")

    # Find August bank files
    cur.execute("""
        SELECT id, name FROM hb_bank_file 
        WHERE batch_id IN %s OR name LIKE '%%T08_2026%%';
    """, (tuple(batch_ids) if batch_ids else (-1,),))
    bank_files = cur.fetchall()
    bank_file_ids = [bf[0] for bf in bank_files]
    print(f"Found {len(bank_files)} August bank files: {bank_files}")

    # 1. Delete bank files
    if bank_file_ids:
        cur.execute("DELETE FROM hb_bank_file WHERE id IN %s;", (tuple(bank_file_ids),))
        print(f"Deleted {cur.rowcount} bank files.")

    # 2. Delete payslip lines
    if slip_ids:
        cur.execute("DELETE FROM hb_payslip_line WHERE payslip_id IN %s;", (tuple(slip_ids),))
        print(f"Deleted {cur.rowcount} payslip lines.")

        cur.execute("DELETE FROM hb_payslip_worked_days WHERE payslip_id IN %s;", (tuple(slip_ids),))
        print(f"Deleted {cur.rowcount} worked days records.")

        cur.execute("DELETE FROM hb_payslip_input WHERE payslip_id IN %s;", (tuple(slip_ids),))
        print(f"Deleted {cur.rowcount} payslip input records.")

        cur.execute("DELETE FROM hb_payslip WHERE id IN %s;", (tuple(slip_ids),))
        print(f"Deleted {cur.rowcount} payslips.")

    # 3. Delete batches
    if batch_ids:
        cur.execute("DELETE FROM hb_payslip_run WHERE id IN %s;", (tuple(batch_ids),))
        print(f"Deleted {cur.rowcount} batches.")

    # 4. Clear any vouchers linked to August payroll if exists
    cur.execute("DELETE FROM hocba_fin_voucher WHERE ref LIKE '%%08/2026%%' OR name LIKE '%%08/2026%%';")
    print(f"Deleted {cur.rowcount} finance vouchers linked to August 2026.")

    conn.commit()
    print("SUCCESS: August 2026 payroll history cleared completely!")
    conn.close()

if __name__ == "__main__":
    clean_august_payroll()
