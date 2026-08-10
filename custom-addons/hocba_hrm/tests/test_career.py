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
        self.assertEqual(self._kinds(out).count('join'), 1)
        joins = [t for t in out['timeline'] if t['badge'] == 'Nhận việc']
        self.assertEqual(len(joins), 1)

    def test_career_join_snapshot_not_counted_as_promotion(self):
        # Bộ lọc dòng thời gian đếm theo kind. Snapshot 'join' mang kind
        # 'promotion' thì người chưa từng thăng chức vẫn thấy chip
        # "Thăng tiến (1)" ngay cạnh ô "Lần thăng chức: 0" — đúng cái mâu
        # thuẫn đã sửa ở tầng thống kê, còn sót ở tầng dòng thời gian.
        bare = self.env['hr.employee'].create({
            'name': 'Chua Thang Chuc Chip', 'x_employee_code': 'EMP-CAR-7'})
        out = _career_payload(self._env(self.hr_mgr), bare.id)
        self.assertEqual(out['stats']['promoCount'], 0)
        self.assertEqual(self._kinds(out).count('promotion'), 0)
        self.assertEqual(self._kinds(out).count('join'), 1)

    def test_career_real_promotion_still_counted(self):
        # Đừng sửa quá tay: thăng chức thật vẫn phải nằm trong nhóm 'promotion'
        # (và các biến động khác — lương/thử việc — cũng vậy).
        self._promo()
        self._promo(x_change_type='salary', date_effective=date(2026, 5, 2))
        kinds = self._kinds(_career_payload(self._env(self.hr_mgr),
                                            self.emp.id))
        self.assertEqual(kinds.count('promotion'), 2)

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

    def test_career_join_snapshot_titled_not_dashes(self):
        # Snapshot 'join' không có chức vụ trước/sau → tiêu đề "— → —" vô
        # nghĩa với người đọc; phải là "Vào làm việc".
        bare = self.env['hr.employee'].create({
            'name': 'Moi Vao', 'x_employee_code': 'EMP-CAR-5'})
        out = _career_payload(self._env(self.hr_mgr), bare.id)
        row = next(t for t in out['timeline'] if t['badge'] == 'Nhận việc')
        self.assertEqual(row['title'], 'Vào làm việc')

    # --- thống kê ---
    def test_career_months_since_promo_none_without_promotion(self):
        # Hồ sơ nào cũng có snapshot 'join'; tính "tháng từ lần thăng tiến"
        # theo bản ghi gần nhất BẤT KỲ LOẠI thì người chưa từng thăng chức
        # vẫn hiện một con số — mâu thuẫn với "Lần thăng chức: 0".
        bare = self.env['hr.employee'].create({
            'name': 'Chua Thang Chuc', 'x_employee_code': 'EMP-CAR-6'})
        out = _career_payload(self._env(self.hr_mgr), bare.id)
        self.assertEqual(out['stats']['promoCount'], 0)
        self.assertIsNone(out['stats']['monthsSincePromo'])

    def test_career_months_since_promo_set_after_promotion(self):
        self._promo()
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertIsNotNone(out['stats']['monthsSincePromo'])

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

    # --- dữ liệu cho biểu đồ (thiết kế lại 2026-08-09: 1 màn dashboard) ---
    def test_criteria_radar_compares_latest_with_previous(self):
        self._eval(when=date(2026, 6, 1), score=6)
        self._eval(when=date(2026, 7, 1), score=9)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        # 2 đợt dùng 2 tiêu chí khác nhau (code theo ngày) → radar phải gộp
        # theo TÊN tiêu chí, đợt trước thiếu thì để None chứ không bịa 0.
        rows = {r['name']: r for r in out['criteriaRadar']}
        self.assertTrue(rows, 'Radar phải có dòng của đợt gần nhất')
        latest = [r for r in out['criteriaRadar'] if r['score'] is not None]
        self.assertTrue(latest)
        self.assertTrue(all(r['maxScore'] > 0 for r in latest))

    def test_criteria_radar_carries_previous_score_same_criterion(self):
        crit = self.env['hr.promotion.criteria'].create({
            'name': 'Tiêu chí chung', 'code': 'car_shared',
            'weight': 100, 'max_score': 10})

        def mk(when, score):
            ev = self.env['hr.promotion.evaluation'].create({
                'employee_id': self.emp.id, 'eval_date': when,
                'verdict_final': 'qualified',
                'line_ids': [(0, 0, {'criteria_id': crit.id, 'score': score})]})
            ev.action_confirm()

        mk(date(2026, 6, 1), 6)
        mk(date(2026, 7, 1), 9)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        row = next(r for r in out['criteriaRadar'] if r['name'] == 'Tiêu chí chung')
        self.assertEqual(row['score'], 9)
        self.assertEqual(row['previous'], 6)

    def test_criteria_radar_empty_without_evaluation(self):
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertEqual(out['criteriaRadar'], [])

    def test_onboarding_progress_counts_by_state(self):
        Step = self.env['hb.onboarding.step']
        for name, state in [('A', 'done'), ('B', 'done'), ('C', 'skipped'),
                            ('D', 'open'), ('E', 'waiting')]:
            Step.create({'employee_id': self.emp.id, 'name': name,
                         'step_type': 'task', 'state': state})
        p = _career_payload(self._env(self.hr_mgr),
                            self.emp.id)['onboardingProgress']
        self.assertEqual(
            [p['done'], p['skipped'], p['open'], p['waiting'], p['total']],
            [2, 1, 1, 1, 5])

    def test_insight_score_improved(self):
        self._eval(when=date(2026, 6, 1), score=6)
        self._eval(when=date(2026, 7, 1), score=9)
        texts = ' | '.join(i['text'] for i in _career_payload(
            self._env(self.hr_mgr), self.emp.id)['insights'])
        self.assertIn('tăng', texts)

    def test_insight_score_dropped(self):
        self._eval(when=date(2026, 6, 1), score=9)
        self._eval(when=date(2026, 7, 1), score=5)
        ins = _career_payload(self._env(self.hr_mgr), self.emp.id)['insights']
        drop = next(i for i in ins if 'giảm' in i['text'])
        self.assertEqual(drop['kind'], 'down')

    def test_insight_weakest_criterion(self):
        crit_lo = self.env['hr.promotion.criteria'].create({
            'name': 'Kỹ năng yếu', 'code': 'car_lo', 'weight': 50,
            'max_score': 10})
        crit_hi = self.env['hr.promotion.criteria'].create({
            'name': 'Kỹ năng mạnh', 'code': 'car_hi', 'weight': 50,
            'max_score': 10})
        ev = self.env['hr.promotion.evaluation'].create({
            'employee_id': self.emp.id, 'eval_date': date(2026, 7, 1),
            'verdict_final': 'qualified',
            'line_ids': [(0, 0, {'criteria_id': crit_lo.id, 'score': 3}),
                         (0, 0, {'criteria_id': crit_hi.id, 'score': 10})]})
        ev.action_confirm()
        texts = ' | '.join(i['text'] for i in _career_payload(
            self._env(self.hr_mgr), self.emp.id)['insights'])
        self.assertIn('Kỹ năng yếu', texts)
        self.assertNotIn('Kỹ năng mạnh', texts.split('thấp nhất')[-1][:40])

    def test_insight_tied_criteria_says_even(self):
        # Điểm bằng nhau hết: min() và max() trả cùng một tiêu chí → hiện
        # "thấp nhất X" ngay cạnh "cao nhất X" thì vô nghĩa (thấy trên Neon
        # 2026-08-09, NV nào cũng 4/5 cả 4 tiêu chí).
        crit_a = self.env['hr.promotion.criteria'].create({
            'name': 'Tiêu chí A', 'code': 'car_tie_a', 'weight': 50,
            'max_score': 10})
        crit_b = self.env['hr.promotion.criteria'].create({
            'name': 'Tiêu chí B', 'code': 'car_tie_b', 'weight': 50,
            'max_score': 10})
        ev = self.env['hr.promotion.evaluation'].create({
            'employee_id': self.emp.id, 'eval_date': date(2026, 7, 1),
            'verdict_final': 'qualified',
            'line_ids': [(0, 0, {'criteria_id': crit_a.id, 'score': 8}),
                         (0, 0, {'criteria_id': crit_b.id, 'score': 8})]})
        ev.action_confirm()
        texts = ' | '.join(i['text'] for i in _career_payload(
            self._env(self.hr_mgr), self.emp.id)['insights'])
        self.assertNotIn('thấp nhất', texts)
        self.assertNotIn('cao nhất', texts)
        self.assertIn('đều nhau', texts)

    def test_insight_no_evaluation_yet(self):
        ins = _career_payload(self._env(self.hr_mgr), self.emp.id)['insights']
        self.assertTrue(any('Chưa có đợt đánh giá' in i['text'] for i in ins))

    def test_insight_long_time_without_promotion(self):
        # Mốc thăng chức cách đây > 12 tháng → cảnh báo, để quản lý nhìn ra
        # ngay người bị bỏ quên.
        self._promo(date_effective=date(2024, 1, 1))
        ins = _career_payload(self._env(self.hr_mgr), self.emp.id)['insights']
        warn = next(i for i in ins if 'chưa có thay đổi chức vụ' in i['text'])
        self.assertEqual(warn['kind'], 'warn')

    def test_insight_salary_hidden_from_non_manager(self):
        # Insight không được rò lương cho người không được xem lương.
        hr_officer = self.env['res.users'].create({
            'name': 'HR Officer Ins', 'login': 'hrofficer_ins',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self._promo(from_wage=10000000, to_wage=15000000,
                    x_evidence_url='http://kpi')
        texts = ' '.join(i['text'] for i in _career_payload(
            self._env(hr_officer), self.emp.id)['insights'])
        self.assertNotIn('15.000.000', texts)
        self.assertNotIn('15000000', texts)

    def test_career_score_trend_ascending(self):
        self._eval(when=date(2026, 7, 1), score=10)
        self._eval(when=date(2026, 6, 1), score=8)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertEqual([p['date'] for p in out['scoreTrend']],
                         ['2026-06-01', '2026-07-01'])
