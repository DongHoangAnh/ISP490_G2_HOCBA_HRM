# ============================================================
# Test tab "Sức khỏe NV" — cảnh báo burnout (Widget 5-6 / BR-040).
# Spec: docs/superpowers/specs/2026-07-07-timeoff-burnout-dashboard-lapsed-link-design.md
# Gọi thẳng helper cấp module _burnout_table theo quy ước repo.
# View tính theo CURRENT_DATE (90 ngày gần nhất) → ngày test đặt động.
# DB test có thể chứa demo data → chỉ assert membership + KPI >=.
# Owner: Nhật Anh.
# ============================================================
from datetime import date, timedelta

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _scope_for, _burnout_table, _public_holiday_dates_env,
)


@tagged('post_install', '-at_install')
class TestTimeoffBurnout(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.user.tz = 'UTC'

        Dept = self.env['hr.department']
        self.dept_a = Dept.create({'name': 'Khối A (burnout)'})
        self.dept_b = Dept.create({'name': 'Khối B (burnout)'})

        self.emp_mgr_a = self._mk_emp('TP A burnout', '150000000001', self.dept_a)
        self.emp_a = self._mk_emp('NV A burnout', '150000000002', self.dept_a)
        self.emp_b = self._mk_emp('NV B burnout', '150000000003', self.dept_b)
        self.dept_a.manager_id = self.emp_mgr_a.id

        self.mgr_a_user = self._mk_user('burnout_mgr_a', self.emp_mgr_a)
        self.user_a = self._mk_user('burnout_nv_a', self.emp_a)
        self.hr_user = self.env['res.users'].create({
            'name': 'HR burnout', 'login': 'burnout_hr', 'tz': 'UTC',
            'group_ids': [(4, self.env.ref('hr.group_hr_manager').id)]})

        self.sick = self.env.ref('hocba_timeoff.hb_leave_type_sick')
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')

    # ----- Helpers (mẫu test_lapsed.py) -----
    def _mk_emp(self, name, cccd, dept):
        # BR-010: NV official cần CCCD 12 số duy nhất.
        return self.env['hr.employee'].create({
            'name': name, 'department_id': dept.id,
            'x_employment_status': 'official', 'identification_id': cccd,
            'x_pit_code': cccd[2:], 'x_social_insurance_no': cccd[:10],
        })

    def _mk_user(self, login, emp):
        user = self.env['res.users'].create({
            'name': login, 'login': login, 'tz': 'UTC',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        emp.user_id = user
        return user

    def _past_working_days(self, n):
        """n ngày LÀM VIỆC (T2–T6, trừ lễ đã seed) gần nhất TRƯỚC hôm nay,
        tăng dần — nằm gọn trong cửa sổ 90 ngày của view."""
        holidays = _public_holiday_dates_env(
            self.env, date.today() - timedelta(days=n * 3 + 30), date.today())
        days, cur = [], date.today() - timedelta(days=1)
        while len(days) < n:
            if cur.weekday() < 5 and cur not in holidays:
                days.append(cur)
            cur -= timedelta(days=1)
        return list(reversed(days))

    def _approved_leave(self, emp, d_from, d_to, leave_type):
        """Đơn nghỉ đã duyệt (state='validate') — view chỉ đếm đơn validate.
        Mẫu approve: tests/test_balances.py."""
        leave = self.env['hr.leave'].create({
            'name': 'Burnout test', 'employee_id': emp.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': d_from, 'request_date_to': d_to,
            'request_date_from_period': 'am',
            'request_date_to_period': 'pm',
        })
        leave.action_approve()
        if leave.state != 'validate':
            leave._action_validate()
        return leave

    def _table(self, user, dept_id=False):
        # View SQL đọc thẳng bảng → flush ORM trước khi query.
        self.env.flush_all()
        env = self.env(user=user)
        return _burnout_table(env, _scope_for(env), dept_id)

    def _find(self, table, emp):
        return next((r for r in table['items']
                     if r['employeeId'] == emp.id), None)

    # ----- Tests -----
    def test_sick_frequency_flagged(self):
        """BR-040 criterion 1: >=3 lần nghỉ ốm / 90 ngày → cảnh báo nhóm ốm."""
        days = self._past_working_days(3)
        for d in days:
            self._approved_leave(self.emp_a, d, d, self.sick)
        table = self._table(self.hr_user)
        row = self._find(table, self.emp_a)
        self.assertIsNotNone(row, 'NV nghỉ ốm 3 lần phải có trong bảng')
        self.assertEqual(row['sickCount3m'], 3)
        self.assertTrue(row['riskReason'].startswith('Nghỉ ốm'))
        self.assertGreaterEqual(table['kpi']['sickFreq'], 1)
        self.assertGreaterEqual(table['kpi']['total'], 1)

    def test_high_absence_flagged(self):
        """BR-040 criterion 2: vắng >10 ngày / 90 ngày → nhóm 'Vắng nhiều'.
        Dùng Không Lương (requires_allocation=False) để không dính quỹ."""
        days = self._past_working_days(11)
        self._approved_leave(self.emp_b, days[0], days[-1], self.unpaid)
        table = self._table(self.hr_user)
        row = self._find(table, self.emp_b)
        self.assertIsNotNone(row, 'NV vắng 11 ngày phải có trong bảng')
        self.assertGreater(row['absenceDays3m'], 10)
        self.assertTrue(row['riskReason'].startswith('Vắng'))
        self.assertGreaterEqual(table['kpi']['highAbsence'], 1)

    def test_normal_employee_not_listed(self):
        """NV không có đơn nào → không nằm trong bảng cảnh báo."""
        table = self._table(self.hr_user)
        self.assertIsNone(self._find(table, self.emp_a))
        self.assertIsNone(self._find(table, self.emp_mgr_a))

    def test_scope_dept_manager_sees_own_dept_only(self):
        """Trưởng phòng A thấy NV phòng A, KHÔNG thấy NV phòng B."""
        days = self._past_working_days(3)
        for d in days:
            self._approved_leave(self.emp_a, d, d, self.sick)   # Khối A
            self._approved_leave(self.emp_b, d, d, self.sick)   # Khối B
        table_hr = self._table(self.hr_user)
        self.assertIsNotNone(self._find(table_hr, self.emp_a))
        self.assertIsNotNone(self._find(table_hr, self.emp_b))
        table_mgr = self._table(self.mgr_a_user)
        self.assertIsNotNone(self._find(table_mgr, self.emp_a))
        self.assertIsNone(self._find(table_mgr, self.emp_b))

    def test_dept_filter_for_hr(self):
        """HR lọc dept → chỉ còn phòng đó (dept truyền vào helper)."""
        days = self._past_working_days(3)
        for d in days:
            self._approved_leave(self.emp_a, d, d, self.sick)
            self._approved_leave(self.emp_b, d, d, self.sick)
        table = self._table(self.hr_user, dept_id=self.dept_a.id)
        self.assertIsNotNone(self._find(table, self.emp_a))
        self.assertIsNone(self._find(table, self.emp_b))

    def test_regular_user_has_no_approve_scope(self):
        """User thường: canApprove=False → endpoint /burnout trả 403
        (gate nằm trong api_burnout, y hệt api_lapsed_dashboard)."""
        env_nv = self.env(user=self.user_a)
        self.assertFalse(_scope_for(env_nv)['canApprove'])
