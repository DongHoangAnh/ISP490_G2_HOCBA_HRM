from datetime import date

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import _career_payload


@tagged('post_install', '-at_install')
class TestCareer(TransactionCase):
    """Trang Lộ trình sự nghiệp — spec 2026-08-09 §4."""

    def setUp(self):
        super().setUp()
        Users = self.env['res.users']
        self.hr_mgr = Users.create({
            'name': 'HR Mgr Career', 'login': 'hrmgr_career',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self.plain = Users.create({
            'name': 'Plain Career', 'login': 'plain_career',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.outsider = Users.create({
            'name': 'Outsider', 'login': 'outsider_career',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})

        self.dept = self.env['hr.department'].create({'name': 'Phòng Lộ trình'})
        Job = self.env['hr.job']
        self.job_old = Job.create({'name': 'Chuyên viên'})
        self.job_new = Job.create({'name': 'Trưởng nhóm'})
        self.emp = self.env['hr.employee'].create({
            'name': 'Nguoi Co Lich Su', 'x_employee_code': 'EMP-CAR-1',
            'department_id': self.dept.id, 'job_id': self.job_old.id,
            'user_id': self.plain.id})
        self.other_emp = self.env['hr.employee'].create({
            'name': 'Nguoi Khac', 'x_employee_code': 'EMP-CAR-2',
            'user_id': self.outsider.id})

    def _env(self, user):
        return self.env(user=user)

    def _promo(self, **kw):
        vals = {'employee_id': self.emp.id, 'x_change_type': 'promotion',
                'from_job_id': self.job_old.id, 'to_job_id': self.job_new.id,
                'date_effective': date(2026, 5, 1),
                'decision_ref': 'QD-01', 'reason': 'Hoàn thành tốt'}
        vals.update(kw)
        return self.env['hr.promotion.history'].create(vals)

    def _eval(self, confirm=True, when=date(2026, 6, 1), score=8):
        crit = self.env['hr.promotion.criteria'].create({
            'name': 'Tiêu chí LT', 'code': 'car_%s' % when.toordinal(),
            'weight': 100, 'max_score': 10})
        ev = self.env['hr.promotion.evaluation'].create({
            'employee_id': self.emp.id, 'eval_date': when,
            'verdict_final': 'qualified',
            'conclusion_note': 'Làm việc chủ động',
            'line_ids': [(0, 0, {'criteria_id': crit.id, 'score': score})]})
        if confirm:
            ev.action_confirm()
        return ev

    def _kinds(self, out):
        return [t['kind'] for t in out['timeline']]

    # --- quyền ---
    def test_career_self_by_zero(self):
        out = _career_payload(self._env(self.plain), 0)
        self.assertTrue(out['isSelf'])
        self.assertEqual(out['employee']['id'], self.emp.id)
        self.assertEqual(out['employee']['code'], 'EMP-CAR-1')

    def test_career_self_by_own_id(self):
        out = _career_payload(self._env(self.plain), self.emp.id)
        self.assertTrue(out['isSelf'])

    def test_career_forbidden_out_of_scope(self):
        with self.assertRaises(AccessError):
            _career_payload(self._env(self.outsider), self.emp.id)

    def test_career_hr_manager_allowed(self):
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertFalse(out['isSelf'])
        self.assertTrue(out['canManage'])

    def test_career_no_employee_for_user(self):
        naked = self.env['res.users'].create({
            'name': 'Khong Ho So', 'login': 'naked_career',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaisesRegex(ValidationError, 'chưa được gắn'):
            _career_payload(self._env(naked), 0)

    def test_career_unknown_employee(self):
        with self.assertRaisesRegex(ValidationError, 'Không tìm thấy nhân viên'):
            _career_payload(self._env(self.hr_mgr), 999999)

    # --- lương ---
    def test_career_hides_salary_from_plain_user_viewing_self(self):
        # Tự xem hồ sơ mình thì thấy lương của chính mình (đồng bộ /api/me).
        self._promo(from_wage=10000000, to_wage=15000000,
                    x_evidence_url='http://kpi')
        out = _career_payload(self._env(self.plain), 0)
        self.assertTrue(out['canSeeSalary'])
        self.assertTrue(out['salaryJourney'])

    def test_career_salary_hidden_from_hr_officer(self):
        # HR officer (hr.group_hr_user, KHÔNG phải manager) không xem lương —
        # giữ nguyên ranh giới _cap_see_salary.
        hr_officer = self.env['res.users'].create({
            'name': 'HR Officer Career', 'login': 'hrofficer_career',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self._promo(from_wage=10000000, to_wage=15000000,
                    x_evidence_url='http://kpi')
        out = _career_payload(self._env(hr_officer), self.emp.id)
        self.assertFalse(out['canSeeSalary'])
        self.assertEqual(out['salaryJourney'], [])
        promo = next(t for t in out['timeline'] if t['kind'] == 'promotion')
        self.assertNotIn('toWage', promo)

    # --- dòng thời gian ---
    def test_career_timeline_has_join_when_no_snapshot(self):
        # Hồ sơ tạo không kèm snapshot 'join' (dữ liệu cũ) vẫn phải có mốc
        # vào làm, để NV mới toanh không thấy trang trống trơn.
        bare = self.env['hr.employee'].with_context(
            hocba_no_join_log=True).create({
                'name': 'Khong Snapshot', 'x_employee_code': 'EMP-CAR-3',
                'x_probation_start': date(2026, 1, 5)})
        out = _career_payload(self._env(self.hr_mgr), bare.id)
        self.assertEqual(self._kinds(out), ['join'])

    def test_career_join_not_duplicated_with_snapshot(self):
        # hr.employee.create tự ghi snapshot 'join' vào hr.promotion.history —
        # thêm mốc tổng hợp nữa là hai dòng "nhận việc" chồng nhau.
        self.emp.x_probation_start = date(2026, 1, 5)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertNotIn('join', self._kinds(out))
        joins = [t for t in out['timeline'] if t['badge'] == 'Nhận việc']
        self.assertEqual(len(joins), 1)

    def test_career_timeline_sorted_desc(self):
        self._promo()
        self._eval()
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        dates = [t['date'] for t in out['timeline'] if t['date']]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_career_timeline_includes_evaluation_and_honor(self):
        self._promo()          # tự sinh 1 mục vinh danh
        self._eval()
        kinds = self._kinds(_career_payload(self._env(self.hr_mgr), self.emp.id))
        self.assertIn('promotion', kinds)
        self.assertIn('evaluation', kinds)
        self.assertIn('honor', kinds)

    def test_career_timeline_includes_onboarding_note(self):
        # "Nhận xét" khách đòi phải nhìn thấy nằm ở result_note của bước.
        self.env['hb.onboarding.step'].create({
            'employee_id': self.emp.id, 'name': 'Đánh giá tuần-2',
            'step_type': 'evaluation', 'state': 'done', 'result': 'pass',
            'result_note': 'Bắt nhịp nhanh', 'done_date': date(2026, 2, 1)})
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        onb = next(t for t in out['timeline'] if t['kind'] == 'onboarding')
        self.assertIn('Bắt nhịp nhanh', onb['detail'])

    def test_career_timeline_skips_pending_onboarding_step(self):
        self.env['hb.onboarding.step'].create({
            'employee_id': self.emp.id, 'name': 'Chưa làm',
            'step_type': 'task', 'state': 'open'})
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertNotIn('onboarding', self._kinds(out))

    def test_career_draft_evaluation_hidden_from_self(self):
        self._eval(confirm=False)
        self.assertNotIn('evaluation', self._kinds(
            _career_payload(self._env(self.plain), 0)))
        self.assertIn('evaluation', self._kinds(
            _career_payload(self._env(self.hr_mgr), self.emp.id)))

    # --- thống kê ---
    def test_career_stats_counts(self):
        self._promo()
        self._eval(when=date(2026, 6, 1), score=8)
        self._eval(when=date(2026, 7, 1), score=10)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        st = out['stats']
        self.assertEqual(st['promoCount'], 1)
        self.assertEqual(st['evalCount'], 2)
        self.assertEqual(st['honorCount'], 1)
        self.assertAlmostEqual(st['avgScore'], 90.0, places=0)
        self.assertAlmostEqual(st['lastScore'], 100.0, places=0)

    def test_career_score_trend_ascending(self):
        self._eval(when=date(2026, 7, 1), score=10)
        self._eval(when=date(2026, 6, 1), score=8)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertEqual([p['date'] for p in out['scoreTrend']],
                         ['2026-06-01', '2026-07-01'])
