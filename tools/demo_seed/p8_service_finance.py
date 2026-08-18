# -*- coding: utf-8 -*-
"""PHASE 8 — Nghỉ việc, yêu cầu dịch vụ nhân sự, quỹ tiền & phiếu thu/chi."""
exec(open('/tmp/seed/common.py').read())

import datetime

Off = env['hocba.offboarding'].sudo()
SReq = env['hocba.hr.request'].sudo()
SMsg = env['hocba.hr.request.message'].sudo()
Sender = env['hocba.hr.request.sender'].sudo()
Fund = env['hocba.fund'].sudo()
Vou = env['hocba.fin.voucher'].sudo()
Cat = {c.code: c for c in env['hocba.fin.category'].sudo().search([])}

hrm = emp('HB.02').user_id
acct = emp('HB.04').user_id
hr_officer = emp('HB.03').user_id

# ── nghỉ việc ────────────────────────────────────────────────────────────
CASES = [
    # code, nguồn, lý do, ngày dự kiến, trạng thái đích, ghi chú
    ('HB.28', 'self', 'voluntary', D(2026, 7, 31), 'done',
     'Chuyển vào TP.HCM sinh sống, xin thôi việc.'),
    ('HB.29', 'self', 'voluntary', D(2026, 9, 15), 'mgr_approved',
     'Tiếp tục học cao học, không sắp xếp được lịch trợ giảng.'),
    ('HB.27', 'self', 'other', D(2026, 9, 30), 'submitted',
     'Bận lịch học kỳ mới, xin dừng cộng tác bán thời gian.'),
]
for code, source, reason_type, leave_date, target, reason in CASES:
    e = emp(code)
    o = Off.search([('employee_id', '=', e.id)], limit=1)
    if not o:
        o = Off.create({
            'employee_id': e.id, 'source': source, 'reason_type': reason_type,
            'expected_leave_date': leave_date, 'reason': reason,
            'request_date': leave_date - datetime.timedelta(days=30),
            'note': 'Hồ sơ demo — quy trình thôi việc.',
        })
    try:
        if o.state == 'draft':
            o.action_submit()
        if target in ('mgr_approved', 'hr_approved', 'done') and o.state == 'submitted':
            o.with_user(e.parent_id.user_id or hrm).action_mgr_approve()
        if target in ('hr_approved', 'done') and o.state == 'mgr_approved':
            o.with_user(hrm).action_hr_approve()
        if target == 'done' and o.state == 'hr_approved':
            o.write({'chk_handover': True, 'chk_documents': True,
                     'chk_payroll': True, 'actual_leave_date': leave_date})
            o.with_user(hrm).action_done()
    except Exception as ex:
        env.cr.rollback()
        say('nghỉ việc %s: %s' % (code, str(ex)[:100]))
    say('nghỉ việc %-7s %-20s → %s' % (code, e.name, o.state))
env.cr.commit()

