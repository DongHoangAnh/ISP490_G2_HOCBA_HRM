"""Tài khoản vai trò trưởng phòng — không phải hồ sơ nhân sự.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Tài khoản tạo từ form "Thêm phòng ban" là tài khoản QUẢN LÝ (tài khoản thứ hai
của một người đã có hồ sơ nhân viên riêng). Nó phải biến mất khỏi Nhận việc,
danh sách Nhân viên và thống kê, nhưng VẪN giữ nguyên quyền duyệt phòng mình và
VẪN hiện ở màn Tài khoản để HR đổi mật khẩu / khoá.

DB test dùng chung nên mọi assert so theo bản ghi do test tự tạo, không so số
tuyệt đối.
"""
from odoo import fields
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

    # ---- Task 1 (code review): chặn onboarding trong _hocba_maybe_assign_onboarding ----
    def _ensure_matching_onboarding_template(self, position_type='staff',
                                              work_form='offline'):
        """Bảo đảm có ít nhất 1 template khớp (position_type, work_form).

        DB test dùng chung nên có thể đã có sẵn (vd onb_template_office từ
        data seed) — chỉ tạo thêm khi thực sự chưa có gì khớp, tránh vọc
        thêm dữ liệu ngoài phạm vi cần cho test này."""
        Template = self.env['hb.onboarding.template'].sudo()
        probe = self.env['hr.employee'].new({
            'x_position_type': position_type, 'x_work_form': work_form})
        if Template._match_for_employee(probe):
            return
        Template.create({
            'name': 'Test tpl %s/%s' % (position_type, work_form),
            'sequence': 1,
            'apply_position_types': position_type,
            'apply_work_form': work_form,
            'step_ids': [(0, 0, {'name': 'Buoc test', 'step_type': 'task'})],
        })

    def test_tai_khoan_vai_tro_khong_gan_onboarding(self):
        """Tài khoản vai trò thử việc + có ngày bắt đầu vẫn KHÔNG được gán
        quy trình nhận việc — đối chứng: NV thật cùng dữ liệu thì CÓ.

        Chốt điều kiện trong _hocba_maybe_assign_onboarding() thay vì chỉ
        lọc ở create(): cách này còn bảo vệ được write() và
        _hocba_migrate_legacy_gates() — cùng một chỗ, không lặp lại điều
        kiện ở nhiều nơi."""
        self._ensure_matching_onboarding_template()
        today = fields.Date.context_today(self.env['hr.employee'])
        role_emp = self.env['hr.employee'].create({
            'name': 'TK Vai Tro Onb', 'x_is_role_account': True,
            'x_position_type': 'staff', 'x_work_form': 'offline',
            'x_probation_start': today})
        real_emp = self.env['hr.employee'].create({
            'name': 'NV That Onb', 'x_position_type': 'staff',
            'x_work_form': 'offline', 'x_probation_start': today})
        self.assertFalse(
            role_emp.x_onboarding_step_ids,
            'Tài khoản vai trò không được gán quy trình nhận việc.')
        self.assertTrue(
            real_emp.x_onboarding_step_ids,
            'NV thật cùng dữ liệu phải được gán quy trình nhận việc '
            '(nếu assert này fail, kiểm tra template khớp trong DB test).')

    def test_batch_create_hon_hop_chi_nv_that_co_moc_join(self):
        """create() một lần với recordset hỗn hợp (vai trò + NV thật) —
        filtered() trong create() phải tách đúng từng bản ghi, không lẫn
        theo vị trí trong vals_list."""
        employees = self.env['hr.employee'].create([
            {'name': 'TK Vai Tro Batch', 'x_is_role_account': True},
            {'name': 'NV That Batch'},
        ])
        role_emp, real_emp = employees[0], employees[1]
        Promotion = self.env['hr.promotion.history'].sudo()
        self.assertFalse(
            Promotion.search([('employee_id', '=', role_emp.id)]),
            'Bản ghi vai trò trong batch không được có mốc "Nhận việc".')
        self.assertTrue(
            Promotion.search([('employee_id', '=', real_emp.id)]),
            'Bản ghi NV thật trong cùng batch vẫn phải có mốc "Nhận việc".')

    # ---- Task 1 (code review): không cấp mã nhân sự cho tài khoản vai trò ----
    def test_tai_khoan_vai_tro_khong_cap_ma_nhan_su(self):
        """Không ngốn số dãy HB.xx của HR. Tạo HAI tài khoản vai trò để
        chứng minh ràng buộc unique(x_employee_code) chấp nhận nhiều bản ghi
        cùng để trống (Postgres: NULL không so bằng NULL) — không suy luận
        suông, để Odoo tự flush và raise nếu sai."""
        role_emp_1 = self.env['hr.employee'].create({
            'name': 'TK Vai Tro Ma 1', 'x_is_role_account': True})
        role_emp_2 = self.env['hr.employee'].create({
            'name': 'TK Vai Tro Ma 2', 'x_is_role_account': True})
        real_emp = self.env['hr.employee'].create({'name': 'NV That Ma'})
        self.assertFalse(
            role_emp_1.x_employee_code,
            'Tài khoản vai trò không được cấp mã nhân sự.')
        self.assertFalse(
            role_emp_2.x_employee_code,
            'Tài khoản vai trò không được cấp mã nhân sự.')
        self.assertTrue(
            real_emp.x_employee_code, 'NV thật vẫn phải có mã nhân sự.')
