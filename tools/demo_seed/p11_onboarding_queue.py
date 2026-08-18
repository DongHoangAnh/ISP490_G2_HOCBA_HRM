# -*- coding: utf-8 -*-
"""PHASE 11 — nạp lại hàng đợi màn Nhận việc.

Từ khi _close_probation chốt thử việc lúc hết chuỗi bước, NV xong hết bước sẽ
lên Chính thức và RỜI hàng đợi — đúng nghiệp vụ, nhưng làm màn Nhận việc trống
nếu bản demo chỉ còn các ca đã xong. Phase này thêm 4 NV thử việc rải các giai
đoạn để review được đủ bộ lọc của màn hình.

Khai đủ CCCD/MST/BHXH để người review bấm hết bước là thấy NV lên Chính thức
thật (thiếu hồ sơ thì hệ thống giữ Thử việc + chuông, cũng đúng nhưng khó demo).
Idempotent: NV đã tồn tại theo mã thì bỏ qua.
"""
exec(open('/tmp/seed/common.py').read())

Emp = env['hr.employee'].sudo()
Dept = env['hr.department'].sudo()
Job = env['hr.job'].sudo()
EType = env['hocba.employee.type'].sudo()

TEACHER = EType.search([('code', '=', 'teacher')], limit=1)
OFFICE = EType.search([('code', '=', 'office_staff')], limit=1)


def dept(name):
    return Dept.search([('name', '=', name)], limit=1)


def job(name, d):
    j = Job.search([('name', '=', name)], limit=1)
    return j or Job.create({'name': name, 'department_id': d.id})


# (mã, tên, phòng, vị trí, loại NV, hình thức, loại vị trí, số bước đã Đạt)
# Bể ứng viên: mỗi lần chạy chỉ lấy đủ để hàng đợi đạt TARGET. Review bấm hết
# bước cho một NV là NV đó lên Chính thức và rời hàng đợi (đúng nghiệp vụ), nên
# script phải "bù" được chứ không chỉ tạo một lần.
TARGET = 4
POOL = [
    ('HB.30', 'Đinh Thuỳ Dương', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung',
     TEACHER, 'offline', 'staff', 0),
    ('HB.31', 'Lâm Bảo Ngọc', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung',
     TEACHER, 'offline', 'staff', 1),
    ('HB.32', 'Vũ Đức Thắng', 'Kinh doanh', 'Chuyên viên Tư vấn tuyển sinh',
     OFFICE, 'offline', 'staff', 0),
    ('HB.33', 'Tạ Minh Châu', 'Marketing', 'Chuyên viên Marketing',
     OFFICE, 'offline', 'staff', 1),
    ('HB.34', 'Chu Khánh Linh', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung',
     TEACHER, 'offline', 'staff', 0),
    ('HB.35', 'Phùng Nhật Nam', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung',
     TEACHER, 'offline', 'staff', 1),
    ('HB.36', 'Trịnh Mỹ Duyên', 'Vận hành', 'Chuyên viên Vận hành',
     OFFICE, 'offline', 'staff', 0),
    ('HB.37', 'Đoàn Gia Bảo', 'Kinh doanh', 'Chuyên viên Tư vấn tuyển sinh',
     OFFICE, 'offline', 'staff', 1),
]

dang_cho = Emp.search_count([('x_employment_status', '=', 'probation')])
can_them = max(0, TARGET - dang_cho)
say('hàng đợi hiện có %d NV, cần thêm %d' % (dang_cho, can_them))

for i, (code, name, dep_name, job_name, etype, wform, ptype, passed) in \
        enumerate(POOL):
    if can_them <= 0:
        break
    if Emp.with_context(active_test=False).search(
            [('x_employee_code', '=', code)], limit=1):
        continue
    can_them -= 1
    d = dept(dep_name)
    e = Emp.create({
        'name': name, 'x_employee_code': code,
        'department_id': d.id, 'job_id': job(job_name, d).id,
        'job_title': job_name,
        'x_employment_status': 'probation',
        'x_work_form': wform, 'x_position_type': ptype,
        'x_employee_type_id': etype.id,
        'x_seniority_level': 'junior',
        # thử việc bắt đầu lệch nhau để cột "Ngày bắt đầu" có dữ liệu thật
        'x_probation_start': TODAY - datetime.timedelta(days=10 + i * 6),
        'birthday': datetime.date(1998 - i, 4 + i, 10 + i),
        'sex': 'female' if i % 2 else 'male', 'marital': 'single',
        'employee_type': 'employee', 'active': True,
        'place_of_birth': 'Hà Nội',
        'identification_id': '001096%06d' % (930 + i),
        'x_id_date_issue': datetime.date(2021, 3, 1),
        'x_id_place_issue': 'Cục Cảnh sát QLHC về TTXH',
        'x_pit_code': '8%09d' % (100000930 + i),
        'x_social_insurance_no': '01%08d' % (20000930 + i),
        'x_health_insurance_no': 'DN4010%09d' % (930 + i),
        'x_health_care_place': 'Bệnh viện Bạch Mai',
        'x_permanent_street': 'Số %d phố Lê Thanh Nghị' % (12 + i),
        'x_permanent_ward': 'Phường Bách Khoa',
        'x_current_same_as_permanent': True,
        'work_phone': '024 7300 %04d' % (1930 + i),
        'private_phone': '09%02d %03d %03d' % (30 + i, 930, 100 + i),
        'emergency_contact': 'Người thân — %s' % name.split()[-1],
        'emergency_phone': '098%03d%04d' % (930 + i, 2930 + i),
    })
    steps = e.x_onboarding_step_ids.sorted(lambda s: (s.sequence, s.id))
    for s in [x for x in steps if not x.is_independent][:passed]:
        if s.state == 'open' and s.step_type == 'evaluation':
            s.action_evaluate('pass', note='Đạt yêu cầu giai đoạn đầu.')
        elif s.state == 'open':
            s.action_complete(note='Đã hoàn thành.')
    e.invalidate_recordset()
    steps = e.x_onboarding_step_ids
    say('%s %s — %s: %d/%d bước, trạng thái %s' % (
        code, name, e.x_onboarding_template_id.name or '(chưa có quy trình)',
        len(steps.filtered(lambda s: s.state in ('done', 'skipped'))),
        len(steps), e.x_employment_status))
env.cr.commit()

print('\n--- hàng đợi Nhận việc ---')
for e in Emp.search([('x_employment_status', '=', 'probation')],
                    order='x_employee_code'):
    steps = e.x_onboarding_step_ids
    print('  %-8s %-20s %-30s %d/%d' % (
        e.x_employee_code, e.name, e.x_onboarding_template_id.name or '—',
        len(steps.filtered(lambda s: s.state in ('done', 'skipped'))),
        len(steps)))
