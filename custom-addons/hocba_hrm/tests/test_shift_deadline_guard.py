from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _shift_decide


@tagged('post_install', '-at_install')
class TestShiftDeadlineGuard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV A', 'x_employment_status': 'ctv'})
        self.mgr_user = self.env['res.users'].create({
            'name': 'Mgr', 'login': 'mgr_guard',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_manager').id])]})

    def _shift(self, start, state='pending'):
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create({
                'employee_id': self.emp.id, 'shift_type': 'ot', 'state': state,
                'start': start, 'end': start + timedelta(hours=2)})

    def test_decide_blocked_after_deadline(self):
        env = self.env(user=self.mgr_user)
        s = self._shift(fields.Datetime.now() - timedelta(hours=1))
        with self.assertRaises(UserError):
            _shift_decide(env, s.id, True, {})

    def test_decide_approved_shift_can_be_rejected_before_deadline(self):
        env = self.env(user=self.mgr_user)
        s = self._shift(fields.Datetime.now() + timedelta(hours=2), state='approved')
        _shift_decide(env, s.id, False, {'reviewNote': 'đổi ý'})
        self.assertEqual(s.state, 'rejected')
        self.assertEqual(s.review_note, 'đổi ý')

    def test_decide_rejected_shift_is_already_decided(self):
        env = self.env(user=self.mgr_user)
        s = self._shift(fields.Datetime.now() + timedelta(hours=2), state='rejected')
        with self.assertRaises(UserError):
            _shift_decide(env, s.id, True, {})
