# -*- coding: utf-8 -*-
"""PHASE 0 — Dọn sạch dữ liệu nghiệp vụ, GIỮ NGUYÊN dữ liệu cấu hình.

Xoá: nhân viên + toàn bộ bản ghi phát sinh quanh họ (chấm công, nghỉ phép,
lương, tuyển dụng, đánh giá, nghỉ việc, dịch vụ, dòng tiền, thông báo).
Giữ: loại nghỉ phép, quy tắc lương, template nhận việc, tiêu chí đánh giá,
loại yêu cầu dịch vụ, mục thu/chi, stage tuyển dụng, định dạng ngân hàng.

Commit sau MỖI model: một model lỗi thì rollback chỉ mất đúng model đó,
không kéo theo phần đã xoá trước (bài học lần chạy đầu).
"""

# Thứ tự quan trọng: con trước, cha sau — tránh vướng khoá ngoại.
ORDER = [
    'hocba.leave.session.resolution', 'hb.leave.adjustment',
    'hr.leave', 'hr.leave.allocation', 'hb.leave.policy.log',
    'hocba.attendance.request', 'hocba.shift.attendance', 'hocba.attendance',
    'hocba.work_shift', 'hocba.work_assignment', 'hocba.teaching.session',
    'hb.payslip.line', 'hb.payslip.worked_days', 'hb.payslip.input',
    'hb.payslip', 'hb.payslip.run', 'hb.bank.file', 'hb.work.entry',
    'hb.contract',
    'hb.interview.slot', 'hr.applicant', 'hb.recruitment.request',
    'hb.performance.review.line', 'hb.performance.review',
    'hocba.offboarding', 'hb.onboarding.step',
    'hr.employee.asset', 'hr.employee.dependent', 'hr.employee.skill',
    'hocba.hr.request.message', 'hocba.hr.request.sender', 'hocba.hr.request',
    'hocba.fin.voucher', 'hocba.fund',
    'hb.notification',
]

# BR-060 chặn unlink lịch sử thăng tiến/đánh giá (audit trail). Quy tắc đó
# đúng cho người dùng, nhưng đây là reset DB demo → xoá thẳng bằng SQL.
SQL_WIPE = [
    'hr_promotion_evaluation_line', 'hr_promotion_evaluation',
    'hb_honor_entry', 'hr_promotion_history',
]

for model in ORDER:
    M = env.get(model)
    if M is None:
        print('  skip (chưa cài)  %s' % model)
        continue
    recs = M.sudo().with_context(active_test=False).search([])
    n = len(recs)
    if not n:
        print('  %-34s 0' % model)
        continue
    try:
        recs.unlink()
        env.cr.commit()
        print('  %-34s xoá %d' % (model, n))
    except Exception as ex:
        env.cr.rollback()
        print('  %-34s LỖI: %s' % (model, str(ex)[:110]))

for table in SQL_WIPE:
    env.cr.execute('DELETE FROM %s' % table)
    print('  %-34s xoá %d (SQL)' % (table, env.cr.rowcount))
env.cr.commit()
env.invalidate_all()

# --- nhân viên: xoá hết, trừ NV gắn với tài khoản hệ thống (admin/OdooBot) ---
Emp = env['hr.employee'].sudo().with_context(active_test=False)
sys_uids = {1, env.ref('base.user_admin').id}
victims = Emp.search([])
keep = victims.filtered(lambda e: e.user_id.id in sys_uids)
kill = victims - keep
print('\n  hr.employee: %d bản ghi, giữ %d (tài khoản hệ thống)' % (len(victims), len(keep)))
for e in kill:
    name, code = e.name, e.x_employee_code or '-'
    try:
        e.unlink()
        env.cr.commit()
        print('    xoá  %-8s %s' % (code, name))
    except Exception as ex:
        env.cr.rollback()
        e.write({'active': False})
        env.cr.commit()
        msg = ' '.join(str(ex).split())
        print('    archive %-8s %-24s (%s)' % (code, name, msg[:150]))

# --- tài khoản: xoá user demo cũ, giữ tài khoản test_* đã ghi trong docs ---
KEEP_LOGINS = {'admin', '__system__', 'public', 'portaltemplate', 'sync4',
               'test_admin@hocba.vn', 'test_hrmanager@hocba.vn',
               'test_hr@hocba.vn', 'test_truongphong@hocba.vn',
               'test_giaovu@hocba.vn', 'test_employee@hocba.vn',
               'test_ctv@hocba.vn'}
for u in env['res.users'].sudo().with_context(active_test=False).search([]):
    if u.login in KEEP_LOGINS:
        continue
    login = u.login
    try:
        u.unlink()
        env.cr.commit()
        print('    xoá user  %s' % login)
    except Exception as ex:
        env.cr.rollback()
        print('    giữ user  %-28s (%s)' % (login, str(ex)[:60]))

# --- phòng ban: archive phòng rác, giữ 6 phòng chuẩn ---
KEEP_DEPTS = {'BOD', 'Kế toán_HCNS', 'Kinh doanh', 'Marketing',
              'Sản phẩm (R&D_SP)', 'Vận hành'}
Dept = env['hr.department'].sudo().with_context(active_test=False)
for d in Dept.search([]):
    if d.name in KEEP_DEPTS:
        d.write({'active': True, 'manager_id': False})
        continue
    nm = d.name
    try:
        d.unlink()
        env.cr.commit()
        print('    xoá phòng  %s' % nm)
    except Exception:
        env.cr.rollback()
        d.write({'active': False})
        env.cr.commit()
        print('    archive phòng  %s' % nm)

env.cr.commit()
print('\nPHASE 0 XONG. Còn lại: %d NV / %d phòng ban / %d user' % (
    env['hr.employee'].sudo().with_context(active_test=False).search_count([]),
    env['hr.department'].sudo().search_count([]),
    env['res.users'].sudo().search_count([])))
