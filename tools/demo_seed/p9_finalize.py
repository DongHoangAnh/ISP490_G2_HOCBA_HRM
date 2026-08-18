# -*- coding: utf-8 -*-
"""PHASE 9 — Dọn nốt + bảng tổng kết dữ liệu demo."""
exec(open('/tmp/seed/common.py').read())

Emp = env['hr.employee'].sudo().with_context(active_test=False)

# NV mặc định gắn với tài khoản admin (tên "Ad"/"Mitchell Admin") không thuộc
# công ty demo → archive để không lọt vào danh sách nhân sự.
for e in Emp.search([('x_employee_code', '=', False)]):
    if e.active:
        e.write({'active': False})
        say('archive NV không mã:', e.name)

# Tài khoản vai trò Admin: SPA mở khoá menu "Tài khoản"/"Cấu hình nhận việc"
# theo cờ isAdmin, còn backend lại kiểm hr.group_hr_user/manager → Admin
# không có nhóm HR sẽ thấy menu nhưng gọi API bị 403. Cấp nhóm HR cho tài
# khoản admin demo để luồng review không vướng; lỗi lệch FE/BE vẫn cần sửa
# ở backend (_is_hr / _hr_flags trong hocba_hrm/controllers/main.py).
admin = env['res.users'].sudo().search(
    [('login', '=', 'test_admin@hocba.vn')], limit=1)
if admin:
    gids = [env.ref(g).id for g in
            ('hr.group_hr_manager', 'hocba_finance.group_finance_manager')
            if env.ref(g, False)]
    admin.write({'group_ids': [(4, g) for g in gids]})
    say('cấp nhóm HR Manager + Finance cho', admin.login)
env.cr.commit()

# ── tổng kết ─────────────────────────────────────────────────────────────
def cnt(model, dom=None):
    M = env.get(model)
    return M.sudo().search_count(dom or []) if M is not None else -1


ROWS = [
    ('Nhân viên (đang làm)', 'hr.employee', []),
    ('Phòng ban', 'hr.department', []),
    ('Vị trí công việc', 'hr.job', []),
    ('Tài khoản nội bộ', 'res.users', [('share', '=', False)]),
    ('Chứng chỉ', 'hr.employee.skill', []),
    ('Người phụ thuộc', 'hr.employee.dependent', []),
    ('Tài sản cấp phát', 'hr.employee.asset', []),
    ('Bước nhận việc', 'hb.onboarding.step', []),
    ('Chấm công', 'hocba.attendance', []),
    ('Ca làm thêm / CTV', 'hocba.work_shift', []),
    ('Đơn chấm công', 'hocba.attendance.request', []),
    ('Buổi dạy', 'hocba.teaching.session', []),
    ('Quỹ phép (allocation)', 'hr.leave.allocation', []),
    ('Đơn nghỉ phép', 'hr.leave', []),
    ('Hợp đồng lao động', 'hb.contract', []),
    ('Giờ dạy (work entry)', 'hb.work.entry', []),
    ('Kỳ lương', 'hb.payslip.run', []),
    ('Phiếu lương', 'hb.payslip', []),
    ('Phiếu yêu cầu tuyển dụng', 'hb.recruitment.request', []),
    ('Ứng viên', 'hr.applicant', []),
    ('Slot phỏng vấn', 'hb.interview.slot', []),
    ('Phiếu đánh giá', 'hb.performance.review', []),
    ('Mốc lộ trình sự nghiệp', 'hr.promotion.history', []),
    ('Mục vinh danh', 'hb.honor.entry', []),
    ('Đơn nghỉ việc', 'hocba.offboarding', []),
    ('Yêu cầu dịch vụ NS', 'hocba.hr.request', []),
    ('Quỹ tiền', 'hocba.fund', []),
    ('Phiếu thu/chi', 'hocba.fin.voucher', []),
    ('Thông báo in-app', 'hb.notification', []),
]
print('\n' + '=' * 58)
print('DỮ LIỆU DEMO — DB hocba_hrm (local)')
print('=' * 58)
for label, model, dom in ROWS:
    print('  %-28s %6d' % (label, cnt(model, dom)))

print('\n--- nhân sự theo phòng ban ---')
for d in env['hr.department'].sudo().search([], order='name'):
    n = env['hr.employee'].sudo().search_count([('department_id', '=', d.id)])
    print('  %-22s %2d NV   TP: %s' % (d.name, n, d.manager_id.name or '—'))

print('\n--- nhân sự theo trạng thái ---')
by = {}
for e in env['hr.employee'].sudo().with_context(active_test=False).search(
        [('x_employee_code', '!=', False)]):
    by[e.x_employment_status] = by.get(e.x_employment_status, 0) + 1
for k in sorted(by):
    print('  %-14s %2d' % (k, by[k]))

print('\n--- tài khoản đăng nhập (mật khẩu chung: %s) ---' % PWD)
for e in env['hr.employee'].sudo().search(
        [('user_id', '!=', False)], order='x_employee_code'):
    u = e.user_id
    roles = []
    if u.has_group('base.group_system'):
        roles.append('Admin')
    if u.has_group('hr.group_hr_manager'):
        roles.append('HR Manager')
    elif u.has_group('hr.group_hr_user'):
        roles.append('HR Officer')
    if u.has_group('hocba_employees.group_hocba_giaovu'):
        roles.append('Giáo vụ')
    if u.has_group('hocba_finance.group_finance_manager'):
        roles.append('Kế toán')
    if env['hr.department'].sudo().search_count([('manager_id', '=', e.id)]):
        roles.append('Trưởng phòng')
    print('  %-7s %-24s %-30s %s' % (
        e.x_employee_code, e.name, u.login, ' / '.join(roles) or 'Nhân viên'))
