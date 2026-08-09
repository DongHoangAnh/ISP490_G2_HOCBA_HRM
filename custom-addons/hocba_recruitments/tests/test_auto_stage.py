"""Tự chuyển bước theo hành động của HR (khâu phỏng vấn).

- Đặt Ngày hẹn PV      : Lên lịch phỏng vấn → Hẹn & mời phỏng vấn
- Gửi thư mời PV       : Hẹn & mời phỏng vấn → Phỏng vấn (test ở tầng model)
- Xếp slot phỏng vấn   : Hẹn & mời phỏng vấn → Phỏng vấn
- Qua giờ PV (CRON-002): Phỏng vấn → Kết quả phỏng vấn
- Kết quả PV = Pass    : Phỏng vấn / Kết quả PV → Gửi Offer (Fail đứng yên)

Bám xmlid bước, không bám tên — admin đổi tên bước trên màn Cấu hình là chuyện
bình thường.
"""
from datetime import timedelta

from odoo import fields
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

    # ── Xếp ứng viên vào slot phỏng vấn ──────────────────────────────────────

    def _slot(self, hours_from_now=24, applicants=None):
        """Slot dài 1 tiếng, mốc tính từ bây giờ (âm = slot đã qua)."""
        start = fields.Datetime.now() + timedelta(hours=hours_from_now)
        return self.env['hb.interview.slot'].create({
            'start_datetime': start,
            'stop_datetime': start + timedelta(hours=1),
            'user_id': self.env.user.id,
            'applicant_ids': [(6, 0, applicants.ids)] if applicants else False,
        })

    def test_20_booking_moves_invite_to_interview(self):
        a = self._applicant(self.st_invite)
        self._slot().write({'applicant_ids': [(4, a.id)]})
        self.assertEqual(a.stage_id, self.st_interview)

    def test_21_booking_at_create_also_moves(self):
        """Slot tạo sẵn kèm ứng viên (import lịch tuần) cũng phải đẩy bước."""
        a = self._applicant(self.st_invite)
        self._slot(applicants=a)
        self.assertEqual(a.stage_id, self.st_interview)

    def test_22_booking_from_schedule_stage_stays(self):
        """Còn ở "Lên lịch phỏng vấn" thì xếp slot KHÔNG nhảy cóc vào Phỏng vấn
        — khâu gửi thư mời vẫn phải chạy (controller ghi interview_date sau đó
        mới đẩy sang "Hẹn & mời phỏng vấn")."""
        a = self._applicant(self.st_sched)
        self._slot().write({'applicant_ids': [(4, a.id)]})
        self.assertEqual(a.stage_id, self.st_sched)

    def test_23_booking_does_not_pull_back(self):
        a = self._applicant(self.st_result)
        self._slot().write({'applicant_ids': [(4, a.id)]})
        self.assertEqual(a.stage_id, self.st_result)

    def test_24_unbooking_does_not_move(self):
        a = self._applicant(self.st_invite)
        slot = self._slot()
        slot.write({'applicant_ids': [(4, a.id)]})
        slot.write({'applicant_ids': [(3, a.id)]})
        self.assertEqual(a.stage_id, self.st_interview,
                         'Gỡ khỏi slot không kéo ngược bước đã đi')

    def test_25_editing_slot_time_does_not_move_others(self):
        """Sửa giờ slot không được đụng bước của ứng viên đang ngồi trong slot."""
        a = self._applicant(self.st_invite)
        slot = self._slot(applicants=a)
        a.write({'stage_id': self.st_sched.id})     # HR kéo tay về bước trước
        slot.write({'notes': 'đổi ghi chú'})
        self.assertEqual(a.stage_id, self.st_sched)

    def test_26_booking_posts_chatter_note(self):
        a = self._applicant(self.st_invite)
        before = len(a.message_ids)
        self._slot().write({'applicant_ids': [(4, a.id)]})
        self.assertGreater(len(a.message_ids), before)

    # ── CRON-REC-002: qua giờ phỏng vấn ──────────────────────────────────────

    def _run_cron(self):
        return self.env['hb.interview.slot']._cron_advance_past_interviews()

    def test_30_past_slot_moves_interview_to_result(self):
        a = self._applicant(self.st_interview)
        self._slot(hours_from_now=-3, applicants=a)
        self.assertEqual(self._run_cron(), 1)
        self.assertEqual(a.stage_id, self.st_result)

    def test_31_future_slot_untouched(self):
        a = self._applicant(self.st_interview)
        self._slot(hours_from_now=5, applicants=a)
        self._run_cron()
        self.assertEqual(a.stage_id, self.st_interview,
                         'Chưa tới giờ PV thì không được đẩy bước')

    def test_32_slot_still_running_untouched(self):
        """Slot bắt đầu 30 phút trước, chưa kết thúc ⇒ vẫn đang phỏng vấn."""
        a = self._applicant(self.st_interview)
        self._slot(hours_from_now=-0.5, applicants=a)
        self._run_cron()
        self.assertEqual(a.stage_id, self.st_interview)

    def test_33_applicant_not_in_interview_stage_untouched(self):
        """Ứng viên còn ở "Lên lịch phỏng vấn" (xếp slot không đẩy bước này) thì
        qua giờ slot cũng không bị cron kéo sang Kết quả — chỉ bước Phỏng vấn mới
        là đầu vào hợp lệ của cron."""
        a = self._applicant(self.st_sched)
        self._slot(hours_from_now=-3, applicants=a)
        self.assertEqual(a.stage_id, self.st_sched)
        self._run_cron()
        self.assertEqual(a.stage_id, self.st_sched,
                         'Chỉ ứng viên đang ở bước Phỏng vấn mới bị đẩy')

    def test_34_already_passed_to_offer_not_pulled_back(self):
        a = self._applicant(self.st_interview)
        self._slot(hours_from_now=-3, applicants=a)
        a.write({'interview_result': 'pass'})       # → Gửi Offer
        self.assertEqual(a.stage_id, self.st_offer)
        self._run_cron()
        self.assertEqual(a.stage_id, self.st_offer)

    def test_35_cron_is_idempotent(self):
        a = self._applicant(self.st_interview)
        self._slot(hours_from_now=-3, applicants=a)
        self._run_cron()
        self.assertEqual(self._run_cron(), 0, 'Lượt chạy sau không đụng ai nữa')
        self.assertEqual(a.stage_id, self.st_result)

    def test_36_absent_applicant_still_moves_to_result(self):
        """Vắng mặt vẫn phải vào bước Kết quả để HR ghi nhận, không kẹt lại."""
        a = self._applicant(self.st_interview)
        a.write({'attendance_status': 'absent'})
        self._slot(hours_from_now=-3, applicants=a)
        self._run_cron()
        self.assertEqual(a.stage_id, self.st_result)

    def test_37_cron_then_result_pass_goes_to_offer(self):
        """Chuỗi đầy đủ: xếp slot → qua giờ → chấm Pass → Gửi Offer."""
        a = self._applicant(self.st_invite)
        self._slot(hours_from_now=-3, applicants=a)
        self.assertEqual(a.stage_id, self.st_interview)
        self._run_cron()
        self.assertEqual(a.stage_id, self.st_result)
        a.write({'interview_result': 'pass'})
        self.assertEqual(a.stage_id, self.st_offer)

    def test_38_cron_then_result_fail_stays(self):
        a = self._applicant(self.st_invite)
        self._slot(hours_from_now=-3, applicants=a)
        self._run_cron()
        a.write({'interview_result': 'fail'})
        self.assertEqual(a.stage_id, self.st_result,
                         'Fail thì đứng nguyên ở Kết quả phỏng vấn, HR tự quyết')

    def test_40_cron_record_wired_correctly(self):
        """Bản ghi CRON-REC-002 phải tồn tại và gọi đúng model/method.

        Sai `model_id` hay gõ nhầm tên method thì XML vẫn load êm, cron chỉ nổ
        lúc chạy nền lúc 30 phút sau — không ai thấy. Chốt bằng test.
        """
        cron = self.env.ref(
            'hocba_recruitments.cron_recruitment_interview_passed',
            raise_if_not_found=False)
        self.assertTrue(cron, 'Thiếu bản ghi cron trong ir_cron_data.xml')
        self.assertEqual(cron.model_id.model, 'hb.interview.slot')
        self.assertEqual(cron.state, 'code')
        self.assertIn('_cron_advance_past_interviews', cron.code)
        self.assertTrue(cron.active)
        self.assertTrue(hasattr(self.env[cron.model_id.model],
                                '_cron_advance_past_interviews'))

    def test_39_cron_posts_chatter_note(self):
        a = self._applicant(self.st_interview)
        self._slot(hours_from_now=-3, applicants=a)
        before = len(a.message_ids)
        self._run_cron()
        self.assertGreater(len(a.message_ids), before)
