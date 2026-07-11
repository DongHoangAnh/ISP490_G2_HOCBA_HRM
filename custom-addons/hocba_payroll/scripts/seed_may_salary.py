#!/usr/bin/env python3
"""
Seed May 2026 salary history into the database.

Usage (run from Odoo shell):
    python odoo-bin shell -d hocba --addons-path=addons,custom-addons \
        < custom-addons/hocba_payroll/scripts/seed_may_salary.py

Or paste into the Odoo shell interactively.
"""
import logging

_logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════
MONTH = 5
YEAR = 2026
DATE_FROM = '2026-05-01'
DATE_END = '2026-05-31'
BATCH_NAME = 'Lương Tháng 05/2026'
STANDARD_DAYS = 22  # May 2026 working days

# ═══════════════════════════════════════════════════════════════════════
# EMPLOYEE SALARY DATA (based on June salary table, adapted for May)
#
# Format: (employee_code, work_days, base_salary,
#          xang_xe, dien_thoai, thuong_khac, ho_tro_nuoi_con, npt)
# ═══════════════════════════════════════════════════════════════════════
EMPLOYEES = [
    ('HB.03',  22,   7300000, 1000000, 1000000, 0, 0, 0),
    ('HB.02',  22,   7300000, 1000000, 1000000, 0, 0, 0),
    ('HB.04',  20,   6000000, 1000000,  800000, 0, 0, 0),
    ('HB.05',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.06',  21,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.39',  22,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.40',  22,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.55',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.57',  21.5, 5700000, 1000000,  800000, 0, 0, 0),
    ('HB.65',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.59',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.58',  20,   6000000, 1000000,  800000, 0, 0, 2),
    ('HB.73',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.68',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.09',  21,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.72',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.75',  22,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.76',  22,   5700000, 1000000,  500000, 0, 0, 0),
    ('HB.85',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.92',  22,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.83',  21,   5700000, 1000000,  800000, 0, 0, 0),
    ('HB.01',  22,   7300000, 1000000,  800000, 0, 0, 1),
    ('HB.100', 22,   5700000,  500000,  400000, 0, 0, 0),
    ('HB.102', 20,   5700000,  500000,  400000, 0, 0, 0),
    ('HB.103', 22,   5700000, 1000000,  800000, 0, 0, 1),
    ('HB.116', 22,   5700000,  400000,  400000, 0, 0, 0),
    ('HB.124', 24,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.127', 22,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.128', 23,   5700000, 1000000, 1000000, 0, 0, 0),
    ('HB.133', 22,   5700000, 1000000, 1000000, 0, 0, 0),
]


def calc_pit(taxable):
    """Vietnam progressive personal income tax (simplified 5-bracket)."""
    if taxable <= 0:
        return 0
    W = taxable
    if W <= 10_000_000:
        return round(W * 0.05)
    elif W <= 30_000_000:
        return round(500_000 + (W - 10_000_000) * 0.10)
    elif W <= 60_000_000:
        return round(2_500_000 + (W - 30_000_000) * 0.20)
    elif W <= 100_000_000:
        return round(8_500_000 + (W - 60_000_000) * 0.30)
    else:
        return round(20_500_000 + (W - 100_000_000) * 0.35)


def compute_salary(nctt, base_salary, xang_xe, dien_thoai, thuong_khac,
                   ho_tro_nuoi_con, npt):
    """Compute all salary components. Returns dict of rule_code -> amount."""
    F = base_salary
    an_ca = round(50000 * nctt)

    # Tổng thu nhập = (ăn_ca + xăng_xe + điện_thoại + F) / 25 * NCTT
    # NOTE: rule uses /25 (hardcoded in salary rule), NOT STANDARD_DAYS
    tong_thu_nhap = round((an_ca + xang_xe + dien_thoai + F) / 25.0 * nctt) if nctt > 0 else 0

    tn_mien_thue = 730000
    tn_truoc_thue = tong_thu_nhap - tn_mien_thue

    giam_tru = 15500000 + int(npt) * 6200000

    bhxh_8_nv = round(F * 0.08)
    bhyt_1_5_nv = round(F * 0.015)
    bhtn_1_nv = round(F * 0.01)

    tn_tinh_thue = max(0, tn_truoc_thue - giam_tru - bhxh_8_nv - bhyt_1_5_nv - bhtn_1_nv)
    thue_tncn = calc_pit(tn_tinh_thue)

    thuc_lanh = round(tong_thu_nhap - bhxh_8_nv - bhyt_1_5_nv - bhtn_1_nv - thue_tncn)

    bhxh_17_5_ct = round(F * 0.175)
    bhyt_3_ct = round(F * 0.03)
    bhtn_1_ct = round(F * 0.01)

    return {
        'an_ca':          an_ca,
        'xang_xe':        xang_xe,
        'dien_thoai':     dien_thoai,
        'thuong_khac':    thuong_khac,
        'ho_tro_nuoi_con': ho_tro_nuoi_con,
        'tong_thu_nhap':  tong_thu_nhap,
        'tn_mien_thue':   tn_mien_thue,
        'tn_truoc_thue':  tn_truoc_thue,
        'npt':            npt,
        'giam_tru':       giam_tru,
        'bhxh_8_nv':      bhxh_8_nv,
        'bhyt_1_5_nv':    bhyt_1_5_nv,
        'bhtn_1_nv':      bhtn_1_nv,
        'tn_tinh_thue':   tn_tinh_thue,
        'thue_tncn':      thue_tncn,
        'thuc_lanh':      thuc_lanh,
        'bhxh_17_5_ct':   bhxh_17_5_ct,
        'bhyt_3_ct':      bhyt_3_ct,
        'bhtn_1_ct':      bhtn_1_ct,
    }


def seed_may_salary():
    """Main seeding function — call from Odoo shell."""
    Batch = env['hb.payslip.run'].sudo()
    Payslip = env['hb.payslip'].sudo()
    Employee = env['hr.employee'].sudo()
    Structure = env['hb.salary.structure'].sudo()
    Rule = env['hb.salary.rule'].sudo()

    # Check if May batch already exists
    existing = Batch.search([
        ('date_start', '>=', DATE_FROM),
        ('date_start', '<=', DATE_END),
    ])
    if existing:
        print(f"[WARN] Batch for May already exists: {existing.mapped('name')}")
        print("       Deleting existing batch and re-creating...")
        for b in existing:
            b.slip_ids.unlink()
            b.unlink()
        env.cr.commit()

    # 1. Create batch
    batch = Batch.create({
        'name': BATCH_NAME,
        'date_start': DATE_FROM,
        'date_end': DATE_END,
        'state': 'draft',
    })
    print(f"[OK] Created batch: {batch.name} (id={batch.id})")

    # 2. Find STRUCT_OFFLINE structure
    struct = Structure.search([('code', '=', 'STRUCT_OFFLINE')], limit=1)
    if not struct:
        print("[ERROR] STRUCT_OFFLINE not found! Run module upgrade first.")
        return
    print(f"[OK] Using structure: {struct.name} (id={struct.id})")

    # 3. Build rule lookup: code -> (rule_id, category_id, name, sequence)
    rules = Rule.search([('structure_id', '=', struct.id)])
    rule_map = {}
    for r in rules:
        rule_map[r.code] = {
            'rule_id': r.id,
            'category_id': r.category_id.id if r.category_id else False,
            'name': r.name,
            'sequence': r.sequence,
        }
    print(f"[OK] Found {len(rule_map)} salary rules")

    # 4. Create payslips for each employee
    created = 0
    skipped = 0

    for emp_code, nctt, base_salary, xang_xe, dien_thoai, thuong_khac, ho_tro_nuoi_con, npt in EMPLOYEES:
        # Find employee by code
        emp = Employee.search([('x_employee_code', '=', emp_code)], limit=1)
        if not emp:
            print(f"  [SKIP] Employee {emp_code} not found in DB")
            skipped += 1
            continue

        # Find contract
        Contract = env['hb.contract'].sudo()
        contract = Contract.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'open'),
        ], limit=1)
        if not contract:
            contract = Contract.search([
                ('employee_id', '=', emp.id),
            ], order='id desc', limit=1)

        # Compute salary
        amounts = compute_salary(
            nctt, base_salary, xang_xe, dien_thoai,
            thuong_khac, ho_tro_nuoi_con, npt,
        )

        # Build payslip lines
        line_vals = []
        for code, amount in amounts.items():
            rm = rule_map.get(code)
            if rm:
                line_vals.append((0, 0, {
                    'rule_id': rm['rule_id'],
                    'category_id': rm['category_id'],
                    'code': code,
                    'name': rm['name'],
                    'sequence': rm['sequence'],
                    'quantity': 1.0,
                    'rate': amount,
                    'amount': amount,
                }))
            else:
                # Rule not found in DB, create line without rule_id
                line_vals.append((0, 0, {
                    'code': code,
                    'name': code,
                    'sequence': 99,
                    'quantity': 1.0,
                    'rate': amount,
                    'amount': amount,
                }))

        # Build worked days
        worked_days_vals = [
            (0, 0, {
                'name': 'Ngày công chuẩn',
                'code': 'STANDARD',
                'sequence': 1,
                'number_of_days': STANDARD_DAYS,
                'number_of_hours': STANDARD_DAYS * 8,
            }),
            (0, 0, {
                'name': 'Ngày công thực tế',
                'code': 'WORK100',
                'sequence': 2,
                'number_of_days': nctt,
                'number_of_hours': nctt * 8,
            }),
        ]

        # Create payslip
        slip = Payslip.create({
            'employee_id': emp.id,
            'contract_id': contract.id if contract else False,
            'structure_id': struct.id,
            'payslip_run_id': batch.id,
            'date_from': DATE_FROM,
            'date_to': DATE_END,
            'state': 'done',  # already computed
            'line_ids': line_vals,
            'worked_days_ids': worked_days_vals,
        })

        created += 1
        print(f"  [OK] {emp_code} {emp.name:30s} NCTT={nctt:5.1f} "
              f"Net={amounts['thuc_lanh']:>12,.0f}")

    # 5. Close the batch
    batch.write({'state': 'close'})
    env.cr.commit()

    print(f"\n{'='*60}")
    print(f"DONE! Created {created} payslips, skipped {skipped}")
    print(f"Batch '{BATCH_NAME}' is CLOSED → visible in salary history")
    print(f"{'='*60}")
    print(f"\nTest APIs:")
    print(f"  GET /hocba-hrm/api/payroll/salary-history?month={MONTH}&year={YEAR}")
    print(f"  GET /hocba-hrm/api/payroll/transfer-list?month={MONTH}&year={YEAR}")


# ── Auto-run when piped into odoo shell ──────────────────────────────
try:
    seed_may_salary()
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
