from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPromotionCriteria(TransactionCase):
    def test_seed_criteria_exist_with_weight(self):
        crits = self.env['hr.promotion.criteria'].search([('active', '=', True)])
        self.assertTrue(len(crits) >= 4, 'Phải seed >= 4 tiêu chí mặc định')
        self.assertTrue(all(c.weight > 0 for c in crits), 'Mọi tiêu chí có trọng số > 0')
        self.assertTrue(all(c.max_score > 0 for c in crits))
