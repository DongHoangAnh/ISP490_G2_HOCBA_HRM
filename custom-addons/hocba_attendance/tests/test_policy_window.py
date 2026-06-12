from datetime import datetime

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPolicyWindow(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].create({
            'name': 'Test',
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
        })

    def test_is_workday_weekday(self):
        # 2026-06-11 is a Thursday
        self.assertTrue(self.policy.is_workday(datetime(2026, 6, 11, 8, 0)))

    def test_is_workday_weekend(self):
        # 2026-06-13 is a Saturday (workday_sat default False)
        self.assertFalse(self.policy.is_workday(datetime(2026, 6, 13, 8, 0)))

    def test_checkin_window_inside(self):
        # Thursday 08:30 -> inside morning window
        self.assertTrue(
            self.policy.is_within_window(datetime(2026, 6, 11, 8, 30), 'in'))

    def test_checkin_window_too_late(self):
        # Thursday 10:00 -> after morning_end 09:30
        self.assertFalse(
            self.policy.is_within_window(datetime(2026, 6, 11, 10, 0), 'in'))

    def test_checkout_window_inside(self):
        # Thursday 16:30 -> inside evening window
        self.assertTrue(
            self.policy.is_within_window(datetime(2026, 6, 11, 16, 30), 'out'))

    def test_window_false_on_weekend_even_if_time_ok(self):
        # Saturday 08:30 -> right time but not a workday
        self.assertFalse(
            self.policy.is_within_window(datetime(2026, 6, 13, 8, 30), 'in'))
