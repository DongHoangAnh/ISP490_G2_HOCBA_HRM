from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestWorkCreditPolicy(TransactionCase):

    def test_policy_credit_defaults(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        self.assertEqual(policy.late_cutoff, 9.5)
        self.assertEqual(policy.morning_credit_cutoff, 10.0)
        self.assertEqual(policy.std_work_hours, 8.0)
        self.assertEqual(policy.afternoon_margin_hours, 2.0)
        self.assertEqual(policy.violation_free_days, 2)
