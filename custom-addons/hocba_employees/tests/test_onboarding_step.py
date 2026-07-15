from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOnboardingAssign(TransactionCase):
    """Gán template → sinh instance snapshot, bước đầu open."""

    def setUp(self):
        super().setUp()
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL VP', 'apply_position_types': 'staff',
            'apply_work_form': 'offline', 'sequence': 1,
            'step_ids': [
                (0, 0, {'name': 'ĐG tuần-2', 'step_type': 'evaluation',
                        'sequence': 1, 'due_days': 14}),
                (0, 0, {'name': 'Cấp thiết bị', 'step_type': 'task',
                        'sequence': 2}),
                (0, 0, {'name': 'ĐG tháng-1', 'step_type': 'evaluation',
                        'sequence': 3, 'due_days': 30,
                        'pass_completes': True}),
                (0, 0, {'name': 'ĐG tháng-2', 'step_type': 'evaluation',
                        'sequence': 4, 'due_days': 60, 'is_extension': True,
                        'pass_completes': True}),
            ]})
        self.start = fields.Date.today() - timedelta(days=5)

    def _mk_emp(self, **kw):
        vals = {'name': 'NV Onb', 'x_position_type': 'staff',
                'x_work_form': 'offline',
                'x_employment_status': 'probation',
                'x_probation_start': self.start}
        vals.update(kw)
        return self.env['hr.employee'].create(vals)

    def test_auto_assign_on_create(self):
        emp = self._mk_emp()
        steps = emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))
        self.assertEqual(emp.x_onboarding_template_id, self.tpl)
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps.mapped('state'),
                         ['open', 'waiting', 'waiting', 'waiting'])
        # snapshot + hạn từ probation_start
        self.assertEqual(steps[0].due_date,
                         self.start + timedelta(days=14))
        self.assertTrue(steps[3].is_extension)

    def test_assign_when_probation_starts_later(self):
        emp = self._mk_emp(x_probation_start=False)
        self.assertFalse(emp.x_onboarding_step_ids)
        emp.write({'x_probation_start': self.start})
        self.assertEqual(len(emp.x_onboarding_step_ids), 4)

    def test_no_template_notifies_hr_not_blocking(self):
        emp = self._mk_emp(x_position_type='freelancer',
                           x_work_form='online')
        self.assertFalse(emp.x_onboarding_step_ids)
        notif = self.env['hb.notification'].sudo().search([
            ('category', '=', 'onboarding'),
            ('kind', '=', 'onboarding_no_template'),
            ('target_ref', '=', emp.id)])
        self.assertTrue(notif)

    def test_snapshot_immune_to_template_edit(self):
        emp = self._mk_emp()
        self.tpl.step_ids.sorted(lambda s: (s.sequence, s.id))[0].write(
            {'name': 'ĐỔI TÊN', 'due_days': 99})
        step0 = emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))[0]
        self.assertEqual(step0.name, 'ĐG tuần-2')
        self.assertEqual(step0.due_date, self.start + timedelta(days=14))

    def test_official_employee_not_assigned(self):
        emp = self._mk_emp(x_employment_status='official',
                           identification_id='017788990001',
                           x_pit_code='8017788990',
                           x_social_insurance_no='0117788990')
        self.assertFalse(emp.x_onboarding_step_ids)


