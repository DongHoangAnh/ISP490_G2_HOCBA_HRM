# -*- coding: utf-8 -*-
"""PHASE 3 — Chấm công, ca làm/OT, đơn chấm công, lịch dạy.

Dải dữ liệu: 01/07/2026 → 15/08/2026 (đủ 1 kỳ đã đóng + 1 kỳ đang chạy).
Có cả ca đi trễ, về sớm, quên check-out, ngoài vùng geofence và nghi ngờ
khuôn mặt để các bộ lọc/cảnh báo trên màn Chấm công đều có bản ghi.
"""
exec(open('/tmp/seed/common.py').read())

import datetime

Att = env['hocba.attendance'].sudo()
Shift = env['hocba.work_shift'].sudo()
Req = env['hocba.attendance.request'].sudo()
Sess = env['hocba.teaching.session'].sudo()
Assign = env['hocba.work_assignment'].sudo()
Emp = env['hr.employee'].sudo()

# ── múi giờ: không set thì Odoo quy về UTC, giờ vào/ra lệch 7 tiếng ───────
env['res.users'].sudo().search([('share', '=', False)]).write(
    {'tz': 'Asia/Ho_Chi_Minh'})

# ── chính sách chấm công: toạ độ văn phòng thật (Bách Khoa, Hà Nội) ──────
OFFICE_LAT, OFFICE_LNG = 21.0037, 105.8420
pol = env['hocba.attendance.policy'].sudo().search([], limit=1)
if pol:
    pol.write({
        'name': 'Chính sách chấm công Học Bá',
        'office_lat': OFFICE_LAT, 'office_lng': OFFICE_LNG,
        'office_radius_m': 150,
        'office_map_url': 'https://maps.google.com/?q=%s,%s' % (OFFICE_LAT, OFFICE_LNG),
    })
say('chính sách chấm công:', pol.name, (pol.office_lat, pol.office_lng))

OFFLINE = Emp.search([('x_work_form', '=', 'offline'),
                      ('x_employment_status', '!=', 'resigned')],
                     order='x_employee_code')
# NV online cũng check-in qua app (không có geofence). Không seed công cho
# nhóm này thì rule `cong` lookup ra 0 ngày → phiếu lương của họ gần như rỗng.
ONLINE = Emp.search([('x_work_form', '=', 'online'),
                     ('x_employment_status', '!=', 'resigned')],
                    order='x_employee_code')
TEACHERS = [emp(c) for c in ('HB.17', 'HB.18', 'HB.19', 'HB.20', 'HB.21')]

# ── chấm công hằng ngày ──────────────────────────────────────────────────
FROM, TO = D(2026, 7, 1), D(2026, 8, 15)
n_new = 0
for e in OFFLINE:
    idx = int(e.x_employee_code.split('.')[-1])
    start_limit = e.x_probation_start or FROM
    for day in workdays(FROM, TO):
        if day < start_limit:
            continue
        if Att.search_count([('employee_id', '=', e.id), ('date', '=', day)]):
            continue
        r = random.random()
        # giờ vào: đa số đúng giờ, ~12% trễ, ~3% trễ nặng
        if r < 0.85:
            h, m = 7, random.choice([45, 50, 55, 58])
        elif r < 0.97:
            h, m = 8, random.choice([12, 18, 25])
        else:
            h, m = 9, random.choice([5, 20])
        vals = {
            'employee_id': e.id, 'source': 'checkin',
            'check_in': dt(day, h, m),
            'check_in_lat': OFFICE_LAT + random.uniform(-0.0004, 0.0004),
            'check_in_lng': OFFICE_LNG + random.uniform(-0.0004, 0.0004),
            'check_in_face_score': round(random.uniform(0.18, 0.45), 3),
        }
        rr = random.random()
        if rr < 0.04:                      # quên check-out
            pass
        else:
            if rr < 0.10:                  # về sớm
                oh, om = 16, random.choice([10, 30, 45])
            else:
                oh, om = 17, random.choice([32, 40, 50, 58])
            vals.update({
                'check_out': dt(day, oh, om),
                'check_out_lat': OFFICE_LAT + random.uniform(-0.0004, 0.0004),
                'check_out_lng': OFFICE_LNG + random.uniform(-0.0004, 0.0004),
                'check_out_face_score': round(random.uniform(0.18, 0.45), 3),
            })
        if random.random() < 0.025:         # chấm công ngoài vùng cho phép
            vals.update({'out_of_zone': True,
                         'check_in_lat': OFFICE_LAT + 0.011,
                         'check_in_lng': OFFICE_LNG - 0.008,
                         'notes': 'Chấm công tại cơ sở 2 — Cầu Giấy.'})
        if random.random() < 0.015:         # ảnh khuôn mặt lệch ngưỡng
            vals.update({'face_suspect': True,
                         'check_in_face_score': round(random.uniform(0.62, 0.78), 3)})
        if idx % 7 == 0 and day.day % 11 == 0:
            vals['notes'] = 'Đi gặp đối tác buổi sáng, về văn phòng lúc trưa.'
        Att.create(vals)
        n_new += 1

