# -*- coding: utf-8 -*-
"""PHASE 1 — Phòng ban, vị trí, 28 hồ sơ nhân viên, tài khoản & phân quyền.

Đủ 4 trục hồ sơ (trạng thái × hình thức × loại vị trí × thâm niên), 6 phòng
ban đều có trưởng phòng, và mỗi NV đều có tài khoản đăng nhập (mật khẩu
chung Hocba@2026) để review được cả màn quản lý lẫn self-service.
"""
exec(open('/tmp/seed/common.py').read())

Emp = env['hr.employee'].sudo()
Users = env['res.users'].sudo()
Dept = env['hr.department'].sudo()

# ── phòng ban ────────────────────────────────────────────────────────────
for name in DEPTS:
    if not dept(name):
        Dept.create({'name': name})
say('phòng ban:', [d.name for d in Dept.search([])])

ETYPE = {t.name: t for t in env['hocba.employee.type'].sudo().search([])}
OFFICE = ETYPE.get('Nhân viên văn phòng')
TEACHER = ETYPE.get('Giáo viên')
CTV = ETYPE.get('Cộng tác viên')

# ── danh sách nhân sự ────────────────────────────────────────────────────
# code, họ tên, phòng, vị trí, trạng thái, hình thức, loại vị trí, thâm niên,
# lương, ngày sinh, giới tính, ngày vào (=mốc thâm niên), ngày lên chính thức,
# trưởng phòng?, login, vai trò, loại NV nghỉ phép
R = [
    ('HB.01', 'Nguyễn Hoàng Nam', 'BOD', 'Giám đốc điều hành', 'official', 'offline', 'manager', 'senior',
     45000000, D(1982, 4, 12), 'male', D(2021, 1, 4), D(2021, 4, 4), True, 'nam.nh@hocba.vn', 'manager', 'fulltime'),
    ('HB.02', 'Đỗ Quang Huy', 'Kế toán_HCNS', 'Trưởng phòng Hành chính Nhân sự', 'official', 'offline', 'manager', 'senior',
     28000000, D(1988, 9, 3), 'male', D(2021, 6, 1), D(2021, 9, 1), True, 'test_hrmanager@hocba.vn', 'hrm', 'fulltime'),
    ('HB.03', 'Trần Thị Bích Ngọc', 'Kế toán_HCNS', 'Chuyên viên Nhân sự', 'official', 'offline', 'staff', 'middle',
     15000000, D(1995, 2, 18), 'female', D(2023, 3, 6), D(2023, 6, 6), False, 'test_hr@hocba.vn', 'hr', 'fulltime'),
    ('HB.04', 'Lê Thị Hồng Vân', 'Kế toán_HCNS', 'Kế toán tổng hợp', 'official', 'offline', 'staff', 'senior',
     16000000, D(1991, 11, 25), 'female', D(2022, 2, 7), D(2022, 5, 7), False, 'van.lth@hocba.vn', 'finance', 'fulltime'),
    ('HB.05', 'Nguyễn Văn An', 'Kế toán_HCNS', 'Hành chính nhân sự', 'probation', 'offline', 'staff', 'junior',
     9500000, D(2001, 7, 9), 'male', D(2026, 7, 6), None, False, 'an.nv@hocba.vn', 'user', 'fulltime'),

    ('HB.06', 'Trần Quốc Việt', 'Kinh doanh', 'Trưởng phòng Kinh doanh', 'official', 'offline', 'manager', 'senior',
     26000000, D(1990, 5, 20), 'male', D(2021, 8, 2), D(2021, 11, 2), True, 'test_truongphong@hocba.vn', 'manager', 'fulltime'),
    ('HB.07', 'Nguyễn Thị Thu Hà', 'Kinh doanh', 'Tư vấn tuyển sinh', 'official', 'offline', 'staff', 'middle',
     12000000, D(1997, 3, 14), 'female', D(2023, 9, 5), D(2023, 12, 5), False, 'test_employee@hocba.vn', 'user', 'fulltime'),
    ('HB.08', 'Phạm Minh Đức', 'Kinh doanh', 'Tư vấn tuyển sinh', 'official', 'offline', 'staff', 'middle',
     11500000, D(1996, 12, 1), 'male', D(2024, 1, 8), D(2024, 4, 8), False, 'duc.pm@hocba.vn', 'user', 'fulltime'),
    ('HB.09', 'Hoàng Thị Lan Anh', 'Kinh doanh', 'Tư vấn tuyển sinh', 'probation', 'offline', 'staff', 'junior',
     9000000, D(2002, 6, 30), 'female', D(2026, 6, 15), None, False, 'lananh.ht@hocba.vn', 'user', 'fulltime'),
    ('HB.10', 'Vũ Đình Trung', 'Kinh doanh', 'Tư vấn tuyển sinh', 'official', 'offline', 'staff', 'junior',
     11000000, D(1999, 10, 11), 'male', D(2025, 2, 10), D(2025, 5, 10), False, 'trung.vd@hocba.vn', 'user', 'fulltime'),
    ('HB.11', 'Nguyễn Đức Thắng', 'BOD', 'Cố vấn chuyên môn', 'advisor', 'online', 'advisor', 'senior',
     15000000, D(1975, 1, 26), 'male', D(2024, 9, 2), None, False, 'thang.nd@hocba.vn', 'user', 'visiting'),

    ('HB.12', 'Lê Minh Khôi', 'Marketing', 'Trưởng phòng Marketing', 'official', 'offline', 'manager', 'senior',
     22000000, D(1992, 8, 8), 'male', D(2022, 3, 1), D(2022, 6, 1), True, 'khoi.lm@hocba.vn', 'manager', 'fulltime'),
    ('HB.13', 'Phạm Thu Trang', 'Marketing', 'Content Marketing', 'official', 'offline', 'staff', 'middle',
     12000000, D(1998, 4, 22), 'female', D(2023, 11, 6), D(2024, 2, 6), False, 'trang.pt@hocba.vn', 'user', 'fulltime'),
    ('HB.14', 'Đặng Hoài Nam', 'Marketing', 'Digital Marketing', 'official', 'offline', 'staff', 'middle',
     13000000, D(1996, 1, 17), 'male', D(2024, 5, 6), D(2024, 8, 6), False, 'namdh@hocba.vn', 'user', 'fulltime'),
    ('HB.15', 'Bùi Thị Ngọc Ánh', 'Marketing', 'Editor', 'parttime', 'online', 'ctv', 'junior',
     7000000, D(2003, 9, 5), 'female', D(2025, 10, 1), None, False, 'anh.btn@hocba.vn', 'user', 'parttime'),
    ('HB.16', 'Đoàn Minh Quân', 'Marketing', 'Thực tập sinh Marketing', 'intern', 'offline', 'staff', 'junior',
     5000000, D(2004, 3, 19), 'male', D(2026, 7, 20), None, False, 'quan.dm@hocba.vn', 'user', 'parttime'),

    ('HB.17', 'Trần Khánh Linh', 'Sản phẩm (R&D_SP)', 'Trưởng phòng Học thuật', 'official', 'offline', 'manager', 'senior',
     24000000, D(1989, 7, 7), 'female', D(2021, 10, 4), D(2022, 1, 4), True, 'linh.tk@hocba.vn', 'manager', 'teacher'),
    ('HB.18', 'Lý Gia Hân', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung', 'official', 'offline', 'staff', 'senior',
     18000000, D(1994, 12, 12), 'female', D(2022, 8, 1), D(2022, 11, 1), False, 'han.lg@hocba.vn', 'user', 'teacher'),
    ('HB.19', 'Nguyễn Thuỳ Dương', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung', 'official', 'online', 'staff', 'middle',
     17000000, D(1997, 5, 3), 'female', D(2023, 7, 3), D(2023, 10, 3), False, 'duong.nt@hocba.vn', 'user', 'teacher'),
    ('HB.20', 'Mã Chí Cường', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung', 'probation', 'offline', 'staff', 'junior',
     13000000, D(2000, 2, 29), 'male', D(2026, 6, 1), None, False, 'cuong.mc@hocba.vn', 'user', 'teacher'),
    ('HB.21', 'Chu Tuyết Nhi', 'Sản phẩm (R&D_SP)', 'Giáo viên tiếng Trung', 'ctv', 'online', 'ctv', 'middle',
     8000000, D(1999, 8, 16), 'female', D(2024, 11, 4), None, False, 'test_ctv@hocba.vn', 'user', 'ctv'),
    ('HB.22', 'Đinh Bảo Long', 'Sản phẩm (R&D_SP)', 'Chuyên viên R&D', 'official', 'offline', 'staff', 'middle',
     14000000, D(1995, 6, 6), 'male', D(2023, 4, 3), D(2023, 7, 3), False, 'long.db@hocba.vn', 'user', 'fulltime'),

    ('HB.23', 'Vũ Thị Mai', 'Vận hành', 'Trưởng phòng Vận hành', 'official', 'offline', 'manager', 'senior',
     20000000, D(1991, 10, 30), 'female', D(2022, 1, 10), D(2022, 4, 10), True, 'mai.vt@hocba.vn', 'manager', 'fulltime'),
    ('HB.24', 'Phạm Văn Long', 'Vận hành', 'Giáo vụ', 'official', 'offline', 'staff', 'middle',
     12000000, D(1996, 9, 21), 'male', D(2023, 2, 6), D(2023, 5, 6), False, 'test_giaovu@hocba.vn', 'giaovu', 'fulltime'),
    ('HB.25', 'Nguyễn Hải Yến', 'Vận hành', 'Trợ giảng', 'official', 'offline', 'staff', 'junior',
     9000000, D(2001, 4, 4), 'female', D(2025, 3, 3), D(2025, 6, 3), False, 'yen.nh@hocba.vn', 'user', 'ta'),
    ('HB.26', 'Trịnh Quang Vinh', 'Vận hành', 'Quản lý học viên', 'official', 'offline', 'staff', 'middle',
     13500000, D(1994, 2, 8), 'male', D(2023, 8, 7), D(2023, 11, 7), False, 'vinh.tq@hocba.vn', 'user', 'fulltime'),
    ('HB.27', 'Lâm Thị Tuyết', 'Vận hành', 'Trợ giảng', 'parttime', 'offline', 'ctv', 'junior',
     6500000, D(2002, 11, 11), 'female', D(2025, 9, 1), None, False, 'tuyet.lt@hocba.vn', 'user', 'ta'),

    # 2 hồ sơ dành cho luồng nghỉ việc (PHASE 8 sẽ đưa vào quy trình)
    ('HB.28', 'Trương Mỹ Duyên', 'Kinh doanh', 'Tư vấn tuyển sinh', 'official', 'offline', 'staff', 'junior',
     10500000, D(1998, 5, 15), 'female', D(2024, 8, 5), D(2024, 11, 5), False, 'duyen.tm@hocba.vn', 'user', 'fulltime'),
    ('HB.29', 'Hà Văn Kiên', 'Vận hành', 'Trợ giảng', 'official', 'offline', 'staff', 'junior',
     9500000, D(2000, 12, 2), 'male', D(2024, 10, 7), D(2025, 1, 7), False, 'kien.hv@hocba.vn', 'user', 'ta'),
]

