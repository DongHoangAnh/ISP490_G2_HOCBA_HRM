from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOnboardingTemplate(TransactionCase):
    """Template quy trình nhận việc: constraints + matching."""

    def _tpl(self, steps, **kw):
        vals = {'name': 'TPL Test',
                'step_ids': [(0, 0, s) for s in steps]}
        vals.update(kw)
        return self.env['hb.onboarding.template'].create(vals)

    def test_template_requires_step(self):
        with self.assertRaises(ValidationError):
            self._tpl([])

    def test_eval_flags_only_on_evaluation(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'T1', 'step_type': 'task',
                        'pass_completes': True}])
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'T1', 'step_type': 'task',
                        'is_extension': True}])

    def test_auto_action_only_on_task(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'E1', 'step_type': 'evaluation',
                        'auto_action': 'grant_assets'}])

    def test_extension_must_follow_evaluation(self):
        # is_extension đứng đầu chuỗi → lỗi
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'E1', 'step_type': 'evaluation',
                        'is_extension': True, 'sequence': 1}])
        # is_extension sau task → lỗi
        with self.assertRaises(ValidationError):
            self._tpl([
                {'name': 'T1', 'step_type': 'task', 'sequence': 1},
                {'name': 'E1', 'step_type': 'evaluation',
                 'is_extension': True, 'sequence': 2}])
        # is_extension ngay sau evaluation → OK
        tpl = self._tpl([
            {'name': 'E1', 'step_type': 'evaluation', 'sequence': 1},
            {'name': 'E2', 'step_type': 'evaluation',
             'is_extension': True, 'sequence': 2}])
        self.assertEqual(len(tpl.step_ids), 2)

    def test_position_types_csv_validated(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'T1', 'step_type': 'task'}],
                      apply_position_types='staff,khong_ton_tai')
        tpl = self._tpl([{'name': 'T1', 'step_type': 'task'}],
                        apply_position_types='staff, manager')
        self.assertTrue(tpl)

    def test_due_days_non_negative(self):
        with self.assertRaises(ValidationError):
            self._tpl([{'name': 'E1', 'step_type': 'evaluation',
                        'due_days': -3}])

    def test_matching(self):
        Tpl = self.env['hb.onboarding.template']
        t_teacher = self.env.ref('hocba_employees.employee_type_teacher')
        # sequence 1-2 để thắng chắc chắn 2 template seed (sequence 5/10)
        tpl_gv = self._tpl([{'name': 'Thử giảng', 'step_type': 'evaluation'}],
                           name='TPL GV', sequence=1,
                           apply_employee_type_ids=[(6, 0, t_teacher.ids)])
        tpl_vp = self._tpl([{'name': 'ĐG', 'step_type': 'evaluation'}],
                           name='TPL VP', sequence=2,
                           apply_position_types='staff,manager',
                           apply_work_form='offline')
        emp_gv = self.env['hr.employee'].create({
            'name': 'GV Match', 'x_employee_type_id': t_teacher.id})
        emp_vp = self.env['hr.employee'].create({
            'name': 'VP Match', 'x_position_type': 'staff',
            'x_work_form': 'offline'})
        emp_none = self.env['hr.employee'].create({
            'name': 'Freelancer Online', 'x_position_type': 'freelancer',
            'x_work_form': 'online'})
        self.assertEqual(Tpl._match_for_employee(emp_gv), tpl_gv)
        self.assertEqual(Tpl._match_for_employee(emp_vp), tpl_vp)
        self.assertFalse(Tpl._match_for_employee(emp_none))
