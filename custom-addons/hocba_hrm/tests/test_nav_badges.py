"""Badge "việc cần xử lý" cạnh tên mục menu (Nhận việc / Nghỉ việc).

Spec: docs/superpowers/specs/2026-08-12-nav-badge-viec-can-xu-ly-design.md

Ràng buộc lớn nhất: số trên badge phải BẰNG số bản ghi user thật sự bấm
được trên màn danh sách. Đếm rộng hơn quyền = mời người ta bấm vào 403.

DB test dùng chung nên count là số toàn cục — mọi assert đều so DELTA quanh
bản ghi do test tự tạo, không so số tuyệt đối.
"""
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import HocBaHRM


@tagged('post_install', '-at_install')
class NavBadgeCase(TransactionCase):
    """Bộ vai trò dùng chung: HR Manager, HR officer, trưởng phòng, giáo vụ,
    nhân viên thường."""

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaHRM()
        gu = self.env.ref('base.group_user').id

        self.dept = self.env['hr.department'].create({'name': 'Badge Dept'})
        self.other_dept = self.env['hr.department'].create(
            {'name': 'Badge Dept Khac'})

        # Trưởng phòng của Badge Dept
        self.tp_user = self.env['res.users'].create({
            'name': 'Badge TP', 'login': 'badge_tp',
            'group_ids': [(6, 0, [gu])]})
        self.tp_emp = self.env['hr.employee'].create({
            'name': 'Badge TP Emp', 'identification_id': '017000000001',
            'user_id': self.tp_user.id, 'department_id': self.dept.id,
            'x_employment_status': 'parttime'})
        self.dept.manager_id = self.tp_emp.id

        # Giáo vụ
        self.gv_user = self.env['res.users'].create({
            'name': 'Badge GV', 'login': 'badge_gv', 'group_ids': [(6, 0, [
                gu, self.env.ref('hocba_employees.group_hocba_giaovu').id])]})

        # HR Manager + HR officer
        self.hrm_user = self.env['res.users'].create({
            'name': 'Badge HRM', 'login': 'badge_hrm', 'group_ids': [(6, 0, [
                gu, self.env.ref('hr.group_hr_manager').id])]})
        self.hru_user = self.env['res.users'].create({
            'name': 'Badge HRU', 'login': 'badge_hru', 'group_ids': [(6, 0, [
                gu, self.env.ref('hr.group_hr_user').id])]})

        # Nhân viên thường (không quản ai)
        self.staff_user = self.env['res.users'].create({
            'name': 'Badge Staff', 'login': 'badge_staff',
            'group_ids': [(6, 0, [gu])]})
        self.staff = self.env['hr.employee'].create({
            'name': 'Badge Staff Emp', 'identification_id': '017000000002',
            'user_id': self.staff_user.id, 'department_id': self.dept.id,
            'x_employment_status': 'parttime'})

        # NV phòng khác + giáo viên (không thuộc phòng nào)
        self.out_emp = self.env['hr.employee'].create({
            'name': 'Badge Out Emp', 'identification_id': '017000000003',
            'department_id': self.other_dept.id,
            'x_employment_status': 'parttime'})
        teacher_type = self.env['hocba.employee.type'].search(
            [('code', '=', 'teacher')], limit=1)
        self.teacher = self.env['hr.employee'].create({
            'name': 'Badge Teacher', 'identification_id': '017000000004',
            'x_employee_type_id': teacher_type.id if teacher_type else False,
            'x_employment_status': 'parttime'})

    def _env(self, user):
        return self.env(user=user)


