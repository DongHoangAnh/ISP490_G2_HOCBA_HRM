from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPromotionCriteria(TransactionCase):
    def test_seed_criteria_exist_with_weight(self):
        crits = self.env['hr.promotion.criteria'].search([('active', '=', True)])
        self.assertTrue(len(crits) >= 4, 'Phải seed >= 4 tiêu chí mặc định')
        self.assertTrue(all(c.weight > 0 for c in crits), 'Mọi tiêu chí có trọng số > 0')
        self.assertTrue(all(c.max_score > 0 for c in crits))

    def test_duplicate_code_rejected(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        Crit = self.env['hr.promotion.criteria']
        Crit.create({'name': 'Dup A', 'code': 'dup_test', 'weight': 10})
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Crit.create({'name': 'Dup B', 'code': 'dup_test', 'weight': 10})
                self.env.flush_all()
