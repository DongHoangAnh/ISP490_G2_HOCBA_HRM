# -*- coding: utf-8 -*-
"""PHASE 4 — Quỹ phép theo chính sách + đơn nghỉ phép đủ trạng thái.

Chạy `_apply_leave_policy` cho từng NV (đúng đường đi thật của hệ thống),
sau đó kéo allocation về trọn năm 2026 để màn Quỹ phép không bị chia tỷ lệ
theo tháng còn lại — dữ liệu demo cần nhìn ra cả năm.
"""
exec(open('/tmp/seed/common.py').read())

import datetime

Leave = env['hr.leave'].sudo()
Alloc = env['hr.leave.allocation'].sudo()
Emp = env['hr.employee'].sudo()
LT = {t.name: t for t in env['hr.leave.type'].sudo().search(
    [('x_hb_managed', '=', True)])}
say('loại nghỉ do Học Bá quản lý:', sorted(LT))

ANNUAL = LT.get('Nghỉ Phép Năm')
SICK = LT.get('Nghỉ Ốm')
UNPAID = LT.get('Nghỉ Không Lương')
PERSONAL = LT.get('Nghỉ Việc Riêng')
MAKEUP = LT.get('Nghỉ Bù')
URGENT = LT.get('Nghỉ Khẩn Cấp')
CLASS_OFF = LT.get('Nghỉ Buổi Dạy')
MATERNITY = LT.get('Nghỉ Thai Sản')

# ── ngày làm bù (T7 đi làm) ──────────────────────────────────────────────
# Model chỉ nhận ngày TƯƠNG LAI (chấm công/lương ngày đã qua tính theo lịch
# lúc đó) → chỉ seed các thứ Bảy sắp tới.
WorkDay = env['hb.work.day'].sudo()
for d, nm in [(D(2026, 8, 29), 'Làm bù nghỉ lễ Quốc khánh 2/9'),
              (D(2026, 12, 26), 'Làm bù nghỉ Tết Dương lịch 2027')]:
    if not WorkDay.search_count([('date', '=', d)]):
        try:
            WorkDay.create({'date': d, 'name': nm})
        except Exception as ex:
            env.cr.rollback()
            say('bỏ qua ngày làm bù %s: %s' % (d, str(ex)[:70]))
say('ngày làm bù:', WorkDay.search_count([]))

# ── quỹ phép theo chính sách ─────────────────────────────────────────────
# _apply_leave_policy chỉ "expire" allocation cũ (đặt date_to) chứ không xoá,
# mà allocation đã dùng thì cũng không giảm/xoá được → chạy lại sẽ nhân đôi
# quỹ. Vì vậy chỉ áp chính sách cho NV CHƯA có allocation nào.
targets = Emp.search([('x_employment_status', 'not in', ('resigned',))])
n_pol = 0
for e in targets:
    if Alloc.with_context(active_test=False).search_count(
            [('employee_id', '=', e.id), ('x_from_policy', '=', True)]):
        continue
    try:
        e._apply_leave_policy(triggered_by='auto')
        n_pol += 1
    except Exception as ex:
        env.cr.rollback()
        say('policy lỗi %s: %s' % (e.x_employee_code, str(ex)[:80]))
say('áp chính sách nghỉ phép cho %d NV' % n_pol)
env.cr.commit()

# Kéo allocation về trọn năm: policy prorate theo số tháng còn lại của năm,
# demo cần thấy quota cả năm 2026 mới đối chiếu được với đơn đã dùng.
for a in Alloc.search([('x_from_policy', '=', True)]):
    rule = a.employee_id.x_current_policy_id
    days = rule.annual_days if rule and rule.annual_days else a.number_of_days
    a.write({'date_from': D(YEAR, 1, 1), 'date_to': D(YEAR, 12, 31),
             'number_of_days': days,
             'name': '%s — %s (%d)' % (a.holiday_status_id.name,
                                       a.employee_id.name, YEAR)})
env.cr.commit()
say('allocation:', Alloc.search_count([]),
    '— tổng ngày:', sum(Alloc.search([]).mapped('number_of_days')))


def approve(lv, refuse=False):
    """Đưa đơn về trạng thái cuối. hr.leave có thể 1 hoặc 2 bậc duyệt
    (validate1 → validate) nên phải gọi lặp cho tới khi chốt."""
    try:
        if refuse:
            lv.action_refuse()
            return
        for _ in range(3):
            if lv.state == 'validate':
                return
            lv.action_approve()
    except Exception as ex:
        say('  duyệt lỗi #%s: %s' % (lv.id, str(ex)[:90]))