GROUPS = {
    'hrm': ['base.group_user', 'hr.group_hr_manager',
            'hocba_finance.group_finance_user'],
    'hr': ['base.group_user', 'hr.group_hr_user'],
    'finance': ['base.group_user', 'hocba_finance.group_finance_manager'],
    'giaovu': ['base.group_user', 'hocba_employees.group_hocba_giaovu'],
    'manager': ['base.group_user'],
    'user': ['base.group_user'],
}
BANKS = [('VCB', '0011'), ('TCB', '1903'), ('MB', '0901'), ('BIDV', '2100'),
         ('ACB', '2345'), ('VPB', '1900')]

hr_resp = env.ref('base.user_admin')

created = 0
for i, (code, name, dep_name, job_name, status, wform, ptype, senior, wage,
        bday, sex, joined, official, is_mgr, login, role, leave_type) in enumerate(R, 1):
    d = dept(dep_name)
    j = job(job_name, d)
    slug = login.split('@')[0]
    bank_code, bank_pref = BANKS[i % len(BANKS)]

    # tài khoản: test_* đã có sẵn (giữ theo docs) → chỉ cập nhật, còn lại tạo mới
    u = Users.with_context(active_test=False).search([('login', '=', login)], limit=1)
    gids = [env.ref(g).id for g in GROUPS[role] if env.ref(g, False)]
    uvals = {'name': name, 'login': login, 'email': login,
             'active': True, 'group_ids': [(6, 0, gids)]}
    if u:
        u.write(uvals)
    else:
        u = Users.create(dict(uvals, password=PWD))
    u.write({'password': PWD})

    vals = {
        'name': name, 'x_employee_code': code,
        'department_id': d.id, 'job_id': j.id, 'job_title': job_name,
        'x_employment_status': status, 'x_work_form': wform,
        'x_position_type': ptype, 'x_seniority_level': senior,
        'x_probation_start': joined, 'x_official_date': official,
        'birthday': bday, 'sex': sex, 'marital': 'single',
        'employee_type': 'employee', 'hr_responsible_id': hr_resp.id,
        'user_id': u.id, 'active': True,
        'work_email': login, 'private_email': slug + '@gmail.com',
        'work_phone': '024 7300 %04d' % (1000 + i),
        'private_phone': '09%02d %03d %03d' % (10 + i, 400 + i, 100 + i),
        'place_of_birth': 'Hà Nội',
        'identification_id': '001096%06d' % i,
        'x_id_date_issue': D(2021, 3, 1),
        'x_id_place_issue': 'Cục Cảnh sát QLHC về TTXH',
        'x_permanent_street': 'Số %d ngõ %d, phố Trần Đại Nghĩa' % (i, 20 + i),
        'x_permanent_ward': 'Phường Bách Khoa',
        'x_current_same_as_permanent': True,
        'x_bank_code': bank_code,
        'x_bank_account_no': '%s%08d' % (bank_pref, 12340000 + i * 7),
        'x_hb_leave_emp_type': leave_type,
        'x_employee_type_id': (TEACHER if leave_type in ('teacher', 'visiting')
                               else CTV if leave_type in ('ctv', 'parttime')
                               else OFFICE).id,
        'emergency_contact': 'Người thân — %s' % name.split()[-1],
        'emergency_phone': '098%03d%04d' % (i, 2000 + i),
    }
    # MST + BHXH khai cho cả NV thử việc: BR-010 chỉ BẮT BUỘC khi lên chính
    # thức, nhưng thiếu thì lúc xong hết bước nhận việc _close_probation không
    # chốt được, NV kẹt lại ở Thử việc + chuông "còn thiếu ...".
    if status != 'resigned':
        vals['x_pit_code'] = '8%09d' % (100000000 + i)
        vals['x_social_insurance_no'] = '01%08d' % (20000000 + i)
        vals['x_health_insurance_no'] = 'DN4010%09d' % i
        vals['x_health_care_place'] = 'Bệnh viện Bạch Mai'

    e = emp(code)
    if e:
        e.write(vals)
    else:
        e = Emp.create(vals)
        created += 1
    # lương nằm trên hr.version (bản ghi hợp đồng hiện hành của Odoo 19)
    if e.version_id:
        e.version_id.write({'wage': wage})
    say('%-7s %-22s %-18s %-10s %s' % (code, name, dep_name, status, login))

env.cr.commit()

# ── trưởng phòng + quản lý trực tiếp ─────────────────────────────────────
MANAGERS = {dep: code for (code, _n, dep, _j, _s, _w, _p, _sn, _wg, _b, _sx,
                           _jd, _od, is_mgr, _l, _r, _lt) in R if is_mgr}
for dep_name, code in MANAGERS.items():
    d, m = dept(dep_name), emp(code)
    d.write({'manager_id': m.id})
    members = Emp.search([('department_id', '=', d.id), ('id', '!=', m.id)])
    members.write({'parent_id': m.id})
    say('TP %-18s → %s (%d NV)' % (dep_name, m.name, len(members)))
# CEO quản lý các trưởng phòng
ceo = emp('HB.01')
for code in MANAGERS.values():
    if code != 'HB.01':
        emp(code).write({'parent_id': ceo.id})

env.cr.commit()
print('\nPHASE 1 XONG — %d NV (%d tạo mới), %d phòng ban, %d tài khoản' % (
    Emp.search_count([]), created, Dept.search_count([]),
    Users.search_count([('share', '=', False)])))
