from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOnboardingFinalize(TransactionCase):
    """Nút "Chuyển chính thức": HR Manager kết thúc thử việc bằng tay khi
    chuỗi nhận việc chạy hết mà không có bước nào mang cờ "Đạt → lên chính
    thức" (vd quy trình Giáo viên: thử giảng → ký hợp đồng).

    Trước đây hết chuỗi chỉ bắn chuông "chờ HR quyết định" nên NV kẹt ở
    thử việc vĩnh viễn — không có đường nào lên official."""

    def setUp(self):
        super().setUp()
        base = self.env.ref('base.group_user').id
        self.hr_user = self.env['res.users'].create({
            'name': 'FinHR', 'login': 'onb_fin_hr',
            'group_ids': [(6, 0, [
                base, self.env.ref('hr.group_hr_manager').id])]})
        self.mgr_user = self.env['res.users'].create({
            'name': 'FinMgr', 'login': 'onb_fin_mgr',
            'group_ids': [(6, 0, [base])]})
        self.mgr_emp = self.env['hr.employee'].create({
            'name': 'FinMgr Emp', 'identification_id': '017788990201',
            'user_id': self.mgr_user.id})
        # Quy trình kiểu Giáo viên: KHÔNG bước nào pass_completes → chuỗi
        # chạy hết vẫn không ai chuyển official.
        self.tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL Kết chuỗi', 'apply_position_types': 'ctv',
            'sequence': 1,
            'step_ids': [
                (0, 0, {'name': 'Thử giảng', 'step_type': 'evaluation',
                        'sequence': 1}),
                (0, 0, {'name': 'Ký hợp đồng', 'step_type': 'task',
                        'sequence': 2}),
            ]})
        # BR-010: đủ CCCD/MST/BHXH để lên official không vướng ràng buộc
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Kết chuỗi', 'x_position_type': 'ctv',
            'parent_id': self.mgr_emp.id,
            'identification_id': '017788990202',
            'x_pit_code': '8017788992',
            'x_social_insurance_no': '0117788992',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today() - timedelta(days=30)})

    def _steps(self):
        return self.emp.x_onboarding_step_ids.sorted(
            lambda s: (s.sequence, s.id))

    def _run_chain(self):
        """Chạy hết chuỗi: thử giảng Đạt → hoàn thành task ký hợp đồng."""
        s = self._steps()
        s[0].action_evaluate('pass')
        self._steps()[1].action_complete()

    def test_finalize_makes_official_on_button_day(self):
        self._run_chain()
        self.assertEqual(self.emp.x_employment_status, 'probation')
        self.emp.with_user(self.hr_user).action_hocba_finalize_onboarding()
        self.assertEqual(self.emp.x_employment_status, 'official')
        self.assertEqual(self.emp.x_official_date, fields.Date.today())
        hist = self.env['hr.promotion.history'].sudo().search([
            ('employee_id', '=', self.emp.id),
            ('x_change_type', '=', 'probation')])
        self.assertTrue(hist)

    def test_finalize_blocked_while_a_step_is_pending(self):
        # mới gán: thử giảng đang open, ký hợp đồng đang waiting
        with self.assertRaises(ValidationError):
            self.emp.with_user(
                self.hr_user).action_hocba_finalize_onboarding()
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_finalize_blocked_when_a_step_failed(self):
        self._steps()[0].action_evaluate('fail', note='Không đáp ứng')
        # fail đã đẩy NV sang 'exiting' — kéo lại probation để kiểm ĐÚNG
        # chốt chặn "có bước không đạt", không phải chốt trạng thái.
        self.emp.sudo().with_context(
            hocba_gate_automation=True, hocba_no_onb_assign=True).write(
                {'x_employment_status': 'probation'})
        with self.assertRaises(ValidationError):
            self.emp.with_user(
                self.hr_user).action_hocba_finalize_onboarding()
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_finalize_blocked_without_any_process(self):
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'NV chưa gán quy trình',
                'x_position_type': 'ctv',
                'identification_id': '017788990203',
                'x_employment_status': 'probation',
                'x_probation_start': fields.Date.today()})
        self.assertFalse(emp.x_onboarding_step_ids)
        with self.assertRaises(ValidationError):
            emp.with_user(self.hr_user).action_hocba_finalize_onboarding()

    def test_finalize_blocked_when_already_official(self):
        self._run_chain()
        self.emp.with_user(self.hr_user).action_hocba_finalize_onboarding()
        with self.assertRaises(ValidationError):
            self.emp.with_user(
                self.hr_user).action_hocba_finalize_onboarding()

    def test_finalize_requires_hr_manager(self):
        self._run_chain()
        stranger = self.env['res.users'].create({
            'name': 'FinStranger', 'login': 'onb_fin_stranger',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            self.emp.with_user(stranger).action_hocba_finalize_onboarding()
        # Quản lý trực tiếp xử lý được TỪNG BƯỚC nhưng không quyết định
        # được biên chế — giữ đúng guard của hr_employee.write().
        with self.assertRaises(AccessError):
            self.emp.with_user(
                self.mgr_user).action_hocba_finalize_onboarding()
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_can_finalize_flag_tracks_chain_state(self):
        ok, reason = self.emp.with_user(
            self.hr_user)._hocba_onboarding_can_finalize()
        self.assertFalse(ok)
        self.assertTrue(reason)
        self._run_chain()
        ok, reason = self.emp.with_user(
            self.hr_user)._hocba_onboarding_can_finalize()
        self.assertTrue(ok)
        self.assertFalse(reason)

    # ---- Chốt khách 2026-08-27 (bản 2): văn phòng cũng đi đường NÚT ----
    def test_office_seed_chain_does_not_auto_promote(self):
        """Quy trình văn phòng seed: Đạt tháng-2 chỉ là XONG BƯỚC.

        Trước bản này tháng-2 mang cờ pass_completes nên Đạt là lên chính
        thức luôn, HR không có chỗ nào chốt lại — nút "Chuyển chính thức"
        vì thế không bao giờ hiện ra với nhân viên văn phòng."""
        emp = self.env['hr.employee'].create({
            'name': 'NV Văn phòng', 'x_position_type': 'staff',
            'x_work_form': 'offline',
            'identification_id': '017788990204',
            'x_pit_code': '8017788994',
            'x_social_insurance_no': '0117788994',
            'x_employment_status': 'probation',
            'x_probation_start': fields.Date.today() - timedelta(days=60)})
        self.assertEqual(emp.x_onboarding_template_id,
                         self.env.ref('hocba_employees.onb_template_office'))

        def steps():
            return emp.x_onboarding_step_ids.sorted(
                lambda s: (s.sequence, s.id))

        steps()[0].action_evaluate('pass')   # ĐG tuần-2
        steps()[2].action_evaluate('pass')   # ĐG tháng-1
        steps()[3].action_evaluate('pass')   # ĐG tháng-2
        self.assertEqual(steps()[3].state, 'done')
        self.assertEqual(emp.x_employment_status, 'probation')

    def test_open_independent_step_does_not_block_button(self):
        """Bước độc lập (vd cấp thiết bị) còn dở KHÔNG chặn nút.

        Nó nằm ngoài chuỗi — nhánh tự động (pass_completes) xưa nay vẫn cho
        NV lên chính thức khi nó còn mở, nên nút thủ công phải xử như vậy."""
        tpl = self.env['hb.onboarding.template'].create({
            'name': 'TPL Có bước độc lập', 'apply_position_types': 'ctv',
            'sequence': 2,
            'step_ids': [
                (0, 0, {'name': 'Đánh giá', 'step_type': 'evaluation',
                        'sequence': 1}),
                (0, 0, {'name': 'Cấp thiết bị', 'step_type': 'task',
                        'sequence': 2, 'is_independent': True}),
            ]})
        emp = self.env['hr.employee'].with_context(
            hocba_no_onb_assign=True).create({
                'name': 'NV Bước độc lập', 'x_position_type': 'ctv',
                'identification_id': '017788990205',
                'x_pit_code': '8017788995',
                'x_social_insurance_no': '0117788995',
                'x_employment_status': 'probation',
                'x_probation_start': fields.Date.today() - timedelta(days=30)})
        emp._hocba_assign_onboarding(template=tpl)
        steps = emp.x_onboarding_step_ids.sorted(lambda s: (s.sequence, s.id))
        steps[0].action_evaluate('pass')
        self.assertEqual(steps[1].state, 'open')

        ok, reason = emp.with_user(
            self.hr_user)._hocba_onboarding_can_finalize()
        self.assertTrue(ok, reason)
        emp.with_user(self.hr_user).action_hocba_finalize_onboarding()
        self.assertEqual(emp.x_employment_status, 'official')
        # Lên chính thức không được âm thầm đóng việc cấp thiết bị hộ HR.
        self.assertEqual(steps[1].state, 'open')