# ── đơn nghỉ phép ────────────────────────────────────────────────────────
# code, loại, từ, đến, kết quả (validate/confirm/refuse/cancel), lý do
REQS = [
    ('HB.07', ANNUAL, D(2026, 2, 16), D(2026, 2, 18), 'validate', 'Về quê sau Tết.'),
    ('HB.08', ANNUAL, D(2026, 3, 9), D(2026, 3, 10), 'validate', 'Việc gia đình.'),
    ('HB.13', ANNUAL, D(2026, 4, 20), D(2026, 4, 24), 'validate', 'Nghỉ phép năm — du lịch Đà Nẵng.'),
    ('HB.14', SICK, D(2026, 5, 6), D(2026, 5, 7), 'validate', 'Sốt virus, có giấy khám bệnh.'),
    ('HB.18', ANNUAL, D(2026, 5, 18), D(2026, 5, 20), 'validate', 'Nghỉ phép năm.'),
    ('HB.22', PERSONAL, D(2026, 6, 1), D(2026, 6, 1), 'validate', 'Cưới em gái.'),
    ('HB.26', ANNUAL, D(2026, 6, 15), D(2026, 6, 17), 'validate', 'Nghỉ phép năm.'),
    ('HB.10', SICK, D(2026, 6, 25), D(2026, 6, 26), 'validate', 'Đau dạ dày, nhập viện 1 ngày.'),
    ('HB.04', ANNUAL, D(2026, 7, 6), D(2026, 7, 8), 'validate', 'Nghỉ phép năm.'),
    ('HB.19', CLASS_OFF, D(2026, 7, 13), D(2026, 7, 13), 'validate', 'Bận việc đột xuất, xin nghỉ buổi dạy.'),
    ('HB.25', ANNUAL, D(2026, 7, 20), D(2026, 7, 21), 'validate', 'Nghỉ phép năm.'),
    ('HB.03', ANNUAL, D(2026, 7, 27), D(2026, 7, 29), 'validate', 'Nghỉ phép năm.'),
    ('HB.12', ANNUAL, D(2026, 8, 3), D(2026, 8, 4), 'validate', 'Đưa con nhập học.'),
    ('HB.24', MAKEUP, D(2026, 8, 7), D(2026, 8, 7), 'validate', 'Nghỉ bù ca trực Chủ nhật 02/8.'),
    ('HB.27', UNPAID, D(2026, 8, 10), D(2026, 8, 12), 'validate', 'Việc riêng, xin nghỉ không lương.'),

    # đang chờ duyệt — để màn "Cần duyệt" có việc
    ('HB.09', ANNUAL, D(2026, 8, 20), D(2026, 8, 21), 'confirm', 'Về quê giỗ tổ.'),
    ('HB.13', ANNUAL, D(2026, 8, 24), D(2026, 8, 26), 'confirm', 'Nghỉ phép năm đợt 2.'),
    ('HB.18', CLASS_OFF, D(2026, 8, 25), D(2026, 8, 25), 'confirm', 'Đi hội thảo chuyên môn, cần người dạy thay.'),
    ('HB.08', PERSONAL, D(2026, 8, 27), D(2026, 8, 27), 'confirm', 'Đi khám sức khoẻ định kỳ.'),
    ('HB.25', SICK, D(2026, 8, 18), D(2026, 8, 19), 'confirm', 'Cảm cúm.'),
    ('HB.20', ANNUAL, D(2026, 9, 1), D(2026, 9, 2), 'confirm', 'Nghỉ lễ nối dài.'),

    # bị từ chối / đã huỷ
    ('HB.10', ANNUAL, D(2026, 8, 17), D(2026, 8, 21), 'refuse', 'Xin nghỉ 5 ngày giữa mùa tuyển sinh.'),
    ('HB.14', UNPAID, D(2026, 7, 15), D(2026, 7, 17), 'refuse', 'Trùng deadline chiến dịch tháng 7.'),
    ('HB.26', ANNUAL, D(2026, 9, 7), D(2026, 9, 8), 'cancel', 'Đổi kế hoạch, tự huỷ đơn.'),
]
n_new = 0
for code, ltype, d1, d2, target, reason in REQS:
    if not ltype:
        continue
    e = emp(code)
    if Leave.with_context(active_test=False).search_count(
            [('employee_id', '=', e.id), ('request_date_from', '=', d1),
             ('holiday_status_id', '=', ltype.id)]):
        continue
    lv = Leave.create({
        'employee_id': e.id, 'holiday_status_id': ltype.id,
        'request_date_from': d1, 'request_date_to': d2,
        'name': reason,
    })
    n_new += 1
    if target == 'validate':
        approve(lv)
    elif target == 'refuse':
        approve(lv, refuse=True)
    elif target == 'cancel':
        approve(lv)
        try:
            lv.action_cancel() if hasattr(lv, 'action_cancel') else lv.write({'state': 'cancel'})
        except Exception:
            env.cr.rollback()
            lv.write({'state': 'cancel'})
env.cr.commit()

# ── nghỉ khẩn cấp (báo sau) + đơn xin rút ────────────────────────────────
if URGENT:
    e = emp('HB.24')
    if not Leave.search_count([('employee_id', '=', e.id),
                               ('holiday_status_id', '=', URGENT.id)]):
        lv = Leave.create({
            'employee_id': e.id, 'holiday_status_id': URGENT.id,
            'request_date_from': D(2026, 8, 5), 'request_date_to': D(2026, 8, 5),
            'name': 'Người nhà nhập viện cấp cứu — báo sau theo BR khẩn cấp.',
            'x_is_emergency': True,
        })
        approve(lv)

# đơn NV tự huỷ (action_cancel của Odoo chỉ mở với đơn tương lai & đúng
# người tạo → demo set thẳng trạng thái cho gọn)
cancelled = Leave.search([('employee_id', '=', emp('HB.26').id),
                          ('request_date_from', '=', D(2026, 9, 7))], limit=1)
if cancelled and cancelled.state != 'cancel':
    cancelled.write({'state': 'cancel'})
    say('đơn đã huỷ:', cancelled.employee_id.name, cancelled.request_date_from)

# một đơn đã duyệt nhưng NV xin rút → chờ HR quyết định
target = Leave.search([('employee_id', '=', emp('HB.12').id),
                       ('state', '=', 'validate')], limit=1)
if target:
    target.write({'x_withdraw_state': 'pending',
                  'x_withdraw_reason': 'Kế hoạch thay đổi, xin rút đơn nghỉ.'})
    say('đơn xin rút:', target.employee_id.name, target.request_date_from)

env.cr.commit()
by_state = {}
for lv in Leave.with_context(active_test=False).search([]):
    by_state[lv.state] = by_state.get(lv.state, 0) + 1
print('\nPHASE 4 XONG — %d đơn nghỉ (+%d mới) %s, %d allocation' % (
    Leave.search_count([]), n_new, by_state, Alloc.search_count([])))
