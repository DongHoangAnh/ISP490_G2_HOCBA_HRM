# -*- coding: utf-8 -*-
"""PHASE 7 — Đánh giá định kỳ, thăng tiến, lộ trình sự nghiệp, bảng vinh danh.

Q2/2026 công bố xong (để xem điểm & xếp loại), Q3/2026 đang chấm dở
(nháp + đã chốt chưa công bố) — đủ 3 trạng thái phiếu trên một màn hình.
"""
exec(open('/tmp/seed/common.py').read())

Review = env['hb.performance.review'].sudo()
Promo = env['hr.promotion.history'].sudo()
Honor = env['hb.honor.entry'].sudo()
Emp = env['hr.employee'].sudo()

hrm = emp('HB.02').user_id
ceo = emp('HB.01').user_id

# ── lịch sử sự nghiệp: mốc vào công ty + lên chính thức ──────────────────
n_promo = 0
for e in Emp.search([], order='x_employee_code'):
    if not e.x_employee_code or not e.x_probation_start:
        continue
    wage = e.version_id.wage or 0.0
    if not Promo.search_count([('employee_id', '=', e.id),
                               ('x_change_type', '=', 'join')]):
        Promo.create({
            'employee_id': e.id, 'date_effective': e.x_probation_start,
            'x_change_type': 'join', 'approved_by': hrm.id,
            'to_job_id': e.job_id.id, 'to_department_id': e.department_id.id,
            'to_wage': wage * 0.85, 'x_employment_status': 'probation',
            'x_work_form': e.x_work_form,
            'decision_ref': 'QĐ-TD/%s' % e.x_employee_code.replace('.', ''),
            'reason': 'Tiếp nhận nhân sự mới, bắt đầu thử việc.',
            # BR: đổi lương phải có bằng chứng (link đánh giá/KPI) hoặc review_id
            'x_evidence_url': 'https://drive.hocba.vn/hs/%s/offer.pdf'
                              % e.x_employee_code.replace('.', ''),
        })
        n_promo += 1
    if e.x_official_date and not Promo.search_count(
            [('employee_id', '=', e.id), ('x_change_type', '=', 'probation')]):
        Promo.create({
            'employee_id': e.id, 'date_effective': e.x_official_date,
            'x_change_type': 'probation', 'approved_by': hrm.id,
            'from_job_id': e.job_id.id, 'to_job_id': e.job_id.id,
            'to_department_id': e.department_id.id,
            'from_wage': wage * 0.85, 'to_wage': wage,
            'x_employment_status': 'official', 'x_work_form': e.x_work_form,
            'decision_ref': 'QĐ-CT/%s' % e.x_employee_code.replace('.', ''),
            'reason': 'Hoàn thành thử việc, chuyển chính thức.',
            'x_evidence_url': 'https://drive.hocba.vn/hs/%s/danhgia-thuviec.pdf'
                              % e.x_employee_code.replace('.', ''),
        })
        n_promo += 1
env.cr.commit()
say('mốc lộ trình sự nghiệp:', Promo.search_count([]), '(+%d)' % n_promo)

# ── phiếu đánh giá ───────────────────────────────────────────────────────
SCORES = {  # điểm theo NV (dùng chung cho mọi tiêu chí, lệch nhẹ theo thứ tự)
    'HB.03': 4.5, 'HB.04': 4.0, 'HB.06': 4.5, 'HB.07': 5.0, 'HB.08': 4.0,
    'HB.10': 3.0, 'HB.12': 4.5, 'HB.13': 4.5, 'HB.14': 4.0, 'HB.17': 5.0,
    'HB.18': 4.5, 'HB.19': 4.0, 'HB.22': 4.0, 'HB.23': 4.5, 'HB.24': 4.0,
    'HB.25': 3.5, 'HB.26': 4.0, 'HB.28': 3.5, 'HB.29': 3.0, 'HB.01': 4.5,
    'HB.21': 3.5, 'HB.27': 3.5, 'HB.11': 4.0, 'HB.15': 3.5,
}
NOTES = {
    5.0: ('Xuất sắc, vượt kỳ vọng ở hầu hết tiêu chí.',
          'Em cảm ơn anh chị đã hỗ trợ trong quý.'),
    4.5: ('Hoàn thành tốt, chủ động và ổn định.',
          'Quý tới em muốn nhận thêm mảng đào tạo nội bộ.'),
    4.0: ('Đạt yêu cầu, cần chủ động hơn trong phối hợp.',
          'Em sẽ cải thiện việc báo cáo tiến độ.'),
    3.5: ('Đạt mức cơ bản, còn chậm ở một số đầu việc.',
          'Em cần thêm hướng dẫn ở phần chuyên môn.'),
    3.0: ('Chưa đạt kỳ vọng, cần kế hoạch cải thiện rõ ràng.',
          'Em nhận thấy cần chỉnh lại giờ giấc và tiến độ.'),
}


def fill(rec, score, publish):
    for line in rec.line_ids:
        line.write({'score': min(score, line.max_score),
                    'note': 'Theo dõi trong kỳ.'})
    mgr_note, self_note = NOTES.get(score, NOTES[4.0])
    rec.write({'manager_note': mgr_note, 'self_note': self_note,
               'hr_note': 'HR đã rà soát, số liệu khớp chấm công/nghỉ phép.',
               'evaluator_id': (rec.employee_id.parent_id.user_id.id
                                or hrm.id)})
    try:
        rec.compute_metrics()
    except Exception:
        env.cr.rollback()
    try:
        rec.action_confirm()
        if publish:
            rec.action_publish()
    except Exception as ex:
        env.cr.rollback()
        say('  phiếu %s: %s' % (rec.employee_id.x_employee_code, str(ex)[:80]))


