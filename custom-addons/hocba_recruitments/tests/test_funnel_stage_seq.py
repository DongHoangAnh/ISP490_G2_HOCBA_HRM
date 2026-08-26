"""Phễu "Theo dõi tuyển dụng" phải bám bước theo XMLID, không theo số cứng.

Hai mốc PV và Nhận việc không có trường riêng nên phải suy từ vị trí của bước
(`stage_id.sequence >= ...`). Trước đây mốc đó là hằng số 60 / 90 — đúng với bộ
bước seed, nhưng màn Cấu hình cho phép THÊM bước và KÉO-THẢ, mà
`action_reorder` ghi lại sequence 10/20/30… nên chèn một bước trước "Phỏng vấn"
là mọi bước sau đó dịch lên một nấc: "Hẹn & mời phỏng vấn" rơi đúng vào 60 và bị
đếm thành đã phỏng vấn. Sai âm thầm, không lỗi, không cảnh báo — người xem chỉ
thấy con số PV cao hơn thực tế.

Test dựng đúng trạng thái sau một lần chèn bước: invite 60 · interview 70 ·
result 80, rồi soi lại con số của phễu.
"""
import json

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestFunnelStageSeq(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dept = cls.env['hr.department'].create({'name': 'Phòng (test funnel seq)'})
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR (test funnel seq)',
            'login': 'test_funnelseq_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref(
                'hr_recruitment.group_hr_recruitment_user').id)],
        })
        cls.job = cls.env['hr.job'].create({
            'name': 'Vị trí (test funnel seq)', 'department_id': cls.dept.id})
        cls.req = cls.env['hb.recruitment.request'].create({
            'department_id': cls.dept.id, 'job_id': cls.job.id,
            'job_title': 'Vị trí (test funnel seq)', 'qty_expected': 2,
            'state': 'recruiting',
        })
        ref = cls.env.ref
        cls.st_invite = ref('hocba_recruitments.hb_stage_invite')
        cls.st_interview = ref('hocba_recruitments.hb_stage_interview')
        cls.st_result = ref('hocba_recruitments.hb_stage_result')

    def setUp(self):
        super().setUp()
        # Trạng thái sau khi admin chèn 1 bước ở đầu quy trình rồi kéo-thả:
        # action_reorder ghi lại 10/20/30… nên mọi bước phía sau dịch lên 1 nấc.
        self.st_invite.sequence = 60
        self.st_interview.sequence = 70
        self.st_result.sequence = 80

    def _applicant(self, stage, name):
        return self.env['hr.applicant'].create({
            'partner_name': name, 'job_id': self.job.id,
            'hb_request_id': self.req.id, 'stage_id': stage.id,
        })

    def _stats(self):
        self.authenticate('test_funnelseq_hr', PWD)
        rows = self.url_open('%s/jobs' % BASE).json()['requests']
        return next(r for r in rows if r['id'] == self.req.id)

    def _group_rows(self, group):
        self.authenticate('test_funnelseq_hr', PWD)
        body = self.url_open(
            '%s/request/%s/applicants?group=%s' % (BASE, self.req.id, group)).json()
        return [r['id'] for r in body['rows']]

    def test_01_ung_vien_chua_phong_van_khong_bi_dem_vao_pv(self):
        a = self._applicant(self.st_invite, 'UV mới được mời PV')
        self.assertEqual(self._stats()['pvCount'], 0,
                         'Bước "Hẹn & mời phỏng vấn" không phải đã phỏng vấn')
        self.assertNotIn(a.id, self._group_rows('pv'))

    def test_02_ung_vien_dang_phong_van_van_duoc_dem(self):
        a = self._applicant(self.st_interview, 'UV đang phỏng vấn')
        self.assertEqual(self._stats()['pvCount'], 1)
        self.assertIn(a.id, self._group_rows('pv'))

    def test_03_con_so_va_danh_sach_khong_lech_nhau(self):
        self._applicant(self.st_invite, 'UV mời PV')
        self._applicant(self.st_interview, 'UV đang PV')
        self._applicant(self.st_result, 'UV đã có kết quả')
        self.assertEqual(self._stats()['pvCount'], len(self._group_rows('pv')))
