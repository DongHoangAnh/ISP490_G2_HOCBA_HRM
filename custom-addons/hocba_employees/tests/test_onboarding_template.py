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


@tagged('post_install', '-at_install')
class TestIndependentStepFlags(TransactionCase):
    """Cờ 'Không ràng buộc thứ tự' — spec 2026-08-08."""

    def _tpl(self, step_vals):
        return self.env['hb.onboarding.template'].create({
            'name': 'TPL Indep', 'sequence': 1,
            'apply_position_types': 'ctv',
            'step_ids': [(0, 0, step_vals)]})

    def test_independent_task_ok(self):
        tpl = self._tpl({'name': 'Cấp thiết bị', 'step_type': 'task',
                         'sequence': 1, 'is_independent': True})
        self.assertTrue(tpl.step_ids.is_independent)

    def test_independent_rejected_on_evaluation(self):
        with self.assertRaisesRegex(ValidationError, 'Việc cần làm'):
            self._tpl({'name': 'ĐG', 'step_type': 'evaluation',
                       'sequence': 1, 'is_independent': True})

    def test_independent_rejected_with_auto_action(self):
        with self.assertRaisesRegex(ValidationError, 'Automation'):
            self._tpl({'name': 'Cấp TB', 'step_type': 'task', 'sequence': 1,
                       'is_independent': True,
                       'auto_action': 'grant_assets'})

    def test_independent_rejected_with_is_extension(self):
        # is_extension chỉ hợp lệ trên evaluation, mà independent lại chỉ
        # hợp lệ trên task → hai cờ không bao giờ đi cùng nhau
        with self.assertRaisesRegex(ValidationError, 'Việc cần làm'):
            self._tpl({'name': 'X', 'step_type': 'evaluation',
                       'sequence': 1, 'is_independent': True,
                       'is_extension': True})


@tagged('post_install', '-at_install')
class TestSyncIndependentEquip(TransactionCase):
    """Vá bước "Cấp thiết bị" trên MỌI quy trình, kể cả bản sao không có
    XML-ID (Neon có 2 cặp template trùng tên: bản 19/07 đang dùng thật và
    bản seed 25/07 mang XML-ID). Migration 19.0.4.0.0 chỉ vá bản XML-ID nên
    trên Neon nó là lệnh rỗng — spec §"Phát sinh khi lên Neon" 2026-08-09."""

    def setUp(self):
        super().setUp()
        self.Tpl = self.env['hb.onboarding.template']
        # Bản sao "mồ côi": KHÔNG XML-ID, vẫn còn auto_action như bản cũ.
        self.tpl = self.Tpl.create({
            'name': 'Bản sao VP', 'sequence': 99,
            'apply_position_types': 'ctv',
            'step_ids': [
                (0, 0, {'name': 'Đánh giá tuần-2', 'sequence': 1,
                        'step_type': 'evaluation'}),
                (0, 0, {'name': 'Cấp thiết bị làm việc', 'sequence': 2,
                        'step_type': 'task', 'auto_action': 'grant_assets'}),
            ]})
        self.equip = self.tpl.step_ids.filtered(
            lambda s: s.name == 'Cấp thiết bị làm việc')

    def _emp_step(self, state):
        emp = self.env['hr.employee'].create({
            'name': 'NV Sync %s' % state,
            'x_employment_status': 'probation'})
        return self.env['hb.onboarding.step'].create({
            'employee_id': emp.id, 'template_id': self.tpl.id,
            'sequence': 2, 'name': 'Cấp thiết bị làm việc',
            'step_type': 'task', 'state': state})

    def test_patches_orphan_template_step(self):
        self.assertFalse(self.equip.is_independent)
        self.Tpl._hocba_sync_independent_equip()
        self.assertTrue(self.equip.is_independent)
        # auto_action phải tắt cùng lúc, nếu không constrain sẽ chặn ngay
        self.assertEqual(self.equip.auto_action, 'none')

    def test_opens_waiting_employee_step(self):
        waiting = self._emp_step('waiting')
        self.Tpl._hocba_sync_independent_equip()
        self.assertTrue(waiting.is_independent)
        self.assertEqual(waiting.state, 'open')

    def test_keeps_history_states(self):
        done = self._emp_step('done')
        skipped = self._emp_step('skipped')
        self.Tpl._hocba_sync_independent_equip()
        self.assertEqual(done.state, 'done')
        self.assertEqual(skipped.state, 'skipped')
        self.assertTrue(done.is_independent)

    def test_idempotent(self):
        first = self.Tpl._hocba_sync_independent_equip()
        again = self.Tpl._hocba_sync_independent_equip()
        self.assertTrue(first['templateSteps'] >= 1)
        self.assertEqual(again, {'templateSteps': 0, 'steps': 0, 'opened': 0})

    def test_ignores_other_step_names(self):
        other = self.tpl.step_ids.filtered(
            lambda s: s.name == 'Đánh giá tuần-2')
        self.Tpl._hocba_sync_independent_equip()
        self.assertFalse(other.is_independent)
