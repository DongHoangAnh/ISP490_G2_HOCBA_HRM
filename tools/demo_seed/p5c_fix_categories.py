# -*- coding: utf-8 -*-
"""PHASE 5c — Tách các dòng "trung gian" ra khỏi nhóm tiền của quy tắc lương.

VẤN ĐỀ (dữ liệu quy tắc trong DB local, không phải code module):
`tong_thu_nhap` và `thuc_lanh` cộng theo NHÓM (`categories.<code>`), nhưng
chính chúng và các dòng trung gian lại nằm CÙNG nhóm với thành phần của mình:

  nhóm "Tổng thu nhập" = tn_mien_thue + tn_truoc_thue + tong_thu_nhap
  nhóm "Thuế TNCN"     = tn_tinh_thue + thue_tncn
  nhóm "Phụ cấp"       = luong_co_ban + cong + ngay_nghi + nctt + phụ cấp thật

→ `categories.tong_thu_nhap` bị cộng 2 lần, `categories.thue_tncn` cộng cả
  thu nhập tính thuế (số dương) vào chỗ đáng lẽ là thuế (số âm), và số ngày
  công (23) bị cộng như tiền. Kết quả: THỰC LÃNH 111.399.610đ cho NV lương
  45.000.000đ — lớn hơn cả tổng thu nhập.

CÁCH VÁ (chỉ dữ liệu): chuyển các dòng chỉ mang tính tham chiếu/trung gian
sang nhóm riêng "Chỉ số tham chiếu" — chúng vẫn hiện trên phiếu và vẫn được
các rule khác đọc qua `rules.get('<code>')`, chỉ không còn bị nhóm tiền cộng.
Cách sửa gốc (đổi công thức hoặc tách nhóm ngay trong cấu hình lương) thuộc
chủ sở hữu module hocba_payroll.
"""
Cat = env['hb.salary.rule.category'].sudo()
Rule = env['hb.salary.rule'].sudo()

info = Cat.search([('code', '=', 'thong_tin')], limit=1)
if not info:
    info = Cat.create({'name': 'Chỉ số tham chiếu', 'code': 'thong_tin',
                       'sequence': 5})
    print('  tạo nhóm "Chỉ số tham chiếu" (thong_tin)')

MOVE = ['luong_co_ban', 'cong', 'ngay_nghi', 'nctt', 'npt', 'giam_tru',
        'tn_mien_thue', 'tn_truoc_thue', 'tn_tinh_thue']
for code in MOVE:
    r = Rule.search([('code', '=', code)], limit=1)
    if r and r.category_id != info:
        print('  %-16s %-22s → Chỉ số tham chiếu' % (code, r.category_id.name))
        r.write({'category_id': info.id})

# `luong_thoi_gian` phụ thuộc worked_days — module không sinh bản ghi
# hb.payslip.worked_days nên dòng này luôn = 0 và trùng vai trò với rule
# `luong`. Tắt để phiếu lương không có dòng 0 vô nghĩa.
lt = Rule.search([('code', '=', 'luong_thoi_gian')], limit=1)
if lt and lt.active:
    lt.write({'active': False})
    print('  tắt rule luong_thoi_gian (thiếu worked_days, trùng rule `luong`)')

env.cr.commit()

# ── tính lại toàn bộ phiếu lương ─────────────────────────────────────────
Slip = env['hb.payslip'].sudo()
for sl in Slip.search([]):
    st = sl.state
    try:
        if st != 'draft':
            sl.write({'state': 'draft'})
        sl.action_compute_sheet()
        if st != 'draft':
            sl.write({'state': st})
    except Exception as ex:
        env.cr.rollback()
        print('  tính lại lỗi %s: %s' % (sl.employee_id.name, str(ex)[:90]))
env.cr.commit()

print('\n=== phiếu lương mẫu sau khi vá ===')
for code in ('HB.01', 'HB.07', 'HB.18', 'HB.21'):
    e = env['hr.employee'].sudo().search([('x_employee_code', '=', code)], limit=1)
    sl = Slip.search([('employee_id', '=', e.id),
                      ('date_from', '=', '2026-07-01')], limit=1)
    if not sl:
        continue
    get = lambda c: sum(l.amount for l in sl.line_ids if l.code == c)
    print('  %-7s %-20s lương %12s | gross %12s | BH %11s | thuế %11s | thực lãnh %13s'
          % (code, e.name, '{:,.0f}'.format(get('luong')),
             '{:,.0f}'.format(get('tong_thu_nhap')),
             '{:,.0f}'.format(get('bhxh_8_nv') + get('bhyt_1_5_nv') + get('bhtn_1_nv')),
             '{:,.0f}'.format(get('thue_tncn')),
             '{:,.0f}'.format(get('thuc_lanh'))))
