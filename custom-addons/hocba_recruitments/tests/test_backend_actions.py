"""Action menu backend Odoo phải bám XMLID bước, không bám TÊN bước.

Màn Cấu hình tuyển dụng cho admin đổi tên bước (và đó là thao tác bình thường,
không phải nghịch dại). Action nào lọc theo `stage_id.name = 'Phỏng vấn'` thì
đúng lúc đổi tên là menu rỗng trơn — không lỗi, không cảnh báo, chỉ đơn giản
không còn dòng nào. Cùng một bài học đã áp cho tự-động-chuyển-bước
(`_hb_advance_stage` bám xmlid), nay áp nốt cho menu backend.
"""
from ast import literal_eval

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBackendActionDomains(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.st_interview = ref('hocba_recruitments.hb_stage_interview')
        cls.st_offer = ref('hocba_recruitments.hb_stage_offer')
        cls.st_onboarding = ref('hocba_recruitments.hb_stage_onboarding')
        cls.job = cls.env['hr.job'].create({'name': 'Vị trí Test Action'})

    def _applicant(self, stage, name):
        return self.env['hr.applicant'].create({
            'partner_name': name, 'job_id': self.job.id, 'stage_id': stage.id,
        })

    def _match(self, action_xmlid):
        """Ứng viên mà action đó hiển thị."""
        action = self.env.ref(action_xmlid)
        return self.env['hr.applicant'].search(literal_eval(action.domain))

    def test_01_interview_action_survives_stage_rename(self):
        a = self._applicant(self.st_interview, 'UV đang phỏng vấn')
        self.st_interview.write({'name': 'PV vòng 1 (admin đổi tên)'})
        self.assertIn(a, self._match('hocba_recruitments.hb_action_interview_list'))

    def test_02_offer_action_survives_stage_rename(self):
        a_offer = self._applicant(self.st_offer, 'UV nhận offer')
        a_onboard = self._applicant(self.st_onboarding, 'UV đang onboard')
        self.st_offer.write({'name': 'Thư mời (admin đổi tên)'})
        self.st_onboarding.write({'name': 'Nhận việc (admin đổi tên)'})
        found = self._match('hocba_recruitments.hb_action_offer_hire')
        self.assertIn(a_offer, found)
        self.assertIn(a_onboard, found)

    def test_03_offer_action_khong_bat_buoc_khac(self):
        """Đổi tên không được làm action bắt nhầm ứng viên bước khác."""
        a_interview = self._applicant(self.st_interview, 'UV vẫn đang PV')
        self.assertNotIn(a_interview,
                         self._match('hocba_recruitments.hb_action_offer_hire'))