@tagged('post_install', '-at_install')
class TestOnboardingBadge(NavBadgeCase):

    def _count(self, user):
        return self.ctrl._onb_pending_count(self._env(user))['count']

    def _step(self, emp, state='open', step_type='task'):
        return self.env['hb.onboarding.step'].create({
            'employee_id': emp.id, 'name': 'Bước %s' % emp.name,
            'step_type': step_type, 'state': state})

    def test_hr_manager_dem_moi_buoc_dang_cho(self):
        before = self._count(self.hrm_user)
        self._step(self.staff)
        self._step(self.out_emp)
        self.assertEqual(self._count(self.hrm_user), before + 2)

    def test_chi_dem_buoc_state_open(self):
        before = self._count(self.hrm_user)
        self._step(self.staff, state='waiting')
        self._step(self.staff, state='done')
        self.assertEqual(self._count(self.hrm_user), before)

    def test_truong_phong_chi_dem_phong_minh(self):
        before = self._count(self.tp_user)
        self._step(self.staff)        # phòng mình → tính
        self._step(self.out_emp)      # phòng khác → không
        self.assertEqual(self._count(self.tp_user), before + 1)

    def test_quan_ly_truc_tiep_dem_cap_duoi(self):
        report = self.env['hr.employee'].create({
            'name': 'Badge Report', 'identification_id': '017000000005',
            'parent_id': self.tp_emp.id, 'department_id': self.other_dept.id,
            'x_employment_status': 'parttime'})
        before = self._count(self.tp_user)
        self._step(report)
        self.assertEqual(self._count(self.tp_user), before + 1)

    def test_giao_vu_chi_dem_buoc_task_cua_giao_vien(self):
        before = self._count(self.gv_user)
        self._step(self.teacher, step_type='task')            # tính
        self._step(self.teacher, step_type='evaluation')      # không: giáo vụ
        self._step(self.staff, step_type='task')              # không: ko phải GV
        self.assertEqual(self._count(self.gv_user), before + 1)

    def test_nhan_vien_thuong_va_hr_officer_khong_co_badge(self):
        self._step(self.staff)
        for user in (self.staff_user, self.hru_user):
            out = self.ctrl._onb_pending_count(self._env(user))
            self.assertFalse(out['canAct'])
            self.assertEqual(out['count'], 0)

    def test_kiem_ca_hai_vai_khong_dem_trung(self):
        """Trưởng phòng KIÊM giáo vụ: một bước task của giáo viên trong phòng
        mình khớp cả 2 nhánh domain — phải đếm 1, không phải 2."""
        self.tp_user.write({'group_ids': [(4, self.env.ref(
            'hocba_employees.group_hocba_giaovu').id)]})
        self.teacher.department_id = self.dept.id
        before = self._count(self.tp_user)
        self._step(self.teacher, step_type='task')
        self.assertEqual(self._count(self.tp_user), before + 1)


@tagged('post_install', '-at_install')
class TestOffboardingBadge(NavBadgeCase):

    def _count(self, user):
        return self.ctrl._offb_pending_count(self._env(user))['count']

    def _don(self, emp, state='submitted'):
        rec = self.env['hocba.offboarding'].create({
            'employee_id': emp.id, 'reason_type': 'voluntary',
            'expected_leave_date': fields.Date.today()})
        if state != 'draft':
            rec.action_submit()
        if state in ('mgr_approved', 'hr_approved'):
            rec.sudo().action_mgr_approve()
        if state == 'hr_approved':
            rec.sudo().action_hr_approve()
        return rec

    def test_truong_phong_dem_don_cho_minh_duyet(self):
        before = self._count(self.tp_user)
        self._don(self.staff)          # phòng mình, chờ QL duyệt → tính
        self._don(self.out_emp)        # phòng khác → không
        self.assertEqual(self._count(self.tp_user), before + 1)

    def test_truong_phong_khong_dem_chang_cua_hr(self):
        before = self._count(self.tp_user)
        self._don(self.staff, state='mgr_approved')
        self.assertEqual(self._count(self.tp_user), before)

    def test_hr_manager_dem_ca_ba_trang_thai_can_bam(self):
        before = self._count(self.hrm_user)
        self._don(self.staff, state='submitted')
        self._don(self.out_emp, state='mgr_approved')
        self._don(self.teacher, state='hr_approved')
        self.assertEqual(self._count(self.hrm_user), before + 3)

    def test_hr_officer_khong_duyet_duoc_nen_khong_co_badge(self):
        self._don(self.staff)
        out = self.ctrl._offb_pending_count(self._env(self.hru_user))
        self.assertFalse(out['canAct'])
        self.assertEqual(out['count'], 0)

    def test_nhan_vien_thuong_khong_co_badge(self):
        self._don(self.staff)
        out = self.ctrl._offb_pending_count(self._env(self.staff_user))
        self.assertFalse(out['canAct'])
        self.assertEqual(out['count'], 0)

    def test_badge_khop_so_nut_bam_duoc_tren_man_danh_sach(self):
        """Chốt chặn chống lệch: badge phải bằng số đơn có can* = True mà
        /api/offboarding/list dựng cho chính user đó."""
        self._don(self.staff, state='submitted')
        self._don(self.teacher, state='mgr_approved')
        self._don(self.out_emp, state='hr_approved')
        for user in (self.hrm_user, self.tp_user, self.gv_user,
                     self.hru_user, self.staff_user):
            env = self._env(user)
            recs = env['hocba.offboarding'].browse(
                env['hocba.offboarding'].sudo().search([]).ids)
            actionable = 0
            for rec in recs:
                d = self.ctrl._offb_json(rec)
                if d['canMgrApprove'] or d['canHrApprove'] or d['canDone']:
                    actionable += 1
            self.assertEqual(
                self.ctrl._offb_pending_count(env)['count'], actionable,
                'Badge lệch số nút bấm được với user %s' % user.login)
