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
