from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestShiftDeadline(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV OT', 'x_employment_status': 'ctv'})
        self.Shift = self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh')

    def _shift(self, **vals):
        base = {'employee_id': self.emp.id, 'shift_type': 'ot',
                'start': '2026-06-15 02:00:00', 'end': '2026-06-15 04:00:00'}
        base.update(vals)
        return self.Shift.create(base)

    def test_deadline_is_start_minus_one_minute(self):
        s = self._shift(start='2026-06-15 03:00:00')
        self.assertEqual(s.deadline, fields.Datetime.from_string('2026-06-15 02:59:00'))

    def test_auto_reject_expired_rejects_past_pending(self):
        past = fields.Datetime.now() - timedelta(hours=1)
        s = self._shift(start=past, end=past + timedelta(hours=2), state='pending')
        self.env['hocba.work_shift']._auto_reject_expired()
        self.assertEqual(s.state, 'rejected')
        self.assertTrue(s.decision_date)

    def test_auto_reject_leaves_future_pending(self):
        future = fields.Datetime.now() + timedelta(hours=1)
        s = self._shift(start=future, end=future + timedelta(hours=2), state='pending')
        self.env['hocba.work_shift']._auto_reject_expired()
        self.assertEqual(s.state, 'pending')

    def test_auto_reject_ignores_approved(self):
        past = fields.Datetime.now() - timedelta(hours=1)
        s = self._shift(start=past, end=past + timedelta(hours=2), state='approved')
        self.env['hocba.work_shift']._auto_reject_expired()
        self.assertEqual(s.state, 'approved')

    def test_assert_actionable_raises_after_deadline(self):
        past = fields.Datetime.now() - timedelta(hours=1)
        s = self._shift(start=past, end=past + timedelta(hours=2))
        with self.assertRaises(UserError):
            s._assert_actionable()

    def test_assert_actionable_passes_before_deadline(self):
        future = fields.Datetime.now() + timedelta(hours=1)
        s = self._shift(start=future, end=future + timedelta(hours=2))
        s._assert_actionable()  # should not raise
