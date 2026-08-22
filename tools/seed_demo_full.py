#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed dữ liệu DEMO đầy đủ cho Học Bá HRM (chạy TRONG container Odoo).

    docker compose -f docker-compose.yml -f docker-compose.local.yml \
        run --rm -v "$PWD/tools:/tools" odoo python3 /tools/seed_demo_full.py

Tuỳ chọn (env):
    SEED_DB       tên database (mặc định hocba_demo)
    SEED_WIPE     1 = xoá dữ liệu nghiệp vụ cũ trước khi seed (mặc định 1)

Sinh ra:
  · 8 tài khoản quản trị (Admin, HR Manager, 5 Trưởng phòng, Giáo vụ)
  · Quy trình tuyển dụng CHẠY THẬT: phiếu yêu cầu → JD → CV → lọc → hẹn PV →
    phỏng vấn → kết quả → offer → nhận việc → onboarding → bàn giao
  · 30 nhân sự tuyển mới (20 văn phòng · 5 giáo viên · 5 CTV) + 12 CV trượt/bùng
  · Chấm công từng ngày T2–T6 tháng 7/2026, nghỉ phép, hợp đồng, bảng lương T7,
    đánh giá Quý 3/2026, tài sản, người phụ thuộc, chứng chỉ, yêu cầu HR

