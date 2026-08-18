# -*- coding: utf-8 -*-
"""PHASE 5 — Hợp đồng lao động, giờ dạy, 2 kỳ lương (07/2026 đã chốt, 08/2026 đang chạy).

Tính lương gọi thẳng `action_compute_sheet` (đồng bộ) thay vì endpoint async
của SPA — trong `odoo shell` không có thread nền để chờ.
"""
exec(open('/tmp/seed/common.py').read())

import datetime

Contract = env['hb.contract'].sudo()
Slip = env['hb.payslip'].sudo()
Run = env['hb.payslip.run'].sudo()
WE = env['hb.work.entry'].sudo()
Emp = env['hr.employee'].sudo()

STRUCT = {s.code: s for s in env['hb.salary.structure'].sudo().search([])}
OFFLINE_S, ONLINE_S = STRUCT.get('STRUCT_OFFLINE'), STRUCT.get('STRUCT_ONLINE')
WE_TYPE = env['hb.work.entry.type'].sudo().search(
    [('name', '=', 'Teaching Hours')], limit=1)

TEACHER_CODES = {'HB.17', 'HB.18', 'HB.19', 'HB.20', 'HB.21'}

# ── hợp đồng lao động ────────────────────────────────────────────────────
n_new = 0
for e in Emp.search([], order='x_employee_code'):
    if not e.x_employee_code:
        continue
    code = e.x_employee_code
    if Contract.search_count([('employee_id', '=', e.id)]):
        continue
    wage = e.version_id.wage or 0.0
    status = e.x_employment_status
    is_mgr = e.x_position_type == 'manager'
    is_teacher = code in TEACHER_CODES
    start = e.x_probation_start or D(2024, 1, 1)

    if status == 'official':
        ins, hd_type = 'standard', 'HĐLĐ không xác định thời hạn'
    elif status in ('probation', 'intern'):
        ins, hd_type = 'none', 'HĐ thử việc'
    elif status == 'advisor':
        ins, hd_type = 'tnld_0_5', 'HĐ cố vấn'
    else:
        ins, hd_type = 'none', 'HĐ cộng tác viên / bán thời gian'

    vals = {
        'employee_id': e.id,
        'name': '%s/%s — %s' % (hd_type, code, e.name),
        'date_start': start,
        'date_end': None if status == 'official' else (
            start + datetime.timedelta(days=180) if status in ('probation', 'intern')
            else D(2026, 12, 31)),
        'state': 'open',
        'wage': wage,
        'x_structure_id': (ONLINE_S if e.x_work_form == 'online' else OFFLINE_S).id,
        'x_insurance_policy': ins,
        'x_insurance_base': wage if ins == 'standard' else 0.0,
        'x_dependent_count': len(e.x_dependent_ids),
        'x_pc_position': 3000000 if is_mgr else 0,
        'x_pc_seniority': 500000 if e.x_seniority_level == 'senior' else 0,
        'x_sp_meal': 730000 if e.x_work_form == 'offline' else 0,
        'x_sp_phone': 200000 if is_mgr or code in ('HB.07', 'HB.08', 'HB.10') else 0,
        'x_sp_transport': 300000 if e.x_work_form == 'offline' else 0,
        'x_sp_uniform': 100000 if e.x_work_form == 'offline' else 0,
    }
    if is_teacher:
        vals.update({
            'x_teaching_hourly_rate': 180000,
            'x_rate_hsk_class': 220000,
            'x_rate_advanced_class': 260000,
            'x_standard_threshold': 60.0,
            'x_has_fixed_base': e.x_employment_status == 'official',
            'x_fixed_base': 6000000 if e.x_employment_status == 'official' else 0,
        })
    try:
        Contract.create(vals)
        n_new += 1
    except Exception as ex:
        env.cr.rollback()
        say('hợp đồng lỗi %s: %s' % (code, str(ex)[:100]))
env.cr.commit()
say('hợp đồng:', Contract.search_count([]), '(+%d)' % n_new)

# ── giờ dạy (work entry) từ lịch dạy đã diễn ra ──────────────────────────
LEVEL = {'HSK5-A1': 'hsk5', 'HSK4-B2': 'hsk4', 'HSK4-F1': 'hsk4',
         'HSK3-D1': 'intermediate', 'SC-E1': 'basic', 'GT-C1': 'basic'}
n_we = 0
sessions = env['hocba.teaching.session'].sudo().search([
    ('session_date', '>=', D(2026, 7, 1)), ('session_date', '<=', D(2026, 8, 15)),
    ('state', '=', 'planned')])
for s in sessions:
    h1, m1 = [int(x) for x in (s.start_time or '18:00').split(':')]
    h2, m2 = [int(x) for x in (s.end_time or '20:00').split(':')]
    ds = dt(s.session_date, h1, m1)
    if WE.search_count([('employee_id', '=', s.employee_id.id),
                        ('date_start', '=', ds)]):
        continue
    WE.create({
        'employee_id': s.employee_id.id,
        'work_entry_type_id': WE_TYPE.id,
        'date_start': ds, 'date_stop': dt(s.session_date, h2, m2),
        'state': 'validated',
        'x_class_code': s.class_id,
        'x_class_level': LEVEL.get(s.class_id, 'basic'),
    })
    n_we += 1
