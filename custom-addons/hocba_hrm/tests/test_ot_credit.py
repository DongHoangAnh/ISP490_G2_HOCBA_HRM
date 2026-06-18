from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _att_me_history


@tagged('post_install', '-at_install')
class TestOtCredit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV OT', 'x_employment_status': 'ctv'})
        self.user = self.env['res.users'].create({
            'name': 'CTV OT User', 'login': 'ctv_ot_user'})
        self.user.tz = 'Asia/Ho_Chi_Minh'
        self.emp.user_id = self.user
        self.WS = self.env['hocba.work_shift'].with_context(tz='Asia/Ho_Chi_Minh')

    def _shift(self, start, end, rate, state='approved'):
        return self.WS.sudo().create({
            'employee_id': self.emp.id, 'start': start, 'end': end,
            'shift_type': 'ot', 'rate': rate, 'state': state})

    def test_ot_summary(self):
        self._shift('2026-06-15 02:00:00', '2026-06-15 04:00:00', 1.5)  # 2h ×1.5
        self._shift('2026-06-16 02:00:00', '2026-06-16 05:00:00', 2.0)  # 3h ×2.0
        s = _att_me_history(self.env(user=self.user), '2026-06')['summary']
        self.assertEqual(s['otShiftCount'], 2)
        self.assertEqual(s['otHours'], 5.0)
        self.assertEqual(s['otCreditHours'], 9.0)   # 2*1.5 + 3*2.0

    def test_ot_other_month_excluded(self):
        self._shift('2026-07-15 02:00:00', '2026-07-15 04:00:00', 1.5)
        s = _att_me_history(self.env(user=self.user), '2026-06')['summary']
        self.assertEqual(s['otShiftCount'], 0)
        self.assertEqual(s['otHours'], 0)

    def test_ot_pending_excluded(self):
        self._shift('2026-06-15 02:00:00', '2026-06-15 04:00:00', 1.5, state='pending')
        s = _att_me_history(self.env(user=self.user), '2026-06')['summary']
        self.assertEqual(s['otShiftCount'], 0)
