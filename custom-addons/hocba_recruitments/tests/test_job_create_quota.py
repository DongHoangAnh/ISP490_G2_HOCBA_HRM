"""Vị trí mới tạo từ SPA KHÔNG được mang sẵn chỉ tiêu tuyển.

Form "Thêm vị trí" ở Kho JD không còn ô "Số lượng cần tuyển" / "Số buổi/tuần"
(quyết định 2026-08-29): chỉ tiêu là của ĐỢT tuyển, đến từ phiếu yêu cầu được
duyệt (`action_approve` cộng `qty_expected` vào `hr.job.no_of_recruitment`).

Default của core `hr.job.no_of_recruitment` là 1, nên bỏ ô đi mà không chốt 0 ở
controller thì mỗi JD vừa tạo đã "còn thiếu 1 người" trong khi chưa có phiếu nào
— chỉ tiêu ma này khiến vị trí không bao giờ về 0 để tự Ngừng đăng tuyển.
"""
import json

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestJobCreateQuota(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dept = cls.env['hr.department'].create(
            {'name': 'Phòng (test job quota)'})
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR (test job quota)',
            'login': 'test_job_quota_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref(
                'hr_recruitment.group_hr_recruitment_user').id)],
        })

    def _create_job(self, payload):
        self.authenticate('test_job_quota_hr', PWD)
        res = self.url_open(
            '%s/jobs' % BASE, data=json.dumps(payload),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()

    def test_01_khong_gui_so_luong_thi_chi_tieu_bang_0(self):
        det = self._create_job({'name': 'Vị trí không gửi số lượng',
                                'depId': self.dept.id})
        self.assertEqual(det['expected'], 0)
        self.assertEqual(
            self.env['hr.job'].browse(det['id']).no_of_recruitment, 0)

    def test_02_gui_so_luong_rong_thi_chi_tieu_bang_0(self):
        """Form vẫn gửi khoá rỗng (state khởi tạo '') — cũng phải ra 0."""
        det = self._create_job({'name': 'Vị trí gửi số lượng rỗng',
                                'depId': self.dept.id, 'expected': ''})
        self.assertEqual(det['expected'], 0)

    def test_03_gui_so_luong_tuong_minh_van_duoc_ton_trong(self):
        """API vẫn nhận số nếu nơi khác (form Sửa vị trí) gửi lên."""
        det = self._create_job({'name': 'Vị trí gửi số lượng 3',
                                'depId': self.dept.id, 'expected': 3})
        self.assertEqual(det['expected'], 3)