@tagged('post_install', '-at_install')
class TestOnboardingEngine(TransactionCase):
    """Máy trạng thái: complete task, auto_action, evaluate đủ nhánh."""

    def setUp(self):
        super().setUp()
        gu = [(6, 0, [self.env.ref('base.group_user').id])]
        self.mgr_user = self.env['res.users'].create({
            'name': 'OMgr', 'login': 'onb_mgr', 'group_ids': gu})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'OMgr Emp', 'identification_id': '017788990101',
            'user_id': self.mgr_user.id})
        # DB thật có thể chưa bật x_is_default (seed noupdate cũ) → tự tạo
        # loại tài sản mặc định riêng cho test grant_assets.
        self.asset_type = self.env['hocba.asset.type'].create({
            'name': 'Test Default Asset', 'code': 'tstonb',
            'x_is_default': True})
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL VP Engine', 'apply_position_types': 'staff',
            'apply_work_form': 'offline', 'sequence': 1,
            'step_ids': [
                (0, 0, {'name': 'ĐG tuần-2', 'step_type': 'evaluation',
                        'sequence': 1, 'due_days': 14}),
                (0, 0, {'name': 'Cấp thiết bị', 'step_type': 'task',
                        'sequence': 2, 'auto_action': 'grant_assets'}),
                (0, 0, {'name': 'ĐG tháng-1', 'step_type': 'evaluation',
                        'sequence': 3, 'due_days': 30,
                        'pass_completes': True}),
                (0, 0, {'name': 'ĐG tháng-2', 'step_type': 'evaluation',
                        'sequence': 4, 'due_days': 60, 'is_extension': True,
                        'pass_completes': True}),
            ]})
        # BR-010: đủ CCCD/MST/BHXH để pass lên official không vướng
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Engine', 'x_position_type': 'staff',
            'x_work_form': 'offline', 'parent_id': self.mgr_emp.id,
            'identification_id': '017788990102',
            'x_pit_code': '8017788991',
            'x_social_insurance_no': '0117788991',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today() - timedelta(days=10)})

    def _steps(self):
        return self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def test_eval_pass_opens_next_and_auto_grants(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        s = self._steps()
        self.assertEqual(s[0].state, 'done')
        self.assertEqual(s[0].result, 'pass')
        # bước task auto_action: tự grant + tự done → tháng-1 mở luôn
        self.assertEqual(s[1].state, 'done')
        self.assertTrue(self.emp.sudo().x_asset_ids)  # F-006 đã cấp
        self.assertEqual(s[2].state, 'open')

    def test_eval_pass_completes_goes_official_skips_rest(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('pass')
        self.assertEqual(self.emp.x_employment_status, 'official')
        self.assertTrue(self.emp.x_official_date)
        self.assertEqual(self._steps()[3].state, 'skipped')
        hist = self.env['hr.promotion.history'].sudo().search([
            ('employee_id', '=', self.emp.id),
            ('x_change_type', '=', 'probation')])
        self.assertTrue(hist)

    def test_eval_extend_to_extension_step(self):
        s = self._steps()
        s[0].action_evaluate('pass')
        self._steps()[2].action_evaluate('extend')
        s = self._steps()
        self.assertEqual(s[2].state, 'done')
        self.assertEqual(s[2].result, 'extend')
        self.assertEqual(s[3].state, 'open')  # bước gia hạn kích hoạt
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_eval_extend_in_place_when_no_extension_next(self):
        # tuần-2 extend → bước kế là task → giữ open + extend_count
        s = self._steps()
        s[0].action_evaluate('extend')
        s = self._steps()
        self.assertEqual(s[0].state, 'open')
        self.assertEqual(s[0].extend_count, 1)
        self.assertEqual(s[1].state, 'waiting')
        # tái đánh giá pass sau đó vẫn chạy tiếp
        s[0].action_evaluate('pass')
        self.assertEqual(self._steps()[2].state, 'open')

    def test_eval_fail_starts_offboarding_and_skips(self):
        s = self._steps()
        with self.assertRaises(ValidationError):
            s[0].action_evaluate('fail')  # fail phải có note
        s[0].action_evaluate('fail', note='Không đáp ứng')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        offb = self.env['hocba.offboarding'].sudo().search([
            ('employee_id', '=', self.emp.id),
            ('source', '=', 'probation')])
        self.assertTrue(offb)
        s = self._steps()
        self.assertTrue(all(x.state == 'skipped' for x in s[1:]))

    def test_cannot_act_when_not_open(self):
        s = self._steps()
        with self.assertRaises(ValidationError):
            s[2].action_evaluate('pass')  # đang waiting
        with self.assertRaises(ValidationError):
            s[1].action_complete()        # task đang waiting

    def test_pass_before_extension_skips_extension(self):
        # pass thường trước is_extension → skip is_extension, mở bước sau
        tpl2 = self.env['hb.onboarding.template'].create({
            'name': 'TPL 2', 'sequence': 1,
            'apply_position_types': 'ctv',
            'step_ids': [
                (0, 0, {'name': 'E1', 'step_type': 'evaluation',
                        'sequence': 1}),
                (0, 0, {'name': 'E2-ext', 'step_type': 'evaluation',
                        'sequence': 2, 'is_extension': True}),
                (0, 0, {'name': 'T-cuối', 'step_type': 'task',
                        'sequence': 3}),
            ]})
        emp2 = self.env['hr.employee'].create({
            'name': 'NV CTV', 'x_position_type': 'ctv',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today()})
        self.assertEqual(emp2.x_onboarding_template_id, tpl2)
        s = emp2.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        s[0].action_evaluate('pass')
        s = emp2.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        self.assertEqual(s[1].state, 'skipped')   # ext bị bỏ
        self.assertEqual(s[2].state, 'open')

    def test_chain_done_without_official_notifies(self):
        # template chỉ có task → xong chuỗi vẫn probation → chuông HR
        self.env['hb.onboarding.template'].create({
            'name': 'TPL mini', 'sequence': 1,
            'apply_position_types': 'advisor',
            'step_ids': [(0, 0, {'name': 'Ký HĐ', 'step_type': 'task',
                                 'sequence': 1})]})
        emp3 = self.env['hr.employee'].create({
            'name': 'NV Advisor', 'x_position_type': 'advisor',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today()})
        emp3.x_onboarding_step_ids.action_complete()
        self.assertEqual(emp3.x_employment_status, 'probation')
        notif = self.env['hb.notification'].sudo().search([
            ('kind', '=', 'onboarding_chain_done'),
            ('target_ref', '=', emp3.id)])
        self.assertTrue(notif)

    def test_skip_auto_trigger_records_without_side_effects(self):
        self.emp.sudo().write({'x_skip_auto_trigger': True})
        s = self._steps()
        s[0].action_evaluate('pass')
        # asset KHÔNG tự cấp, nhưng chuỗi vẫn tiến
        self.assertFalse(self.emp.sudo().x_asset_ids)
        self._steps()[2].action_evaluate('pass')
        # KHÔNG tự lên official
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_seed_templates_exist(self):
        gv = self.env.ref('hocba_employees.onb_template_teacher')
        vp = self.env.ref('hocba_employees.onb_template_office')
        self.assertEqual(len(gv.step_ids), 2)
        self.assertEqual(len(vp.step_ids), 4)
        steps = vp.step_ids.sorted(lambda s: (s.sequence, s.id))
        self.assertEqual(steps.mapped('step_type'),
                         ['evaluation', 'task', 'evaluation', 'evaluation'])
        self.assertTrue(steps[2].pass_completes)
        self.assertTrue(steps[3].is_extension and steps[3].pass_completes)
        self.assertEqual(steps[1].auto_action, 'grant_assets')
        # thử giảng KHÔNG pass_completes (pass hiện không lên chính thức)
        gv_steps = gv.step_ids.sorted(lambda s: (s.sequence, s.id))
        self.assertFalse(gv_steps[0].pass_completes)

    def test_reassign_template_manual(self):
        gv = self.env.ref('hocba_employees.onb_template_teacher')
        emp = self.emp
        self._steps()[0].action_evaluate('pass')
        done_before = len(emp.x_onboarding_step_ids.filtered(
            lambda s: s.state == 'done'))
        emp._hocba_assign_onboarding(template=gv)
        self.assertEqual(emp.x_onboarding_template_id, gv)
        # bước done giữ lại làm lịch sử, bước mới nối vào sau
        self.assertEqual(len(emp.x_onboarding_step_ids.filtered(
            lambda s: s.state == 'done')), done_before)
        news = emp.x_onboarding_step_ids.filtered(
            lambda s: s.template_id == gv)
        self.assertEqual(len(news), 2)
        news = news.sorted(lambda s: (s.sequence, s.id))
        self.assertEqual(news[0].state, 'open')
        # sequence bước mới phải đứng sau bước cũ còn giữ
        self.assertGreater(news[0].sequence, max(
            (emp.x_onboarding_step_ids - news).mapped('sequence')))

    def test_permission_evaluate(self):
        stranger = self.env['res.users'].create({
            'name': 'Stranger', 'login': 'onb_stranger',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        s = self._steps()
        with self.assertRaises(AccessError):
            s[0].with_user(stranger).action_evaluate('pass')
        # Quản lý trực tiếp thì được
        s[0].with_user(self.mgr_user).action_evaluate('pass')
        self.assertEqual(self._steps()[0].result, 'pass')
        self.assertEqual(self._steps()[0].done_by_id, self.mgr_user)


@tagged('post_install', '-at_install')
class TestOnboardingMigration(TransactionCase):
    """Map field cổng cứng cũ → bước động (migration 19.0.2.0.0)."""

    def test_migrate_legacy_group_b(self):
        start = fields.Date.today() - timedelta(days=40)
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'Legacy B', 'x_position_type': 'staff',
                'x_work_form': 'offline',
                'x_employment_status': 'probation',
                'x_probation_start': start})
        # giả lập dữ liệu cũ: tuần-2 pass, thiết bị đã cấp, tháng-1 extend
        emp.sudo().with_context(hocba_no_onb_assign=True).write({
            'x_eval_2w_result': 'pass',
            'x_eval_2w_date': start + timedelta(days=14),
            'x_equip_grant_date': start + timedelta(days=15),
            'x_eval_1m_result': 'extend',
            'x_eval_1m_date': start + timedelta(days=30),
        })
        self.assertFalse(emp.x_onboarding_step_ids)
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        s = emp.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        self.assertEqual(len(s), 4)
        self.assertEqual(
            [(x.name, x.state) for x in s[:3]],
            [('Đánh giá tuần-2', 'done'),
             ('Cấp thiết bị làm việc', 'done'),
             ('Đánh giá tháng-1', 'done')])
        self.assertEqual(s[2].result, 'extend')
        self.assertEqual(s[3].state, 'open')   # cổng tháng-2 đang chờ
        # idempotent
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        self.assertEqual(len(emp.x_onboarding_step_ids), 4)

    def test_migrate_legacy_teacher_trial_pass(self):
        t_teacher = self.env.ref('hocba_employees.employee_type_teacher')
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'Legacy GV', 'x_employee_type_id': t_teacher.id,
                'x_employment_status': 'probation',
                'x_probation_start': fields.Date.today() - timedelta(days=9)})
        emp.sudo().with_context(hocba_no_onb_assign=True).write({
            'x_trial_lesson_result': 'pass',
            'x_trial_lesson_date': fields.Date.today() - timedelta(days=2),
            'x_trial_score_method': 8, 'x_trial_score_content': 9})
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        s = emp.x_onboarding_step_ids.sorted(lambda x: (x.sequence, x.id))
        self.assertEqual(len(s), 2)
        self.assertEqual(s[0].result, 'pass')
        self.assertIn('8', s[0].result_note)  # điểm cũ ghi vào nhận xét
        self.assertEqual(s[1].state, 'open')  # Ký HĐ thỉnh giảng chờ

    def test_migrate_fresh_probation_assigns_template(self):
        # NV thử việc chưa có dữ liệu cổng cũ → migration gán template mới
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'Fresh Prob', 'x_position_type': 'staff',
                'x_work_form': 'offline',
                'x_employment_status': 'probation',
                'x_probation_start': fields.Date.today()})
        self.assertFalse(emp.x_onboarding_step_ids)
        self.env['hr.employee']._hocba_migrate_legacy_gates()
        self.assertTrue(emp.x_onboarding_step_ids)
