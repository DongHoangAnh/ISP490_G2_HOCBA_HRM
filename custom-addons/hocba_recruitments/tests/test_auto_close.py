"""Tự động Ngừng đăng + đóng phiếu khi job tuyển đủ chỉ tiêu.

Ngữ nghĩa core Odoo 19: hr.job.no_of_recruitment = số CÒN THIẾU — core tự trừ 1
khi applicant vào stage hired, cộng lại 1 khi kéo ra khỏi hired. Phiếu yêu cầu
được duyệt (action_approve) cộng qty_expected vào số còn thiếu.
Hook tự đóng chạy khi còn thiếu <= 0 sau một lượt hired.

Ca 1: chưa đủ (còn thiếu 1) → không đụng gì.
Ca 2: đủ (còn thiếu 0) → job stopped + unpublish + phiếu recruiting bị đóng.
Ca 3: kéo ra khỏi hired sau khi đã tự đóng → job KHÔNG tự mở lại.
Ca 4: duyệt phiếu mới sau khi đã đóng → job trở lại recruiting, không tự publish.

Chế độ cấu hình (ir.config_parameter hocba_recruitments.auto_close_mode —
spec 2026-07-23-recruitment-config-design.md):
  full (mặc định) = hành vi trên · stop = chỉ ngừng đăng, giữ phiếu ·
  warn = chỉ cảnh báo chatter · off = tắt · giá trị lạ → coi như full.
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAutoCloseRecruitment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dept = cls.env['hr.department'].create({'name': 'Phòng Test AutoClose'})
        Stage = cls.env['hr.recruitment.stage']
        cls.stage_new = Stage.search([('hired_stage', '=', False)], limit=1)
        if not cls.stage_new:
            cls.stage_new = Stage.create({'name': 'Mới (test)', 'sequence': 1})
        cls.stage_hired = Stage.search([('hired_stage', '=', True)], limit=1)
        if not cls.stage_hired:
            cls.stage_hired = Stage.create(
                {'name': 'Đã tuyển (test)', 'hired_stage': True, 'sequence': 99})
        cls.job = cls.env['hr.job'].create({
            'name': 'Vị trí Test AutoClose',
            'department_id': cls.dept.id,
            'recruitment_status': 'recruiting',
            'x_published': True,
            # hr.job mặc định no_of_recruitment=1 → set 0 để chỉ tiêu
            # đến thuần từ phiếu yêu cầu bên dưới.
            'no_of_recruitment': 0,
        })
        # Phiếu yêu cầu qty=2 → duyệt → còn thiếu = 2, phiếu recruiting
        cls.req = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dept.id,
            'job_id': cls.job.id,
            'job_title': cls.job.name,
            'qty_expected': 2,
        })
        cls.req.action_submit()
        cls.req.action_approve()

    def _new_applicant(self, name):
        return self.env['hr.applicant'].create({
            'partner_name': name,
            'job_id': self.job.id,
            'stage_id': self.stage_new.id,
        })

    def test_01_not_enough_hired_keeps_publishing(self):
        """1/2 hired (còn thiếu 1) → vẫn Đang tuyển + published, phiếu recruiting."""
        a1 = self._new_applicant('UV Một')
        a1.write({'stage_id': self.stage_hired.id})
        self.assertEqual(self.job.no_of_recruitment, 1, 'core phải trừ còn 1')
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        self.assertTrue(self.job.x_published)
        self.assertEqual(self.req.state, 'recruiting')

    def test_02_enough_hired_auto_stops(self):
        """2/2 hired (còn thiếu 0) → tự stopped + unpublish + phiếu closed."""
        a1 = self._new_applicant('UV Một')
        a2 = self._new_applicant('UV Hai')
        a1.write({'stage_id': self.stage_hired.id})
        a2.write({'stage_id': self.stage_hired.id})
        self.assertEqual(self.job.no_of_recruitment, 0)
        self.assertEqual(self.job.recruitment_status, 'stopped')
        self.assertFalse(self.job.x_published)
        if 'is_published' in self.job._fields:
            self.assertFalse(self.job.is_published)
        self.assertEqual(self.req.state, 'closed')

    def test_03_unhire_does_not_reopen(self):
        """Kéo 1 UV ra khỏi hired sau khi tự đóng → job giữ nguyên stopped."""
        a1 = self._new_applicant('UV Một')
        a2 = self._new_applicant('UV Hai')
        (a1 + a2).write({'stage_id': self.stage_hired.id})
        self.assertEqual(self.job.recruitment_status, 'stopped')
        a2.write({'stage_id': self.stage_new.id})
        # core cộng lại 1 vào còn thiếu, nhưng job không tự mở lại
        self.assertEqual(self.job.no_of_recruitment, 1)
        self.assertEqual(self.job.recruitment_status, 'stopped')
        self.assertFalse(self.job.x_published)

    def test_04_new_request_reopens_status_not_publish(self):
        """Duyệt phiếu mới sau khi đóng → recruiting trở lại, KHÔNG tự publish."""
        a1 = self._new_applicant('UV Một')
        a2 = self._new_applicant('UV Hai')
        (a1 + a2).write({'stage_id': self.stage_hired.id})
        self.assertEqual(self.job.recruitment_status, 'stopped')
        self.assertEqual(self.job.no_of_recruitment, 0)
        req2 = self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id,
            'job_id': self.job.id,
            'job_title': self.job.name,
            'qty_expected': 1,
        })
        req2.action_submit()
        req2.action_approve()
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        self.assertEqual(self.job.no_of_recruitment, 1, 'còn thiếu = 1 từ phiếu mới')
        self.assertFalse(self.job.x_published, 'không được tự publish lại')

    def test_05_publish_flag_syncs_status(self):
        """Đổi cờ publish ở tầng model (mọi cửa) → trạng thái tuyển khớp theo."""
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        # Ngừng đăng → Dừng tuyển
        self.job.write({'x_published': False})
        self.assertEqual(self.job.recruitment_status, 'stopped')
        # Đăng lại → Đang tuyển, 2 cờ gương nhau
        self.job.write({'x_published': True})
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        if 'is_published' in self.job._fields:
            self.assertTrue(self.job.is_published)
            # Cửa website: ghi is_published cũng đồng bộ ngược
            self.job.write({'is_published': False})
            self.assertEqual(self.job.recruitment_status, 'stopped')
            self.assertFalse(self.job.x_published)

    def test_06_explicit_status_wins_over_sync(self):
        """Trạng thái truyền tường minh cùng write không bị sync đè."""
        self.job.write({'x_published': False, 'recruitment_status': 'recruiting'})
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        self.assertFalse(self.job.x_published)

    # ── Chế độ auto-close cấu hình được ──────────────────────────────────────

    def _set_mode(self, mode):
        self.env['ir.config_parameter'].sudo().set_param(
            'hocba_recruitments.auto_close_mode', mode)

    def _hire_full_quota(self):
        a1 = self._new_applicant('UV Một')
        a2 = self._new_applicant('UV Hai')
        (a1 + a2).write({'stage_id': self.stage_hired.id})

    def test_07_mode_stop_keeps_requests_open(self):
        """stop: ngừng đăng nhưng KHÔNG đóng phiếu đang tuyển."""
        self._set_mode('stop')
        self._hire_full_quota()
        self.assertEqual(self.job.recruitment_status, 'stopped')
        self.assertFalse(self.job.x_published)
        self.assertEqual(self.req.state, 'recruiting',
                         'mode stop không được đóng phiếu')

    def test_08_mode_warn_only_posts_message(self):
        """warn: giữ nguyên trạng thái + publish, chỉ post cảnh báo chatter."""
        self._set_mode('warn')
        before = len(self.job.message_ids)
        self._hire_full_quota()
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        self.assertTrue(self.job.x_published)
        self.assertEqual(self.req.state, 'recruiting')
        self.assertGreater(len(self.job.message_ids), before,
                           'phải có message cảnh báo trên chatter')

    def test_09_mode_off_does_nothing(self):
        """off: tuyển đủ vẫn không đổi gì."""
        self._set_mode('off')
        before = len(self.job.message_ids)
        self._hire_full_quota()
        self.assertEqual(self.job.recruitment_status, 'recruiting')
        self.assertTrue(self.job.x_published)
        self.assertEqual(self.req.state, 'recruiting')
        self.assertEqual(len(self.job.message_ids), before)

    def test_10_unknown_mode_falls_back_full(self):
        """Giá trị param rác → hành vi mặc định full."""
        self._set_mode('banana')
        self._hire_full_quota()
        self.assertEqual(self.job.recruitment_status, 'stopped')
        self.assertEqual(self.req.state, 'closed')
