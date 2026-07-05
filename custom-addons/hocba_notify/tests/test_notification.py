from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestNotification(TransactionCase):
    def test_module_loaded(self):
        self.assertIn('hb.notification', self.env)
