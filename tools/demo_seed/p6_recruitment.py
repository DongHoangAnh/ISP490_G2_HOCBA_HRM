# -*- coding: utf-8 -*-
"""PHASE 6 — Phiếu yêu cầu tuyển dụng, ứng viên rải đủ 10 bước, lịch phỏng vấn."""
exec(open('/tmp/seed/common.py').read())

import datetime

Req = env['hb.recruitment.request'].sudo()
App = env['hr.applicant'].sudo()
Slot = env['hb.interview.slot'].sudo()
Stage = env['hr.recruitment.stage'].sudo()

ST = {s.name: s for s in Stage.search([], order='sequence')}
S = lambda n: ST.get(n) and ST[n].id

# ── phiếu yêu cầu tuyển dụng ─────────────────────────────────────────────
REQUESTS = [
    # khoá, phòng, chức danh, SL, lý do, level, state, lương từ-đến, ngày cần
    ('GV-HSK', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung', 3, 'expansion',
     'mid', 'recruiting', 15000000, 22000000, D(2026, 9, 15),
     'Mở thêm 3 lớp HSK4-5 cho khoá mùa thu.'),
    ('TVTS', 'Kinh doanh', 'Tư vấn tuyển sinh', 2, 'expansion',
     'junior', 'recruiting', 9000000, 14000000, D(2026, 9, 1),
     'Tăng đội tư vấn phục vụ mùa cao điểm tháng 9.'),
    ('TG', 'Vận hành', 'Trợ giảng', 2, 'replacement',
     'fresher', 'recruiting', 7000000, 9500000, D(2026, 9, 20),
     'Bù 2 trợ giảng nghỉ việc quý III.'),
    ('MKT-VIDEO', 'Marketing', 'Chuyên viên Video Marketing', 1, 'new',
     'mid', 'submitted', 13000000, 18000000, D(2026, 10, 1),
     'Mảng video ngắn chưa có người phụ trách.'),
    ('KT', 'Kế toán_HCNS', 'Kế toán thanh toán', 1, 'new',
     'junior', 'draft', 10000000, 13000000, D(2026, 10, 15),
     'Chia tải cho kế toán tổng hợp.'),
    ('GV-ONLINE', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung online', 2, 'expansion',
     'junior', 'closed', 12000000, 16000000, D(2026, 7, 1),
     'Đã tuyển đủ cho lớp online khoá hè.'),
]
hrm_user = emp('HB.02').user_id
ceo_user = emp('HB.01').user_id
REQ = {}
for key, dep_name, title, qty, reason, level, state, s_from, s_to, need_by, note in REQUESTS:
    d = dept(dep_name)
    r = Req.search([('job_title', '=', title), ('department_id', '=', d.id)], limit=1)
    vals = {
        'department_id': d.id, 'job_title': title, 'qty_expected': qty,
        'reason': reason, 'level': level, 'state': state,
        'salary_from': s_from, 'salary_to': s_to,
        'salary_range': '%d - %d tr' % (s_from // 1000000, s_to // 1000000),
        'expected_start_date': need_by, 'date_request': need_by - datetime.timedelta(days=45),
        'job_id': job(title, d).id,
        'requester_id': d.manager_id.user_id.id or hrm_user.id,
        'manager_id': d.manager_id.user_id.id or hrm_user.id,
        'hr_manager_id': hrm_user.id, 'director_id': ceo_user.id,
        'work_type': 'onsite' if 'online' not in title else 'remote',
        'education': 'bachelor', 'experience_years': 1.0 if level in ('fresher', 'junior') else 3.0,
        'language_requirement': 'HSK 5 trở lên' if 'Giáo viên' in title else 'Giao tiếp tiếng Trung cơ bản',
        'skill_description': note, 'note': '<p>%s</p>' % note,
    }
    if r:
        r.write(vals)
    else:
        r = Req.create(vals)
    REQ[key] = r
    say('phiếu YCTD %-10s %-32s SL=%d  %s' % (key, title, qty, state))
env.cr.commit()

# ── ứng viên ─────────────────────────────────────────────────────────────
# họ tên, phiếu, bước, đánh giá CV, kết quả PV, lương mong muốn, ưu tiên
CAND = [
    # đang ở đầu phễu
    ('Nguyễn Khánh Chi', 'GV-HSK', 'Đăng tuyển & tổng hợp CV', None, None, 16000000, '1'),
    ('Trần Bảo Anh', 'GV-HSK', 'Đăng tuyển & tổng hợp CV', None, None, 15000000, '0'),
    ('Lê Hồng Sơn', 'GV-HSK', 'Lọc CV', 'pass', None, 18000000, '2'),
    ('Phạm Diệu Linh', 'GV-HSK', 'Lọc CV', 'potential', None, 17000000, '1'),
    ('Vũ Thanh Tùng', 'GV-HSK', 'Lọc CV', 'fail', None, 25000000, '0'),
    ('Đỗ Mai Phương', 'GV-HSK', 'Lên lịch phỏng vấn', 'pass', None, 19000000, '2'),
    ('Hoàng Anh Tuấn', 'GV-HSK', 'Hẹn & mời phỏng vấn', 'pass', None, 18500000, '1'),
    ('Ngô Thu Hiền', 'GV-HSK', 'Phỏng vấn', 'pass', None, 20000000, '2'),
    ('Bùi Quốc Khánh', 'GV-HSK', 'Kết quả phỏng vấn', 'pass', 'pass', 21000000, '3'),
    ('Đinh Thị Kim Oanh', 'GV-HSK', 'Kết quả phỏng vấn', 'pass', 'fail', 24000000, '0'),
    ('Lý Minh Châu', 'GV-HSK', 'Gửi Offer', 'pass', 'pass', 20000000, '3'),
    ('Trịnh Hải Đăng', 'GV-HSK', 'Onboarding', 'pass', 'pass', 19500000, '3'),

    ('Nguyễn Thuý Quỳnh', 'TVTS', 'Đăng tuyển & tổng hợp CV', None, None, 10000000, '0'),
    ('Phan Đức Hùng', 'TVTS', 'Lọc CV', 'pass', None, 11000000, '1'),
    ('Trương Ngọc Bích', 'TVTS', 'Lọc CV', 'contact_later', None, 12000000, '0'),
    ('Đặng Văn Toàn', 'TVTS', 'Lên lịch phỏng vấn', 'pass', None, 11500000, '1'),
    ('Mai Thị Hạnh', 'TVTS', 'Phỏng vấn', 'pass', None, 10500000, '2'),
    ('Cao Minh Trí', 'TVTS', 'Kết quả phỏng vấn', 'pass', 'pass', 12000000, '3'),
    ('Lương Thảo Vy', 'TVTS', 'Gửi Offer', 'pass', 'pass', 11800000, '3'),
    ('Hồ Sỹ Nam', 'TVTS', 'Kết quả phỏng vấn', 'pass', 'potential', 13500000, '1'),

    ('Nguyễn Hà My', 'TG', 'Đăng tuyển & tổng hợp CV', None, None, 8000000, '0'),
    ('Trần Duy Mạnh', 'TG', 'Lọc CV', 'pass', None, 8500000, '1'),
    ('Lê Ngọc Trâm', 'TG', 'Hẹn & mời phỏng vấn', 'pass', None, 9000000, '1'),
    ('Phạm Gia Huy', 'TG', 'Phỏng vấn', 'pass', None, 8800000, '2'),
    ('Vũ Hoài Thu', 'TG', 'Kết quả phỏng vấn', 'pass', 'pass', 9200000, '3'),
    ('Đỗ Nhật Minh', 'TG', 'Lọc CV', 'fail', None, 12000000, '0'),

    ('Nguyễn Tiến Dũng', 'MKT-VIDEO', 'Đăng tuyển & tổng hợp CV', None, None, 15000000, '1'),
    ('Trần Yến Nhi', 'MKT-VIDEO', 'Lọc CV', 'pass', None, 16000000, '2'),
    ('Lê Bá Thành', 'MKT-VIDEO', 'Lọc CV', 'potential', None, 17500000, '1'),

    # đã tuyển xong (phiếu GV-ONLINE)
    ('Nguyễn Thuỳ Dương', 'GV-ONLINE', 'Bàn giao nhân sự', 'pass', 'pass', 17000000, '3'),
    ('Chu Tuyết Nhi', 'GV-ONLINE', 'Bàn giao nhân sự', 'pass', 'pass', 8000000, '2'),
    ('Trần Quang Vũ', 'GV-ONLINE', 'Kết quả phỏng vấn', 'pass', 'fail', 22000000, '0'),
]

SOURCES = ['Facebook', 'TopCV', 'Giới thiệu nội bộ', 'Website Học Bá', 'LinkedIn']
Src = env['utm.source'].sudo()
src_recs = []
for nm in SOURCES:
    s = Src.search([('name', '=', nm)], limit=1) or Src.create({'name': nm})
    src_recs.append(s)

interviewers = [emp('HB.02').user_id.id, emp('HB.17').user_id.id,
                emp('HB.06').user_id.id]
n_app = 0
for i, (name, key, stage_name, cvres, ivres, salary, prio) in enumerate(CAND, 1):
    if App.with_context(active_test=False).search_count([('partner_name', '=', name)]):
        continue
    r = REQ[key]
    slug = 'ungvien%02d' % i
    stage_seq = ST[stage_name].sequence
    vals = {
        'partner_name': name,
        'email_from': '%s@gmail.com' % slug,
        'partner_phone': '09%02d%03d%03d' % (20 + i % 60, 100 + i, 700 + i),
        'job_id': r.job_id.id, 'hb_request_id': r.id,
        'stage_id': ST[stage_name].id,
        'department_id': r.department_id.id,
        'salary_expected': salary,
        'priority': prio,
        'source_id': src_recs[i % len(src_recs)].id,
        'date_received': D(2026, 7, 1) + datetime.timedelta(days=i % 40),
        'availability': D(2026, 9, 1) + datetime.timedelta(days=i % 20),
        'cv_link': 'https://drive.google.com/file/d/demo-cv-%s' % slug,
        'cv_note': 'CV nộp qua %s.' % src_recs[i % len(src_recs)].name,
        'applicant_notes': '<p>Ứng viên cho vị trí %s.</p>' % r.job_title,
    }
    if cvres:
        vals['cv_filter_result'] = cvres
    if stage_seq >= 50:
        vals.update({
            'interview_date': D(2026, 8, 3) + datetime.timedelta(days=i % 12),
            'interview_time': '%02d:00' % (9 + i % 7),
            'interviewer_ids': [(6, 0, [interviewers[i % len(interviewers)]])],
            'attendance_status': 'present',
        })
    if ivres:
        vals['interview_result'] = ivres
    if stage_seq >= 80 and ivres == 'pass':
        vals.update({'salary_proposed': int(salary * 0.95),
                     'offer_content': 'Offer mức %s đ/tháng, thử việc 2 tháng.'
                                      % '{:,.0f}'.format(salary * 0.95)})
    if stage_seq >= 90:
        vals['onboard_result'] = 'arrived'
    App.create(vals)
    n_app += 1
env.cr.commit()
say('ứng viên:', App.search_count([]), '(+%d)' % n_app)

# ── lịch rảnh phỏng vấn ──────────────────────────────────────────────────
n_slot = 0
for uid_ in interviewers:
    for k in range(6):
        day = TODAY + datetime.timedelta(days=1 + k)
        if day.weekday() >= 5:
            continue
        start = dt(day, 9 + (k % 3) * 2)
        if Slot.search_count([('user_id', '=', uid_), ('start_datetime', '=', start)]):
            continue
        Slot.create({'user_id': uid_, 'start_datetime': start,
                     'stop_datetime': start + datetime.timedelta(hours=1),
                     'notes': 'Slot phỏng vấn vòng chuyên môn.'})
        n_slot += 1
# gán 2 ứng viên vào slot
booked = App.search([('stage_id', '=', S('Hẹn & mời phỏng vấn'))], limit=2)
slots = Slot.search([], limit=2)
for s, a in zip(slots, booked):
    s.write({'applicant_ids': [(4, a.id)]})
env.cr.commit()
say('slot phỏng vấn:', Slot.search_count([]), '(+%d)' % n_slot)

by_stage = {}
for a in App.search([]):
    by_stage[a.stage_id.name] = by_stage.get(a.stage_id.name, 0) + 1
print('\nPHASE 6 XONG — %d phiếu YCTD, %d ứng viên, %d slot' % (
    Req.search_count([]), App.search_count([]), Slot.search_count([])))
for k in sorted(by_stage, key=lambda n: ST[n].sequence if n in ST else 999):
    print('   %-28s %d' % (k, by_stage[k]))
