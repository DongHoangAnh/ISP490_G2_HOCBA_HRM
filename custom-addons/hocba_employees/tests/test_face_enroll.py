from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestFaceEnroll(TransactionCase):
    """Kiosk self-service: a regular (non-HR) employee must be able to read
    their own attendance info and enroll their face sample."""

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Regular Emp',
            'login': 'reg_face_enroll',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Regular Emp',
            'user_id': self.user.id,
        })

    def test_regular_employee_can_enroll_face(self):
        Emp = self.env['hr.employee'].with_user(self.user)
        Emp.enroll_self_face({'photo': 'ZmFrZQ==', 'descriptor': [0.1] * 128})
        self.employee.invalidate_recordset()
        self.assertTrue(self.employee.x_face_descriptor)
        self.assertTrue(self.employee.x_face_enrolled)

    def test_regular_employee_can_read_attendance_info(self):
        Emp = self.env['hr.employee'].with_user(self.user)
        info = Emp.get_self_attendance_info()
        self.assertEqual(info['employee_id'], self.employee.id)
        self.assertFalse(info['enrolled'])
