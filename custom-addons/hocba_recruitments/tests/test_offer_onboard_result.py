"""Kết quả nhận việc — ứng viên nhận offer rồi có đến hay không.

Spec: docs/superpowers/specs/2026-08-09-recruitment-onboard-result-design.md

Trước bản này tab "Offer & Nhận việc" chỉ có đường đi tiếp (offer → ngày nhận
việc → tạo hồ sơ NV); ứng viên bùng nằm lại vô thời hạn ở bước Gửi Offer, lẫn
với người đang chờ tới ngày đi làm, và không đo được tỷ lệ nhận offer rồi bùng.

Ô mới `hr.applicant.onboard_result` (Đã đến / Không nhận việc; trống = chưa xác
định) là chỗ chốt: đến thì đánh "Đã đến" rồi bấm tạo hồ sơ, không đến thì đánh
"Không nhận việc" — hồ sơ VẪN ở tab Offer kèm badge đỏ, không lưu trữ.
"""
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestOnboardResult(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dept = cls.env['hr.department'].create({'name': 'Phòng Offer (test)'})
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR (test offer)',
            'login': 'test_offer_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref('hr_recruitment.group_hr_recruitment_user').id)],
        })
        Stage = cls.env['hr.recruitment.stage']
        cls.stage_offer = Stage.search(
            [('sequence', '>=', 80), ('hired_stage', '=', False)],
            order='sequence', limit=1)
        cls.stage_hired = Stage.search([('hired_stage', '=', True)], limit=1)

        cls.job = cls.env['hr.job'].create({
            'name': 'Vị trí offer (test)',
            'department_id': cls.dept.id, 'no_of_recruitment': 0})
        # qty rộng để ứng viên vào bước hired không kích hoạt tự đóng phiếu.
        cls.req = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dept.id, 'job_id': cls.job.id,
            'job_title': cls.job.name, 'qty_expected': 10})
        cls.req.action_submit()
        cls.req.action_approve()

    def _uv(self, name, **vals):
        return self.env['hr.applicant'].create(dict(
            {'partner_name': name, 'job_id': self.job.id,
             'stage_id': self.stage_offer.id}, **vals))

    def _patch(self, app_id, payload, expect=200):
        self.authenticate('test_offer_hr', PWD)
        res = self.url_open('%s/applicant/%s' % (BASE, app_id),
                            data=payload,
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    def _row(self, req):
        self.authenticate('test_offer_hr', PWD)
        rows = self.url_open('%s/jobs' % BASE).json()['requests']
        found = [r for r in rows if r['id'] == req.id]
        self.assertTrue(found)
        return found[0]

    # ── Ghi nhận kết quả ─────────────────────────────────────────────────────

    def test_01_record_arrived_and_no_show(self):
        """Lưu được cả hai giá trị qua API, đọc lại đúng."""
        a = self._uv('UV đã đến')
        det = self._patch(a.id, '{"onboardResult": "arrived"}')
        self.assertEqual(det['onboardResult'], 'arrived')
        self.assertEqual(a.onboard_result, 'arrived')

        b = self._uv('UV bùng')
        det = self._patch(b.id, '{"onboardResult": "no_show"}')
        self.assertEqual(det['onboardResult'], 'no_show')

    def test_02_blank_means_undecided(self):
        """Chưa điền = chưa xác định, không phải giá trị riêng."""
        a = self._uv('UV chờ tới ngày')
        self.assertFalse(a.onboard_result)
        self.authenticate('test_offer_hr', PWD)
        row = self.url_open('%s/applicant/%s' % (BASE, a.id)).json()
        self.assertEqual(row['onboardResult'], '')

    def test_03_bad_value_rejected(self):
        a = self._uv('UV giá trị lạ')
        self._patch(a.id, '{"onboardResult": "banana"}', expect=400)
        self.assertFalse(a.onboard_result)

    def test_04_labels_shipped_to_spa(self):
        """SPA không hard-code chuỗi tiếng Việt — nhãn phải đi kèm payload."""
        self.authenticate('test_offer_hr', PWD)
        labels = self.url_open('%s/cv' % BASE).json()['onboardResultLabels']
        self.assertEqual(set(labels), {'arrived', 'no_show'})

    # ── BR-OB-02: chặn tạo hồ sơ khi ứng viên bùng ───────────────────────────

    def test_10_no_show_blocks_create_employee(self):
        """Ẩn nút ở UI chỉ là lớp mềm; gọi thẳng API vẫn phải bị chặn."""
        a = self._uv('UV bùng chặn tạo hồ sơ', onboard_result='no_show')
        self.authenticate('test_offer_hr', PWD)
        res = self.url_open('%s/applicant/%s/create-employee' % (BASE, a.id),
                            data='{}', headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, 400, res.text[:400])
        self.assertFalse(a.employee_id, 'không được tạo hồ sơ nhân viên')

    def test_11_arrived_can_create_employee(self):
        a = self._uv('UV đến rồi tạo hồ sơ', onboard_result='arrived')
        self.authenticate('test_offer_hr', PWD)
        res = self.url_open('%s/applicant/%s/create-employee' % (BASE, a.id),
                            data='{}', headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, 200, res.text[:400])
        self.assertTrue(res.json().get('created'))
        self.assertTrue(a.employee_id)

    # ── Thông báo "cần hoàn thiện hồ sơ" sau khi Onboard ─────────────────────
    # Hồ sơ tạo từ ứng viên thiếu CCCD / MST / BHXH (tuyển dụng không có các
    # thông tin này). Thiếu ba mục đó thì KHÔNG lên chính thức được (BR-010) —
    # mà người tạo hồ sơ là bộ phận tuyển dụng, người phải điền lại là HR, nên
    # nếu không báo thì hồ sơ nằm im tới lúc hết thử việc mới lòi ra.

    def _notifs_for(self, emp):
        return self.env['hb.notification'].sudo().search([
            ('kind', '=', 'profile_incomplete'),
            ('target_ref', '=', emp.id)])

    def test_14_onboard_sends_profile_incomplete_notification(self):
        a = self._uv('UV bao hoan thien', onboard_result='arrived')
        self.authenticate('test_offer_hr', PWD)
        self.url_open('%s/applicant/%s/create-employee' % (BASE, a.id),
                      data='{}', headers={'Content-Type': 'application/json'})
        notifs = self._notifs_for(a.employee_id)
        self.assertTrue(notifs, 'phải có thông báo cần hoàn thiện hồ sơ')
        n = notifs[0]
        self.assertEqual(n.category, 'onboarding')
        self.assertEqual(n.level, 'warning')
        # Bấm thông báo phải mở đúng hồ sơ đó, không phải danh sách chung.
        self.assertEqual(n.target_view, 'employees')
        self.assertEqual(n.target_ref, a.employee_id.id)
        self.assertIn('CCCD', n.body or '')
        self.assertIn('BHXH', n.body or '')

    def test_15_notification_reaches_recruiter_who_clicked(self):
        """Người bấm Onboard phải nhận được — họ là người biết hồ sơ vừa sinh ra."""
        a = self._uv('UV bao nguoi bam', onboard_result='arrived')
        self.authenticate('test_offer_hr', PWD)
        self.url_open('%s/applicant/%s/create-employee' % (BASE, a.id),
                      data='{}', headers={'Content-Type': 'application/json'})
        recipients = self._notifs_for(a.employee_id).mapped('recipient_id')
        self.assertIn(self.user_hr, recipients)

    def test_16_no_notification_when_profile_already_complete(self):
        """Hồ sơ đã đủ CCCD/MST/BHXH (tạo lại từ ứng viên đã có NV) ⇒ không báo
        thừa. Ở đây ứng viên đã gắn NV nên endpoint trả về hồ sơ cũ, không tạo."""
        emp = self.env['hr.employee'].create({
            'name': 'NV du ho so', 'x_employment_status': 'probation',
            'identification_id': '111122223333',
            'x_pit_code': '8123456789', 'x_social_insurance_no': '0123456789'})
        a = self._uv('UV da co ho so', onboard_result='arrived',
                     employee_id=emp.id)
        self.authenticate('test_offer_hr', PWD)
        self.url_open('%s/applicant/%s/create-employee' % (BASE, a.id),
                      data='{}', headers={'Content-Type': 'application/json'})
        self.assertFalse(self._notifs_for(emp))

    # ── BR-OB-03 / BR-OB-04 ──────────────────────────────────────────────────

    def test_12_cannot_mark_no_show_after_handover(self):
        """Đã bàn giao nhân sự mà đánh "không nhận việc" là mâu thuẫn dữ liệu."""
        a = self._uv('UV đã bàn giao')
        a.write({'stage_id': self.stage_hired.id})
        with self.assertRaises(ValidationError):
            a.write({'onboard_result': 'no_show'})

    def test_13_no_show_is_reversible(self):
        """UV đổi ý / HR chọn nhầm — không khoá một chiều."""
        a = self._uv('UV đổi ý', onboard_result='no_show')
        a.write({'onboard_result': 'arrived'})
        self.assertEqual(a.onboard_result, 'arrived')
        a.write({'onboard_result': False})
        self.assertFalse(a.onboard_result)

    # ── Phễu: ô "Nhận việc" phải trừ người bùng (cách C) ─────────────────────

    def test_20_no_show_excluded_from_onboard_count(self):
        """Có ngày nhận việc nhưng đã bùng → KHÔNG tính là nhận việc."""
        self._uv('UV có ngày rồi bùng',
                 start_date='2026-09-20', onboard_result='no_show')
        self.assertEqual(self._row(self.req)['onboard'], 0)

    def test_21_arrived_counts_even_without_start_date(self):
        """Đánh "Đã đến" là đủ, không bắt phải điền ngày mới được tính."""
        self._uv('UV đến nhưng chưa điền ngày', onboard_result='arrived')
        self.assertEqual(self._row(self.req)['onboard'], 1)

    def test_22_old_rule_still_works(self):
        """Dữ liệu cũ chưa ai điền ô mới vẫn đếm như trước — không tụt về 0."""
        self._uv('UV cũ chỉ có ngày', start_date='2026-09-20')
        self.assertEqual(self._row(self.req)['onboard'], 1)

    def test_23_funnel_invariant_holds(self):
        """hired ≤ Nhận việc ≤ PV — bất biến phễu không được vỡ vì ô mới."""
        self._uv('UV bùng', start_date='2026-09-20', onboard_result='no_show')
        self._uv('UV đến', onboard_result='arrived')
        handed = self._uv('UV bàn giao')
        handed.write({'stage_id': self.stage_hired.id})

        r = self._row(self.req)
        self.assertGreaterEqual(r['onboard'], r['hired'])
        self.assertGreaterEqual(r['pvCount'], r['onboard'])