env.cr.commit()
say('giờ dạy (work entry):', WE.search_count([]), '(+%d)' % n_we)


def build_run(name, d1, d2, close):
    run = Run.search([('date_start', '=', d1), ('date_end', '=', d2)], limit=1)
    if not run:
        run = Run.create({'name': name, 'date_start': d1, 'date_end': d2})
    contracts = Contract.search([
        ('state', '=', 'open'), ('employee_id.active', '=', True),
        ('date_start', '<=', d2),
        '|', ('date_end', '=', False), ('date_end', '>=', d1)])
    have = set(run.slip_ids.mapped('employee_id').ids)
    for c in contracts:
        if c.employee_id.id in have:
            continue
        have.add(c.employee_id.id)
        Slip.create({'employee_id': c.employee_id.id, 'contract_id': c.id,
                     'date_from': d1, 'date_to': d2, 'payslip_run_id': run.id,
                     'structure_id': c.x_structure_id.id})
    env.cr.commit()
    ok = err = 0
    for sl in run.slip_ids:
        try:
            sl.action_compute_sheet()
            ok += 1
        except Exception as ex:
            env.cr.rollback()
            err += 1
            say('  tính lương lỗi %s: %s' % (sl.employee_id.name, str(ex)[:80]))
    env.cr.commit()
    say('%s — %d phiếu, tính OK %d, lỗi %d' % (name, len(run.slip_ids), ok, err))
    if close:
        for sl in run.slip_ids:
            try:
                sl.action_payslip_verify()
                sl.action_payslip_done()
            except Exception as ex:
                env.cr.rollback()
                say('  chốt lỗi %s: %s' % (sl.employee_id.name, str(ex)[:80]))
        try:
            run.action_close()
        except Exception as ex:
            env.cr.rollback()
            say('  đóng kỳ lỗi: %s' % str(ex)[:90])
    env.cr.commit()
    return run


run7 = build_run('Kỳ lương 07/2026', D(2026, 7, 1), D(2026, 7, 31), close=True)
run8 = build_run('Kỳ lương 08/2026', D(2026, 8, 1), D(2026, 8, 31), close=False)

# ── phản hồi của NV trên phiếu lương đã chốt ─────────────────────────────
CONFIRMED = {'HB.03', 'HB.04', 'HB.07', 'HB.08', 'HB.13', 'HB.14', 'HB.18',
             'HB.22', 'HB.24', 'HB.26'}
REJECTED = {'HB.10': 'Thiếu 1 ca OT ngày 25/7, nhờ HR kiểm tra lại.',
            'HB.25': 'Phụ cấp ăn trưa tính thiếu 2 ngày.'}
for sl in run7.slip_ids:
    code = sl.employee_id.x_employee_code
    if code in REJECTED:
        sl.write({'x_employee_confirm': 'rejected',
                  'x_employee_feedback': REJECTED[code],
                  'x_email_sent': True, 'x_email_sent_date': dt(D(2026, 8, 3), 9)})
    elif code in CONFIRMED:
        sl.write({'x_employee_confirm': 'confirmed',
                  'x_confirmed_date': dt(D(2026, 8, 4), 10),
                  'x_email_sent': True, 'x_email_sent_date': dt(D(2026, 8, 3), 9)})
    else:
        sl.write({'x_employee_confirm': 'pending',
                  'x_email_sent': True, 'x_email_sent_date': dt(D(2026, 8, 3), 9),
                  'x_confirm_deadline': dt(D(2026, 8, 10), 17)})

# thưởng / phạt trên kỳ đang chạy để demo cột điều chỉnh
BONUS = {'HB.07': (2000000, 'Vượt 120% chỉ tiêu tuyển sinh tháng 7'),
         'HB.13': (1500000, 'Bài viết đạt 50k lượt tiếp cận'),
         'HB.18': (1000000, 'Lớp HSK4-B2 đạt 100% học viên hài lòng')}
PENALTY = {'HB.10': (300000, 'Đi trễ 4 lần trong tháng')}
for sl in run8.slip_ids:
    code = sl.employee_id.x_employee_code
    if code in BONUS:
        amt, why = BONUS[code]
        sl.write({'x_bonus_extra': amt, 'x_bonus_reason': why})
    if code in PENALTY:
        amt, why = PENALTY[code]
        sl.write({'x_penalty_amount': amt, 'x_penalty_reason': why})
    try:
        sl.action_compute_sheet()
    except Exception:
        env.cr.rollback()
env.cr.commit()

tot7 = sum(l.amount for s in run7.slip_ids
           for l in s.line_ids if l.code == 'thuc_lanh')
print('\nPHASE 5 XONG — %d hợp đồng, %d giờ dạy, %d kỳ lương, %d phiếu '
      '(tổng thực lãnh 07/2026 ≈ %s đ)'
      % (Contract.search_count([]), WE.search_count([]), Run.search_count([]),
         Slip.search_count([]), '{:,.0f}'.format(tot7)))