# NV online: làm 3 buổi/tuần (T2, T4, T6), khung giờ linh hoạt, không toạ độ.
for e in ONLINE:
    start_limit = e.x_probation_start or FROM
    for day in workdays(FROM, TO):
        if day < start_limit or day.weekday() not in (0, 2, 4):
            continue
        if Att.search_count([('employee_id', '=', e.id), ('date', '=', day)]):
            continue
        h, m = 8, random.choice([0, 10, 25])
        Att.create({
            'employee_id': e.id, 'source': 'checkin',
            'check_in': dt(day, h, m),
            'check_out': dt(day, 17, random.choice([30, 40, 55])),
            'notes': 'Làm việc online.',
        })
        n_new += 1
env.cr.commit()
say('bản ghi chấm công:', Att.search_count([]), '(+%d)' % n_new)

# ── phân công công việc ──────────────────────────────────────────────────
ASSIGNS = [
    ('HB.13', 'Chiến dịch Back-to-school 2026', 'Marketing Q3', D(2026, 7, 1), D(2026, 9, 30)),
    ('HB.14', 'Tối ưu quảng cáo tuyển sinh HSK', 'Ads HSK', D(2026, 7, 15), None),
    ('HB.22', 'Biên soạn giáo trình HSK 4 bản 2026', 'Giáo trình 2026', D(2026, 6, 1), D(2026, 12, 31)),
    ('HB.26', 'Chăm sóc lớp HSK3 khoá hè', 'Vận hành hè', D(2026, 6, 15), D(2026, 8, 31)),
]
for code, name, proj, d1, d2 in ASSIGNS:
    e = emp(code)
    if Assign.search_count([('employee_id', '=', e.id), ('name', '=', name)]):
        continue
    Assign.create({'employee_id': e.id, 'name': name, 'project_name': proj,
                   'assigned_date': d1, 'end_date': d2,
                   'job_title': e.job_title})
say('phân công:', Assign.search_count([]))

# ── ca làm thêm / ca CTV ─────────────────────────────────────────────────
hrm_user = emp('HB.02').user_id
SHIFTS = [
    # code, ngày, giờ bắt đầu, số giờ, loại, mức OT, trạng thái, lý do
    ('HB.13', D(2026, 7, 11), 9, 4, 'ot', '150', 'approved', 'Chạy bài đăng khai giảng cuối tuần'),
    ('HB.14', D(2026, 7, 18), 18, 3, 'ot', '150', 'approved', 'Đẩy chiến dịch quảng cáo trước hạn'),
    ('HB.08', D(2026, 7, 25), 18, 3, 'ot', '150', 'approved', 'Trực hotline tuyển sinh tối'),
    ('HB.22', D(2026, 8, 1), 9, 6, 'ot', '150', 'approved', 'Hoàn thiện bản thảo giáo trình'),
    ('HB.26', D(2026, 8, 2), 8, 8, 'ot', '300', 'approved', 'Trực khai giảng khoá hè (Chủ nhật)'),
    ('HB.07', D(2026, 8, 8), 18, 2, 'ot', '150', 'approved', 'Tư vấn phụ huynh ngoài giờ'),
    ('HB.13', D(2026, 8, 12), 18, 2, 'ot', '150', 'pending', 'Chuẩn bị ấn phẩm hội thảo'),
    ('HB.14', D(2026, 8, 13), 18, 3, 'ot', '150', 'pending', 'Xử lý sự cố landing page'),
    ('HB.24', D(2026, 8, 14), 18, 2, 'ot', '150', 'pending', 'Xếp lịch lớp mới cho tháng 9'),
    ('HB.10', D(2026, 8, 15), 9, 4, 'ot', '150', 'rejected', 'Đề xuất muộn, không có kế hoạch trước'),
    ('HB.21', D(2026, 7, 14), 18, 2, 'ctv', '100', 'approved', 'Ca dạy CTV lớp HSK4 tối'),
    ('HB.21', D(2026, 7, 21), 18, 2, 'ctv', '100', 'approved', 'Ca dạy CTV lớp HSK4 tối'),
    ('HB.21', D(2026, 8, 4), 18, 2, 'ctv', '100', 'approved', 'Ca dạy CTV lớp HSK4 tối'),
    ('HB.27', D(2026, 8, 5), 17, 3, 'ctv', '100', 'approved', 'Trợ giảng lớp giao tiếp'),
    ('HB.15', D(2026, 8, 11), 14, 4, 'ctv', '100', 'pending', 'Dựng video bài giảng mẫu'),
]
for code, day, h, dur, stype, lvl, state, reason in SHIFTS:
    e = emp(code)
    start = dt(day, h)
    if Shift.search_count([('employee_id', '=', e.id), ('start', '=', start)]):
        continue
    v = {'employee_id': e.id, 'start': start,
         'end': start + datetime.timedelta(hours=dur),
         'shift_type': stype, 'ot_level': lvl, 'state': state,
         'reason': reason}
    if state != 'pending':
        v.update({'reviewer_id': hrm_user.id,
                  'decision_date': dt(day, 20),
                  'review_note': 'Đồng ý theo kế hoạch phòng.' if state == 'approved'
                                 else 'Không duyệt: đăng ký sau khi ca đã diễn ra.'})
    Shift.create(v)
