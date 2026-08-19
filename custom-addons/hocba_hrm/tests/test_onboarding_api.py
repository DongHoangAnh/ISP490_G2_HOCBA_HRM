from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOnboardingTemplateReplaceAll(TransactionCase):
    """API sửa template dùng pattern replace-all steps ((5,0,0) + create) —
    kiểm chứng ORM giữ constraint và KHÔNG ảnh hưởng NV đã gán (snapshot).
    Route quyền (403 non-HR-Manager) dùng chung _hr_flags như các API khác."""

    def setUp(self):
        super().setUp()
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL API', 'sequence': 1,
            'apply_position_types': 'staff',
            'step_ids': [
                (0, 0, {'name': 'B1 cũ', 'step_type': 'evaluation',
                        'sequence': 1, 'due_days': 7}),
                (0, 0, {'name': 'B2 cũ', 'step_type': 'task',
                        'sequence': 2}),
            ]})

    def test_replace_all_steps(self):
        self.tpl.write({'step_ids': [(5, 0, 0)] + [
            (0, 0, {'name': 'E1', 'step_type': 'evaluation',
                    'sequence': 1, 'due_days': 10}),
            (0, 0, {'name': 'E2-ext', 'step_type': 'evaluation',
                    'sequence': 2, 'is_extension': True,
                    'pass_completes': True}),
            (0, 0, {'name': 'T3', 'step_type': 'task', 'sequence': 3}),
        ]})
        steps = self.tpl.step_ids.sorted(lambda s: (s.sequence, s.id))
        self.assertEqual(steps.mapped('name'), ['E1', 'E2-ext', 'T3'])
        self.assertTrue(steps[1].is_extension)

    def test_replace_all_keeps_constraints(self):
        # extension đứng sau task → constraint template phải chặn
        with self.assertRaises(ValidationError):
            self.tpl.write({'step_ids': [(5, 0, 0)] + [
                (0, 0, {'name': 'T1', 'step_type': 'task', 'sequence': 1}),
                (0, 0, {'name': 'E-ext', 'step_type': 'evaluation',
                        'sequence': 2, 'is_extension': True}),
            ]})

    def test_snapshot_survives_replace_all(self):
        emp = self.env['hr.employee'].create({
            'name': 'NV API Snap', 'x_position_type': 'staff',
            'x_employment_status': 'probation',
            'x_probation_start': '2026-07-01'})
        self.assertEqual(emp.x_onboarding_template_id, self.tpl)
        before = emp.x_onboarding_step_ids.mapped('name')
        self.tpl.write({'step_ids': [(5, 0, 0)] + [
            (0, 0, {'name': 'MỚI', 'step_type': 'task', 'sequence': 1}),
        ]})
        self.assertEqual(emp.x_onboarding_step_ids.mapped('name'), before)


class _FakeRequest:
    """Đủ để _onb_emp_item đọc request.env.user ngoài context HTTP."""

    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestOnboardingFinalizeFlag(TransactionCase):
    """Cờ canFinalize trong payload màn Nhận việc — FE bật/tắt nút
    "Chuyển chính thức". Chuỗi hết bước mà không bước nào pass_completes
    thì đây là đường duy nhất để NV lên Chính thức."""

    def setUp(self):
        super().setUp()
        from odoo import http
        from odoo.addons.hocba_hrm.controllers.main import HocBaHRM
        self.ctrl = HocBaHRM()
        self.http = http
        base = self.env.ref('base.group_user').id
        self.hr_user = self.env['res.users'].create({
            'name': 'HR Fin', 'login': 'onbfin_api_hr',
            'group_ids': [(6, 0, [
                base, self.env.ref('hr.group_hr_manager').id])]})
        self.mgr_user = self.env['res.users'].create({
            'name': 'Mgr Fin', 'login': 'onbfin_api_mgr',
            'group_ids': [(6, 0, [base])]})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'Mgr Fin Emp', 'identification_id': '014444440301',
            'user_id': self.mgr_user.id})
        self.tpl_fin = self.env['hb.onboarding.template'].create({
            'name': 'TPL API Kết chuỗi', 'sequence': 1,
            'apply_position_types': 'ctv',
            'step_ids': [
                (0, 0, {'name': 'Thử giảng', 'step_type': 'evaluation',
                        'sequence': 1}),
                (0, 0, {'name': 'Ký hợp đồng', 'step_type': 'task',
                        'sequence': 2}),
            ]})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV API Kết chuỗi', 'x_position_type': 'ctv',
            'parent_id': self.mgr_emp.id,
            'identification_id': '014444440302',
            'x_pit_code': '8014444440',
            'x_social_insurance_no': '0114444440',
            'x_employment_status': 'probation',
            'x_probation_start': '2026-07-01'})

    def _item(self, user):
        self.http._request_stack.push(_FakeRequest(self.env(user=user)))
        try:
            return self.ctrl._onb_emp_item(
                self.env(user=user)['hr.employee'].sudo().browse(self.emp.id))
        finally:
            self.http._request_stack.pop()

    def _run_chain(self):
        steps = self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))
        steps[0].action_evaluate('pass')
        self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[1].action_complete()

    def test_flag_false_while_chain_running(self):
        self.assertFalse(self._item(self.hr_user)['canFinalize'])

    def test_flag_true_for_hr_manager_when_chain_done(self):
        self._run_chain()
        self.assertTrue(self._item(self.hr_user)['canFinalize'])

    def test_flag_false_for_non_hr_manager(self):
        self._run_chain()
        self.assertFalse(self._item(self.mgr_user)['canFinalize'])
