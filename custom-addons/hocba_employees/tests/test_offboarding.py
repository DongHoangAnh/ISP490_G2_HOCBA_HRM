from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOffboardingModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Off Target',
            'identification_id': '012345678901',
        })

    def _make(self, **kw):
        vals = {
            'employee_id': self.emp.id,
            'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today(),
        }
        vals.update(kw)
        return self.env['hocba.offboarding'].create(vals)

    def test_create_generates_code_and_draft(self):
        rec = self._make()
        self.assertNotIn(rec.name, ('/', False))
        self.assertTrue(rec.name.startswith('OFF/'))
        self.assertEqual(rec.state, 'draft')
        self.assertEqual(rec.source, 'self')

    def test_happy_path_states(self):
        rec = self._make()
        rec.action_submit()
        self.assertEqual(rec.state, 'submitted')
        rec.sudo().action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        self.assertTrue(rec.mgr_approved_by)
        rec.sudo().action_hr_approve()
        self.assertEqual(rec.state, 'hr_approved')
        self.assertTrue(rec.hr_approved_by)

    def test_submit_only_from_draft(self):
        from odoo.exceptions import ValidationError
        rec = self._make()
        rec.action_submit()
        with self.assertRaises(ValidationError):
            rec.action_submit()

    def test_direct_manager_can_approve(self):
        mgr_user = self.env['res.users'].create({
            'name': 'DirectMgr', 'login': 'off_direct_mgr',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        mgr_emp = self.env['hr.employee'].create({
            'name': 'DirectMgr Emp', 'identification_id': '015555555501',
            'user_id': mgr_user.id})
        self.emp.parent_id = mgr_emp
        rec = self._make()
        rec.action_submit()
        rec.with_user(mgr_user).action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')

    def _advance_to_hr_approved(self, rec):
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        rec.sudo().action_hr_approve()

    def test_done_closes_profile_and_locks_user(self):
        user = self.env['res.users'].create({
            'name': 'Leaver', 'login': 'off_leaver_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.emp.user_id = user
        rec = self._make()
        self._advance_to_hr_approved(rec)
        rec.sudo().action_done()
        self.assertEqual(rec.state, 'done')
        self.assertEqual(self.emp.x_employment_status, 'resigned')
        self.assertFalse(self.emp.active)
        self.assertFalse(user.active)
        self.assertEqual(rec.actual_leave_date, fields.Date.today())

    def test_done_blocked_when_asset_assigned(self):
        from odoo.exceptions import ValidationError
        atype = self.env['hocba.asset.type'].create({
            'name': 'Laptop Off', 'code': 'LAPOFF'})
        self.env['hr.employee.asset'].create({
            'employee_id': self.emp.id,
            'asset_type_id': atype.id,
            'asset_code': 'LAPOFF-1',
            'grant_date': fields.Date.today(),
            'condition_in': 'new',
        })
        rec = self._make()
        self._advance_to_hr_approved(rec)
        with self.assertRaises(ValidationError):
            rec.sudo().action_done()
        self.assertEqual(rec.state, 'hr_approved')

    def test_refuse_after_mgr_restores_status(self):
        rec = self._make()
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        self.assertEqual(self.emp.x_employment_status, 'exiting')
        rec.sudo().action_refuse()
        self.assertEqual(rec.state, 'refused')
        self.assertEqual(self.emp.x_employment_status, 'probation')

    def test_cancel_only_before_approval(self):
        from odoo.exceptions import ValidationError
        rec = self._make()
        rec.action_submit()
        rec.sudo().action_mgr_approve()
        with self.assertRaises(ValidationError):
            rec.sudo().action_cancel()

    def test_cancel_before_submit(self):
        rec = self._make()
        rec.action_cancel()
        self.assertEqual(rec.state, 'cancelled')


@tagged('post_install', '-at_install')
class TestOffboardingAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        # Phòng A có trưởng phòng là mgrA
        self.mgrA_user = self.env['res.users'].create({
            'name': 'MgrA', 'login': 'off_mgra',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.mgrA = self.env['hr.employee'].create({
            'name': 'MgrA Emp', 'identification_id': '011111111101',
            'user_id': self.mgrA_user.id})
        self.deptA = self.env['hr.department'].create({
            'name': 'Dept A Off', 'manager_id': self.mgrA.id})
        # NV phòng A
        self.staffA_user = self.env['res.users'].create({
            'name': 'StaffA', 'login': 'off_staffa',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.staffA = self.env['hr.employee'].create({
            'name': 'StaffA Emp', 'identification_id': '011111111102',
            'department_id': self.deptA.id, 'user_id': self.staffA_user.id})
        # Giáo vụ + 1 giáo viên
        teacher_type = self.env['hocba.employee.type'].search(
            [('code', '=', 'teacher')], limit=1)
        self.gv_user = self.env['res.users'].create({
            'name': 'GiaoVu', 'login': 'off_gv',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hocba_employees.group_hocba_giaovu').id])]})
        self.teacher = self.env['hr.employee'].create({
            'name': 'Teacher Off', 'identification_id': '011111111103',
            'x_employee_type_id': teacher_type.id if teacher_type else False})

    def _submit_for(self, emp, submitter_user):
        rec = self.env['hocba.offboarding'].with_user(submitter_user).create({
            'employee_id': emp.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        rec.action_submit()
        return rec

    def test_manager_approves_own_dept(self):
        rec = self._submit_for(self.staffA, self.staffA_user)
        rec.with_user(self.mgrA_user).action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')

    def test_manager_cannot_approve_other_dept(self):
        from odoo.exceptions import AccessError
        staffB = self.env['hr.employee'].create({
            'name': 'StaffB', 'identification_id': '011111111104'})
        rec = self.env['hocba.offboarding'].sudo().create({
            'employee_id': staffB.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        rec.sudo().action_submit()
        with self.assertRaises(AccessError):
            rec.with_user(self.mgrA_user).action_mgr_approve()

    def test_giaovu_approves_teacher_not_office(self):
        from odoo.exceptions import AccessError
        rec_t = self.env['hocba.offboarding'].sudo().create({
            'employee_id': self.teacher.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        rec_t.sudo().action_submit()
        rec_t.with_user(self.gv_user).action_mgr_approve()
        self.assertEqual(rec_t.state, 'mgr_approved')
        rec_o = self._submit_for(self.staffA, self.staffA_user)
        with self.assertRaises(AccessError):
            rec_o.with_user(self.gv_user).action_mgr_approve()

    def test_employee_cannot_self_approve(self):
        from odoo.exceptions import AccessError
        rec = self._submit_for(self.staffA, self.staffA_user)
        with self.assertRaises(AccessError):
            rec.with_user(self.staffA_user).action_mgr_approve()

    def test_employee_cannot_refuse_own_submitted(self):
        from odoo.exceptions import AccessError
        rec = self._submit_for(self.staffA, self.staffA_user)
        with self.assertRaises(AccessError):
            rec.with_user(self.staffA_user).action_refuse()

    def test_refuse_at_mgr_approved_requires_hr(self):
        """Từ chối ở bước mgr_approved chỉ HR Manager (không phải TBP)."""
        from odoo.exceptions import AccessError
        rec = self._submit_for(self.staffA, self.staffA_user)
        rec.with_user(self.mgrA_user).action_mgr_approve()
        self.assertEqual(rec.state, 'mgr_approved')
        with self.assertRaises(AccessError):
            rec.with_user(self.mgrA_user).action_refuse()

    def test_read_scope_isolated_by_record_rule(self):
        """Chứng minh record rule lọc READ (không chỉ guard trong action)."""
        Off = self.env['hocba.offboarding'].sudo()
        staffB = self.env['hr.employee'].create({
            'name': 'StaffB Scope', 'identification_id': '011111111105'})
        rec_a = Off.create({'employee_id': self.staffA.id,
                            'reason_type': 'voluntary',
                            'expected_leave_date': fields.Date.today()})
        rec_t = Off.create({'employee_id': self.teacher.id,
                            'reason_type': 'voluntary',
                            'expected_leave_date': fields.Date.today()})
        rec_b = Off.create({'employee_id': staffB.id,
                            'reason_type': 'voluntary',
                            'expected_leave_date': fields.Date.today()})
        # NV thường chỉ thấy đơn của mình
        staff_seen = self.env['hocba.offboarding'].with_user(
            self.staffA_user).search([]).ids
        self.assertIn(rec_a.id, staff_seen)
        self.assertNotIn(rec_t.id, staff_seen)
        self.assertNotIn(rec_b.id, staff_seen)
        # Trưởng phòng thấy đơn NV phòng mình, không thấy giáo viên/NV phòng khác
        mgr_seen = self.env['hocba.offboarding'].with_user(
            self.mgrA_user).search([]).ids
        self.assertIn(rec_a.id, mgr_seen)
        self.assertNotIn(rec_t.id, mgr_seen)
        self.assertNotIn(rec_b.id, mgr_seen)
        # Giáo vụ chỉ thấy đơn của giáo viên
        gv_seen = self.env['hocba.offboarding'].with_user(
            self.gv_user).search([]).ids
        self.assertIn(rec_t.id, gv_seen)
        self.assertNotIn(rec_a.id, gv_seen)
        self.assertNotIn(rec_b.id, gv_seen)


@tagged('post_install', '-at_install')
class TestOffboardingProbation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Probation Fail', 'identification_id': '013333333301',
            'x_employment_status': 'probation'})

    def test_gate_fail_creates_offboarding(self):
        self.emp._hocba_start_offboarding('tuần-2')
        rec = self.env['hocba.offboarding'].search(
            [('employee_id', '=', self.emp.id)])
        self.assertEqual(len(rec), 1)
        self.assertEqual(rec.source, 'probation')
        self.assertEqual(rec.reason_type, 'performance')
        self.assertEqual(rec.state, 'hr_approved')
        self.assertEqual(rec.prev_employment_status, 'probation')
        self.assertEqual(self.emp.x_employment_status, 'exiting')

    def test_gate_fail_idempotent_no_duplicate(self):
        """Cổng rớt lại (re-fire) không tạo đơn offboarding trùng."""
        self.emp._hocba_start_offboarding('tuần-2')
        self.emp._hocba_start_offboarding('tháng-1')
        recs = self.env['hocba.offboarding'].search(
            [('employee_id', '=', self.emp.id)])
        self.assertEqual(len(recs), 1)

    def test_probation_completes_via_action_done(self):
        """MVP: luồng rớt thử việc đóng hồ sơ qua CÙNG action_done."""
        self.emp._hocba_start_offboarding('tuần-2')
        rec = self.env['hocba.offboarding'].search(
            [('employee_id', '=', self.emp.id)])
        rec.sudo().action_done()
        self.assertEqual(rec.state, 'done')
        self.assertEqual(self.emp.x_employment_status, 'resigned')
        self.assertFalse(self.emp.active)
