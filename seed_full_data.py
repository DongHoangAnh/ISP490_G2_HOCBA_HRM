"""
Seed employees via Odoo XML-RPC + attendance data from 2025 to Aug 2026.
Must run AFTER Odoo is up on port 8069.
"""
import xmlrpc.client
import subprocess
import random
import os
import sys
from datetime import date, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Odoo XML-RPC connection ──
URL = 'http://localhost:8069'
DB = 'hocba_hrm'
USER = 'admin'
PASS = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USER, PASS, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def call(model, method, *args, **kw):
    return models.execute_kw(DB, uid, PASS, model, method, *args, **kw)

DB_CONTAINER = "isp490_g2_hocba_hrm-db-1"

def raw_sql(query):
    r = subprocess.run(
        ["docker", "exec", DB_CONTAINER, "psql", "-U", "odoo", "-d", "hocba_hrm", "-t", "-A", "-c", query],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return (r.stdout or '').strip()

def sql_file(content):
    tmp = os.path.join(os.path.dirname(__file__), '_tmp.sql')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    subprocess.run(
        f'type "{tmp}" | docker exec -i {DB_CONTAINER} psql -U odoo -d hocba_hrm',
        shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    os.remove(tmp)

# ══════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════

# Existing employees: fix contract start dates
EXISTING = [
    (2, "2025-03-01", 12000000),   # Nguyen Van An
    (3, "2025-01-15", 9500000),    # Tran Thi Binh
    (4, "2025-06-01", 15000000),   # Le Hoang Cuong
    (5, "2025-04-15", 8000000),    # Pham Thu Dung
    (6, "2025-02-01", 22000000),   # Vu Minh Duc
    (7, "2025-08-01", 7000000),    # Do Thi Hoa
    (8, "2025-05-01", 18000000),   # Bui Quang Huy
    (9, "2026-08-06", 2000000),    # hung
]

# New employees to create via XML-RPC
NEW_EMP = [
    # (name, code, join_date, wage, dept_id, job_id)
    ("Trương Văn Khoa",  "HB-D08", "2025-01-05", 10000000, 1, 8),   # Administration, HCNS
    ("Ngô Thị Lan",      "HB-D09", "2025-02-10", 8500000,  1, 4),   # Administration, QL hoc vien
    ("Hoàng Minh Tú",    "HB-D10", "2025-07-01", 11000000, 2, 5),   # Marketing, Content
    ("Lý Thanh Hà",      "HB-D11", "2025-09-15", 9000000,  7, None),# BOD
    ("Đinh Quốc Bảo",    "HB-D12", "2025-11-01", 13000000, 4, 1),   # Kinh doanh, Tu van
    ("Mai Thị Ngọc",     "HB-D13", "2026-01-05", 7500000,  6, 8),   # Ke toan, HCNS
    ("Phan Văn Tùng",    "HB-D14", "2026-03-01", 16000000, 1, None),# Administration
    ("Võ Thị Yến",       "HB-D15", "2026-05-15", 8000000,  2, 5),   # Marketing, Content
]

print("=== SEED FULL REALISTIC DATA ===\n")

# ── Step 0: Clean old data ──
print("Step 0: Clean old payslip + attendance...")
raw_sql("DELETE FROM hb_bank_file; DELETE FROM hb_payslip_line; DELETE FROM hb_payslip; DELETE FROM hb_payslip_run; DELETE FROM hocba_attendance;")
print("  Done.\n")

# ── Step 1: Fix existing employee contracts ──
print("Step 1: Fix existing contracts...")
for eid, ds, w in EXISTING:
    raw_sql(f"UPDATE hb_contract SET date_start='{ds}', wage={w} WHERE employee_id={eid}")
    c = raw_sql(f"SELECT count(*) FROM hb_contract WHERE employee_id={eid}")
    if c == '0':
        raw_sql(f"INSERT INTO hb_contract (employee_id,date_start,state,wage,name,create_uid,write_uid,create_date,write_date) VALUES ({eid},'{ds}','open',{w},'HD-{eid}',1,1,NOW(),NOW())")
print("  Done.\n")

# ── Step 2: Create new employees via XML-RPC ──
print("Step 2: Create new employees via Odoo ORM...")
all_employees = []

# Add existing first
for eid, ds, w in EXISTING:
    name = raw_sql(f"SELECT name FROM hr_employee WHERE id={eid}")
    all_employees.append((eid, ds, w, name))

for name, code, join_date, wage, dept_id, job_id in NEW_EMP:
    # Check if already exists
    existing = call('hr.employee', 'search', [[['x_employee_code', '=', code]]])
    if existing:
        eid = existing[0]
        print(f"  {name} ({code}) already exists (id={eid})")
        # Update contract
        raw_sql(f"UPDATE hb_contract SET date_start='{join_date}', wage={wage} WHERE employee_id={eid}")
        c = raw_sql(f"SELECT count(*) FROM hb_contract WHERE employee_id={eid}")
        if c == '0':
            raw_sql(f"INSERT INTO hb_contract (employee_id,date_start,state,wage,name,create_uid,write_uid,create_date,write_date) VALUES ({eid},'{join_date}','open',{wage},'HD-{code}',1,1,NOW(),NOW())")
        all_employees.append((eid, join_date, wage, name))
        continue

    vals = {
        'name': name,
        'x_employee_code': code,
        'x_employment_status': 'official',
        'department_id': dept_id,
        # Required fields for 'official' status (BR-010)
        'identification_id': f'0{random.randint(10000000000, 99999999999)}',
        'x_pit_code': f'{random.randint(1000000000, 9999999999)}',
        'x_social_insurance_no': f'{random.randint(1000000000, 9999999999)}',
    }
    if job_id:
        vals['job_id'] = job_id

    try:
        eid = call('hr.employee', 'create', [vals])
        print(f"  Created: {name} ({code}) → id={eid}")
        # Create contract
        raw_sql(f"INSERT INTO hb_contract (employee_id,date_start,state,wage,name,create_uid,write_uid,create_date,write_date) VALUES ({eid},'{join_date}','open',{wage},'HD-{code}',1,1,NOW(),NOW())")
        all_employees.append((eid, join_date, wage, name))
    except Exception as e:
        print(f"  ERROR creating {name}: {e}")

print(f"  Total employees: {len(all_employees)}\n")

# ── Step 3: Generate attendance data ──
print("Step 3: Generate attendance (22-25 cong/thang)...")
TODAY = date(2026, 8, 16)
all_stmts = []

for eid, ds_str, w, name in all_employees:
    join_d = date.fromisoformat(ds_str)
    start = join_d + timedelta(days=1)
    count = 0

    cur = date(start.year, start.month, 1)
    if start.day <= 5:
        cur = date(start.year, start.month, 1)

    while cur <= TODAY:
        if cur.month == 12:
            m_end = date(cur.year, 12, 31)
        else:
            m_end = date(cur.year, cur.month + 1, 1) - timedelta(days=1)
        if m_end > TODAY:
            m_end = TODAY

        # Absent days: mostly 0-1, rarely 2
        r = random.random()
        absent = 0 if r < 0.50 else (1 if r < 0.80 else 2)

        wdays = []
        d = max(cur, start)
        while d <= m_end:
            if d.weekday() < 5:
                wdays.append(d)
            d += timedelta(days=1)

        if absent > 0 and len(wdays) > absent:
            rm = random.sample(range(len(wdays)), absent)
            wdays = [x for i, x in enumerate(wdays) if i not in rm]

        for wd in wdays:
            ci_off = random.randint(-10, 15)
            h = 8 if ci_off >= 0 else 7
            m = ci_off if ci_off >= 0 else (60 + ci_off)
            co_m = random.randint(0, 30)
            late = max(0, ci_off - 5) if ci_off > 5 else 0
            sid = 2 if late > 0 else 1
            sc = 'late' if late > 0 else 'on_time'
            wh = round(8.0 + co_m / 60.0, 1)

            all_stmts.append(
                f"INSERT INTO hocba_attendance "
                f"(employee_id,date,check_in,check_out,expected_check_out,"
                f"status_id,status_code,work_credit,morning_credit,afternoon_credit,"
                f"working_hours,late_minutes,early_leave_minutes,missing_minutes,"
                f"active,face_suspect,out_of_zone,out_of_window,needs_review,"
                f"create_uid,write_uid,create_date,write_date) VALUES ("
                f"{eid},'{wd}','{wd} {h:02d}:{m:02d}:00','{wd} 17:{co_m:02d}:00','{wd} 17:00:00',"
                f"{sid},'{sc}',1.0,0.5,0.5,"
                f"{wh},{late},0,0,"
                f"true,false,false,false,false,"
                f"1,1,NOW(),NOW())"
            )
            count += 1

        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)

    print(f"  {name:25s} join={ds_str}  {count:>4d} records")

print(f"\n  Total: {len(all_stmts)} records")

# Insert via temp file
print("\nStep 4: Inserting attendance...")
CHUNK = 300
for i in range(0, len(all_stmts), CHUNK):
    chunk = all_stmts[i:i+CHUNK]
    sql_file(";\n".join(chunk) + ";\n")
    print(f"  {min(i+CHUNK, len(all_stmts))}/{len(all_stmts)}")

# Verify
print("\nStep 5: Verification...")
v = raw_sql(
    "SELECT e.name, MIN(a.date), MAX(a.date), COUNT(*) "
    "FROM hocba_attendance a JOIN hr_employee e ON e.id=a.employee_id "
    "GROUP BY e.name ORDER BY e.name"
)
print(f"\n{'Name':25s} {'From':12s} {'To':12s} {'Days':>5s}")
print("-" * 58)
for line in v.split('\n'):
    if '|' in line:
        p = [x.strip() for x in line.split('|')]
        print(f"{p[0]:25s} {p[1]:12s} {p[2]:12s} {p[3]:>5s}")

print("\n[OK] Part A Done!")