# ── yêu cầu dịch vụ nhân sự ──────────────────────────────────────────────
TYPE = {t.code: t for t in env['hocba.hr.request.type'].sudo().search([])}
TICKETS = [
    # code NV, loại, tiêu đề, nội dung, trạng thái, ẩn danh, đánh giá sao
    ('HB.07', 'confirm_work', 'Xin giấy xác nhận công tác làm hồ sơ vay',
     'Em cần giấy xác nhận đang công tác tại Học Bá để nộp ngân hàng, nhờ HR hỗ trợ ạ.',
     'closed', False, '5'),
    ('HB.13', 'confirm_income', 'Xác nhận thu nhập 6 tháng đầu 2026',
     'Nhờ HR xác nhận thu nhập từ 01/2026 đến 06/2026 giúp em.',
     'answered', False, None),
    ('HB.08', 'contract_copy', 'Xin bản sao y hợp đồng lao động',
     'Em làm mất bản hợp đồng, xin cấp lại 1 bản sao y.',
     'in_progress', False, None),
    ('HB.25', 'qna_payroll', 'Phụ cấp ăn trưa tháng 7 tính thiếu?',
     'Em thấy phụ cấp ăn trưa tháng 7 ít hơn tháng 6 dù đi làm đủ, nhờ anh chị kiểm tra.',
     'new', False, None),
    ('HB.10', 'reissue_badge', 'Cấp lại thẻ nhân viên',
     'Thẻ của em bị hỏng chip, không quẹt cửa được.',
     'new', False, None),
    ('HB.22', 'work_proposal', 'Đề xuất mua bản quyền phần mềm dựng giáo trình',
     'Nhóm R&D cần bản quyền phần mềm để chuẩn hoá giáo trình HSK, chi phí ~6 triệu/năm.',
     'in_progress', False, None),
    ('HB.14', 'feedback', 'Góp ý về không gian làm việc tầng 3',
     'Điều hoà tầng 3 kêu to, ảnh hưởng khi họp online với khách.',
     'closed', False, '4'),
    ('HB.24', 'complaint_mgr', 'Phản ánh việc phân ca chưa công bằng',
     'Em thấy lịch trực cuối tuần dồn vào một số bạn, mong được xem lại.',
     'in_progress', True, None),
    ('HB.19', 'other', 'Xin hỗ trợ thiết bị dạy online',
     'Micro của em hỏng, xin công ty hỗ trợ mua mới.',
     'answered', False, None),
    ('HB.26', 'qna_payroll', 'Hỏi về mức đóng BHXH sau khi tăng lương',
     'Sau khi điều chỉnh lương thì mức đóng BHXH thay đổi thế nào ạ?',
     'closed', False, '5'),
]
for code, tcode, subject, body, state, anon, rating in TICKETS:
    e = emp(code)
    t = TYPE.get(tcode)
    if not t or SReq.search_count([('subject', '=', subject)]):
        continue
    r = SReq.create({
        'type_id': t.id, 'subject': subject, 'body': body,
        'recipient_scope': t.default_recipient, 'is_anonymous': anon,
        'priority': 'urgent' if tcode in ('qna_payroll', 'complaint_mgr') else 'normal',
        'target_department_id': e.department_id.id,
        'state': 'new',
    })
    Sender.create({'request_id': r.id, 'employee_id': e.id,
                   'user_id': e.user_id.id, 'department_id': e.department_id.id})
    vals = {'state': state}
    if state != 'new':
        vals.update({'handler_id': hr_officer.id,
                     'claimed_at': dt(D(2026, 8, 6), 9)})
        SMsg.create({'request_id': r.id, 'author_id': hr_officer.id,
                     'author_role': 'handler',
                     'body': 'Chào bạn, HR đã tiếp nhận và đang xử lý yêu cầu này.'})
    if state in ('answered', 'closed'):
        vals['answered_at'] = dt(D(2026, 8, 7), 15)
        SMsg.create({'request_id': r.id, 'author_id': hr_officer.id,
                     'author_role': 'handler',
                     'body': 'HR đã xử lý xong, bạn kiểm tra lại giúp nhé.'})
    if state == 'closed':
        vals.update({'closed_at': dt(D(2026, 8, 8), 10),
                     'closed_reason': 'Người gửi xác nhận đã xử lý xong.'})
        if rating:
            vals['rating'] = rating
    r.write(vals)

# create_date mặc định = lúc chạy script (16/8), trong khi mốc tiếp nhận/trả
# lời đặt ở 6-8/8 → "thời gian xử lý trung bình" ra số âm. Lùi ngày tạo bằng
# SQL (create_date là cột hệ thống, ORM không cho ghi).
env.cr.execute(
    "UPDATE hocba_hr_request SET create_date = %s "
    "WHERE claimed_at IS NOT NULL AND create_date > claimed_at",
    (dt(D(2026, 8, 5), 8, 30),))
say('lùi ngày tạo %d yêu cầu dịch vụ' % env.cr.rowcount)
env.cr.commit()
env.invalidate_all()
say('yêu cầu dịch vụ:', SReq.search_count([]))

# ── quỹ tiền & phiếu thu/chi ─────────────────────────────────────────────
FUNDS = [
    ('QTM', 'Quỹ tiền mặt văn phòng', 'cash', 'Kế toán_HCNS', 50000000),
    ('TKNH', 'Tài khoản ngân hàng VCB', 'bank', 'Kế toán_HCNS', 850000000),
]
FD = {}
for code, name, ftype, dep_name, opening in FUNDS:
    f = Fund.search([('code', '=', code)], limit=1)
    vals = {'code': code, 'name': name, 'fund_type': ftype,
            'department_id': dept(dep_name).id, 'opening_balance': opening}
    f = f.write(vals) and f or (f if f else Fund.create(vals))
    FD[code] = Fund.search([('code', '=', code)], limit=1)
say('quỹ tiền:', [(f.code, f.name) for f in Fund.search([])])

