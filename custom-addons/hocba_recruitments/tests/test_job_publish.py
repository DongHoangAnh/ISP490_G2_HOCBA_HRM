"""Đăng tuyển / Ngừng đăng phải chạy trên DB KHÔNG cài website_hr_recruitment.

`is_published` là field của `website_hr_recruitment`, không phải của
`hr_recruitment`. Manifest module này không depends nó (cố ý — không bắt mọi cài
đặt gánh cả bộ website chỉ vì một cờ boolean), nên controller tuyệt đối không
được ghi thẳng field đó: DB thiếu module → ORM ném ValueError → controller không
bắt (chỉ bắt AccessError/ValidationError/UserError) → HTTP 500 trần, nút Đăng
tuyển chết. Ghi `x_published` thì `hr_job.write()` tự soi gương sang
`is_published` KHI field tồn tại.

Chiều ĐỌC cũng phải thống nhất: trước đây `_job_row` lùi về `x_published` còn
tab Theo dõi và popup JD lùi về `False`, nên trên DB không có website thì vị trí
nào cũng hiện "chưa đăng" và nút Chép link không bao giờ xuất hiện.
"""
from odoo.tests import TransactionCase, tagged

from odoo.addons.hocba_recruitments.controllers.main import HocBaTuyenDung


@tagged('post_install', '-at_install')
class TestJobPublishVals(TransactionCase):
    """_job_vals() chỉ đọc payload nên gọi thẳng được, không cần dựng HTTP."""

    def test_01_publish_true_khong_ghi_is_published(self):
        vals = HocBaTuyenDung()._job_vals({'published': True})
        self.assertNotIn(
            'is_published', vals,
            'Controller không được ghi field của website_hr_recruitment')
        self.assertTrue(vals['x_published'])
        self.assertEqual(vals['recruitment_status'], 'recruiting')

    def test_02_publish_false_khong_ghi_is_published(self):
        vals = HocBaTuyenDung()._job_vals({'published': False})
        self.assertNotIn('is_published', vals)
        self.assertFalse(vals['x_published'])
        self.assertEqual(vals['recruitment_status'], 'stopped')

    def test_03_khong_gui_published_thi_khong_dung_toi_hai_co(self):
        vals = HocBaTuyenDung()._job_vals({'name': 'Trợ giảng'})
        self.assertNotIn('is_published', vals)
        self.assertNotIn('x_published', vals)
        self.assertNotIn('recruitment_status', vals)


@tagged('post_install', '-at_install')
class TestJobPublishRead(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaTuyenDung()
        self.job = self.env['hr.job'].create({'name': 'Trợ giảng (test publish)'})

    def test_10_job_rong_tra_false(self):
        self.assertFalse(self.ctrl._job_published(self.env['hr.job']))

    def test_11_dang_tuyen_tra_true(self):
        self.job.write({'x_published': True})
        self.assertTrue(self.ctrl._job_published(self.job))

    def test_12_ngung_dang_tra_false(self):
        self.job.write({'x_published': True})
        self.job.write({'x_published': False})
        self.assertFalse(self.ctrl._job_published(self.job))
