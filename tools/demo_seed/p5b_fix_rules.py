# -*- coding: utf-8 -*-
"""PHASE 5b — Vá dữ liệu quy tắc lương để kỳ lương demo ra số đúng.

Chỉ sửa DỮ LIỆU (bản ghi hb.salary.rule trong DB), KHÔNG đụng code module.
Ba vấn đề gặp khi tính thử lương trên DB local:

1. `_evaluate_rule_condition` (hocba_payroll/models/payslip.py) gọi
   `safe_eval(rule.condition_python, localdict)` ở CHẾ ĐỘ EVAL. Điều kiện
   viết theo chuẩn Odoo `result = <biểu thức>` là một CÂU LỆNH nên compile
   ở mode eval sẽ ném SyntaxError → rule bị bỏ qua, trả 0. Hậu quả: toàn bộ
   khối BHXH/BHYT/BHTN (cả phần công ty lẫn nhân viên) và hoa hồng sale
   luôn = 0 trên mọi phiếu lương.
   → Vá dữ liệu: viết lại điều kiện thành BIỂU THỨC thuần (bỏ `result =`).
   Cách sửa gốc nên là đổi `_evaluate_rule_condition` sang mode='exec' rồi
   đọc localdict['result'] — việc này thuộc module lương, cần chủ sở hữu.

2. Rule `luong_thoi_gian` tham chiếu `contract.x_is_sale` và
   `contract._hocba_sale_base()` — KHÔNG tồn tại ở bất kỳ đâu trong repo →
   AttributeError → dòng "Lương thời gian" = 0 trên mọi phiếu.

3. Có 3 rule bị nhân đôi (tong_thu_nhap, tam_ung_tru_khac, thuc_lanh).
"""
Rule = env['hb.salary.rule'].sudo()

# ── 1. điều kiện python: câu lệnh → biểu thức ────────────────────────────
n_cond = 0
for r in Rule.search([('condition_type', '=', 'python')]):
    src = (r.condition_python or '').strip()
    if not src.startswith('result'):
        continue
    expr = src.split('=', 1)[1].strip()
    r.write({'condition_python': expr})
    print('  điều kiện  %-16s %s' % (r.code, expr[:80]))
    n_cond += 1

# ── 2. bỏ nhánh sale không tồn tại trong "Lương thời gian" ───────────────
lt = Rule.search([('code', '=', 'luong_thoi_gian')], limit=1)
if lt and 'x_is_sale' in (lt.amount_python_compute or ''):
    lt.write({'amount_python_compute': (
        "\nstd_days = inputs.STD_DAYS.amount or 24.0"
        "\ntotal_days = ((worked_days.WORK100.number_of_days or 0.0)"
        "\n              + (worked_days.OT.number_of_days or 0.0))"
        "\nratio = total_days / std_days if std_days else 0.0"
        "\nbase = contract.wage or 0.0"
        "\nresult = round(base * ratio)"
        "\nresult_qty = total_days"
        "\nresult_rate = base / std_days if std_days else 0.0\n")})
    print('  sửa rule luong_thoi_gian: bỏ nhánh contract.x_is_sale')

hh = Rule.search([('code', '=', 'hoa_hong_sale')], limit=1)
if hh and 'x_is_sale' in (hh.condition_python or ''):
    # chưa có mô hình sale rate → tắt rule thay vì để nó ném lỗi mỗi lần tính
    hh.write({'condition_python': 'False', 'active': False})
    print('  tắt rule hoa_hong_sale (thiếu contract._hocba_sale_rate)')

# ── 3. dọn rule trùng mã (giữ bản id nhỏ nhất) ───────────────────────────
seen, dups = {}, Rule.browse()
for r in Rule.search([], order='id'):
    if r.code in seen:
        dups |= r
    else:
        seen[r.code] = r.id
if dups:
    print('  xoá %d rule trùng mã: %s' % (len(dups), dups.mapped('code')))
    dups.unlink()

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

sample = Slip.search([('date_from', '=', '2026-07-01')], limit=1)
print('\nPHASE 5b XONG — sửa %d điều kiện. Phiếu mẫu %s (%s):'
      % (n_cond, sample.number, sample.employee_id.name))
for l in sample.line_ids.sorted('sequence'):
    if l.code in ('luong_co_ban', 'luong_thoi_gian', 'tong_phu_cap',
                  'tong_thu_nhap', 'bhxh_8_nv', 'bhyt_1_5_nv', 'bhtn_1_nv',
                  'tn_tinh_thue', 'thue_tncn', 'thuc_lanh'):
        print('   %-18s %15s' % (l.code, '{:,.0f}'.format(l.amount)))
