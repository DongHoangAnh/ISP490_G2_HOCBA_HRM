"""Tự chuyển bước theo hành động của HR (khâu phỏng vấn).

- Đặt Ngày hẹn PV      : Lên lịch phỏng vấn → Hẹn & mời phỏng vấn
- Gửi thư mời PV       : Hẹn & mời phỏng vấn → Phỏng vấn (test ở tầng model)

Bám xmlid bước, không bám tên — admin đổi tên bước trên màn Cấu hình là chuyện
bình thường.
"""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAutoStage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.st_screen = ref('hocba_recruitments.hb_stage_screening')
        cls.st_sched = ref('hocba_recruitments.hb_stage_schedule')
        cls.st_invite = ref('hocba_recruitments.hb_stage_invite')
        cls.st_interview = ref('hocba_recruitments.hb_stage_interview')
        cls.st_result = ref('hocba_recruitments.hb_stage_result')
        cls.st_offer = ref('hocba_recruitments.hb_stage_offer')
        cls.job = cls.env['hr.job'].create(
            {'name': 'Vị trí Test AutoStage', 'no_of_recruitment': 3})

    def _make_ref_stage(self, xmlid, **vals):
        """Bước mới kèm xmlid module hocba_recruitments — để _hb_stage() tra được."""
        st = self.env['hr.recruitment.stage'].create(
            dict({'name': xmlid, 'sequence': 900}, **vals))
        self.env['ir.model.data'].create({
            'module': 'hocba_recruitments', 'name': xmlid,
            'model': 'hr.recruitment.stage', 'res_id': st.id})
        return st

    def _applicant(self, stage, name='UV auto stage'):
        return self.env['hr.applicant'].create({
            'partner_name': name, 'job_id': self.job.id, 'stage_id': stage.id,
        })

    # ── Đặt Ngày hẹn PV ──────────────────────────────────────────────────────

    def test_01_set_interview_date_moves_schedule_to_invite(self):
        a = self._applicant(self.st_sched)
        a.write({'interview_date': '2026-08-20'})
        self.assertEqual(a.stage_id, self.st_invite)

    def test_02_set_interview_date_does_not_pull_back(self):
        """Ứng viên đã đi xa hơn thì đặt lại ngày PV không kéo lùi bước."""
        a = self._applicant(self.st_interview)
        a.write({'interview_date': '2026-08-21'})
        self.assertEqual(a.stage_id, self.st_interview)

    def test_03_other_stage_untouched(self):
        a = self._applicant(self.st_screen)
        a.write({'interview_date': '2026-08-22'})
        self.assertEqual(a.stage_id, self.st_screen,
                         'Chỉ bước "Lên lịch phỏng vấn" mới tự nhảy')

    def test_04_clearing_date_does_not_move(self):
        a = self._applicant(self.st_sched)
        a.write({'interview_date': False})
        self.assertEqual(a.stage_id, self.st_sched,
                         'Xoá trắng ngày không phải là "đã lên lịch"')

    def test_05_posts_chatter_note(self):
        a = self._applicant(self.st_sched)
        before = len(a.message_ids)
        a.write({'interview_date': '2026-08-23'})
        self.assertGreater(len(a.message_ids), before,
                           'Máy đổi bước thì phải để lại vết trên chatter')

    # ── Pass lọc CV ──────────────────────────────────────────────────────────

    def test_10_pass_cv_moves_screening_to_schedule(self):
        a = self._applicant(self.st_screen)
        a.write({'cv_filter_result': 'pass'})
        self.assertEqual(a.stage_id, self.st_sched)

    def test_11_fail_or_potential_cv_stays(self):
        for val in ('fail', 'potential', 'contact_later'):
            a = self._applicant(self.st_screen, 'UV cv %s' % val)
            a.write({'cv_filter_result': val})
            self.assertEqual(a.stage_id, self.st_screen,
                             'Chỉ Pass mới tự đi tiếp, %s thì HR tự quyết' % val)

    # ── Pass phỏng vấn ───────────────────────────────────────────────────────

    def test_12_pass_interview_from_interview_stage(self):
        a = self._applicant(self.st_interview)
        a.write({'interview_result': 'pass'})
        self.assertEqual(a.stage_id, self.st_offer)

    def test_13_pass_interview_from_result_stage(self):
        """Kết quả PV hay được điền lúc đã ở bước "Kết quả phỏng vấn"."""
        a = self._applicant(self.st_result)
        a.write({'interview_result': 'pass'})
        self.assertEqual(a.stage_id, self.st_offer)

    def test_14_fail_interview_stays(self):
        a = self._applicant(self.st_result)
        a.write({'interview_result': 'fail'})
        self.assertEqual(a.stage_id, self.st_result)

    def test_15_pass_interview_does_not_pull_back(self):
        a = self._applicant(self.st_screen)
        a.write({'interview_result': 'pass'})
        self.assertEqual(a.stage_id, self.st_screen)

    # ── Gửi thư mời PV ───────────────────────────────────────────────────────

    def test_06_invite_moves_invite_to_interview(self):
        a = self._applicant(self.st_invite)
        a._hb_advance_stage('hb_stage_invite', 'hb_stage_interview', 'test')
        self.assertEqual(a.stage_id, self.st_interview)

    def test_07_advance_skips_records_in_other_stages(self):
        a_ok = self._applicant(self.st_invite, 'UV dung buoc')
        a_no = self._applicant(self.st_screen, 'UV khac buoc')
        (a_ok | a_no)._hb_advance_stage(
            'hb_stage_invite', 'hb_stage_interview', 'test')
        self.assertEqual(a_ok.stage_id, self.st_interview)
        self.assertEqual(a_no.stage_id, self.st_screen)

    def test_08_hidden_target_stage_is_noop(self):
        """Admin ẩn bước đích ⇒ im lặng bỏ qua, không chặn thao tác của HR.

        Tự dựng bước + xmlid riêng thay vì ẩn bước seed: bước seed đang có
        ứng viên nên guard _check_can_hide chặn ẩn (đúng như thiết kế).
        """
        hidden = self._make_ref_stage('hb_stage_test_hidden')
        hidden.active = False           # bước mới, chưa có ứng viên ⇒ ẩn được
        a = self._applicant(self.st_invite)
        a._hb_advance_stage('hb_stage_invite', 'hb_stage_test_hidden', 'test')
        self.assertEqual(a.stage_id, self.st_invite)

    def test_08b_missing_target_stage_is_noop(self):
        """Bước đích đã bị xoá hẳn ⇒ cũng chỉ bỏ qua, không nổ lỗi."""
        a = self._applicant(self.st_invite)
        a._hb_advance_stage('hb_stage_invite', 'hb_stage_khong_ton_tai', 'test')
        self.assertEqual(a.stage_id, self.st_invite)

    def test_09_renaming_stage_does_not_break(self):
        """Bám xmlid nên đổi tên bước không ảnh hưởng."""
        a = self._applicant(self.st_sched)
        self.st_invite.name = 'Mời PV (tên mới)'
        a.write({'interview_date': '2026-08-24'})
        self.assertEqual(a.stage_id, self.st_invite)
