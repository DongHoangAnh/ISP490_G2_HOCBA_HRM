from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError


@tagged('post_install', '-at_install')
class TestDepartment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.hr = self.env['res.users'].create({
            'name': 'HR', 'login': 'hr_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain', 'login': 'plain_dept',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng A'})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV A', 'department_id': self.dept.id})

    def _env(self, user):
        return self.env(user=user)

    # ---- Ràng buộc xóa (Task 1) ----
    def test_unlink_blocked_when_has_members(self):
        with self.assertRaises(UserError):
            self.dept.unlink()

    def test_unlink_blocked_when_has_children(self):
        parent = self.env['hr.department'].create({'name': 'Cha'})
        self.env['hr.department'].create({'name': 'Con', 'parent_id': parent.id})
        with self.assertRaises(UserError):
            parent.unlink()

    def test_unlink_ok_when_empty(self):
        empty = self.env['hr.department'].create({'name': 'Trống'})
        empty.unlink()
        self.assertFalse(empty.exists())