VOUCHERS = [
    # ngày, quỹ, loại, mục, số tiền, diễn giải, đối tác, trạng thái
    (D(2026, 6, 5), 'TKNH', 'income', 'DT_BANHANG', 420000000, 'Học phí khoá hè đợt 1', 'Học viên khoá hè', 'posted'),
    (D(2026, 6, 28), 'TKNH', 'expense', 'TRA_LUONG', 285000000, 'Trả lương kỳ 06/2026', 'CBNV Học Bá', 'posted'),
    (D(2026, 7, 3), 'TKNH', 'income', 'DT_BANHANG', 385000000, 'Học phí khoá hè đợt 2', 'Học viên khoá hè', 'posted'),
    (D(2026, 7, 5), 'QTM', 'expense', 'CSVC', 18500000, 'Mua 5 bộ bàn ghế phòng học 302', 'Nội thất Hoà Phát', 'posted'),
    (D(2026, 7, 8), 'TKNH', 'expense', 'TIENNHA', 65000000, 'Tiền thuê mặt bằng tháng 7', 'Chủ nhà — 175 Trần Đại Nghĩa', 'posted'),
    (D(2026, 7, 10), 'TKNH', 'expense', 'ADS', 42000000, 'Chạy ads tuyển sinh khoá thu', 'Meta Ads', 'posted'),
    (D(2026, 7, 15), 'QTM', 'expense', 'SINHHOAT_VP', 3200000, 'Nước uống, văn phòng phẩm tháng 7', 'Cửa hàng Minh Long', 'posted'),
    (D(2026, 7, 20), 'TKNH', 'expense', 'BHXH', 58000000, 'Nộp BHXH quý III đợt 1', 'BHXH quận Hai Bà Trưng', 'posted'),
    (D(2026, 7, 25), 'QTM', 'expense', 'KHEN_THUONG', 12000000, 'Thưởng nhân viên xuất sắc Q2/2026', 'CBNV được vinh danh', 'posted'),
    (D(2026, 7, 28), 'TKNH', 'expense', 'TRA_LUONG', 292000000, 'Trả lương kỳ 07/2026', 'CBNV Học Bá', 'posted'),
    (D(2026, 7, 30), 'TKNH', 'income', 'THU_BAOLUU', 24000000, 'Học viên khôi phục lớp bảo lưu', 'Học viên bảo lưu', 'posted'),
    (D(2026, 8, 2), 'TKNH', 'income', 'DT_BANHANG', 460000000, 'Học phí khoá thu đợt 1', 'Học viên khoá thu', 'posted'),
    (D(2026, 8, 5), 'QTM', 'expense', 'SACH_HD', 8600000, 'In giáo trình HSK4 bản 2026', 'Nhà in Tân Việt', 'posted'),
    (D(2026, 8, 8), 'TKNH', 'expense', 'TIENNHA', 65000000, 'Tiền thuê mặt bằng tháng 8', 'Chủ nhà — 175 Trần Đại Nghĩa', 'approved'),
    (D(2026, 8, 10), 'TKNH', 'expense', 'ADS', 38000000, 'Chạy ads video ngắn tháng 8', 'TikTok Ads', 'approved'),
    (D(2026, 8, 11), 'QTM', 'expense', 'DIENNUOC', 9400000, 'Tiền điện nước tháng 7', 'EVN Hà Nội', 'approved'),
    (D(2026, 8, 12), 'QTM', 'expense', 'LIENHOAN', 15000000, 'Liên hoan tổng kết khoá hè', 'Nhà hàng Sen Tây Hồ', 'draft'),
    (D(2026, 8, 13), 'TKNH', 'expense', 'OUTSOURCE', 22000000, 'Thuê dựng video giới thiệu khoá thu', 'Studio Bối Bối', 'draft'),
    (D(2026, 8, 14), 'QTM', 'income', 'THU_KHAC', 5000000, 'Thu tiền bán giáo trình lẻ', 'Khách lẻ', 'draft'),
    (D(2026, 8, 15), 'TKNH', 'expense', 'INTERNET', 4200000, 'Cước internet + điện thoại tháng 8', 'Viettel', 'draft'),
]
n_v = 0
for day, fcode, vtype, ccode, amount, memo, partner, state in VOUCHERS:
    f, c = FD.get(fcode), Cat.get(ccode)
    if not f or not c:
        continue
    name = '%s/%s/%s' % ('PT' if vtype == 'income' else 'PC',
                         day.strftime('%Y%m'), '%04d' % (n_v + 1))
    if Vou.search_count([('memo', '=', memo), ('voucher_date', '=', day)]):
        continue
    v = Vou.create({
        'name': name, 'voucher_date': day, 'fund_id': f.id,
        'voucher_type': vtype, 'category_id': c.id, 'amount': amount,
        'memo': memo, 'partner_name': partner, 'source': 'manual',
        'state': 'draft',
    })
    if state in ('approved', 'posted'):
        v.write({'state': 'approved', 'approved_by': hrm.id,
                 'approved_date': dt(day, 16)})
    if state == 'posted':
        v.write({'state': 'posted', 'posted_by': acct.id,
                 'posted_date': dt(day, 17)})
    n_v += 1
env.cr.commit()
say('phiếu thu/chi:', Vou.search_count([]), '(+%d)' % n_v)

print('\nPHASE 8 XONG — %d đơn nghỉ việc, %d yêu cầu dịch vụ, %d quỹ, %d phiếu thu/chi, %d thông báo'
      % (Off.search_count([]), SReq.search_count([]), Fund.search_count([]),
         Vou.search_count([]), env['hb.notification'].sudo().search_count([])))
