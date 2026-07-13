"""Test _dashboard_stats + các helper tab dashboard (tuyển dụng/chấm công/
nghỉ phép/lương). Spec: docs/superpowers/specs/SPEC_DASHBOARD_HR_OVERVIEW.md.

Dùng trưởng phòng (scope = phòng mình) để đếm được chính xác trên DB test
có sẵn demo data; helper toàn cục (tuyển dụng) so bằng DELTA với baseline."""
from datetime import date, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _dashboard_stats, _dashboard_recruitment, _dashboard_attendance,
    _dashboard_timeoff, _dashboard_payroll, _dash_scope_emp_ids,
    _last_months, _years_between)


@tagged('post_install', '-at_install')
class TestDashboardStats(TransactionCase):

    def setUp(self):
        super().setUp()
        today = fields.Date.today()
        self.dep = self.env['hr.department'].create({'name': 'Dep Dashboard'})
        self.mgr_user = self.env['res.users'].create({
            'name': 'Mgr Dash', 'login': 'mgr_dash',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        # Trưởng phòng: 30 tuổi, vào làm 3 năm, chính thức 12/2025
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'Mgr Dash', 'x_employee_code': 'HB.DASH1',
            'department_id': self.dep.id, 'user_id': self.mgr_user.id,
            'birthday': today.replace(year=today.year - 30),
            'x_probation_start': today.replace(year=today.year - 3),
            'x_official_date': date(2025, 12, 1),
        })
        self.dep.manager_id = self.mgr_emp
        # NV đang làm: 24 tuổi, vào làm 1 năm, chính thức 1/2026
        self.emp_a = self.env['hr.employee'].create({
            'name': 'Emp Dash A', 'x_employee_code': 'HB.DASH2',
            'department_id': self.dep.id,
            'birthday': today.replace(year=today.year - 24),
            'x_probation_start': today.replace(year=today.year - 1),
            'x_official_date': date(2026, 1, 15),
        })
        # NV đã nghỉ (archive) — vẫn phải đếm vào Offboard + tổng
        self.emp_b = self.env['hr.employee'].create({
            'name': 'Emp Dash B', 'x_employee_code': 'HB.DASH3',
            'department_id': self.dep.id,
        })
        self.emp_b.sudo().with_context(hocba_gate_automation=True).write(
            {'x_employment_status': 'resigned', 'active': False})
        self.stats = _dashboard_stats(self.env(user=self.mgr_user))

    def test_kpi_counts(self):
        kpi = self.stats['kpi']
        self.assertEqual(kpi['total'], 3)
        self.assertEqual(kpi['onboard'], 2)
        self.assertEqual(kpi['offboard'], 1)

    def test_kpi_averages(self):
        kpi = self.stats['kpi']
        self.assertEqual(kpi['avgAge'], 27)        # (30 + 24) / 2
        self.assertEqual(kpi['avgSeniority'], 2)   # (3 + 1) / 2

    def test_age_and_seniority_distribution(self):
        self.assertEqual(
            self.stats['byAge'],
            [{'age': 24, 'count': 1}, {'age': 30, 'count': 1}])
        self.assertEqual(
            self.stats['bySeniority'],
            [{'years': 1, 'count': 1}, {'years': 3, 'count': 1}])

    def test_official_by_month_sorted(self):
        self.assertEqual(
            self.stats['officialByMonth'],
            [{'label': '12/2025', 'count': 1}, {'label': '1/2026', 'count': 1}])

    def test_plain_user_gets_zeros(self):
        plain = self.env['res.users'].create({
            'name': 'Plain Dash', 'login': 'plain_dash',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        stats = _dashboard_stats(self.env(user=plain))
        self.assertEqual(stats['kpi']['total'], 0)
        self.assertEqual(stats['byAge'], [])

    def test_hr_scope_covers_department(self):
        """HR/Admin thấy tất cả — số liệu bao được phòng test (DB có demo)."""
        stats = _dashboard_stats(self.env)
        self.assertGreaterEqual(stats['kpi']['total'], 3)
        self.assertGreaterEqual(stats['kpi']['offboard'], 1)

    def test_years_between_edge_cases(self):
        self.assertIsNone(_years_between(None, date(2026, 1, 1)))
        self.assertIsNone(_years_between(date(2027, 1, 1), date(2026, 1, 1)))
        self.assertEqual(
            _years_between(date(2000, 7, 11), date(2026, 7, 10)), 25)
        self.assertEqual(
            _years_between(date(2000, 7, 10), date(2026, 7, 10)), 26)

    def test_by_department(self):
        self.assertIn({'dep': 'Dep Dashboard', 'count': 2},
                      self.stats['byDepartment'])

    def test_turnover_series(self):
        tv = self.stats['turnoverByMonth']
        self.assertEqual(len(tv), 12)
        for row in tv:
            self.assertGreaterEqual(row['rate'], 0)
            self.assertIn('count', row)

    def test_tabs_flags_dept_manager(self):
        tabs = self.stats['tabs']
        self.assertFalse(tabs['recruitment'])   # không phải HR
        self.assertTrue(tabs['attendance'])     # trưởng phòng có scope
        self.assertTrue(tabs['timeoff'])
        self.assertFalse(tabs['payroll'])       # chỉ HR Manager

    def test_last_months(self):
        self.assertEqual(_last_months(3, date(2026, 1, 15)),
                         [(2025, 11), (2025, 12), (2026, 1)])

    def test_scope_helper(self):
        self.assertIsNone(_dash_scope_emp_ids(self.env))  # admin = tất cả
        plain = self.env['res.users'].create({
            'name': 'Plain Scope', 'login': 'plain_scope_dash',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.assertEqual(_dash_scope_emp_ids(self.env(user=plain)), [])
        mgr_ids = _dash_scope_emp_ids(self.env(user=self.mgr_user))
        self.assertIn(self.emp_a.id, mgr_ids)


@tagged('post_install', '-at_install')
class TestDashboardRecruitment(TransactionCase):
    """Phễu/nguồn/vị trí mở so bằng DELTA với baseline (DB có thể có sẵn
    dữ liệu tuyển dụng demo)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.baseline = _dashboard_recruitment(cls.env)
        cls.dep = cls.env['hr.department'].create({'name': 'Dep DashRec'})
        Stage = cls.env['hr.recruitment.stage']
        cls.stage_new = Stage.search(
            [('hired_stage', '=', False)], limit=1) or Stage.create(
            {'name': 'Mới (dash)', 'sequence': 1})
        cls.stage_hired = Stage.search(
            [('hired_stage', '=', True)], limit=1) or Stage.create(
            {'name': 'Đã tuyển (dash)', 'hired_stage': True, 'sequence': 99})
        # no_of_recruitment=5 để hook auto-close không đóng phiếu recruiting
        cls.job = cls.env['hr.job'].create({
            'name': 'Job DashRec', 'department_id': cls.dep.id,
            'no_of_recruitment': 5})
        src = cls.env['utm.source'].create({'name': 'TopCV (dash)'})
        d0 = date(2026, 6, 1)
        A = cls.env['hr.applicant']
        a1 = A.create({
            'partner_name': 'UV Dash 1', 'job_id': cls.job.id,
            'stage_id': cls.stage_new.id, 'date_received': d0,
            'cv_filter_result': 'pass', 'attendance_status': 'present',
            'interview_result': 'pass',
            'start_date': d0 + timedelta(days=20), 'source_id': src.id})
        a1.write({'stage_id': cls.stage_hired.id})
        A.create({
            'partner_name': 'UV Dash 2', 'job_id': cls.job.id,
            'stage_id': cls.stage_new.id, 'date_received': d0,
            'cv_filter_result': 'pass', 'attendance_status': 'present',
            'interview_result': 'fail'})
        A.create({
            'partner_name': 'UV Dash 3', 'job_id': cls.job.id,
            'stage_id': cls.stage_new.id, 'date_received': d0,
            'cv_filter_result': 'fail'})
        A.create({
            'partner_name': 'UV Dash 4', 'job_id': cls.job.id,
            'stage_id': cls.stage_new.id, 'date_received': d0})
        cls.req = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dep.id, 'job_id': cls.job.id,
            'job_title': 'Job DashRec', 'qty_expected': 2})
        cls.req.write({'state': 'recruiting'})
        cls.stats = _dashboard_recruitment(cls.env)

    def _funnel(self, stats):
        return {r['stage']: r['count'] for r in stats['funnel']}

    def test_funnel_deltas(self):
        before, after = self._funnel(self.baseline), self._funnel(self.stats)
        self.assertEqual(after['Nộp CV'] - before['Nộp CV'], 4)
        self.assertEqual(after['Pass lọc CV'] - before['Pass lọc CV'], 2)
        self.assertEqual(after['Tham gia PV'] - before['Tham gia PV'], 2)
        self.assertEqual(after['Pass PV'] - before['Pass PV'], 1)
        self.assertEqual(after['Nhận việc'] - before['Nhận việc'], 1)

    def test_time_to_hire(self):
        tth = self.stats['timeToHire']
        self.assertEqual(
            tth['hired'] - self.baseline['timeToHire']['hired'], 1)
        if self.baseline['timeToHire']['hired'] == 0:
            self.assertEqual(tth['avgDays'], 20)

    def test_source_counted(self):
        """Tổng đếm nguồn = tổng CV (nguồn nhỏ có thể bị gộp vào 'Khác'
        khi DB sẵn nhiều nguồn lớn hơn) và danh sách sort giảm dần."""
        total = sum(r['count'] for r in self.stats['bySource'])
        base = sum(r['count'] for r in self.baseline['bySource'])
        self.assertEqual(total - base, 4)
        named = [r['count'] for r in self.stats['bySource']
                 if r['label'] != 'Khác']
        self.assertEqual(named, sorted(named, reverse=True))

    def test_open_by_dept(self):
        row = next(r for r in self.stats['openByDept']
                   if r['dep'] == 'Dep DashRec')
        self.assertEqual(row['requests'], 1)
        self.assertEqual(row['qty'], 2)


@tagged('post_install', '-at_install')
class TestDashboardTabHelpers(TransactionCase):
    """Cấu trúc dữ liệu các tab Chấm công / Nghỉ phép / Lương — chạy trên DB
    bất kỳ (có/không dữ liệu) không được vỡ, đủ 12 tháng, số không âm."""

    def test_attendance_structure(self):
        st = _dashboard_attendance(self.env)
        self.assertEqual(len(st['rateByMonth']), 12)
        self.assertEqual(len(st['otByMonth']), 12)
        for row in st['rateByMonth']:
            self.assertGreaterEqual(row['latePct'], 0)
            self.assertLessEqual(row['latePct'], 100)
        self.assertLessEqual(len(st['topLate']), 7)

    def test_timeoff_structure(self):
        st = _dashboard_timeoff(self.env)
        self.assertEqual(len(st['byMonth']), 12)
        self.assertGreaterEqual(st['remaining'], 0)
        self.assertGreaterEqual(st['takenDays'], 0)
        self.assertIsInstance(st['byType'], list)

    def test_payroll_structure(self):
        st = _dashboard_payroll(self.env)
        self.assertEqual(len(st['fundByMonth']), 12)
        self.assertIsInstance(st['byDept'], list)
        for row in st['avgByLevel']:
            self.assertGreater(row['avg'], 0)
            self.assertGreater(row['count'], 0)