for role in ('office', 'teacher'):
    r = Review.open_period(role, 'quarter', 2026, 2)
    say('mở kỳ Q2/2026 %-8s tạo %d, bỏ qua %d' % (role, r['created'], r['skipped']))
    r = Review.open_period(role, 'quarter', 2026, 3)
    say('mở kỳ Q3/2026 %-8s tạo %d, bỏ qua %d' % (role, r['created'], r['skipped']))
env.cr.commit()

# Q2: chấm hết + công bố
for rec in Review.search([('period_index', '=', 2), ('state', '=', 'draft')]):
    fill(rec, SCORES.get(rec.employee_id.x_employee_code, 4.0), publish=True)
env.cr.commit()

# Q3: 6 phiếu đã chốt chờ công bố, còn lại để nháp
done_q3 = 0
for rec in Review.search([('period_index', '=', 3), ('state', '=', 'draft')],
                         order='employee_id'):
    if done_q3 >= 6:
        break
    fill(rec, SCORES.get(rec.employee_id.x_employee_code, 4.0), publish=False)
    done_q3 += 1
env.cr.commit()

by_state = {}
for rec in Review.search([]):
    by_state[rec.state] = by_state.get(rec.state, 0) + 1
say('phiếu đánh giá:', Review.search_count([]), by_state)

# ── thăng tiến gắn với kỳ đánh giá ───────────────────────────────────────
PROMOTIONS = [
    ('HB.07', 'Chuyên viên Tư vấn tuyển sinh cấp cao', 12000000, 15000000,
     D(2026, 7, 1), 'Đạt 5.0 kỳ Q2/2026, dẫn đầu doanh số tuyển sinh.'),
    ('HB.18', 'Giáo viên chính tiếng Trung', 18000000, 21000000,
     D(2026, 7, 1), 'Kết quả lớp HSK4-B2 xuất sắc, hỗ trợ đào tạo GV mới.'),
    ('HB.13', 'Chuyên viên Content Marketing cấp cao', 12000000, 14500000,
     D(2026, 8, 1), 'Chuỗi bài viết vượt 150% chỉ tiêu tiếp cận.'),
]
for code, new_title, old_wage, new_wage, eff, reason in PROMOTIONS:
    e = emp(code)
    if Promo.search_count([('employee_id', '=', e.id),
                           ('x_change_type', '=', 'promotion')]):
        continue
    new_job = job(new_title, e.department_id)
    rv = Review.search([('employee_id', '=', e.id), ('period_index', '=', 2),
                        ('period_year', '=', 2026)], limit=1)
    Promo.create({
        'employee_id': e.id, 'date_effective': eff,
        'x_change_type': 'promotion', 'approved_by': ceo.id,
        'from_job_id': e.job_id.id, 'to_job_id': new_job.id,
        'to_department_id': e.department_id.id,
        'from_wage': old_wage, 'to_wage': new_wage,
        'x_employment_status': 'official', 'x_work_form': e.x_work_form,
        'review_id': rv.id or False, 'reason': reason,
        'decision_ref': 'QĐ-TT/%s/2026' % code.replace('.', ''),
        'x_evidence_url': 'https://drive.hocba.vn/hs/%s/danhgia-q2-2026.pdf'
                          % code.replace('.', ''),
        'allowance_note': 'Điều chỉnh phụ cấp trách nhiệm theo vị trí mới.',
    })
    e.write({'job_id': new_job.id, 'job_title': new_title})
    if e.version_id:
        e.version_id.write({'wage': new_wage})
env.cr.commit()
say('thăng tiến:', Promo.search_count([('x_change_type', '=', 'promotion')]))

# ── bảng vinh danh ───────────────────────────────────────────────────────
HONORS = [
    ('HB.07', 'promotion', D(2026, 7, 1), 'Thăng chức Chuyên viên Tư vấn cấp cao',
     'Dẫn đầu doanh số tuyển sinh 2 quý liên tiếp.', 1),
    ('HB.18', 'promotion', D(2026, 7, 1), 'Thăng chức Giáo viên chính',
     'Lớp HSK4-B2 đạt 100% học viên hài lòng.', 2),
    ('HB.17', 'achievement', D(2026, 7, 10), 'Giáo viên xuất sắc Q2/2026',
     'Điểm đánh giá 5.0, dẫn dắt chương trình đào tạo nội bộ.', 1),
    ('HB.13', 'achievement', D(2026, 8, 1), 'Nội dung ấn tượng nhất tháng 7',
     'Bài viết đạt hơn 50.000 lượt tiếp cận.', 3),
    ('HB.02', 'tenure', D(2026, 6, 1), 'Kỷ niệm 5 năm gắn bó',
     'Đồng hành cùng Học Bá từ những ngày đầu.', 1),
    ('HB.06', 'tenure', D(2026, 8, 2), 'Kỷ niệm 5 năm gắn bó',
     'Xây dựng đội ngũ Kinh doanh từ 2 lên 6 người.', 2),
    ('HB.24', 'other', D(2026, 8, 8), 'Sáng kiến xếp lịch lớp tự động',
     'Giảm 40% thời gian xếp lịch mỗi tháng.', 1),
]
for code, cat, day, title, desc, rank in HONORS:
    e = emp(code)
    if Honor.search_count([('employee_id', '=', e.id), ('title', '=', title)]):
        continue
    Honor.create({'employee_id': e.id, 'category': cat, 'date_awarded': day,
                  'title': title, 'description': desc, 'rank': rank,
                  'source': 'manual'})
env.cr.commit()

print('\nPHASE 7 XONG — %d phiếu đánh giá %s, %d mốc sự nghiệp, %d mục vinh danh'
      % (Review.search_count([]), by_state, Promo.search_count([]),
         Honor.search_count([])))
