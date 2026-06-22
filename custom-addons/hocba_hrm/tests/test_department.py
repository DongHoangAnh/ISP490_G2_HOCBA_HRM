from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.addons.hocba_hrm.controllers.main import _dept_payload, _dept_list


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

    # ---- _dept_list / _dept_payload (Task 2) ----
    def test_list_forbidden_for_plain(self):
        with self.assertRaises(AccessError):
            _dept_list(self._env(self.plain))

    def test_list_returns_departments_and_employees(self):
        out = _dept_list(self._env(self.hr))
        names = [d['name'] for d in out['departments']]
        self.assertIn('Phòng A', names)
        self.assertTrue(any(e['id'] == self.emp.id for e in out['employees']))

    def test_payload_employee_count(self):
        out = _dept_list(self._env(self.hr))
        row = next(d for d in out['departments'] if d['id'] == self.dept.id)
        self.assertEqual(row['employeeCount'], 1)
        self.assertTrue(row['active'])

    def test_list_excludes_archived_by_default(self):
        self.dept.active = False
        names = [d['name'] for d in _dept_list(self._env(self.hr))['departments']]
        self.assertNotIn('Phòng A', names)

    def test_list_includes_archived_when_requested(self):
        self.dept.active = False
        names = [d['name'] for d in
                 _dept_list(self._env(self.hr), archived=True)['departments']]
        self.assertIn('Phòng A', names)
