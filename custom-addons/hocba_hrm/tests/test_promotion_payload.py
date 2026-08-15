from odoo import http
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM


class _FakeRequest:
    """Đủ để _employee_detail đọc request.env.user ngoài context HTTP."""

    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestPromotionPayloadTitle(TransactionCase):
    """Tiêu đề mốc trong tab Thăng tiến của hồ sơ (drawer + "Hồ sơ của tôi").

    Trang Lộ trình sự nghiệp đã bỏ tiêu đề "— → —" cho snapshot nhận việc
    (spec 2026-08-09 §8.3), nhưng tab Thăng tiến vẫn dựng tiêu đề từ
    fromJob/toJob nên hồ sơ nào cũng mở ra bằng một dòng "— → —".
    """

    _LABELS = {'status': {}, 'work_form': {}, 'position': {},
               'asset_condition': {}, 'relationship': {}}

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()
        http._request_stack.push(_FakeRequest(self.env))
        self.addCleanup(http._request_stack.pop)

    def _detail(self, emp):
        return self.ctrl._employee_detail(
            emp, self._LABELS, is_hr=True, is_mgr=True)

    def test_join_snapshot_titled_not_dashes(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV Moi Vao', 'x_employee_code': 'EMP-PROMO-1'})
        row = self._detail(emp)['promotions'][0]
        self.assertEqual(row['changeType'], 'join')
        self.assertEqual(row['title'], 'Vào làm việc')

    def test_real_promotion_keeps_arrow_title(self):
        job_a = self.env['hr.job'].create({'name': 'Chuyên viên PP'})
        job_b = self.env['hr.job'].create({'name': 'Trưởng nhóm PP'})
        emp = self.env['hr.employee'].create({
            'name': 'NV Thang Chuc', 'x_employee_code': 'EMP-PROMO-2',
            'job_id': job_a.id})
        self.env['hr.promotion.history'].create({
            'employee_id': emp.id, 'x_change_type': 'promotion',
            'from_job_id': job_a.id, 'to_job_id': job_b.id,
            'date_effective': '2026-05-01'})
        row = next(r for r in self._detail(emp)['promotions']
                   if r['changeType'] == 'promotion')
        self.assertEqual(row['title'], 'Chuyên viên PP → Trưởng nhóm PP')
