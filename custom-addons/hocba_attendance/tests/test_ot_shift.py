from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOtShift(TransactionCase):

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'CTV OT', 'x_employment_status': 'ctv'})

    def _shift(self, **vals):
        base = {
            'employee_id': self.emp.id,
            'start': '2026-06-15 02:00:00', 'end': '2026-06-15 04:00:00',
            'shift_type': 'ot',
        }
        base.update(vals)
        return self.env['hocba.work_shift'].with_context(
            tz='Asia/Ho_Chi_Minh').create(base)

    def test_default_level_is_100(self):
        s = self._shift()
        self.assertEqual(s.ot_level, '100')
        self.assertEqual(s.rate, 1.0)

    def test_level_maps_to_rate(self):
        self.assertEqual(self._shift(ot_level='150').rate, 1.5)
        self.assertEqual(self._shift(ot_level='300',
                         start='2026-06-16 02:00:00',
                         end='2026-06-16 04:00:00').rate, 3.0)

    def test_changing_level_recomputes_rate(self):
        s = self._shift(ot_level='150')
        self.assertEqual(s.rate, 1.5)
        s.ot_level = '300'
        self.assertEqual(s.rate, 3.0)
