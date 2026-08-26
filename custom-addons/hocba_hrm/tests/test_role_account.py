"""Tài khoản vai trò trưởng phòng — không phải hồ sơ nhân sự.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Tài khoản tạo từ form "Thêm phòng ban" là tài khoản QUẢN LÝ (tài khoản thứ hai
của một người đã có hồ sơ nhân viên riêng). Nó phải biến mất khỏi Nhận việc,
danh sách Nhân viên và thống kê, nhưng VẪN giữ nguyên quyền duyệt phòng mình và
VẪN hiện ở màn Tài khoản để HR đổi mật khẩu / khoá.

DB test dùng chung nên mọi assert so theo bản ghi do test tự tạo, không so số
tuyệt đối.
"""
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _dept_create, _emp_scope_domain, _account_list)


@tagged('post_install', '-at_install')
class TestRoleAccount(TransactionCase):

    def setUp(self):
        super().setUp()
        gu = self.env.ref('base.group_user').id
        self.hrm = self.env['res.users'].create({
            'name': 'HRM Role', 'login': 'hrm_role_acc',
            'group_ids': [(6, 0, [gu,
                                  self.env.ref('hr.group_hr_manager').id])]})

    def _mgr_block(self, login='tp_role_1', name='TP Vai Tro'):
        return {'name': name, 'login': login,
                'password': 'Hocba@2026', 'password_confirm': 'Hocba@2026'}

    def _create_dept(self, name='Phong Vai Tro', login='tp_role_1'):
        """Tạo phòng ban kèm tài khoản vai trò, trả về (dept, emp)."""
        env = self.env(user=self.hrm)
        _dept_create(env, {'name': name, 'manager': self._mgr_block(login=login)})
        dept = env['hr.department'].sudo().search(
            [('name', '=', name)], limit=1)
        return dept, dept.manager_id

    # ---- Task 1: cờ trên model ----
    def test_create_khong_ghi_moc_nhan_viec(self):
        """Tài khoản vai trò không sinh mốc thăng tiến 'join'."""
        emp = self.env['hr.employee'].create({
            'name': 'Chi La Tai Khoan', 'x_is_role_account': True})
        self.assertTrue(emp.x_is_role_account)
        logs = self.env['hr.promotion.history'].sudo().search(
            [('employee_id', '=', emp.id)])
        self.assertFalse(
            logs, 'Tài khoản vai trò không được có mốc "Nhận việc".')

    def test_nv_thuong_van_ghi_moc_nhan_viec(self):
        """Không làm hỏng đường đi của nhân viên thật."""
        emp = self.env['hr.employee'].create({'name': 'NV That Su'})
        self.assertFalse(emp.x_is_role_account)
        logs = self.env['hr.promotion.history'].sudo().search(
            [('employee_id', '=', emp.id)])
        self.assertTrue(logs, 'NV thật vẫn phải có mốc "Nhận việc".')
