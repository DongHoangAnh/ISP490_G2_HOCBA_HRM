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

    def _review(self, index=1, state='published', scores=None, emp=None):
        """Phiếu đánh giá định kỳ (hocba_reviews) — nguồn CHÍNH của mốc đánh
        giá từ 2026-08-12. create() tự sinh dòng chấm từ bộ tiêu chí.
        scores: dict {thứ_tự_dòng: điểm}; dòng không khai thì chấm tối đa."""
        rec = self.env['hb.performance.review'].create({
            'employee_id': (emp or self.emp).id, 'period_type': 'quarter',
            'period_year': 2026, 'period_index': index})
        for i, line in enumerate(rec.line_ids):
            line.score = (scores or {}).get(i, line.max_score)
        rec.manager_note = 'Nhận xét của quản lý cho kỳ %s.' % index
        if state in ('confirmed', 'published'):
            rec.action_confirm()
        if state == 'published':
            rec.action_publish()
        return rec

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
        self._review(index=1)
        self._review(index=2)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        rows = {r['name']: r for r in out['criteriaRadar']}
        self.assertTrue(rows, 'Radar phải có dòng của phiếu gần nhất')
        self.assertTrue(all(r['maxScore'] > 0 for r in rows.values()))

    def test_criteria_radar_carries_previous_score_same_criterion(self):
        # Cùng bộ tiêu chí qua 2 kỳ → dòng radar phải mang điểm kỳ liền trước.
        self._review(index=1, scores={0: 1})
        latest = self._review(index=2, scores={0: 3})
        name = latest.line_ids[0].criteria_id.name
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        row = next(r for r in out['criteriaRadar'] if r['name'] == name)
        self.assertEqual(row['score'], 3)
        self.assertEqual(row['previous'], 1)

    def test_criteria_radar_bo_qua_dot_danh_gia_cu(self):
        """Chỉ còn MỘT bộ tiêu chí (hb.review.criteria): đợt cũ vẫn nằm trên
        timeline nhưng KHÔNG được góp tiêu chí vào radar."""
        self._eval(when=date(2026, 6, 1), score=8)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        self.assertEqual(out['criteriaRadar'], [])
        self.assertIn('evaluation', self._kinds(out))

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
        rv = self._review(index=1, scores={0: 1})   # dòng đầu điểm thấp nhất
        weakest = rv.line_ids[0].criteria_id.name
        texts = ' | '.join(i['text'] for i in _career_payload(
            self._env(self.hr_mgr), self.emp.id)['insights'])
        self.assertIn('thấp nhất', texts)
        self.assertIn(weakest, texts.split('thấp nhất')[-1][:80])

    def test_insight_tied_criteria_says_even(self):
        # Điểm bằng nhau hết: min() và max() trả cùng một tiêu chí → hiện
        # "thấp nhất X" ngay cạnh "cao nhất X" thì vô nghĩa (thấy trên Neon
        # 2026-08-09, NV nào cũng 4/5 cả 4 tiêu chí).
        self._review(index=1)   # mọi tiêu chí đều chấm tối đa → hoà tuyệt đối
        texts = ' | '.join(i['text'] for i in _career_payload(
            self._env(self.hr_mgr), self.emp.id)['insights'])
        self.assertNotIn('thấp nhất', texts)
        self.assertNotIn('cao nhất', texts)
        self.assertIn('đều nhau', texts)

    # --- nguồn đánh giá mới: phạm vi trạng thái theo người xem ---
    def test_nhan_vien_chi_thay_phieu_da_cong_bo(self):
        """hocba_reviews chỉ báo NV ở bước publish; cho NV thấy phiếu vừa chốt
        là lộ kết quả trước khi HR công bố."""
        self._review(index=1, state='confirmed')
        out = _career_payload(self._env(self.plain), 0)
        self.assertEqual(
            [e for e in out['evaluations'] if e['source'] == 'review'], [])

    def test_nhan_vien_thay_phieu_da_cong_bo(self):
        self._review(index=1, state='published')
        out = _career_payload(self._env(self.plain), 0)
        got = [e for e in out['evaluations'] if e['source'] == 'review']
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]['state'], 'published')

    def test_quan_ly_thay_ca_phieu_moi_chot(self):
        self._review(index=1, state='confirmed')
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        got = [e for e in out['evaluations'] if e['source'] == 'review']
        self.assertEqual([e['state'] for e in got], ['confirmed'])

    def test_timeline_gop_ca_hai_nguon(self):
        self._eval(when=date(2026, 3, 1), score=8)      # nguồn cũ
        self._review(index=2, state='published')        # nguồn mới
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        srcs = sorted(e['source'] for e in out['evaluations'])
        self.assertEqual(srcs, ['legacy', 'review'])
        self.assertEqual(
            len([k for k in self._kinds(out) if k == 'evaluation']), 2)

    def test_dot_cu_khong_con_chi_tiet_tieu_chi(self):
        """Mốc cũ giữ lại làm lịch sử nhưng không bày điểm bộ tiêu chí đã bỏ."""
        self._eval(when=date(2026, 3, 1), score=8)
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        legacy = next(e for e in out['evaluations'] if e['source'] == 'legacy')
        self.assertEqual(legacy['lines'], [])

    def test_score_trend_gom_ca_hai_nguon_theo_thu_tu_ngay(self):
        self._eval(when=date(2026, 3, 1), score=8)
        self._review(index=2, state='published')
        out = _career_payload(self._env(self.hr_mgr), self.emp.id)
        dates = [p['date'] for p in out['scoreTrend']]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), 2)

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