Tên người lấy từ file Excel nghiệp vụ của trung tâm cho "giống người thật";
email/điện thoại/CCCD/số tài khoản đều là dữ liệu GIẢ sinh theo quy tắc.
"""
import logging
import os
import random
import sys
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime, timedelta

import odoo
from odoo.api import Environment, SUPERUSER_ID
from odoo.modules.registry import Registry

_log = logging.getLogger('seed_demo')
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

DB = os.environ.get('SEED_DB', 'hocba_demo')
WIPE = os.environ.get('SEED_WIPE', '1') == '1'
PASSWORD = 'Hocba@2026'

TODAY = date(2026, 8, 16)
JULY = (date(2026, 7, 1), date(2026, 7, 31))

random.seed(20260816)

# ══════════════════════════════════════════════════════════════════════════
# Danh sách người — tên thật lấy từ sheet nghiệp vụ, thông tin còn lại là giả
# ══════════════════════════════════════════════════════════════════════════

# (tên, login, phòng ban, chức danh, nhóm quyền)
MANAGERS = [
    ('Lưu Thị Hường',        'test_admin',        'BOD',           'Giám đốc điều hành',        'admin'),
    ('Hoàng Thị Ngọc Anh',   'test_hrmanager',    'Kế toán_HCNS',  'Trưởng phòng Nhân sự',      'hr_manager'),
    ('Nguyễn Trung Kiên',    'test_tp_marketing', 'Marketing',     'Trưởng phòng Marketing',    'dept_manager'),
    ('Trần Thị Ánh',         'test_tp_kinhdoanh', 'Kinh doanh',    'Trưởng phòng Kinh doanh',   'dept_manager'),
    ('Phan Quỳnh Giang',     'test_tp_sanpham',   'Sản phẩm',      'Trưởng phòng VH & SP',      'dept_manager'),
    ('Cao Việt Khánh',       'test_tp_vanhanh',   'Vận hành',      'Trưởng phòng Vận hành',     'dept_manager'),
    ('Nguyễn Thị Len',       'test_tp_ketoan',    'Kế toán_HCNS',  'Kế toán trưởng',            'dept_manager'),
    ('Lê Thị Thùy',          'test_giaovu',       'Sản phẩm',      'Chuyên viên Giáo vụ',       'giaovu'),
]

# (tên, phòng ban, chức danh, mã vị trí JD, ngày nhận việc, lương)
OFFICE_HIRES = [
    ('Nguyễn Thị Thương',      'Kinh doanh',   'Chuyên viên TVTS',        'tvts',    date(2026, 6, 1),  9_500_000),
    ('Đỗ Thị Hải Ngọc',        'Kinh doanh',   'Nhân viên TVTS',          'tvts',    date(2026, 6, 1),  8_000_000),
    ('Trương Thị Trang',       'Kinh doanh',   'Nhân viên TVTS',          'tvts',    date(2026, 6, 1),  8_000_000),
    ('Phùng Minh Anh',         'Kinh doanh',   'Nhân viên TVTS',          'tvts',    date(2026, 6, 16), 8_000_000),
    ('Đặng Thị Thu Hà',        'Kinh doanh',   'Nhân viên TVTS',          'tvts',    date(2026, 6, 16), 8_000_000),
    ('Trần Khánh Linh',        'Kinh doanh',   'Nhân viên TVTS thử việc', 'tvts',    date(2026, 7, 1),  7_500_000),
    ('Lô Đức Thịnh',           'Marketing',    'Digital Ads Facebook',    'content', date(2026, 6, 1),  10_000_000),
    ('Vũ Hoàng Minh',          'Marketing',    'Digital Ads Google',      'content', date(2026, 6, 1),  10_000_000),
    ('Nguyễn Thị Mai',         'Marketing',    'Social Facebook + IG',    'content', date(2026, 6, 16), 9_000_000),
    ('Phạm Thanh Hoa',         'Marketing',    'Nhân viên Thiết kế',      'content', date(2026, 6, 16), 9_000_000),
    ('Ngô Thị Minh Tuyết',     'Vận hành',     'Chuyên viên QLHV',        'qlhv',    date(2026, 6, 1),  9_500_000),
    ('Lê Thị Phương',          'Vận hành',     'Nhân viên QLHV',          'qlhv',    date(2026, 6, 1),  8_500_000),
    ('Nguyễn Bình An',         'Vận hành',     'Nhân viên QLHV',          'qlhv',    date(2026, 6, 16), 8_500_000),
    ('Võ Lê Duy Hoàng',        'Vận hành',     'Nhân viên QLHV',          'qlhv',    date(2026, 7, 1),  8_500_000),
    ('Lê Thu Thảo',            'Sản phẩm',     'Chuyên viên R&D',         'rnd',     date(2026, 6, 1),  11_000_000),
    ('Bùi Thị Trang',          'Sản phẩm',     'Nhân viên Học thuật',     'trogiang', date(2026, 6, 1), 8_500_000),
    ('Đinh Hoàng Mai Phương',  'Sản phẩm',     'Nhân viên Giáo vụ',       'giaovu',  date(2026, 6, 16), 8_500_000),
    ('Lê Thị Dung',            'Kế toán_HCNS', 'Chuyên viên HCNS',        'hcns',    date(2026, 6, 1),  9_000_000),
    ('Nguyễn Thị Phương Nga',  'Kế toán_HCNS', 'Nhân viên Kế toán',       'hcns',    date(2026, 6, 16), 9_000_000),
    ('Đặng Vũ Thu Hà',         'Kế toán_HCNS', 'Nhân viên tuyển dụng',    'hcns',    date(2026, 7, 1),  8_000_000),
]

# (tên, chức danh, ngày nhận việc, lương, đơn giá giờ, trình độ)
TEACHER_HIRES = [
    ('Hán Vũ Tú Ngọc',        'Giáo viên tiếng Trung', date(2026, 6, 1),  12_000_000, 220_000, 'HSK6'),
    ('Nguyễn Thị Thanh Thuý', 'Giáo viên tiếng Trung', date(2026, 6, 1),  12_000_000, 220_000, 'HSK6'),
    ('Đỗ Thu Giang',          'Giáo viên tiếng Trung', date(2026, 6, 16), 11_000_000, 200_000, 'HSK5'),
    ('Mai Hoài Tâm',          'Giáo viên tiếng Trung', date(2026, 6, 16), 11_000_000, 200_000, 'HSK5'),
    ('Lê Thị Ngọc Trang',     'Giáo viên tiếng Trung', date(2026, 7, 1),  10_500_000, 190_000, 'HSK5'),
]

# (tên, phòng ban, chức danh, mã vị trí, ngày nhận việc, lương khoán)
CTV_HIRES = [
    ('Nguyễn Minh Trung',      'Kế toán_HCNS', 'CTV Tuyển dụng',  'hcns',    date(2026, 7, 1), 4_000_000),
    ('Bùi Thị Tú',             'Kế toán_HCNS', 'CTV HCNS',        'hcns',    date(2026, 7, 1), 4_000_000),
    ('Nguyễn Phương Thảo',     'Marketing',    'CTV Content FB',  'content', date(2026, 7, 1), 4_500_000),
    ('Nguyễn Vũ Bình Dương',   'Marketing',    'CTV Ads Google',  'content', date(2026, 7, 1), 4_500_000),
    ('Đỗ Thị Minh Tuyết',      'Kinh doanh',   'CTV Gọi lọc',     'tvts',    date(2026, 7, 1), 3_500_000),
]

# CV không thành công — (tên, mã vị trí, kết cục)
#   fail_cv    : trượt vòng lọc CV
#   fail_call  : từ chối phỏng vấn
#   absent     : không đến phỏng vấn
#   fail_pv    : trượt phỏng vấn
#   potential  : tiềm năng, để dành đợt sau
#   no_show    : nhận offer rồi bùng
#   in_progress: đang xử lý (CV mới / chờ PV)
REJECTED = [
    ('Lâm Thị Thuỳ',           'teacher', 'fail_cv'),
    ('Hà Thị Hồng',            'teacher', 'fail_cv'),
    ('Phạm Thị Thanh Mai',     'teacher', 'fail_call'),
    ('Nguyễn Thị Thuỷ',        'teacher', 'absent'),
    ('Lê Thuỳ Chang',          'teacher', 'fail_pv'),
    ('Lê Thị Tâm',             'teacher', 'potential'),
    ('Nguyễn Thị Minh Thuỳ',   'teacher', 'no_show'),
    ('Ngọc Thuý Hường',        'tvts',    'fail_cv'),
    ('Nguyễn Thị Kim Chi',     'tvts',    'fail_pv'),
    ('Trịnh Thu Hằng',         'tvts',    'in_progress'),
    ('Vũ Đức Long',            'content', 'in_progress'),
    ('Hoàng Thị Ngọc Diệp',    'qlhv',    'in_progress'),
]

# Mã vị trí → tên JD trong DB (data/hb_job_positions.xml)
JOB_BY_KEY = {
    'tvts':     'Tư vấn tuyển sinh',
    'teacher':  'Giáo viên dạy tiếng Trung',
    'rnd':      'Chuyên viên R&D',
    'trogiang': 'Trợ giảng',
    'giaovu':   'Giáo vụ',
    'qlhv':     'Quản lý học viên',
    'content':  'Content Marketing',
    'hcns':     'Hành chính nhân sự',
}
JOB_DEPT = {
    'tvts': 'Kinh doanh', 'teacher': 'Sản phẩm', 'rnd': 'Sản phẩm',
    'trogiang': 'Sản phẩm', 'giaovu': 'Sản phẩm', 'qlhv': 'Vận hành',
    'content': 'Marketing', 'hcns': 'Kế toán_HCNS',
}

PROVINCES = ['Hà Nội', 'Hải Phòng', 'Nam Định', 'Thanh Hóa', 'Nghệ An',
             'Bắc Ninh', 'Hưng Yên', 'Thái Bình', 'Phú Thọ', 'Hải Dương']
WARDS = ['Phường Dịch Vọng', 'Phường Mai Dịch', 'Phường Trung Hòa',
         'Phường Khương Trung', 'Phường Yên Hòa', 'Phường Cổ Nhuế']
STREETS = ['Số 12 ngõ 84 Trần Thái Tông', 'Số 5 Nguyễn Khánh Toàn',
           'Số 68 Cầu Giấy', 'Số 21 Duy Tân', 'Số 143 Nguyễn Ngọc Vũ',
           'Số 7 ngách 15 Phạm Văn Đồng']

_counter = {'cccd': 0, 'phone': 0, 'bank': 0, 'tax': 0, 'si': 0}


def slug(name):
    """'Nguyễn Thị Mai' → 'nguyenthimai' (bỏ dấu, bỏ khoảng trắng)."""
    s = unicodedata.normalize('NFD', name)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'D')
    return ''.join(c for c in s.lower() if c.isalnum())


def next_cccd():
    _counter['cccd'] += 1
    return '0010%08d' % (12345600 + _counter['cccd'])


def next_phone():
    _counter['phone'] += 1
    return '09%08d' % (12000000 + _counter['phone'] * 137)


def next_bank_acc():
    _counter['bank'] += 1
    return '99%010d' % (2026000000 + _counter['bank'] * 7919)


def next_tax():
    _counter['tax'] += 1
    return '80%08d' % (12345600 + _counter['tax'] * 31)


def next_si():
    _counter['si'] += 1
    return '01%08d' % (20260000 + _counter['si'] * 17)


def workdays(d1, d2):
    """Các ngày T2–T6 trong khoảng [d1, d2]."""
    out, d = [], d1
    while d <= d2:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def utc(d, hour, minute=0):
    """Giờ VN (UTC+7) → datetime UTC lưu trong DB."""
    return datetime(d.year, d.month, d.day, hour - 7, minute)


class Seeder:
    def __init__(self, env, registry=None):
        self.env = env
        self.registry = registry or env.registry
        self.dept = {}
        self.jobs = {}
        self.emp = {}       # tên → hr.employee
        self.users = {}     # login → res.users
        self.requests = {}  # mã vị trí → hb.recruitment.request
        self.stats = {}


    # ── chạy 1 thao tác trong savepoint: lỗi 1 bản ghi không đổ cả phase ──
    @contextmanager
    def guard(self, label):
        try:
            with self.env.cr.savepoint():
                yield
        except Exception as ex:                          # noqa: BLE001
            _log.warning('    ! %s: %s', label, str(ex).strip()[:120])

    # ── tiện ích ────────────────────────────────────────────────────────
    def ref(self, xmlid):
        return self.env.ref(xmlid, raise_if_not_found=False)

    def step(self, title):
        _log.info('\n━━━ %s', title)

    def done(self, key, n, label):
        self.stats[key] = n
        _log.info('    ✓ %s: %s', label, n)

    # ══════════════════════════════════════════════════════════════════
    # 0. Dọn dữ liệu nghiệp vụ cũ
    # ══════════════════════════════════════════════════════════════════
    def wipe(self):
        """Xoá sạch dữ liệu nghiệp vụ bằng SQL.

        Cố ý KHÔNG đi qua ORM: nhiều model chặn unlink theo nghiệp vụ (phiếu
        đánh giá đã chốt, lịch sử thăng tiến, cấp phép đã duyệt) — đúng cho
        production nhưng làm reset DB demo bất khả thi. Thứ tự bảng đi từ con
        lên cha để không vướng khoá ngoại RESTRICT.
        """
        self.step('0. Dọn dữ liệu nghiệp vụ cũ (SQL)')
        env = self.env
        tables = [
            'hb_payslip_line', 'hb_payslip_worked_days', 'hb_payslip_input',
            'hb_payslip', 'hb_payslip_run', 'hb_bank_file', 'hb_contract',
            'hb_performance_review_line', 'hb_performance_review',
            'hocba_attendance', 'hocba_teaching_attendance',
            'hocba_shift_attendance', 'hocba_work_shift',
            'hocba_attendance_request',
            'hr_leave', 'hr_leave_allocation',
            'hocba_hr_request_message', 'hocba_hr_request_sender',
            'hocba_hr_request',
            'hb_onboarding_step', 'hr_employee_asset', 'hr_employee_dependent',
            'hr_employee_skill', 'hr_promotion_history',
            'hr_promotion_evaluation', 'hb_honor_entry', 'hocba_offboarding',
            'hb_notification',
            'hb_interview_slot_applicant_rel', 'hb_interview_slot',
            'hr_applicant', 'hb_recruitment_request',
        ]
        # Nghỉ lễ do module cài (có xmlid) thì GIỮ; dòng "X: Time Off" sinh ra
        # khi duyệt đơn nghỉ thì XOÁ. Sót lại là bẫy chí mạng cho lần seed sau:
        # chúng nằm trên lịch chung (resource_id rỗng) nên cả công ty bị coi là
        # không làm việc ngày đó ⇒ đơn nghỉ mới ra 0 ngày và không duyệt được.
        with self.guard('xoá nghỉ lễ phát sinh'):
            env.cr.execute("""
                DELETE FROM resource_calendar_leaves l
                 WHERE NOT EXISTS (SELECT 1 FROM ir_model_data d
                                    WHERE d.model = 'resource.calendar.leaves'
                                      AND d.res_id = l.id)
            """)
            if env.cr.rowcount:
                _log.info('    - resource_calendar_leaves: xoá %s',
                          env.cr.rowcount)
        for table in tables:
            with self.guard('xoá bảng %s' % table):
                env.cr.execute("SELECT to_regclass(%s)", (table,))
                if not env.cr.fetchone()[0]:
                    continue
                env.cr.execute('DELETE FROM "%s"' % table)
                if env.cr.rowcount:
                    _log.info('    - %s: xoá %s', table, env.cr.rowcount)
        env.invalidate_all()
        # Nhân viên + tài khoản (giữ admin gốc uid 1/2)
        emps = env['hr.employee'].sudo().with_context(active_test=False).search([])
        if emps:
            n = len(emps)
            emps.write({'department_id': False})
            env['hr.department'].sudo().search([]).write({'manager_id': False})
            emps.unlink()
            _log.info('    - hr.employee: xoá %s', n)
        users = env['res.users'].sudo().with_context(active_test=False).search(
            [('id', '>', 2), ('login', 'like', '%@hocba.vn')])
        if users:
            n = len(users)
            users.unlink()
            _log.info('    - res.users: xoá %s', n)
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 1. Danh mục nền: phòng ban, vị trí JD
    # ══════════════════════════════════════════════════════════════════
    def load_base(self):
        self.step('1. Danh mục nền (phòng ban · vị trí JD)')
        Dept = self.env['hr.department'].sudo()
        for key, name in [('Marketing', 'Marketing'), ('Sản phẩm', 'Sản phẩm (R&D_SP)'),
                          ('Kinh doanh', 'Kinh doanh'), ('Vận hành', 'Vận hành'),
                          ('Kế toán_HCNS', 'Kế toán_HCNS'), ('BOD', 'BOD')]:
            d = Dept.search([('name', '=', name)], limit=1)
            if not d:
                d = Dept.create({'name': name})
            self.dept[key] = d
        Job = self.env['hr.job'].sudo()
        for key, name in JOB_BY_KEY.items():
            j = Job.search([('name', '=', name)], limit=1)
            if not j:
                j = Job.create({'name': name})
            j.write({'department_id': self.dept[JOB_DEPT[key]].id,
                     'recruitment_status': 'recruiting', 'x_published': True})
            self.jobs[key] = j
        # Lịch làm việc chuẩn theo giờ VN — để nguyên tz mặc định (Brussels) thì
        # đơn nghỉ phép báo "nhân viên không làm việc trong khoảng này".
        cal = self.env.company.resource_calendar_id
        if cal:
            cal.sudo().write({'tz': 'Asia/Ho_Chi_Minh',
                              'name': 'Giờ hành chính 8h–17h (VN)'})
            # Khoảng giờ làm việc của lịch được ormcache theo registry: không
            # xoá cache thì phần sau của script vẫn tính theo tz cũ (Brussels)
            # ⇒ duyệt đơn nghỉ báo "nhân viên không làm việc trong khoảng này".
            self.env.registry.clear_cache()
        self.env.company.sudo().write({'name': 'Học Bá Education'})
        self.done('depts', len(self.dept), 'phòng ban')
        self.done('jobs', len(self.jobs), 'vị trí JD')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 2. Tài khoản quản trị + hồ sơ nhân sự của họ
    # ══════════════════════════════════════════════════════════════════
    def _groups_for(self, kind):
        g = []

        def add(xmlid):
            rec = self.ref(xmlid)
            if rec:
                g.append(rec.id)

        add('base.group_user')
        if kind == 'admin':
            add('base.group_system')
            add('hr.group_hr_manager')
            add('hr_recruitment.group_hr_recruitment_manager')
            add('hocba_employees.group_hocba_giaovu')
            add('hocba_finance.group_finance_manager')
            add('hr_holidays.group_hr_holidays_manager')
        elif kind == 'hr_manager':
            add('hr.group_hr_manager')
            add('hr_recruitment.group_hr_recruitment_manager')
            add('hr_holidays.group_hr_holidays_manager')
            add('hocba_finance.group_finance_user')
        elif kind == 'dept_manager':
            add('hr.group_hr_user')
            add('hr_recruitment.group_hr_recruitment_user')
            add('hr_holidays.group_hr_holidays_user')
        elif kind == 'giaovu':
            add('hocba_employees.group_hocba_giaovu')
            add('hr.group_hr_user')
        return g

    def _make_employee(self, name, dept, job_title, *, status, emp_type,
                       position_type, probation_start, wage, work_form='offline',
                       job_key=None, seniority='middle', official_date=None,
                       applicant=None):
        """Tạo hr.employee + điền đủ hồ sơ pháp lý/ngân hàng/địa chỉ."""
        env = self.env
        etype = env['hocba.employee.type'].sudo().search(
            [('code', '=', emp_type)], limit=1)
        login = '%s@hocba.vn' % slug(name)
        vals = {
            'name': name,
            'department_id': self.dept[dept].id,
            'job_title': job_title,
            'work_email': login,
            'work_phone': next_phone(),
            'private_email': login,
            'private_phone': next_phone(),
            'x_employment_status': 'probation',
            'x_employee_type_id': etype.id if etype else False,
            'x_position_type': position_type,
            'x_work_form': work_form,
            'x_seniority_level': seniority,
            'x_probation_start': probation_start,
            'birthday': date(random.randint(1993, 2003), random.randint(1, 12),
                             random.randint(1, 28)),
            'marital': random.choice(['single', 'single', 'married']),
            'x_permanent_ward': random.choice(WARDS),
            'x_permanent_street': random.choice(STREETS),
            'x_current_same_as_permanent': True,
        }
        if job_key and job_key in self.jobs:
            vals['job_id'] = self.jobs[job_key].id
        if applicant:
            vals['applicant_ids'] = [(6, 0, [applicant.id])]
        emp = env['hr.employee'].sudo().create(vals)
        # CCCD / lương nằm trên hr.version (Odoo 19) — hr.employee chỉ là related.
        # date_version PHẢI lùi về ngày vào làm: version mặc định bắt đầu từ
        # hôm nay, nên mọi tính toán cho tháng 7 (nghỉ phép, work entry) coi như
        # nhân viên chưa có lịch làm việc ⇒ đơn nghỉ ra 0 ngày.
        ver_vals = {'identification_id': next_cccd(), 'wage': wage}
        for fname, fval in (('date_version', probation_start),
                            ('contract_date_start', probation_start)):
            if fname in emp.version_id._fields:
                ver_vals[fname] = fval
        emp.version_id.sudo().write(ver_vals)
        emp.sudo().write({
            'x_id_date_issue': date(2021, random.randint(1, 12), random.randint(1, 28)),
            'x_id_place_issue': 'Cục Cảnh sát QLHC về TTXH',
            'x_pit_code': next_tax(),
            'x_social_insurance_no': next_si(),
            'x_bank_account_no': next_bank_acc(),
            'x_bank_code': random.choice(['VCB', 'TCB', 'MB']),
            'x_health_insurance_no': 'DN4%s' % random.randint(1000000000, 9999999999),
            'x_health_care_place': 'Bệnh viện E Hà Nội',
        })
        if status != 'probation':
            upd = {'x_employment_status': status}
            if status == 'official':
                upd['x_official_date'] = official_date or (
                    probation_start + timedelta(days=60))
            emp.sudo().write(upd)
        self.emp[name] = emp
        return emp

    def _make_user(self, emp, login, kind):
        user = self.env['res.users'].sudo().create({
            'name': emp.name,
            'login': login,
            'password': PASSWORD,
            'email': login,
            'tz': 'Asia/Ho_Chi_Minh',
            'group_ids': [(6, 0, self._groups_for(kind))],
        })
        emp.sudo().write({'user_id': user.id, 'work_email': login})
        self.users[login] = user
        return user

    def seed_managers(self):
        self.step('2. Tài khoản quản trị & trưởng phòng')
        for name, login_short, dept, title, kind in MANAGERS:
            login = '%s@hocba.vn' % login_short
            emp = self._make_employee(
                name, dept, title,
                status='official', emp_type='office',
                position_type='manager' if kind != 'giaovu' else 'staff',
                probation_start=date(2024, 3, 1), wage=25_000_000
                if kind in ('admin', 'hr_manager') else 20_000_000,
                seniority='senior', official_date=date(2024, 5, 1))
            self._make_user(emp, login, kind)
            _log.info('    · %-24s %-26s %s', name, login, title)
        # Trưởng phòng thật sự của từng phòng ban
        for name, _l, dept, _t, kind in MANAGERS:
            if kind == 'dept_manager':
                self.dept[dept].sudo().write({'manager_id': self.emp[name].id})
        self.dept['BOD'].sudo().write({'manager_id': self.emp['Lưu Thị Hường'].id})
        self.done('managers', len(MANAGERS), 'tài khoản quản trị')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 3. Phiếu yêu cầu tuyển dụng (chạy đúng luồng duyệt)
    # ══════════════════════════════════════════════════════════════════
    def seed_requests(self):
        self.step('3. Phiếu yêu cầu tuyển dụng (nháp → gửi duyệt → đang tuyển)')
        Req = self.env['hb.recruitment.request'].sudo()
        need = {}
        for _n, _d, _t, key, _s, _w in OFFICE_HIRES:
            need[key] = need.get(key, 0) + 1
        need['teacher'] = len(TEACHER_HIRES)
        for _n, _d, _t, key, _s, _w in CTV_HIRES:
            need[key] = need.get(key, 0) + 1

        salary = {'tvts': '8 – 12 triệu', 'teacher': '10 – 15 triệu',
                  'rnd': '11 – 15 triệu', 'trogiang': '7 – 9 triệu',
                  'giaovu': '8 – 10 triệu', 'qlhv': '8 – 11 triệu',
                  'content': '9 – 13 triệu', 'hcns': '8 – 12 triệu'}
        for i, (key, qty) in enumerate(sorted(need.items())):
            dept = self.dept[JOB_DEPT[key]]
            mgr = dept.manager_id.user_id or self.users['test_hrmanager@hocba.vn']
            req = Req.create({
                'date_request': date(2026, 5, 4) + timedelta(days=i),
                'department_id': dept.id,
                'job_id': self.jobs[key].id,
                'job_title': self.jobs[key].name,
                'qty_expected': qty,
                'reason': 'expansion' if key in ('teacher', 'tvts') else 'new',
                'level': 'junior',
                'education': 'bachelor',
                'experience_years': 1.0,
                'skill_description': 'Giao tiếp tốt, thành thạo tin học văn phòng.',
                'language_requirement': 'HSK4 trở lên' if key == 'teacher' else 'Không bắt buộc',
                'expected_start_date': date(2026, 6, 1),
                'salary_range': salary.get(key, '8 – 12 triệu'),
                'salary_from': 8_000_000, 'salary_to': 15_000_000,
                'work_type': 'onsite',
                'manager_id': mgr.id,
                'hr_manager_id': self.users['test_hrmanager@hocba.vn'].id,
                'requester_id': mgr.id,
            })
            req.action_submit()
            req.with_user(self.users['test_hrmanager@hocba.vn']).action_approve()
            self.requests[key] = req
            _log.info('    · %s · %s · %s người', req.name, req.job_title, qty)
        self.done('requests', len(self.requests), 'phiếu đang tuyển')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 4. Lịch rảnh phỏng vấn
    # ══════════════════════════════════════════════════════════════════
    def seed_slots(self):
        self.step('4. Lịch rảnh phỏng vấn của trưởng phòng')
        Slot = self.env['hb.interview.slot'].sudo()
        n = 0
        interviewers = [self.emp[m[0]].user_id for m in MANAGERS
                        if m[4] == 'dept_manager']
        for user in interviewers:
            for day_offset in range(0, 10):
                d = date(2026, 5, 18) + timedelta(days=day_offset)
                if d.weekday() >= 5:
                    continue
                for hour in (9, 14):
                    with self.guard('slot %s %s' % (user.name, d)):
                        Slot.create({
                            'user_id': user.id,
                            'start_datetime': utc(d, hour),
                            'stop_datetime': utc(d, hour + 1),
                        })
                        n += 1
        self.done('slots', n, 'slot phỏng vấn')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 5. CV ứng viên — chạy hết phễu tuyển dụng
    # ══════════════════════════════════════════════════════════════════
    def _stage(self, ref):
        return self.ref('hocba_recruitments.' + ref)

    def _new_applicant(self, name, job_key, received, ctv='anhhtn'):
        job = self.jobs[job_key]
        return self.env['hr.applicant'].sudo().create({
            'partner_name': name,
            'email_from': '%s@ungvien.demo' % slug(name),
            'partner_phone': next_phone(),
            'job_id': job.id,
            'department_id': job.department_id.id,
            'date_received': received,
            'ctv_tuyen_dung': ctv,
            'cv_link': 'CV_%s.pdf' % slug(name),
            'stage_id': self._stage('hb_stage_sourcing').id,
            'hb_request_id': self.requests[job_key].id
            if job_key in self.requests else False,
        })

    def _run_funnel(self, app, interviewer_name, pv_date, outcome, start_date=None,
                    offer_text=None):
        """Đẩy CV qua các bước; write() của model tự chuyển stage theo dữ liệu."""
        stage = self._stage
        if outcome == 'in_progress':
            app.write({'stage_id': stage('hb_stage_screening').id,
                       'cv_note': 'CV mới nhận, đang chờ lọc.'})
            return
        if outcome == 'fail_cv':
            app.write({'stage_id': stage('hb_stage_screening').id,
                       'cv_filter_result': 'fail',
                       'cv_note': 'Chưa đạt yêu cầu về kinh nghiệm.'})
            return
        # Pass lọc CV → tự sang bước Hẹn lịch
        app.write({'stage_id': stage('hb_stage_screening').id})
        app.write({'cv_filter_result': 'pass', 'cv_note': 'Hồ sơ phù hợp.'})
        if outcome == 'fail_call':
            app.write({'call_status': 'refuse',
                       'cv_note': 'Ứng viên đã nhận việc nơi khác.'})
            return
        if outcome == 'potential':
            app.write({'call_status': 'potential',
                       'cv_note': 'Tiềm năng — để dành đợt tuyển sau.'})
            return
        app.write({'call_status': 'agree'})
        # Đặt lịch PV → tự sang bước Mời phỏng vấn
        app.write({'interview_date': pv_date,
                   'interview_time': random.choice(['9h', '10h', '14h', '15h30']),
                   'interviewer_name': interviewer_name})
        if outcome == 'absent':
            app.write({'attendance_status': 'absent',
                       'cv_note': 'Ứng viên không đến buổi phỏng vấn.'})
            return
        app.write({'stage_id': stage('hb_stage_interview').id,
                   'attendance_status': 'present'})
        if outcome == 'fail_pv':
            app.write({'interview_result': 'fail',
                       'offer_note': 'Chuyên môn chưa đáp ứng vị trí.'})
            return
        # Pass phỏng vấn → bước Kết quả PV, sau đó gửi offer
        app.write({'interview_result': 'pass'})
        app.write({'stage_id': stage('hb_stage_offer').id,
                   'offer_content': offer_text or 'Thử việc 2 tháng, lương thoả thuận.',
                   'start_date': start_date,
                   'candidate_confirmed': 'Đã xác nhận qua mail'})
        if outcome == 'no_show':
            app.write({'onboard_result': 'no_show',
                       'offer_note': 'Đã nhận offer nhưng không đến ngày hẹn.'})
            return
        app.write({'onboard_result': 'arrived'})

    def seed_applicants(self):
        self.step('5. CV ứng viên — chạy hết phễu tuyển dụng')
        pv_base = date(2026, 5, 18)
        i = 0
        self.hired_apps = []
        for name, dept, title, key, start, wage in OFFICE_HIRES:
            i += 1
            app = self._new_applicant(name, key, pv_base - timedelta(days=7 + i % 5))
            self._run_funnel(app, self.dept[dept].manager_id.name or 'HR',
                             pv_base + timedelta(days=i % 8), 'arrived', start,
                             'Lương thử việc 85%%, chính thức %s đ/tháng.' % f'{wage:,}')
            self.hired_apps.append((app, ('office', name, dept, title, key, start, wage)))
        for name, title, start, wage, rate, level in TEACHER_HIRES:
            i += 1
            app = self._new_applicant(name, 'teacher', pv_base - timedelta(days=6 + i % 4))
            self._run_funnel(app, self.emp['Phan Quỳnh Giang'].name,
                             pv_base + timedelta(days=i % 8), 'arrived', start,
                             'Đơn giá %s đ/giờ, tối thiểu 60 giờ/tháng.' % f'{rate:,}')
            self.hired_apps.append((app, ('teacher', name, 'Sản phẩm', title,
                                          'teacher', start, wage, rate, level)))
        for name, dept, title, key, start, wage in CTV_HIRES:
            i += 1
            app = self._new_applicant(name, key, pv_base - timedelta(days=3 + i % 4))
            self._run_funnel(app, self.dept[dept].manager_id.name or 'HR',
                             pv_base + timedelta(days=10 + i % 5), 'arrived', start,
                             'Cộng tác viên khoán việc theo tháng.')
            self.hired_apps.append((app, ('ctv', name, dept, title, key, start, wage)))
        for name, key, outcome in REJECTED:
            i += 1
            app = self._new_applicant(name, key, pv_base - timedelta(days=i % 9))
            self._run_funnel(app, self.dept[JOB_DEPT[key]].manager_id.name or 'HR',
                             pv_base + timedelta(days=i % 10), outcome,
                             date(2026, 7, 1))
        total = self.env['hr.applicant'].sudo().search_count([])
        self.done('applicants', total, 'CV trong hệ thống')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 6. Nhận việc: tạo hồ sơ nhân viên từ ứng viên
    # ══════════════════════════════════════════════════════════════════
    def seed_hires(self):
        self.step('6. Nhận việc — tạo hồ sơ nhân sự từ ứng viên')
        for app, info in self.hired_apps:
            kind = info[0]
            if kind == 'office':
                _k, name, dept, title, key, start, wage = info
                emp = self._make_employee(
                    name, dept, title, status='probation', emp_type='office',
                    position_type='staff', probation_start=start, wage=wage,
                    job_key=key, applicant=app,
                    seniority='junior' if 'Nhân viên' in title else 'middle')
            elif kind == 'teacher':
                _k, name, dept, title, key, start, wage, rate, level = info
                emp = self._make_employee(
                    name, dept, title, status='probation', emp_type='teacher',
                    position_type='staff', probation_start=start, wage=wage,
                    job_key=key, applicant=app, seniority='middle')
                emp.sudo().write({
                    'x_trial_lesson_date': start - timedelta(days=7),
                    'x_trial_lesson_class': 'HSK3 - Lớp tối 2-4-6',
                    'x_trial_score_method': round(random.uniform(7.5, 9.5), 1),
                    'x_trial_score_content': round(random.uniform(7.5, 9.5), 1),
                    'x_trial_lesson_result': 'pass',
                    'x_trial_lesson_note': 'Phát âm chuẩn, quản lý lớp tốt.',
                })
            else:
                _k, name, dept, title, key, start, wage = info
                emp = self._make_employee(
                    name, dept, title, status='ctv', emp_type='contractor',
                    position_type='ctv', probation_start=start, wage=wage,
                    work_form='online', job_key=key, applicant=app,
                    seniority='junior')
            app.sudo().write({'employee_id': emp.id})
            app._hb_advance_stage(['hb_stage_result', 'hb_stage_offer'],
                                  'hb_stage_onboarding',
                                  'Do đã tạo hồ sơ nhân viên (Onboard).')
        self.done('hires', len(self.hired_apps), 'hồ sơ nhân sự tạo từ tuyển dụng')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 7. Onboarding + lên chính thức
    # ══════════════════════════════════════════════════════════════════
    def seed_onboarding(self):
        self.step('7. Quy trình nhận việc & lên chính thức')
        env = self.env
        Step = env['hb.onboarding.step'].sudo()
        done_steps = 0
        official = 0
        for app, info in self.hired_apps:
            emp = app.employee_id
            if not emp:
                continue
            start = emp.x_probation_start
            total = len(emp.x_onboarding_step_ids)
            # NV vào từ 16/06 trở về trước đã đủ 2 tháng thử việc tính tới 16/08
            # → chạy trọn quy trình; người mới vào 01/07 mới xong vài bước đầu.
            full = bool(start and start <= date(2026, 6, 16))
            limit = total if full else max(1, total // 3)
            for _i in range(limit):
                st = Step.search([('employee_id', '=', emp.id),
                                  ('state', '=', 'open')],
                                 order='sequence, id', limit=1)
                if not st:
                    break
                # savepoint: một bước hỏng không kéo đổ cả phase
                try:
                    with env.cr.savepoint():
                        if st.step_type == 'evaluation':
                            st.action_evaluate(
                                'pass', 'Đạt yêu cầu, tiếp tục công việc.',
                                st.due_date or start)
                        else:
                            st.action_complete('Đã hoàn thành.')
                    done_steps += 1
                except Exception as ex:                  # noqa: BLE001
                    _log.warning('    ! bước "%s" (%s): %s', st.name, emp.name,
                                 str(ex)[:110])
                    break
            emp = emp.sudo()
            if full and emp.x_employment_status == 'probation':
                try:
                    with env.cr.savepoint():
                        emp.with_context(hocba_gate_automation=True).write({
                            'x_employment_status': 'official',
                            'x_official_date': start + timedelta(days=60),
                        })
                except Exception as ex:                  # noqa: BLE001
                    _log.warning('    ! lên chính thức %s: %s', emp.name,
                                 str(ex)[:110])
            if emp.x_employment_status == 'official':
                official += 1
        self.done('onb_steps', done_steps, 'bước nhận việc đã xử lý')
        self.done('official', official, 'nhân viên lên chính thức')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 8. Tài khoản đăng nhập cho nhân viên
    # ══════════════════════════════════════════════════════════════════
    def seed_employee_users(self):
        self.step('8. Tài khoản đăng nhập cho nhân viên mới')
        n = 0
        for app, info in self.hired_apps:
            emp = app.employee_id
            if not emp or emp.user_id:
                continue
            login = '%s@hocba.vn' % slug(emp.name)
            if self.env['res.users'].sudo().with_context(active_test=False).search_count(
                    [('login', '=', login)]):
                login = '%s.%s@hocba.vn' % (slug(emp.name), emp.id)
            self._make_user(emp, login, 'employee')
            n += 1
        self.done('emp_users', n, 'tài khoản nhân viên')
        self.env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 9. Tài sản · người phụ thuộc · chứng chỉ
    # ══════════════════════════════════════════════════════════════════
    def seed_profile_extras(self):
        self.step('9. Tài sản · người phụ thuộc · chứng chỉ')
        env = self.env
        Asset = env['hr.employee.asset'].sudo()
        AType = env['hocba.asset.type'].sudo()
        types = {t.code: t for t in AType.search([])}
        n_asset = n_dep = n_cert = 0
        all_emps = env['hr.employee'].sudo().search([])
        for i, emp in enumerate(all_emps):
            if emp.x_employment_status == 'ctv':
                continue
            for code in ('pc', 'monitor', 'chair'):
                t = types.get(code)
                if not t:
                    continue
                with self.guard('tài sản %s %s' % (code, emp.name)):
                    Asset.create({
                        'employee_id': emp.id, 'asset_type_id': t.id,
                        'asset_code': '%s-%03d' % (code.upper(), emp.id),
                        'grant_date': emp.x_probation_start or date(2026, 6, 1),
                        'condition_in': random.choice(['new', 'good']),
                    })
                    n_asset += 1
            if i % 3 == 0:
                with self.guard('NPT của %s' % emp.name):
                    env['hr.employee.dependent'].sudo().create({
                        'employee_id': emp.id,
                        'name': 'Con %s' % emp.name.split()[-1],
                        'relationship': 'child',
                        'birthday': date(2020, random.randint(1, 12), random.randint(1, 28)),
                        'national_id': next_cccd(),
                        'date_start': date(2026, 1, 1),
                    })
                    n_dep += 1
        # Chứng chỉ HSK cho giáo viên
        Skill = env['hr.employee.skill'].sudo()
        stype = env['hr.skill.type'].sudo().search([('name', 'ilike', 'ngôn ngữ')], limit=1) \
            or env['hr.skill.type'].sudo().search([], limit=1)
        for name, title, start, wage, rate, level in TEACHER_HIRES:
            emp = self.emp.get(name)
            if not emp or not stype:
                continue
            skill = env['hr.skill'].sudo().search(
                [('skill_type_id', '=', stype.id), ('name', 'ilike', level)], limit=1)
            if not skill:
                skill = env['hr.skill'].sudo().search(
                    [('skill_type_id', '=', stype.id)], limit=1)
            lvl = env['hr.skill.level'].sudo().search(
                [('skill_type_id', '=', stype.id)], limit=1, order='level_progress desc')
            if not (skill and lvl):
                continue
            with self.guard('chứng chỉ %s' % name):
                Skill.create({
                    'employee_id': emp.id, 'skill_type_id': stype.id,
                    'skill_id': skill.id, 'skill_level_id': lvl.id,
                    'x_cert_date': date(2024, 6, 15),
                    'x_cert_expiry': date(2026, 9, 30),
                    'x_cert_verified': True,
                })
                n_cert += 1
        self.done('assets', n_asset, 'tài sản cấp phát')
        self.done('dependents', n_dep, 'người phụ thuộc')
        self.done('certs', n_cert, 'chứng chỉ giáo viên')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 10. Nghỉ phép tháng 7
    # ══════════════════════════════════════════════════════════════════
    def seed_timeoff(self):
        self.step('10. Nghỉ phép — cấp phép năm 2026 & đơn nghỉ tháng 7')
        env = self.env
        env.invalidate_all()
        env.registry.clear_cache()
        ltype = env['hr.leave.type'].sudo().search(
            [('requires_allocation', '=', True)], limit=1)
        n_alloc = n_leave = 0
        self.leave_days = {}
        emps = env['hr.employee'].sudo().search([('x_employment_status', '!=', 'ctv')])
        for emp in emps:
            if not ltype:
                break
            with self.guard('cấp phép %s' % emp.name):
                alloc = env['hr.leave.allocation'].sudo().create({
                    'name': 'Phép năm 2026',
                    'holiday_status_id': ltype.id,
                    'employee_id': emp.id,
                    'number_of_days': 12,
                    'date_from': date(2026, 1, 1),
                })
                if alloc.state != 'validate':
                    alloc.action_approve()
                n_alloc += 1
        self.done('allocs', n_alloc, 'phiếu cấp phép năm')
        env.cr.commit()

        # ── Đơn nghỉ phép: BẮT BUỘC chạy trên cursor mới ─────────────────
        # hr.leave.number_of_days là compute-store, tính qua lịch làm việc của
        # nhân viên. Trong CÙNG transaction vừa tạo nhân viên + đổi tz lịch, nó
        # luôn ra 0 (cache resource/version của transaction còn giữ trạng thái
        # cũ) ⇒ duyệt đơn báo "nhân viên không làm việc trong khoảng này".
        # Cursor mới = transaction mới = cache sạch, đọc lại từ DB đã commit.
        picks = [(e.id, e.name) for e in emps[:6]]
        with self.registry.cursor() as cr2:
            env2 = Environment(cr2, SUPERUSER_ID, dict(env.context))
            for i, (emp_id, emp_name) in enumerate(picks):
                d = date(2026, 7, 6 + i * 3)
                while d.weekday() >= 5:
                    d += timedelta(days=1)
                try:
                    with cr2.savepoint():
                        leave = env2['hr.leave'].sudo().create({
                            'name': 'Nghỉ phép cá nhân',
                            'holiday_status_id': ltype.id,
                            'employee_id': emp_id,
                            'request_date_from': d,
                            'request_date_to': d,
                        })
                        if leave.state in ('draft', 'confirm'):
                            leave.sudo().action_approve()
                        self.leave_days.setdefault(emp_id, set()).add(d)
                        n_leave += 1
                        _log.info('      · %s nghỉ %s (%s ngày)', emp_name, d,
                                  leave.number_of_days)
                except Exception as ex:                  # noqa: BLE001
                    _log.warning('    ! đơn nghỉ %s: %s', emp_name,
                                 str(ex).strip()[:120])
            cr2.commit()
        self.done('leaves', n_leave, 'đơn nghỉ phép tháng 7')

    # ══════════════════════════════════════════════════════════════════
    # 11. Chấm công tháng 7/2026
    # ══════════════════════════════════════════════════════════════════
    def seed_attendance(self):
        self.step('11. Chấm công tháng 7/2026 (T2–T6, trừ ngày nghỉ phép)')
        env = self.env
        Att = env['hocba.attendance'].sudo()
        days = workdays(*JULY)
        rows = []
        emps = env['hr.employee'].sudo().search([])
        for emp in emps:
            start = emp.x_probation_start or date(2026, 1, 1)
            off = self.leave_days.get(emp.id, set())
            rnd = random.Random(emp.id * 977 + 7)
            for d in days:
                if d < start or d in off:
                    continue
                r = rnd.random()
                if r > 0.90:            # đi trễ
                    cin, cout = utc(d, 8, rnd.choice([12, 18, 25])), utc(d, 17)
                    note = 'Đi trễ'
                elif r > 0.86:          # về sớm
                    cin, cout = utc(d, 8), utc(d, 16, 30)
                    note = 'Về sớm'
                elif r > 0.83:          # nửa ngày
                    cin, cout = utc(d, 8), utc(d, 12)
                    note = 'Nghỉ buổi chiều'
                else:
                    cin, cout = utc(d, 8), utc(d, 17, rnd.choice([0, 5, 12]))
                    note = 'Đúng giờ'
                rows.append({
                    'employee_id': emp.id, 'check_in': cin, 'check_out': cout,
                    'notes': note,
                })
        for i in range(0, len(rows), 500):
            Att.create(rows[i:i + 500])
        self.done('attendance', len(rows), 'dòng chấm công tháng 7')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 11b. Buổi dạy của giáo viên · ca CTV/OT · đơn sửa chấm công
    # ══════════════════════════════════════════════════════════════════
    def seed_shift_and_teaching(self):
        self.step('11b. Buổi dạy giáo viên · ca CTV & OT · đơn sửa chấm công')
        env = self.env
        # ── Buổi dạy: chỉ số đánh giá của nhóm giảng viên đọc từ bảng này,
        # không có buổi dạy thì phiếu đánh giá giáo viên ra 0 điểm tự động.
        TA = env['hocba.teaching.attendance'].sudo()
        classes = ['HSK1 - Tối 2-4-6', 'HSK2 - Tối 3-5-7', 'HSK3 - Sáng 2-4-6',
                   'HSK4 - Tối 3-5', 'HSK5 - Chiều 7-CN']
        n_teach = 0
        for idx, (name, _t, start, _w, _r, _l) in enumerate(TEACHER_HIRES):
            emp = self.emp.get(name)
            if not emp:
                continue
            rnd = random.Random(emp.id)
            klass = classes[idx % len(classes)]
            for d in workdays(*JULY):
                if d.weekday() not in (0, 2, 4) or d < start:   # T2-T4-T6
                    continue
                late = rnd.random() > 0.9
                with self.guard('buổi dạy %s %s' % (name, d)):
                    TA.create({
                        'cms_session_id': 'DEMO-%s-%s' % (emp.id, d.isoformat()),
                        'cms_class_id': 'DEMO-CLS-%s' % (idx + 1),
                        'class_name': klass,
                        'employee_id': emp.id,
                        'session_date': d,
                        'session_start': '18:00', 'session_end': '20:00',
                        'role_type': 'MAIN_TEACHER',
                        # đúng giờ = tới sớm 17:45; trễ = 18:05 (quá giờ vào lớp)
                        'check_in': utc(d, 18, 5) if late else utc(d, 17, 45),
                        'check_out': utc(d, 20, 5),
                        'out_of_window': late,
                    })
                    n_teach += 1
        self.done('teaching', n_teach, 'buổi dạy tháng 7')

        # ── Ca CTV + ca OT (Excel 3.6 "Bảng công OT")
        Shift = env['hocba.work_shift'].sudo()
        SAtt = env['hocba.shift.attendance'].sudo()
        n_shift = 0
        ctvs = [self.emp[n] for n, *_ in CTV_HIRES if n in self.emp]
        for i, emp in enumerate(ctvs):
            for w in range(4):
                d = date(2026, 7, 7 + w * 7 + (i % 3))
                if d.month != 7:
                    continue
                with self.guard('ca CTV %s %s' % (emp.name, d)):
                    sh = Shift.create({
                        'employee_id': emp.id,
                        'start': utc(d, 18), 'end': utc(d, 21),
                        'shift_type': 'ctv', 'ot_level': '100',
                        'state': 'approved',
                        'reason': 'Ca cộng tác viên buổi tối',
                        'reviewer_id': self.users['test_hrmanager@hocba.vn'].id,
                    })
                    SAtt.create({'shift_id': sh.id,
                                 'check_in': utc(d, 18), 'check_out': utc(d, 21)})
                    n_shift += 1
        # OT của nhân viên văn phòng: 2 ca đã duyệt + 1 ca chờ duyệt mỗi người
        ot_emps = [self.emp[n] for n, *_ in OFFICE_HIRES[:6] if n in self.emp]
        for i, emp in enumerate(ot_emps):
            for w, (state, level) in enumerate(
                    [('approved', '150'), ('approved', '100'), ('pending', '300')]):
                d = date(2026, 7, 4 + w * 7 + (i % 2) * 2)
                if d.month != 7:
                    continue
                with self.guard('ca OT %s %s' % (emp.name, d)):
                    sh = Shift.create({
                        'employee_id': emp.id,
                        'start': utc(d, 18), 'end': utc(d, 20, 30),
                        'shift_type': 'ot', 'ot_level': level,
                        'state': state,
                        'reason': 'Chạy chiến dịch tuyển sinh tháng 7',
                        'reviewer_id': self.users['test_hrmanager@hocba.vn'].id
                        if state == 'approved' else False,
                    })
                    if state == 'approved':
                        SAtt.create({'shift_id': sh.id,
                                     'check_in': utc(d, 18),
                                     'check_out': utc(d, 20, 30)})
                    n_shift += 1
        self.done('shifts', n_shift, 'ca CTV/OT')

        # ── Đơn xin sửa chấm công (2 chờ duyệt · 1 duyệt · 1 từ chối)
        Req = env['hocba.attendance.request'].sudo()
        Att = env['hocba.attendance'].sudo()
        n_req = 0
        targets = [(n, 'pending') for n, *_ in OFFICE_HIRES[6:8]]
        targets += [(OFFICE_HIRES[8][0], 'approved'),
                    (OFFICE_HIRES[9][0], 'rejected')]
        for j, (name, state) in enumerate(targets):
            emp = self.emp.get(name)
            if not emp:
                continue
            d = date(2026, 7, 8 + j * 2)
            att = Att.search([('employee_id', '=', emp.id), ('date', '=', d)],
                             limit=1)
            with self.guard('đơn sửa công %s' % name):
                Req.create({
                    'employee_id': emp.id,
                    'request_date': d,
                    'attendance_id': att.id if att else False,
                    'proposed_check_in': utc(d, 8),
                    'proposed_check_out': utc(d, 17, 30),
                    'reason': 'Quên bấm giờ ra do đi gặp khách hàng.',
                    'state': state,
                    'reviewer_id': self.users['test_hrmanager@hocba.vn'].id
                    if state != 'pending' else False,
                    'review_note': {'approved': 'Đã đối chiếu camera, duyệt.',
                                    'rejected': 'Không có bằng chứng, từ chối.',
                                    'pending': False}[state],
                })
                n_req += 1
        self.done('att_requests', n_req, 'đơn sửa chấm công')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 12. Hợp đồng lao động
    # ══════════════════════════════════════════════════════════════════
    def seed_contracts(self):
        self.step('12. Hợp đồng lao động')
        env = self.env
        Contract = env['hb.contract'].sudo()
        struct_off = env['hb.salary.structure'].sudo().search(
            [('code', '=', 'STRUCT_OFFLINE')], limit=1)
        struct_on = env['hb.salary.structure'].sudo().search(
            [('code', '=', 'STRUCT_ONLINE')], limit=1)
        teacher_rate = {n: (r, w) for n, _t, _s, w, r, _l in TEACHER_HIRES}
        n = 0
        for emp in env['hr.employee'].sudo().search([]):
            wage = emp.version_id.wage if 'wage' in emp.version_id._fields else 0
            is_ctv = emp.x_employment_status == 'ctv'
            is_teacher = emp.x_employee_type_id.code == 'teacher'
            vals = {
                'name': 'HĐLĐ %s - %s' % (emp.x_employee_code or emp.id, emp.name),
                'employee_id': emp.id,
                'date_start': emp.x_probation_start or date(2026, 1, 1),
                'wage': wage,
                'state': 'open',
                'x_insurance_base': 0 if is_ctv else wage,
                'x_insurance_policy': 'none' if is_ctv else 'standard',
                'x_structure_id': (struct_on if is_ctv else struct_off).id,
                'x_pc_parking': 0 if is_ctv else 200_000,
                'x_pc_fuel': 0 if is_ctv else 300_000,
                'x_sp_meal': 0 if is_ctv else 730_000,
                'x_sp_phone': 100_000 if emp.x_position_type == 'manager' else 0,
                'x_pc_position': 3_000_000 if emp.x_position_type == 'manager' else 0,
            }
            if is_teacher:
                rate, _w = teacher_rate.get(emp.name, (200_000, 0))
                vals.update({
                    'x_teaching_hourly_rate': rate,
                    'x_rate_hsk_class': rate + 40_000,
                    'x_standard_threshold': 60.0,
                    'x_has_fixed_base': True,
                    'x_fixed_base': 3_000_000,
                })
            Contract.create(vals)
            n += 1
        self.done('contracts', n, 'hợp đồng hiệu lực')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 13. Bảng lương tháng 7/2026
    # ══════════════════════════════════════════════════════════════════
    def seed_payroll(self):
        self.step('13. Bảng lương tháng 7/2026')
        env = self.env
        run = env['hb.payslip.run'].sudo().create({
            'name': 'Bảng lương tháng 07/2026',
            'date_start': JULY[0], 'date_end': JULY[1],
        })
        Slip = env['hb.payslip'].sudo()
        n = 0
        for emp in env['hr.employee'].sudo().search([]):
            contract = env['hb.contract'].sudo().search(
                [('employee_id', '=', emp.id), ('state', '=', 'open')], limit=1)
            if not contract:
                continue
            slip = Slip.create({
                'employee_id': emp.id,
                'contract_id': contract.id,
                'structure_id': contract.x_structure_id.id,
                'payslip_run_id': run.id,
                'date_from': JULY[0], 'date_to': JULY[1],
                'x_kpi_score': round(random.uniform(70, 100), 1),
            })
            with self.guard('tính lương %s' % emp.name):
                slip.action_compute_sheet()
                n += 1
        with self.guard('chốt batch lương'):
            run.action_verify()
        self.done('payslips', n, 'phiếu lương đã tính')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 14. Đánh giá định kỳ Quý 3/2026 (chứa tháng 7)
    # ══════════════════════════════════════════════════════════════════
    def seed_reviews(self):
        self.step('14. Đánh giá nhân sự — Quý 3/2026 (kỳ chứa tháng 7)')
        env = self.env
        Review = env['hb.performance.review'].sudo()
        hr_user = self.users['test_hrmanager@hocba.vn']
        n = n_conf = 0
        for emp in env['hr.employee'].sudo().search([]):
            mgr = emp.department_id.manager_id.user_id or hr_user
            rev = None
            with self.guard('phiếu đánh giá %s' % emp.name):
                rev = Review.create({
                    'employee_id': emp.id,
                    'period_type': 'quarter',
                    'period_year': 2026,
                    'period_index': 3,
                    'evaluator_id': mgr.id,
                    'self_note': 'Hoàn thành công việc được giao trong tháng 7.',
                    'manager_note': 'Chủ động, phối hợp tốt với đồng nghiệp.',
                })
                for line in rev.line_ids:
                    if not line.is_auto:
                        line.sudo().write({
                            'score': round(random.uniform(0.7, 1.0)
                                           * (line.max_score or 5)),
                            'note': 'Đạt yêu cầu.',
                        })
                n += 1
            # 2/3 số phiếu đã chốt & công bố, còn lại để nháp cho demo thao tác
            if rev and n % 3:
                with self.guard('chốt đánh giá %s' % emp.name):
                    rev.sudo().action_confirm()
                    rev.sudo().action_publish()
                    n_conf += 1
        self.done('reviews', n, 'phiếu đánh giá Quý 3/2026')
        self.done('reviews_pub', n_conf, 'phiếu đã chốt & công bố')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    # 15. Yêu cầu gửi HR
    # ══════════════════════════════════════════════════════════════════
    def seed_service(self):
        self.step('15. Yêu cầu gửi phòng Nhân sự')
        env = self.env
        Req = env['hocba.hr.request'].sudo()
        types = env['hocba.hr.request.type'].sudo().search([])
        if not types:
            return
        samples = [
            ('Xin giấy xác nhận công tác', 'Em cần giấy xác nhận công tác để làm thủ tục vay ngân hàng.', 'new'),
            ('Xác nhận thu nhập / bảng lương', 'Nhờ HR xác nhận thu nhập 3 tháng gần nhất.', 'in_progress'),
            ('Hỏi đáp lương / BHXH / thuế', 'Cho em hỏi tháng 7 em bị trừ BHXH bao nhiêu ạ?', 'answered'),
            ('Cấp lại thẻ nhân viên', 'Em làm mất thẻ nhân viên, xin cấp lại.', 'closed'),
            ('Đề xuất / xin ý kiến công việc', 'Đề xuất mua thêm 2 tai nghe cho bộ phận sale.', 'new'),
            ('Đánh giá & góp ý', 'Góp ý về quy trình chấm công bằng khuôn mặt.', 'answered'),
        ]
        # Người gửi KHÔNG được là HR/Admin: đơn do chính người xử lý gửi thì
        # tin nhắn của họ mang vai "người gửi", action_answer sẽ báo chưa ai trả lời.
        hr_logins = {'test_hrmanager@hocba.vn', 'test_admin@hocba.vn'}
        emps = [e for e in env['hr.employee'].sudo().search([])
                if e.user_id and e.user_id.login not in hr_logins][:12]
        n = 0
        for i, (tname, body, target) in enumerate(samples):
            t = types.filtered(lambda x: x.name == tname)[:1] or types[:1]
            emp = emps[i % len(emps)] if emps else None
            if not emp:
                break
            with self.guard('yêu cầu "%s"' % tname):
                # create_request() là cổng chính thức phía người gửi (ACL của
                # hocba.hr.request KHÔNG cho user thường create trực tiếp).
                res = Req.with_user(emp.user_id).create_request({
                    'type_id': t.id,
                    'subject': tname,
                    'body': body,
                })
                rid = res.get('id') if isinstance(res, dict) else res.id
                req = Req.browse(rid)
                hr = self.users['test_hrmanager@hocba.vn']
                if target in ('in_progress', 'answered', 'closed'):
                    req.with_user(hr).action_claim()
                if target in ('answered', 'closed'):
                    req.with_user(hr).post_message(
                        'Chào bạn, HR đã tiếp nhận và xử lý yêu cầu này.')
                    # Tin nhắn tạo bằng with_user(SUPERUSER_ID) nên o2m
                    # message_ids trong cache của `req` chưa thấy → action_answer
                    # sẽ tưởng chưa ai trả lời.
                    env.invalidate_all()
                    req.with_user(hr).action_answer()
                if target == 'closed':
                    req.with_user(hr).action_close('Đã xử lý xong.')
                n += 1
        self.done('requests_hr', n, 'yêu cầu gửi HR')
        env.cr.commit()

    # ══════════════════════════════════════════════════════════════════
    def summary(self):
        env = self.env
        self.step('TỔNG KẾT')
        counts = [
            ('Phòng ban', 'hr.department', []),
            ('Nhân sự', 'hr.employee', []),
            ('  · chính thức', 'hr.employee', [('x_employment_status', '=', 'official')]),
            ('  · thử việc', 'hr.employee', [('x_employment_status', '=', 'probation')]),
            ('  · CTV', 'hr.employee', [('x_employment_status', '=', 'ctv')]),
            ('  · giáo viên', 'hr.employee', [('x_employee_type_id.code', '=', 'teacher')]),
            ('Tài khoản đăng nhập', 'res.users', [('login', 'like', '%@hocba.vn')]),
            ('Phiếu yêu cầu tuyển dụng', 'hb.recruitment.request', []),
            ('CV ứng viên', 'hr.applicant', []),
            ('Slot phỏng vấn', 'hb.interview.slot', []),
            ('Bước nhận việc', 'hb.onboarding.step', []),
            ('Chấm công tháng 7', 'hocba.attendance', []),
            ('Buổi dạy giáo viên', 'hocba.teaching.attendance', []),
            ('Ca CTV / OT', 'hocba.work_shift', []),
            ('Đơn sửa chấm công', 'hocba.attendance.request', []),
            ('Hợp đồng', 'hb.contract', []),
            ('Phiếu lương', 'hb.payslip', []),
            ('Phiếu đánh giá', 'hb.performance.review', []),
            ('Đơn nghỉ phép', 'hr.leave', []),
            ('Yêu cầu HR', 'hocba.hr.request', []),
            ('Thông báo', 'hb.notification', []),
        ]
        for label, model, dom in counts:
            if model not in env:
                continue
            _log.info('    %-28s %s', label, env[model].sudo().search_count(dom))


def main():
    odoo.tools.config.parse_config([
        '-c', '/etc/odoo/odoo.conf', '-d', DB,
        '--addons-path=/mnt/extra-addons',
        '--db_host=%s' % os.environ.get('HOST', 'db'),
        '--db_port=%s' % os.environ.get('PORT', '5432'),
        '--db_user=%s' % os.environ.get('USER', 'odoo'),
        '--db_password=%s' % os.environ.get('PASSWORD', 'odoo_password'),
    ])
    reg = Registry(DB)
    with reg.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {
            'tz': 'Asia/Ho_Chi_Minh',
            'lang': 'en_US',
            'tracking_disable': True,
            'mail_create_nolog': True,
            'mail_notrack': True,
            'no_reset_password': True,
        })
        s = Seeder(env, reg)
        _log.info('╔══════════════════════════════════════════════════════╗')
        _log.info('║  SEED DEMO — Học Bá HRM · DB %-24s║', DB)
        _log.info('╚══════════════════════════════════════════════════════╝')
        if WIPE:
            s.wipe()
        s.load_base()
        s.seed_managers()
        s.seed_requests()
        s.seed_slots()
        s.seed_applicants()
        s.seed_hires()
        s.seed_onboarding()
        s.seed_employee_users()
        s.seed_profile_extras()
        s.seed_timeoff()
        s.seed_attendance()
        s.seed_shift_and_teaching()
        s.seed_contracts()
        s.seed_payroll()
        s.seed_reviews()
        s.seed_service()
        s.summary()
        cr.commit()
    _log.info('\n✅ Seed xong. Mật khẩu chung: %s', PASSWORD)


if __name__ == '__main__':
    main()
