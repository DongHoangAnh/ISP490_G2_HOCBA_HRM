# -*- coding: utf-8 -*-
"""PHASE 5d — Trả lại dòng lương gốc cho cấu trúc Offline + gom demo về 1 cấu trúc.

1. `luong_thoi_gian` (dòng lương chính của cấu trúc Offline) tính theo
   `worked_days.WORK100` — nhưng KHÔNG chỗ nào trong module sinh bản ghi
   `hb.payslip.worked_days`, nên ngày công luôn = 0 → lương gốc = 0.
   Vá dữ liệu: đổi sang lấy `rules.get('nctt')` — chính là số ngày công
   thực tế mà rule `cong` đã lookup từ bảng chấm công.

2. Cấu trúc "Lương Online (đơn giản)" chỉ có 2 rule (`luong`, `thuong`),
   KHÔNG có tổng thu nhập / bảo hiểm / thuế / thực lãnh → phiếu lương NV
   online luôn hiện 0đ. Đây là khoảng trống cấu hình của module lương.
   Bản demo cho toàn bộ hợp đồng dùng cấu trúc Offline (đầy đủ) để mọi
   phiếu lương đều ra số; cấu trúc Online giữ nguyên, chờ chủ sở hữu bổ sung.
"""
Rule = env['hb.salary.rule'].sudo().with_context(active_test=False)

lt = Rule.search([('code', '=', 'luong_thoi_gian')], limit=1)
if lt:
    lt.write({
        'active': True,
        'amount_python_compute': (
            "\n# Ngày công lấy từ rule `nctt` (= `cong` từ bảng chấm công +"
            "\n# ngày nghỉ tính lương). Module không sinh worked_days nên"
            "\n# không dùng worked_days.WORK100 được."
            "\nstd_days = inputs.STD_DAYS.amount or 24.0"
            "\ntotal_days = rules.get('nctt', 0) or 0.0"
            "\nratio = min(total_days / std_days, 1.0) if std_days else 0.0"
            "\nbase = contract.wage or 0.0"
            "\nresult = round(base * ratio)"
            "\nresult_qty = total_days"
            "\nresult_rate = round(base / std_days) if std_days else 0.0\n"),
    })
    print('  bật lại luong_thoi_gian, tính theo nctt')

OFFLINE_S = env['hb.salary.structure'].sudo().search(
    [('code', '=', 'STRUCT_OFFLINE')], limit=1)
moved = env['hb.contract'].sudo().search([('x_structure_id', '!=', OFFLINE_S.id)])
if moved:
    moved.write({'x_structure_id': OFFLINE_S.id})
    print('  chuyển %d hợp đồng sang cấu trúc Offline (đầy đủ)' % len(moved))
env.cr.commit()

Slip = env['hb.payslip'].sudo()
Slip.search([]).write({'structure_id': OFFLINE_S.id})
env.cr.commit()

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

print('\n=== phiếu lương 07/2026 sau khi vá ===')
for e in env['hr.employee'].sudo().search([], order='x_employee_code'):
    sl = Slip.search([('employee_id', '=', e.id),
                      ('date_from', '=', '2026-07-01')], limit=1)
    if not sl:
        continue
    g = lambda c: sum(l.amount for l in sl.line_ids if l.code == c)
    print('  %-7s %-20s HĐ %11s | công %5.1f | gross %11s | BH %10s | thuế %10s | thực lãnh %12s'
          % (e.x_employee_code, e.name[:20],
             '{:,.0f}'.format(sl.contract_id.wage), g('nctt'),
             '{:,.0f}'.format(g('tong_thu_nhap')),
             '{:,.0f}'.format(g('bhxh_8_nv') + g('bhyt_1_5_nv') + g('bhtn_1_nv')),
             '{:,.0f}'.format(g('thue_tncn')),
             '{:,.0f}'.format(g('thuc_lanh'))))
