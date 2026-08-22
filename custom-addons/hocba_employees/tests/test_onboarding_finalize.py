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
