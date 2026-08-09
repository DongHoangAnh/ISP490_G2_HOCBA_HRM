"""Tự chuyển bước từ hành động trên tab Offer & Nhận việc.

- Gửi "Thư mời nhận việc" : Phỏng vấn / Kết quả PV → Gửi Offer
- Gửi "Thư mời phỏng vấn"  : Hẹn & mời phỏng vấn   → Phỏng vấn
- Bấm nút "Onboard"        : Kết quả PV / Gửi Offer → Onboarding

Test ở tầng HTTP vì luật nằm trong controller (MAIL_STAGE_RULES + endpoint
create-employee), không phải trong model — gọi thẳng model sẽ xanh giả.

SPA gửi mail bằng cách mở Gmail rồi xác nhận qua /mail/log-sent, KHÔNG qua
/send (SMTP). Vì vậy luật phải chạy được ở đường log-sent; đó là điểm hay bị vá
sót nên khoá bằng test.
"""
import json

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestMailStage(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.st_invite = ref('hocba_recruitments.hb_stage_invite')
        cls.st_interview = ref('hocba_recruitments.hb_stage_interview')
        cls.st_result = ref('hocba_recruitments.hb_stage_result')
        cls.st_offer = ref('hocba_recruitments.hb_stage_offer')
        cls.st_onboarding = ref('hocba_recruitments.hb_stage_onboarding')
        cls.st_hired = ref('hocba_recruitments.hb_stage_hired')

        cls.tmpl_offer = ref('hocba_recruitments.email_template_job_offer')
        cls.tmpl_invite = ref('hocba_recruitments.email_template_interview_invite')
        cls.tmpl_welcome = ref('hocba_recruitments.email_template_welcome')

        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR tuyển dụng (test mail stage)',
            'login': 'test_mstage_hr', 'password': PWD,
            'group_ids': [(4, ref('hr_recruitment.group_hr_recruitment_user').id)],
        })
        cls.job = cls.env['hr.job'].create(
            {'name': 'Vị trí Test MailStage', 'no_of_recruitment': 5})

    def setUp(self):
        super().setUp()
        self.authenticate('test_mstage_hr', PWD)

    # ── helper ───────────────────────────────────────────────────────────────

    def _applicant(self, stage, name='UV mail stage'):
        return self.env['hr.applicant'].create({
            'partner_name': name, 'email_from': 'uv_mstage@example.com',
            'job_id': self.job.id, 'stage_id': stage.id,
        })

    def _log_sent(self, applicant, template=None):
        item = {'applicantId': applicant.id, 'subject': 'Thư test'}
        if template:
            item['templateId'] = template.id
        return self.url_open(
            '%s/mail/log-sent' % BASE, data=json.dumps({'logs': [item]}),
            headers={'Content-Type': 'application/json'})

    def _onboard(self, applicant):
        return self.url_open(
            '%s/applicant/%s/create-employee' % (BASE, applicant.id),
            data='{}', headers={'Content-Type': 'application/json'})

    # ── Thư mời nhận việc → Gửi Offer ────────────────────────────────────────

    def test_01_job_offer_mail_moves_result_to_offer(self):
        a = self._applicant(self.st_result)
        res = self._log_sent(a, self.tmpl_offer)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['logged'], 1)
        self.assertEqual(a.stage_id, self.st_offer)

    def test_02_job_offer_mail_moves_interview_to_offer(self):
        """Gửi offer thẳng từ bước Phỏng vấn (HR chốt ngay trong buổi PV)."""
        a = self._applicant(self.st_interview)
        self._log_sent(a, self.tmpl_offer)
        self.assertEqual(a.stage_id, self.st_offer)

    def test_03_job_offer_mail_does_not_pull_back(self):
        a = self._applicant(self.st_onboarding)
        self._log_sent(a, self.tmpl_offer)
        self.assertEqual(a.stage_id, self.st_onboarding)

    def test_04_job_offer_mail_posts_chatter_note(self):
        a = self._applicant(self.st_result)
        before = len(a.message_ids)
        self._log_sent(a, self.tmpl_offer)
        self.assertGreater(len(a.message_ids), before)

    # ── Thư mời phỏng vấn qua đường Gmail ────────────────────────────────────

    def test_05_invite_mail_moves_invite_to_interview(self):
        """Luật cũ trước đây chỉ chạy ở /send (SMTP); SPA dùng Gmail nên phải
        chạy được cả ở log-sent."""
        a = self._applicant(self.st_invite)
        self._log_sent(a, self.tmpl_invite)
        self.assertEqual(a.stage_id, self.st_interview)

    # ── Mẫu khác / thiếu templateId ⇒ không đụng bước ────────────────────────

    def test_06_other_template_does_not_move(self):
        a = self._applicant(self.st_result)
        self._log_sent(a, self.tmpl_welcome)
        self.assertEqual(a.stage_id, self.st_result)

    def test_07_missing_template_id_only_logs(self):
        """Client cũ không gửi templateId ⇒ vẫn ghi lịch sử, không đổi bước."""
        a = self._applicant(self.st_result)
        res = self._log_sent(a)
        self.assertEqual(res.json()['logged'], 1)
        self.assertEqual(a.stage_id, self.st_result)

    def test_08_deleted_template_id_is_noop(self):
        """Mẫu đã bị xoá ⇒ bỏ qua im lặng, không nổ 500 giữa lúc ghi lịch sử."""
        a = self._applicant(self.st_result)
        ghost = self.env['mail.template'].create(
            {'name': 'Mẫu tạm sẽ xoá', 'model_id': self.env.ref(
                'hr_recruitment.model_hr_applicant').id})
        ghost_id = ghost.id
        ghost.unlink()
        res = self.url_open(
            '%s/mail/log-sent' % BASE,
            data=json.dumps({'logs': [{'applicantId': a.id, 'subject': 'x',
                                       'templateId': ghost_id}]}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(a.stage_id, self.st_result)

    # ── Nút Onboard → Onboarding ─────────────────────────────────────────────

    def test_10_onboard_moves_offer_to_onboarding(self):
        a = self._applicant(self.st_offer, 'UV onboard tu offer')
        res = self._onboard(a)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['created'])
        self.assertEqual(a.stage_id, self.st_onboarding)

    def test_11_onboard_moves_result_to_onboarding(self):
        """Nhận việc luôn không qua khâu gửi offer trên hệ thống."""
        a = self._applicant(self.st_result, 'UV onboard tu ket qua')
        self._onboard(a)
        self.assertEqual(a.stage_id, self.st_onboarding)

    def test_12_onboard_does_not_pull_back_from_hired(self):
        a = self._applicant(self.st_hired, 'UV onboard da ban giao')
        self._onboard(a)
        self.assertEqual(a.stage_id, self.st_hired)

    def test_13_onboard_twice_keeps_stage(self):
        """Lần 2 chỉ trả về hồ sơ cũ ⇒ không được kéo ngược bước HR đã đẩy tiếp."""
        a = self._applicant(self.st_offer, 'UV onboard hai lan')
        self._onboard(a)
        a.write({'stage_id': self.st_hired.id})
        res = self._onboard(a)
        self.assertFalse(res.json()['created'])
        self.assertEqual(a.stage_id, self.st_hired)

    def test_14_onboard_posts_chatter_note(self):
        a = self._applicant(self.st_offer, 'UV onboard chatter')
        before = len(a.message_ids)
        self._onboard(a)
        self.assertGreater(len(a.message_ids), before)
