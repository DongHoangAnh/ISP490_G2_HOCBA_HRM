from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOffboardingModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Off Target',
            'identification_id': '012345678901',
        })

    def _make(self, **kw):
        vals = {
            'employee_id': self.emp.id,
            'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today(),
        }
        vals.update(kw)
        return self.env['hocba.offboarding'].create(vals)

    def test_create_generates_code_and_draft(self):
        rec = self._make()
        self.assertNotIn(rec.name, ('/', False))
        self.assertTrue(rec.name.startswith('OFF/'))
        self.assertEqual(rec.state, 'draft')
        self.assertEqual(rec.source, 'self')