say('ca làm thêm/CTV:', Shift.search_count([]))

# ── đơn chấm công (quên/sai giờ) ─────────────────────────────────────────
REQS = [
    ('HB.07', D(2026, 7, 9), 7, 50, 17, 40, 'approved', 'Quên check-out do đi gặp phụ huynh cuối giờ.'),
    ('HB.13', D(2026, 7, 23), 7, 55, 17, 35, 'approved', 'Máy chấm công lỗi camera buổi sáng.'),
    ('HB.25', D(2026, 8, 5), 7, 48, 17, 45, 'approved', 'Mất mạng khi bấm check-in.'),
    ('HB.10', D(2026, 8, 11), 7, 50, 17, 40, 'pending', 'Đi công tác cơ sở 2, chấm ngoài vùng.'),
    ('HB.08', D(2026, 8, 13), 7, 45, 17, 50, 'pending', 'Quên check-out, nhờ HR bổ sung.'),
    ('HB.26', D(2026, 8, 6), 7, 30, 18, 30, 'rejected', 'Không có bằng chứng làm thêm giờ.'),
]
for code, day, ih, im, oh, om, state, reason in REQS:
    e = emp(code)
    if Req.search_count([('employee_id', '=', e.id), ('request_date', '=', day)]):
        continue
    att = Att.search([('employee_id', '=', e.id), ('date', '=', day)], limit=1)
    v = {'employee_id': e.id, 'request_date': day, 'reason': reason,
         'state': state, 'attendance_id': att.id or False,
         'proposed_check_in': dt(day, ih, im),
         'proposed_check_out': dt(day, oh, om)}
    if state != 'pending':
        v.update({'reviewer_id': hrm_user.id, 'decision_date': dt(day, 18),
                  'review_note': 'Đã đối chiếu camera, chấp nhận.'
                                 if state == 'approved' else 'Thiếu căn cứ.'})
    Req.create(v)
say('đơn chấm công:', Req.search_count([]))
env.cr.commit()

# ── lịch dạy (nguồn CMS) ─────────────────────────────────────────────────
CLASSES = [
    ('HB.17', 'HSK5-A1', 'HSK 5 — Lớp A1', [0, 2, 4], '18:00', '20:00'),
    ('HB.18', 'HSK4-B2', 'HSK 4 — Lớp B2', [1, 3], '18:00', '20:00'),
    ('HB.18', 'GT-C1', 'Giao tiếp cơ bản — C1', [5], '09:00', '11:00'),
    ('HB.19', 'HSK3-D1', 'HSK 3 — Lớp D1 (online)', [0, 2], '19:30', '21:30'),
    ('HB.20', 'SC-E1', 'Sơ cấp 1 — Lớp E1', [1, 3], '17:30', '19:30'),
    ('HB.21', 'HSK4-F1', 'HSK 4 — Lớp F1 (CTV)', [2, 5], '18:00', '20:00'),
]
S_FROM, S_TO = D(2026, 7, 1), D(2026, 9, 30)
n_sess = 0
for code, cid, cname, weekdays_, t1, t2 in CLASSES:
    e = emp(code)
    d = S_FROM
    while d <= S_TO:
        if d.weekday() in weekdays_:
            sid = 'CMS-%s-%s' % (cid, d.strftime('%Y%m%d'))
            if not Sess.search_count([('cms_session_id', '=', sid)]):
                Sess.create({
                    'cms_session_id': sid, 'employee_id': e.id,
                    'class_id': cid, 'class_name': cname,
                    'session_date': d, 'start_time': t1, 'end_time': t2,
                    'state': 'planned',
                })
                n_sess += 1
        d += datetime.timedelta(days=1)
say('buổi dạy:', Sess.search_count([]), '(+%d)' % n_sess)

env.cr.commit()
print('\nPHASE 3 XONG — %d chấm công, %d ca làm, %d đơn, %d buổi dạy, %d phân công' % (
    Att.search_count([]), Shift.search_count([]), Req.search_count([]),
    Sess.search_count([]), Assign.search_count([])))
